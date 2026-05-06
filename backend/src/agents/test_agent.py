from __future__ import annotations

"""测试验证 Agent"""

import base64
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

from .base_agent import BaseAgent, AgentInput, AgentOutput


class TestAgent(BaseAgent):
    """
    测试验证 Agent
    职责：
      Phase 1 — 生成测试文件 + 依赖清单（由 service 触发，结果需人工确认安装）
      Phase 2 — 安装依赖 + 执行测试（由 service._run_testing_phase2 直接调用）
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Phase 1: 生成测试文件与依赖声明，不执行测试。"""
        code_files = input_data.context.get("generated_code", {})
        resolved_stack = input_data.context.get("solution_structured", {}).get("resolved_stack", {})
        feedback = input_data.human_feedback

        test_files, deps_manifest, token_usage, model = await self._llm_generate_tests(
            code_files, resolved_stack, feedback
        )

        return AgentOutput(
            success=True,
            result={
                "test_files": test_files,
                "deps_manifest": deps_manifest,
                "test_results": {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0},
                "report": self._format_deps_report(deps_manifest),
                "pass_rate": "待执行",
            },
            summary=f"测试文件生成完成，共 {len(test_files)} 个文件，请确认安装依赖后执行测试",
            details=self._format_deps_report(deps_manifest),
            needs_human_review=True,  # 始终需要人工确认依赖安装
            token_usage=token_usage,
            model=model,
        )

    async def _llm_generate_tests(
        self,
        code_files: Dict[str, str],
        resolved_stack: dict,
        feedback: str | None,
    ) -> tuple:
        """两次 LLM 调用：先生成测试代码，再单独分析依赖。"""
        import json

        code_summary = "\n\n".join(
            f"=== {path} ===\n{content}"
            for path, content in code_files.items()
        )
        backend = resolved_stack.get("backend", "unknown")
        frontend = resolved_stack.get("frontend", "unknown")
        testing_stack = resolved_stack.get("testing", "unknown")

        usage_totals: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        model_name = self.model_name

        def _accum(resp) -> None:
            if resp.usage:
                for k in usage_totals:
                    usage_totals[k] += int(resp.usage.get(k, 0) or 0)
            if resp.model:
                nonlocal model_name
                model_name = resp.model

        # ── Call 1: 只生成测试代码 ────────────────────────────────────────
        def code_prompt(retry_hint: str = "") -> str:
            hint = f"\n\n⚠️ {retry_hint}" if retry_hint else ""
            fb = f"\n\n根据以下反馈修改：\n{feedback}" if feedback else ""
            return f"""请为以下代码编写单元测试。

## 技术栈
- 后端: {backend} / 前端: {frontend} / 测试框架: {testing_stack}

## 代码文件
{code_summary}

## 输出规则（只能用这种格式，不能用任何其他格式）
每个测试文件用下面的 XML 标签块输出，标签名必须完全一致：

<file path="tests/test_xxx.py">
<summary>覆盖内容说明</summary>
<content>
测试代码正文（纯文本，不要用 markdown 代码块包裹）
</content>
</file>

可以输出多个 <file> 块。不要输出 JSON，不要解释，不要额外前缀。{hint}{fb}"""

        test_files: dict[str, str] = {}
        last_code_response = ""
        for attempt in range(1, 4):
            hint = f"第 {attempt} 次重试：上次未能解析到 <file> 标签，请严格按格式输出" if attempt > 1 else ""
            resp = await self.call_llm_response(code_prompt(hint))
            last_code_response = resp.content
            _accum(resp)

            test_files = self._parse_tagged_files(last_code_response)
            if not test_files:
                test_files = self._parse_code_blocks(last_code_response, backend)
            if test_files:
                print(f"[TestAgent] ✅ Call 1 成功（第 {attempt} 次），解析到 {len(test_files)} 个测试文件")
                break
            preview = last_code_response[:600].replace("\n", "\n  ")
            print(f"[TestAgent] ⚠️ Call 1 第 {attempt} 次解析失败，响应预览：\n  {preview}\n{'─'*56}")

        if not test_files:
            print("[TestAgent] ❌ Call 1 三次均失败，使用占位文件")
            test_files = {"tests/test_placeholder.py": "# 测试文件生成失败，请人工编写\n"}

        # ── Call 2: 只分析依赖，返回 JSON ────────────────────────────────
        test_code_summary = "\n\n".join(
            f"=== {path} ===\n{content[:800]}"
            for path, content in test_files.items()
        )
        deps_prompt = f"""根据以下测试代码，列出运行这些测试需要安装的额外 Python/Node 包。

## 测试文件
{test_code_summary}

## 技术栈
- 后端: {backend} / 测试框架: {testing_stack}

## 要求
- 只列出测试本身需要的包（不重复列项目已有的业务依赖）
- 直接返回 JSON，不要任何解释文字

返回格式（严格 JSON，无其他内容）：
{{
  "pip_packages": ["pytest"],
  "npm_packages": [],
  "install_commands": {{
    "python": "pip install pytest",
    "node": ""
  }}
}}"""

        deps_manifest: dict = {"pip_packages": [], "npm_packages": [], "install_commands": {}}
        try:
            resp2 = await self.call_llm_response(deps_prompt, expect_json=True)
            _accum(resp2)
            raw = resp2.content.strip()
            # strip markdown if model wraps it anyway
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                deps_manifest.update(parsed)
            print(f"[TestAgent] ✅ Call 2 deps: pip={deps_manifest.get('pip_packages')} npm={deps_manifest.get('npm_packages')}")
        except Exception as exc:
            print(f"[TestAgent] ⚠️ Call 2 deps 解析失败（{exc}），使用空清单")

        final_usage = usage_totals if any(usage_totals.values()) else None
        return test_files, deps_manifest, final_usage, model_name

    def _parse_code_blocks(self, response_text: str, backend: str) -> dict[str, str]:
        """Fallback：从 ```python 代码块中提取测试文件。"""
        files: dict[str, str] = {}
        pattern = re.compile(r"```(?:python|py)\s*\n(.*?)```", re.DOTALL)
        for i, code in enumerate(pattern.findall(response_text)):
            code = code.strip()
            if not code:
                continue
            if "def test_" in code or "import pytest" in code or "describe(" in code:
                suffix = ".py" if "python" in backend.lower() else ".js"
                files[f"tests/test_generated_{i + 1}{suffix}"] = code
        return files

    # ──────────────────────────────────────────────────────────────
    # Phase 2 helpers (called directly by service._run_testing_phase2)
    # ──────────────────────────────────────────────────────────────

    def install_deps(self, project_path: str, deps_manifest: dict) -> dict:
        """安装测试依赖，返回安装结果。"""
        result = {"success": True, "pip": None, "npm": None, "errors": []}
        proj = Path(project_path)

        pip_packages = deps_manifest.get("pip_packages", [])
        npm_packages = deps_manifest.get("npm_packages", [])

        if pip_packages:
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet"] + pip_packages,
                    cwd=str(proj),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                result["pip"] = "ok" if proc.returncode == 0 else proc.stderr[:300]
                if proc.returncode != 0:
                    result["success"] = False
                    result["errors"].append(f"pip: {proc.stderr[:200]}")
            except Exception as exc:
                result["pip"] = str(exc)
                result["success"] = False
                result["errors"].append(f"pip: {exc}")

        if npm_packages:
            npm_cmd = "npm"
            try:
                proc = subprocess.run(
                    [npm_cmd, "install", "--save-dev", "--silent"] + npm_packages,
                    cwd=str(proj),
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                result["npm"] = "ok" if proc.returncode == 0 else proc.stderr[:300]
                if proc.returncode != 0:
                    result["success"] = False
                    result["errors"].append(f"npm: {proc.stderr[:200]}")
            except Exception as exc:
                result["npm"] = str(exc)
                result["success"] = False
                result["errors"].append(f"npm: {exc}")

        return result

    def run_tests(self, project_path: str, test_files: dict[str, str]) -> dict:
        """写入测试文件并执行，返回测试结果。"""
        default: dict = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0, "ran": False}
        proj = Path(project_path)
        if not proj.exists():
            return default

        # 写测试文件
        for rel_path, content in test_files.items():
            target = proj / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        # 检测测试类型
        has_python = any(p.endswith(".py") for p in test_files)
        has_node = any(p.endswith((".ts", ".tsx", ".js", ".jsx")) for p in test_files)

        if has_python:
            return self._run_pytest(proj)
        if has_node:
            return self._run_npm_test(proj)
        return default

    def _run_pytest(self, proj: Path) -> dict:
        result: dict = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0, "ran": True}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
                cwd=str(proj),
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {**result, **self._parse_pytest_output(proc.stdout + proc.stderr), "ran": True}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return {**result, "ran": False}

    def _run_npm_test(self, proj: Path) -> dict:
        result: dict = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0, "ran": True}
        # check if package.json has test script
        pkg = proj / "package.json"
        try:
            import json
            data = json.loads(pkg.read_text()) if pkg.exists() else {}
            scripts = data.get("scripts", {})
            if "test" not in scripts:
                return {**result, "ran": False, "errors": ["package.json 中无 test 脚本"]}
        except Exception:
            return {**result, "ran": False}

        try:
            proc = subprocess.run(
                ["npm", "test", "--", "--watchAll=false", "--passWithNoTests"],
                cwd=str(proj),
                capture_output=True,
                text=True,
                timeout=180,
            )
            return {**result, **self._parse_jest_output(proc.stdout + proc.stderr), "ran": True}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return {**result, "ran": False}

    def _parse_pytest_output(self, output: str) -> dict:
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        failed_lines = re.findall(r"FAILED\s+(\S+)", output)
        return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "errors": failed_lines[:10],
            "coverage": 0,
        }

    def _parse_jest_output(self, output: str) -> dict:
        # "Tests: 3 passed, 1 failed, 4 total"
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        total_match = re.search(r"(\d+) total", output)
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        total = int(total_match.group(1)) if total_match else passed + failed
        return {"passed": passed, "failed": failed, "total": total, "errors": [], "coverage": 0}

    # ──────────────────────────────────────────────────────────────
    # Shared helpers
    # ──────────────────────────────────────────────────────────────

    def _parse_tagged_files(self, response_text: str) -> dict[str, str]:
        files: dict[str, str] = {}
        pattern = re.compile(
            r"<file\s+path=[\"']([^\"']+)[\"']>\s*(?:<summary>.*?</summary>\s*)?<(?P<tag>content|content_base64)>\s*(?P<body>.*?)\s*</(?P=tag)>\s*</file>",
            re.DOTALL,
        )
        for match in pattern.finditer(response_text):
            path = match.group(1).strip()
            tag = match.group("tag").strip()
            payload = match.group("body")
            if not path or payload is None:
                continue
            if tag == "content_base64":
                encoded_content = payload.strip()
                if not encoded_content:
                    continue
                try:
                    content = base64.b64decode(encoded_content).decode("utf-8")
                except Exception:
                    continue
            else:
                content = payload
            files[path] = content
        return files

    def _format_deps_report(self, deps_manifest: dict) -> str:
        pip = deps_manifest.get("pip_packages", [])
        npm = deps_manifest.get("npm_packages", [])
        lines = ["## 测试依赖清单", ""]
        if pip:
            lines.append("### Python 依赖")
            for p in pip:
                lines.append(f"- `{p}`")
            lines.append("")
        if npm:
            lines.append("### Node.js 依赖")
            for p in npm:
                lines.append(f"- `{p}`")
            lines.append("")
        if not pip and not npm:
            lines.append("_未检测到额外测试依赖_")
        cmds = deps_manifest.get("install_commands", {})
        if cmds:
            lines.append("### 安装命令")
            for lang, cmd in cmds.items():
                lines.append(f"```\n{cmd}\n```")
        return "\n".join(lines)

    def format_test_report(self, test_results: dict, install_result: dict) -> str:
        passed = test_results.get("passed", 0)
        total = test_results.get("total", 0)
        ran = test_results.get("ran", False)
        lines = [
            "## 测试报告",
            "",
            f"- 总计: {total} 项测试",
            f"- 通过: {passed} ✅",
            f"- 失败: {test_results.get('failed', 0)} ❌",
            f"- 代码覆盖率: {test_results.get('coverage', 'N/A')}%",
        ]
        if not ran:
            lines.append("\n> ⚠️ 测试未能执行（环境问题），请人工确认")
        if install_result.get("errors"):
            lines.append("\n### 安装错误")
            for err in install_result["errors"]:
                lines.append(f"- {err}")
        if test_results.get("errors"):
            lines.append("\n### 失败用例")
            for err in test_results["errors"]:
                lines.append(f"- {err}")
        return "\n".join(lines)

    def _format_report(self, results: dict) -> str:
        """Kept for backward compatibility."""
        return self.format_test_report(results, {})

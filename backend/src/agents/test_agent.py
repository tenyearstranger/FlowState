from __future__ import annotations

"""测试验证 Agent"""

from .base_agent import BaseAgent, AgentInput, AgentOutput
from typing import Dict
import json
import re
import subprocess
from pathlib import Path
import shutil
import os
import sys


class TestAgent(BaseAgent):
    """
    测试验证 Agent
    职责：为生成的代码编写并执行测试，输出测试报告
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {})
        project_summary = input_data.context.get("project_summary", "")
        project_path = input_data.context.get("project_path", "")
        feedback = input_data.human_feedback

        test_files, test_results, token_usage, model = await self._llm_generate_tests(
            code_files,
            project_summary,
            feedback,
        )
        execution_results = self._run_generated_tests(
            project_path=project_path,
            code_files=code_files,
            test_files=test_files,
        )
        if execution_results is not None:
            test_results.update(execution_results)

        passed = test_results.get("passed", 0)
        total = test_results.get("total", 0)
        executed = bool(test_results.get("executed", False))
        all_pass = executed and passed == total and total > 0

        return AgentOutput(
            success=all_pass,
            result={
                "test_files": test_files,
                "test_results": test_results,
                "report": self._format_report(test_results),
                "pass_rate": f"{passed}/{total}",
            },
            summary=f"测试完成：{passed}/{total} 通过",
            details=self._format_report(test_results),
            needs_human_review=not all_pass,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_generate_tests(
        self,
        code_files: Dict[str, str],
        project_summary: str,
        feedback: str | None,
    ) -> tuple:
        """调用 LLM 生成测试代码"""
        code_summary = "\n\n".join(
            f"=== {path} ===\n{content[:500]}"
            for path, content in code_files.items()
        )

        user_message = f"""请为以下代码编写全面的单元测试。

代码文件清单：
{code_summary}

项目摘要：
{project_summary or "未提供"}

要求：
1. 为每个关键模块编写测试
2. 根据项目技术栈选择合适测试框架，不要默认假设是 FastAPI
3. 测试应包括：正常路径、异常路径、边界条件
4. 每个测试文件必须按标签格式返回
5. 如果你没有真实执行测试，请在结果 JSON 中明确标记 executed=false，不要虚构 passed/failed

输出格式：
先返回一个或多个测试文件块：
<test_file path="tests/<filepath>">
完整测试代码
</test_file>

最后返回一个 JSON 对象，字段包含：
- total
- passed
- failed
- coverage
- errors
- executed

不要输出 Markdown 代码块，不要解释。
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        llm_response = await self.call_llm_response(
            user_message,
            sanitize_output=False,
            use_stop_tokens=False,
        )
        response = llm_response.content

        # 解析测试文件
        test_files = self._parse_test_files(response)

        # 解析测试结果
        test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "coverage": 0,
            "executed": False,
        }
        try:
            parsed = self._extract_json_object(response)
            if parsed is not None:
                test_results.update(parsed)
        except Exception:
            pass

        if not test_files:
            test_files = {
                "tests/test_app.py": f'# Auto-generated tests\n# Review required before running\n"""\n{response[:1000]}\n"""\n',
            }
            test_results["errors"] = test_results.get("errors", []) + ["未解析到结构化测试文件，已生成人工检查占位测试"]
        if not test_results.get("executed", False):
            test_results["errors"] = test_results.get("errors", []) + ["测试结果未经过真实执行验证，需人工或外部 runner 复核"]

        return test_files, test_results, llm_response.usage, llm_response.model

    def _run_generated_tests(
        self,
        *,
        project_path: str,
        code_files: Dict[str, str],
        test_files: dict[str, str],
    ) -> dict | None:
        project_dir = Path(project_path).expanduser().resolve() if project_path else None
        if project_dir is None or not project_dir.exists() or not project_dir.is_dir():
            return {
                "executed": False,
                "errors": ["缺少有效项目目录，无法真实执行测试"],
            }

        written_files = self._write_test_files(project_dir, test_files)
        bootstrap_errors = self._prepare_test_environment(project_dir, code_files)
        if bootstrap_errors and any("依赖安装失败" in error or "无法创建或定位项目 Python 虚拟环境" in error for error in bootstrap_errors):
            return {
                "total": 0,
                "passed": 0,
                "failed": len(test_files) or 1,
                "coverage": 0,
                "errors": bootstrap_errors,
                "executed": False,
            }
        command = self._detect_test_command(project_dir, code_files)
        if command is None:
            return {
                "executed": False,
                "errors": bootstrap_errors + ["未识别到可执行的测试命令，请手动运行测试"],
            }

        try:
            completed = subprocess.run(
                command,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                shell=False,
            )
        except Exception as error:
            return {
                "executed": False,
                "errors": [f"测试命令执行失败: {error}"],
            }

        output = "\n".join(
            part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
        ).strip()
        summary = self._summarize_execution(
            command=command,
            return_code=completed.returncode,
            output=output,
            fallback_total=len(written_files) or len(test_files),
        )
        if bootstrap_errors:
            summary["errors"] = bootstrap_errors + list(summary.get("errors", []))
        return summary

    def _prepare_test_environment(
        self,
        project_dir: Path,
        code_files: Dict[str, str],
    ) -> list[str]:
        errors: list[str] = []
        if (project_dir / "requirements.txt").exists():
            python_cmd = self._ensure_project_python(project_dir)
            if python_cmd is None:
                return ["无法创建或定位项目 Python 虚拟环境"]

            install_command = [python_cmd, "-m", "pip", "install", "-r", "requirements.txt"]
            try:
                completed = subprocess.run(
                    install_command,
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                    shell=False,
                )
            except Exception as error:
                return [f"依赖安装失败: {error}"]

            if completed.returncode != 0:
                output = "\n".join(
                    part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
                ).strip()
                errors.append(f"依赖安装失败（exit={completed.returncode}）")
                errors.extend(self._extract_output_errors(output))

        return errors

    def _ensure_project_python(self, project_dir: Path) -> str | None:
        venv_python = self._project_venv_python(project_dir)
        if venv_python.exists():
            return str(venv_python)

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "venv", ".venv"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                shell=False,
            )
        except Exception:
            return None

        if completed.returncode != 0 or not venv_python.exists():
            return None
        return str(venv_python)

    def _project_venv_python(self, project_dir: Path) -> Path:
        if os.name == "nt":
            return project_dir / ".venv" / "Scripts" / "python.exe"
        return project_dir / ".venv" / "bin" / "python"

    def _write_test_files(self, project_dir: Path, test_files: dict[str, str]) -> list[Path]:
        written_files: list[Path] = []
        for relative_path, content in test_files.items():
            normalized = relative_path.strip().lstrip("/").replace("\\", "/")
            if not normalized or ".." in Path(normalized).parts:
                continue
            target_path = project_dir / normalized
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            written_files.append(target_path)
        return written_files

    def _detect_test_command(
        self,
        project_dir: Path,
        code_files: Dict[str, str],
    ) -> list[str] | None:
        project_python = self._project_venv_python(project_dir)
        if (project_dir / "package.json").exists():
            npm_cmd = self._resolve_executable("npm", project_dir)
            if npm_cmd:
                return [npm_cmd, "test"]

        if (project_dir / "pyproject.toml").exists():
            pytest_cmd = self._resolve_executable("pytest", project_dir)
            if project_python.exists():
                return [str(project_python), "-m", "pytest", "-q"]
            if pytest_cmd:
                return [pytest_cmd, "-q"]

        if (project_dir / "requirements.txt").exists():
            pytest_cmd = self._resolve_executable("pytest", project_dir)
            if project_python.exists():
                return [str(project_python), "-m", "pytest", "-q"]
            if pytest_cmd:
                return [pytest_cmd, "-q"]

        if any(path.endswith(".py") for path in code_files):
            pytest_cmd = self._resolve_executable("pytest", project_dir)
            if project_python.exists():
                return [str(project_python), "-m", "pytest", "-q"]
            if pytest_cmd:
                return [pytest_cmd, "-q"]

        return None

    def _resolve_executable(self, executable: str, project_dir: Path) -> str | None:
        candidates: list[str] = []

        if os.name == "nt":
            candidates.extend(
                [
                    f"{executable}.cmd",
                    f"{executable}.exe",
                    f"{executable}.bat",
                    executable,
                ]
            )
        else:
            candidates.append(executable)

        local_bin = project_dir / "node_modules" / ".bin"
        for candidate in candidates:
            local_candidate = local_bin / candidate
            if local_candidate.exists():
                return str(local_candidate)

        for candidate in candidates:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        return None

    def _summarize_execution(
        self,
        *,
        command: list[str],
        return_code: int,
        output: str,
        fallback_total: int,
    ) -> dict:
        total = 0
        passed = 0
        failed = 0
        coverage = 0
        errors: list[str] = []

        pytest_match = re.search(
            r"(?:(\d+)\s+failed)?[, ]*\s*(?:(\d+)\s+passed)?",
            output,
            re.IGNORECASE,
        )
        if pytest_match:
            failed = int(pytest_match.group(1) or 0)
            passed = int(pytest_match.group(2) or 0)
            total = failed + passed

        vitest_match = re.search(r"Tests?\s+(\d+)\s+failed.*?(\d+)\s+passed", output, re.IGNORECASE | re.DOTALL)
        if vitest_match:
            failed = int(vitest_match.group(1) or 0)
            passed = int(vitest_match.group(2) or 0)
            total = failed + passed
        else:
            vitest_pass_match = re.search(r"Tests?\s+(\d+)\s+passed", output, re.IGNORECASE)
            if vitest_pass_match and total == 0:
                passed = int(vitest_pass_match.group(1) or 0)
                total = passed

        coverage_match = re.search(r"coverage[^0-9]*(\d+)%", output, re.IGNORECASE)
        if coverage_match:
            coverage = int(coverage_match.group(1))

        if total == 0 and return_code == 0 and fallback_total > 0:
            total = fallback_total
            passed = fallback_total
            failed = 0

        if return_code != 0:
            if total == 0:
                total = fallback_total
                failed = fallback_total or 1
                passed = 0
            errors.append(
                f"测试命令失败（exit={return_code}）: {' '.join(command)}"
            )

        if output:
            errors.extend(self._extract_output_errors(output))

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "coverage": coverage,
            "errors": errors,
            "executed": True,
        }

    def _extract_output_errors(self, output: str) -> list[str]:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            return []
        tail = lines[-8:]
        return tail[:4]

    def _parse_test_files(self, response: str) -> dict[str, str]:
        test_files: dict[str, str] = {}

        tagged_pattern = re.compile(
            r'<test_file\s+path="([^"]+)">\s*(.*?)\s*</test_file>',
            re.DOTALL,
        )
        for filepath, content in tagged_pattern.findall(response):
            path = filepath.strip()
            body = content.strip()
            if path and body:
                test_files[path] = body

        if test_files:
            return test_files

        fenced_pattern = re.compile(r'```(tests/\S[^\n]*)\n(.*?)```', re.DOTALL)
        for filepath, content in fenced_pattern.findall(response):
            path = filepath.strip()
            body = content.strip()
            if path and body:
                test_files[path] = body

        return test_files

    def _extract_json_object(self, response: str) -> dict | None:
        if "```json" in response:
            try:
                json_str = response.split("```json", 1)[1].split("```", 1)[0].strip()
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            parsed = json.loads(response[start:end + 1])
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _format_report(self, results: dict) -> str:
        lines = [
            "## 测试报告",
            "",
            f"- 总计: {results['total']} 项测试",
            f"- 通过: {results['passed']} ✅",
            f"- 失败: {results['failed']} ❌",
            f"- 代码覆盖率: {results.get('coverage', 'N/A')}%",
        ]
        if results.get("errors"):
            lines.append("\n### 错误详情")
            for err in results["errors"]:
                lines.append(f"- {err}")
        return "\n".join(lines)

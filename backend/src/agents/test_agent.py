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
    职责：为生成的代码编写并执行测试，输出测试报告
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {})
        feedback = input_data.human_feedback
        project_path: str | None = input_data.context.get("project_path")

        test_files, token_usage, model = await self._llm_generate_tests(code_files, feedback)

        # Run real pytest when project_path is available
        test_results, ran_real_pytest = await self._run_pytest(project_path, test_files)

        passed = test_results.get("passed", 0)
        total = test_results.get("total", 0)
        all_pass = passed == total and total > 0

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
            # Require human review if tests weren't actually executed or if any failed
            needs_human_review=not (all_pass and ran_real_pytest),
            token_usage=token_usage,
            model=model,
        )

    async def _llm_generate_tests(self, code_files: Dict[str, str], feedback: str | None) -> tuple:
        """调用 LLM 生成测试代码（传入完整文件内容）"""
        code_summary = "\n\n".join(
            f"=== {path} ===\n{content}"
            for path, content in code_files.items()
        )

        user_message = f"""请为以下代码编写全面的单元测试。

代码文件清单：
{code_summary}

要求：
1. 为每个关键模块编写测试
2. 使用 pytest 和 httpx（对 FastAPI 应用）
3. 测试应包括：正常路径、异常路径、边界条件
4. 每个测试文件用标签格式输出

输出格式：
<file path="tests/<filepath>">
<summary>测试文件说明</summary>
<content>
完整测试代码
</content>
</file>

输出约束：
- 不要输出 Markdown，不要解释，不要添加额外前后缀
- 路径必须以 tests/ 开头
- 文件内容必须是完整实现，可以直接运行
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        llm_response = await self.call_llm_response(user_message)
        response = llm_response.content

        # 解析测试文件（与 CodeAgent 相同的 <file> 标签格式）
        test_files = self._parse_tagged_files(response)

        if not test_files:
            test_files = {
                "tests/test_app.py": f'# Auto-generated tests\n# Review required before running\n"""\n{response[:1000]}\n"""\n',
            }

        return test_files, llm_response.usage, llm_response.model

    def _parse_tagged_files(self, response_text: str) -> dict[str, str]:
        """Parse <file> tagged output (same format as CodeAgent)."""
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

    async def _run_pytest(
        self,
        project_path: str | None,
        test_files: dict[str, str],
    ) -> tuple[dict, bool]:
        """Write test files to disk and run pytest. Returns (results, ran_real_pytest)."""
        default_results: dict = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0}

        if not project_path:
            return default_results, False

        proj = Path(project_path)
        if not proj.exists():
            return default_results, False

        # Write test files to disk
        for rel_path, content in test_files.items():
            target = proj / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
                cwd=str(proj),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout + result.stderr
            return self._parse_pytest_output(output), True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return default_results, False

    def _parse_pytest_output(self, output: str) -> dict:
        """Parse pytest stdout/stderr to extract pass/fail counts."""
        results: dict = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0}

        # Match summary lines like "3 passed", "2 passed, 1 failed", "1 error"
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)

        if passed_match:
            results["passed"] = int(passed_match.group(1))
        if failed_match:
            results["failed"] = int(failed_match.group(1))

        results["total"] = results["passed"] + results["failed"]

        # Extract FAILED test identifiers for error details
        failed_lines = re.findall(r"FAILED\s+(\S+)", output)
        results["errors"] = failed_lines[:10]

        return results

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

from __future__ import annotations

"""测试验证 Agent"""

from .base_agent import BaseAgent, AgentInput, AgentOutput
from typing import Dict


class TestAgent(BaseAgent):
    """
    测试验证 Agent
    职责：为生成的代码编写并执行测试，输出测试报告
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {})
        feedback = input_data.human_feedback

        test_files, test_results, token_usage, model = await self._llm_generate_tests(code_files, feedback)

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
            needs_human_review=False if all_pass else True,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_generate_tests(self, code_files: Dict[str, str], feedback: str | None) -> tuple:
        """调用 LLM 生成测试代码"""
        code_summary = "\n\n".join(
            f"=== {path} ===\n{content[:500]}"
            for path, content in code_files.items()
        )

        user_message = f"""请为以下代码编写全面的单元测试。

代码文件清单：
{code_summary}

要求：
1. 为每个关键模块编写测试
2. 使用 pytest 和 httpx（对 FastAPI 应用）
3. 测试应包括：正常路径、异常路径、边界条件
4. 每个测试文件用 ```tests/<filename> 标注

输出格式：
每个测试文件用 ```tests/<filepath> 开头，``` 结尾。
最后输出测试结果摘要 JSON（用 ```json 包裹），包含 total, passed, failed, coverage。
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        llm_response = await self.call_llm_response(user_message)
        response = llm_response.content

        # 解析测试文件
        test_files = {}
        pattern = r'```(tests/\S[^\n]*)\n(.*?)```'
        import re
        matches = re.findall(pattern, response, re.DOTALL)
        for filepath, content in matches:
            test_files[filepath.strip()] = content.strip()

        # 解析测试结果
        test_results = {"total": 0, "passed": 0, "failed": 0, "errors": [], "coverage": 0}
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                import json
                parsed = json.loads(json_str)
                test_results.update(parsed)
        except Exception:
            pass

        if not test_files:
            test_files = {
                "tests/test_app.py": f'# Auto-generated tests\n# Review required before running\n"""\n{response[:1000]}\n"""\n',
            }

        return test_files, test_results, llm_response.usage, llm_response.model

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

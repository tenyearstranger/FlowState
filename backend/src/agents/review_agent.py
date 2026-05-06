from __future__ import annotations

"""代码评审 Agent"""

import json
from .base_agent import BaseAgent, AgentInput, AgentOutput
from typing import Dict


class ReviewAgent(BaseAgent):
    """
    代码评审 Agent
    职责：审查代码质量、安全性、最佳实践，输出评审报告
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {})
        test_report = input_data.context.get("test_report", "")
        project_summary = input_data.context.get("project_summary", "")
        feedback = input_data.human_feedback

        review, token_usage, model = await self._llm_review(
            code_files,
            test_report,
            project_summary,
            feedback,
        )

        issues = review.get("issues", [])
        critical = sum(1 for i in issues if i["severity"] == "critical")

        return AgentOutput(
            success=critical == 0,
            result={
                "review": review,
                "report": self._format_review(review),
                "issues": issues,
                "score": review.get("score", 0),
            },
            summary=f"评审完成：评分 {review.get('score', 0)}/100，发现 {len(issues)} 个问题",
            details=self._format_review(review),
            needs_human_review=True,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_review(
        self,
        code_files: Dict[str, str],
        test_report: str,
        project_summary: str,
        feedback: str | None,
    ) -> tuple[dict, dict[str, int] | None, str]:
        """调用 LLM 进行代码评审"""
        code_summary = "\n\n".join(
            f"=== {path} ===\n{content[:800]}"
            for path, content in code_files.items()
        )

        user_message = f"""请对以下代码进行全面评审。

代码文件：
{code_summary}

测试报告：
{test_report}

项目摘要：
{project_summary or "未提供"}

请输出 JSON 格式的评审报告，包含以下字段：
1. score: 0-100 的评分
2. summary: 总体评价
3. strengths: 优点列表
4. issues: 问题列表（每个问题包含 file, line, severity, message）
5. suggestions: 改进建议列表

严重级别：critical / high / medium / low

约束：
- 只报告能从给定代码、测试报告、项目摘要中直接推断的问题
- 如果证据不足，不要虚构具体 API、构建配置或安全漏洞
- line 字段无法确定时填 0

只输出 JSON，不要其他内容。
"""

        if feedback:
            user_message += f"\n\n根据以下反馈调整评审：\n{feedback}"

        try:
            parsed, llm_response = await self.call_llm_json_response(user_message)
            return parsed, llm_response.usage, llm_response.model
        except ValueError:
            return {
                "score": 0,
                "summary": "评审结果解析失败，无法给出可靠结论",
                "strengths": [],
                "issues": [{"file": "unknown", "line": 0, "severity": "high", "message": "评审输出无法解析，请人工复核"}],
                "suggestions": ["重新执行评审或人工审核"],
            }, None, self.model_name

    def _format_review(self, review: dict) -> str:
        lines = [
            "## 代码评审报告",
            "",
            f"**评分: {review['score']}/100**",
            f"**总体评价: {review['summary']}**",
            "",
            "### ✅ 优点",
        ]
        for s in review["strengths"]:
            lines.append(f"- {s}")

        lines.append("\n### ⚠️ 问题清单")
        for issue in review["issues"]:
            sev_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
            }
            icon = sev_icon.get(issue["severity"], "⚪")
            lines.append(
                f"- {icon} [{issue['severity']}] {issue['file']}:{issue['line']} "
                f"— {issue['message']}"
            )

        lines.append("\n### 💡 改进建议")
        for s in review["suggestions"]:
            lines.append(f"- {s}")

        return "\n".join(lines)

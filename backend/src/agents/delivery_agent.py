from __future__ import annotations

"""交付部署 Agent"""

from .base_agent import BaseAgent, AgentInput, AgentOutput
from typing import Dict
from datetime import datetime


class DeliveryAgent(BaseAgent):
    """
    交付部署 Agent
    职责：打包变更、生成 PR/变更日志、准备部署配置
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {})
        review_report = input_data.context.get("review_report", "")
        project_summary = input_data.context.get("project_summary", "")
        feedback = input_data.human_feedback

        delivery, token_usage, model = await self._llm_prepare_delivery(
            code_files,
            review_report,
            project_summary,
            feedback,
        )

        return AgentOutput(
            success=True,
            result={
                **delivery,
                "result": self._format_delivery(delivery),
            },
            summary=(
                f"交付就绪：生成 PR #{delivery['pr_number']}，"
                f"变更 {delivery['changes']} 个文件"
            ),
            details=self._format_delivery(delivery),
            needs_human_review=True,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_prepare_delivery(
        self,
        code_files: Dict[str, str],
        review_report: str,
        project_summary: str,
        feedback: str | None,
    ) -> tuple[dict, dict[str, int] | None, str]:
        """调用 LLM 准备交付"""
        file_list = "\n".join(f"- `{p}`" for p in code_files)
        package_json = code_files.get("package.json", "")

        user_message = f"""请准备代码交付所需的信息。

变更文件清单：
{file_list}

评审报告：
{review_report[:500]}

项目摘要：
{project_summary or "未提供"}

package.json（如存在）：
{package_json[:1500] or "未提供"}

请输出 JSON 格式（只输出 JSON）：
1. pr_title: PR 标题
2. pr_description: PR 描述（Markdown 格式，包含变更说明和验证步骤）
3. branch: 功能分支名
4. commit_message: Git 提交信息
5. deployment_command: 部署命令

约束：
- deployment_command 必须尽量基于 package.json 脚本或已知文件推断
- 若无法可靠判断部署命令，请输出 "manual verification required"
"""

        if feedback:
            user_message += f"\n\n根据以下反馈调整：\n{feedback}"

        try:
            parsed, llm_response = await self.call_llm_json_response(user_message)
        except ValueError:
            parsed = {}
            llm_response = None
        parsed["changes"] = len(code_files)
        parsed["files_changed"] = list(code_files.keys())
        parsed["pr_number"] = parsed.get("pr_number", 1)
        parsed["generated_at"] = datetime.now().isoformat()
        parsed.setdefault("pr_title", "feat: 自动生成代码")
        parsed.setdefault("pr_description", "基于 FlowState 流水线自动生成的代码。")
        parsed.setdefault("branch", "feature/auto-gen")
        parsed.setdefault("commit_message", "feat: auto-generate code via FlowState")
        parsed.setdefault("deployment_command", "manual verification required")
        return parsed, getattr(llm_response, "usage", None), getattr(llm_response, "model", self.model_name)

    def _format_delivery(self, delivery: dict) -> str:
        lines = [
            "## 📦 交付汇总",
            "",
            f"**PR 编号:** #{delivery['pr_number']}",
            f"**标题:** {delivery['pr_title']}",
            f"**分支:** {delivery['branch']}",
            f"**变更文件数:** {delivery['changes']}",
            "",
            "### 变更文件清单",
        ]
        for f in delivery["files_changed"]:
            lines.append(f"- `{f}`")

        lines.extend([
            "",
            "### 部署命令",
            f"```bash\n{delivery['deployment_command']}\n```",
            "",
            "### 提交信息",
            f"```\n{delivery['commit_message']}\n```",
        ])
        return "\n".join(lines)

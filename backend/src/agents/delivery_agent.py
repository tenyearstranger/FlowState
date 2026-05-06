from __future__ import annotations

"""交付部署 Agent"""

import json
from .base_agent import BaseAgent, AgentInput, AgentOutput
from typing import Dict
from datetime import datetime


class DeliveryAgent(BaseAgent):
    """
    交付部署 Agent
    职责：打包变更、生成 PR/变更日志、准备部署配置
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        code_files = input_data.context.get("generated_code", {}) or {}
        review_report = input_data.context.get("review_report", "") or ""
        test_report = input_data.context.get("test_report", "") or ""
        requirement_doc = input_data.context.get("requirement_doc", "") or ""
        solution_doc = input_data.context.get("solution_doc", "") or ""
        code_diff = input_data.context.get("code_diff", "") or ""
        feedback = input_data.human_feedback

        delivery, token_usage, model = await self._llm_prepare_delivery(
            code_files=code_files,
            review_report=review_report,
            test_report=test_report,
            requirement_doc=requirement_doc,
            solution_doc=solution_doc,
            code_diff=code_diff,
            feedback=feedback,
        )

        return AgentOutput(
            success=True,
            result={
                **delivery,
                "result": self._format_delivery(delivery),
            },
            summary=f"交付就绪：{delivery['pr_title']}，变更 {delivery['changes']} 个文件",
            details=self._format_delivery(delivery),
            needs_human_review=True,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_prepare_delivery(
        self,
        *,
        code_files: Dict[str, str],
        review_report: str,
        test_report: str,
        requirement_doc: str,
        solution_doc: str,
        code_diff: str,
        feedback: str | None,
    ) -> tuple[dict, dict[str, int] | None, str]:
        """调用 LLM 准备交付信息"""
        file_list = "\n".join(f"- `{p}`" for p in code_files)

        user_message = f"""请为以下代码变更准备 PR 交付信息。

## 需求摘要
{requirement_doc[:600]}

## 技术方案摘要
{solution_doc[:400]}

## 变更文件（共 {len(code_files)} 个）
{file_list}

## 代码 Diff（摘要）
{code_diff[:3000] or "（无 diff，直接由文件清单描述变更）"}

## 测试报告
{test_report[:600] or "（无测试报告）"}

## 代码评审报告
{review_report[:600] or "（无评审报告）"}

请输出 JSON（只输出 JSON，不要任何解释）：
{{
  "pr_title": "简明的 PR 标题（feat/fix/refactor: 简短描述，不超过 72 字符）",
  "pr_description": "完整的 PR 描述（Markdown 格式）：\\n## 变更内容\\n## 测试验证\\n## 评审结论\\n## 如何验证",
  "commit_message": "git commit 信息（Conventional Commits 格式）",
  "changelog": "CHANGELOG 条目（Markdown 格式，简短列出主要变更）",
  "deployment_notes": "部署注意事项（如无特殊要求填 无）"
}}"""

        if feedback:
            user_message += f"\n\n根据以下反馈调整：\n{feedback}"

        llm_response = await self.call_llm_response(user_message, expect_json=True)
        response = llm_response.content
        try:
            raw = response.strip()
            if raw.startswith("```"):
                import re
                raw = re.sub(r"^```[a-z]*\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
        except (json.JSONDecodeError, Exception):
            parsed = {}

        parsed["changes"] = len(code_files)
        parsed["files_changed"] = list(code_files.keys())
        parsed["generated_at"] = datetime.now().isoformat()
        parsed.setdefault("pr_title", "feat: AI 自动生成代码变更")
        parsed.setdefault("pr_description", "基于 FlowState 流水线自动生成的代码变更。")
        parsed.setdefault("commit_message", "feat: auto-generate code via FlowState")
        parsed.setdefault("changelog", f"- 自动生成 {len(code_files)} 个文件的代码变更")
        parsed.setdefault("deployment_notes", "无特殊部署要求")
        return parsed, llm_response.usage, llm_response.model

    def _format_delivery(self, delivery: dict) -> str:
        lines = [
            "## 📦 交付汇总",
            "",
            f"**PR 标题:** {delivery.get('pr_title', '（未生成）')}",
            f"**变更文件数:** {delivery.get('changes', 0)}",
            f"**生成时间:** {delivery.get('generated_at', '')}",
            "",
        ]

        files_changed = delivery.get("files_changed", [])
        if files_changed:
            lines.append("### 变更文件清单")
            for f in files_changed:
                lines.append(f"- `{f}`")
            lines.append("")

        commit_message = delivery.get("commit_message", "")
        if commit_message:
            lines.extend([
                "### 提交信息",
                f"```\n{commit_message}\n```",
                "",
            ])

        changelog = delivery.get("changelog", "")
        if changelog:
            lines.extend([
                "### CHANGELOG",
                changelog,
                "",
            ])

        deployment_notes = delivery.get("deployment_notes", "")
        if deployment_notes and deployment_notes.strip() not in ("无", "无特殊部署要求"):
            lines.extend([
                "### 部署注意事项",
                deployment_notes,
                "",
            ])

        pr_description = delivery.get("pr_description", "")
        if pr_description:
            lines.extend([
                "### PR 描述",
                pr_description,
            ])

        return "\n".join(lines)

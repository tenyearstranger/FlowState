"""需求分析 Agent"""

import json
from .base_agent import BaseAgent, AgentInput, AgentOutput


class RequirementAgent(BaseAgent):
    """
    需求分析 Agent
    职责：解析用户输入的原始需求，输出结构化 PRD 文档
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        raw = input_data.context.get("requirement_raw", "")
        feedback = input_data.human_feedback

        # 构建提示词
        user_message = f"""请分析以下原始需求，输出结构化的 PRD 文档。

原始需求：
{raw}

请按以下格式组织：
1. 业务目标
2. 功能清单（用列表列出所有功能点）
3. 用户故事
4. 验收标准
5. 模块划分（JSON 格式，包含模块名称和优先级 P0/P1/P2）

输出格式要求：
- PRD 文档用 Markdown 格式
- 在文档末尾，用 ```json 代码块输出模块划分 JSON
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        # 调用 LLM
        structured_doc = await self.call_llm(user_message)

        # 从文档中提取模块列表
        modules = self._extract_modules(structured_doc)

        return AgentOutput(
            success=True,
            result={
                "document": structured_doc,
                "raw_requirement": raw,
                "modules": modules,
            },
            summary=f"需求分析完成，识别出 {len(modules)} 个功能模块",
            details=structured_doc,
            needs_human_review=True,
        )

    # -------- 辅助方法 --------

    def _extract_modules(self, doc: str) -> list:
        """从文档中提取模块列表"""
        # 尝试从 ```json 代码块中提取
        try:
            if "```json" in doc:
                json_str = doc.split("```json")[1].split("```")[0].strip()
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict) and "modules" in parsed:
                    return parsed["modules"]
        except (json.JSONDecodeError, IndexError):
            pass

        # 默认 fallback
        return [
            {"name": "用户认证", "priority": "P0"},
            {"name": "核心业务逻辑", "priority": "P0"},
            {"name": "配置管理", "priority": "P1"},
        ]

"""方案设计 Agent"""

import json
from .base_agent import BaseAgent, AgentInput, AgentOutput


class SolutionAgent(BaseAgent):
    """
    方案设计 Agent
    职责：基于需求文档，设计技术方案（架构、API、数据模型）
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        req_doc = input_data.context.get("requirement_doc", "")
        feedback = input_data.human_feedback

        user_message = f"""请基于以下需求文档，设计完整的技术方案。

需求文档：
{req_doc}

请包含以下内容：
1. **整体架构** - 架构风格、前后端技术栈
2. **目录结构** - 项目文件和目录组织
3. **核心 API 设计** - 关键接口路径、方法、请求/响应格式
4. **数据模型** - 核心实体、字段和关系
5. **技术选型理由** - 为什么选择这些技术

输出格式：Markdown 文档。
在文档末尾，用 ```json 代码块输出 API 设计的 JSON 概览。
"""

        if feedback:
            user_message += f"\n\n根据以下反馈调整方案：\n{feedback}"

        solution = await self.call_llm(user_message)

        # 尝试提取架构和 tech_stack
        architecture, tech_stack = self._parse_solution(solution)

        return AgentOutput(
            success=True,
            result={
                "design": solution,
                "architecture": architecture,
                "tech_stack": tech_stack,
                "api_design": self._extract_api_design(solution),
            },
            summary=f"技术方案已生成：{' + '.join(tech_stack[:3])}",
            details=solution,
            needs_human_review=True,
        )

    def _parse_solution(self, solution: str) -> tuple:
        """从方案文档中解析架构描述和技术栈"""
        architecture = "前后端分离架构"
        tech_stack = ["Python FastAPI", "SQLite"]

        # 尝试从正文提取技术栈信息
        lines = solution.lower().split("\n")
        keywords = ["fastapi", "flask", "django", "react", "vue", "sqlite",
                    "postgresql", "mysql", "redis", "docker", "nginx"]
        found = []
        for kw in keywords:
            if any(kw in line for line in lines):
                found.append(kw.capitalize())
        if found:
            tech_stack = found[:5]

        return architecture, tech_stack

    def _extract_api_design(self, solution: str) -> dict:
        """从方案中提取 API 设计 JSON"""
        try:
            if "```json" in solution:
                json_str = solution.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
        return {"note": "API 设计嵌入在文档中"}

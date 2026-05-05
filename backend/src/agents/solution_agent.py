"""方案设计 Agent"""

from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseAgent, AgentInput, AgentOutput


class SolutionAgent(BaseAgent):
    """
    方案设计 Agent
    职责：基于需求文档，输出结构化技术方案文档
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        requirement_doc = input_data.context.get("requirement_doc", "")
        project_path = input_data.context.get("project_path", "")
        project_summary = input_data.context.get("project_summary", "")
        feedback = input_data.human_feedback
        requirement_summary = self._build_requirement_summary(requirement_doc)

        structured_payload = await self._generate_structured_payload(
            requirement_doc=requirement_summary,
            project_path=project_path,
            project_summary=project_summary,
            feedback=feedback,
        )
        structured_doc = self._render_markdown(
            payload=structured_payload,
            project_path=project_path,
            project_summary=project_summary,
            requirement_summary=requirement_summary,
        )
        api_design = self._normalize_apis(structured_payload.get("api_design"))
        tech_stack = self._normalize_string_list(structured_payload.get("tech_stack"))
        resolved_stack = self._normalize_stack(structured_payload.get("resolved_stack"))
        file_plan = self._normalize_file_plan(structured_payload.get("file_plan"))
        structured_payload["resolved_stack"] = resolved_stack
        structured_payload["file_plan"] = file_plan

        return AgentOutput(
            success=True,
            result={
                "design": structured_doc,
                "architecture": str(structured_payload.get("architecture_overview") or "").strip(),
                "tech_stack": tech_stack,
                "resolved_stack": resolved_stack,
                "file_plan": file_plan,
                "api_design": api_design,
                "structured_solution": structured_payload,
            },
            summary=f"技术方案已生成：{len(api_design)} 个核心接口，{len(file_plan)} 个目标文件",
            details=structured_doc,
            needs_human_review=True,
        )

    async def _generate_structured_payload(
        self,
        *,
        requirement_doc: str,
        project_path: str,
        project_summary: str,
        feedback: str | None,
    ) -> dict[str, Any]:
        user_message = f"""请基于以下需求文档和项目上下文，输出结构化技术方案 JSON。

需求文档：
{requirement_doc}

项目目录：
{project_path or "未提供"}

项目扫描摘要：
{project_summary or "未提供项目扫描摘要"}

请返回一个 JSON 对象，字段要求如下：
- "title": 方案标题，字符串
- "architecture_overview": 整体架构说明，字符串
- "tech_stack": 技术栈字符串数组
- "resolved_stack": 对象，必须包含：
  - "frontend": 前端技术栈
  - "backend": 后端技术栈
  - "database": 数据库技术
  - "state_management": 状态管理方案
  - "notifications": 通知/提醒方案
  - "testing": 测试技术栈
- "directory_structure": 对象数组，每项包含：
  - "path": 路径
  - "purpose": 作用说明
- "file_plan": 对象数组，每项包含：
  - "path": 相对文件路径
  - "layer": 所属层，例如 frontend/backend/shared/config
  - "purpose": 文件职责
  - "must_generate": 布尔值，必须为 true/false
- "api_design": 对象数组，每项包含：
  - "name": 接口名称
  - "method": HTTP 方法
  - "path": 接口路径
  - "description": 接口用途
  - "request": 请求要点
  - "response": 响应要点
- "data_models": 对象数组，每项包含：
  - "name": 模型名称
  - "description": 模型说明
  - "fields": 对象数组，每项包含 "name"、"type"、"required"、"description"
- "technical_rationale": 字符串数组
- "risks": 字符串数组
- "open_questions": 字符串数组

输出约束：
- 只返回 JSON 对象，不要解释，不要输出 Markdown
- 缺失字段请返回空数组或空字符串，不要省略
- 请基于真实产品建设思路给出可执行方案，不要复述“生成文档流程”本身
- `file_plan` 必须给出 stage3 需要实际生成的具体文件，不能只写目录
- `file_plan` 请覆盖该方案需要落盘的完整文件集合，`must_generate` 只用于标识首批核心文件，不要为了迎合模型输出而刻意压缩文件数量
"""

        if feedback:
            user_message += f"\n\n请根据以下反馈修订方案：\n{feedback}"

        structured_json = await self.call_llm(
            user_message,
            expect_json=True,
            temperature=0.1,
        )
        parsed = json.loads(structured_json)
        if not isinstance(parsed, dict):
            raise ValueError("方案设计模型返回的结构不是 JSON 对象")
        return parsed

    def _render_markdown(
        self,
        *,
        payload: dict[str, Any],
        project_path: str,
        project_summary: str,
        requirement_summary: str,
    ) -> str:
        title = str(payload.get("title") or "技术方案文档").strip() or "技术方案文档"
        architecture = str(payload.get("architecture_overview") or "待补充整体架构设计。").strip()
        tech_stack = self._normalize_string_list(payload.get("tech_stack"))
        resolved_stack = self._normalize_stack(payload.get("resolved_stack"))
        directory_structure = self._normalize_directory_structure(payload.get("directory_structure"))
        file_plan = self._normalize_file_plan(payload.get("file_plan"))
        api_design = self._normalize_apis(payload.get("api_design"))
        data_models = self._normalize_data_models(payload.get("data_models"))
        technical_rationale = self._normalize_string_list(payload.get("technical_rationale"))
        risks = self._normalize_string_list(payload.get("risks"))
        open_questions = self._normalize_string_list(payload.get("open_questions"))

        sections = [
            "# 技术方案文档",
            "",
            "## 标题",
            title,
            "",
            "## 需求摘要",
            requirement_summary or "未提供需求摘要。",
            "",
            "## 项目上下文",
            f"- 项目目录：{project_path or '未提供'}",
            "",
            project_summary or "未提供项目扫描摘要。",
            "",
            "## 整体架构",
            architecture,
            "",
            "## 技术栈",
            *self._render_bullets(tech_stack, "待补充技术栈"),
            "",
            "## Stage3 使用的技术栈约束",
            f"- 前端：{resolved_stack['frontend']}",
            f"- 后端：{resolved_stack['backend']}",
            f"- 数据库：{resolved_stack['database']}",
            f"- 状态管理：{resolved_stack['state_management']}",
            f"- 通知方案：{resolved_stack['notifications']}",
            f"- 测试方案：{resolved_stack['testing']}",
            "",
            "## 目录结构",
        ]

        if directory_structure:
            for item in directory_structure:
                sections.append(f"- `{item['path']}`: {item['purpose']}")
        else:
            sections.append("- 待补充目录结构设计")

        sections.extend(["", "## Stage3 文件清单"])
        if file_plan:
            for item in file_plan:
                required_mark = "必须生成" if item["must_generate"] else "可选生成"
                sections.append(
                    f"- `{item['path']}` [{item['layer']}] {required_mark}: {item['purpose']}"
                )
        else:
            sections.append("- 待补充具体文件清单")

        sections.extend(["", "## 核心 API 设计"])
        if api_design:
            for api in api_design:
                sections.extend(
                    [
                        f"### {api['name']}",
                        f"- 方法：{api['method']}",
                        f"- 路径：`{api['path']}`",
                        f"- 用途：{api['description']}",
                        f"- 请求：{api['request']}",
                        f"- 响应：{api['response']}",
                        "",
                    ]
                )
        else:
            sections.extend(["- 待补充 API 设计", ""])

        sections.append("## 数据模型")
        if data_models:
            for model in data_models:
                sections.extend(
                    [
                        f"### {model['name']}",
                        model["description"] or "待补充模型说明。",
                        "",
                    ]
                )
                for field in model["fields"]:
                    required_mark = "必填" if field["required"] else "可选"
                    sections.append(
                        f"- `{field['name']}` ({field['type']}, {required_mark})：{field['description']}"
                    )
                sections.append("")
        else:
            sections.extend(["- 待补充数据模型设计", ""])

        sections.extend(
            [
                "## 技术选型理由",
                *self._render_bullets(technical_rationale, "待补充技术选型理由"),
                "",
                "## 风险与约束",
                *self._render_bullets(risks, "暂无明显风险"),
                "",
                "## 开放问题",
                *self._render_bullets(open_questions, "暂无开放问题"),
                "",
                "```json",
                json.dumps(
                    {
                        "resolved_stack": resolved_stack,
                        "file_plan": file_plan,
                        "api_design": api_design,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
            ]
        )

        return "\n".join(sections).strip()

    def _build_requirement_summary(self, requirement_doc: str) -> str:
        if not requirement_doc.strip():
            return "未提供需求文档。"

        sections_to_keep = ["## 标题", "## 业务目标", "## 功能清单", "## 验收标准", "## 模块划分"]
        lines = requirement_doc.splitlines()
        kept: list[str] = []
        current_header = None
        capture = False

        for line in lines:
            if line.startswith("## "):
                current_header = line.strip()
                capture = current_header in sections_to_keep
                if capture:
                    kept.append(current_header)
                continue
            if capture:
                kept.append(line)

        summary = "\n".join(kept).strip()
        return summary or requirement_doc[:1200]

    def _normalize_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    def _render_bullets(self, items: list[str], fallback: str) -> list[str]:
        if not items:
            return [f"- {fallback}"]
        return [f"- {item}" for item in items]

    def _normalize_directory_structure(self, value: Any) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        if not isinstance(value, list):
            return normalized
        for item in value:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "").strip()
            purpose = str(item.get("purpose") or "").strip()
            if path:
                normalized.append({"path": path, "purpose": purpose or "待补充说明"})
        return normalized

    def _normalize_apis(self, value: Any) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        if not isinstance(value, list):
            return normalized
        for item in value:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "未命名接口").strip()
            method = str(item.get("method") or "GET").strip().upper()
            path = str(item.get("path") or "/").strip()
            normalized.append(
                {
                    "name": name,
                    "method": method,
                    "path": path,
                    "description": str(item.get("description") or "").strip(),
                    "request": str(item.get("request") or "").strip() or "待补充请求体说明",
                    "response": str(item.get("response") or "").strip() or "待补充响应说明",
                }
            )
        return normalized

    def _normalize_stack(self, value: Any) -> dict[str, str]:
        defaults = {
            "frontend": "待补充前端技术栈",
            "backend": "待补充后端技术栈",
            "database": "待补充数据库方案",
            "state_management": "待补充状态管理方案",
            "notifications": "待补充通知方案",
            "testing": "待补充测试技术栈",
        }
        if not isinstance(value, dict):
            return defaults
        normalized = defaults.copy()
        for key in normalized:
            text = str(value.get(key) or "").strip()
            if text:
                normalized[key] = text
        return normalized

    def _normalize_file_plan(self, value: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        if not isinstance(value, list):
            return normalized
        for item in value:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "").strip()
            if not path:
                continue
            normalized.append(
                {
                    "path": path,
                    "layer": str(item.get("layer") or "shared").strip() or "shared",
                    "purpose": str(item.get("purpose") or "").strip() or "待补充文件职责",
                    "must_generate": bool(item.get("must_generate", True)),
                }
            )
        return normalized

    def _normalize_data_models(self, value: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        if not isinstance(value, list):
            return normalized
        for item in value:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            fields: list[dict[str, Any]] = []
            raw_fields = item.get("fields")
            if isinstance(raw_fields, list):
                for field in raw_fields:
                    if not isinstance(field, dict):
                        continue
                    field_name = str(field.get("name") or "").strip()
                    if not field_name:
                        continue
                    fields.append(
                        {
                            "name": field_name,
                            "type": str(field.get("type") or "string").strip(),
                            "required": bool(field.get("required", True)),
                            "description": str(field.get("description") or "").strip() or "待补充字段说明",
                        }
                    )
            normalized.append(
                {
                    "name": name,
                    "description": str(item.get("description") or "").strip(),
                    "fields": fields,
                }
            )
        return normalized

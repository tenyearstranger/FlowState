from __future__ import annotations

"""编码实现 Agent"""

import base64
import json
import re
import time
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent, AgentInput, AgentOutput


class CodeAgent(BaseAgent):
    """
    编码实现 Agent
    职责：基于技术方案中的 tech stack 与 file plan 生成多文件代码
    """

    BATCH_SIZE = 3
    MAX_BATCH_RETRIES = 3
    CONTEXT_FILE_MAX_CHARS = 1500

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        solution_doc = input_data.context.get("solution_doc", "")
        structured_solution = input_data.context.get("solution_structured", {}) or {}
        req_doc = input_data.context.get("requirement_doc", "")
        feedback = input_data.human_feedback

        files, token_usage, model = await self._llm_generate_code(
            solution=solution_doc,
            structured_solution=structured_solution,
            req=req_doc,
            feedback=feedback,
        )

        if not files:
            raise ValueError("代码生成未返回任何具体文件")

        resolved_stack = self._normalize_stack(structured_solution.get("resolved_stack"))

        return AgentOutput(
            success=True,
            result={
                "files": files,
                "structure": list(files.keys()),
                "language": resolved_stack["backend"],
                "framework": resolved_stack["frontend"],
                "resolved_stack": resolved_stack,
            },
            summary=f"代码生成完成，共 {len(files)} 个文件",
            details="\n".join(f"  ✅ {fname}" for fname in files),
            needs_human_review=False,
            token_usage=token_usage,
            model=model,
        )

    async def _llm_generate_code(
        self,
        *,
        solution: str,
        structured_solution: dict[str, Any],
        req: str,
        feedback: str | None,
    ) -> tuple[dict[str, str], dict[str, int] | None, str]:
        resolved_stack = self._normalize_stack(structured_solution.get("resolved_stack"))
        architecture = str(structured_solution.get("architecture_overview") or "").strip()
        api_design = structured_solution.get("api_design", [])
        data_models = structured_solution.get("data_models", [])
        file_plan = self._normalize_file_plan(structured_solution.get("file_plan"))
        if not file_plan:
            raise ValueError("缺少 stage2 产出的具体文件清单，无法进入代码生成")
        target_files = list(file_plan)
        if not target_files:
            raise ValueError("file_plan 中没有可生成的文件")

        generated_files: dict[str, str] = {}
        generated_paths: list[str] = []
        usage_totals = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        model_name = self.model_name
        total_batches = len(list(self._chunk_file_plan(target_files, self.BATCH_SIZE)))
        gen_start = time.time()

        print(
            f"\n{'='*60}\n"
            f"[CodeAgent] 开始生成代码\n"
            f"  文件总数: {len(target_files)}  批次大小: {self.BATCH_SIZE}  共 {total_batches} 批\n"
            f"  文件清单: {', '.join(f['path'] for f in target_files)}\n"
            f"{'='*60}"
        )

        for batch_index, batch in enumerate(self._chunk_file_plan(target_files, self.BATCH_SIZE), start=1):
            batch_files: dict[str, str] = {}
            pending_batch = list(batch)
            batch_file_names = ", ".join(item["path"] for item in pending_batch)
            print(f"\n[CodeAgent] ▶ Batch {batch_index}/{total_batches}: {batch_file_names}")
            batch_start = time.time()

            for retry_index in range(1, self.MAX_BATCH_RETRIES + 1):
                if retry_index > 1:
                    missing = ", ".join(item["path"] for item in pending_batch)
                    print(f"[CodeAgent]   ↻ 重试 {retry_index}/{self.MAX_BATCH_RETRIES}，缺失: {missing}")

                user_message = self._build_batch_prompt(
                    req=req,
                    solution=solution,
                    architecture=architecture,
                    resolved_stack=resolved_stack,
                    api_design=api_design,
                    data_models=data_models,
                    full_file_plan=file_plan,
                    current_batch=pending_batch,
                    generated_files=generated_files,
                    batch_index=batch_index,
                    total_batches=total_batches,
                    retry_index=retry_index,
                    feedback=feedback,
                )

                response = await self.call_llm_response(
                    user_message,
                    temperature=0.1,
                )
                response_text = response.content
                if response.usage:
                    for key in usage_totals:
                        usage_totals[key] += int(response.usage.get(key, 0) or 0)
                if response.model:
                    model_name = response.model

                new_files = self._parse_tagged_files(response_text)
                if not new_files:
                    try:
                        parsed = json.loads(response_text)
                        new_files = self._normalize_files(parsed, pending_batch)
                    except Exception as error:
                        if retry_index >= self.MAX_BATCH_RETRIES:
                            raise self._build_parse_error(response_text) from error
                        print(f"[CodeAgent]   ✗ 解析失败，将重试: {error}")
                        continue

                filtered_new_files = {
                    path: content
                    for path, content in new_files.items()
                    if any(item["path"] == path for item in pending_batch)
                }
                batch_files.update(filtered_new_files)
                generated_paths.extend(
                    path for path in filtered_new_files
                    if path not in generated_paths
                )
                pending_batch = [
                    item for item in batch
                    if item["path"] not in batch_files
                ]

                if not pending_batch:
                    break

            if pending_batch:
                missing_paths = ", ".join(item["path"] for item in pending_batch)
                raise ValueError(f"代码生成缺少目标文件: {missing_paths}")

            generated_files.update(batch_files)
            batch_elapsed = time.time() - batch_start
            tokens_so_far = usage_totals["total_tokens"]
            written = ", ".join(batch_files.keys())
            print(
                f"[CodeAgent]   ✅ Batch {batch_index}/{total_batches} 完成 "
                f"({batch_elapsed:.1f}s, 累计 {tokens_so_far} tokens)\n"
                f"            写入: {written}"
            )

        # Post-generation consistency review: fix cross-file import/interface mismatches
        print(f"\n[CodeAgent] 🔍 一致性检查（共 {len(generated_files)} 个文件）...")
        review_start = time.time()
        generated_files = await self._consistency_review(generated_files, usage_totals)
        print(f"[CodeAgent] ✅ 一致性检查完成 ({time.time() - review_start:.1f}s)")
        total_elapsed = time.time() - gen_start
        print(
            f"\n[CodeAgent] 🎉 代码生成全部完成！\n"
            f"  文件数: {len(generated_files)}  总耗时: {total_elapsed:.1f}s  "
            f"总 tokens: {usage_totals['total_tokens']}\n"
            f"{'='*60}\n"
        )

        final_usage = usage_totals if any(usage_totals.values()) else None
        return self._validate_required_files(generated_files, target_files), final_usage, model_name

    def _build_batch_prompt(
        self,
        *,
        req: str,
        solution: str,
        architecture: str,
        resolved_stack: dict[str, str],
        api_design: Any,
        data_models: Any,
        full_file_plan: list[dict[str, Any]],
        current_batch: list[dict[str, Any]],
        generated_files: dict[str, str],
        batch_index: int,
        total_batches: int,
        retry_index: int,
        feedback: str | None,
    ) -> str:
        user_message = f"""请基于以下需求文档、技术方案和既定文件清单，生成当前批次的完整可运行代码。

## 需求文档
{req}

## 技术方案
{solution}

## 架构概要
{architecture or "未提供架构概要"}

## 必须遵守的技术栈
{json.dumps(resolved_stack, ensure_ascii=False, indent=2)}

## 核心 API 设计
{json.dumps(api_design, ensure_ascii=False, indent=2)}

## 核心数据模型
{json.dumps(data_models, ensure_ascii=False, indent=2)}

## 全量文件计划（供你保持一致）
{json.dumps(full_file_plan, ensure_ascii=False, indent=2)}

## 当前需要生成的文件批次（第 {batch_index}/{total_batches} 批，第 {retry_index} 次尝试）
{json.dumps(current_batch, ensure_ascii=False, indent=2)}

## 已生成文件（供上下文参考，保持接口一致）
{self._build_files_context(generated_files, self.CONTEXT_FILE_MAX_CHARS)}

请按以下标签格式返回当前批次的每个文件：
<file path="相对文件路径">
<summary>该文件的作用</summary>
<content>
完整 UTF-8 文本文件内容
</content>
</file>

输出约束：
- 不要输出 Markdown，不要解释，不要添加额外前后缀
- 只返回当前批次要求生成的文件，不要省略
- 路径必须与当前批次 file_plan 对齐，不能返回 output.txt 之类的兜底文件
- 文件内容必须是完整实现，不能只写 TODO 或伪代码
- 优先使用 `content` 标签返回纯文本；仅在你无法直接输出文本时才使用 `content_base64`
- 控制文件体积，优先生成简洁实现：单文件建议不超过 140 行，避免长篇注释和重复样板
- 如果这是重试，请只补齐当前批次里尚未返回的文件
"""

        if feedback:
            user_message += f"\n\n请根据以下反馈修改：\n{feedback}"

        return user_message

    def _build_files_context(self, files: dict[str, str], max_chars: int) -> str:
        """Format already-generated files for inclusion in subsequent prompts."""
        if not files:
            return "（暂无已生成文件）"
        parts: list[str] = []
        for path, content in files.items():
            if len(content) > max_chars:
                body = content[:max_chars] + f"\n… (已截断，剩余 {len(content) - max_chars} 字符)"
            else:
                body = content
            parts.append(f"=== {path} ===\n{body}")
        return "\n\n".join(parts)

    async def _consistency_review(
        self,
        files: dict[str, str],
        usage_totals: dict[str, int],
    ) -> dict[str, str]:
        """LLM pass to fix cross-file import/interface mismatches after all files are generated."""
        if len(files) <= 1:
            return files

        file_summaries = self._build_files_context(files, self.CONTEXT_FILE_MAX_CHARS)
        user_message = f"""你是一位代码审查专家。以下是刚生成的全部文件，请检查它们之间是否存在不一致（如 import 路径错误、接口签名不匹配、变量名不统一、缺少必要 export 等），并输出修正后的完整文件。

## 所有生成文件
{file_summaries}

请按以下标签格式返回需要修正的文件（无需修正的文件可以省略）：
<file path="相对文件路径">
<summary>修正内容说明</summary>
<content>
修正后的完整文件内容
</content>
</file>

如果所有文件均一致无需修改，请只回复：ALL_CONSISTENT
"""
        response = await self.call_llm_response(user_message, temperature=0.1)
        if response.usage:
            for key in usage_totals:
                usage_totals[key] += int(response.usage.get(key, 0) or 0)

        response_text = response.content.strip()
        if response_text == "ALL_CONSISTENT":
            print("[CodeAgent]   → 所有文件一致，无需修正")
            return files

        fixes = self._parse_tagged_files(response_text)
        if fixes:
            print(f"[CodeAgent]   → 修正了 {len(fixes)} 个文件: {', '.join(fixes.keys())}")
        if fixes:
            # Only update files that already exist; don't let the review add new ones
            existing_fixes = {p: c for p, c in fixes.items() if p in files}
            return {**files, **existing_fixes}
        return files

    def _normalize_stack(self, value: Any) -> dict[str, str]:
        defaults = {
            "frontend": "unknown-frontend",
            "backend": "unknown-backend",
            "database": "unknown-database",
            "state_management": "unknown-state-management",
            "notifications": "unknown-notifications",
            "testing": "unknown-testing",
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

    def _chunk_file_plan(
        self,
        file_plan: list[dict[str, Any]],
        batch_size: int,
    ) -> list[list[dict[str, Any]]]:
        return [
            file_plan[index: index + batch_size]
            for index in range(0, len(file_plan), batch_size)
        ]

    def _normalize_files(
        self,
        parsed: Any,
        file_plan: list[dict[str, Any]],
    ) -> dict[str, str]:
        if not isinstance(parsed, dict):
            raise ValueError("代码生成模型返回的结构不是 JSON 对象")

        raw_files = parsed.get("files")
        if not isinstance(raw_files, list):
            raise ValueError("代码生成模型未返回 files 数组")

        files: dict[str, str] = {}
        for item in raw_files:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "").strip()
            encoded_content = str(item.get("content_base64") or "").strip()
            if not path or not encoded_content:
                continue
            try:
                content = base64.b64decode(encoded_content).decode("utf-8")
            except Exception as error:
                raise ValueError(f"文件 {path} 的 base64 内容无效: {error}") from error
            files[path] = content

        return self._validate_required_files(files, file_plan)

    def _parse_tagged_files(self, response_text: str) -> dict[str, str]:
        files: dict[str, str] = {}
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned_response)
            cleaned_response = re.sub(r"\s*```$", "", cleaned_response)
        pattern = re.compile(
            r"<file\s+path=[\"']([^\"']+)[\"']>\s*(?:<summary>.*?</summary>\s*)?<(?P<tag>content|content_base64)>\s*(?P<body>.*?)\s*</(?P=tag)>\s*</file>",
            re.DOTALL,
        )
        for match in pattern.finditer(cleaned_response):
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
                except Exception as error:
                    raise ValueError(f"文件 {path} 的 base64 内容无效: {error}") from error
            else:
                content = payload
            files[path] = content
        return files

    def _build_parse_error(self, response_text: str) -> ValueError:
        debug_path = Path("/tmp/flowstate-codeagent-last-response.txt")
        debug_path.write_text(response_text, encoding="utf-8")
        preview = response_text.strip().replace("\n", "\\n")[:400]
        return ValueError(
            "代码生成响应无法解析，既不是标签块也不是 JSON。"
            f" 已写入调试文件: {debug_path}；响应预览: {preview}"
        )

    def _validate_required_files(
        self,
        files: dict[str, str],
        file_plan: list[dict[str, Any]],
    ) -> dict[str, str]:
        missing = [
            item["path"]
            for item in file_plan
            if item["path"] not in files
        ]
        if missing:
            raise ValueError(f"代码生成缺少目标文件: {', '.join(missing)}")

        return files

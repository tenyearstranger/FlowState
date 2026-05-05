"""编码实现 Agent"""

import re
from typing import Dict
from .base_agent import BaseAgent, AgentInput, AgentOutput


class CodeAgent(BaseAgent):
    """
    编码实现 Agent
    职责：基于技术方案，生成完整的多文件代码
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        solution_doc = input_data.context.get("solution_doc", "")
        req_doc = input_data.context.get("requirement_doc", "")
        feedback = input_data.human_feedback

        files = await self._llm_generate_code(solution_doc, req_doc, feedback)

        return AgentOutput(
            success=True,
            result={
                "files": files,
                "structure": list(files.keys()),
                "language": "python",
                "framework": "fastapi",
            },
            summary=f"代码生成完成，共 {len(files)} 个文件",
            details="\n".join(f"  ✅ {fname}" for fname in files),
            needs_human_review=False,  # 代码生成后自动进入测试
        )

    async def _llm_generate_code(
        self, solution: str, req: str, feedback: str | None
    ) -> Dict[str, str]:
        """调用 LLM 生成多文件代码"""
        user_message = f"""请基于以下技术方案和需求文档，生成完整可运行的代码。

## 技术方案
{solution}

## 需求文档
{req}

要求：
1. 生成多文件代码，每个文件用 ```filename 标注文件名
2. 代码应完整可运行，包含必要的 import 和类型注解
3. 包含 requirements.txt（如用 Python）或 package.json（如用 Node.js）
4. 代码中不要包含 TODO 占位，给出完整实现

输出格式：
每个文件用 ```<filepath> 开头，``` 结尾。
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        response = await self.call_llm(user_message)
        return self._parse_files(response)

    def _parse_files(self, response: str) -> Dict[str, str]:
        """从 LLM 响应中解析多文件代码"""
        files = {}
        # 匹配 ```filepath ... ``` 代码块
        pattern = r'```(\S[^\n]*)\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)

        for filepath, content in matches:
            filepath = filepath.strip()
            # 清理可能的语言标识（如 ```python app/main.py → app/main.py）
            parts = filepath.split(maxsplit=1)
            if len(parts) > 1:
                lang_keywords = {"python", "javascript", "typescript", "java", "go", "rust", "bash", "dockerfile", "yaml", "json", "html", "css", "js", "ts", "py", "rs", "go"}
                if parts[0].lower() in lang_keywords:
                    filepath = parts[1]
            files[filepath] = content.strip()

        # 如果正则没匹配到，尝试逐行解析
        if not files:
            lines = response.split("\n")
            current_file = None
            current_content = []
            for line in lines:
                if line.startswith("```") and len(line) > 3:
                    if current_file:
                        files[current_file] = "\n".join(current_content).strip()
                    current_file = line[3:].strip()
                    current_content = []
                elif line.strip() == "```":
                    if current_file:
                        files[current_file] = "\n".join(current_content).strip()
                        current_file = None
                        current_content = []
                elif current_file:
                    current_content.append(line)

        return files if files else {"output.txt": response}

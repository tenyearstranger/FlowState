"""
FlowState 全局配置

集中管理所有 API 配置、模型参数、默认行为。
支持：
1. 环境变量加载（12-Factor App 风格）
2. 配置文件加载（YAML/JSON）
3. 合理的默认值（开箱即用 DeepSeek）
"""

from __future__ import annotations

import os
import json
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================================
# 枚举定义
# ============================================================================

class LLMProvider(str, Enum):
    """支持的 LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"            # 本地部署（如 Ollama / vLLM）


class OutputMode(str, Enum):
    """Pipeline 输出模式"""
    AUTO = "auto"              # 全自动（跳过 human review）
    INTERACTIVE = "interactive"  # 交互式（需要人类确认）


# ============================================================================
# 配置数据类
# ============================================================================

@dataclass
class LLMSettings:
    """LLM API 连接配置"""
    provider: LLMProvider = LLMProvider.DEEPSEEK
    model: str = "gpt-4"               # 模型名称
    api_key: str = ""                   # API Key（从环境变量读取）
    base_url: str = ""                  # 自定义端点
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: int = 120

    def resolve_api_key(self) -> str:
        """读取 API Key：优先用配置值，再从环境变量读取"""
        if self.api_key:
            return self.api_key
        env_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
            LLMProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
        }
        env_var = env_map.get(self.provider)
        if env_var:
            return os.getenv(env_var, "")
        return ""

    @property
    def is_configured(self) -> bool:
        """是否已配置 API Key"""
        return bool(self.resolve_api_key())


@dataclass
class StageSettings:
    """单个 Agent 阶段配置"""
    model_override: Optional[str] = None         # 覆盖默认模型
    temperature_override: Optional[float] = None # 覆盖默认温度
    needs_human_review: bool = True              # 该阶段是否需要人工确认
    system_prompt: str = ""                      # 自定义系统提示词


@dataclass
class PipelineSettings:
    """Pipeline 运行配置"""
    output_mode: OutputMode = OutputMode.INTERACTIVE
    storage_dir: str = ".devflow_state"
    max_retries_per_stage: int = 3
    auto_cleanup_days: int = 7  # 自动清理超过 N 天的历史


@dataclass
class CodeGenSettings:
    """代码生成相关配置"""
    output_dir: str = "./generated_output"
    default_language: str = "python"
    default_framework: str = "fastapi"
    include_docker: bool = True
    include_tests: bool = True
    include_docs: bool = False


# ============================================================================
# 全局配置主类
# ============================================================================

@dataclass
class FlowStateConfig:
    """FlowState 全局配置"""

    # LLM API 配置
    llm: LLMSettings = field(default_factory=LLMSettings)

    # Pipeline 运行配置
    pipeline: PipelineSettings = field(default_factory=PipelineSettings)

    # 代码生成配置
    codegen: CodeGenSettings = field(default_factory=CodeGenSettings)

    # 各 Agent 阶段配置
    stages: Dict[str, StageSettings] = field(default_factory=lambda: {
        "requirement_analysis": StageSettings(
            needs_human_review=True,
            system_prompt=(
                "你是一个资深的业务需求分析师。请将用户的原始需求拆解为结构化的 PRD 文档，"
                "包含：业务目标、功能清单、用户故事、验收标准。"
            ),
        ),
        "solution_design": StageSettings(
            needs_human_review=True,
            system_prompt=(
                "你是一个资深的软件架构师。请基于需求文档输出技术方案，"
                "包含：整体架构、技术选型、目录结构、API 设计、数据模型。"
            ),
        ),
        "coding": StageSettings(
            needs_human_review=False,
            system_prompt=(
                "你是一个资深的全栈工程师。请基于技术方案输出完整可运行的代码。"
                "代码应包含必要的注释和类型注解。"
            ),
        ),
        "testing": StageSettings(
            needs_human_review=False,
            system_prompt=(
                "你是一个资深的测试工程师。请为生成的代码编写全面的单元测试和集成测试。"
            ),
        ),
        "code_review": StageSettings(
            needs_human_review=True,
            system_prompt=(
                "你是一个资深的代码审查员。请审查代码质量、安全性、性能、可维护性，"
                "输出评分和改进建议。"
            ),
        ),
        "delivery": StageSettings(
            needs_human_review=True,
            system_prompt=(
                "你是一个 DevOps 工程师。请准备变更集、生成 PR 描述、编写变更日志，"
                "确保交付物可部署上线。"
            ),
        ),
    })

    # 是否启用详细日志
    verbose: bool = False


# ============================================================================
# 配置加载器
# ============================================================================

_CONFIG_INSTANCE: Optional[FlowStateConfig] = None


def _load_from_env() -> FlowStateConfig:
    """从环境变量加载配置覆盖"""
    cfg = FlowStateConfig()

    # --- LLM 配置 ---
    provider_str = os.getenv("FS_LLM_PROVIDER", "").lower()
    if provider_str:
        try:
            cfg.llm.provider = LLMProvider(provider_str)
        except ValueError:
            print(f"[FlowState] 警告: 未知 LLM 提供商 '{provider_str}'，使用默认 deepseek")

    cfg.llm.model = os.getenv("FS_LLM_MODEL", cfg.llm.model)
    cfg.llm.api_key = os.getenv("FS_LLM_API_KEY", cfg.llm.api_key)
    cfg.llm.base_url = os.getenv("FS_LLM_BASE_URL", cfg.llm.base_url)
    cfg.llm.temperature = float(os.getenv("FS_LLM_TEMPERATURE", str(cfg.llm.temperature)))
    cfg.llm.max_tokens = int(os.getenv("FS_LLM_MAX_TOKENS", str(cfg.llm.max_tokens)))

    # --- Pipeline 配置 ---
    mode_str = os.getenv("FS_OUTPUT_MODE", "").lower()
    if mode_str:
        try:
            cfg.pipeline.output_mode = OutputMode(mode_str)
        except ValueError:
            pass
    cfg.pipeline.storage_dir = os.getenv("FS_STORAGE_DIR", cfg.pipeline.storage_dir)

    # --- 代码生成配置 ---
    cfg.codegen.output_dir = os.getenv("FS_OUTPUT_DIR", cfg.codegen.output_dir)
    cfg.codegen.default_language = os.getenv("FS_DEFAULT_LANG", cfg.codegen.default_language)
    cfg.codegen.default_framework = os.getenv("FS_DEFAULT_FRAMEWORK", cfg.codegen.default_framework)

    # --- 日志 ---
    cfg.verbose = os.getenv("FS_VERBOSE", "0") in ("1", "true", "yes")

    return cfg


def _load_from_json(path: str) -> FlowStateConfig:
    """从 JSON 配置文件加载"""
    cfg = _load_from_env()  # 先用环境变量做基准

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 递归覆盖
    _deep_merge(cfg, data)
    return cfg


def _resolve_env_var(value: Any) -> Any:
    """解析字符串中的 ${VAR_NAME} 占位符为环境变量值"""
    if isinstance(value, str) and "${" in value:
        import re
        def _replace(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        return re.sub(r'\$\{(\w+)\}', _replace, value)
    return value


def _deep_merge(cfg: FlowStateConfig, data: dict) -> None:
    """将 dict 数据递归合并到配置对象"""
    llm_fields = {"provider", "model", "api_key", "base_url", "temperature", "max_tokens"}
    pipeline_fields = {"output_mode", "storage_dir", "max_retries_per_stage"}
    codegen_fields = {"output_dir", "default_language", "default_framework",
                      "include_docker", "include_tests", "include_docs"}

    if "llm" in data:
        for k, v in data["llm"].items():
            if k in llm_fields and v is not None:
                v = _resolve_env_var(v)
                if k == "provider":
                    try:
                        v = LLMProvider(v)
                    except ValueError:
                        continue
                setattr(cfg.llm, k, v)

    if "pipeline" in data:
        for k, v in data["pipeline"].items():
            if k in pipeline_fields and v is not None:
                if k == "output_mode":
                    try:
                        v = OutputMode(v)
                    except ValueError:
                        continue
                setattr(cfg.pipeline, k, v)

    if "codegen" in data:
        for k, v in data["codegen"].items():
            if k in codegen_fields and v is not None:
                setattr(cfg.codegen, k, v)

    if "stages" in data and isinstance(data["stages"], dict):
        for stage_name, stage_cfg in data["stages"].items():
            if stage_name in cfg.stages:
                existing = cfg.stages[stage_name]
                if "needs_human_review" in stage_cfg:
                    existing.needs_human_review = stage_cfg["needs_human_review"]
                if "model_override" in stage_cfg:
                    existing.model_override = stage_cfg["model_override"]
                if "system_prompt" in stage_cfg:
                    existing.system_prompt = stage_cfg["system_prompt"]


def get_config(reload: bool = False) -> FlowStateConfig:
    """
    获取全局配置单例

    Args:
        reload: 是否重新加载（忽略缓存）

    加载优先级：
    1. 环境变量（FS_* 前缀）
    2. JSON 配置文件（如存在）
    3. 默认值
    """
    global _CONFIG_INSTANCE

    if _CONFIG_INSTANCE is None or reload:
        # 先从环境变量加载
        _CONFIG_INSTANCE = _load_from_env()

        # 再尝试从配置文件加载（覆盖环境变量中的部分字段）
        config_path = os.getenv("FS_CONFIG_PATH", "flowstate.config.json")
        if os.path.exists(config_path):
            _CONFIG_INSTANCE = _load_from_json(config_path)

    return _CONFIG_INSTANCE


def get_stage_config(stage_type: str) -> StageSettings:
    """
    快速获取某个阶段的配置

    Args:
        stage_type: StageType 的 value，如 "requirement_analysis"
    """
    cfg = get_config()
    return cfg.stages.get(stage_type, StageSettings())


def quick_configure(
    provider: str = "deepseek",
    model: str = "gpt-4",
    api_key: str = "",
    output_mode: str = "interactive",
) -> FlowStateConfig:
    """
    快速配置入口（适用于启动时一行代码完成配置）

    Usage:
        from src.config import quick_configure
        config = quick_configure(
            provider="openai",
            model="gpt-4",
            api_key="sk-xxx",
        )
    """
    global _CONFIG_INSTANCE

    cfg = get_config(reload=True)
    cfg.llm.provider = LLMProvider(provider) if provider else LLMProvider.DEEPSEEK
    cfg.llm.model = model or cfg.llm.model
    cfg.llm.api_key = api_key or cfg.llm.api_key
    if output_mode:
        cfg.pipeline.output_mode = OutputMode(output_mode)

    _CONFIG_INSTANCE = cfg
    return cfg


# ============================================================================
# 便捷访问属性
# ============================================================================

@property
def llm_config(self) -> LLMSettings:
    return get_config().llm

@property
def pipeline_config(self) -> PipelineSettings:
    return get_config().pipeline


# ============================================================================
# 示例配置文件生成
# ============================================================================

SAMPLE_CONFIG = {
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "${OPENAI_API_KEY}",
        "base_url": "",
        "temperature": 0.2,
        "max_tokens": 4096
    },
    "pipeline": {
        "output_mode": "interactive",
        "storage_dir": ".devflow_state",
        "max_retries_per_stage": 3,
        "auto_cleanup_days": 7
    },
    "codegen": {
        "output_dir": "./generated_output",
        "default_language": "python",
        "default_framework": "fastapi",
        "include_docker": True,
        "include_tests": True,
        "include_docs": False
    },
    "stages": {
        "requirement_analysis": {
            "needs_human_review": True,
            "model_override": None
        },
        "solution_design": {
            "needs_human_review": True,
            "model_override": None
        },
        "coding": {
            "needs_human_review": False,
            "model_override": None
        },
        "testing": {
            "needs_human_review": False,
            "model_override": None
        },
        "code_review": {
            "needs_human_review": True,
            "model_override": "gpt-4"
        },
        "delivery": {
            "needs_human_review": True,
            "model_override": None
        }
    }
}


def generate_sample_config(path: str = "flowstate.config.json") -> str:
    """生成示例配置文件供用户编辑"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_CONFIG, f, indent=2, ensure_ascii=False)
    print(f"[FlowState] 示例配置文件已生成: {path}")
    print(f"[FlowState] 请编辑该文件后运行，或通过环境变量 FS_* 配置")
    return path

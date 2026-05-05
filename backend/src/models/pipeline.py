"""FlowState pipline 数据模型"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageType(str, Enum):
    REQUIREMENT = "requirement_analysis"
    SOLUTION = "solution_design"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "code_review"
    DELIVERY = "delivery"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class ApproveAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"


class PipelineContext(BaseModel):
    """贯穿整个 Pipeline 的上下文"""
    project_path: str = ""
    project_summary: Optional[str] = None
    requirement_raw: str = ""
    requirement_doc: Optional[str] = None
    requirement_doc_path: Optional[str] = None
    solution_doc: Optional[str] = None
    solution_doc_path: Optional[str] = None
    solution_structured: Optional[Dict[str, Any]] = None
    generated_code: Optional[Dict[str, str]] = None
    test_report: Optional[str] = None
    review_report: Optional[str] = None
    delivery_result: Optional[str] = None


class StageNode(BaseModel):
    """流水线中一个阶段节点"""
    stage_type: StageType
    status: StageStatus = StageStatus.PENDING
    agent_output: Optional[Dict[str, Any]] = None
    human_feedback: Optional[str] = None
    human_approval: Optional[ApproveAction] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class Pipeline(BaseModel):
    """完整研发流水线"""
    id: str = Field(
        default_factory=lambda: f"pipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    title: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    stages: List[StageNode] = []
    context: PipelineContext = PipelineContext()
    logs: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

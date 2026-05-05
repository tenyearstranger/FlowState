export type StageStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "awaiting_review"
  | "rejected";

export interface PipelineStage {
  id: string;
  name: string;
  nameEn: string;
  agent: string;
  status: StageStatus;
  duration?: number;
  tokens?: number;
  output?: string;
  isCheckpoint?: boolean;
  startedAt?: string;
  completedAt?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  status: "running" | "completed" | "failed" | "paused" | "pending";
  progress: number;
  currentStage: number;
  stages: PipelineStage[];
  createdAt: string;
  updatedAt: string;
  template?: string;
  projectPath?: string;
  projectSummary?: string;
  requirementDocPath?: string;
}

export interface CreatePipelinePayload {
  projectPath: string;
  requirement: string;
}

export type CheckpointStatus = "pending" | "approved" | "rejected";

export interface Checkpoint {
  id: string;
  pipelineId: string;
  pipelineName: string;
  stage: string;
  stageIndex: number;
  status: CheckpointStatus;
  createdAt: string;
  output: string;
  rejectReason?: string;
}

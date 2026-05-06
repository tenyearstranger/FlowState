export type CheckpointStatus = "pending" | "approved" | "rejected";

export interface ReviewIssue {
  file: string;
  line: number;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
}

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
  subPhase?: string | null;
  depsManifest?: {
    pip_packages?: string[];
    npm_packages?: string[];
    install_commands?: Record<string, string>;
  } | null;
  reviewScore?: number | null;
  reviewIssues?: ReviewIssue[] | null;
  passRate?: string | null;
}

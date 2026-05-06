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

export interface PipelineGitStageCommit {
  stage_type: string;
  commit_sha: string;
  commit_message: string;
  committed_at: string;
  files_changed: string[];
}

export interface PipelineGitContext {
  mode: "disabled" | "worktree";
  enabled: boolean;
  repo_root?: string | null;
  base_branch?: string | null;
  base_commit?: string | null;
  worktree_path?: string | null;
  working_branch?: string | null;
  initialized: boolean;
  stage_commits: PipelineGitStageCommit[];
  total_files_changed: string[];
  head_commit?: string | null;
  diff_stats?: {
    files?: number;
    insertions?: number;
    deletions?: number;
  } | null;
  pr_title?: string | null;
  pr_description?: string | null;
  pr_command?: string | null;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  status: "running" | "completed" | "failed" | "paused" | "pending" | "cancelled";
  progress: number;
  currentStage: number;
  stages: PipelineStage[];
  createdAt: string;
  updatedAt: string;
  template?: string;
  projectPath?: string;
  projectSummary?: string;
  requirementDocPath?: string;
  solutionDocPath?: string;
}

export interface CreatePipelinePayload {
  projectPath: string;
  requirement: string;
}

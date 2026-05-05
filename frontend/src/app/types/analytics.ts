export interface PipelineRunDatum {
  day: string;
  success: number;
  failed: number;
  total: number;
}

export interface TokenUsageDatum {
  time: string;
  tokens: number;
}

export interface StageDurationDatum {
  stage: string;
  avg: number;
  p95: number;
}

export interface AgentSuccessDatum {
  name: string;
  rate: number;
}

export interface AnalyticsOverview {
  summary: {
    totalRuns: number;
    totalSuccess: number;
    totalTokens: number;
    averageDurationMinutes: number;
    mergedChanges: number;
  };
  pipelineRuns: PipelineRunDatum[];
  tokenUsage: TokenUsageDatum[];
  stageDurations: StageDurationDatum[];
  agentSuccessRates: AgentSuccessDatum[];
}

export interface ActivityItem {
  time: string;
  text: string;
  type: "success" | "checkpoint" | "warning" | "error";
}

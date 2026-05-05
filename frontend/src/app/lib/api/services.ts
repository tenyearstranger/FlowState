import { apiClient } from "./client";
import type { Agent } from "../../types/agent";
import type { ActivityItem, AnalyticsOverview } from "../../types/analytics";
import type { Checkpoint } from "../../types/checkpoint";
import type { CreatePipelinePayload, Pipeline } from "../../types/pipeline";

type RequestOptions = {
  signal?: AbortSignal;
};

export const pipelinesApi = {
  create: (payload: CreatePipelinePayload, options?: RequestOptions) =>
    apiClient.post<Pipeline>("/pipelines", payload, options),
  getById: (id: string, options?: RequestOptions) =>
    apiClient.get<Pipeline>(`/pipelines/${id}`, options),
  list: (options?: RequestOptions) => apiClient.get<Pipeline[]>("/pipelines", options),
  logs: (id: string, options?: RequestOptions) =>
    apiClient.get<string[]>(`/pipelines/${id}/logs`, options),
};

export const agentsApi = {
  list: (options?: RequestOptions) => apiClient.get<Agent[]>("/agents", options),
};

export const checkpointsApi = {
  approve: (id: string, options?: RequestOptions) =>
    apiClient.post<Checkpoint>(`/checkpoints/${id}/approve`, undefined, options),
  list: (options?: RequestOptions) =>
    apiClient.get<Checkpoint[]>("/checkpoints", { ...options, query: { status: "all" } }),
  reject: (id: string, reason: string, options?: RequestOptions) =>
    apiClient.post<Checkpoint>(`/checkpoints/${id}/reject`, { reason }, options),
};

export const analyticsApi = {
  getOverview: (options?: RequestOptions) =>
    apiClient.get<AnalyticsOverview>("/analytics", options),
};

export const activitiesApi = {
  listRecent: (options?: RequestOptions) =>
    apiClient.get<ActivityItem[]>("/activities/recent", options),
};

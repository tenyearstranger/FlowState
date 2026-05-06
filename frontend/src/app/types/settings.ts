export interface SettingsLlmConfig {
  provider: string;
  model: string;
  baseUrl: string;
  apiKey: string;
}

export interface SettingsPipelineConfig {
  defaultProvider: string;
  maxAgentRetries: number;
  checkpointTimeoutMinutes: number;
  autoCreateBranch: boolean;
  autoCommitCode: boolean;
  autoCreateMR: boolean;
  branchNamePattern: string;
  repositoryPath: string;
  semanticIndex: boolean;
}

export interface SettingsGeneralConfig {
  checkpointNotifications: boolean;
  pipelineCompleteNotifications: boolean;
  agentFailureAlerts: boolean;
  logRetentionDays: string;
  anonymousUsageStats: boolean;
  appVersion: string;
  engineVersion: string;
  apiVersion: string;
}

export interface SettingsData {
  llm: SettingsLlmConfig;
  agentConfigs: Record<string, SettingsLlmConfig>;
  pipeline: SettingsPipelineConfig;
  general: SettingsGeneralConfig;
}

export interface SettingsUpdatePayload {
  llm: SettingsLlmConfig;
  agentConfigs: Record<string, SettingsLlmConfig>;
  pipeline: SettingsPipelineConfig;
  general: Omit<SettingsGeneralConfig, "appVersion" | "engineVersion" | "apiVersion">;
}

export interface SettingsValidationResult {
  ok: boolean;
  message: string;
  provider: string;
  model: string;
}

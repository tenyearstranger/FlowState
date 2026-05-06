export interface SettingsProvider {
  id: string;
  name: string;
  models: string[];
  color: string;
  active: boolean;
  hasKey: boolean;
  maskedKey: string;
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
  providers: SettingsProvider[];
  pipeline: SettingsPipelineConfig;
  general: SettingsGeneralConfig;
}

export interface SettingsProviderUpdate {
  id: string;
  active: boolean;
  apiKey?: string | null;
}

export interface SettingsUpdatePayload {
  providers: SettingsProviderUpdate[];
  pipeline: SettingsPipelineConfig;
  general: Omit<SettingsGeneralConfig, "appVersion" | "engineVersion" | "apiVersion">;
}

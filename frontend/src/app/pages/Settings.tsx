import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { motion } from "motion/react";
import {
  Settings as SettingsIcon,
  Key,
  Bot,
  GitBranch,
  Check,
  Eye,
  EyeOff,
  RefreshCw,
  Trash2,
  ToggleLeft,
  ToggleRight,
  RotateCcw,
} from "lucide-react";
import { useApiQuery } from "../hooks/useApiQuery";
import { getErrorMessage } from "../lib/api/client";
import { settingsApi } from "../lib/api/services";
import type { SettingsData, SettingsProvider, SettingsUpdatePayload } from "../types/settings";

type Tab = "providers" | "pipeline" | "general";

type ProviderDraft = SettingsProvider & {
  apiKeyDraft: string;
};

const emptySettings: SettingsData = {
  providers: [],
  pipeline: {
    defaultProvider: "deepseek",
    maxAgentRetries: 3,
    checkpointTimeoutMinutes: 60,
    autoCreateBranch: true,
    autoCommitCode: true,
    autoCreateMR: true,
    branchNamePattern: "devflow/{pipeline-id}-{slug}",
    repositoryPath: "./src",
    semanticIndex: false,
  },
  general: {
    checkpointNotifications: true,
    pipelineCompleteNotifications: true,
    agentFailureAlerts: true,
    logRetentionDays: "7",
    anonymousUsageStats: false,
    appVersion: "v0.1.0-alpha",
    engineVersion: "v0.1.0",
    apiVersion: "v1",
  },
};

export function Settings() {
  const [activeTab, setActiveTab] = useState<Tab>("providers");
  const [draft, setDraft] = useState<SettingsData>(emptySettings);
  const [providerDrafts, setProviderDrafts] = useState<ProviderDraft[]>([]);
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const settingsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => settingsApi.get({ signal }), []),
    []
  );

  useEffect(() => {
    if (!settingsQuery.data) {
      return;
    }
    setDraft(settingsQuery.data);
    setProviderDrafts(
      settingsQuery.data.providers.map((provider) => ({
        ...provider,
        apiKeyDraft: "",
      }))
    );
  }, [settingsQuery.data]);

  const providerIds = useMemo(
    () => providerDrafts.map((provider) => provider.id),
    [providerDrafts]
  );

  const handleProviderChange = (providerId: string, updater: (provider: ProviderDraft) => ProviderDraft) => {
    setProviderDrafts((current) =>
      current.map((provider) => (provider.id === providerId ? updater(provider) : provider))
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const payload: SettingsUpdatePayload = {
        providers: providerDrafts.map((provider) => ({
          id: provider.id,
          active: provider.active,
          apiKey:
            provider.apiKeyDraft.trim() !== ""
              ? provider.apiKeyDraft.trim()
              : provider.hasKey
              ? undefined
              : "",
        })),
        pipeline: draft.pipeline,
        general: {
          checkpointNotifications: draft.general.checkpointNotifications,
          pipelineCompleteNotifications: draft.general.pipelineCompleteNotifications,
          agentFailureAlerts: draft.general.agentFailureAlerts,
          logRetentionDays: draft.general.logRetentionDays,
          anonymousUsageStats: draft.general.anonymousUsageStats,
        },
      };
      const updated = await settingsApi.update(payload);
      setDraft(updated);
      setProviderDrafts(
        updated.providers.map((provider) => ({
          ...provider,
          apiKeyDraft: "",
        }))
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (error) {
      setSaveError(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const tabs: { id: Tab; label: string; icon: typeof SettingsIcon }[] = [
    { id: "providers", label: "LLM 提供商", icon: Bot },
    { id: "pipeline", label: "Pipeline 配置", icon: GitBranch },
    { id: "general", label: "通用设置", icon: SettingsIcon },
  ];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            设置
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            配置 LLM 提供商、Pipeline 参数与系统设置
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-xl"
          style={{
            background: saved
              ? "rgba(52,199,89,0.12)"
              : "linear-gradient(135deg, #5B72FF, #A259FF)",
            border: saved ? "1px solid rgba(52,199,89,0.25)" : "none",
            color: saved ? "#34C759" : "white",
            fontSize: 13,
            fontWeight: 500,
            cursor: saving ? "not-allowed" : "pointer",
            boxShadow: saved ? "none" : "0 4px 14px rgba(91,114,255,0.3)",
            transition: "all 0.2s",
            opacity: saving ? 0.75 : 1,
          }}
        >
          {saved ? <><Check size={13} /> 已保存</> : saving ? "保存中..." : "保存更改"}
        </motion.button>
      </div>

      {(settingsQuery.error || saveError) && (
        <div className="px-8 pt-5">
          <div
            className="rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {saveError ?? settingsQuery.error}
            </span>
            <button
              onClick={settingsQuery.reload}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "rgba(255,255,255,0.65)",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              <RotateCcw size={12} />
              重试
            </button>
          </div>
        </div>
      )}

      <div
        className="flex items-center gap-1 px-8 py-3 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all"
            style={{
              background: activeTab === tab.id ? "rgba(91,114,255,0.12)" : "transparent",
              color: activeTab === tab.id ? "#A0ABFF" : "rgba(255,255,255,0.45)",
              border: `1px solid ${activeTab === tab.id ? "rgba(91,114,255,0.22)" : "transparent"}`,
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            <tab.icon size={12} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {settingsQuery.loading && providerIds.length === 0 ? (
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)" }}>正在加载设置...</div>
        ) : null}

        {activeTab === "providers" && (
          <div className="max-w-2xl space-y-4">
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginBottom: 20 }}>
              配置 AI 模型提供商，Agent 将在运行时使用这些配置。
            </p>
            {providerDrafts.map((provider, index) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                index={index}
                showKey={Boolean(showKey[provider.id])}
                onToggleKey={() =>
                  setShowKey((current) => ({ ...current, [provider.id]: !current[provider.id] }))
                }
                onToggleActive={() =>
                  handleProviderChange(provider.id, (current) => ({
                    ...current,
                    active: !current.active,
                  }))
                }
                onRemoveKey={() =>
                  handleProviderChange(provider.id, (current) => ({
                    ...current,
                    hasKey: false,
                    maskedKey: "",
                    apiKeyDraft: "",
                  }))
                }
                onApiKeyDraftChange={(value) =>
                  handleProviderChange(provider.id, (current) => ({
                    ...current,
                    apiKeyDraft: value,
                  }))
                }
              />
            ))}
          </div>
        )}

        {activeTab === "pipeline" && (
          <div className="max-w-2xl space-y-6">
            <SectionCard title="默认 Pipeline 配置">
              <SettingRow label="默认 LLM 提供商" desc="新建 Agent 时的默认提供商">
                <select
                  value={draft.pipeline.defaultProvider}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, defaultProvider: event.target.value },
                    }))
                  }
                  className="px-3 py-2 rounded-lg"
                  style={selectStyle}
                >
                  {providerDrafts.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </SettingRow>
              <SettingRow label="Agent 最大重试次数" desc="当 Agent 执行失败或被 Reject 时的最大重试次数">
                <input
                  type="number"
                  value={draft.pipeline.maxAgentRetries}
                  min={1}
                  max={10}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: {
                        ...current.pipeline,
                        maxAgentRetries: Math.max(1, Number(event.target.value) || 1),
                      },
                    }))
                  }
                  className="w-20 px-3 py-2 rounded-lg text-center"
                  style={inputStyle}
                />
              </SettingRow>
              <SettingRow label="检查点超时时间" desc="检查点等待人工审批的超时时间（分钟）">
                <input
                  type="number"
                  value={draft.pipeline.checkpointTimeoutMinutes}
                  min={5}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: {
                        ...current.pipeline,
                        checkpointTimeoutMinutes: Math.max(5, Number(event.target.value) || 5),
                      },
                    }))
                  }
                  className="w-20 px-3 py-2 rounded-lg text-center"
                  style={inputStyle}
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="Git 集成">
              <SettingRow label="自动创建分支" desc="代码生成完成后自动创建功能分支">
                <ToggleSwitch
                  on={draft.pipeline.autoCreateBranch}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, autoCreateBranch: !current.pipeline.autoCreateBranch },
                    }))
                  }
                />
              </SettingRow>
              <SettingRow label="自动提交代码" desc="代码生成后自动 commit（需人工审批后才推送）">
                <ToggleSwitch
                  on={draft.pipeline.autoCommitCode}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, autoCommitCode: !current.pipeline.autoCommitCode },
                    }))
                  }
                />
              </SettingRow>
              <SettingRow label="自动发起 MR" desc="交付集成阶段自动创建 Merge Request">
                <ToggleSwitch
                  on={draft.pipeline.autoCreateMR}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, autoCreateMR: !current.pipeline.autoCreateMR },
                    }))
                  }
                />
              </SettingRow>
              <SettingRow label="Branch 命名规则" desc="">
                <input
                  type="text"
                  value={draft.pipeline.branchNamePattern}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, branchNamePattern: event.target.value },
                    }))
                  }
                  className="px-3 py-2 rounded-lg"
                  style={{ ...inputStyle, width: 220, fontFamily: "monospace" }}
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="代码库上下文">
              <SettingRow label="代码库路径" desc="Agent 分析代码时的根目录">
                <input
                  type="text"
                  value={draft.pipeline.repositoryPath}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, repositoryPath: event.target.value },
                    }))
                  }
                  className="px-3 py-2 rounded-lg"
                  style={{ ...inputStyle, width: 160, fontFamily: "monospace" }}
                />
              </SettingRow>
              <SettingRow label="语义索引" desc="对代码库进行向量化索引，提升 Agent 检索准确率">
                <ToggleSwitch
                  on={draft.pipeline.semanticIndex}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      pipeline: { ...current.pipeline, semanticIndex: !current.pipeline.semanticIndex },
                    }))
                  }
                />
              </SettingRow>
            </SectionCard>
          </div>
        )}

        {activeTab === "general" && (
          <div className="max-w-2xl space-y-6">
            <SectionCard title="通知">
              <SettingRow label="检查点提醒" desc="有新的检查点需要审批时发送通知">
                <ToggleSwitch
                  on={draft.general.checkpointNotifications}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      general: { ...current.general, checkpointNotifications: !current.general.checkpointNotifications },
                    }))
                  }
                />
              </SettingRow>
              <SettingRow label="Pipeline 完成通知" desc="Pipeline 运行完成时通知">
                <ToggleSwitch
                  on={draft.general.pipelineCompleteNotifications}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      general: {
                        ...current.general,
                        pipelineCompleteNotifications: !current.general.pipelineCompleteNotifications,
                      },
                    }))
                  }
                />
              </SettingRow>
              <SettingRow label="Agent 失败告警" desc="Agent 执行失败时即时告警">
                <ToggleSwitch
                  on={draft.general.agentFailureAlerts}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      general: { ...current.general, agentFailureAlerts: !current.general.agentFailureAlerts },
                    }))
                  }
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="数据与隐私">
              <SettingRow label="保留日志天数" desc="Pipeline 运行日志的保留时间">
                <select
                  value={draft.general.logRetentionDays}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      general: { ...current.general, logRetentionDays: event.target.value },
                    }))
                  }
                  className="px-3 py-2 rounded-lg"
                  style={selectStyle}
                >
                  <option value="7">7 天</option>
                  <option value="30">30 天</option>
                  <option value="90">90 天</option>
                  <option value="forever">永久</option>
                </select>
              </SettingRow>
              <SettingRow label="匿名使用统计" desc="帮助改进产品（不包含代码内容）">
                <ToggleSwitch
                  on={draft.general.anonymousUsageStats}
                  onToggle={() =>
                    setDraft((current) => ({
                      ...current,
                      general: { ...current.general, anonymousUsageStats: !current.general.anonymousUsageStats },
                    }))
                  }
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="关于">
              <div className="py-2 space-y-2">
                {[
                  { label: "版本", value: draft.general.appVersion },
                  { label: "Pipeline 引擎", value: draft.general.engineVersion },
                  { label: "API 版本", value: draft.general.apiVersion },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-1">
                    <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>{item.label}</span>
                    <span style={{ fontSize: 12, fontFamily: "monospace", color: "rgba(255,255,255,0.35)" }}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        )}
      </div>
    </div>
  );
}

function ProviderCard({
  provider,
  index,
  showKey,
  onToggleKey,
  onToggleActive,
  onRemoveKey,
  onApiKeyDraftChange,
}: {
  provider: ProviderDraft;
  index: number;
  showKey: boolean;
  onToggleKey: () => void;
  onToggleActive: () => void;
  onRemoveKey: () => void;
  onApiKeyDraftChange: (value: string) => void;
}) {
  const displayValue = showKey ? provider.maskedKey || provider.apiKeyDraft : provider.maskedKey;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: `1px solid ${provider.active ? `${provider.color}25` : "rgba(255,255,255,0.07)"}`,
      }}
    >
      <div
        className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: `${provider.color}15`,
              border: `1px solid ${provider.color}25`,
            }}
          >
            <Bot size={14} style={{ color: provider.color }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
              {provider.name}
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>
              {provider.models.join(" · ")}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {provider.hasKey && (
            <span
              className="flex items-center gap-1 px-2 py-0.5 rounded-md"
              style={{
                fontSize: 10,
                color: "#34C759",
                background: "rgba(52,199,89,0.1)",
                border: "1px solid rgba(52,199,89,0.2)",
              }}
            >
              <Check size={9} /> 已配置
            </span>
          )}
          <button onClick={onToggleActive} style={{ background: "none", border: "none", cursor: "pointer" }}>
            {provider.active ? (
              <ToggleRight size={22} style={{ color: provider.color }} />
            ) : (
              <ToggleLeft size={22} style={{ color: "rgba(255,255,255,0.25)" }} />
            )}
          </button>
        </div>
      </div>

      <div className="px-5 py-4">
        <label
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "rgba(255,255,255,0.45)",
            display: "flex",
            alignItems: "center",
            gap: 5,
            marginBottom: 8,
          }}
        >
          <Key size={10} /> API Key
        </label>

        {provider.hasKey ? (
          <div className="flex items-center gap-2">
            <div
              className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontFamily: "monospace",
                  color: "rgba(255,255,255,0.5)",
                  flex: 1,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {displayValue || "已保存，明文不展示"}
              </span>
            </div>
            <button
              onClick={onToggleKey}
              className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
            >
              {showKey ? (
                <EyeOff size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              ) : (
                <Eye size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              )}
            </button>
            <button
              onClick={onRemoveKey}
              className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
            >
              <Trash2 size={13} style={{ color: "rgba(255,69,58,0.6)" }} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="password"
              value={provider.apiKeyDraft}
              onChange={(event) => onApiKeyDraftChange(event.target.value)}
              placeholder="sk-..."
              className="flex-1 px-3 py-2 rounded-lg"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "rgba(255,255,255,0.7)",
                fontSize: 12,
                fontFamily: "monospace",
                outline: "none",
              }}
            />
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <div className="px-5 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.5)" }}>
          {title}
        </span>
      </div>
      <div className="px-5 py-2">{children}</div>
    </div>
  );
}

function SettingRow({
  label,
  desc,
  children,
}: {
  label: string;
  desc: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="flex-1 pr-4">
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.75)", fontWeight: 500 }}>{label}</div>
        {desc ? (
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>{desc}</div>
        ) : null}
      </div>
      {children}
    </div>
  );
}

function ToggleSwitch({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button onClick={onToggle} style={{ background: "none", border: "none", cursor: "pointer" }}>
      {on ? (
        <ToggleRight size={24} style={{ color: "#5B72FF" }} />
      ) : (
        <ToggleLeft size={24} style={{ color: "rgba(255,255,255,0.25)" }} />
      )}
    </button>
  );
}

const inputStyle = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.1)",
  color: "rgba(255,255,255,0.7)",
  fontSize: 12,
  outline: "none",
} as const;

const selectStyle = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.1)",
  color: "rgba(255,255,255,0.7)",
  fontSize: 12,
  outline: "none",
} as const;

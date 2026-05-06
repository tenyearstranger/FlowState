import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router";
import { motion } from "motion/react";
import { toast } from "sonner";
import {
  Bot,
  Check,
  CheckCircle,
  ChevronRight,
  Clock,
  GitBranch,
  Key,
  RefreshCw,
  RotateCcw,
  Settings as SettingsIcon,
  ToggleLeft,
  ToggleRight,
  Zap,
} from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { useApiQuery } from "../hooks/useApiQuery";
import { getErrorMessage } from "../lib/api/client";
import { agentsApi, settingsApi } from "../lib/api/services";
import type { Agent } from "../types/agent";
import type { SettingsData, SettingsLlmConfig, SettingsUpdatePayload } from "../types/settings";

type Tab = "agents" | "pipeline" | "general";

const emptySettings: SettingsData = {
  llm: {
    provider: "deepseek",
    model: "deepseek-chat",
    baseUrl: "https://api.deepseek.com/",
    apiKey: "",
  },
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

function getTab(tab: string | null): Tab {
  if (tab === "agents" || tab === "pipeline" || tab === "general") {
    return tab;
  }
  return "pipeline";
}

function buildSettingsPayload(draft: SettingsData): SettingsUpdatePayload {
  return {
    llm: draft.llm,
    pipeline: draft.pipeline,
    general: {
      checkpointNotifications: draft.general.checkpointNotifications,
      pipelineCompleteNotifications: draft.general.pipelineCompleteNotifications,
      agentFailureAlerts: draft.general.agentFailureAlerts,
      logRetentionDays: draft.general.logRetentionDays,
      anonymousUsageStats: draft.general.anonymousUsageStats,
    },
  };
}

export function Settings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = getTab(searchParams.get("tab"));
  const [draft, setDraft] = useState<SettingsData>(emptySettings);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [configSaving, setConfigSaving] = useState(false);
  const [configError, setConfigError] = useState<string | null>(null);
  const [configDraft, setConfigDraft] = useState<SettingsLlmConfig>(emptySettings.llm);

  const settingsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => settingsApi.get({ signal }), []),
    []
  );
  const agentsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => agentsApi.list({ signal }), []),
    []
  );

  useEffect(() => {
    if (!searchParams.get("tab")) {
      setSearchParams({ tab: "pipeline" }, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (!settingsQuery.data) {
      return;
    }
    setDraft(settingsQuery.data);
  }, [settingsQuery.data]);

  useEffect(() => {
    const agents = agentsQuery.data ?? [];
    if (!selectedAgent && agents[0]) {
      setSelectedAgent(agents[0].id);
      return;
    }

    if (selectedAgent && !agents.some((agent) => agent.id === selectedAgent)) {
      setSelectedAgent(agents[0]?.id ?? "");
    }
  }, [agentsQuery.data, selectedAgent]);

  const agents = agentsQuery.data ?? [];
  const activeAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgent) ?? agents[0],
    [agents, selectedAgent]
  );

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await settingsApi.update(buildSettingsPayload(draft));
      setDraft(updated);
      setSaved(true);
      toast.success("设置已保存", {
        description: "Pipeline 与通用设置已更新。",
      });
      window.setTimeout(() => setSaved(false), 2500);
    } catch (error) {
      const message = getErrorMessage(error);
      setSaveError(message);
      toast.error("保存失败", { description: message });
    } finally {
      setSaving(false);
    }
  };

  const handleConfigSave = async () => {
    setConfigSaving(true);
    setConfigError(null);
    try {
      const updated = await settingsApi.update(
        buildSettingsPayload({
          ...draft,
          llm: configDraft,
          pipeline: {
            ...draft.pipeline,
            defaultProvider: configDraft.provider,
          },
        })
      );
      setDraft(updated);
      setConfigOpen(false);
      toast.success("Agent 配置已保存", {
        description: "后端 LLM 运行参数已经更新。",
      });
    } catch (error) {
      const message = getErrorMessage(error);
      setConfigError(message);
      toast.error("保存失败", { description: message });
    } finally {
      setConfigSaving(false);
    }
  };

  const openConfigDialog = () => {
    setConfigError(null);
    setConfigDraft(draft.llm);
    setConfigOpen(true);
  };

  const tabs: { id: Exclude<Tab, "agents">; label: string; icon: typeof SettingsIcon }[] = [
    { id: "pipeline", label: "Pipeline 配置", icon: GitBranch },
    { id: "general", label: "通用设置", icon: SettingsIcon },
  ];

  const pageDescriptions: Record<Tab, string> = {
    agents: "查看各阶段 Agent 的运行状态，并通过配置弹窗管理后端 LLM 运行参数。",
    pipeline: "配置 Pipeline 的重试策略、Git 行为与代码库上下文。",
    general: "管理通知、日志保留与应用级通用设置。",
  };

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
            {pageDescriptions[activeTab]}
          </p>
        </div>

        {activeTab !== "agents" ? (
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
        ) : (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={openConfigDialog}
            className="flex items-center gap-2 px-4 py-2 rounded-xl"
            style={{
              background: "linear-gradient(135deg, #5B72FF, #7C8FFF)",
              color: "white",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
              boxShadow: "0 4px 14px rgba(91,114,255,0.24)",
            }}
          >
            <SettingsIcon size={13} />
            配置
          </motion.button>
        )}
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
              onClick={() => {
                settingsQuery.reload();
                agentsQuery.reload();
              }}
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

      {activeTab !== "agents" && (
        <div
          className="flex items-center gap-1 px-8 py-3 flex-shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSearchParams({ tab: tab.id })}
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
      )}

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {settingsQuery.loading && !draft.llm.apiKey ? (
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)" }}>正在加载设置...</div>
        ) : null}

        {activeTab === "agents" && (
          <AgentManagementTab
            agents={agents}
            loading={agentsQuery.loading}
            error={agentsQuery.error}
            activeAgent={activeAgent}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
            onReload={agentsQuery.reload}
            onOpenConfig={openConfigDialog}
            llmConfig={draft.llm}
          />
        )}

        {activeTab === "pipeline" && (
          <div className="max-w-2xl space-y-6">
            <SectionCard title="默认 Pipeline 配置">
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

      <AgentConfigDialog
        open={configOpen}
        onOpenChange={setConfigOpen}
        activeAgent={activeAgent}
        draft={configDraft}
        saving={configSaving}
        error={configError}
        onChange={(field, value) =>
          setConfigDraft((current) => ({
            ...current,
            [field]: value,
          }))
        }
        onSave={handleConfigSave}
      />
    </div>
  );
}

function AgentManagementTab({
  agents,
  loading,
  error,
  activeAgent,
  selectedAgent,
  onSelectAgent,
  onReload,
  onOpenConfig,
  llmConfig,
}: {
  agents: Agent[];
  loading: boolean;
  error: string | null;
  activeAgent: Agent | undefined;
  selectedAgent: string;
  onSelectAgent: (agentId: string) => void;
  onReload: () => void;
  onOpenConfig: () => void;
  llmConfig: SettingsLlmConfig;
}) {
  if (error) {
    return (
      <div
        className="rounded-2xl p-4 flex items-center justify-between"
        style={{
          background: "rgba(255,69,58,0.06)",
          border: "1px solid rgba(255,69,58,0.18)",
        }}
      >
        <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>{error}</span>
        <button
          onClick={onReload}
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
    );
  }

  if (!activeAgent && !loading) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: "rgba(255,255,255,0.35)" }}>
        暂无 Agent 数据
      </div>
    );
  }

  return (
    <div className="flex gap-6 min-h-[620px]">
      <div
        className="w-72 flex-shrink-0 overflow-y-auto p-4 space-y-2 rounded-2xl"
        style={{
          border: "1px solid rgba(255,255,255,0.06)",
          background: "rgba(255,255,255,0.02)",
        }}
      >
        {agents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.04 }}
            onClick={() => onSelectAgent(agent.id)}
            className="p-4 rounded-xl cursor-pointer transition-all"
            style={{
              background: selectedAgent === agent.id ? `${agent.color}0D` : "rgba(255,255,255,0.025)",
              border: `1px solid ${
                selectedAgent === agent.id ? `${agent.color}30` : "rgba(255,255,255,0.07)"
              }`,
            }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 relative"
                style={{ background: `${agent.color}18` }}
              >
                <Bot size={15} style={{ color: agent.color }} />
                {agent.status === "running" && (
                  <div
                    className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2"
                    style={{
                      background: "#34C759",
                      borderColor: "#0d0d11",
                    }}
                  />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: "rgba(255,255,255,0.85)",
                    fontFamily: "monospace",
                  }}
                  className="truncate"
                >
                  {agent.name}
                </div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 1 }}>
                  {agent.role}
                </div>
              </div>
              <ChevronRight size={11} style={{ color: "rgba(255,255,255,0.2)", flexShrink: 0 }} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        {activeAgent ? (
          <>
            <motion.div
              key={activeAgent.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl p-6"
              style={{
                background: `${activeAgent.color}08`,
                border: `1px solid ${activeAgent.color}20`,
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center"
                    style={{
                      background: `${activeAgent.color}18`,
                      border: `1px solid ${activeAgent.color}30`,
                    }}
                  >
                    <Bot size={24} style={{ color: activeAgent.color }} />
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 18,
                        fontWeight: 600,
                        color: "white",
                        fontFamily: "monospace",
                        letterSpacing: "-0.5px",
                      }}
                    >
                      {activeAgent.name}
                    </div>
                    <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", marginTop: 2 }}>
                      {activeAgent.role}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
                    style={{
                      fontSize: 11,
                      fontWeight: 500,
                      background:
                        activeAgent.status === "running"
                          ? "rgba(52,199,89,0.1)"
                          : "rgba(255,255,255,0.05)",
                      color: activeAgent.status === "running" ? "#34C759" : "rgba(255,255,255,0.4)",
                      border: `1px solid ${
                        activeAgent.status === "running"
                          ? "rgba(52,199,89,0.2)"
                          : "rgba(255,255,255,0.08)"
                      }`,
                    }}
                  >
                    {activeAgent.status === "running" ? "运行中" : "空闲"}
                  </span>
                  <button
                    onClick={onOpenConfig}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
                    style={{
                      fontSize: 11,
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      color: "rgba(255,255,255,0.72)",
                      cursor: "pointer",
                    }}
                  >
                    <SettingsIcon size={11} /> 配置
                  </button>
                </div>
              </div>

              <p
                style={{
                  fontSize: 13,
                  color: "rgba(255,255,255,0.5)",
                  lineHeight: 1.6,
                  marginTop: 16,
                }}
              >
                {activeAgent.description}
              </p>

              <div className="flex items-center gap-2 mt-4">
                <span
                  className="px-3 py-1 rounded-lg"
                  style={{
                    fontSize: 11,
                    fontFamily: "monospace",
                    color: "#6B9FFF",
                    background: "rgba(107,159,255,0.12)",
                    border: "1px solid rgba(107,159,255,0.24)",
                  }}
                >
                  {llmConfig.provider}
                </span>
                <span
                  className="px-3 py-1 rounded-lg"
                  style={{
                    fontSize: 11,
                    fontFamily: "monospace",
                    color: "rgba(255,255,255,0.45)",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.07)",
                  }}
                >
                  {llmConfig.model}
                </span>
              </div>
            </motion.div>

            <div className="grid grid-cols-3 gap-4">
              {[
                {
                  label: "累计完成任务",
                  value: activeAgent.tasksCompleted,
                  unit: "次",
                  icon: CheckCircle,
                  color: "#34C759",
                },
                {
                  label: "平均执行时长",
                  value: activeAgent.avgDuration,
                  unit: "s",
                  icon: Clock,
                  color: "#5B72FF",
                },
                {
                  label: "平均 Token 消耗",
                  value: activeAgent.avgTokens.toLocaleString(),
                  unit: "",
                  icon: Zap,
                  color: "#FF9F0A",
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl p-4"
                  style={{
                    background: "rgba(255,255,255,0.025)",
                    border: "1px solid rgba(255,255,255,0.07)",
                  }}
                >
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center mb-3"
                    style={{ background: `${stat.color}15` }}
                  >
                    <stat.icon size={13} style={{ color: stat.color }} />
                  </div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 600,
                      color: "white",
                      letterSpacing: "-0.5px",
                    }}
                  >
                    {stat.value}
                    <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>{stat.unit}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 3 }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4">
              <SectionCard title="当前后端 LLM 配置">
                <div className="py-2 space-y-3">
                  {[
                    { label: "FS_LLM_PROVIDER", value: llmConfig.provider },
                    { label: "FS_LLM_MODEL", value: llmConfig.model },
                    { label: "FS_LLM_BASE_URL", value: llmConfig.baseUrl || "-" },
                    { label: "FS_LLM_API_KEY", value: llmConfig.apiKey ? "已配置" : "未配置" },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between gap-4 py-1">
                      <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", fontFamily: "monospace" }}>
                        {item.label}
                      </span>
                      <span
                        style={{
                          fontSize: 12,
                          color: "rgba(255,255,255,0.8)",
                          fontFamily: "monospace",
                          textAlign: "right",
                        }}
                      >
                        {item.value}
                      </span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </div>
          </>
        ) : (
          <div className="h-full flex items-center justify-center" style={{ color: "rgba(255,255,255,0.35)" }}>
            {loading ? "正在加载 Agent..." : "暂无 Agent 数据"}
          </div>
        )}
      </div>
    </div>
  );
}

function AgentConfigDialog({
  open,
  onOpenChange,
  activeAgent,
  draft,
  saving,
  error,
  onChange,
  onSave,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  activeAgent: Agent | undefined;
  draft: SettingsLlmConfig;
  saving: boolean;
  error: string | null;
  onChange: (field: keyof SettingsLlmConfig, value: string) => void;
  onSave: () => Promise<void>;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-2xl p-0"
        style={{
          background: "#121218",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "white",
        }}
      >
        <DialogHeader className="px-6 pt-6 pb-4 text-left" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <DialogTitle style={{ fontSize: 18, color: "white" }}>
            {activeAgent ? `${activeAgent.name} 配置` : "Agent 配置"}
          </DialogTitle>
          <DialogDescription style={{ color: "rgba(255,255,255,0.45)", lineHeight: 1.6 }}>
            这里只保留后端实际使用的 4 个 LLM 参数，对应 `FS_LLM_*` 环境变量。
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-5 space-y-4">
          {error && (
            <div
              className="rounded-xl px-4 py-3"
              style={{
                background: "rgba(255,69,58,0.06)",
                border: "1px solid rgba(255,69,58,0.18)",
                color: "rgba(255,255,255,0.72)",
                fontSize: 12,
              }}
            >
              {error}
            </div>
          )}

          <LlmInputField
            label="FS_LLM_PROVIDER"
            value={draft.provider}
            placeholder="deepseek"
            onChange={(value) => onChange("provider", value)}
          />
          <LlmInputField
            label="FS_LLM_MODEL"
            value={draft.model}
            placeholder="deepseek-chat"
            onChange={(value) => onChange("model", value)}
          />
          <LlmInputField
            label="FS_LLM_BASE_URL"
            value={draft.baseUrl}
            placeholder="https://api.deepseek.com/"
            onChange={(value) => onChange("baseUrl", value)}
          />
          <LlmInputField
            label="FS_LLM_API_KEY"
            value={draft.apiKey}
            placeholder="sk-..."
            onChange={(value) => onChange("apiKey", value)}
            secret
          />
        </div>

        <DialogFooter
          className="px-6 py-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 rounded-xl"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "rgba(255,255,255,0.6)",
              cursor: "pointer",
            }}
          >
            取消
          </button>
          <button
            onClick={() => void onSave()}
            disabled={saving}
            className="px-4 py-2 rounded-xl flex items-center gap-2"
            style={{
              background: "linear-gradient(135deg, #5B72FF, #A259FF)",
              color: "white",
              cursor: saving ? "not-allowed" : "pointer",
              opacity: saving ? 0.7 : 1,
            }}
          >
            <RefreshCw size={13} />
            {saving ? "保存中..." : "保存配置"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function LlmInputField({
  label,
  value,
  placeholder,
  onChange,
  secret = false,
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  secret?: boolean;
}) {
  return (
    <div>
      <label
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: "rgba(255,255,255,0.45)",
          display: "flex",
          alignItems: "center",
          gap: 5,
          marginBottom: 8,
          fontFamily: "monospace",
        }}
      >
        <Key size={10} /> {label}
      </label>
      <input
        type={secret ? "password" : "text"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "rgba(255,255,255,0.78)",
          fontSize: 12,
          fontFamily: "monospace",
          outline: "none",
        }}
      />
    </div>
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

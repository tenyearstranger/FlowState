import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import {
  Bot,
  Zap,
  Clock,
  CheckCircle,
  Settings,
  ChevronRight,
  Play,
  RotateCcw,
} from "lucide-react";
import { useApiQuery } from "../hooks/useApiQuery";
import { agentsApi } from "../lib/api/services";

const providerColors: Record<string, string> = {
  OpenAI: "#74AA9C",
  Anthropic: "#D4A96A",
};

const providerBgs: Record<string, string> = {
  OpenAI: "rgba(116,170,156,0.08)",
  Anthropic: "rgba(212,169,106,0.08)",
};

export function Agents() {
  const [selectedAgent, setSelectedAgent] = useState("");
  const agentsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => agentsApi.list({ signal }), []),
    []
  );
  const agents = agentsQuery.data ?? [];

  useEffect(() => {
    if (!selectedAgent && agents[0]) {
      setSelectedAgent(agents[0].id);
    }
  }, [agents, selectedAgent]);

  const activeAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgent) ?? agents[0],
    [agents, selectedAgent]
  );

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            Agent 管理
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            {agentsQuery.loading
              ? "正在同步 Agent 数据..."
              : `${agents.length} 个 Agent · ${agents.filter((agent) => agent.status === "running").length} 个运行中`}
          </p>
        </div>
      </div>

      {agentsQuery.error && (
        <div className="px-8 pt-5">
          <div
            className="rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {agentsQuery.error}
            </span>
            <button
              onClick={agentsQuery.reload}
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

      <div className="flex-1 flex overflow-hidden">
        <div
          className="w-72 flex-shrink-0 overflow-y-auto p-4 space-y-2"
          style={{ borderRight: "1px solid rgba(255,255,255,0.05)" }}
        >
          {agents.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.04 }}
              onClick={() => setSelectedAgent(agent.id)}
              className="p-4 rounded-xl cursor-pointer transition-all"
              style={{
                background:
                  selectedAgent === agent.id
                    ? `${agent.color}0D`
                    : "rgba(255,255,255,0.025)",
                border: `1px solid ${
                  selectedAgent === agent.id
                    ? `${agent.color}30`
                    : "rgba(255,255,255,0.07)"
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

              <div className="flex items-center gap-3 mt-3">
                <span
                  className="px-2 py-0.5 rounded-md"
                  style={{
                    fontSize: 9,
                    fontFamily: "monospace",
                    color: providerColors[agent.provider] || "rgba(255,255,255,0.4)",
                    background: providerBgs[agent.provider] || "rgba(255,255,255,0.04)",
                    border: `1px solid ${providerColors[agent.provider] || "rgba(255,255,255,0.08)"}20`,
                  }}
                >
                  {agent.provider}
                </span>
                <span
                  style={{
                    fontSize: 9,
                    fontFamily: "monospace",
                    color: "rgba(255,255,255,0.3)",
                    background: "rgba(255,255,255,0.04)",
                    padding: "1px 5px",
                    borderRadius: 4,
                  }}
                >
                  {agent.model}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {activeAgent ? (
            <motion.div
              key={activeAgent.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div
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
                        color:
                          activeAgent.status === "running"
                            ? "#34C759"
                            : "rgba(255,255,255,0.4)",
                        border: `1px solid ${
                          activeAgent.status === "running"
                            ? "rgba(52,199,89,0.2)"
                            : "rgba(255,255,255,0.08)"
                        }`,
                      }}
                    >
                      {activeAgent.status === "running" && (
                        <span className="relative flex w-1.5 h-1.5">
                          <span
                            className="absolute inline-flex w-full h-full rounded-full animate-ping"
                            style={{ background: "#34C759", opacity: 0.4 }}
                          />
                          <span
                            className="relative inline-flex rounded-full w-1.5 h-1.5"
                            style={{ background: "#34C759" }}
                          />
                        </span>
                      )}
                      {activeAgent.status === "running" ? "运行中" : "空闲"}
                    </span>
                    <button
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
                      style={{
                        fontSize: 11,
                        background: "rgba(255,255,255,0.05)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        color: "rgba(255,255,255,0.5)",
                        cursor: "pointer",
                      }}
                    >
                      <Settings size={11} /> 配置
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
                      color: providerColors[activeAgent.provider] || "rgba(255,255,255,0.5)",
                      background: providerBgs[activeAgent.provider] || "rgba(255,255,255,0.05)",
                      border: `1px solid ${providerColors[activeAgent.provider] || "rgba(255,255,255,0.1)"}30`,
                    }}
                  >
                    {activeAgent.provider}
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
                    {activeAgent.model}
                  </span>
                </div>
              </div>

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
                      <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>
                        {stat.unit}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 3 }}>
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>

              <div
                className="rounded-2xl overflow-hidden"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.07)",
                }}
              >
                <div
                  className="flex items-center justify-between px-5 py-4"
                  style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
                >
                  <div className="flex items-center gap-2">
                    <Bot size={12} style={{ color: "rgba(255,255,255,0.4)" }} />
                    <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.6)" }}>
                      System Prompt
                    </span>
                  </div>
                  <button
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg"
                    style={{
                      fontSize: 11,
                      color: "#7C8FFF",
                      background: "rgba(91,114,255,0.08)",
                      border: "1px solid rgba(91,114,255,0.15)",
                      cursor: "pointer",
                    }}
                  >
                    编辑 Prompt
                  </button>
                </div>
                <div
                  className="p-5"
                  style={{
                    fontSize: 12,
                    color: "rgba(255,255,255,0.5)",
                    lineHeight: 1.75,
                    fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {`You are ${activeAgent.name}, a specialized AI agent in the DevFlow pipeline.

Your role: ${activeAgent.role}
Your task: ${activeAgent.description}

## Output Contract
- Always output structured, machine-readable content
- Follow the defined output schema strictly
- If input is ambiguous, ask for clarification before proceeding
- Include confidence scores for critical decisions

## Behavior Rules
- Be concise and precise
- Prioritize correctness over completeness
- Flag potential issues or risks explicitly
- Never make assumptions about undefined requirements`}
                </div>
              </div>

              <div
                className="rounded-2xl p-5"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.07)",
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.6)" }}>
                    快速测试
                  </span>
                </div>
                <textarea
                  placeholder={`向 ${activeAgent.name} 发送一条测试消息...`}
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl resize-none mb-3"
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 12,
                    outline: "none",
                    lineHeight: 1.6,
                  }}
                />
                <button
                  className="flex items-center gap-2 px-4 py-2 rounded-lg"
                  style={{
                    background: `${activeAgent.color}18`,
                    border: `1px solid ${activeAgent.color}30`,
                    color: activeAgent.color,
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: "pointer",
                  }}
                >
                  <Play size={12} /> 发送测试
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="h-full flex items-center justify-center" style={{ color: "rgba(255,255,255,0.35)" }}>
              {agentsQuery.loading ? "正在加载 Agent..." : "暂无 Agent 数据"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

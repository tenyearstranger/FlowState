import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { motion } from "motion/react";
import {
  ArrowLeft,
  Play,
  Pause,
  StopCircle,
  RotateCcw,
  ChevronRight,
  Bot,
  CheckSquare,
  Clock,
  Zap,
  Terminal,
  ChevronDown,
  Copy,
  Check,
  FolderOpen,
  FileSearch,
} from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";
import { pipelinesApi } from "../lib/api/services";
import type { PipelineStage } from "../types/pipeline";

const stageColors: Record<string, string> = {
  "需求分析": "#5B72FF",
  "方案设计": "#A259FF",
  "代码生成": "#FF7A5C",
  "测试生成": "#34C759",
  "代码评审": "#FF9F0A",
  "交付集成": "#00C7BE",
};

function OutputPanel({ stage }: { stage: PipelineStage }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (stage.output) {
      navigator.clipboard.writeText(stage.output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!stage.output) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
          style={{ background: "rgba(255,255,255,0.04)" }}
        >
          <Terminal size={16} style={{ color: "rgba(255,255,255,0.2)" }} />
        </div>
        <p style={{ fontSize: 12, color: "rgba(255,255,255,0.3)" }}>
          {stage.status === "idle" ? "等待执行..." : "正在生成输出..."}
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={handleCopy}
        className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-lg z-10"
        style={{
          background: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "rgba(255,255,255,0.5)",
          fontSize: 11,
          cursor: "pointer",
        }}
      >
        {copied ? <Check size={11} /> : <Copy size={11} />}
        {copied ? "已复制" : "复制"}
      </button>
      <div
        className="rounded-xl p-4 overflow-y-auto"
        style={{
          background: "rgba(0,0,0,0.3)",
          border: "1px solid rgba(255,255,255,0.06)",
          maxHeight: 320,
          fontSize: 12,
          color: "rgba(255,255,255,0.7)",
          lineHeight: 1.7,
          fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
          whiteSpace: "pre-wrap",
        }}
      >
        {stage.output}
      </div>
    </div>
  );
}

function StageCard({
  stage,
  index,
  isActive,
  onClick,
}: {
  stage: PipelineStage;
  index: number;
  isActive: boolean;
  onClick: () => void;
}) {
  const color = stageColors[stage.name] || "#5B72FF";

  const statusIcon = () => {
    if (stage.status === "completed") {
      return (
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center"
          style={{ background: "rgba(52,199,89,0.15)", border: "1px solid rgba(52,199,89,0.3)" }}
        >
          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
            <path d="M1 4L3.5 6.5L9 1" stroke="#34C759" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
      );
    }
    if (stage.status === "running") {
      return (
        <div className="relative w-6 h-6 flex items-center justify-center">
          <div
            className="w-6 h-6 rounded-full absolute animate-spin"
            style={{
              border: "1.5px solid transparent",
              borderTopColor: color,
              borderRightColor: `${color}50`,
            }}
          />
          <Bot size={10} style={{ color }} />
        </div>
      );
    }
    if (stage.status === "awaiting_review") {
      return (
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center"
          style={{ background: "rgba(255,159,10,0.15)", border: "1px solid rgba(255,159,10,0.3)" }}
        >
          <CheckSquare size={10} style={{ color: "#FF9F0A" }} />
        </div>
      );
    }
    if (stage.status === "failed") {
      return (
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center"
          style={{ background: "rgba(255,69,58,0.15)", border: "1px solid rgba(255,69,58,0.3)" }}
        >
          <span style={{ fontSize: 12, color: "#FF453A", fontWeight: 700, lineHeight: 1 }}>x</span>
        </div>
      );
    }
    return (
      <div
        className="w-6 h-6 rounded-full flex items-center justify-center"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.1)",
        }}
      >
        <span style={{ fontSize: 9, color: "rgba(255,255,255,0.3)", fontWeight: 600 }}>
          {index + 1}
        </span>
      </div>
    );
  };

  return (
    <motion.div
      whileHover={{ y: -1 }}
      onClick={onClick}
      className="rounded-xl p-4 cursor-pointer transition-all"
      style={{
        background: isActive ? `${color}0D` : "rgba(255,255,255,0.025)",
        border: `1px solid ${isActive ? `${color}30` : "rgba(255,255,255,0.07)"}`,
      }}
    >
      <div className="flex items-center gap-3 mb-3">
        {statusIcon()}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              style={{
                fontSize: 12,
                fontWeight: 500,
                color: stage.status === "idle" ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.85)",
              }}
            >
              {stage.name}
            </span>
            {stage.isCheckpoint && (
              <span
                style={{
                  fontSize: 9,
                  color: "#FF9F0A",
                  background: "rgba(255,159,10,0.1)",
                  padding: "1px 5px",
                  borderRadius: 4,
                  border: "1px solid rgba(255,159,10,0.2)",
                }}
              >
                检查点
              </span>
            )}
          </div>
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>{stage.agent}</span>
        </div>
        {stage.status !== "idle" && <StatusBadge status={stage.status as any} size="sm" />}
      </div>

      {stage.status !== "idle" && (
        <div className="flex items-center gap-3 text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
          {stage.duration !== undefined && stage.duration > 0 && (
            <span className="flex items-center gap-1">
              <Clock size={9} />
              {stage.duration}s
            </span>
          )}
          {stage.tokens && (
            <span className="flex items-center gap-1">
              <Zap size={9} />
              {stage.tokens.toLocaleString()} tokens
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

export function PipelineDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedStage, setSelectedStage] = useState("");
  const [showLogs, setShowLogs] = useState(true);
  const [logCount, setLogCount] = useState(0);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const pipelineQuery = useApiQuery(
    useCallback(
      (signal: AbortSignal) => {
        if (!id) {
          return Promise.reject(new Error("缺少流水线 ID"));
        }
        return pipelinesApi.getById(id, { signal });
      },
      [id]
    ),
    [id],
    { enabled: Boolean(id) }
  );

  const logsQuery = useApiQuery(
    useCallback(
      (signal: AbortSignal) => {
        if (!id) {
          return Promise.resolve<string[]>([]);
        }
        return pipelinesApi.logs(id, { signal });
      },
      [id]
    ),
    [id],
    { enabled: Boolean(id), initialData: [] }
  );

  const pipeline = pipelineQuery.data;
  const logs = logsQuery.data ?? [];
  const activeStage = useMemo(
    () => pipeline?.stages.find((stage) => stage.id === selectedStage),
    [pipeline, selectedStage]
  );

  useEffect(() => {
    if (!pipeline) {
      return;
    }

    const defaultStageId =
      pipeline.stages.find((stage) => stage.status === "running" || stage.status === "awaiting_review")?.id ||
      pipeline.stages[0]?.id ||
      "";

    if (!selectedStage || !pipeline.stages.some((stage) => stage.id === selectedStage)) {
      setSelectedStage(defaultStageId);
    }
  }, [pipeline, selectedStage]);

  useEffect(() => {
    if (!pipeline) {
      return;
    }

    if (pipeline.status === "running") {
      setLogCount(Math.min(logs.length, 8));
      return;
    }

    setLogCount(logs.length);
  }, [logs.length, pipeline]);

  useEffect(() => {
    if (pipeline?.status !== "running" || logCount >= logs.length) {
      return;
    }

    const interval = setInterval(() => {
      setLogCount((count) => Math.min(count + 1, logs.length));
    }, 1200);

    return () => clearInterval(interval);
  }, [logCount, logs.length, pipeline?.status]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logCount]);

  if (pipelineQuery.loading && !pipeline) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: "rgba(255,255,255,0.35)" }}>
        正在加载流水线详情...
      </div>
    );
  }

  if (pipelineQuery.error || !pipeline) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4">
        <div style={{ fontSize: 14, color: "rgba(255,255,255,0.6)" }}>
          {pipelineQuery.error ?? "未找到流水线"}
        </div>
        <button
          onClick={() => navigate("/pipelines")}
          className="px-4 py-2 rounded-lg"
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "rgba(255,255,255,0.7)",
            cursor: "pointer",
          }}
        >
          返回列表
        </button>
      </div>
    );
  }

  const progressPercent = pipeline.progress;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div
        className="flex items-center gap-4 px-6 py-4 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <button
          onClick={() => navigate("/pipelines")}
          className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-white/[0.06] transition-colors"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
        >
          <ArrowLeft size={14} style={{ color: "rgba(255,255,255,0.6)" }} />
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h2
              style={{ fontSize: 15, fontWeight: 600, color: "white", letterSpacing: "-0.3px" }}
              className="truncate"
            >
              {pipeline.name}
            </h2>
            <StatusBadge status={pipeline.status} size="sm" />
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>{pipeline.id}</span>
            <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
              {pipeline.template}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className="w-32 h-1.5 rounded-full overflow-hidden"
            style={{ background: "rgba(255,255,255,0.06)" }}
          >
            <motion.div
              className="h-full rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              style={{ background: "linear-gradient(90deg, #5B72FF, #A259FF)" }}
            />
          </div>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", minWidth: 30 }}>
            {progressPercent}%
          </span>
        </div>

        <div className="flex items-center gap-2">
          {pipeline.status === "running" && (
            <>
              <button
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                style={{
                  background: "rgba(255,159,10,0.1)",
                  border: "1px solid rgba(255,159,10,0.2)",
                  color: "#FF9F0A",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                <Pause size={12} /> 暂停
              </button>
              <button
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                style={{
                  background: "rgba(255,69,58,0.08)",
                  border: "1px solid rgba(255,69,58,0.15)",
                  color: "#FF453A",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                <StopCircle size={12} /> 终止
              </button>
            </>
          )}
          {(pipeline.status === "paused" || pipeline.status === "failed") && (
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              style={{
                background: "rgba(91,114,255,0.1)",
                border: "1px solid rgba(91,114,255,0.2)",
                color: "#7C8FFF",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              {pipeline.status === "paused" ? <><Play size={12} /> 继续</> : <><RotateCcw size={12} /> 重试</>}
            </button>
          )}
        </div>
      </div>

      {(pipeline.projectPath || pipeline.projectSummary || pipeline.requirementDocPath) && (
        <div
          className="mx-6 mt-5 rounded-2xl p-5 flex-shrink-0"
          style={{
            background: "rgba(255,255,255,0.025)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <FileSearch size={13} style={{ color: "rgba(255,255,255,0.45)" }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
              项目上下文
            </span>
          </div>

          {pipeline.projectPath && (
            <div className="mb-4">
              <div
                className="flex items-center gap-2 mb-2"
                style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
              >
                <FolderOpen size={11} />
                项目本地目录
              </div>
              <div
                className="rounded-xl px-4 py-3"
                style={{
                  background: "rgba(0,0,0,0.22)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  color: "rgba(255,255,255,0.72)",
                  fontSize: 12,
                  fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                  wordBreak: "break-all",
                }}
              >
                {pipeline.projectPath}
              </div>
            </div>
          )}

          {pipeline.projectSummary && (
            <div>
              <div
                className="flex items-center gap-2 mb-2"
                style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
              >
                <Terminal size={11} />
                目录扫描摘要
              </div>
              <div
                className="rounded-xl px-4 py-3"
                style={{
                  background: "rgba(0,0,0,0.22)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  color: "rgba(255,255,255,0.66)",
                  fontSize: 12,
                  lineHeight: 1.7,
                  whiteSpace: "pre-wrap",
                }}
              >
                {pipeline.projectSummary}
              </div>
            </div>
          )}

          {pipeline.requirementDocPath && (
            <div className="mt-4">
              <div
                className="flex items-center gap-2 mb-2"
                style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
              >
                <Terminal size={11} />
                需求文档落盘路径
              </div>
              <div
                className="rounded-xl px-4 py-3"
                style={{
                  background: "rgba(0,0,0,0.22)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  color: "rgba(255,255,255,0.72)",
                  fontSize: 12,
                  fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                  wordBreak: "break-all",
                }}
              >
                {pipeline.requirementDocPath}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-hidden flex gap-0">
        <div
          className="w-64 flex-shrink-0 overflow-y-auto p-4 space-y-2"
          style={{ borderRight: "1px solid rgba(255,255,255,0.05)" }}
        >
          {pipeline.stages.map((stage, index) => (
            <div key={stage.id} className="relative">
              <StageCard
                stage={stage}
                index={index}
                isActive={selectedStage === stage.id}
                onClick={() => setSelectedStage(stage.id)}
              />
              {index < pipeline.stages.length - 1 && (
                <div className="flex items-center justify-center py-0.5">
                  <div
                    className="w-px"
                    style={{
                      height: 12,
                      background:
                        pipeline.stages[index + 1].status !== "idle"
                          ? "rgba(91,114,255,0.3)"
                          : "rgba(255,255,255,0.06)",
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          {activeStage && (
            <div className="flex-1 overflow-y-auto">
              <div
                className="flex items-center justify-between px-6 py-4 sticky top-0 z-10"
                style={{
                  background: "#0d0d11",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center"
                    style={{
                      background: `${stageColors[activeStage.name] || "#5B72FF"}18`,
                      border: `1px solid ${stageColors[activeStage.name] || "#5B72FF"}30`,
                    }}
                  >
                    <Bot size={14} style={{ color: stageColors[activeStage.name] || "#5B72FF" }} />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "white" }}>
                      {activeStage.name}
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
                      {activeStage.agent} · {activeStage.nameEn}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {activeStage.duration !== undefined && activeStage.duration > 0 && (
                    <div className="text-right">
                      <div style={{ fontSize: 18, fontWeight: 600, color: "white" }}>
                        {activeStage.duration}s
                      </div>
                      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>执行时长</div>
                    </div>
                  )}
                  {activeStage.tokens && (
                    <div className="text-right">
                      <div style={{ fontSize: 18, fontWeight: 600, color: "white" }}>
                        {activeStage.tokens.toLocaleString()}
                      </div>
                      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>Tokens</div>
                    </div>
                  )}
                  <StatusBadge status={activeStage.status as any} />
                </div>
              </div>

              {activeStage.status === "awaiting_review" && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mx-6 mt-5 p-4 rounded-xl flex items-center justify-between"
                  style={{
                    background: "rgba(255,159,10,0.06)",
                    border: "1px solid rgba(255,159,10,0.2)",
                  }}
                >
                  <div className="flex items-center gap-3">
                    <CheckSquare size={16} style={{ color: "#FF9F0A" }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: "#FF9F0A" }}>
                        等待人工检查点审批
                      </div>
                      <div style={{ fontSize: 11, color: "rgba(255,159,10,0.6)" }}>
                        请审查以下 Agent 产出物，然后选择 Approve 或 Reject
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate("/checkpoints")}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg"
                    style={{
                      background: "rgba(255,159,10,0.15)",
                      border: "1px solid rgba(255,159,10,0.3)",
                      color: "#FF9F0A",
                      fontSize: 12,
                      fontWeight: 500,
                      cursor: "pointer",
                    }}
                  >
                    前往审批 <ChevronRight size={12} />
                  </button>
                </motion.div>
              )}

              {activeStage.status === "running" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mx-6 mt-5 p-3 rounded-xl flex items-center gap-3"
                  style={{
                    background: "rgba(91,114,255,0.06)",
                    border: "1px solid rgba(91,114,255,0.15)",
                  }}
                >
                  <div className="flex gap-1">
                    {[0, 1, 2].map((index) => (
                      <motion.div
                        key={index}
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1.2, repeat: Infinity, delay: index * 0.2 }}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: "#5B72FF" }}
                      />
                    ))}
                  </div>
                  <span style={{ fontSize: 12, color: "#7C8FFF" }}>
                    {activeStage.agent} 正在执行中...
                  </span>
                </motion.div>
              )}

              <div className="p-6">
                <div
                  className="flex items-center gap-2 mb-3"
                  style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", fontWeight: 500 }}
                >
                  <Terminal size={12} />
                  产出物
                </div>
                <OutputPanel stage={activeStage} />
              </div>
            </div>
          )}

          <div
            className="flex-shrink-0"
            style={{
              borderTop: "1px solid rgba(255,255,255,0.05)",
              maxHeight: showLogs ? 200 : 40,
              transition: "max-height 0.25s ease",
              overflow: "hidden",
            }}
          >
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="flex items-center gap-2 w-full px-5 py-2.5 hover:bg-white/[0.02] transition-colors"
              style={{ background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
            >
              <Terminal size={11} style={{ color: "rgba(255,255,255,0.35)" }} />
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", flex: 1 }}>
                Pipeline 运行日志
              </span>
              <ChevronDown
                size={12}
                style={{
                  color: "rgba(255,255,255,0.3)",
                  transform: showLogs ? "rotate(180deg)" : "none",
                  transition: "transform 0.2s",
                }}
              />
            </button>
            {showLogs && (
              <div
                className="overflow-y-auto px-5 pb-3"
                style={{
                  maxHeight: 160,
                  fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                }}
              >
                {logsQuery.error && (
                  <div style={{ fontSize: 11, color: "#FF453A", lineHeight: 1.8 }}>
                    {logsQuery.error}
                  </div>
                )}
                {logs.slice(0, logCount).map((log, index) => (
                  <motion.div
                    key={`${index}-${log}`}
                    initial={index >= logCount - 1 ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    style={{
                      fontSize: 11,
                      color: log.includes("✓")
                        ? "#34C759"
                        : log.includes("⏸")
                        ? "#FF9F0A"
                        : log.includes("ERROR") || log.includes("失败")
                        ? "#FF453A"
                        : "rgba(255,255,255,0.4)",
                      lineHeight: 1.8,
                    }}
                  >
                    {log}
                  </motion.div>
                ))}
                {pipeline.status === "running" && (
                  <motion.div
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.4, repeat: Infinity }}
                    style={{ fontSize: 11, color: "#5B72FF" }}
                  >
                    ▋
                  </motion.div>
                )}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

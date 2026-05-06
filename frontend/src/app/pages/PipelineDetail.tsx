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
  ExternalLink,
  GitBranch,
  GitCommitHorizontal,
  FolderTree,
  FileCode2,
} from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";
import { checkpointsApi, gitApi, pipelinesApi } from "../lib/api/services";
import { getErrorMessage } from "../lib/api/client";
import type { PipelineGitContext, PipelineStage } from "../types/pipeline";

const stageColors: Record<string, string> = {
  "需求分析": "#5B72FF",
  "方案设计": "#A259FF",
  "代码生成": "#FF7A5C",
  "测试生成": "#34C759",
  "代码评审": "#FF9F0A",
  "交付集成": "#00C7BE",
};

const stageTypeLabels: Record<string, string> = {
  requirement_analysis: "需求分析",
  solution_design: "方案设计",
  coding: "代码生成",
  testing: "测试生成",
  code_review: "代码评审",
  delivery: "交付集成",
};

type FileTreeNode = {
  name: string;
  path: string;
  kind: "dir" | "file";
  children: FileTreeNode[];
  stages: string[];
};

function shortSha(value: string | null | undefined) {
  return value ? value.slice(0, 8) : "未生成";
}

function normalizeGitDisplayPath(filePath: string, pipelineId: string | undefined) {
  const normalized = filePath.replace(/\\/g, "/").replace(/^\/+/, "");
  if (!normalized) {
    return normalized;
  }

  if (pipelineId) {
    const scopedPrefix = `.flowstate/${pipelineId}/`;
    if (normalized.startsWith(scopedPrefix)) {
      return normalized.slice(scopedPrefix.length);
    }
  }

  if (normalized.startsWith(".flowstate/")) {
    const parts = normalized.split("/").filter(Boolean);
    if (parts.length >= 4) {
      return parts.slice(2).join("/");
    }
  }

  return normalized;
}

function buildFileTree(git: PipelineGitContext | undefined, pipelineId: string | undefined) {
  const fileStages = new Map<string, Set<string>>();

  git?.stage_commits.forEach((commit) => {
    const stageLabel = stageTypeLabels[commit.stage_type] ?? commit.stage_type;
    commit.files_changed.forEach((filePath) => {
      const displayPath = normalizeGitDisplayPath(filePath, pipelineId);
      if (!displayPath) {
        return;
      }
      if (!fileStages.has(displayPath)) {
        fileStages.set(displayPath, new Set());
      }
      fileStages.get(displayPath)?.add(stageLabel);
    });
  });

  git?.total_files_changed.forEach((filePath) => {
    const displayPath = normalizeGitDisplayPath(filePath, pipelineId);
    if (!displayPath) {
      return;
    }
    if (!fileStages.has(displayPath)) {
      fileStages.set(displayPath, new Set());
    }
  });

  const roots: FileTreeNode[] = [];
  const index = new Map<string, FileTreeNode>();

  Array.from(fileStages.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .forEach(([filePath, stages]) => {
      const parts = filePath.split("/").filter(Boolean);
      let currentChildren = roots;
      let currentPath = "";

      parts.forEach((part, nodeIndex) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        const isFile = nodeIndex === parts.length - 1;
        let node = index.get(currentPath);

        if (!node) {
          node = {
            name: part,
            path: currentPath,
            kind: isFile ? "file" : "dir",
            children: [],
            stages: [],
          };
          index.set(currentPath, node);
          currentChildren.push(node);
        }

        if (isFile) {
          node.stages = Array.from(stages).sort((left, right) => left.localeCompare(right));
        }

        currentChildren = node.children;
      });
    });

  const sortNodes = (nodes: FileTreeNode[]) => {
    nodes.sort((left, right) => {
      if (left.kind !== right.kind) {
        return left.kind === "dir" ? -1 : 1;
      }
      return left.name.localeCompare(right.name);
    });
    nodes.forEach((node) => sortNodes(node.children));
  };

  sortNodes(roots);
  return roots;
}

function collectDirectoryPaths(nodes: FileTreeNode[]) {
  const paths: string[] = [];

  const visit = (entries: FileTreeNode[]) => {
    entries.forEach((node) => {
      if (node.kind === "dir") {
        paths.push(node.path);
        visit(node.children);
      }
    });
  };

  visit(nodes);
  return paths;
}

function GitFileTree({ nodes }: { nodes: FileTreeNode[] }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    setExpanded(new Set(collectDirectoryPaths(nodes)));
  }, [nodes]);

  if (!nodes.length) {
    return (
      <div
        className="rounded-xl px-4 py-4"
        style={{
          background: "rgba(0,0,0,0.22)",
          border: "1px solid rgba(255,255,255,0.06)",
          color: "rgba(255,255,255,0.5)",
          fontSize: 12,
        }}
      >
        当前还没有可展示的 Git 变更文件。
      </div>
    );
  }

  const toggle = (path: string) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const renderNode = (node: FileTreeNode, depth: number) => {
    const isDir = node.kind === "dir";
    const isOpen = expanded.has(node.path);

    return (
      <div key={node.path}>
        <button
          onClick={() => {
            if (isDir) {
              toggle(node.path);
            }
          }}
          className="w-full flex items-center gap-2 rounded-lg px-3 py-2 transition-colors hover:bg-white/[0.03]"
          style={{
            background: "none",
            border: "none",
            cursor: isDir ? "pointer" : "default",
            paddingLeft: 12 + depth * 18,
            textAlign: "left",
          }}
        >
          {isDir ? (
            <ChevronDown
              size={12}
              style={{
                color: "rgba(255,255,255,0.3)",
                transform: isOpen ? "rotate(0deg)" : "rotate(-90deg)",
                transition: "transform 0.2s",
              }}
            />
          ) : (
            <div style={{ width: 12 }} />
          )}

          {isDir ? (
            <FolderTree size={13} style={{ color: "rgba(124,143,255,0.9)" }} />
          ) : (
            <FileCode2 size={13} style={{ color: "rgba(255,255,255,0.58)" }} />
          )}

          <span
            style={{
              color: isDir ? "rgba(255,255,255,0.82)" : "rgba(255,255,255,0.68)",
              fontSize: 12,
              fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
              flex: 1,
              minWidth: 0,
            }}
            className="truncate"
          >
            {node.name}
          </span>

          {!isDir && node.stages.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap justify-end">
              {node.stages.map((stage) => (
                <span
                  key={`${node.path}-${stage}`}
                  className="px-1.5 py-0.5 rounded-md"
                  style={{
                    background: "rgba(91,114,255,0.08)",
                    border: "1px solid rgba(91,114,255,0.14)",
                    color: "rgba(160,171,255,0.92)",
                    fontSize: 10,
                    lineHeight: 1.2,
                  }}
                >
                  {stage}
                </span>
              ))}
            </div>
          )}
        </button>

        {isDir && isOpen && node.children.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div
      className="rounded-xl py-2"
      style={{
        background: "rgba(0,0,0,0.22)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {nodes.map((node) => renderNode(node, 0))}
    </div>
  );
}

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
  const [showProjectContext, setShowProjectContext] = useState(false);
  const [showGitContext, setShowGitContext] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<"pause" | "resume" | "cancel" | "retry" | "confirm-deps" | null>(null);
  const [pathActionMessage, setPathActionMessage] = useState<string | null>(null);
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

  const gitStatusQuery = useApiQuery(
    useCallback(
      (signal: AbortSignal) => {
        if (!id) {
          return Promise.reject(new Error("缺少流水线 ID"));
        }
        return gitApi.getStatus(id, { signal });
      },
      [id]
    ),
    [id],
    { enabled: Boolean(id) }
  );

  const pipeline = pipelineQuery.data;
  const logs = logsQuery.data ?? [];
  const git = gitStatusQuery.data;
  const gitFileTree = useMemo(() => buildFileTree(git, pipeline?.id), [git, pipeline?.id]);
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
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const syncPipeline = async () => {
    pipelineQuery.reload();
    logsQuery.reload();
    gitStatusQuery.reload();
  };

  const handlePathAction = async (
    targetPath: string | undefined,
    action: "open" | "reveal",
    label: string
  ) => {
    if (!targetPath) {
      return;
    }

    setPathActionMessage(null);

    try {
      if (window.api) {
        if (action === "reveal" && window.api.showItemInFolder) {
          await window.api.showItemInFolder(targetPath);
          return;
        }

        if (window.api.openPath) {
          const result = await window.api.openPath(targetPath);
          if (!result) {
            return;
          }
          throw new Error(result);
        }
      }

      await navigator.clipboard.writeText(targetPath);
      setPathActionMessage(`${label}路径已复制，请在本地文件管理器中打开。`);
    } catch (error) {
      setPathActionMessage(getErrorMessage(error));
    }
  };

  const runPipelineAction = async (
    action: "pause" | "resume" | "cancel" | "retry",
    request: () => Promise<unknown>
  ) => {
    if (!id || actionLoading) {
      return;
    }
    setActionError(null);
    setActionLoading(action);
    try {
      await request();
      await syncPipeline();
    } catch (error) {
      setActionError(getErrorMessage(error));
    } finally {
      setActionLoading(null);
    }
  };

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
                onClick={() =>
                  runPipelineAction("pause", () => pipelinesApi.pause(pipeline.id))
                }
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                style={{
                  background: "rgba(255,159,10,0.1)",
                  border: "1px solid rgba(255,159,10,0.2)",
                  color: "#FF9F0A",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                <Pause size={12} /> {actionLoading === "pause" ? "暂停中..." : "暂停"}
              </button>
              <button
                onClick={() =>
                  runPipelineAction("cancel", () => pipelinesApi.cancel(pipeline.id))
                }
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                style={{
                  background: "rgba(255,69,58,0.08)",
                  border: "1px solid rgba(255,69,58,0.15)",
                  color: "#FF453A",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                <StopCircle size={12} /> {actionLoading === "cancel" ? "终止中..." : "终止"}
              </button>
            </>
          )}
          {(pipeline.status === "paused" || pipeline.status === "failed") && (
            <button
              onClick={() => {
                if (pipeline.status === "paused" && activeStage?.status === "awaiting_review") {
                  navigate("/checkpoints");
                  return;
                }
                runPipelineAction(
                  pipeline.status === "paused" ? "resume" : "retry",
                  () =>
                    pipeline.status === "paused"
                      ? pipelinesApi.resume(pipeline.id)
                      : pipelinesApi.retry(pipeline.id)
                );
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              style={{
                background: "rgba(91,114,255,0.1)",
                border: "1px solid rgba(91,114,255,0.2)",
                color: "#7C8FFF",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              {pipeline.status === "paused" ? (
                <>
                  <Play size={12} /> {activeStage?.status === "awaiting_review" ? "前往审批" : actionLoading === "resume" ? "继续中..." : "继续"}
                </>
              ) : (
                <>
                  <RotateCcw size={12} /> {actionLoading === "retry" ? "重试中..." : "重试"}
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {actionError && (
        <div className="mx-6 mt-4 rounded-xl px-4 py-3" style={{ background: "rgba(255,69,58,0.06)", border: "1px solid rgba(255,69,58,0.18)", color: "rgba(255,255,255,0.78)", fontSize: 12 }}>
          {actionError}
        </div>
      )}

      {(pipeline.projectPath || pipeline.projectSummary || pipeline.requirementDocPath || pipeline.solutionDocPath) && (
        <div
          className="mx-6 mt-5 rounded-2xl flex-shrink-0 overflow-hidden"
          style={{
            background: "rgba(255,255,255,0.025)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <button
            onClick={() => setShowProjectContext(!showProjectContext)}
            className="flex items-center gap-2 w-full px-5 py-3 hover:bg-white/[0.02] transition-colors"
            style={{ background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
          >
            <FileSearch size={13} style={{ color: "rgba(255,255,255,0.45)" }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)", flex: 1 }}>
              项目上下文
            </span>
            <ChevronDown
              size={12}
              style={{
                color: "rgba(255,255,255,0.3)",
                transform: showProjectContext ? "rotate(180deg)" : "none",
                transition: "transform 0.2s",
              }}
            />
          </button>

          {showProjectContext && (
            <div className="px-5 pb-5 space-y-4">
              {pipeline.projectPath && (
                <div>
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <div
                      className="flex items-center gap-2"
                      style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                    >
                      <FolderOpen size={11} />
                      项目本地目录
                    </div>
                    <button
                      onClick={() => handlePathAction(pipeline.projectPath, "reveal", "项目目录")}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
                      style={{
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        color: "rgba(255,255,255,0.62)",
                        fontSize: 11,
                        cursor: "pointer",
                      }}
                    >
                      <FolderOpen size={11} />
                      打开目录
                    </button>
                  </div>
                  <div
                    className="rounded-xl px-4 py-2.5"
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
                    className="rounded-xl px-4 py-2.5"
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

              {(pipeline.requirementDocPath || pipeline.solutionDocPath) && (
                <div className="flex gap-4">
                  {pipeline.requirementDocPath && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span
                          style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                        >
                          需求文档
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handlePathAction(pipeline.requirementDocPath, "open", "需求文档")}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg"
                            style={{
                              background: "rgba(91,114,255,0.08)",
                              border: "1px solid rgba(91,114,255,0.18)",
                              color: "#A0ABFF",
                              fontSize: 10,
                              cursor: "pointer",
                            }}
                          >
                            <ExternalLink size={10} />
                            打开
                          </button>
                          <button
                            onClick={() => handlePathAction(pipeline.requirementDocPath, "reveal", "需求文档")}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg"
                            style={{
                              background: "rgba(255,255,255,0.04)",
                              border: "1px solid rgba(255,255,255,0.08)",
                              color: "rgba(255,255,255,0.62)",
                              fontSize: 10,
                              cursor: "pointer",
                            }}
                          >
                            <FolderOpen size={10} />
                            定位
                          </button>
                        </div>
                      </div>
                      <div
                        className="rounded-xl px-3 py-2 truncate"
                        style={{
                          background: "rgba(0,0,0,0.22)",
                          border: "1px solid rgba(255,255,255,0.06)",
                          color: "rgba(255,255,255,0.72)",
                          fontSize: 12,
                          fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                        }}
                      >
                        {pipeline.requirementDocPath}
                      </div>
                    </div>
                  )}

                  {pipeline.solutionDocPath && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span
                          style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                        >
                          方案文档
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handlePathAction(pipeline.solutionDocPath, "open", "方案文档")}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg"
                            style={{
                              background: "rgba(162,89,255,0.08)",
                              border: "1px solid rgba(162,89,255,0.18)",
                              color: "#C7A7FF",
                              fontSize: 10,
                              cursor: "pointer",
                            }}
                          >
                            <ExternalLink size={10} />
                            打开
                          </button>
                          <button
                            onClick={() => handlePathAction(pipeline.solutionDocPath, "reveal", "方案文档")}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg"
                            style={{
                              background: "rgba(255,255,255,0.04)",
                              border: "1px solid rgba(255,255,255,0.08)",
                              color: "rgba(255,255,255,0.62)",
                              fontSize: 10,
                              cursor: "pointer",
                            }}
                          >
                            <FolderOpen size={10} />
                            定位
                          </button>
                        </div>
                      </div>
                      <div
                        className="rounded-xl px-3 py-2 truncate"
                        style={{
                          background: "rgba(0,0,0,0.22)",
                          border: "1px solid rgba(255,255,255,0.06)",
                          color: "rgba(255,255,255,0.72)",
                          fontSize: 12,
                          fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                        }}
                      >
                        {pipeline.solutionDocPath}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {pathActionMessage && (
                <div
                  className="rounded-xl px-4 py-3"
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.72)",
                    fontSize: 12,
                  }}
                >
                  {pathActionMessage}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {(pipeline.projectPath || git || gitStatusQuery.loading || gitStatusQuery.error) && (
        <div
          className="mx-6 mt-4 rounded-2xl flex-shrink-0 overflow-hidden"
          style={{
            background: "rgba(255,255,255,0.025)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <button
            onClick={() => setShowGitContext(!showGitContext)}
            className="flex items-center gap-2 w-full px-5 py-3 hover:bg-white/[0.02] transition-colors"
            style={{ background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
          >
            <GitBranch size={13} style={{ color: "rgba(255,255,255,0.45)" }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)", flex: 1 }}>
              Git 工作树
            </span>
            <ChevronDown
              size={12}
              style={{
                color: "rgba(255,255,255,0.3)",
                transform: showGitContext ? "rotate(180deg)" : "none",
                transition: "transform 0.2s",
              }}
            />
          </button>

          {showGitContext && (
            <div className="px-5 pb-5 space-y-5">
              {gitStatusQuery.loading && !git && (
                <div
                  className="rounded-xl px-4 py-4"
                  style={{
                    background: "rgba(0,0,0,0.22)",
                    border: "1px solid rgba(255,255,255,0.06)",
                    color: "rgba(255,255,255,0.5)",
                    fontSize: 12,
                  }}
                >
                  正在加载 Git 状态...
                </div>
              )}

              {gitStatusQuery.error && !gitStatusQuery.loading && (
                <div
                  className="rounded-xl px-4 py-4"
                  style={{
                    background: "rgba(255,69,58,0.06)",
                    border: "1px solid rgba(255,69,58,0.18)",
                    color: "rgba(255,255,255,0.78)",
                    fontSize: 12,
                  }}
                >
                  {gitStatusQuery.error}
                </div>
              )}

              {git && (
                <>
                  <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                    <div
                      className="rounded-xl px-4 py-3"
                      style={{ background: "rgba(0,0,0,0.22)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", marginBottom: 6 }}>
                        基线分支
                      </div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.82)", fontWeight: 500 }}>
                        {git.base_branch ?? "未识别"}
                      </div>
                    </div>
                    <div
                      className="rounded-xl px-4 py-3"
                      style={{ background: "rgba(0,0,0,0.22)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", marginBottom: 6 }}>
                        工作分支
                      </div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.82)", fontWeight: 500 }}>
                        {git.working_branch ?? "未创建"}
                      </div>
                    </div>
                    <div
                      className="rounded-xl px-4 py-3"
                      style={{ background: "rgba(0,0,0,0.22)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", marginBottom: 6 }}>
                        当前 Head
                      </div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.82)", fontWeight: 500 }}>
                        {shortSha(git.head_commit)}
                      </div>
                    </div>
                    <div
                      className="rounded-xl px-4 py-3"
                      style={{ background: "rgba(0,0,0,0.22)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", marginBottom: 6 }}>
                        变更文件
                      </div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.82)", fontWeight: 500 }}>
                        {git.total_files_changed.length} 个
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.95fr)] gap-4">
                    <div className="min-w-0">
                      <div
                        className="flex items-center gap-2 mb-2"
                        style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                      >
                        <FolderTree size={11} />
                        变更文件树
                      </div>
                      <GitFileTree nodes={gitFileTree} />
                    </div>

                    <div className="min-w-0">
                      <div
                        className="flex items-center gap-2 mb-2"
                        style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                      >
                        <GitCommitHorizontal size={11} />
                        阶段提交
                      </div>
                      <div className="space-y-3">
                        {git.stage_commits.length === 0 && (
                          <div
                            className="rounded-xl px-4 py-4"
                            style={{
                              background: "rgba(0,0,0,0.22)",
                              border: "1px solid rgba(255,255,255,0.06)",
                              color: "rgba(255,255,255,0.5)",
                              fontSize: 12,
                            }}
                          >
                            当前还没有 stage commit。
                          </div>
                        )}

                        {git.stage_commits.map((commit) => (
                          <div
                            key={`${commit.stage_type}-${commit.commit_sha}`}
                            className="rounded-xl px-4 py-3"
                            style={{
                              background: "rgba(0,0,0,0.22)",
                              border: "1px solid rgba(255,255,255,0.06)",
                            }}
                          >
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <div>
                                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.84)", fontWeight: 500 }}>
                                  {stageTypeLabels[commit.stage_type] ?? commit.stage_type}
                                </div>
                                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>
                                  {new Date(commit.committed_at).toLocaleString("zh-CN")}
                                </div>
                              </div>
                              <span
                                style={{
                                  fontSize: 11,
                                  color: "rgba(160,171,255,0.9)",
                                  fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                                }}
                              >
                                {shortSha(commit.commit_sha)}
                              </span>
                            </div>
                            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.66)", lineHeight: 1.6 }}>
                              {commit.commit_message}
                            </div>
                            {commit.files_changed.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-1.5">
                                {commit.files_changed.map((filePath) => {
                                  const displayPath = normalizeGitDisplayPath(filePath, pipeline.id);
                                  return (
                                  <span
                                    key={`${commit.commit_sha}-${filePath}`}
                                    className="px-2 py-1 rounded-lg"
                                    style={{
                                      background: "rgba(255,255,255,0.04)",
                                      border: "1px solid rgba(255,255,255,0.07)",
                                      color: "rgba(255,255,255,0.58)",
                                      fontSize: 10,
                                      fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                                    }}
                                  >
                                    {displayPath}
                                  </span>
                                )})}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {(git.repo_root || git.pr_command || git.pr_url) && (
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                      <div className="space-y-4">
                        {git.repo_root && (
                          <div>
                            <div
                              className="flex items-center justify-between gap-3 mb-2"
                              style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                            >
                              <span>仓库根目录</span>
                              <button
                                onClick={() => handlePathAction(git.repo_root ?? undefined, "reveal", "仓库目录")}
                                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
                                style={{
                                  background: "rgba(255,255,255,0.04)",
                                  border: "1px solid rgba(255,255,255,0.08)",
                                  color: "rgba(255,255,255,0.62)",
                                  fontSize: 11,
                                  cursor: "pointer",
                                }}
                              >
                                <FolderOpen size={11} />
                                打开目录
                              </button>
                            </div>
                            <div
                              className="rounded-xl px-4 py-2.5"
                              style={{
                                background: "rgba(0,0,0,0.22)",
                                border: "1px solid rgba(255,255,255,0.06)",
                                color: "rgba(255,255,255,0.72)",
                                fontSize: 12,
                                fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                                wordBreak: "break-all",
                              }}
                            >
                              {git.repo_root}
                            </div>
                          </div>
                        )}

                        {git.pr_url && (
                          <div>
                            <div
                              className="flex items-center gap-2 mb-2"
                              style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                            >
                              <ExternalLink size={11} />
                              Pull Request
                            </div>
                            <a
                              href={git.pr_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 rounded-xl px-4 py-3 hover:bg-white/[0.04] transition-colors"
                              style={{
                                background: "rgba(0,209,88,0.06)",
                                border: "1px solid rgba(0,209,88,0.2)",
                                color: "#34C759",
                                fontSize: 12,
                                fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                                wordBreak: "break-all",
                                textDecoration: "none",
                              }}
                            >
                              <ExternalLink size={12} style={{ flexShrink: 0 }} />
                              {git.pr_url}
                            </a>
                          </div>
                        )}
                      </div>

                      {git.pr_command && (
                        <div>
                          <div
                            className="flex items-center gap-2 mb-2"
                            style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", fontWeight: 500 }}
                          >
                            <Terminal size={11} />
                            {git.pr_url ? "PR 命令（已自动创建）" : "PR 命令（手动运行）"}
                          </div>
                          <div
                            className="rounded-xl px-4 py-3"
                            style={{
                              background: "rgba(0,0,0,0.22)",
                              border: "1px solid rgba(255,255,255,0.06)",
                              color: git.pr_url ? "rgba(255,255,255,0.38)" : "rgba(255,255,255,0.72)",
                              fontSize: 12,
                              fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                              lineHeight: 1.7,
                              whiteSpace: "pre-wrap",
                            }}
                          >
                            {git.pr_command}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
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

              {activeStage.status === "awaiting_review" && activeStage.subPhase === "deps_confirm" ? (
                // ── Testing Phase 1: 依赖确认 Banner ──
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mx-6 mt-5 p-4 rounded-xl"
                  style={{
                    background: "rgba(48,209,88,0.06)",
                    border: "1px solid rgba(48,209,88,0.2)",
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <CheckSquare size={16} style={{ color: "#30D158" }} />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: "#30D158" }}>
                          需要安装测试依赖
                        </div>
                        <div style={{ fontSize: 11, color: "rgba(48,209,88,0.6)" }}>
                          确认后将自动安装依赖并执行测试
                        </div>
                      </div>
                    </div>
                    <button
                      disabled={actionLoading === "confirm-deps"}
                      onClick={async () => {
                        if (!id) return;
                        setActionLoading("confirm-deps");
                        try {
                          // checkpoint id format: cp-{pipelineId}-testing
                          const checkpointId = `cp-${id}-testing`;
                          await checkpointsApi.confirmDeps(checkpointId);
                          await syncPipeline();
                        } catch (e) {
                          setActionError(e instanceof Error ? e.message : "操作失败");
                        } finally {
                          setActionLoading(null);
                        }
                      }}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg"
                      style={{
                        background: actionLoading === "confirm-deps" ? "rgba(48,209,88,0.08)" : "rgba(48,209,88,0.15)",
                        border: "1px solid rgba(48,209,88,0.3)",
                        color: "#30D158",
                        fontSize: 12,
                        fontWeight: 500,
                        cursor: actionLoading === "confirm-deps" ? "not-allowed" : "pointer",
                        opacity: actionLoading === "confirm-deps" ? 0.6 : 1,
                      }}
                    >
                      {actionLoading === "confirm-deps" ? "安装中..." : "确认安装并运行测试"}
                    </button>
                  </div>
                  {/* 依赖清单 */}
                  {activeStage.depsManifest && (
                    <div
                      className="rounded-lg p-3 mt-1"
                      style={{ background: "rgba(0,0,0,0.2)", fontSize: 11 }}
                    >
                      {(activeStage.depsManifest.pip_packages ?? []).length > 0 && (
                        <div className="mb-1">
                          <span style={{ color: "rgba(255,255,255,0.4)" }}>pip: </span>
                          <span style={{ color: "rgba(255,255,255,0.75)" }}>
                            {activeStage.depsManifest.pip_packages!.join("  ")}
                          </span>
                        </div>
                      )}
                      {(activeStage.depsManifest.npm_packages ?? []).length > 0 && (
                        <div>
                          <span style={{ color: "rgba(255,255,255,0.4)" }}>npm: </span>
                          <span style={{ color: "rgba(255,255,255,0.75)" }}>
                            {activeStage.depsManifest.npm_packages!.join("  ")}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ) : activeStage.status === "awaiting_review" ? (
                // ── 普通 Checkpoint 审批 Banner ──
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
              ) : null}

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
                {logs.map((log, index) => (
                  <motion.div
                    key={`${index}-${log}`}
                    initial={{ opacity: 0 }}
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

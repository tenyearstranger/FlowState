import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  Plus,
  Search,
  GitBranch,
  ArrowRight,
  X,
  Zap,
  Filter,
  RotateCcw,
  FolderOpen,
} from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";
import { getErrorMessage } from "../lib/api/client";
import { pipelinesApi } from "../lib/api/services";
import type { CreatePipelinePayload, Pipeline } from "../types/pipeline";

const stageLabels = ["需求分析", "方案设计", "代码生成", "测试生成", "代码评审", "交付集成"];

function NewPipelineModal({ onClose }: { onClose: () => void }) {
  const [projectPath, setProjectPath] = useState("");
  const [requirement, setRequirement] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [choosingDirectory, setChoosingDirectory] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChooseDirectory = async () => {
    if (choosingDirectory) {
      return;
    }

    setChoosingDirectory(true);
    setSubmitError(null);

    try {
      if (window.api?.chooseDirectory) {
        const selectedPath = await window.api.chooseDirectory();
        if (selectedPath) {
          setProjectPath(selectedPath);
        }
        return;
      }

      const picker = (window as Window & {
        showDirectoryPicker?: () => Promise<{ name?: string }>;
      }).showDirectoryPicker;

      if (picker) {
        await picker();
        setSubmitError(
          "浏览器环境无法读取文件夹绝对路径，请手动粘贴项目本地目录，或使用桌面版的“打开文件夹”按钮。"
        );
        return;
      }

      setSubmitError("当前环境不支持目录选择器，请手动输入项目本地目录。");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setSubmitError("打开目录选择器失败，请重试或手动输入项目本地目录。");
    } finally {
      setChoosingDirectory(false);
    }
  };

  const handleSubmit = async () => {
    if (!projectPath.trim() || !requirement.trim() || submitting) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    const payload: CreatePipelinePayload = {
      projectPath: projectPath.trim(),
      requirement: requirement.trim(),
    };

    try {
      const pipeline = await pipelinesApi.create(payload);
      onClose();
      navigate(`/pipelines/${pipeline.id}`);
    } catch (error) {
      setSubmitError(getErrorMessage(error));
      setSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
        className="w-[540px] rounded-2xl overflow-hidden"
        style={{
          background: "#141418",
          border: "1px solid rgba(255,255,255,0.1)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
        }}
      >
        <div
          className="flex items-center justify-between px-6 py-5"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "white" }}>新建流水线</h2>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
              输入项目目录与自然语言需求，AI 将直接开始处理
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/[0.06] transition-colors"
            style={{ background: "none", border: "none", cursor: "pointer" }}
          >
            <X size={14} style={{ color: "rgba(255,255,255,0.5)" }} />
          </button>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            <div>
              <label
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "rgba(255,255,255,0.5)",
                  display: "block",
                  marginBottom: 8,
                }}
              >
                项目本地目录
              </label>
              <div className="flex gap-2">
                <input
                  value={projectPath}
                  onChange={(event) => setProjectPath(event.target.value)}
                  placeholder="请输入项目本地绝对路径，例如 /Users/yuki/code/my-project"
                  className="flex-1 rounded-xl px-4 py-3"
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.85)",
                    fontSize: 13,
                    outline: "none",
                  }}
                  onFocus={(event) =>
                    (event.target.style.border = "1px solid rgba(91,114,255,0.4)")
                  }
                  onBlur={(event) =>
                    (event.target.style.border = "1px solid rgba(255,255,255,0.08)")
                  }
                />
                <button
                  type="button"
                  onClick={handleChooseDirectory}
                  disabled={choosingDirectory}
                  className="flex items-center gap-2 px-4 rounded-xl"
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: choosingDirectory ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.72)",
                    cursor: choosingDirectory ? "not-allowed" : "pointer",
                    fontSize: 12,
                    flexShrink: 0,
                  }}
                >
                  <FolderOpen size={13} />
                  {choosingDirectory ? "打开中..." : "打开文件夹"}
                </button>
              </div>
            </div>

            <div>
              <label
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "rgba(255,255,255,0.5)",
                  display: "block",
                  marginBottom: 8,
                }}
              >
                自然语言需求
              </label>
              <textarea
                value={requirement}
                onChange={(event) => setRequirement(event.target.value)}
                placeholder="用自然语言描述你的需求，AI 将直接结合项目目录进行分析。

例如：在现有项目中实现一个用户收藏功能，允许用户收藏文章，并提供收藏列表页面，支持分页和排序。"
                className="w-full rounded-xl px-4 py-3 resize-none"
                rows={6}
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "rgba(255,255,255,0.85)",
                  fontSize: 13,
                  outline: "none",
                  lineHeight: 1.6,
                }}
                onFocus={(event) =>
                  (event.target.style.border = "1px solid rgba(91,114,255,0.4)")
                }
                onBlur={(event) =>
                  (event.target.style.border = "1px solid rgba(255,255,255,0.08)")
                }
              />
            </div>

            <div
              className="flex items-start gap-2 p-3 rounded-lg"
              style={{ background: "rgba(91,114,255,0.06)", border: "1px solid rgba(91,114,255,0.12)" }}
            >
              <Zap size={12} style={{ color: "#7C8FFF", marginTop: 1, flexShrink: 0 }} />
              <p style={{ fontSize: 11.5, color: "rgba(255,255,255,0.45)", lineHeight: 1.5 }}>
                AI 会先读取你提供的项目本地目录，再基于自然语言需求生成 6 阶段 Pipeline，并在关键检查点等待审批。
              </p>
            </div>

            {submitError && (
              <div
                className="rounded-xl px-4 py-3"
                style={{
                  background: "rgba(255,69,58,0.06)",
                  border: "1px solid rgba(255,69,58,0.18)",
                  color: "rgba(255,255,255,0.72)",
                  fontSize: 12,
                }}
              >
                {submitError}
              </div>
            )}
          </div>
        </div>

        <div
          className="flex items-center justify-end gap-3 px-6 py-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg"
            style={{
              fontSize: 13,
              color: "rgba(255,255,255,0.5)",
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.08)",
              cursor: "pointer",
            }}
          >
            取消
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={!projectPath.trim() || !requirement.trim() || submitting}
            onClick={handleSubmit}
            className="flex items-center gap-1.5 px-5 py-2 rounded-lg"
            style={{
              fontSize: 13,
              fontWeight: 500,
              background: projectPath.trim() && requirement.trim() && !submitting
                ? "linear-gradient(135deg, #5B72FF, #A259FF)"
                : "rgba(255,255,255,0.06)",
              color: projectPath.trim() && requirement.trim() && !submitting ? "white" : "rgba(255,255,255,0.3)",
              border: "none",
              cursor: projectPath.trim() && requirement.trim() && !submitting ? "pointer" : "not-allowed",
              boxShadow: projectPath.trim() && requirement.trim() && !submitting ? "0 4px 14px rgba(91,114,255,0.3)" : "none",
            }}
          >
            <Zap size={13} /> {submitting ? "创建中..." : "启动 Pipeline"}
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export function Pipelines() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const pipelinesQuery = useApiQuery(
    useCallback((signal: AbortSignal) => pipelinesApi.list({ signal }), []),
    []
  );

  const pipelines = pipelinesQuery.data ?? [];
  const filtered = useMemo(
    () =>
      pipelines.filter((pipeline) => {
        const matchSearch =
          search === "" ||
          pipeline.name.toLowerCase().includes(search.toLowerCase()) ||
          pipeline.description.toLowerCase().includes(search.toLowerCase());
        const matchFilter = filter === "all" || pipeline.status === filter;
        return matchSearch && matchFilter;
      }),
    [filter, pipelines, search]
  );

  return (
    <div className="h-full flex flex-col">
      <div
        className="flex items-center justify-between px-8 py-5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            流水线
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            {pipelinesQuery.loading ? "正在加载..." : `${pipelines.length} 条流水线`}
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl"
          style={{
            background: "linear-gradient(135deg, #5B72FF, #A259FF)",
            fontSize: 13,
            fontWeight: 500,
            color: "white",
            border: "none",
            cursor: "pointer",
            boxShadow: "0 4px 16px rgba(91,114,255,0.3)",
          }}
        >
          <Plus size={14} />
          新建流水线
        </motion.button>
      </div>

      {pipelinesQuery.error && (
        <div className="px-8 pt-5">
          <div
            className="rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {pipelinesQuery.error}
            </span>
            <button
              onClick={pipelinesQuery.reload}
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
        className="flex items-center gap-4 px-8 py-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        <div className="relative flex-1 max-w-xs">
          <Search
            size={13}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "rgba(255,255,255,0.3)" }}
          />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="搜索流水线..."
            className="w-full pl-9 pr-3 py-2 rounded-lg"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.07)",
              color: "rgba(255,255,255,0.8)",
              fontSize: 12,
              outline: "none",
            }}
          />
        </div>

        <div className="flex items-center gap-1">
          <Filter size={11} style={{ color: "rgba(255,255,255,0.3)" }} />
          {["all", "running", "paused", "completed", "failed", "cancelled"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className="px-3 py-1 rounded-lg transition-all"
              style={{
                fontSize: 11,
                background: filter === status ? "rgba(91,114,255,0.15)" : "rgba(255,255,255,0.03)",
                color: filter === status ? "#A0ABFF" : "rgba(255,255,255,0.4)",
                border: `1px solid ${
                  filter === status ? "rgba(91,114,255,0.25)" : "rgba(255,255,255,0.06)"
                }`,
                cursor: "pointer",
              }}
            >
              {status === "all"
                ? "全部"
                : status === "running"
                ? "运行中"
                : status === "paused"
                ? "暂停"
                : status === "completed"
                ? "已完成"
                : status === "failed"
                ? "失败"
                : "已终止"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-5 space-y-3">
        {filtered.map((pipeline, index) => (
          <PipelineCard
            key={pipeline.id}
            pipeline={pipeline}
            index={index}
            onClick={() => navigate(`/pipelines/${pipeline.id}`)}
          />
        ))}
        {!pipelinesQuery.loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <GitBranch size={32} style={{ color: "rgba(255,255,255,0.1)", marginBottom: 12 }} />
            <p style={{ fontSize: 14, color: "rgba(255,255,255,0.3)" }}>
              {search || filter !== "all" ? "未找到匹配的流水线" : "暂无流水线数据"}
            </p>
          </div>
        )}
      </div>

      <AnimatePresence>
        {showModal && <NewPipelineModal onClose={() => setShowModal(false)} />}
      </AnimatePresence>
    </div>
  );
}

function PipelineCard({
  pipeline,
  index,
  onClick,
}: {
  pipeline: Pipeline;
  index: number;
  onClick: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      whileHover={{ y: -1 }}
      onClick={onClick}
      className="rounded-2xl p-5 cursor-pointer group"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.07)",
        transition: "all 0.15s ease",
      }}
      onMouseEnter={(event) =>
        (event.currentTarget.style.border = "1px solid rgba(255,255,255,0.12)")
      }
      onMouseLeave={(event) =>
        (event.currentTarget.style.border = "1px solid rgba(255,255,255,0.07)")
      }
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 pr-4">
          <div className="flex items-center gap-2 mb-1">
            <h3
              style={{ fontSize: 14, fontWeight: 500, color: "rgba(255,255,255,0.9)" }}
              className="truncate"
            >
              {pipeline.name}
            </h3>
            {pipeline.template && (
              <span
                style={{
                  fontSize: 10,
                  color: "rgba(255,255,255,0.35)",
                  background: "rgba(255,255,255,0.06)",
                  padding: "1px 7px",
                  borderRadius: 4,
                  flexShrink: 0,
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                {pipeline.template}
              </span>
            )}
          </div>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }} className="truncate">
            {pipeline.description}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={pipeline.status} size="sm" />
          <ArrowRight
            size={14}
            className="opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color: "rgba(255,255,255,0.4)" }}
          />
        </div>
      </div>

      <div className="flex items-center gap-1 mb-3">
        {stageLabels.map((label, stageIndex) => {
          const stage = pipeline.stages[stageIndex];
          const status = stage?.status || "idle";
          return (
            <div key={label} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full h-1 rounded-full overflow-hidden"
                style={{ background: "rgba(255,255,255,0.06)" }}
              >
                <motion.div
                  className="h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{
                    width:
                      status === "completed" ? "100%" :
                      status === "running" ? "60%" :
                      "0%",
                  }}
                  transition={{ duration: 0.6, delay: 0.1 * stageIndex }}
                  style={{
                    background:
                      status === "completed" ? "#34C759" :
                      status === "running" ? "#5B72FF" :
                      status === "failed" ? "#FF453A" :
                      status === "awaiting_review" ? "#FF9F0A" :
                      "transparent",
                  }}
                />
              </div>
              <span
                style={{
                  fontSize: 9,
                  color:
                    status === "completed" ? "rgba(52,199,89,0.7)" :
                    status === "running" ? "rgba(91,114,255,0.9)" :
                    status === "awaiting_review" ? "rgba(255,159,10,0.8)" :
                    "rgba(255,255,255,0.2)",
                  fontWeight: status === "running" ? 500 : 400,
                }}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            {pipeline.id}
          </span>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.2)" }}>·</span>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            更新于 {new Date(pipeline.updatedAt).toLocaleString("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
        <span style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
          {pipeline.progress}%
        </span>
      </div>
    </motion.div>
  );
}

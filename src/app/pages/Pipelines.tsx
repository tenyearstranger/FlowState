import { useState } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  Plus,
  Search,
  GitBranch,
  ArrowRight,
  X,
  Zap,
  AlertCircle,
  TrendingUp,
  ChevronRight,
  Filter,
} from "lucide-react";
import { mockPipelines, type Pipeline } from "../data/mockData";
import { StatusBadge } from "../components/ui/StatusBadge";

const stageLabels = ["需求分析", "方案设计", "代码生成", "测试生成", "代码评审", "交付集成"];

const templates = [
  { id: "feature", label: "新功能开发", desc: "6 阶段完整流程", icon: Zap, color: "#5B72FF" },
  { id: "bugfix", label: "Bug 修复", desc: "精简 4 阶段", icon: AlertCircle, color: "#FF9F0A" },
  { id: "refactor", label: "重构优化", desc: "含架构评审", icon: TrendingUp, color: "#A259FF" },
];

function NewPipelineModal({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState<"template" | "input">("template");
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [requirement, setRequirement] = useState("");
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
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
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-5"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "white" }}>新建流水线</h2>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
              {step === "template" ? "选择流程模板" : "描述你的需求"}
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
          {step === "template" ? (
            <div className="space-y-3">
              {templates.map((t) => (
                <motion.button
                  key={t.id}
                  whileHover={{ x: 2 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setSelectedTemplate(t.id)}
                  className="w-full flex items-center gap-4 p-4 rounded-xl transition-all"
                  style={{
                    background:
                      selectedTemplate === t.id
                        ? `${t.color}12`
                        : "rgba(255,255,255,0.03)",
                    border: `1px solid ${
                      selectedTemplate === t.id
                        ? `${t.color}35`
                        : "rgba(255,255,255,0.07)"
                    }`,
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: `${t.color}18` }}
                  >
                    <t.icon size={16} style={{ color: t.color }} />
                  </div>
                  <div className="flex-1">
                    <div style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                      {t.label}
                    </div>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 1 }}>
                      {t.desc}
                    </div>
                  </div>
                  {selectedTemplate === t.id && (
                    <div
                      className="w-5 h-5 rounded-full flex items-center justify-center"
                      style={{ background: t.color }}
                    >
                      <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
                        <path d="M1 3.5L3.5 6L8 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    </div>
                  )}
                </motion.button>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label
                  style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: 8 }}
                >
                  需求描述
                </label>
                <textarea
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                  placeholder="用自然语言描述你的需求，AI 将自动拆解为多阶段 Pipeline 任务...

例如：实现一个用户收藏功能，允许用户收藏文章，并提供收藏列表页面，支持分页和排序。"
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
                  onFocus={(e) =>
                    (e.target.style.border = "1px solid rgba(91,114,255,0.4)")
                  }
                  onBlur={(e) =>
                    (e.target.style.border = "1px solid rgba(255,255,255,0.08)")
                  }
                />
              </div>

              <div
                className="flex items-start gap-2 p-3 rounded-lg"
                style={{ background: "rgba(91,114,255,0.06)", border: "1px solid rgba(91,114,255,0.12)" }}
              >
                <Zap size={12} style={{ color: "#7C8FFF", marginTop: 1, flexShrink: 0 }} />
                <p style={{ fontSize: 11.5, color: "rgba(255,255,255,0.45)", lineHeight: 1.5 }}>
                  AI 将自动分析需求，通过 <strong style={{ color: "rgba(255,255,255,0.6)" }}>6 个阶段</strong> 逐步完成从需求到代码的全链路自动化。你将在关键检查点参与审批。
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          {step === "template" ? (
            <>
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
                disabled={!selectedTemplate}
                onClick={() => setStep("input")}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg"
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  background: selectedTemplate
                    ? "linear-gradient(135deg, #5B72FF, #A259FF)"
                    : "rgba(255,255,255,0.06)",
                  color: selectedTemplate ? "white" : "rgba(255,255,255,0.3)",
                  border: "none",
                  cursor: selectedTemplate ? "pointer" : "not-allowed",
                  boxShadow: selectedTemplate ? "0 4px 14px rgba(91,114,255,0.3)" : "none",
                }}
              >
                下一步 <ChevronRight size={13} />
              </motion.button>
            </>
          ) : (
            <>
              <button
                onClick={() => setStep("template")}
                className="px-4 py-2 rounded-lg"
                style={{
                  fontSize: 13,
                  color: "rgba(255,255,255,0.5)",
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  cursor: "pointer",
                }}
              >
                上一步
              </button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={!requirement.trim()}
                onClick={() => {
                  onClose();
                  navigate("/pipelines/pl-001");
                }}
                className="flex items-center gap-1.5 px-5 py-2 rounded-lg"
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  background: requirement.trim()
                    ? "linear-gradient(135deg, #5B72FF, #A259FF)"
                    : "rgba(255,255,255,0.06)",
                  color: requirement.trim() ? "white" : "rgba(255,255,255,0.3)",
                  border: "none",
                  cursor: requirement.trim() ? "pointer" : "not-allowed",
                  boxShadow: requirement.trim() ? "0 4px 14px rgba(91,114,255,0.3)" : "none",
                }}
              >
                <Zap size={13} /> 启动 Pipeline
              </motion.button>
            </>
          )}
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

  const filtered = mockPipelines.filter((p) => {
    const matchSearch =
      search === "" ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === "all" || p.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <div className="h-full flex flex-col">
      {/* Top Bar */}
      <div
        className="flex items-center justify-between px-8 py-5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            流水线
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            {mockPipelines.length} 条流水线
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

      {/* Filters */}
      <div
        className="flex items-center gap-4 px-8 py-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search
            size={13}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "rgba(255,255,255,0.3)" }}
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
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

        {/* Status Filter */}
        <div className="flex items-center gap-1">
          <Filter size={11} style={{ color: "rgba(255,255,255,0.3)" }} />
          {["all", "running", "paused", "completed", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="px-3 py-1 rounded-lg transition-all"
              style={{
                fontSize: 11,
                background: filter === f ? "rgba(91,114,255,0.15)" : "rgba(255,255,255,0.03)",
                color:
                  filter === f ? "#A0ABFF" : "rgba(255,255,255,0.4)",
                border: `1px solid ${filter === f ? "rgba(91,114,255,0.25)" : "rgba(255,255,255,0.06)"}`,
                cursor: "pointer",
              }}
            >
              {f === "all" ? "全部" : f === "running" ? "运行中" : f === "paused" ? "暂停" : f === "completed" ? "已完成" : "失败"}
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline List */}
      <div className="flex-1 overflow-y-auto px-8 py-5 space-y-3">
        {filtered.map((pipeline, i) => (
          <PipelineCard
            key={pipeline.id}
            pipeline={pipeline}
            index={i}
            onClick={() => navigate(`/pipelines/${pipeline.id}`)}
          />
        ))}
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <GitBranch size={32} style={{ color: "rgba(255,255,255,0.1)", marginBottom: 12 }} />
            <p style={{ fontSize: 14, color: "rgba(255,255,255,0.3)" }}>未找到匹配的流水线</p>
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
      onMouseEnter={(e) =>
        (e.currentTarget.style.border = "1px solid rgba(255,255,255,0.12)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.border = "1px solid rgba(255,255,255,0.07)")
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

      {/* Stage Progress */}
      <div className="flex items-center gap-1 mb-3">
        {stageLabels.map((label, i) => {
          const stage = pipeline.stages[i];
          const status = stage?.status || "idle";
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
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
                  transition={{ duration: 0.6, delay: 0.1 * i }}
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

      {/* Footer */}
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

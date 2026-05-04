import { useState } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  CheckSquare,
  Clock,
  Check,
  X,
  MessageSquare,
  RotateCcw,
  GitBranch,
  ChevronRight,
  AlertTriangle,
  Eye,
} from "lucide-react";
import { mockCheckpoints } from "../data/mockData";

type CheckpointStatus = "pending" | "approved" | "rejected";

interface LocalCheckpoint {
  id: string;
  pipelineId: string;
  pipelineName: string;
  stage: string;
  stageIndex: number;
  status: CheckpointStatus;
  createdAt: string;
  output: string;
  rejectReason?: string;
}

export function CheckpointReview() {
  const navigate = useNavigate();
  const [checkpoints, setCheckpoints] = useState<LocalCheckpoint[]>(
    mockCheckpoints.map((c) => ({ ...c, status: "pending" as CheckpointStatus }))
  );
  const [selected, setSelected] = useState<string>(checkpoints[0]?.id || "");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [actionDone, setActionDone] = useState<string | null>(null);

  const selectedCp = checkpoints.find((c) => c.id === selected);
  const pendingCount = checkpoints.filter((c) => c.status === "pending").length;

  const handleApprove = (id: string) => {
    setCheckpoints((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "approved" } : c))
    );
    setActionDone("approved");
    setTimeout(() => setActionDone(null), 3000);
  };

  const handleReject = (id: string) => {
    if (!rejectReason.trim()) return;
    setCheckpoints((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, status: "rejected", rejectReason } : c
      )
    );
    setShowRejectInput(false);
    setRejectReason("");
    setActionDone("rejected");
    setTimeout(() => setActionDone(null), 3000);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <div className="flex items-center gap-2">
            <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
              审批检查点
            </h1>
            {pendingCount > 0 && (
              <span
                className="px-2 py-0.5 rounded-full"
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: "rgba(255,80,80,0.15)",
                  color: "#FF6B6B",
                  border: "1px solid rgba(255,80,80,0.25)",
                }}
              >
                {pendingCount} 待审批
              </span>
            )}
          </div>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            Human-in-the-Loop · 在关键节点做 Approve / Reject 决策
          </p>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Checkpoint List */}
        <div
          className="w-72 flex-shrink-0 overflow-y-auto p-4 space-y-2"
          style={{ borderRight: "1px solid rgba(255,255,255,0.05)" }}
        >
          {checkpoints.map((cp, i) => (
            <motion.div
              key={cp.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => {
                setSelected(cp.id);
                setShowRejectInput(false);
              }}
              className="p-4 rounded-xl cursor-pointer transition-all"
              style={{
                background:
                  selected === cp.id
                    ? "rgba(91,114,255,0.08)"
                    : "rgba(255,255,255,0.025)",
                border: `1px solid ${
                  selected === cp.id
                    ? "rgba(91,114,255,0.25)"
                    : "rgba(255,255,255,0.07)"
                }`,
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{
                      background:
                        cp.status === "approved"
                          ? "rgba(52,199,89,0.15)"
                          : cp.status === "rejected"
                          ? "rgba(255,69,58,0.15)"
                          : "rgba(255,159,10,0.15)",
                    }}
                  >
                    {cp.status === "approved" ? (
                      <Check size={11} style={{ color: "#34C759" }} />
                    ) : cp.status === "rejected" ? (
                      <X size={11} style={{ color: "#FF453A" }} />
                    ) : (
                      <CheckSquare size={11} style={{ color: "#FF9F0A" }} />
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 500,
                      color:
                        cp.status === "approved"
                          ? "#34C759"
                          : cp.status === "rejected"
                          ? "#FF453A"
                          : "#FF9F0A",
                    }}
                  >
                    {cp.status === "approved"
                      ? "已通过"
                      : cp.status === "rejected"
                      ? "已拒绝"
                      : "待审批"}
                  </span>
                </div>
                <ChevronRight
                  size={11}
                  style={{ color: "rgba(255,255,255,0.2)" }}
                />
              </div>

              <div
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "rgba(255,255,255,0.75)",
                  marginBottom: 3,
                }}
                className="truncate"
              >
                {cp.pipelineName}
              </div>
              <div className="flex items-center gap-1.5">
                <GitBranch size={9} style={{ color: "rgba(255,255,255,0.3)" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>
                  {cp.stage} · 检查点
                </span>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <Clock size={9} style={{ color: "rgba(255,255,255,0.25)" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>
                  {new Date(cp.createdAt).toLocaleString("zh-CN", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Right: Review Panel */}
        {selectedCp ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Review Header */}
            <div
              className="flex items-center justify-between px-6 py-4 flex-shrink-0"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
            >
              <div>
                <div className="flex items-center gap-2">
                  <Eye size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
                  <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                    {selectedCp.stage} · Agent 产出物
                  </span>
                </div>
                <p style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>
                  {selectedCp.pipelineName}
                </p>
              </div>

              <button
                onClick={() => navigate(`/pipelines/${selectedCp.pipelineId}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-white/[0.04] transition-colors"
                style={{
                  fontSize: 11,
                  color: "#7C8FFF",
                  background: "rgba(91,114,255,0.08)",
                  border: "1px solid rgba(91,114,255,0.18)",
                  cursor: "pointer",
                }}
              >
                查看流水线 <ChevronRight size={11} />
              </button>
            </div>

            {/* Output Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div
                className="rounded-2xl overflow-hidden"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.07)",
                }}
              >
                <div
                  className="flex items-center justify-between px-5 py-3"
                  style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
                >
                  <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.4)" }}>
                    产出物内容
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      color: "rgba(255,255,255,0.25)",
                      fontFamily: "monospace",
                    }}
                  >
                    {selectedCp.id}
                  </span>
                </div>
                <div
                  className="p-5 overflow-y-auto"
                  style={{
                    maxHeight: 400,
                    fontSize: 12.5,
                    color: "rgba(255,255,255,0.7)",
                    lineHeight: 1.75,
                    fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {selectedCp.output}
                </div>
              </div>

              {selectedCp.rejectReason && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-4 rounded-xl flex items-start gap-3"
                  style={{
                    background: "rgba(255,69,58,0.06)",
                    border: "1px solid rgba(255,69,58,0.15)",
                  }}
                >
                  <AlertTriangle size={14} style={{ color: "#FF453A", flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 500, color: "#FF453A", marginBottom: 4 }}>
                      拒绝原因
                    </div>
                    <p style={{ fontSize: 12, color: "rgba(255,69,58,0.8)" }}>
                      {selectedCp.rejectReason}
                    </p>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Action Area */}
            <div
              className="flex-shrink-0 px-6 py-5"
              style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
            >
              <AnimatePresence>
                {actionDone && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center gap-2 mb-4 p-3 rounded-xl"
                    style={{
                      background:
                        actionDone === "approved"
                          ? "rgba(52,199,89,0.08)"
                          : "rgba(255,69,58,0.08)",
                      border: `1px solid ${
                        actionDone === "approved"
                          ? "rgba(52,199,89,0.2)"
                          : "rgba(255,69,58,0.2)"
                      }`,
                    }}
                  >
                    {actionDone === "approved" ? (
                      <Check size={13} style={{ color: "#34C759" }} />
                    ) : (
                      <X size={13} style={{ color: "#FF453A" }} />
                    )}
                    <span
                      style={{
                        fontSize: 12,
                        color:
                          actionDone === "approved" ? "#34C759" : "#FF453A",
                        fontWeight: 500,
                      }}
                    >
                      {actionDone === "approved"
                        ? "已通过审批，Pipeline 将继续下一阶段"
                        : "已拒绝，Agent 将携带反馈重新执行此阶段"}
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>

              {selectedCp.status === "pending" && (
                <>
                  {showRejectInput ? (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-3"
                    >
                      <div>
                        <label
                          style={{
                            fontSize: 11,
                            fontWeight: 500,
                            color: "rgba(255,255,255,0.5)",
                            display: "block",
                            marginBottom: 6,
                          }}
                        >
                          拒绝原因 <span style={{ color: "#FF453A" }}>*</span>
                        </label>
                        <textarea
                          value={rejectReason}
                          onChange={(e) => setRejectReason(e.target.value)}
                          placeholder="请描述问题或需要 Agent 重新考虑的点，这将作为反馈传递给 Agent..."
                          rows={3}
                          className="w-full px-4 py-3 rounded-xl resize-none"
                          style={{
                            background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,69,58,0.3)",
                            color: "rgba(255,255,255,0.8)",
                            fontSize: 12,
                            outline: "none",
                            lineHeight: 1.6,
                          }}
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setShowRejectInput(false)}
                          className="px-4 py-2 rounded-lg flex-1"
                          style={{
                            background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,255,255,0.08)",
                            color: "rgba(255,255,255,0.5)",
                            fontSize: 12,
                            cursor: "pointer",
                          }}
                        >
                          取消
                        </button>
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          disabled={!rejectReason.trim()}
                          onClick={() => handleReject(selectedCp.id)}
                          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg flex-1"
                          style={{
                            background: rejectReason.trim()
                              ? "rgba(255,69,58,0.15)"
                              : "rgba(255,255,255,0.04)",
                            border: `1px solid ${
                              rejectReason.trim()
                                ? "rgba(255,69,58,0.3)"
                                : "rgba(255,255,255,0.06)"
                            }`,
                            color: rejectReason.trim() ? "#FF453A" : "rgba(255,255,255,0.3)",
                            fontSize: 12,
                            fontWeight: 500,
                            cursor: rejectReason.trim() ? "pointer" : "not-allowed",
                          }}
                        >
                          <RotateCcw size={12} /> 确认拒绝并重做
                        </motion.button>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setShowRejectInput(true)}
                        className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl flex-1"
                        style={{
                          background: "rgba(255,69,58,0.06)",
                          border: "1px solid rgba(255,69,58,0.2)",
                          color: "#FF453A",
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: "pointer",
                        }}
                      >
                        <X size={14} />
                        Reject
                        <span style={{ fontSize: 10, opacity: 0.6 }}>（回退重做）</span>
                      </motion.button>

                      <motion.button
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => handleApprove(selectedCp.id)}
                        className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl flex-1"
                        style={{
                          background: "rgba(52,199,89,0.1)",
                          border: "1px solid rgba(52,199,89,0.25)",
                          color: "#34C759",
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: "pointer",
                          boxShadow: "0 4px 16px rgba(52,199,89,0.1)",
                        }}
                      >
                        <Check size={14} />
                        Approve
                        <span style={{ fontSize: 10, opacity: 0.6 }}>（继续下一阶段）</span>
                      </motion.button>
                    </div>
                  )}

                  <div className="flex items-center gap-2 mt-3">
                    <MessageSquare size={10} style={{ color: "rgba(255,255,255,0.25)" }} />
                    <span style={{ fontSize: 10.5, color: "rgba(255,255,255,0.3)" }}>
                      Reject 后，Agent 将携带你的反馈意见重新执行此阶段，最多重试 3 次
                    </span>
                  </div>
                </>
              )}

              {selectedCp.status !== "pending" && (
                <div
                  className="flex items-center justify-center p-4 rounded-xl"
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <span style={{ fontSize: 12, color: "rgba(255,255,255,0.3)" }}>
                    此检查点已处理完毕
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <CheckSquare size={40} style={{ color: "rgba(255,255,255,0.08)", margin: "0 auto 12px" }} />
              <p style={{ fontSize: 14, color: "rgba(255,255,255,0.3)" }}>暂无待审批检查点</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

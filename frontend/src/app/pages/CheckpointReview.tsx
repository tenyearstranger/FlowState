import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { toast } from "sonner";
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
import { useApiQuery } from "../hooks/useApiQuery";
import { getErrorMessage } from "../lib/api/client";
import { checkpointsApi } from "../lib/api/services";
import type { Checkpoint } from "../types/checkpoint";

export function CheckpointReview() {
  const navigate = useNavigate();
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [selected, setSelected] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [actionDone, setActionDone] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const checkpointsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => checkpointsApi.list({ signal }), []),
    []
  );

  useEffect(() => {
    if (checkpointsQuery.data) {
      setCheckpoints(checkpointsQuery.data);
    }
  }, [checkpointsQuery.data]);

  useEffect(() => {
    if (!selected && checkpoints[0]) {
      setSelected(checkpoints[0].id);
      return;
    }

    if (selected && !checkpoints.some((checkpoint) => checkpoint.id === selected)) {
      setSelected(checkpoints[0]?.id ?? "");
    }
  }, [checkpoints, selected]);

  const selectedCp = useMemo(
    () => checkpoints.find((checkpoint) => checkpoint.id === selected),
    [checkpoints, selected]
  );
  const pendingCount = checkpoints.filter((checkpoint) => checkpoint.status === "pending").length;

  const updateCheckpointList = useCallback((updatedCheckpoint: Checkpoint) => {
    let nextSelectedId = "";

    setCheckpoints((prev) => {
      const nextCheckpoints = prev.map((checkpoint) =>
        checkpoint.id === updatedCheckpoint.id ? updatedCheckpoint : checkpoint
      );
      const nextPendingCheckpoint =
        nextCheckpoints.find(
          (checkpoint) =>
            checkpoint.id !== updatedCheckpoint.id && checkpoint.status === "pending"
        ) ?? nextCheckpoints.find((checkpoint) => checkpoint.id === updatedCheckpoint.id);

      nextSelectedId = nextPendingCheckpoint?.id ?? nextCheckpoints[0]?.id ?? "";
      return nextCheckpoints;
    });

    if (nextSelectedId) {
      setSelected(nextSelectedId);
    }
  }, []);

  const handleApprove = async (id: string) => {
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setActionError(null);
    try {
      const updated = await checkpointsApi.approve(id);
      updateCheckpointList(updated);
      checkpointsQuery.reload();
      setActionDone("approved");
      setShowRejectInput(false);
      setRejectReason("");
      toast.success("提交成功", {
        description: "审批结果已保存，流水线会继续推进到下一阶段。",
      });
      setTimeout(() => setActionDone(null), 3000);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      setActionError(errorMessage);
      toast.error("提交失败", {
        description: errorMessage,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async (id: string) => {
    if (!rejectReason.trim() || submitting) {
      return;
    }

    setSubmitting(true);
    setActionError(null);
    try {
      const updated = await checkpointsApi.reject(id, rejectReason.trim());
      updateCheckpointList(updated);
      checkpointsQuery.reload();
      setShowRejectInput(false);
      setRejectReason("");
      setActionDone("rejected");
      toast.success("提交成功", {
        description: "已退回当前阶段，Agent 会结合你的反馈重新执行。",
      });
      setTimeout(() => setActionDone(null), 3000);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      setActionError(errorMessage);
      toast.error("提交失败", {
        description: errorMessage,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
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

      {checkpointsQuery.error && (
        <div className="px-8 pt-5">
          <div
            className="rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {checkpointsQuery.error}
            </span>
            <button
              onClick={checkpointsQuery.reload}
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
          {checkpoints.map((checkpoint, index) => (
            <motion.div
              key={checkpoint.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => {
                setSelected(checkpoint.id);
                setShowRejectInput(false);
              }}
              className="p-4 rounded-xl cursor-pointer transition-all"
              style={{
                background:
                  selected === checkpoint.id
                    ? "rgba(91,114,255,0.08)"
                    : "rgba(255,255,255,0.025)",
                border: `1px solid ${
                  selected === checkpoint.id
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
                        checkpoint.status === "approved"
                          ? "rgba(52,199,89,0.15)"
                          : checkpoint.status === "rejected"
                          ? "rgba(255,69,58,0.15)"
                          : "rgba(255,159,10,0.15)",
                    }}
                  >
                    {checkpoint.status === "approved" ? (
                      <Check size={11} style={{ color: "#34C759" }} />
                    ) : checkpoint.status === "rejected" ? (
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
                        checkpoint.status === "approved"
                          ? "#34C759"
                          : checkpoint.status === "rejected"
                          ? "#FF453A"
                          : "#FF9F0A",
                    }}
                  >
                    {checkpoint.status === "approved"
                      ? "已通过"
                      : checkpoint.status === "rejected"
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
                {checkpoint.pipelineName}
              </div>
              <div className="flex items-center gap-1.5">
                <GitBranch size={9} style={{ color: "rgba(255,255,255,0.3)" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>
                  {checkpoint.stage} · 检查点
                </span>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <Clock size={9} style={{ color: "rgba(255,255,255,0.25)" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>
                  {new Date(checkpoint.createdAt).toLocaleString("zh-CN", {
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

        {selectedCp ? (
          <div className="flex-1 flex flex-col overflow-hidden">
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

            <div className="flex-1 overflow-y-auto p-6">
              {actionError && (
                <div
                  className="mb-4 rounded-xl px-4 py-3"
                  style={{
                    background: "rgba(255,69,58,0.06)",
                    border: "1px solid rgba(255,69,58,0.18)",
                    color: "rgba(255,255,255,0.72)",
                    fontSize: 12,
                  }}
                >
                  {actionError}
                </div>
              )}

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
                          onChange={(event) => setRejectReason(event.target.value)}
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
                          disabled={!rejectReason.trim() || submitting}
                          onClick={() => handleReject(selectedCp.id)}
                          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg flex-1"
                          style={{
                            background: rejectReason.trim() && !submitting
                              ? "rgba(255,69,58,0.15)"
                              : "rgba(255,255,255,0.04)",
                            border: `1px solid ${
                              rejectReason.trim() && !submitting
                                ? "rgba(255,69,58,0.3)"
                                : "rgba(255,255,255,0.06)"
                            }`,
                            color: rejectReason.trim() && !submitting ? "#FF453A" : "rgba(255,255,255,0.3)",
                            fontSize: 12,
                            fontWeight: 500,
                            cursor: rejectReason.trim() && !submitting ? "pointer" : "not-allowed",
                          }}
                        >
                          <RotateCcw size={12} /> {submitting ? "提交中..." : "确认拒绝并重做"}
                        </motion.button>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setShowRejectInput(true)}
                        disabled={submitting}
                        className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl flex-1"
                        style={{
                          background: "rgba(255,69,58,0.06)",
                          border: "1px solid rgba(255,69,58,0.2)",
                          color: "#FF453A",
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: submitting ? "not-allowed" : "pointer",
                          opacity: submitting ? 0.6 : 1,
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
                        disabled={submitting}
                        className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl flex-1"
                        style={{
                          background: "rgba(52,199,89,0.1)",
                          border: "1px solid rgba(52,199,89,0.25)",
                          color: "#34C759",
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: submitting ? "not-allowed" : "pointer",
                          boxShadow: "0 4px 16px rgba(52,199,89,0.1)",
                          opacity: submitting ? 0.6 : 1,
                        }}
                      >
                        <Check size={14} />
                        {submitting ? "提交中..." : "Approve"}
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
              <p style={{ fontSize: 14, color: "rgba(255,255,255,0.3)" }}>
                {checkpointsQuery.loading ? "正在加载检查点..." : "暂无待审批检查点"}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

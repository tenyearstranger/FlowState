import { useNavigate } from "react-router";
import { motion } from "motion/react";
import {
  GitBranch,
  Bot,
  CheckSquare,
  GitMerge,
  ArrowRight,
  Plus,
  Clock,
  TrendingUp,
  Zap,
  AlertCircle,
} from "lucide-react";
import { mockPipelines } from "../data/mockData";
import { StatusBadge } from "../components/ui/StatusBadge";

const stats = [
  {
    label: "活跃流水线",
    value: "3",
    change: "+1",
    icon: GitBranch,
    color: "#5B72FF",
    bg: "rgba(91,114,255,0.1)",
  },
  {
    label: "Agent 运行中",
    value: "3",
    change: "正常",
    icon: Bot,
    color: "#34C759",
    bg: "rgba(52,199,89,0.1)",
  },
  {
    label: "待审批检查点",
    value: "2",
    change: "需关注",
    icon: CheckSquare,
    color: "#FF9F0A",
    bg: "rgba(255,159,10,0.1)",
  },
  {
    label: "已合并变更",
    value: "18",
    change: "+5 本周",
    icon: GitMerge,
    color: "#A259FF",
    bg: "rgba(162,89,255,0.1)",
  },
];

const recentActivity = [
  { time: "2分钟前", text: "pl-001 · CodegenAgent 完成代码生成", type: "success" },
  { time: "8分钟前", text: "pl-001 · ArchitectAgent 产出方案设计，等待人工审批", type: "checkpoint" },
  { time: "15分钟前", text: "pl-001 · RequirementsAgent 完成需求分析", type: "success" },
  { time: "32分钟前", text: "pl-002 · 方案设计检查点等待审批（已超时 17m）", type: "warning" },
  { time: "1小时前", text: "pl-005 · TestAgent 运行失败，原因：测试覆盖率不足 (62%)", type: "error" },
  { time: "3小时前", text: "pl-003 · DeliveryAgent 成功创建 MR #42，已合并", type: "success" },
];

export function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-end justify-between">
            <div>
              <h1
                style={{
                  fontSize: 26,
                  fontWeight: 600,
                  color: "#FFFFFF",
                  letterSpacing: "-0.5px",
                  marginBottom: 4,
                }}
              >
                概览
              </h1>
              <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                2026年5月4日 · 3 条流水线正在运行
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate("/pipelines")}
              className="flex items-center gap-2 px-4 py-2 rounded-xl"
              style={{
                background: "linear-gradient(135deg, #5B72FF 0%, #A259FF 100%)",
                fontSize: 13,
                fontWeight: 500,
                color: "white",
                boxShadow: "0 4px 16px rgba(91,114,255,0.3)",
                border: "none",
                cursor: "pointer",
              }}
            >
              <Plus size={14} />
              新建流水线
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-4 gap-4 mb-8"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 + i * 0.04 }}
              whileHover={{ y: -2 }}
              className="rounded-2xl p-5 cursor-pointer"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: stat.bg }}
                >
                  <stat.icon size={16} style={{ color: stat.color }} />
                </div>
                <span
                  style={{
                    fontSize: 10,
                    color: "rgba(255,255,255,0.35)",
                    background: "rgba(255,255,255,0.05)",
                    padding: "2px 7px",
                    borderRadius: 20,
                  }}
                >
                  {stat.change}
                </span>
              </div>
              <div
                style={{ fontSize: 28, fontWeight: 600, color: "white", letterSpacing: "-1px" }}
              >
                {stat.value}
              </div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
                {stat.label}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Main content: Pipelines + Activity */}
        <div className="grid grid-cols-3 gap-6">
          {/* Recent Pipelines */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="col-span-2 rounded-2xl overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div
              className="flex items-center justify-between px-6 py-4"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
            >
              <div className="flex items-center gap-2">
                <GitBranch size={14} style={{ color: "rgba(255,255,255,0.4)" }} />
                <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
                  近期流水线
                </span>
              </div>
              <button
                onClick={() => navigate("/pipelines")}
                className="flex items-center gap-1 hover:opacity-80 transition-opacity"
                style={{ fontSize: 12, color: "#7C8FFF", background: "none", border: "none", cursor: "pointer" }}
              >
                查看全部 <ArrowRight size={11} />
              </button>
            </div>

            <div>
              {mockPipelines.slice(0, 4).map((pipeline, i) => (
                <motion.div
                  key={pipeline.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.25 + i * 0.05 }}
                  onClick={() => navigate(`/pipelines/${pipeline.id}`)}
                  className="px-6 py-4 flex items-center gap-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  style={{ borderTop: i > 0 ? "1px solid rgba(255,255,255,0.04)" : "none" }}
                >
                  {/* Status indicator */}
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{
                      background:
                        pipeline.status === "running"
                          ? "#5B72FF"
                          : pipeline.status === "completed"
                          ? "#34C759"
                          : pipeline.status === "failed"
                          ? "#FF453A"
                          : pipeline.status === "paused"
                          ? "#FF9F0A"
                          : "rgba(255,255,255,0.2)",
                    }}
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}
                        className="truncate"
                      >
                        {pipeline.name}
                      </span>
                      {pipeline.template && (
                        <span
                          style={{
                            fontSize: 10,
                            color: "rgba(255,255,255,0.3)",
                            background: "rgba(255,255,255,0.05)",
                            padding: "1px 6px",
                            borderRadius: 4,
                            flexShrink: 0,
                          }}
                        >
                          {pipeline.template}
                        </span>
                      )}
                    </div>

                    {/* Progress bar */}
                    <div className="flex items-center gap-3">
                      <div
                        className="flex-1 rounded-full overflow-hidden"
                        style={{ height: 3, background: "rgba(255,255,255,0.06)" }}
                      >
                        <motion.div
                          className="h-full rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${pipeline.progress}%` }}
                          transition={{ duration: 0.8, delay: 0.3 + i * 0.05, ease: "easeOut" }}
                          style={{
                            background:
                              pipeline.status === "failed"
                                ? "#FF453A"
                                : "linear-gradient(90deg, #5B72FF, #A259FF)",
                          }}
                        />
                      </div>
                      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", flexShrink: 0 }}>
                        {pipeline.progress}%
                      </span>
                    </div>
                  </div>

                  <StatusBadge status={pipeline.status} size="sm" />
                  <ArrowRight size={13} style={{ color: "rgba(255,255,255,0.2)", flexShrink: 0 }} />
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div
              className="flex items-center gap-2 px-5 py-4"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
            >
              <Clock size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
                实时动态
              </span>
            </div>

            <div className="px-4 py-3 space-y-1">
              {recentActivity.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.04 }}
                  className="flex gap-2.5 py-2.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {item.type === "success" && (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#34C759" }} />
                    )}
                    {item.type === "checkpoint" && (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#FF9F0A" }} />
                    )}
                    {item.type === "warning" && (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#FF9F0A" }} />
                    )}
                    {item.type === "error" && (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#FF453A" }} />
                    )}
                  </div>
                  <div>
                    <p style={{ fontSize: 11.5, color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>
                      {item.text}
                    </p>
                    <p style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", marginTop: 2 }}>
                      {item.time}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="mt-6 rounded-2xl p-5"
          style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
              Pipeline 模板
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              {
                title: "新功能开发",
                desc: "完整的 6 阶段开发流程",
                icon: Zap,
                color: "#5B72FF",
              },
              {
                title: "Bug 修复",
                desc: "精简的 4 阶段修复流程",
                icon: AlertCircle,
                color: "#FF9F0A",
              },
              {
                title: "重构优化",
                desc: "含架构评审的重构流程",
                icon: TrendingUp,
                color: "#A259FF",
              },
            ].map((template) => (
              <motion.button
                key={template.title}
                whileHover={{ y: -2, background: "rgba(255,255,255,0.06)" }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate("/pipelines")}
                className="flex items-center gap-3 p-4 rounded-xl text-left transition-all"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  cursor: "pointer",
                }}
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: `${template.color}18` }}
                >
                  <template.icon size={14} style={{ color: template.color }} />
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.75)" }}>
                    {template.title}
                  </div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
                    {template.desc}
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

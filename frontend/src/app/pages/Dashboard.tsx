import { useCallback } from "react";
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
  RotateCcw,
} from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";
import {
  activitiesApi,
  agentsApi,
  analyticsApi,
  checkpointsApi,
  pipelinesApi,
} from "../lib/api/services";

const templates = [
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
];

export function Dashboard() {
  const navigate = useNavigate();
  const dashboardQuery = useApiQuery(
    useCallback(async (signal: AbortSignal) => {
      const [pipelines, agents, checkpoints, analytics, recentActivity] = await Promise.all([
        pipelinesApi.list({ signal }),
        agentsApi.list({ signal }),
        checkpointsApi.list({ signal }),
        analyticsApi.getOverview({ signal }),
        activitiesApi.listRecent({ signal }),
      ]);

      return { agents, analytics, checkpoints, pipelines, recentActivity };
    }, []),
    []
  );

  const pipelines = dashboardQuery.data?.pipelines ?? [];
  const agents = dashboardQuery.data?.agents ?? [];
  const checkpoints = dashboardQuery.data?.checkpoints ?? [];
  const analytics = dashboardQuery.data?.analytics;
  const recentActivity = dashboardQuery.data?.recentActivity ?? [];

  const activePipelines = pipelines.filter((pipeline) =>
    ["running", "paused", "pending"].includes(pipeline.status)
  ).length;
  const runningAgents = agents.filter((agent) => agent.status === "running").length;
  const pendingCheckpoints = checkpoints.filter((checkpoint) => checkpoint.status === "pending").length;
  const mergedChanges = analytics?.summary.mergedChanges ?? 0;

  const stats = [
    {
      label: "活跃流水线",
      value: dashboardQuery.loading ? "--" : String(activePipelines),
      change: `${pipelines.length} 总计`,
      icon: GitBranch,
      color: "#5B72FF",
      bg: "rgba(91,114,255,0.1)",
    },
    {
      label: "Agent 运行中",
      value: dashboardQuery.loading ? "--" : String(runningAgents),
      change: agents.length > 0 ? `${agents.length} 已配置` : "等待数据",
      icon: Bot,
      color: "#34C759",
      bg: "rgba(52,199,89,0.1)",
    },
    {
      label: "待审批检查点",
      value: dashboardQuery.loading ? "--" : String(pendingCheckpoints),
      change: pendingCheckpoints > 0 ? "需关注" : "正常",
      icon: CheckSquare,
      color: "#FF9F0A",
      bg: "rgba(255,159,10,0.1)",
    },
    {
      label: "已合并变更",
      value: dashboardQuery.loading ? "--" : String(mergedChanges),
      change: "来自分析接口",
      icon: GitMerge,
      color: "#A259FF",
      bg: "rgba(162,89,255,0.1)",
    },
  ];

  const todayLabel = new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
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
                {todayLabel} · {dashboardQuery.loading ? "正在同步数据" : `${activePipelines} 条活跃流水线`}
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

        {dashboardQuery.error && (
          <div
            className="mb-6 rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {dashboardQuery.error}
            </span>
            <button
              onClick={dashboardQuery.reload}
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
        )}

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

        <div className="grid grid-cols-3 gap-6">
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
                style={{
                  fontSize: 12,
                  color: "#7C8FFF",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                查看全部 <ArrowRight size={11} />
              </button>
            </div>

            <div>
              {pipelines.slice(0, 4).map((pipeline, i) => (
                <motion.div
                  key={pipeline.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.25 + i * 0.05 }}
                  onClick={() => navigate(`/pipelines/${pipeline.id}`)}
                  className="px-6 py-4 flex items-center gap-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  style={{ borderTop: i > 0 ? "1px solid rgba(255,255,255,0.04)" : "none" }}
                >
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

              {!dashboardQuery.loading && pipelines.length === 0 && (
                <div className="px-6 py-10 text-center" style={{ color: "rgba(255,255,255,0.35)" }}>
                  暂无流水线数据
                </div>
              )}
            </div>
          </motion.div>

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
                  key={`${item.time}-${item.text}`}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.04 }}
                  className="flex gap-2.5 py-2.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {(item.type === "success" || item.type === "checkpoint" || item.type === "warning" || item.type === "error") && (
                      <div
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          background:
                            item.type === "success"
                              ? "#34C759"
                              : item.type === "error"
                              ? "#FF453A"
                              : "#FF9F0A",
                        }}
                      />
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

              {!dashboardQuery.loading && recentActivity.length === 0 && (
                <div className="px-2 py-4" style={{ fontSize: 11.5, color: "rgba(255,255,255,0.35)" }}>
                  暂无动态
                </div>
              )}
            </div>
          </motion.div>
        </div>

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
            {templates.map((template) => (
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

import { useCallback } from "react";
import { motion } from "motion/react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { BarChart2, Zap, Clock, TrendingUp, CheckCircle, RotateCcw } from "lucide-react";
import { useApiQuery } from "../hooks/useApiQuery";
import { analyticsApi } from "../lib/api/services";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          background: "#1a1a20",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 10,
          padding: "8px 12px",
          fontSize: 11,
          color: "rgba(255,255,255,0.7)",
        }}
      >
        <p style={{ color: "rgba(255,255,255,0.5)", marginBottom: 4 }}>{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function Analytics() {
  const analyticsQuery = useApiQuery(
    useCallback((signal: AbortSignal) => analyticsApi.getOverview({ signal }), []),
    []
  );
  const analytics = analyticsQuery.data;
  const summary = analytics?.summary;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            可观测性面板
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            Pipeline 运行状态实时可视化 · 最近 7 天
          </p>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl"
          style={{
            background: "rgba(52,199,89,0.08)",
            border: "1px solid rgba(52,199,89,0.15)",
          }}
        >
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
          <span style={{ fontSize: 11, color: "rgba(52,199,89,0.9)", fontWeight: 500 }}>
            {analyticsQuery.loading ? "同步中" : "实时数据"}
          </span>
        </div>
      </div>

      {analyticsQuery.error && (
        <div className="px-6 pt-5">
          <div
            className="rounded-2xl p-4 flex items-center justify-between"
            style={{
              background: "rgba(255,69,58,0.06)",
              border: "1px solid rgba(255,69,58,0.18)",
            }}
          >
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.72)" }}>
              {analyticsQuery.error}
            </span>
            <button
              onClick={analyticsQuery.reload}
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

      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "总运行次数", value: summary?.totalRuns ?? "--", icon: BarChart2, color: "#5B72FF" },
            {
              label: "成功率",
              value:
                summary && summary.totalRuns > 0
                  ? `${((summary.totalSuccess / summary.totalRuns) * 100).toFixed(1)}%`
                  : "--",
              icon: CheckCircle,
              color: "#34C759",
            },
            {
              label: "今日 Token 消耗",
              value: summary ? `${(summary.totalTokens / 1000).toFixed(1)}K` : "--",
              icon: Zap,
              color: "#FF9F0A",
            },
            {
              label: "平均耗时",
              value: summary ? `${summary.averageDurationMinutes.toFixed(1)}m` : "--",
              icon: Clock,
              color: "#A259FF",
            },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl p-5"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center mb-3"
                style={{ background: `${stat.color}15` }}
              >
                <stat.icon size={14} style={{ color: stat.color }} />
              </div>
              <div
                style={{ fontSize: 26, fontWeight: 600, color: "white", letterSpacing: "-0.5px" }}
              >
                {stat.value}
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-5 mb-5">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-2xl p-5"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center gap-2 mb-5">
              <TrendingUp size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                每日 Pipeline 运行量
              </span>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={analytics?.pipelineRuns ?? []} barSize={20} barGap={4}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.04)"
                  vertical={false}
                />
                <XAxis
                  dataKey="day"
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={20}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="success" name="成功" fill="#34C759" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failed" name="失败" fill="#FF453A" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: "#34C759" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>成功</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: "#FF453A" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>失败</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="rounded-2xl p-5"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center gap-2 mb-5">
              <Zap size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                今日 Token 消耗趋势
              </span>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={analytics?.tokenUsage ?? []}>
                <defs>
                  <linearGradient id="tokenGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FF9F0A" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#FF9F0A" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.04)"
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={35}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="tokens"
                  name="Tokens"
                  stroke="#FF9F0A"
                  strokeWidth={2}
                  fill="url(#tokenGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        <div className="grid grid-cols-2 gap-5">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="rounded-2xl p-5"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center gap-2 mb-5">
              <Clock size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                各阶段平均耗时 (s)
              </span>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={analytics?.stageDurations ?? []} layout="vertical" barSize={10}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="stage"
                  tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={70}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="avg" name="平均" fill="#5B72FF" radius={[0, 4, 4, 0]} />
                <Bar dataKey="p95" name="P95" fill="rgba(91,114,255,0.25)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="rounded-2xl p-5"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center gap-2 mb-5">
              <CheckCircle size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                Agent 成功率
              </span>
            </div>
            <div className="space-y-3">
              {(analytics?.agentSuccessRates ?? []).map((agent, index) => (
                <div key={agent.name} className="flex items-center gap-3">
                  <div
                    className="flex-shrink-0"
                    style={{
                      width: 100,
                      fontSize: 10,
                      color: "rgba(255,255,255,0.45)",
                      fontFamily: "monospace",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {agent.name.replace("Agent", "")}
                  </div>
                  <div
                    className="flex-1 rounded-full overflow-hidden"
                    style={{ height: 6, background: "rgba(255,255,255,0.05)" }}
                  >
                    <motion.div
                      className="h-full rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${agent.rate}%` }}
                      transition={{ duration: 0.8, delay: 0.4 + index * 0.06, ease: "easeOut" }}
                      style={{
                        background:
                          agent.rate >= 97
                            ? "#34C759"
                            : agent.rate >= 92
                            ? "#5B72FF"
                            : "#FF9F0A",
                      }}
                    />
                  </div>
                  <span
                    style={{
                      fontSize: 11,
                      color:
                        agent.rate >= 97
                          ? "#34C759"
                          : agent.rate >= 92
                          ? "#7C8FFF"
                          : "#FF9F0A",
                      fontWeight: 500,
                      flexShrink: 0,
                      minWidth: 36,
                      textAlign: "right",
                    }}
                  >
                    {agent.rate}%
                  </span>
                </div>
              ))}

              {!analyticsQuery.loading && (analytics?.agentSuccessRates.length ?? 0) === 0 && (
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
                  暂无统计数据
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

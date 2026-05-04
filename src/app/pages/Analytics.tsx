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
  LineChart,
  Line,
} from "recharts";
import { BarChart2, Zap, Clock, TrendingUp, CheckCircle } from "lucide-react";

const pipelineRunData = [
  { day: "4/28", success: 3, failed: 0, total: 3 },
  { day: "4/29", success: 5, failed: 1, total: 6 },
  { day: "4/30", success: 4, failed: 0, total: 4 },
  { day: "5/1", success: 6, failed: 1, total: 7 },
  { day: "5/2", success: 8, failed: 0, total: 8 },
  { day: "5/3", success: 7, failed: 2, total: 9 },
  { day: "5/4", success: 3, failed: 1, total: 4 },
];

const tokenUsageData = [
  { time: "08:00", tokens: 2400 },
  { time: "09:00", tokens: 8600 },
  { time: "10:00", tokens: 5200 },
  { time: "11:00", tokens: 12400 },
  { time: "12:00", tokens: 3800 },
  { time: "13:00", tokens: 9200 },
  { time: "14:00", tokens: 14600 },
];

const stageDurationData = [
  { stage: "需求分析", avg: 38, p95: 62 },
  { stage: "方案设计", avg: 92, p95: 145 },
  { stage: "代码生成", avg: 145, p95: 220 },
  { stage: "测试生成", avg: 67, p95: 98 },
  { stage: "代码评审", avg: 78, p95: 130 },
  { stage: "交付集成", avg: 25, p95: 38 },
];

const agentSuccessData = [
  { name: "RequirementsAgent", rate: 98.2 },
  { name: "ArchitectAgent", rate: 95.1 },
  { name: "CodegenAgent", rate: 91.8 },
  { name: "TestAgent", rate: 88.4 },
  { name: "ReviewAgent", rate: 97.3 },
  { name: "DeliveryAgent", rate: 99.1 },
];

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
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ color: p.color }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function Analytics() {
  const totalRuns = pipelineRunData.reduce((s, d) => s + d.total, 0);
  const totalSuccess = pipelineRunData.reduce((s, d) => s + d.success, 0);
  const successRate = ((totalSuccess / totalRuns) * 100).toFixed(1);
  const totalTokens = tokenUsageData.reduce((s, d) => s + d.tokens, 0);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
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
            实时数据
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Top Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "总运行次数", value: totalRuns, unit: "次", icon: BarChart2, color: "#5B72FF" },
            { label: "成功率", value: `${successRate}%`, unit: "", icon: CheckCircle, color: "#34C759" },
            { label: "今日 Token 消耗", value: (totalTokens / 1000).toFixed(1) + "K", unit: "", icon: Zap, color: "#FF9F0A" },
            { label: "平均耗时", value: "7.4m", unit: "", icon: Clock, color: "#A259FF" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
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

        {/* Charts Row 1 */}
        <div className="grid grid-cols-2 gap-5 mb-5">
          {/* Pipeline Runs */}
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
              <BarChart data={pipelineRunData} barSize={20} barGap={4}>
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

          {/* Token Usage */}
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
              <AreaChart data={tokenUsageData}>
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

        {/* Charts Row 2 */}
        <div className="grid grid-cols-2 gap-5">
          {/* Stage Duration */}
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
              <BarChart data={stageDurationData} layout="vertical" barSize={10}>
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

          {/* Agent Success Rate */}
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
              {agentSuccessData.map((agent, i) => (
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
                      transition={{ duration: 0.8, delay: 0.4 + i * 0.06, ease: "easeOut" }}
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
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

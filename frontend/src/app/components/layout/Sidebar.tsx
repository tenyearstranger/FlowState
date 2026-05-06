import { useCallback } from "react";
import { NavLink, useLocation } from "react-router";
import {
  LayoutDashboard,
  GitBranch,
  Bot,
  CheckSquare,
  BarChart2,
  Settings,
  Zap,
  ChevronRight,
} from "lucide-react";
import { motion } from "motion/react";
import { useApiQuery } from "../../hooks/useApiQuery";
import { agentsApi, checkpointsApi } from "../../lib/api/services";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "概览", exact: true },
  { to: "/pipelines", icon: GitBranch, label: "流水线" },
  { to: "/checkpoints", icon: CheckSquare, label: "审批检查点" },
  { to: "/settings?tab=agents", icon: Bot, label: "Agent 管理", settingsTab: "agents" },
  { to: "/analytics", icon: BarChart2, label: "可观测性" },
];

const bottomItems = [
  { to: "/settings?tab=pipeline", icon: Settings, label: "设置", settingsTab: "settings" },
];

export function Sidebar() {
  const location = useLocation();
  const sidebarQuery = useApiQuery(
    useCallback(async (signal: AbortSignal) => {
      const [agents, checkpoints] = await Promise.all([
        agentsApi.list({ signal }),
        checkpointsApi.list({ signal }),
      ]);

      return { agents, checkpoints };
    }, []),
    []
  );
  const runningAgents =
    sidebarQuery.data?.agents.filter((agent) => agent.status === "running").length ?? 0;
  const pendingCheckpoints =
    sidebarQuery.data?.checkpoints.filter((checkpoint) => checkpoint.status === "pending").length ?? 0;
  const currentSettingsTab = new URLSearchParams(location.search).get("tab");

  const isActive = (to: string, exact?: boolean, settingsTab?: string) => {
    if (settingsTab) {
      if (settingsTab === "settings") {
        return location.pathname === "/settings" && currentSettingsTab !== "agents";
      }
      return location.pathname === "/settings" && currentSettingsTab === settingsTab;
    }
    if (exact) return location.pathname === to;
    return location.pathname.startsWith(to);
  };

  return (
    <aside
      className="w-[220px] h-full flex flex-col select-none"
      style={{
        background: "rgba(16, 16, 20, 0.85)",
        backdropFilter: "blur(20px)",
        borderRight: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, #5B72FF 0%, #A259FF 100%)",
              boxShadow: "0 2px 12px rgba(91,114,255,0.4)",
            }}
          >
            <Zap size={15} className="text-white" />
          </div>
          <div>
            <div
              className="text-white"
              style={{ fontSize: 14, fontWeight: 600, letterSpacing: "-0.3px" }}
            >
              AI DevFlow
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", letterSpacing: "0.5px" }}>
              研发流程引擎
            </div>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: "rgba(255,255,255,0.05)", margin: "0 16px 12px" }} />

      {/* Nav Items */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const active = isActive(item.to, item.exact, item.settingsTab);
          const badge = item.to === "/checkpoints" ? pendingCheckpoints : undefined;
          return (
            <NavLink key={item.to} to={item.to} end={item.exact}>
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer relative overflow-hidden group"
                style={{
                  background: active
                    ? "rgba(91,114,255,0.15)"
                    : "transparent",
                  transition: "background 0.15s ease",
                }}
              >
                {active && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 rounded-lg"
                    style={{
                      background: "rgba(91,114,255,0.12)",
                      borderLeft: "2px solid rgba(91,114,255,0.9)",
                    }}
                    initial={false}
                    transition={{ type: "spring", stiffness: 400, damping: 35 }}
                  />
                )}
                {!active && (
                  <div
                    className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ background: "rgba(255,255,255,0.04)" }}
                  />
                )}
                <item.icon
                  size={15}
                  className="relative z-10 flex-shrink-0"
                  style={{
                    color: active ? "#7C8FFF" : "rgba(255,255,255,0.45)",
                  }}
                />
                <span
                  className="relative z-10 flex-1"
                  style={{
                    fontSize: 13,
                    fontWeight: active ? 500 : 400,
                    color: active ? "#E8EAFF" : "rgba(255,255,255,0.55)",
                  }}
                >
                  {item.label}
                </span>
                {badge ? (
                  <span
                    className="relative z-10 px-1.5 py-0.5 rounded-full"
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      background: "rgba(255,80,80,0.2)",
                      color: "#FF6B6B",
                      border: "1px solid rgba(255,80,80,0.25)",
                    }}
                  >
                    {badge}
                  </span>
                ) : null}
              </motion.div>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-4 space-y-0.5">
        <div style={{ height: 1, background: "rgba(255,255,255,0.05)", margin: "8px 4px 8px" }} />

        {/* Status indicator */}
        <div
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg mb-1"
          style={{ background: "rgba(52,199,89,0.06)", border: "1px solid rgba(52,199,89,0.12)" }}
        >
          <div className="relative flex items-center">
            <div className="w-2 h-2 rounded-full" style={{ background: "#34C759" }} />
            <div
              className="absolute w-2 h-2 rounded-full animate-ping"
              style={{ background: "#34C759", opacity: 0.4 }}
            />
          </div>
          <span style={{ fontSize: 11, color: "rgba(52,199,89,0.9)", fontWeight: 500 }}>
            {sidebarQuery.loading ? "同步 Agent 状态..." : `${runningAgents} 个 Agent 运行中`}
          </span>
        </div>

        {bottomItems.map((item) => {
          const active = isActive(item.to, false, item.settingsTab);
          return (
            <NavLink key={item.to} to={item.to}>
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer group"
                style={{
                  background: active ? "rgba(91,114,255,0.12)" : "transparent",
                }}
              >
                <div
                  className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ background: "rgba(255,255,255,0.04)" }}
                />
                <item.icon
                  size={15}
                  style={{ color: active ? "#7C8FFF" : "rgba(255,255,255,0.4)" }}
                />
                <span
                  style={{
                    fontSize: 13,
                    color: active ? "#E8EAFF" : "rgba(255,255,255,0.5)",
                    fontWeight: active ? 500 : 400,
                  }}
                >
                  {item.label}
                </span>
              </motion.div>
            </NavLink>
          );
        })}

        {/* User avatar */}
        <div style={{ height: 1, background: "rgba(255,255,255,0.05)", margin: "8px 4px" }} />
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer hover:bg-white/[0.03] transition-colors">
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: "linear-gradient(135deg, #5B72FF, #A259FF)" }}
          >
            <span style={{ fontSize: 10, fontWeight: 600, color: "white" }}>AD</span>
          </div>
          <div className="flex-1 min-w-0">
            <div style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.75)" }}>
              Admin
            </div>
          </div>
          <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.25)" }} />
        </div>
      </div>
    </aside>
  );
}

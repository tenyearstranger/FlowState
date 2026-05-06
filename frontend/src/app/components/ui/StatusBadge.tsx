type Status = "running" | "completed" | "failed" | "paused" | "pending" | "idle" | "awaiting_review" | "rejected" | "cancelled";

const statusConfig: Record<Status, { label: string; color: string; bg: string; border: string; dot?: boolean }> = {
  running: { label: "运行中", color: "#5B72FF", bg: "rgba(91,114,255,0.1)", border: "rgba(91,114,255,0.2)", dot: true },
  completed: { label: "已完成", color: "#34C759", bg: "rgba(52,199,89,0.1)", border: "rgba(52,199,89,0.2)" },
  failed: { label: "失败", color: "#FF453A", bg: "rgba(255,69,58,0.1)", border: "rgba(255,69,58,0.2)" },
  paused: { label: "已暂停", color: "#FF9F0A", bg: "rgba(255,159,10,0.1)", border: "rgba(255,159,10,0.2)" },
  pending: { label: "等待中", color: "rgba(255,255,255,0.45)", bg: "rgba(255,255,255,0.05)", border: "rgba(255,255,255,0.08)" },
  idle: { label: "空闲", color: "rgba(255,255,255,0.35)", bg: "rgba(255,255,255,0.04)", border: "rgba(255,255,255,0.06)" },
  awaiting_review: { label: "等待审批", color: "#FF9F0A", bg: "rgba(255,159,10,0.1)", border: "rgba(255,159,10,0.2)", dot: true },
  rejected: { label: "已拒绝", color: "#FF453A", bg: "rgba(255,69,58,0.1)", border: "rgba(255,69,58,0.2)" },
  cancelled: { label: "已终止", color: "#FF453A", bg: "rgba(255,69,58,0.1)", border: "rgba(255,69,58,0.2)" },
};

interface StatusBadgeProps {
  status: Status;
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.idle;
  const isSmall = size === "sm";

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full"
      style={{
        padding: isSmall ? "2px 7px" : "3px 9px",
        fontSize: isSmall ? 10 : 11,
        fontWeight: 500,
        color: config.color,
        background: config.bg,
        border: `1px solid ${config.border}`,
        letterSpacing: "0.2px",
      }}
    >
      {config.dot && (
        <span
          className="relative inline-flex"
          style={{ width: 6, height: 6 }}
        >
          <span
            className="absolute inline-flex w-full h-full rounded-full animate-ping"
            style={{ background: config.color, opacity: 0.4 }}
          />
          <span
            className="relative inline-flex rounded-full"
            style={{ width: 6, height: 6, background: config.color }}
          />
        </span>
      )}
      {!config.dot && (
        <span
          className="rounded-full"
          style={{ width: 5, height: 5, background: config.color, flexShrink: 0 }}
        />
      )}
      {config.label}
    </span>
  );
}

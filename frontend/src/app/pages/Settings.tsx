import { useState } from "react";
import { motion } from "motion/react";
import {
  Settings as SettingsIcon,
  Key,
  Bot,
  GitBranch,
  Check,
  Eye,
  EyeOff,
  RefreshCw,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";

const providers = [
  {
    id: "openai",
    name: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    color: "#74AA9C",
    active: true,
    hasKey: true,
    maskedKey: "sk-proj-••••••••••••••••••••••••••••••••••••••••••XXXX",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    models: ["claude-3-7-sonnet", "claude-3-5-haiku", "claude-3-opus"],
    color: "#D4A96A",
    active: true,
    hasKey: true,
    maskedKey: "sk-ant-••••••••••••••••••••••••••••••••••••••••XXXX",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    models: ["deepseek-chat", "deepseek-coder"],
    color: "#6B9FFF",
    active: false,
    hasKey: false,
    maskedKey: "",
  },
  {
    id: "qwen",
    name: "通义千问 (Qwen)",
    models: ["qwen-max", "qwen-plus", "qwen-turbo"],
    color: "#FF7A5C",
    active: false,
    hasKey: false,
    maskedKey: "",
  },
];

type Tab = "providers" | "pipeline" | "general";

export function Settings() {
  const [activeTab, setActiveTab] = useState<Tab>("providers");
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs: { id: Tab; label: string; icon: typeof SettingsIcon }[] = [
    { id: "providers", label: "LLM 提供商", icon: Bot },
    { id: "pipeline", label: "Pipeline 配置", icon: GitBranch },
    { id: "general", label: "通用设置", icon: SettingsIcon },
  ];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "white", letterSpacing: "-0.4px" }}>
            设置
          </h1>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>
            配置 LLM 提供商、Pipeline 参数与系统设置
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          className="flex items-center gap-2 px-4 py-2 rounded-xl"
          style={{
            background: saved
              ? "rgba(52,199,89,0.12)"
              : "linear-gradient(135deg, #5B72FF, #A259FF)",
            border: saved ? "1px solid rgba(52,199,89,0.25)" : "none",
            color: saved ? "#34C759" : "white",
            fontSize: 13,
            fontWeight: 500,
            cursor: "pointer",
            boxShadow: saved ? "none" : "0 4px 14px rgba(91,114,255,0.3)",
            transition: "all 0.2s",
          }}
        >
          {saved ? <><Check size={13} /> 已保存</> : "保存更改"}
        </motion.button>
      </div>

      {/* Tabs */}
      <div
        className="flex items-center gap-1 px-8 py-3 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all"
            style={{
              background:
                activeTab === tab.id
                  ? "rgba(91,114,255,0.12)"
                  : "transparent",
              color:
                activeTab === tab.id
                  ? "#A0ABFF"
                  : "rgba(255,255,255,0.45)",
              border: `1px solid ${
                activeTab === tab.id
                  ? "rgba(91,114,255,0.22)"
                  : "transparent"
              }`,
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            <tab.icon size={12} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {activeTab === "providers" && (
          <div className="max-w-2xl space-y-4">
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginBottom: 20 }}>
              配置 AI 模型提供商，Agent 将在运行时使用这些配置。支持运行时切换。
            </p>

            {providers.map((provider, i) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                index={i}
                showKey={showKey[provider.id] || false}
                onToggleKey={() =>
                  setShowKey((prev) => ({ ...prev, [provider.id]: !prev[provider.id] }))
                }
              />
            ))}

            <button
              className="flex items-center gap-2 w-full py-3 rounded-xl"
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px dashed rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.4)",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              <Plus size={13} /> 添加自定义提供商
            </button>
          </div>
        )}

        {activeTab === "pipeline" && (
          <div className="max-w-2xl space-y-6">
            <SectionCard title="默认 Pipeline 配置">
              <SettingRow
                label="默认 LLM 提供商"
                desc="新建 Agent 时的默认提供商"
              >
                <select
                  className="px-3 py-2 rounded-lg"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 12,
                    outline: "none",
                  }}
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </SettingRow>
              <SettingRow
                label="Agent 最大重试次数"
                desc="当 Agent 执行失败或被 Reject 时的最大重试次数"
              >
                <input
                  type="number"
                  defaultValue={3}
                  min={1}
                  max={10}
                  className="w-20 px-3 py-2 rounded-lg text-center"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 12,
                    outline: "none",
                  }}
                />
              </SettingRow>
              <SettingRow
                label="检查点超时时间"
                desc="Human-in-the-Loop 检查点等待人工审批的超时时间（分钟）"
              >
                <input
                  type="number"
                  defaultValue={60}
                  min={5}
                  className="w-20 px-3 py-2 rounded-lg text-center"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 12,
                    outline: "none",
                  }}
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="Git 集成">
              <SettingRow label="自动创建分支" desc="代码生成完成后自动创建功能分支">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
              <SettingRow label="自动提交代码" desc="代码生成后自动 commit（需人工审批后才推送）">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
              <SettingRow label="自动发起 MR" desc="交付集成阶段自动创建 Merge Request">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
              <SettingRow label="Branch 命名规则" desc="">
                <input
                  type="text"
                  defaultValue="devflow/{pipeline-id}-{slug}"
                  className="px-3 py-2 rounded-lg"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 11,
                    fontFamily: "monospace",
                    outline: "none",
                    width: 220,
                  }}
                />
              </SettingRow>
            </SectionCard>

            <SectionCard title="代码库上下文">
              <SettingRow label="代码库路径" desc="Agent 分析代码时的根目录">
                <input
                  type="text"
                  defaultValue="./src"
                  className="px-3 py-2 rounded-lg"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 11,
                    fontFamily: "monospace",
                    outline: "none",
                    width: 160,
                  }}
                />
              </SettingRow>
              <SettingRow label="语义索引" desc="对代码库进行向量化索引，提升 Agent 检索准确率">
                <ToggleSwitch defaultOn={false} />
              </SettingRow>
            </SectionCard>
          </div>
        )}

        {activeTab === "general" && (
          <div className="max-w-2xl space-y-6">
            <SectionCard title="通知">
              <SettingRow label="检查点提醒" desc="有新的检查点需要审批时发送通知">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
              <SettingRow label="Pipeline 完成通知" desc="Pipeline 运行完成时通知">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
              <SettingRow label="Agent 失败告警" desc="Agent 执行失败时即时告警">
                <ToggleSwitch defaultOn={true} />
              </SettingRow>
            </SectionCard>

            <SectionCard title="数据与隐私">
              <SettingRow label="保留日志天数" desc="Pipeline 运行日志的保留时间">
                <select
                  className="px-3 py-2 rounded-lg"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 12,
                    outline: "none",
                  }}
                >
                  <option>7 天</option>
                  <option>30 天</option>
                  <option>90 天</option>
                  <option>永久</option>
                </select>
              </SettingRow>
              <SettingRow label="匿名使用统计" desc="帮助改进产品（不包含代码内容）">
                <ToggleSwitch defaultOn={false} />
              </SettingRow>
            </SectionCard>

            <SectionCard title="关于">
              <div className="py-2 space-y-2">
                {[
                  { label: "版本", value: "v0.1.0-alpha" },
                  { label: "Pipeline 引擎", value: "v0.1.0" },
                  { label: "API 版本", value: "v1" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-1">
                    <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>
                      {item.label}
                    </span>
                    <span
                      style={{
                        fontSize: 12,
                        fontFamily: "monospace",
                        color: "rgba(255,255,255,0.35)",
                      }}
                    >
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        )}
      </div>
    </div>
  );
}

function ProviderCard({
  provider,
  index,
  showKey,
  onToggleKey,
}: {
  provider: (typeof providers)[0];
  index: number;
  showKey: boolean;
  onToggleKey: () => void;
}) {
  const [active, setActive] = useState(provider.active);
  const [hasKey, setHasKey] = useState(provider.hasKey);
  const [inputKey, setInputKey] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: `1px solid ${active ? `${provider.color}25` : "rgba(255,255,255,0.07)"}`,
      }}
    >
      {/* Provider Header */}
      <div
        className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: `${provider.color}15`,
              border: `1px solid ${provider.color}25`,
            }}
          >
            <Bot size={14} style={{ color: provider.color }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
              {provider.name}
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>
              {provider.models.join(" · ")}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {hasKey && (
            <span
              className="flex items-center gap-1 px-2 py-0.5 rounded-md"
              style={{
                fontSize: 10,
                color: "#34C759",
                background: "rgba(52,199,89,0.1)",
                border: "1px solid rgba(52,199,89,0.2)",
              }}
            >
              <Check size={9} /> 已配置
            </span>
          )}
          <button onClick={() => setActive(!active)} style={{ background: "none", border: "none", cursor: "pointer" }}>
            {active ? (
              <ToggleRight size={22} style={{ color: provider.color }} />
            ) : (
              <ToggleLeft size={22} style={{ color: "rgba(255,255,255,0.25)" }} />
            )}
          </button>
        </div>
      </div>

      {/* API Key */}
      <div className="px-5 py-4">
        <label
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "rgba(255,255,255,0.45)",
            display: "flex",
            alignItems: "center",
            gap: 5,
            marginBottom: 8,
          }}
        >
          <Key size={10} /> API Key
        </label>

        {hasKey ? (
          <div className="flex items-center gap-2">
            <div
              className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontFamily: "monospace",
                  color: "rgba(255,255,255,0.5)",
                  flex: 1,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {showKey ? "sk-••••-real-key-hidden-for-demo-•••••" : provider.maskedKey}
              </span>
            </div>
            <button
              onClick={onToggleKey}
              className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
            >
              {showKey ? (
                <EyeOff size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              ) : (
                <Eye size={13} style={{ color: "rgba(255,255,255,0.4)" }} />
              )}
            </button>
            <button
              onClick={() => setHasKey(false)}
              className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
            >
              <Trash2 size={13} style={{ color: "rgba(255,69,58,0.6)" }} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder={`sk-...`}
              className="flex-1 px-3 py-2 rounded-lg"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "rgba(255,255,255,0.7)",
                fontSize: 12,
                fontFamily: "monospace",
                outline: "none",
              }}
            />
            <button
              onClick={() => {
                if (inputKey.trim()) {
                  setHasKey(true);
                  setInputKey("");
                }
              }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg"
              style={{
                background: inputKey.trim()
                  ? `${provider.color}18`
                  : "rgba(255,255,255,0.04)",
                border: `1px solid ${inputKey.trim() ? `${provider.color}30` : "rgba(255,255,255,0.08)"}`,
                color: inputKey.trim() ? provider.color : "rgba(255,255,255,0.3)",
                fontSize: 12,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              <Check size={12} /> 保存
            </button>
          </div>
        )}

        {hasKey && (
          <div className="flex items-center gap-2 mt-3">
            <button
              className="flex items-center gap-1 px-2 py-1 rounded-md hover:bg-white/[0.04] transition-colors"
              style={{
                fontSize: 10,
                color: "rgba(255,255,255,0.4)",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.06)",
                cursor: "pointer",
              }}
            >
              <RefreshCw size={9} /> 测试连接
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <div
        className="px-5 py-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.5)" }}>
          {title}
        </span>
      </div>
      <div className="px-5 py-2">{children}</div>
    </div>
  );
}

function SettingRow({
  label,
  desc,
  children,
}: {
  label: string;
  desc: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="flex items-center justify-between py-3"
      style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
    >
      <div className="flex-1 pr-4">
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.75)", fontWeight: 500 }}>
          {label}
        </div>
        {desc && (
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>
            {desc}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

function ToggleSwitch({ defaultOn }: { defaultOn: boolean }) {
  const [on, setOn] = useState(defaultOn);
  return (
    <button
      onClick={() => setOn(!on)}
      style={{ background: "none", border: "none", cursor: "pointer" }}
    >
      {on ? (
        <ToggleRight size={24} style={{ color: "#5B72FF" }} />
      ) : (
        <ToggleLeft size={24} style={{ color: "rgba(255,255,255,0.25)" }} />
      )}
    </button>
  );
}

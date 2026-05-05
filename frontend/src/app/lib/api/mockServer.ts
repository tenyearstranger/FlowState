import type { Agent } from "../../types/agent";
import type { ActivityItem, AnalyticsOverview } from "../../types/analytics";
import type { Checkpoint } from "../../types/checkpoint";
import type { CreatePipelinePayload, Pipeline, PipelineStage } from "../../types/pipeline";

type QueryValue = string | number | boolean | null | undefined;

interface MockRequestOptions {
  body?: unknown;
  method: string;
  path: string;
  query?: Record<string, QueryValue>;
}

const TEMPLATE_LABELS: Record<string, string> = {
  bugfix: "Bug 修复",
  feature: "新功能开发",
  refactor: "重构优化",
};

const PIPELINE_STAGE_TEMPLATE: PipelineStage[] = [
  {
    id: "stage-1",
    name: "需求分析",
    nameEn: "Requirements Analysis",
    agent: "RequirementsAgent",
    status: "completed",
    duration: 42,
    tokens: 3240,
    output: `## 结构化需求文档

### 功能目标
实现一个用户认证系统，支持 JWT Token 刷新机制。

### 核心需求
1. 用户注册：邮箱 + 密码，自动发送验证邮件
2. 用户登录：支持邮箱/用户名登录，返回 Access Token (15min) + Refresh Token (7d)
3. Token 刷新：Access Token 过期后自动刷新，无需重新登录
4. 用户登出：吊销 Refresh Token，清除会话`,
  },
  {
    id: "stage-2",
    name: "方案设计",
    nameEn: "Design",
    agent: "ArchitectAgent",
    status: "awaiting_review",
    duration: 87,
    tokens: 5680,
    isCheckpoint: true,
    output: `## 技术方案设计

### 架构决策
采用无状态 JWT 方案，Refresh Token 存储于 Redis，支持主动吊销。

### API 设计
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET /auth/me`,
  },
  {
    id: "stage-3",
    name: "代码生成",
    nameEn: "Code Generation",
    agent: "CodegenAgent",
    status: "idle",
    duration: 0,
    tokens: 0,
    output: `## 代码变更集

等待方案审批通过后生成。`,
  },
  {
    id: "stage-4",
    name: "测试生成",
    nameEn: "Test Generation",
    agent: "TestAgent",
    status: "idle",
  },
  {
    id: "stage-5",
    name: "代码评审",
    nameEn: "Code Review",
    agent: "ReviewAgent",
    status: "idle",
    isCheckpoint: true,
  },
  {
    id: "stage-6",
    name: "交付集成",
    nameEn: "Delivery",
    agent: "DeliveryAgent",
    status: "idle",
  },
];

function createStages(prefix: string, statuses: PipelineStage["status"][]): PipelineStage[] {
  return PIPELINE_STAGE_TEMPLATE.map((stage, index) => ({
    ...stage,
    id: `${prefix}-stage-${index + 1}`,
    status: statuses[index] ?? stage.status,
    tokens: statuses[index] === "idle" ? undefined : stage.tokens,
    duration: statuses[index] === "idle" ? undefined : stage.duration,
    output: statuses[index] === "idle" && index > 1 ? undefined : stage.output,
  }));
}

const pipelines: Pipeline[] = [
  {
    id: "pl-001",
    name: "用户认证系统 · JWT Token 刷新",
    description: "实现 Access Token / Refresh Token 双 Token 机制，支持无感刷新",
    status: "running",
    progress: 28,
    currentStage: 1,
    template: "新功能开发",
    stages: createStages("pl-001", ["completed", "awaiting_review", "idle", "idle", "idle", "idle"]),
    createdAt: "2026-05-04T08:30:00Z",
    updatedAt: "2026-05-04T09:12:00Z",
  },
  {
    id: "pl-002",
    name: "API 限流中间件重构",
    description: "将现有的 IP 限流升级为基于用户/租户的分级限流策略",
    status: "paused",
    progress: 33,
    currentStage: 1,
    template: "重构优化",
    stages: createStages("pl-002", ["completed", "awaiting_review", "idle", "idle", "idle", "idle"]),
    createdAt: "2026-05-03T14:20:00Z",
    updatedAt: "2026-05-03T16:45:00Z",
  },
  {
    id: "pl-003",
    name: "数据库连接池优化",
    description: "修复高并发场景下连接池泄漏问题，优化超时配置",
    status: "completed",
    progress: 100,
    currentStage: 5,
    template: "Bug 修复",
    stages: createStages("pl-003", ["completed", "completed", "completed", "completed", "completed", "completed"]),
    createdAt: "2026-05-02T10:00:00Z",
    updatedAt: "2026-05-02T14:30:00Z",
  },
  {
    id: "pl-004",
    name: "消息推送服务接入 WebSocket",
    description: "为实时通知功能添加 WebSocket 支持，替换现有轮询方案",
    status: "pending",
    progress: 0,
    currentStage: 0,
    template: "新功能开发",
    stages: createStages("pl-004", ["idle", "idle", "idle", "idle", "idle", "idle"]),
    createdAt: "2026-05-04T10:00:00Z",
    updatedAt: "2026-05-04T10:00:00Z",
  },
  {
    id: "pl-005",
    name: "日志系统升级 · OpenTelemetry",
    description: "统一接入 OpenTelemetry，支持分布式追踪和指标采集",
    status: "failed",
    progress: 67,
    currentStage: 3,
    template: "重构优化",
    stages: createStages("pl-005", ["completed", "completed", "completed", "failed", "idle", "idle"]),
    createdAt: "2026-05-01T09:00:00Z",
    updatedAt: "2026-05-01T11:20:00Z",
  },
];

const pipelineLogs: Record<string, string[]> = {
  "pl-001": [
    "[08:30:01] Pipeline pl-001 已启动",
    "[08:30:02] RequirementsAgent 初始化，模型: gpt-4o",
    "[08:30:35] 需求分析完成，输出 423 tokens",
    "[08:30:36] ArchitectAgent 初始化，模型: claude-3-7-sonnet",
    "[08:31:08] 技术方案已生成，触发检查点 [方案设计审批]",
    "[08:31:09] ⏸ 等待人工审批...",
  ],
  "pl-002": [
    "[15:02:11] Pipeline pl-002 已启动",
    "[15:08:42] RequirementsAgent 需求梳理完成",
    "[15:10:03] ArchitectAgent 生成限流重构方案",
    "[15:10:04] ⏸ 等待人工审批...",
  ],
  "pl-003": [
    "[10:00:01] Pipeline pl-003 已启动",
    "[13:58:44] DeliveryAgent 已创建 MR #42",
    "[14:30:00] ✓ 流水线执行完成",
  ],
  "pl-004": ["[10:00:00] Pipeline pl-004 已创建，等待调度执行"],
  "pl-005": [
    "[09:00:01] Pipeline pl-005 已启动",
    "[10:44:15] TestAgent 正在分析代码变更集...",
    "[10:51:32] ERROR 测试覆盖率不足 (62%)",
  ],
};

const agents: Agent[] = [
  {
    id: "agent-1",
    name: "RequirementsAgent",
    role: "需求分析师",
    description: "理解自然语言需求，澄清歧义，输出结构化需求文档与验收标准",
    model: "gpt-4o",
    provider: "OpenAI",
    status: "idle",
    tasksCompleted: 47,
    avgDuration: 38,
    avgTokens: 3200,
    color: "#5B72FF",
  },
  {
    id: "agent-2",
    name: "ArchitectAgent",
    role: "架构设计师",
    description: "分析现有代码库，设计技术方案，确定文件变更清单与 API 接口",
    model: "claude-3-7-sonnet",
    provider: "Anthropic",
    status: "running",
    tasksCompleted: 41,
    avgDuration: 92,
    avgTokens: 5800,
    color: "#A259FF",
  },
  {
    id: "agent-3",
    name: "CodegenAgent",
    role: "代码生成器",
    description: "按照技术方案逐文件生成或修改代码，输出完整的代码变更集",
    model: "claude-3-7-sonnet",
    provider: "Anthropic",
    status: "idle",
    tasksCompleted: 39,
    avgDuration: 145,
    avgTokens: 12600,
    color: "#FF7A5C",
  },
  {
    id: "agent-4",
    name: "TestAgent",
    role: "测试工程师",
    description: "根据代码变更集自动生成单元测试和集成测试，输出测试报告",
    model: "gpt-4o-mini",
    provider: "OpenAI",
    status: "running",
    tasksCompleted: 35,
    avgDuration: 67,
    avgTokens: 4100,
    color: "#34C759",
  },
  {
    id: "agent-5",
    name: "ReviewAgent",
    role: "代码审查员",
    description: "多维度审查代码变更（正确性、安全性、规范性），生成评审报告",
    model: "gpt-4o",
    provider: "OpenAI",
    status: "idle",
    tasksCompleted: 38,
    avgDuration: 78,
    avgTokens: 6200,
    color: "#FF9F0A",
  },
  {
    id: "agent-6",
    name: "DeliveryAgent",
    role: "交付集成",
    description: "整合所有变更，自动创建 Git 分支、提交代码、发起 MR/PR",
    model: "gpt-4o-mini",
    provider: "OpenAI",
    status: "running",
    tasksCompleted: 30,
    avgDuration: 25,
    avgTokens: 1800,
    color: "#00C7BE",
  },
];

let checkpoints: Checkpoint[] = [
  {
    id: "cp-001",
    pipelineId: "pl-001",
    pipelineName: "用户认证系统 · JWT Token 刷新",
    stage: "方案设计",
    stageIndex: 1,
    status: "pending",
    createdAt: "2026-05-04T08:52:00Z",
    output: pipelines[0].stages[1].output ?? "",
  },
  {
    id: "cp-002",
    pipelineId: "pl-002",
    pipelineName: "API 限流中间件重构",
    stage: "方案设计",
    stageIndex: 1,
    status: "pending",
    createdAt: "2026-05-03T15:10:00Z",
    output: `## API 限流重构方案

### 当前问题
现有方案仅支持 IP 级别限流，无法区分不同用户等级。

### 方案设计
采用令牌桶算法，基于 Redis 实现分级限流。`,
  },
];

let activities: ActivityItem[] = [
  { time: "2分钟前", text: "pl-001 · ArchitectAgent 产出方案设计，等待人工审批", type: "checkpoint" },
  { time: "15分钟前", text: "pl-002 · 方案设计检查点等待审批（已超时 17m）", type: "warning" },
  { time: "1小时前", text: "pl-005 · TestAgent 运行失败，原因：测试覆盖率不足 (62%)", type: "error" },
  { time: "3小时前", text: "pl-003 · DeliveryAgent 成功创建 MR #42，已合并", type: "success" },
];

const analyticsOverview: AnalyticsOverview = {
  summary: {
    totalRuns: 41,
    totalSuccess: 36,
    totalTokens: 56200,
    averageDurationMinutes: 7.4,
    mergedChanges: 18,
  },
  pipelineRuns: [
    { day: "4/28", success: 3, failed: 0, total: 3 },
    { day: "4/29", success: 5, failed: 1, total: 6 },
    { day: "4/30", success: 4, failed: 0, total: 4 },
    { day: "5/1", success: 6, failed: 1, total: 7 },
    { day: "5/2", success: 8, failed: 0, total: 8 },
    { day: "5/3", success: 7, failed: 2, total: 9 },
    { day: "5/4", success: 3, failed: 1, total: 4 },
  ],
  tokenUsage: [
    { time: "08:00", tokens: 2400 },
    { time: "09:00", tokens: 8600 },
    { time: "10:00", tokens: 5200 },
    { time: "11:00", tokens: 12400 },
    { time: "12:00", tokens: 3800 },
    { time: "13:00", tokens: 9200 },
    { time: "14:00", tokens: 14600 },
  ],
  stageDurations: [
    { stage: "需求分析", avg: 38, p95: 62 },
    { stage: "方案设计", avg: 92, p95: 145 },
    { stage: "代码生成", avg: 145, p95: 220 },
    { stage: "测试生成", avg: 67, p95: 98 },
    { stage: "代码评审", avg: 78, p95: 130 },
    { stage: "交付集成", avg: 25, p95: 38 },
  ],
  agentSuccessRates: [
    { name: "RequirementsAgent", rate: 98.2 },
    { name: "ArchitectAgent", rate: 95.1 },
    { name: "CodegenAgent", rate: 91.8 },
    { name: "TestAgent", rate: 88.4 },
    { name: "ReviewAgent", rate: 97.3 },
    { name: "DeliveryAgent", rate: 99.1 },
  ],
};

function clonePipeline(pipeline: Pipeline): Pipeline {
  return {
    ...pipeline,
    stages: pipeline.stages.map((stage) => ({ ...stage })),
  };
}

function cloneCheckpoint(checkpoint: Checkpoint): Checkpoint {
  return { ...checkpoint };
}

function cloneActivities(items: ActivityItem[]) {
  return items.map((item) => ({ ...item }));
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseBody<T>(body: unknown): T {
  if (typeof body === "string") {
    return JSON.parse(body) as T;
  }

  return body as T;
}

function prependActivity(activity: ActivityItem) {
  activities = [activity, ...activities].slice(0, 20);
}

function createPipelineName(requirement: string) {
  const firstLine = requirement.split("\n")[0].trim();
  return firstLine.length > 26 ? `${firstLine.slice(0, 26)}...` : firstLine;
}

function buildNewPipeline(payload: CreatePipelinePayload): Pipeline {
  const nextId = `pl-${String(pipelines.length + 1).padStart(3, "0")}`;
  const now = new Date().toISOString();
  const stageStatuses: PipelineStage["status"][] = ["running", "idle", "idle", "idle", "idle", "idle"];
  const stages = createStages(nextId, stageStatuses).map((stage, index) => ({
    ...stage,
    output:
      index === 0
        ? `## 需求描述

${payload.requirement}

Mock API 已接收该流水线请求，后续可直接替换为真实后端返回。`
        : stage.output,
  }));

  stages[0].status = "running";
  stages[0].duration = 0;
  stages[0].tokens = 0;

  return {
    id: nextId,
    name: createPipelineName(payload.requirement),
    description: payload.requirement,
    status: "running",
    progress: 8,
    currentStage: 0,
    template: TEMPLATE_LABELS[payload.template] ?? payload.template,
    stages,
    createdAt: now,
    updatedAt: now,
  };
}

function updatePipelineAfterCheckpoint(checkpoint: Checkpoint, approved: boolean, rejectReason?: string) {
  const pipeline = pipelines.find((item) => item.id === checkpoint.pipelineId);
  if (!pipeline) {
    return;
  }

  const currentStage = pipeline.stages[checkpoint.stageIndex];
  if (!currentStage) {
    return;
  }

  if (approved) {
    currentStage.status = "completed";
    currentStage.completedAt = new Date().toISOString();
    const nextStage = pipeline.stages[checkpoint.stageIndex + 1];
    if (nextStage) {
      nextStage.status = "running";
      nextStage.startedAt = new Date().toISOString();
      nextStage.tokens = nextStage.tokens ?? 0;
      nextStage.duration = nextStage.duration ?? 0;
      pipeline.currentStage = checkpoint.stageIndex + 1;
      pipeline.progress = Math.round(((checkpoint.stageIndex + 1) / pipeline.stages.length) * 100);
      pipeline.status = "running";
    } else {
      pipeline.currentStage = checkpoint.stageIndex;
      pipeline.progress = 100;
      pipeline.status = "completed";
    }
    pipeline.updatedAt = new Date().toISOString();
    pipelineLogs[pipeline.id] = [
      ...(pipelineLogs[pipeline.id] ?? []),
      `[${new Date().toLocaleTimeString("zh-CN", { hour12: false })}] ✓ 检查点审批通过`,
    ];
    prependActivity({
      time: "刚刚",
      text: `${pipeline.id} · ${checkpoint.stage} 检查点审批已通过`,
      type: "success",
    });
    return;
  }

  currentStage.status = "rejected";
  pipeline.status = "paused";
  pipeline.updatedAt = new Date().toISOString();
  pipelineLogs[pipeline.id] = [
    ...(pipelineLogs[pipeline.id] ?? []),
    `[${new Date().toLocaleTimeString("zh-CN", { hour12: false })}] 检查点被拒绝: ${rejectReason ?? "需要重新评审"}`,
  ];
  prependActivity({
    time: "刚刚",
    text: `${pipeline.id} · ${checkpoint.stage} 检查点被拒绝，等待 Agent 重做`,
    type: "warning",
  });
}

export async function mockApiRequest<T>({ body, method, path, query }: MockRequestOptions): Promise<T> {
  await sleep(180);

  if (method === "GET" && path === "/pipelines") {
    return pipelines.map(clonePipeline) as T;
  }

  if (method === "POST" && path === "/pipelines") {
    const payload = parseBody<CreatePipelinePayload>(body);
    const pipeline = buildNewPipeline(payload);
    pipelines.unshift(pipeline);
    pipelineLogs[pipeline.id] = [
      `[${new Date().toLocaleTimeString("zh-CN", { hour12: false })}] Pipeline ${pipeline.id} 已启动`,
      `[${new Date().toLocaleTimeString("zh-CN", { hour12: false })}] RequirementsAgent 正在分析需求...`,
    ];
    prependActivity({
      time: "刚刚",
      text: `${pipeline.id} · 已创建新流水线`,
      type: "success",
    });
    return clonePipeline(pipeline) as T;
  }

  const pipelineMatch = path.match(/^\/pipelines\/([^/]+)$/);
  if (method === "GET" && pipelineMatch) {
    const pipeline = pipelines.find((item) => item.id === pipelineMatch[1]);
    if (!pipeline) {
      throw new Error("未找到流水线");
    }
    return clonePipeline(pipeline) as T;
  }

  const logMatch = path.match(/^\/pipelines\/([^/]+)\/logs$/);
  if (method === "GET" && logMatch) {
    return [...(pipelineLogs[logMatch[1]] ?? [])] as T;
  }

  if (method === "GET" && path === "/agents") {
    return agents.map((agent) => ({ ...agent })) as T;
  }

  if (method === "GET" && path === "/checkpoints") {
    const status = query?.status;
    const result =
      status === "all" || status === undefined
        ? checkpoints
        : checkpoints.filter((checkpoint) => checkpoint.status === status);
    return result.map(cloneCheckpoint) as T;
  }

  const approveMatch = path.match(/^\/checkpoints\/([^/]+)\/approve$/);
  if (method === "POST" && approveMatch) {
    const checkpoint = checkpoints.find((item) => item.id === approveMatch[1]);
    if (!checkpoint) {
      throw new Error("未找到检查点");
    }
    checkpoint.status = "approved";
    updatePipelineAfterCheckpoint(checkpoint, true);
    return cloneCheckpoint(checkpoint) as T;
  }

  const rejectMatch = path.match(/^\/checkpoints\/([^/]+)\/reject$/);
  if (method === "POST" && rejectMatch) {
    const checkpoint = checkpoints.find((item) => item.id === rejectMatch[1]);
    if (!checkpoint) {
      throw new Error("未找到检查点");
    }
    checkpoint.status = "rejected";
    checkpoint.rejectReason = String(parseBody<{ reason?: string }>(body)?.reason ?? "");
    updatePipelineAfterCheckpoint(checkpoint, false, checkpoint.rejectReason);
    return cloneCheckpoint(checkpoint) as T;
  }

  if (method === "GET" && path === "/analytics") {
    return {
      ...analyticsOverview,
      pipelineRuns: analyticsOverview.pipelineRuns.map((item) => ({ ...item })),
      tokenUsage: analyticsOverview.tokenUsage.map((item) => ({ ...item })),
      stageDurations: analyticsOverview.stageDurations.map((item) => ({ ...item })),
      agentSuccessRates: analyticsOverview.agentSuccessRates.map((item) => ({ ...item })),
    } as T;
  }

  if (method === "GET" && path === "/activities/recent") {
    return cloneActivities(activities) as T;
  }

  throw new Error(`未实现的 Mock API: ${method} ${path}`);
}

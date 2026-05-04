export type StageStatus = "idle" | "running" | "completed" | "failed" | "awaiting_review" | "rejected";

export interface PipelineStage {
  id: string;
  name: string;
  nameEn: string;
  agent: string;
  status: StageStatus;
  duration?: number; // seconds
  tokens?: number;
  output?: string;
  isCheckpoint?: boolean;
  startedAt?: string;
  completedAt?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  status: "running" | "completed" | "failed" | "paused" | "pending";
  progress: number;
  currentStage: number;
  stages: PipelineStage[];
  createdAt: string;
  updatedAt: string;
  template?: string;
}

export const PIPELINE_STAGES_TEMPLATE: PipelineStage[] = [
  {
    id: "stage-1",
    name: "需求分析",
    nameEn: "Requirements Analysis",
    agent: "RequirementsAgent",
    status: "completed",
    duration: 42,
    tokens: 3240,
    isCheckpoint: false,
    output: `## 结构化需求文档

### 功能目标
实现一个用户认证系统，支持 JWT Token 刷新机制。

### 核心需求
1. **用户注册**：邮箱 + 密码，自动发送验证邮件
2. **用户登录**：支持邮箱/用户名登录，返回 Access Token (15min) + Refresh Token (7d)
3. **Token 刷新**：Access Token 过期后自动刷新，无需重新登录
4. **用户登出**：吊销 Refresh Token，清除会话

### 验收标准
- [ ] POST /auth/register 注册接口响应 < 500ms
- [ ] POST /auth/login 登录成功返回双 Token
- [ ] POST /auth/refresh Token 刷新成功率 > 99.9%
- [ ] 所有密码字段使用 bcrypt 加密（cost factor >= 12）

### 影响范围
- 新增：auth 模块（3 个文件）
- 修改：用户表（新增字段）
- 依赖：JWT 库、邮件服务`,
  },
  {
    id: "stage-2",
    name: "方案设计",
    nameEn: "Design",
    agent: "ArchitectAgent",
    status: "completed",
    duration: 87,
    tokens: 5680,
    isCheckpoint: true,
    output: `## 技术方案设计

### 架构决策
采用无状态 JWT 方案，Refresh Token 存储于 Redis，支持主动吊销。

### 文件变更清单
\`\`\`
src/
├── auth/
│   ├── auth.controller.ts     [新增] REST 端点
│   ├── auth.service.ts        [新增] 核心业务逻辑
│   ├── auth.module.ts         [新增] NestJS 模块定义
│   ├── jwt.strategy.ts        [新增] Passport JWT 策略
│   └── dto/
│       ├── login.dto.ts       [新增]
│       └── register.dto.ts    [新增]
├── users/
│   └── user.entity.ts         [修改] 新增 refreshTokenHash 字段
└── app.module.ts              [修改] 注册 AuthModule
\`\`\`

### API 设计
| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | 用户注册 |
| POST | /auth/login | 用户登录 |
| POST | /auth/refresh | Token 刷新 |
| POST | /auth/logout | 用户登出 |
| GET | /auth/me | 获取当前用户 |

### 安全考量
- Refresh Token 使用 SHA-256 哈希后存储
- 启用 Redis TTL 自动过期
- Rate Limiting: 登录 5次/分钟`,
  },
  {
    id: "stage-3",
    name: "代码生成",
    nameEn: "Code Generation",
    agent: "CodegenAgent",
    status: "completed",
    duration: 134,
    tokens: 12450,
    isCheckpoint: false,
    output: `## 代码变更集 (Diff)

\`\`\`diff
+ src/auth/auth.service.ts (新增 +187 行)
+ src/auth/auth.controller.ts (新增 +94 行)
+ src/auth/auth.module.ts (新增 +32 行)
+ src/auth/jwt.strategy.ts (新增 +45 行)
+ src/auth/dto/login.dto.ts (新增 +18 行)
+ src/auth/dto/register.dto.ts (新增 +22 行)
~ src/users/user.entity.ts (修改 +3/-0 行)
~ src/app.module.ts (修改 +2/-0 行)
\`\`\`

**总计**: +401 行新增，0 行删除`,
  },
  {
    id: "stage-4",
    name: "测试生成",
    nameEn: "Test Generation",
    agent: "TestAgent",
    status: "running",
    duration: 0,
    tokens: 2100,
    isCheckpoint: false,
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

export const mockPipelines: Pipeline[] = [
  {
    id: "pl-001",
    name: "用户认证系统 · JWT Token 刷新",
    description: "实现 Access Token / Refresh Token 双 Token 机制，支持无感刷新",
    status: "running",
    progress: 55,
    currentStage: 3,
    template: "新功能开发",
    stages: PIPELINE_STAGES_TEMPLATE,
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
    template: "重构流程",
    stages: PIPELINE_STAGES_TEMPLATE.map((s, i) => ({
      ...s,
      id: `pl002-stage-${i}`,
      status: i === 0 ? "completed" : i === 1 ? "awaiting_review" : "idle",
    })),
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
    stages: PIPELINE_STAGES_TEMPLATE.map((s, i) => ({
      ...s,
      id: `pl003-stage-${i}`,
      status: "completed",
    })),
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
    stages: PIPELINE_STAGES_TEMPLATE.map((s, i) => ({
      ...s,
      id: `pl004-stage-${i}`,
      status: "idle",
    })),
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
    template: "重构流程",
    stages: PIPELINE_STAGES_TEMPLATE.map((s, i) => ({
      ...s,
      id: `pl005-stage-${i}`,
      status: i < 3 ? "completed" : i === 3 ? "failed" : "idle",
    })),
    createdAt: "2026-05-01T09:00:00Z",
    updatedAt: "2026-05-01T11:20:00Z",
  },
];

export const mockAgents = [
  {
    id: "agent-1",
    name: "RequirementsAgent",
    role: "需求分析师",
    description: "理解自然语言需求，澄清歧义，输出结构化需求文档与验收标准",
    model: "gpt-4o",
    provider: "OpenAI",
    status: "idle" as const,
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
    status: "idle" as const,
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
    status: "running" as const,
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
    status: "running" as const,
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
    status: "idle" as const,
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
    status: "running" as const,
    tasksCompleted: 30,
    avgDuration: 25,
    avgTokens: 1800,
    color: "#00C7BE",
  },
];

export const mockCheckpoints = [
  {
    id: "cp-001",
    pipelineId: "pl-001",
    pipelineName: "用户认证系统 · JWT Token 刷新",
    stage: "方案设计",
    stageIndex: 1,
    status: "pending" as const,
    createdAt: "2026-05-04T08:52:00Z",
    output: mockPipelines[0].stages[1].output || "",
  },
  {
    id: "cp-002",
    pipelineId: "pl-002",
    pipelineName: "API 限流中间件重构",
    stage: "方案设计",
    stageIndex: 1,
    status: "pending" as const,
    createdAt: "2026-05-03T15:10:00Z",
    output: `## API 限流重构方案

### 当前问题
现有方案仅支持 IP 级别限流，无法区分不同用户等级，导致:
- 免费用户和付费用户共享限额
- 无法对特定 API 设置差异化限流规则

### 方案设计
采用令牌桶算法，基于 Redis 实现分级限流：

\`\`\`
限流维度: user_id + api_path + tier
配额策略:
  - Free:       100 req/min
  - Pro:        1000 req/min
  - Enterprise: 10000 req/min
\`\`\`

### 变更文件
- src/middleware/rate-limit.ts [重写]
- src/config/rate-limit.config.ts [新增]
- src/decorators/throttle.ts [新增]`,
  },
];

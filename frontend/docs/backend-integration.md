# FlowState 后端对接文档

## 目标

前端已经从页面内假数据切换为统一的 RESTful API 数据层。  
当前约定是：

- 开发时如果**没有配置** `VITE_API_BASE_URL`，前端会自动启用内置 Mock API
- 联调或上线时，只要配置 `VITE_API_BASE_URL`，前端就会请求真实后端

相关实现位置：

- API Client: [src/app/lib/api/client.ts](/Users/yuki/code/FlowState/src/app/lib/api/client.ts:1)
- API Services: [src/app/lib/api/services.ts](/Users/yuki/code/FlowState/src/app/lib/api/services.ts:1)
- Dev Mock API: [src/app/lib/api/mockServer.ts](/Users/yuki/code/FlowState/src/app/lib/api/mockServer.ts:1)
- 领域类型: [src/app/types/pipeline.ts](/Users/yuki/code/FlowState/src/app/types/pipeline.ts:1)

## 前端运行方式

### 1. 无后端直接开发

直接执行：

```bash
npm run dev
```

默认行为：

- 若未设置 `VITE_API_BASE_URL`，自动走内置 Mock API
- 页面可正常打开，创建流水线、查看详情、审批检查点、查看分析页都能工作

### 2. 对接真实后端

创建本地环境变量文件，例如 `.env.local`：

```bash
VITE_API_BASE_URL=http://localhost:8080/api
```

然后执行：

```bash
npm run dev
```

此时前端会请求真实后端。

### 3. 强制使用 Mock API

即使配置了后端地址，也可以强制走 mock：

```bash
VITE_USE_MOCK_API=true
```

### 4. 禁止网络失败时回退 Mock

开发环境下，如果已配置真实后端但网络请求直接失败，前端默认会回退到 Mock API，保证 `npm run dev` 可用。  
如果你想严格暴露联调问题，可以配置：

```bash
VITE_DISABLE_MOCK_FALLBACK=true
```

## 接口总览

前端当前使用这些接口：

| Method | Path | 用途 |
|---|---|---|
| GET | `/pipelines` | 流水线列表 |
| POST | `/pipelines` | 创建流水线 |
| GET | `/pipelines/:id` | 流水线详情 |
| GET | `/pipelines/:id/logs` | 流水线运行日志 |
| GET | `/agents` | Agent 列表 |
| GET | `/checkpoints` | 检查点列表 |
| POST | `/checkpoints/:id/approve` | 通过检查点 |
| POST | `/checkpoints/:id/reject` | 拒绝检查点 |
| GET | `/analytics` | 分析面板数据 |
| GET | `/activities/recent` | Dashboard 实时动态 |

## 数据模型

### Pipeline

```ts
type StageStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "awaiting_review"
  | "rejected";

interface PipelineStage {
  id: string;
  name: string;
  nameEn: string;
  agent: string;
  status: StageStatus;
  duration?: number;
  tokens?: number;
  output?: string;
  isCheckpoint?: boolean;
  startedAt?: string;
  completedAt?: string;
}

interface Pipeline {
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
```

### Create Pipeline Request

```ts
interface CreatePipelinePayload {
  template: string;
  requirement: string;
}
```

### Agent

```ts
interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  model: string;
  provider: string;
  status: "idle" | "running";
  tasksCompleted: number;
  avgDuration: number;
  avgTokens: number;
  color: string;
}
```

### Checkpoint

```ts
type CheckpointStatus = "pending" | "approved" | "rejected";

interface Checkpoint {
  id: string;
  pipelineId: string;
  pipelineName: string;
  stage: string;
  stageIndex: number;
  status: CheckpointStatus;
  createdAt: string;
  output: string;
  rejectReason?: string;
}
```

### Analytics

```ts
interface AnalyticsOverview {
  summary: {
    totalRuns: number;
    totalSuccess: number;
    totalTokens: number;
    averageDurationMinutes: number;
    mergedChanges: number;
  };
  pipelineRuns: { day: string; success: number; failed: number; total: number }[];
  tokenUsage: { time: string; tokens: number }[];
  stageDurations: { stage: string; avg: number; p95: number }[];
  agentSuccessRates: { name: string; rate: number }[];
}
```

### Activity

```ts
interface ActivityItem {
  time: string;
  text: string;
  type: "success" | "checkpoint" | "warning" | "error";
}
```

## 接口细节

### 1. 获取流水线列表

`GET /pipelines`

响应：

```json
[
  {
    "id": "pl-001",
    "name": "用户认证系统 · JWT Token 刷新",
    "description": "实现 Access Token / Refresh Token 双 Token 机制，支持无感刷新",
    "status": "running",
    "progress": 28,
    "currentStage": 1,
    "template": "新功能开发",
    "createdAt": "2026-05-04T08:30:00Z",
    "updatedAt": "2026-05-04T09:12:00Z",
    "stages": []
  }
]
```

说明：

- `stages` 建议完整返回，前端列表页会直接使用各阶段状态

### 2. 创建流水线

`POST /pipelines`

请求体：

```json
{
  "template": "feature",
  "requirement": "实现一个用户收藏功能，支持收藏列表分页"
}
```

响应：

```json
{
  "id": "pl-006",
  "name": "实现一个用户收藏功能...",
  "description": "实现一个用户收藏功能，支持收藏列表分页",
  "status": "running",
  "progress": 8,
  "currentStage": 0,
  "template": "新功能开发",
  "createdAt": "2026-05-04T12:00:00.000Z",
  "updatedAt": "2026-05-04T12:00:00.000Z",
  "stages": []
}
```

说明：

- 成功后前端会直接跳转到 `/pipelines/:id`

### 3. 获取流水线详情

`GET /pipelines/:id`

响应：

- 返回完整 `Pipeline`
- `stages` 必须完整返回

### 4. 获取流水线日志

`GET /pipelines/:id/logs`

响应：

```json
[
  "[08:30:01] Pipeline pl-001 已启动",
  "[08:31:09] ⏸ 等待人工审批..."
]
```

说明：

- 当前前端按字符串数组渲染
- 后续如果要升级为流式日志，建议新增 SSE 或 WebSocket，而不是直接改这个接口返回结构

### 5. 获取 Agent 列表

`GET /agents`

响应：

- 返回 `Agent[]`

### 6. 获取检查点列表

`GET /checkpoints?status=all`

响应：

- 返回 `Checkpoint[]`

说明：

- 当前前端固定会传 `status=all`
- 后端可以保留筛选能力，便于未来扩展

### 7. 通过检查点

`POST /checkpoints/:id/approve`

响应：

- 返回更新后的 `Checkpoint`

建议后端联动行为：

- 当前检查点状态改为 `approved`
- 同步推进对应流水线阶段状态
- 更新流水线 `progress`
- 在日志中追加审批通过记录

### 8. 拒绝检查点

`POST /checkpoints/:id/reject`

请求体：

```json
{
  "reason": "限流分层规则还不够清晰，请补充租户维度说明"
}
```

响应：

- 返回更新后的 `Checkpoint`

建议后端联动行为：

- 当前检查点状态改为 `rejected`
- 保存 `rejectReason`
- 同步更新对应流水线阶段状态，例如 `rejected` 或 `paused`

### 9. 获取分析面板数据

`GET /analytics`

响应：

- 返回 `AnalyticsOverview`

说明：

- 这是一个聚合接口，前端希望一次拿齐图表需要的所有数据
- 这样比拆成多个小接口更稳定，也更少改动

### 10. 获取 Dashboard 实时动态

`GET /activities/recent`

响应：

- 返回 `ActivityItem[]`

## 后端实现建议

推荐保留以下分层：

1. `controllers`
   负责 REST 路由和 DTO 校验
2. `services`
   负责业务逻辑和聚合
3. `repositories`
   负责 DB 读写
4. `presenters` 或 `serializers`
   保证对前端输出结构稳定

## 联调建议

建议按这个顺序接：

1. `GET /pipelines`
2. `GET /pipelines/:id`
3. `GET /pipelines/:id/logs`
4. `POST /pipelines`
5. `GET /checkpoints`
6. `POST /checkpoints/:id/approve`
7. `POST /checkpoints/:id/reject`
8. `GET /agents`
9. `GET /analytics`
10. `GET /activities/recent`

这样可以先打通主流程，再接统计与看板类接口。

## 当前前端约束

- 所有时间字段建议返回 ISO 8601 字符串
- `status` 字段必须严格使用前端约定的枚举值
- 列表页和详情页都直接依赖 `stages`
- `analytics` 建议继续保留聚合响应，不要拆散
- `logs` 目前是 `string[]`，最省改动

## 如果后端字段想改名

可以改，但建议先在 `src/app/lib/api/services.ts` 增加一层 adapter，再映射成前端当前领域模型。  
这样页面层不需要跟着一起改，扩展性会更好。

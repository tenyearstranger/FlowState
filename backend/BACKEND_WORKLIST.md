# FlowState 后端当前工作清单

## 这份文档的目的

这份文档基于当前仓库里的前后端代码整理，目标是回答一个问题：

**后端现在真正需要做什么，才能让前端从 mock API 平滑切到真实后端。**

结论先说：

- 前端已经明确了 REST API 形状和页面依赖
- 后端目前已经有 **Pipeline 引擎、Agent、状态存储**
- 但后端 **还没有 HTTP API 层**
- 而且后端内部模型和前端展示模型 **并不是 1:1 对齐**

所以后端当前最重要的工作，不是继续补 Agent，而是：

1. 搭一个 Web API 服务
2. 把引擎模型转换成前端需要的 DTO
3. 把前端依赖的 10 个接口补齐
4. 处理“运行中 / 等待审批 / 驳回 / 统计 / 日志”这些前端展示需求

---

## 一、我看到的当前后端现状

### 1. 已经有的能力

后端已经实现了这些核心能力：

- `DevFlowEngine` 可以创建、运行、审批流水线  
  参考: [backend/src/engine.py](./src/engine.py)
- `StateStore` 可以把 pipeline 状态存到本地 JSON 文件  
  参考: [backend/src/store/state_store.py](./src/store/state_store.py)
- 6 个 Agent 已经具备基础执行逻辑  
  参考:
  - [backend/src/agents/requirement_agent.py](./src/agents/requirement_agent.py)
  - [backend/src/agents/solution_agent.py](./src/agents/solution_agent.py)
  - [backend/src/agents/code_agent.py](./src/agents/code_agent.py)
  - [backend/src/agents/test_agent.py](./src/agents/test_agent.py)
  - [backend/src/agents/review_agent.py](./src/agents/review_agent.py)
  - [backend/src/agents/delivery_agent.py](./src/agents/delivery_agent.py)
- 已有端到端连通性测试脚本  
  参考: [backend/tests/test_pipeline_full.py](./tests/test_pipeline_full.py)

### 2. 还没有的能力

当前后端缺少这些前端接入必需的部分：

- 没有 `FastAPI` / `Flask` / `Starlette` 等 Web 框架
- 没有 HTTP 路由
- 没有请求/响应 DTO 层
- 没有把后端内部模型转换成前端模型的 adapter 层
- 没有前端所需的 analytics 聚合接口
- 没有 activity feed（最近动态）接口
- 没有日志查询接口
- 没有 Agent 列表接口

### 3. 一个很关键的事实

后端现在更像：

**“可运行的 AI pipeline engine”**

而前端需要的是：

**“一个面向页面消费的 REST API 服务”**

中间还差一层完整的“应用服务 / API 输出层”。

---

## 二、前端当前真实依赖的接口

前端当前通过 [frontend/src/app/lib/api/services.ts](../frontend/src/app/lib/api/services.ts) 依赖这些接口：

- `GET /pipelines`
- `POST /pipelines`
- `GET /pipelines/:id`
- `GET /pipelines/:id/logs`
- `GET /agents`
- `GET /checkpoints`
- `POST /checkpoints/:id/approve`
- `POST /checkpoints/:id/reject`
- `GET /analytics`
- `GET /activities/recent`

如果后端想先最小可用落地，至少要先做这 10 个。

---

## 三、前后端当前最重要的不匹配

这一块是联调时最容易出问题的地方。

### 1. Pipeline 状态枚举不一致

前端期望：

- `pending`
- `running`
- `paused`
- `completed`
- `failed`

定义位置：  
[frontend/src/app/types/pipeline.ts](../frontend/src/app/types/pipeline.ts)

后端当前内部状态：

- `pending`
- `running`
- `waiting_human`
- `completed`
- `failed`
- `cancelled`

定义位置：  
[backend/src/models/pipeline.py](./src/models/pipeline.py)

这意味着后端不能直接把内部 `Pipeline` 原样吐给前端，必须做映射：

- `waiting_human` -> 前端建议映射成 `paused`
- `cancelled` -> 前端目前没有这个值，短期建议映射成 `failed` 或扩展前端枚举

### 2. Stage 状态枚举不一致

前端 stage 期望：

- `idle`
- `running`
- `completed`
- `failed`
- `awaiting_review`
- `rejected`

后端 stage 当前：

- `pending`
- `running`
- `waiting_human`
- `approved`
- `rejected`
- `completed`
- `failed`

建议映射：

- `pending` -> `idle`
- `waiting_human` -> `awaiting_review`
- `approved` -> `completed` 或继续保留为中间态但输出给前端时转为 `completed`

### 3. Pipeline 字段结构不一致

前端 `Pipeline` 需要：

- `name`
- `description`
- `status`
- `progress`
- `currentStage`
- `template`
- `stages`
- `createdAt`
- `updatedAt`

后端当前 `Pipeline` 只有：

- `id`
- `title`
- `status`
- `stages`
- `context`
- `created_at`
- `updated_at`
- `error`

也就是说，后端至少要补或推导这些字段：

- `name` <- 可由 `title` 映射
- `description` <- 当前可用 `context.requirement_raw`
- `progress` <- 需要根据阶段状态计算
- `currentStage` <- 需要根据当前阶段计算
- `template` <- 当前后端没有，需要在创建流水线时存进去

### 4. Checkpoint 模型当前不存在成品 DTO

前端需要：

- `id`
- `pipelineId`
- `pipelineName`
- `stage`
- `stageIndex`
- `status`
- `createdAt`
- `output`
- `rejectReason?`

后端当前没有独立 `Checkpoint` 模型，需要从：

- `Pipeline`
- `StageNode`
- `human_feedback`
- `human_approval`
- `agent_output`

动态组装出来。

### 5. Analytics / Activities 后端还没有数据源

前端分析页和 Dashboard 都依赖聚合数据，但后端目前没有：

- 运行次数聚合
- token 使用统计
- 阶段耗时统计
- Agent 成功率统计
- 最近动态事件流

这一部分短期建议先用：

- `StateStore` 中的历史 pipeline 文件做离线聚合
- 没有的数据先返回可推导值或空数组

---

## 四、后端当前最该做的事情

下面按优先级给出建议。

### P0：先让前端能连上真实后端

这是第一阶段最重要的目标。

#### 1. 增加 Web API 框架

建议直接用 FastAPI。

原因：

- 与当前 Python 技术栈匹配
- 类型和 Pydantic 兼容
- 很适合做 DTO 和接口文档
- 后续如果要加 SSE / WebSocket 也顺手

建议新增：

- `backend/src/api/app.py`
- `backend/src/api/routes/`
- `backend/src/api/schemas/`
- `backend/src/api/mappers/`

同时 `requirements.txt` 需要补：

- `fastapi`
- `uvicorn`

#### 2. 提供一个统一的 Engine 初始化入口

当前 `DevFlowEngine` 可以工作，但没有一个“API 启动时统一注册 Agent”的地方。

建议新增：

- `backend/src/bootstrap.py`

职责：

- 初始化 `DevFlowEngine`
- 注册 6 个 Agent
- 注入 `StateStore`
- 提供全局单例或依赖注入入口

#### 3. 做 DTO / Mapper 层

这一步必须做，不建议让 API 直接返回内部 `Pipeline`。

建议拆出：

- `backend/src/api/schemas/pipeline.py`
- `backend/src/api/schemas/checkpoint.py`
- `backend/src/api/schemas/agent.py`
- `backend/src/api/schemas/analytics.py`
- `backend/src/api/mappers/pipeline_mapper.py`

Mapper 的职责：

- 把内部 `Pipeline` -> 前端 `Pipeline DTO`
- 把内部 `StageNode` -> 前端 `PipelineStage DTO`
- 把内部审批阶段 -> 前端 `Checkpoint DTO`

### P1：补齐前端主流程接口

#### 4. 实现流水线接口

需要实现：

- `GET /pipelines`
- `POST /pipelines`
- `GET /pipelines/{id}`
- `GET /pipelines/{id}/logs`

其中：

##### `POST /pipelines`

前端请求体是：

```json
{
  "template": "feature",
  "requirement": "..."
}
```

当前后端 `create_pipeline()` 只接收：

- `requirement`
- `title`

所以后端需要：

- 接收 `template`
- 存储 `template`
- 可能还要根据模板决定 stage 策略

短期最小方案：

- 先把 `template` 作为 metadata 存进 pipeline
- 当前不改变引擎执行流程

##### `GET /pipelines/{id}/logs`

这是后端目前完全没有的能力。

建议短期做法：

- 在 Engine 执行时追加结构化日志
- 每个 pipeline 单独存一个日志列表

建议新增：

- `backend/src/store/log_store.py`

或者直接在 `StateStore` 旁边维护：

- `flow_state/{pipeline_id}.log.json`

### P1：实现审批能力

#### 5. 实现检查点列表接口

需要实现：

- `GET /checkpoints`

这个接口本质上不是独立实体表，而是：

**从所有 pipeline 的 stages 中筛出等待人工确认的阶段**

建议规则：

- `StageStatus.WAITING_HUMAN` -> `pending`
- `StageStatus.REJECTED` -> `rejected`
- `human_approval == APPROVE` 或阶段已通过 -> `approved`

#### 6. 实现审批动作接口

需要实现：

- `POST /checkpoints/{id}/approve`
- `POST /checkpoints/{id}/reject`

这两个接口内部最终应该调用：

- `DevFlowEngine.approve_stage(...)`

注意一个设计点：

前端的 checkpoint id 目前是扁平字符串，但后端审批真正需要的是：

- `pipeline_id`
- `stage_index`

所以后端需要决定 checkpoint id 方案，建议：

```txt
cp:{pipeline_id}:{stage_index}
```

这样可以从 URL 里的 checkpoint id 解析出实际定位信息。

### P2：补齐展示型接口

#### 7. 实现 `GET /agents`

这个接口后端现在也没有现成模型，但很好补。

建议先返回静态配置 + 运行统计组合：

- Agent name
- role
- model
- provider
- status
- tasksCompleted
- avgDuration
- avgTokens
- color

短期可以：

- 大部分字段先静态配置
- `status` 由当前正在运行的 pipeline 推导
- 统计字段先从历史 pipeline 近似计算

#### 8. 实现 `GET /activities/recent`

这个接口后端当前没有事件流。

建议短期方案：

- 从 pipeline 创建、阶段完成、等待审批、审批通过、审批拒绝、运行失败这些动作中写事件
- 单独维护一个 event store

建议新增：

- `backend/src/store/event_store.py`

事件字段建议至少有：

- `time`
- `text`
- `type`
- `pipeline_id`
- `stage_type`

#### 9. 实现 `GET /analytics`

这个接口当前完全是前端聚合视图，需要后端加工。

建议短期先做一个聚合服务：

- 从 `StateStore.list_pipelines()` 读取所有历史 pipeline
- 统计：
  - 每日运行量
  - 成功 / 失败数
  - 各阶段平均耗时
  - Agent 成功率

其中下面这几个字段当前不容易准确拿到：

- `totalTokens`
- `mergedChanges`

建议短期策略：

- `totalTokens`：从 stage `agent_output` 或 LLM usage 补采集后再真实统计
- `mergedChanges`：当前后端没有 Git/PR 集成，先返回 `0`

---

## 五、后端代码里现在最值得立刻修的结构问题

### 1. `Pipeline.stages` 和 `Pipeline.context` 使用了可变默认值

位置：  
[backend/src/models/pipeline.py](./src/models/pipeline.py)

当前写法：

- `stages: List[StageNode] = []`
- `context: PipelineContext = PipelineContext()`

这类默认可变对象容易埋共享状态风险。

建议改成 `default_factory`。

### 2. 目前没有“后台执行任务”的调度方式

当前 `create_pipeline()` 只是创建，不会自动启动；
`run_pipeline()` 是 async，需要外部自己触发。

对于 HTTP API 来说，`POST /pipelines` 一般不适合阻塞整个执行流程。

建议：

- 创建成功后立刻返回
- 用后台任务启动 `run_pipeline()`

如果用 FastAPI，可以先用：

- `asyncio.create_task(...)`

后续再升级为正式任务队列。

### 3. `approve_stage()` 现在直接继续执行流水线

这个逻辑本身没问题，但如果从 HTTP 层触发，要考虑：

- 超时
- 并发重复审批
- 流水线已完成或状态不合法时的幂等性

建议补：

- 阶段状态校验
- 幂等处理
- 审批前锁定 pipeline

### 4. 缺少日志采集

前端已经展示日志面板，但后端完全没有正式日志模型。

建议不要把日志临时拼接在前端。
应该在后端执行阶段时就记录：

- pipeline 启动
- stage 开始
- stage 完成
- stage 等待审批
- stage 审批通过 / 拒绝
- 异常失败

---

## 六、建议的最小落地目录结构

建议先演进成这样：

```txt
backend/
  src/
    api/
      app.py
      routes/
        pipelines.py
        checkpoints.py
        agents.py
        analytics.py
        activities.py
      schemas/
        pipeline.py
        checkpoint.py
        agent.py
        analytics.py
      mappers/
        pipeline_mapper.py
    services/
      pipeline_service.py
      analytics_service.py
      activity_service.py
    store/
      state_store.py
      log_store.py
      event_store.py
    bootstrap.py
    engine.py
```

这会比把 HTTP 路由直接塞进 `engine.py` 清晰很多。

---

## 七、建议的开发顺序

建议按下面顺序做，最稳：

### 阶段 1：打通最小主链路

1. 引入 FastAPI / uvicorn
2. 新建 app 启动入口
3. 初始化 engine + 注册 agents
4. 实现 `GET /pipelines`
5. 实现 `GET /pipelines/{id}`
6. 实现 `POST /pipelines`

### 阶段 2：补审批链路

7. 实现 checkpoint DTO 和 mapper
8. 实现 `GET /checkpoints`
9. 实现 `POST /checkpoints/{id}/approve`
10. 实现 `POST /checkpoints/{id}/reject`

### 阶段 3：补体验接口

11. 实现 `GET /pipelines/{id}/logs`
12. 实现 `GET /agents`
13. 实现 `GET /activities/recent`
14. 实现 `GET /analytics`

### 阶段 4：再做增强

15. 加 CORS
16. 加后台任务 / 异步调度
17. 加真正的 DB 持久化
18. 加事件流 / WebSocket / SSE

---

## 八、如果只问一句话：后端现在最该做什么

答案是：

**先把现有 Python engine 包一层 FastAPI，并做一层前后端 DTO 映射。**

不是先优化 Agent，也不是先做更复杂的生成逻辑，而是先把：

- 创建流水线
- 查询流水线
- 查询审批
- 审批通过 / 拒绝

这些前端主链路真正打通。

---

## 九、一个现实判断

从当前代码看，后端已经具备“内核”，但还没有“产品接口层”。

所以后端当前的工作重点应该从：

**AI 生成能力**

切到：

**API 产品化、状态建模、前端契约对齐**

这是现在最影响联调效率、也最值得优先解决的部分。

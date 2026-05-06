好的，我来帮你更新 `backend/README.md`，补充架构说明、环境变量配置、开发模式说明等内容。

---

文件路径：`backend/README.md`

```markdown
# FlowState - Backend

FlowState 的 FastAPI 后端服务，提供流水线编排、Agent 执行引擎及前端 UI API。

## 架构概览

当前后端处于 **UI 接口真实 + 流水线执行可选** 的状态：

- **UI 接口已是后端真实 API**：`/api/pipelines`、`/api/agents`、`/api/checkpoints`、`/api/analytics`、`/api/activities` 均由后端提供，不再依赖前端 mock。
- **`/api/dev/seed`**：演示数据入口。主动调用可在本地生成示例流水线，方便前端开发和调试。
- **流水线执行是否真实**取决于 LLM 配置：
  - 若配置了 `FS_LLM_*` 并创建/审批流程，后端会真实调用 LLM 执行各阶段（需求分析→方案→代码→测试→评审→交付）。
  - 若未配置 LLM 或未触发执行，则仅存储与状态变更。

## 环境变量配置

使用前需配置环境变量（参考 `env.ps1`），至少需要设置 LLM 配置才能执行真实流水线：

```bash
# LLM 配置（必须，用于真实流水线执行）
export FS_LLM_PROVIDER=deepseek
export FS_LLM_API_KEY=your_api_key_here
export FS_OUTPUT_MODE=auto
export FS_LLM_MODEL=deepseek-chat
export FS_LLM_BASE_URL=https://api.deepseek.com/
```

### 在 Windows PowerShell 中

```powershell
.\env.ps1
```

该脚本会设置上述所有后端环境变量，以及前端开发所需的环境变量。

## 开发模式说明

### 两种运行模式

|       模式       | 条件                                 | 行为                                               |
| :--------------: | :----------------------------------- | :------------------------------------------------- |
|   **演示模式**   | 调用 `POST /api/dev/seed?reset=true` | 生成静态示例数据，UI 可展示完整界面，无需 LLM 配置 |
| **真实执行模式** | 配置 `FS_LLM_*` + 创建/审批流程      | 后端真实调用 LLM 执行各阶段                        |

### 快速开始（演示模式）

```bash
# 1. 启动后端
c:/python314/python.exe -m uvicorn src.api.app:app --reload --port 8000

# 2. 生成演示数据（在另一个终端）
curl -X POST "http://localhost:8000/api/dev/seed?reset=true"

# 3. 验证
curl http://localhost:8000/api/pipelines
```

### 前端配合

前端需要设置以下环境变量才能连接后端真实 API：

```bash
export VITE_API_BASE_URL=http://localhost:8000
export VITE_DISABLE_MOCK_FALLBACK=true
export VITE_USE_MOCK_API=false
```

若未设置 `VITE_API_BASE_URL`，前端将默认走内置 mock 数据。

## API 路由

### 版本化 API（`/api/v1/*`）

用于真实流水线引擎操作：

| 端点                         | 方法  | 用途           |
| :--------------------------- | :---: | :------------- |
| `/api/v1/pipelines`          | POST  | 创建新流水线   |
| `/api/v1/pipelines/{id}`     |  GET  | 获取流水线详情 |
| `/api/v1/pipelines/{id}/run` | POST  | 启动流水线执行 |

### UI API（`/api/*`）

用于前端界面展示，由独立路由器提供服务：

#### Pipelines (UI)

| 端点                         | 方法  | 路由器文件                           |
| :--------------------------- | :---: | :----------------------------------- |
| `/api/dev/seed`              | POST  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines`             |  GET  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines`             | POST  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}`        |  GET  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}/logs`   |  GET  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}/pause`  | POST  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}/resume` | POST  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}/cancel` | POST  | `routers/pipelines.py` (`ui_router`) |
| `/api/pipelines/{id}/retry`  | POST  | `routers/pipelines.py` (`ui_router`) |

#### Agents

| 端点          | 方法  | 路由器文件          |
| :------------ | :---: | :------------------ |
| `/api/agents` |  GET  | `routers/agents.py` |

#### Checkpoints

| 端点                            | 方法  | 路由器文件               |
| :------------------------------ | :---: | :----------------------- |
| `/api/checkpoints`              |  GET  | `routers/checkpoints.py` |
| `/api/checkpoints/{id}/approve` | POST  | `routers/checkpoints.py` |
| `/api/checkpoints/{id}/reject`  | POST  | `routers/checkpoints.py` |

#### Analytics

| 端点             | 方法  | 路由器文件             |
| :--------------- | :---: | :--------------------- |
| `/api/analytics` |  GET  | `routers/analytics.py` |

#### Activities

| 端点                     | 方法  | 路由器文件              |
| :----------------------- | :---: | :---------------------- |
| `/api/activities/recent` |  GET  | `routers/activities.py` |

## 路由器文件结构

```
src/api/routers/
├── __init__.py
├── app.py                # FastAPI 应用创建，注册所有路由器
├── ui_shared.py          # 共享工具函数（种子数据生成、格式化等）
├── pipelines.py          # Pipeline 操作（v1 + UI）
├── agents.py             # Agent 状态/统计
├── checkpoints.py        # 检查点审批/拒绝
├── analytics.py          # 分析汇总
├── activities.py         # 最近活动
├── health.py             # 健康检查
├── settings.py           # 系统设置
└── frontend_mock.py      # 开发回退（精简）
```

## 测试

```bash
# 运行所有测试
pytest backend/tests/

# 运行特定测试文件
pytest backend/tests/test_api_app.py -v

# 运行 UI API 冒烟测试（验证所有关键端点）
pytest backend/tests/test_api_app.py::test_ui_api_routes_smoke -v
```
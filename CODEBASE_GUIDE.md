# FlowState 代码讲解

这份文档的目标不是穷举所有文件，而是帮你先建立一张“项目地图”。
如果你是第一次接手这个仓库，建议按下面的顺序读：

1. `package.json`
2. `src/main.tsx`
3. `src/app/App.tsx`
4. `src/app/routes.tsx`
5. `src/app/components/layout/*`
6. `src/app/data/mockData.ts`
7. 具体页面文件

## 1. 这是个什么项目

这个项目本质上是一个：

- 前端渲染层：`React + Vite + TypeScript`
- 桌面壳：`Electron`
- UI 风格：深色面板 + 仪表盘风格 + 少量动效

可以把它理解成：

- Vite 负责把 React 页面跑起来和打包
- Electron 负责把页面装进桌面窗口
- 页面里的数据目前主要来自本地 mock 数据，还没有接真实后端

## 2. 运行链路怎么走

先看 `package.json` 里的几个关键脚本：

- `npm run dev`
  作用：启动 Vite，并同时监听 Electron 相关 TypeScript 编译
- `npm run dev:desktop`
  作用：在 `dev` 的基础上，等前端和 Electron 主进程准备好后，直接拉起桌面应用
- `npm run build`
  作用：同时构建前端产物和 Electron 产物

这几个脚本说明项目分成两部分：

- 渲染进程：`src/` 里的 React 页面
- 主进程：`electron/` 里的 Electron 代码

## 3. 目录结构怎么理解

### `src/`

前端主目录，桌面窗口里真正显示的内容都在这里。

- `src/main.tsx`
  React 挂载入口，把 `App` 渲染到 `#root`
- `src/app/App.tsx`
  很薄的一层，只负责把路由提供给整个应用
- `src/app/routes.tsx`
  路由总表，是理解页面结构的第一站
- `src/app/components/`
  公共组件目录
- `src/app/pages/`
  各个页面
- `src/app/data/mockData.ts`
  当前页面展示所依赖的示例数据和类型定义
- `src/styles/`
  全局样式入口、字体、主题和 Tailwind 相关配置

### `electron/`

Electron 主进程和预加载脚本。

- `electron/main.ts`
  负责创建桌面窗口，并决定开发环境加载本地服务还是生产环境加载打包后的 `dist/index.html`
- `electron/preload.ts`
  负责通过 `contextBridge` 暴露一个安全的浏览器侧 API

### `build-electron/`

这是 Electron TypeScript 编译后的产物目录，不是源码。
它通常应该被忽略提交，源码还是看 `electron/`。

## 4. React 入口是怎么串起来的

### 第一步：`src/main.tsx`

这里做了两件事：

- 引入全局样式 `src/styles/index.css`
- 用 `ReactDOM.createRoot(...).render(...)` 挂载 `App`

所以你可以把它当成“前端启动按钮”。

### 第二步：`src/app/App.tsx`

`App` 本身几乎没有业务逻辑，只返回一个 `RouterProvider`。

这意味着：

- 真正控制界面结构的不是 `App`
- 而是路由配置 `src/app/routes.tsx`

### 第三步：`src/app/routes.tsx`

这里使用的是 `createHashRouter`，而不是 `BrowserRouter`。

这个选择对 Electron 很常见，因为：

- Hash 路由不依赖服务端路由回退
- 打包成桌面应用后更稳定
- 像 `#/pipelines` 这种路径更容易直接在本地文件环境下工作

当前路由层级可以理解成：

- `/` -> 外层布局 `Layout`
- `index` -> `Dashboard`
- `/pipelines` -> 流水线列表
- `/pipelines/:id` -> 流水线详情
- `/checkpoints` -> 审批检查点
- `/agents` -> Agent 管理
- `/analytics` -> 可观测性
- `/settings` -> 设置

也就是说，`Layout` 是页面骨架，`children` 才是中间切换的内容区。

## 5. Layout 和 Sidebar 是骨架

### `src/app/components/layout/Layout.tsx`

这个组件定义了整个应用最外层结构：

- 左边是 `Sidebar`
- 右边是 `main`
- `main` 里面通过 `Outlet` 渲染当前子页面

它还顺手做了几件视觉层面的事：

- 固定整屏高度 `h-screen`
- 禁止整体溢出
- 统一暗色背景
- 叠了一层很轻的径向渐变

所以如果你想改“整个应用的底色、整体布局、左右结构”，优先看这个文件。

### `src/app/components/layout/Sidebar.tsx`

这个组件负责左侧导航。

它的核心思路很简单：

- `navItems` 和 `bottomItems` 这两个数组定义了菜单内容
- `useLocation()` 判断当前路由
- `NavLink` 负责点击跳转
- `motion.div` 负责 hover、点击和激活态动效

这意味着以后你要新增页面时，通常要同时改两处：

1. `src/app/routes.tsx` 新增路由
2. `src/app/components/layout/Sidebar.tsx` 新增菜单项

## 6. 数据层现在是什么状态

### `src/app/data/mockData.ts`

这是目前最值得认真看的业务文件之一，因为它既提供了示例数据，也在暗示产品模型。

里面主要有三层内容：

- 类型定义
  比如 `StageStatus`、`PipelineStage`、`Pipeline`
- 模板数据
  比如 `PIPELINE_STAGES_TEMPLATE`
- 页面直接消费的 mock 数据
  比如 `mockPipelines`、`mockAgents`

从这里可以看出，这个产品当前在建模一条 AI 驱动研发流水线：

- 一条 `Pipeline` 表示一次任务流程
- 一个 `Pipeline` 包含多个 `PipelineStage`
- 每个阶段会关联一个 Agent
- 阶段有运行状态、token 消耗、产出文本、是否是 checkpoint 等信息

如果你后面要接真实接口，这个文件会很像“前端数据契约草稿”。
通常替换顺序会是：

1. 保留类型定义
2. 把 mock 数据替换成 API 请求结果
3. 把页面里直接引用 `mockPipelines` 的地方换成状态管理或数据请求逻辑

## 7. 页面是怎么组织的

### `src/app/pages/Dashboard.tsx`

这是一个典型页面，适合当样板来读。

它展示了这个项目常见的页面写法：

- 页面内部自己定义小块静态数据，例如 `stats`、`recentActivity`
- 从 `mockData.ts` 读取业务数据，例如 `mockPipelines`
- 用 `useNavigate()` 实现点击跳转
- 用 `motion` 做卡片和列表动效
- 用内联 `style` 和 Tailwind 类名混合控制界面

如果你想快速掌握这个仓库的编码风格，先把这个页面读明白会很有帮助。

### 其它页面

你可以把其余页面理解成围绕同一套领域模型的不同视图：

- `Pipelines.tsx`
  流水线列表页
- `PipelineDetail.tsx`
  单条流水线详情页，通常是业务最重的页面之一
- `CheckpointReview.tsx`
  审批/检查点处理页
- `Agents.tsx`
  Agent 列表或状态概览
- `Analytics.tsx`
  统计与可观测性视图
- `Settings.tsx`
  配置页

建议你的阅读顺序是：

1. `Dashboard.tsx`
2. `Pipelines.tsx`
3. `PipelineDetail.tsx`
4. 其它页面

因为前两个文件更容易建立整体认知，`PipelineDetail.tsx` 往往会包含更完整的交互和状态表达。

## 8. 组件层怎么读

### 业务组件和通用组件是分开的

- `src/app/components/layout/`
  放骨架类组件
- `src/app/components/ui/`
  放通用 UI 组件
- `src/app/components/figma/`
  看名字像是从设计稿或生成流程里带来的特殊组件

例如 `src/app/components/ui/StatusBadge.tsx` 是个很典型的通用展示组件：

- 输入：`status`
- 输出：不同颜色、文案、圆点和边框样式

它的价值在于把状态显示规则集中起来，避免每个页面重复写一遍“运行中是蓝色，失败是红色”。

如果以后状态体系变了，优先改这种集中封装的组件，收益最大。

## 9. 样式层怎么理解

### `src/styles/index.css`

这是全局样式入口，主要做三件事：

- 引入字体
- 引入 Tailwind 相关样式
- 引入主题样式

同时它定义了一些全局行为：

- `html, body, #root` 占满全屏
- 默认字体是 `Inter`
- 全局 `box-sizing: border-box`
- 滚动条做了较细的暗色样式

从现有代码看，这个项目的样式方式是“混合式”：

- 用 Tailwind 类名做布局和通用排版
- 用内联 `style` 写精确颜色、阴影、渐变、边框

所以后面改 UI 时，通常要同时看两种东西：

- JSX 上的 className
- JSX 上的 style 对象

## 10. Electron 这一层在干什么

### `electron/main.ts`

它是桌面应用的主入口。

关键逻辑：

- `app.whenReady()` 后创建窗口
- 开发环境下加载本地 Vite 地址
- 生产环境下加载 `dist/index.html`
- 窗口关闭后在非 macOS 环境退出应用

这里最重要的理解是：

- React 页面仍然是网页技术渲染
- Electron 只是把它装进桌面应用窗口

### `electron/preload.ts`

这里通过 `contextBridge.exposeInMainWorld('api', ...)` 暴露了一个很简单的 `ping` API。

这通常意味着项目未来准备把“Node / 系统能力”通过 preload 安全地下发给前端。
现在它还很轻，但这会是后续扩展桌面能力的入口，例如：

- 文件读写
- 系统通知
- 打开本地目录
- 与主进程通信

## 11. 你以后最常改哪些地方

如果你要新增一个页面，通常会改：

1. `src/app/pages/` 新建页面组件
2. `src/app/routes.tsx` 注册路由
3. `src/app/components/layout/Sidebar.tsx` 补导航入口

如果你要改整站布局或壳层样式，通常会改：

1. `src/app/components/layout/Layout.tsx`
2. `src/app/components/layout/Sidebar.tsx`
3. `src/styles/index.css`

如果你要接后端接口，通常会先从这些地方下手：

1. `src/app/data/mockData.ts`
2. 当前直接消费 mock 数据的页面
3. 逐步抽出 API 请求层和状态管理层

如果你要改桌面行为，通常会改：

1. `electron/main.ts`
2. `electron/preload.ts`

## 12. 这个项目现在的阶段判断

从代码状态来看，它更像是一个：

- 已经有明确产品方向的前端原型
- UI 完成度不低
- 业务模型已经有雏形
- 但数据层和桌面能力还比较早期

最明显的特征有：

- 页面结构已经比较完整
- mock 数据相对丰富
- Electron preload 还很轻
- 缺少真实接口接入痕迹
- README 还几乎没写

所以你现在理解项目的最佳方式不是从“后端接口”切入，而是：

1. 先理解页面和领域模型
2. 再理解路由和布局
3. 最后再考虑如何把 mock 数据替换成真实数据

## 13. 推荐你的下一步阅读顺序

如果你只想快速上手，建议按这个顺序继续看：

1. `src/app/routes.tsx`
2. `src/app/components/layout/Layout.tsx`
3. `src/app/components/layout/Sidebar.tsx`
4. `src/app/data/mockData.ts`
5. `src/app/pages/Dashboard.tsx`
6. `src/app/pages/Pipelines.tsx`
7. `src/app/pages/PipelineDetail.tsx`

如果你是准备开始改功能，建议先回答这 3 个问题：

1. 这次改动是页面视觉层，还是业务数据层？
2. 改动发生在渲染层 `src/`，还是桌面壳 `electron/`？
3. 现在这个页面吃的是 mock 数据，还是真实数据？

把这 3 个问题搞清楚，动手时会稳很多。

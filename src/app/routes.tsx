import { createHashRouter } from "react-router";
import { Layout } from "./components/layout/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Pipelines } from "./pages/Pipelines";
import { PipelineDetail } from "./pages/PipelineDetail";
import { CheckpointReview } from "./pages/CheckpointReview";
import { Agents } from "./pages/Agents";
import { Analytics } from "./pages/Analytics";
import { Settings } from "./pages/Settings";

export const router = createHashRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "pipelines", Component: Pipelines },
      { path: "pipelines/:id", Component: PipelineDetail },
      { path: "checkpoints", Component: CheckpointReview },
      { path: "agents", Component: Agents },
      { path: "analytics", Component: Analytics },
      { path: "settings", Component: Settings },
    ],
  },
]);

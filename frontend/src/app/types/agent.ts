export interface Agent {
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

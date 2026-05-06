import { Navigate } from "react-router";

export function Agents() {
  return <Navigate to="/settings?tab=agents" replace />;
}

import { Outlet } from "react-router";
import { Sidebar } from "./Sidebar";
import { Toaster } from "../ui/sonner";

export function Layout() {
  return (
    <div
      className="w-full h-screen flex overflow-hidden"
      style={{
        background: "#0d0d11",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Subtle background gradient */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(91,114,255,0.08) 0%, transparent 70%)",
        }}
      />

      <Sidebar />

      <main className="flex-1 h-full overflow-hidden relative flex flex-col">
        <Outlet />
      </main>

      <Toaster />
    </div>
  );
}

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// The frontend talks to the FastAPI backend. In dev we proxy /api and /health
// to localhost:8000 so the app works with no CORS friction. Override the
// target with VITE_API_TARGET if your backend runs elsewhere.
export default defineConfig(({ mode }) => {
  // loadEnv includes VITE_API_TARGET from either the shell or .env files.
  // This makes isolated staging runs possible without editing source code.
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.VITE_API_TARGET || "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": { target, changeOrigin: true },
        "/health": { target, changeOrigin: true },
      },
    },
  };
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The frontend talks to the FastAPI backend. In dev we proxy /api and /health
// to localhost:8000 so the app works with no CORS friction. Override the
// target with VITE_API_TARGET if your backend runs elsewhere.
const target = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target, changeOrigin: true },
      "/health": { target, changeOrigin: true },
    },
  },
});

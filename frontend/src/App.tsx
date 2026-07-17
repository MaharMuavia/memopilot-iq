import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        {/* Landing page is the entry point. */}
        <Route path="/" element={<LandingPage />} />
        {/* The MemoryAgent dashboard. */}
        <Route path="/app" element={<DashboardPage />} />
        {/* Convenience alias. */}
        <Route path="/demo" element={<Navigate to="/app" replace />} />
        {/* Anything else falls back to the landing page. */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

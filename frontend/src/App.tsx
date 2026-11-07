import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import ComparePage from "./pages/ComparePage";
import DemoHomePage from "./pages/DemoHomePage";
import DataHealthPage from "./pages/DataHealthPage";
import LoginPage from "./pages/LoginPage";
import RankingPage from "./pages/RankingPage";
import HelpPage from "./pages/HelpPage";
import RiskMonitorPage from "./pages/RiskMonitorPage";
import SettingsPage from "./pages/SettingsPage";
import ScreenerPage from "./pages/ScreenerPage";
import TraderDetailPage from "./pages/TraderDetailPage";

const TechnicalDocsPage = lazy(() => import("./pages/TechnicalDocsPage"));

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<DemoHomePage />} />
        <Route path="/data-health" element={<DataHealthPage />} />
        <Route path="/screener" element={<ScreenerPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/risk" element={<RiskMonitorPage />} />
        <Route path="/ranking" element={<RankingPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route
          path="/technical"
          element={
            <Suspense
              fallback={<div className="h-64 animate-pulse rounded-2xl bg-panel" />}
            >
              <TechnicalDocsPage />
            </Suspense>
          }
        />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/traders/:id" element={<TraderDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import ComparePage from "./pages/ComparePage";
import DemoHomePage from "./pages/DemoHomePage";
import DataHealthPage from "./pages/DataHealthPage";
import LoginPage from "./pages/LoginPage";
import ScreenerPage from "./pages/ScreenerPage";
import TraderDetailPage from "./pages/TraderDetailPage";

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
        <Route path="/traders/:id" element={<TraderDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

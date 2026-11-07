import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import DemoHomePage from "./pages/DemoHomePage";
import DataHealthPage from "./pages/DataHealthPage";
import LoginPage from "./pages/LoginPage";
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
        <Route path="/traders/:id" element={<TraderDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

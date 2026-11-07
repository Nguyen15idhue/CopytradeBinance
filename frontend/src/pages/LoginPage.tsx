import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { login } from "../lib/api";
import { getAccessToken, saveSession } from "../lib/auth";
import ThemeToggle from "../components/ThemeToggle";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Admin123!ChangeMe");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (getAccessToken()) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await login(email, password);
      saveSession(result.access_token, result.refresh_token, result.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-app px-4 text-strong">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm rounded-2xl border border-line bg-panel p-6 shadow-xl"
      >
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">
          CopytradeBinance
        </p>
        <h1 className="mt-2 text-2xl font-semibold">Đăng nhập</h1>
        <p className="mt-1 text-sm text-muted">Screener &amp; Risk Analytics</p>

        <label className="mt-6 block text-sm text-body">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong outline-none focus:border-emerald-500"
            autoComplete="username"
            required
          />
        </label>

        <label className="mt-4 block text-sm text-body">
          Mật khẩu
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong outline-none focus:border-emerald-500"
            autoComplete="current-password"
            required
          />
        </label>

        {error ? (
          <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-lg bg-emerald-500 px-4 py-2 font-medium text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          {loading ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>

        <p className="mt-4 text-xs text-faint">
          Tài khoản demo: <code>admin@example.com</code> / <code>Admin123!ChangeMe</code>
        </p>
      </form>
    </div>
  );
}

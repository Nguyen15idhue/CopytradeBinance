const ACCESS_KEY = "ct_access_token";
const REFRESH_KEY = "ct_refresh_token";
const USER_KEY = "ct_user";
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

let refreshPromise: Promise<boolean> | null = null;

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser(): { email: string; role: string } | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as { email: string; role: string };
  } catch {
    return null;
  }
}

export function saveSession(accessToken: string, refreshToken: string, user: unknown): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Làm mới access token bằng refresh token (7 ngày). Single-flight: nhiều request
 * 401 cùng lúc chỉ gọi /auth/refresh một lần.
 */
export async function refreshSession(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return false;
      const body = (await response.json()) as {
        data?: { access_token?: string; refresh_token?: string };
      };
      const access = body.data?.access_token;
      const nextRefresh = body.data?.refresh_token;
      if (!access || !nextRefresh) return false;
      setTokens(access, nextRefresh);
      return true;
    } catch {
      return false;
    }
  })();
  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

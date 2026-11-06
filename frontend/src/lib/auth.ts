const ACCESS_KEY = "ct_access_token";
const REFRESH_KEY = "ct_refresh_token";
const USER_KEY = "ct_user";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
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

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

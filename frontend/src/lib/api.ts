import { clearSession, getAccessToken } from "./auth";
import type {
  CollectorStatus,
  CompareResponse,
  FunnelSummary,
  LoginResult,
  Paged,
  PerformanceResponse,
  PositionRow,
  RiskEventsResponse,
  RiskResponse,
  RiskSummary,
  SavedView,
  ScoreResponse,
  ScreenerResponse,
  TraderDetail,
  TradeRow,
  TransferRow,
} from "../types/trader";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

interface ApiResponse<T> {
  data: T;
  meta: { request_id: string; generated_at: string };
  error: null;
}

interface ApiErrorBody {
  data: null;
  error: { code: string; message: string; details?: unknown };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = (await response.json().catch(() => null)) as
    | ApiResponse<T>
    | ApiErrorBody
    | null;

  if (!response.ok) {
    if (response.status === 401) clearSession();
    const errorBody = body as ApiErrorBody | null;
    throw new ApiError(
      response.status,
      errorBody?.error?.code ?? "REQUEST_FAILED",
      errorBody?.error?.message ?? "Yêu cầu thất bại",
    );
  }
  if (!body || !("data" in body)) {
    throw new ApiError(500, "INVALID_RESPONSE", "Phản hồi API không hợp lệ");
  }
  return (body as ApiResponse<T>).data;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  return request<LoginResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getTrader(id: string): Promise<TraderDetail> {
  return request<TraderDetail>(`/traders/${encodeURIComponent(id)}`);
}

export async function getCollectorStatus(): Promise<CollectorStatus> {
  return request<CollectorStatus>("/collector/status");
}

export function toQuery(filters: Record<string, unknown>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === null || value === undefined || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, String(item));
    } else {
      params.set(key, String(value));
    }
  }
  return params.toString();
}

export async function getScreener(filters: Record<string, unknown>): Promise<ScreenerResponse> {
  return request<ScreenerResponse>(`/traders?${toQuery(filters)}`);
}

export async function getFunnelSummary(): Promise<FunnelSummary> {
  return request<FunnelSummary>("/traders/funnel-summary");
}

export async function getSavedViews(): Promise<SavedView[]> {
  return request<SavedView[]>("/saved-views");
}

export async function saveView(name: string, filters: Record<string, unknown>): Promise<SavedView> {
  return request<SavedView>("/saved-views", {
    method: "POST",
    body: JSON.stringify({ name, filters }),
  });
}

export async function deleteView(id: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/saved-views/${id}`, { method: "DELETE" });
}

const id = (value: string) => encodeURIComponent(value);

export async function getPerformance(portfolioId: string): Promise<PerformanceResponse> {
  return request<PerformanceResponse>(`/traders/${id(portfolioId)}/performance`);
}

export async function getPositions(
  portfolioId: string,
  page = 1,
  pageSize = 50,
): Promise<Paged<PositionRow>> {
  return request<Paged<PositionRow>>(
    `/traders/${id(portfolioId)}/positions?page=${page}&page_size=${pageSize}`,
  );
}

export async function getTrades(
  portfolioId: string,
  page = 1,
  pageSize = 50,
): Promise<Paged<TradeRow>> {
  return request<Paged<TradeRow>>(
    `/traders/${id(portfolioId)}/trades?page=${page}&page_size=${pageSize}`,
  );
}

export async function getTransfers(portfolioId: string): Promise<Paged<TransferRow>> {
  return request<Paged<TransferRow>>(`/traders/${id(portfolioId)}/transfers?page_size=20`);
}

export async function getRisk(portfolioId: string): Promise<RiskResponse> {
  return request<RiskResponse>(`/traders/${id(portfolioId)}/risk`);
}

export async function getScore(portfolioId: string): Promise<ScoreResponse> {
  return request<ScoreResponse>(`/traders/${id(portfolioId)}/score`);
}

export async function getCompare(ids: string[]): Promise<CompareResponse> {
  return request<CompareResponse>(`/compare?ids=${ids.map(encodeURIComponent).join(",")}`);
}

export async function getRiskSummary(): Promise<RiskSummary> {
  return request<RiskSummary>("/risk/summary");
}

export async function getRiskEvents(params: Record<string, unknown>): Promise<RiskEventsResponse> {
  return request<RiskEventsResponse>(`/risk/events?${toQuery(params)}`);
}

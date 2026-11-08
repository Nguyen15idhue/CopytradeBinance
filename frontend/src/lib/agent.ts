import { getAccessToken, refreshSession } from "./auth";
import type { AgentMessageItem, AgentSessionItem } from "../types/agent";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

const SESSION_KEY = "ct_agent_session_id";
const OPEN_KEY = "ct_agent_open";

export function getStoredAgentSession(): number | null {
  try {
    const id = Number(localStorage.getItem(SESSION_KEY));
    return Number.isFinite(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
}

export function storeAgentSession(id: number | null): void {
  try {
    if (id && id > 0) localStorage.setItem(SESSION_KEY, String(id));
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    // localStorage bị chặn: bỏ qua.
  }
}

export function getStoredAgentOpen(): boolean {
  try {
    return sessionStorage.getItem(OPEN_KEY) === "1";
  } catch {
    return false;
  }
}

export function storeAgentOpen(open: boolean): void {
  try {
    if (open) sessionStorage.setItem(OPEN_KEY, "1");
    else sessionStorage.removeItem(OPEN_KEY);
  } catch {
    // sessionStorage bị chặn: bỏ qua.
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = (await response.json().catch(() => null)) as {
    data?: T;
    error?: { code: string; message: string };
  } | null;
  if (!response.ok) {
    throw new Error(body?.error?.message ?? "Yêu cầu thất bại");
  }
  if (!body || !("data" in body)) throw new Error("Phản hồi API không hợp lệ");
  return (body as { data: T }).data;
}

export async function listAgentSessions(): Promise<{ items: AgentSessionItem[] }> {
  return request("/agent/sessions");
}

export async function getAgentSession(id: number): Promise<{
  session: AgentSessionItem;
  messages: AgentMessageItem[];
}> {
  return request(`/agent/sessions/${id}`);
}

export async function deleteAgentSession(id: number): Promise<{ deleted: number }> {
  return request(`/agent/sessions/${id}`, { method: "DELETE" });
}

export async function sendAgentFeedback(
  messageId: number,
  rating: number,
): Promise<unknown> {
  return request("/agent/feedback", {
    method: "POST",
    body: JSON.stringify({ message_id: messageId, rating }),
  });
}

export interface AgentStreamHandlers {
  onTrace: (tool: string, summary: string | undefined, ok: boolean | undefined) => void;
  onCitation: (items: { source_type: string; ref: string }[]) => void;
  onWarning: (message: string) => void;
  onDone: (answer: string, usage: unknown, messageId: number, sessionId: number) => void;
  onError: (message: string) => void;
}

export async function streamAgentChat(
  message: string,
  sessionId: number | null,
  handlers: AgentStreamHandlers,
  signal: AbortSignal,
): Promise<void> {
  const send = async (): Promise<Response> => {
    const token = getAccessToken();
    return fetch(`${API_BASE}/agent/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal,
    });
  };

  let response = await send();
  if (response.status === 401) {
    if (await refreshSession()) {
      response = await send();
    }
  }
  if (!response.ok || !response.body) {
    throw new Error("Không kết nối được trợ lý AI");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  const lines: string[] = [];

  function dispatch(event: string, raw: string) {
    let data: Record<string, unknown> = {};
    try {
      data = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return;
    }
    if (event === "tool_call") {
      handlers.onTrace(String(data.tool ?? ""), undefined, undefined);
    } else if (event === "tool_result") {
      handlers.onTrace(
        String(data.tool ?? ""),
        String(data.summary ?? ""),
        data.ok === true,
      );
    } else if (event === "citation") {
      const items = Array.isArray(data.items) ? data.items : [];
      handlers.onCitation(
        items as { source_type: string; ref: string }[],
      );
    } else if (event === "warning") {
      handlers.onWarning(String(data.message ?? ""));
    } else if (event === "done") {
      handlers.onDone(
        String(data.answer ?? ""),
        data.usage,
        Number(data.message_id ?? 0),
        Number(data.session_id ?? 0),
      );
    } else if (event === "error") {
      handlers.onError(String(data.message ?? "Trợ lý AI gặp lỗi"));
    }
  }

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      dispatchBlock(part);
    }
  }
  if (buffer.trim()) dispatchBlock(buffer);
  buffer = "";

  function dispatchBlock(part: string) {
    lines.length = 0;
    for (const line of part.split("\n")) {
      if (line.startsWith("event:")) currentEvent = line.slice(6).trim();
      else if (line.startsWith("data:")) lines.push(line.slice(5).trim());
    }
    if (currentEvent && lines.length > 0) dispatch(currentEvent, lines.join("\n"));
    currentEvent = "";
  }
}

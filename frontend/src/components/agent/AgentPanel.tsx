import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getStoredUser } from "../../lib/auth";
import CopyPlanCard from "./CopyPlanCard";
import Markdown from "./Markdown";
import {
  deleteAgentSession,
  getAgentSession,
  getStoredAgentSession,
  listAgentSessions,
  sendAgentFeedback,
  storeAgentSession,
  streamAgentChat,
} from "../../lib/agent";
import type {
  AgentCitation,
  AgentMessageItem,
  AgentSessionItem,
  AgentStatus,
  AgentTrace,
} from "../../types/agent";

const SUGGESTED = [
  "Top 10 trader an toàn, ít rủi ro, lợi nhuận tốt",
  "Dữ liệu collector có mới không?",
  "Hệ thống tính Sharpe và risk_score thế nào?",
];

function startOfDay(value: Date): Date {
  const copy = new Date(value);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function groupSessions(items: AgentSessionItem[]): Array<[string, AgentSessionItem[]]> {
  const today = startOfDay(new Date());
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const week = new Date(today);
  week.setDate(today.getDate() - 7);
  const buckets: Record<string, AgentSessionItem[]> = {
    "Hôm nay": [],
    "Hôm qua": [],
    "7 ngày qua": [],
    "Cũ hơn": [],
  };
  for (const item of items) {
    const raw = item.updated_at ?? item.created_at;
    if (!raw) {
      buckets["Cũ hơn"].push(item);
      continue;
    }
    const date = new Date(raw);
    if (date >= today) buckets["Hôm nay"].push(item);
    else if (date >= yesterday) buckets["Hôm qua"].push(item);
    else if (date >= week) buckets["7 ngày qua"].push(item);
    else buckets["Cũ hơn"].push(item);
  }
  return Object.entries(buckets).filter(([, list]) => list.length > 0);
}

interface ChatMessage extends AgentMessageItem {
  traces?: AgentTrace[];
  citations?: AgentCitation[];
  warnings?: string[];
  pending?: boolean;
  serverId?: number;
}

function FeedbackButtons({ messageId }: { messageId: number }) {
  const [sent, setSent] = useState<number | null>(null);
  async function vote(rating: number) {
    try {
      await sendAgentFeedback(messageId, rating);
      setSent(rating);
    } catch {
      setSent(null);
    }
  }
  if (sent !== null) return <p className="mt-1 text-xs text-muted">Đã ghi nhận đánh giá.</p>;
  return (
    <div className="mt-1 flex gap-1">
      <button
        type="button"
        onClick={() => vote(5)}
        aria-label="Đánh giá hữu ích"
        className="rounded border border-line px-2 py-0.5 text-xs text-muted"
      >
        👍 Hữu ích
      </button>
      <button
        type="button"
        onClick={() => vote(1)}
        aria-label="Đánh giá chưa hữu ích"
        className="rounded border border-line px-2 py-0.5 text-xs text-muted"
      >
        👎 Chưa hữu ích
      </button>
    </div>
  );
}

function SourceLabel({ source }: { source: string }) {
  if (source === "web") return "Web";
  if (source === "docs" || source === "code") return "Tài liệu";
  return "Dữ liệu";
}

function CitationChips({ items }: { items: AgentCitation[] }) {
  if (items.length === 0) return null;
  const groups = new Map<string, AgentCitation[]>();
  for (const item of items) {
    const key = item.source_type || "database";
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  return (
    <div className="mt-1 space-y-1">
      {[...groups.entries()].map(([source, cites]) => (
        <div key={source} className="flex flex-wrap items-center gap-1">
          <span className="text-[11px] font-medium text-muted">
            <SourceLabel source={source} />:
          </span>
          {cites.map((cite, index) => (
            <span
              key={index}
              title={cite.as_of ? `Cập nhật: ${cite.as_of}` : ""}
              className="rounded-full border border-line px-2 py-0.5 text-[11px] text-muted"
            >
              {cite.ref}
              {cite.as_of ? ` · ${cite.as_of.slice(0, 10)}` : ""}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}

function TraceBox({ traces }: { traces: AgentTrace[] }) {
  const [open, setOpen] = useState(false);
  if (traces.length === 0) return null;
  return (
    <div className="mt-2 text-xs">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="rounded border border-line px-2 py-0.5 text-muted"
      >
        {open ? "Ẩn" : "Hiện"} {traces.length} truy vấn
      </button>
      {open ? (
        <ul className="mt-1 space-y-1 text-muted">
          {traces.map((trace, index) => (
            <li key={index} className="rounded bg-elevated px-2 py-1">
              Đã gọi {trace.tool}
              {trace.summary ? ` — ${trace.summary}` : ""}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export default function AgentPanel({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  const sessionsQuery = useQuery({
    queryKey: ["agent-sessions"],
    queryFn: listAgentSessions,
  });

  useEffect(() => {
    inputRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    if (status !== "streaming") {
      setElapsed(0);
      return;
    }
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [status]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, status]);

  async function openSession(id: number) {
    setError(null);
    const detail = await getAgentSession(id);
    setSessionId(id);
    storeAgentSession(id);
    setMessages(
      detail.messages.map((item) => ({
        ...item,
        traces: [],
        citations: [],
        warnings: [],
        serverId: item.role === "assistant" ? item.id : undefined,
      })),
    );
  }

  useEffect(() => {
    const stored = getStoredAgentSession();
    if (!stored) return;
    let cancelled = false;
    setRestoring(true);
    getAgentSession(stored)
      .then((detail) => {
        if (cancelled) return;
        setSessionId(stored);
        setMessages(
          detail.messages.map((item) => ({
            ...item,
            traces: [],
            citations: [],
            warnings: [],
            serverId: item.role === "assistant" ? item.id : undefined,
          })),
        );
      })
      .catch(() => {
        // Phiên cũ bị xoá hoặc không còn quyền: bỏ ghim.
        storeAgentSession(null);
      })
      .finally(() => {
        if (!cancelled) setRestoring(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function newChat() {
    abortRef.current?.abort();
    setSessionId(null);
    storeAgentSession(null);
    setMessages([]);
    setError(null);
    setStatus("idle");
  }

  async function removeSession(id: number) {
    await deleteAgentSession(id);
    if (id === sessionId) newChat();
    queryClient.invalidateQueries({ queryKey: ["agent-sessions"] });
  }

  async function send(text: string) {
    const content = text.trim();
    if (!content || status === "streaming") return;
    setError(null);
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content,
      traces: [],
      citations: [],
      warnings: [],
    };
    const assistantMessage: ChatMessage = {
      id: Date.now() + 1,
      role: "assistant",
      content: "",
      traces: [],
      citations: [],
      warnings: [],
      pending: true,
    };
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setStatus("streaming");
    const controller = new AbortController();
    abortRef.current = controller;
    let streamError: string | null = null;
    try {
      await streamAgentChat(
        content,
        sessionId,
        {
          onTrace: (tool, summary, ok) => {
            setMessages((prev) =>
              prev.map((item) =>
                item.id === assistantMessage.id
                  ? { ...item, traces: [...(item.traces ?? []), { tool, summary, ok }] }
                  : item,
              ),
            );
          },
          onCitation: (items) => {
            setMessages((prev) =>
              prev.map((item) =>
                item.id === assistantMessage.id
                  ? { ...item, citations: [...(item.citations ?? []), ...items] }
                  : item,
              ),
            );
          },
          onWarning: (message) => {
            setMessages((prev) =>
              prev.map((item) =>
                item.id === assistantMessage.id
                  ? { ...item, warnings: [...(item.warnings ?? []), message] }
                  : item,
              ),
            );
          },
          onDone: (answer, _usage, messageId, sessionId, copyPlan) => {
            if (sessionId) {
              setSessionId(sessionId);
              storeAgentSession(sessionId);
            }
            setMessages((prev) =>
              prev.map((item) =>
                item.id === assistantMessage.id
                  ? {
                      ...item,
                      content: answer,
                      copy_plan: copyPlan,
                      pending: false,
                      serverId: messageId,
                    }
                  : item,
              ),
            );
          },
          onError: (message) => {
            streamError = message;
          },
        },
        controller.signal,
      );
    } catch (err) {
      streamError = err instanceof Error ? err.message : "Trợ lý AI gặp lỗi";
    }
    if (streamError) {
      setError(streamError);
      setMessages((prev) => prev.filter((item) => item.id !== assistantMessage.id));
      setStatus("error");
    } else {
      setStatus("idle");
      queryClient.invalidateQueries({ queryKey: ["agent-sessions"] });
    }
  }

  const items = sessionsQuery.data?.items ?? [];
  const groups = groupSessions(items);

  const panelClass = expanded
    ? "fixed inset-0 z-50 flex flex-col bg-panel"
    : "fixed inset-0 z-50 flex flex-col bg-panel md:inset-auto md:bottom-20 md:right-6 md:h-[76vh] md:w-[460px] md:rounded-2xl md:border md:border-line md:shadow-2xl";

  const sidebar = expanded && sidebarOpen ? (
    <aside className="hidden w-1/4 min-w-[180px] max-w-[320px] shrink-0 flex-col border-r border-line bg-app/40 md:flex">
      <div className="flex items-center justify-between border-b border-line px-3 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-faint">
          Đoạn chat
        </span>
        <button
          type="button"
          onClick={() => setSidebarOpen(false)}
          aria-label="Thu gọn danh sách đoạn chat"
          title="Thu gọn"
          className="rounded-md px-1.5 py-0.5 text-sm text-muted hover:bg-elevated"
        >
          «
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {items.length === 0 ? (
          <p className="px-2 py-3 text-xs text-muted">Chưa có đoạn chat nào.</p>
        ) : (
          groups.map(([label, list]) => (
            <div key={label} className="mb-3">
              <p className="px-2 pb-1 text-[11px] font-medium uppercase tracking-wide text-faint">
                {label}
              </p>
              <ul className="space-y-0.5">
                {list.map((session) => (
                  <li key={session.id} className="group flex items-center">
                    <button
                      type="button"
                      onClick={() => openSession(session.id)}
                      className={`min-w-0 flex-1 truncate rounded-md px-2 py-1.5 text-left text-sm ${
                        session.id === sessionId
                          ? "bg-emerald-500/10 text-accent"
                          : "text-body hover:bg-elevated"
                      }`}
                    >
                      {session.title || `Chat ${session.id}`}
                    </button>
                    <button
                      type="button"
                      onClick={() => removeSession(session.id)}
                      aria-label={`Xóa ${session.title || session.id}`}
                      className="shrink-0 rounded px-1 text-xs text-faint opacity-0 hover:text-danger group-hover:opacity-100"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </aside>
  ) : null;

  return (
    <div role="dialog" aria-label="Trợ lý AI" className={panelClass}>
      <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-line px-3">
        <div className="flex min-w-0 items-center gap-2">
          {expanded && !sidebarOpen ? (
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Mở danh sách đoạn chat"
              title="Danh sách đoạn chat"
              className="rounded-md px-1.5 py-0.5 text-sm text-muted hover:bg-elevated"
            >
              ☰
            </button>
          ) : null}
          <p className="truncate text-sm font-semibold text-strong">Trợ lý AI</p>
          <span className="truncate text-xs text-muted">
            {status === "streaming" ? `Đang trả lời… ${elapsed}s` : ""}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            aria-label={expanded ? "Thu nhỏ" : "Phóng to toàn màn hình"}
            title={expanded ? "Thu nhỏ" : "Phóng to"}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-line text-sm text-body hover:bg-elevated"
          >
            {expanded ? "🗗" : "⛶"}
          </button>
          <button
            type="button"
            onClick={newChat}
            aria-label="Đoạn chat mới"
            title="Đoạn chat mới"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-line text-base text-body hover:bg-elevated"
          >
            +
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng trợ lý AI"
            title="Đóng"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-line text-body hover:bg-elevated"
          >
            ×
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {sidebar}
        <div className="flex min-w-0 flex-1 flex-col">
          <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.length === 0 && restoring ? (
              <p className="text-sm text-muted">Đang mở lại đoạn chat…</p>
            ) : null}
            {messages.length === 0 && !restoring ? (
              <div className="space-y-2">
                <p className="text-sm text-muted">Gợi ý câu hỏi:</p>
                {SUGGESTED.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => send(prompt)}
                    className="block w-full rounded-lg border border-line px-3 py-2 text-left text-sm text-body hover:bg-elevated"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            ) : null}
            {messages.map((item) => (
              <div key={item.id} className={item.role === "user" ? "text-right" : "text-left"}>
                <div
                  className={`inline-block max-w-full rounded-xl px-3 py-2 text-sm ${
                    item.role === "user" ? "bg-emerald-500/15 text-strong" : "bg-elevated text-body"
                  }`}
                >
                  {item.role === "assistant" && !item.pending ? (
                    <Markdown text={item.content} />
                  ) : (
                    <span className="whitespace-pre-wrap">
                      {item.pending && !item.content ? "Đang suy nghĩ…" : item.content}
                    </span>
                  )}
                </div>
                {item.role === "assistant" ? (
                  <>
                    {item.copy_plan ? <CopyPlanCard plan={item.copy_plan} /> : null}
                    <TraceBox traces={item.traces ?? []} />
                    <CitationChips items={item.citations ?? []} />
                    {item.serverId ? <FeedbackButtons messageId={item.serverId} /> : null}
                    {(item.warnings ?? []).map((warning, index) => (
                      <p key={index} className="mt-1 text-xs text-warn">
                        ⚠ {warning}
                      </p>
                    ))}
                  </>
                ) : null}
              </div>
            ))}
            {error ? (
              <p className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
                {error}
              </p>
            ) : null}
          </div>

          <div className="shrink-0 p-3 pt-0">
            <div className="relative rounded-xl border border-line bg-app focus-within:border-accent">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") send(input);
                }}
                rows={2}
                aria-label="Nhập câu hỏi cho trợ lý AI"
                placeholder="Nhập câu hỏi… (Ctrl+Enter để gửi)"
                className="max-h-40 w-full resize-none rounded-xl bg-transparent px-3 py-2 pr-24 text-sm text-strong outline-none placeholder:text-faint"
              />
              <div className="absolute bottom-2 right-2 flex items-center gap-1">
                {status === "streaming" ? (
                  <button
                    type="button"
                    onClick={() => abortRef.current?.abort()}
                    aria-label="Dừng trả lời"
                    title="Dừng"
                    className="flex h-8 items-center justify-center rounded-lg border border-line px-2 text-xs text-body"
                  >
                    Dừng
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => send(input)}
                  disabled={status === "streaming" || !input.trim()}
                  aria-label="Gửi"
                  title="Gửi"
                  className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 text-sm font-semibold text-white disabled:opacity-40"
                >
                  ➤
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function useIsAgentAdmin() {
  return getStoredUser()?.role === "admin";
}

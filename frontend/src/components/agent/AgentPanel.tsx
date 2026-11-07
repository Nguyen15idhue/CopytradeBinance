import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getStoredUser } from "../../lib/auth";
import {
  deleteAgentSession,
  getAgentSession,
  listAgentSessions,
  streamAgentChat,
} from "../../lib/agent";
import type {
  AgentCitation,
  AgentMessageItem,
  AgentStatus,
  AgentTrace,
} from "../../types/agent";

const SUGGESTED = [
  "Top 10 trader an toàn, ít rủi ro, lợi nhuận tốt",
  "Dữ liệu collector có mới không?",
  "Hệ thống tính Sharpe và risk_score thế nào?",
];

interface ChatMessage extends AgentMessageItem {
  traces?: AgentTrace[];
  citations?: AgentCitation[];
  warnings?: string[];
  pending?: boolean;
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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [error, setError] = useState<string | null>(null);
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
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, status]);

  async function openSession(id: number) {
    setError(null);
    const detail = await getAgentSession(id);
    setSessionId(id);
    setMessages(
      detail.messages.map((item) => ({ ...item, traces: [], citations: [], warnings: [] })),
    );
  }

  function newChat() {
    abortRef.current?.abort();
    setSessionId(null);
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
          onDone: (answer) => {
            setMessages((prev) =>
              prev.map((item) =>
                item.id === assistantMessage.id
                  ? { ...item, content: answer, pending: false }
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

  return (
    <div
      role="dialog"
      aria-label="Trợ lý AI"
      className="fixed inset-0 z-50 flex flex-col bg-panel md:inset-auto md:bottom-20 md:right-6 md:h-[70vh] md:w-[440px] md:rounded-2xl md:border md:border-line md:shadow-2xl"
    >
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <p className="font-semibold text-strong">Trợ lý AI</p>
          <p className="text-xs text-muted">
            {status === "streaming" ? "Đang trả lời…" : "Hỏi đáp copy trading, hệ thống, mã nguồn"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={newChat}
            aria-label="Đoạn chat mới"
            className="rounded-lg border border-line px-2 py-1 text-sm text-body"
          >
            + Mới
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng trợ lý AI"
            className="rounded-lg border border-line px-2 py-1 text-body"
          >
            ×
          </button>
        </div>
      </div>

      {items.length > 0 ? (
        <div className="flex gap-2 overflow-x-auto border-b border-line px-4 py-2 text-xs">
          {items.slice(0, 10).map((session) => (
            <div
              key={session.id}
              className={`flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 ${
                session.id === sessionId ? "border-accent text-accent" : "border-line text-muted"
              }`}
            >
              <button type="button" onClick={() => openSession(session.id)} className="max-w-32 truncate">
                {session.title || `Chat ${session.id}`}
              </button>
              <button
                type="button"
                onClick={() => removeSession(session.id)}
                aria-label={`Xóa ${session.title || session.id}`}
                className="text-faint"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.length === 0 ? (
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
              className={`inline-block max-w-full whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${
                item.role === "user" ? "bg-emerald-500/15 text-strong" : "bg-elevated text-body"
              }`}
            >
              {item.pending && !item.content ? "Đang suy nghĩ…" : item.content}
            </div>
            {item.role === "assistant" ? (
              <>
                <TraceBox traces={item.traces ?? []} />
                {(item.citations ?? []).length > 0 ? (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {item.citations!.map((cite, index) => (
                      <span
                        key={index}
                        title={cite.as_of ?? ""}
                        className="rounded-full border border-line px-2 py-0.5 text-[11px] text-muted"
                      >
                        {cite.source_type}: {cite.ref}
                      </span>
                    ))}
                  </div>
                ) : null}
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

      <div className="border-t border-line p-3">
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
          className="w-full rounded-lg border border-line bg-app px-3 py-2 text-sm text-strong"
        />
        <div className="mt-2 flex justify-end gap-2">
          {status === "streaming" ? (
            <button
              type="button"
              onClick={() => abortRef.current?.abort()}
              className="rounded-lg border border-line px-3 py-1.5 text-sm text-body"
            >
              Dừng
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => send(input)}
            disabled={status === "streaming" || !input.trim()}
            className="rounded-lg bg-emerald-500 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            Gửi
          </button>
        </div>
      </div>
    </div>
  );
}

export function useIsAgentAdmin() {
  return getStoredUser()?.role === "admin";
}

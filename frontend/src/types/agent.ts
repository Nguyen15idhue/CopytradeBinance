export interface AgentSessionItem {
  id: number;
  title: string;
  model: string;
  created_at: string | null;
  updated_at: string | null;
  archived_at: string | null;
}

export interface AgentMessageItem {
  id: number;
  role: "user" | "assistant";
  content: string;
}

export interface AgentCitation {
  source_type: string;
  ref: string;
  as_of?: string | null;
}

export interface AgentTrace {
  tool: string;
  summary?: string;
  ok?: boolean;
}

export interface AgentDoneUsage {
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
}

export type AgentStatus = "idle" | "streaming" | "error";

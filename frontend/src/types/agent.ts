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
  copy_plan?: AgentCopyPlan | null;
  copy_plan_version?: number | null;
}

export interface CopyPlanField {
  value: unknown;
  source: string;
  status: string;
  unit?: string | null;
  min?: number | null;
  max?: number | null;
  note?: string | null;
  evidence_id?: string | null;
  [key: string]: unknown;
}

export interface AgentCopyPlan {
  version: number;
  trader_id: string;
  limits_version?: string;
  copy_mode: CopyPlanField;
  copy_amount_usd: CopyPlanField;
  cost_per_order_usd: CopyPlanField;
  max_cost_per_order_pct: CopyPlanField;
  total_stop_loss_usd: CopyPlanField;
  symbols: CopyPlanField;
  copy_existing_positions: CopyPlanField;
  better_entry_price: CopyPlanField;
  margin_mode: CopyPlanField;
  leverage: CopyPlanField;
  max_slippage_pct: CopyPlanField;
  take_profit_pct: CopyPlanField;
  stop_loss_pct: CopyPlanField;
  close_all_at_take_profit: CopyPlanField;
  auto_invest: CopyPlanField;
  can_copy: boolean | null;
  used_capital_usd?: number | null;
  warnings: string[];
  missing_fields: string[];
  assumptions: string[];
  [key: string]: unknown;
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

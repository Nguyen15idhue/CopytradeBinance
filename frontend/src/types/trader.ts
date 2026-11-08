export interface Metric {
  key: string;
  label: string;
  value: number | string | null;
  unit: string;
  source: string;
  window: string | null;
  note: string | null;
}

export interface TraderDetail {
  trader: {
    id: string;
    nickname: string | null;
    portfolio_type: string | null;
    status: string | null;
    description: string | null;
    runtime_days: number | null;
    last_trade_time: string | null;
  };
  tier: string;
  reasons: string[];
  pre_score: number | null;
  metrics: Metric[];
  profile: {
    aum: number | null;
    copy_aum: number | null;
    current_copy_count: number | null;
    max_copy_count: number | null;
    leverage: number | null;
    win_orders: number | null;
    total_orders: number | null;
    pnl: number | null;
  };
  confidence: number;
  flags: string[];
  provenance: {
    source: string | null;
    collected_at: string | null;
    endpoint: string;
    window: string;
    published: boolean;
  };
  freshness?:
    | {
        minutes: number | null;
        level: "ok" | "stale" | "very_stale" | "unknown";
        as_of?: string | null;
      }
    | null;
  as_of?: string | null;
  computed_at?: string | null;
  disclaimer: string;
  generated_at: string;
}

export interface CollectorStatus {
  enabled: boolean;
  kill_switch_key: string;
  tiers: Record<string, number>;
  latest_runs: Record<
    string,
    | {
        status: string;
        started_at: string;
        finished_at: string | null;
        requests: number;
        items_ok: number;
        error_count: number;
        detail: Record<string, unknown> | null;
      }
    | null
  >;
  jobs: Array<{
    id: string;
    kind: string;
    status: string;
    requested_at?: string | null;
    started_at: string | null;
    finished_at: string | null;
    error: string | null;
    result?: Record<string, unknown> | null;
  }>;
  raw_archive: {
    files: number;
    bytes: number;
    records?: number;
    mode?: string;
    latest_at?: string | null;
    source?: string;
  };
  generated_at: string;
}

export interface CollectorJob {
  id: string;
  kind: string;
  status: string;
  requested_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface ScreenerItem {
  id: string;
  nickname: string | null;
  portfolio_type: string | null;
  status: string | null;
  potential_tier: string;
  pre_score: number | null;
  score: number | null;
  band: string | null;
  confidence: number | null;
  rankable: boolean;
  hard_flags: string[];
  risk_level: string | null;
  roi_90d: number | null;
  mdd_90d: number | null;
  sharpe: number | null;
  win_rate_order_90d: number | null;
  win_orders: number | null;
  total_orders_90d: number | null;
  runtime_days: number | null;
  current_copiers: number | null;
  copy_aum: number | null;
  aum: number | null;
  max_leverage: number | null;
  profit_factor: number | null;
  fee_drag_pct: number | null;
  avg_leverage: number | null;
  position_win_rate: number | null;
  risk_score: number | null;
  as_of?: string | null;
  freshness?:
    | {
        minutes: number | null;
        level: "ok" | "stale" | "very_stale" | "unknown";
        as_of?: string | null;
      }
    | null;
  windows: Record<
    string,
    {
      roi?: number | null;
      mdd?: number | null;
      sharpe?: number | null;
      copier_pnl?: number | null;
      win_rate?: number | null;
    }
  >;
  low_sample: boolean;
  filter_reasons: string[];
  breakdown: {
    components?: Record<
      string,
      { score: number; weight: number; contribution: number | null; missing?: string[] }
    >;
    missing?: string[];
  };
  computed_at?: string | null;
  top_symbol: string | null;
}

export interface ScreenerResponse {
  items: ScreenerItem[];
  page: number;
  page_size: number;
  total: number;
  sort_by: string;
  sort_dir: "asc" | "desc";
  config_version: number;
  window?: string;
  window_missing?: boolean;
  risk_score_missing?: boolean;
}

export interface FunnelSummary {
  universe: number;
  watch: number;
  qualified: number;
  high: number;
  excluded: number;
}

export interface SavedView {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  created_at?: string;
}

export interface PerformanceWindow {
  window: string;
  roi: number | null;
  pnl: number | null;
  mdd: number | null;
  copier_pnl: number | null;
  win_rate: number | null;
  win_orders: number | null;
  total_orders: number | null;
  sharpe: number | null;
  collected_at: string;
}

export interface PerformanceResponse {
  windows: Record<string, PerformanceWindow | null>;
  chart: Array<{ date_time: number; value: number }>;
  chart_note: string;
  benchmark: number | null;
  benchmark_note: string;
}

export interface PositionRow {
  id: string;
  symbol: string | null;
  side: string | null;
  leverage: number | null;
  isolated: string | null;
  opened_at: string | null;
  closed_at: string | null;
  closing_pnl: number | null;
  roi: number | null;
  status: string | null;
}

export interface TradeRow {
  hash: string;
  time: string | null;
  symbol: string | null;
  side: string | null;
  price: number | null;
  qty: number | null;
  notional: number | null;
  fee: number | null;
  realized_profit: number | null;
  position_side: string | null;
}

export interface TransferRow {
  time: string | null;
  coin: string | null;
  amount: number | null;
  from: string | null;
  to: string | null;
  type: string | null;
}

export interface Paged<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface RiskResponse {
  risk_level: string | null;
  flags: string[];
  events: Array<{
    code: string;
    severity: string;
    label: string;
    evidence: Record<string, unknown>;
    status: string;
  }>;
}

export interface ScoreResponse {
  config_version: number;
  score: number | null;
  band: string | null;
  confidence: number | null;
  rankable: boolean;
  hard_flags: string[];
  breakdown: {
    components?: Record<
      string,
      { score: number; weight: number; contribution: number | null; missing?: string[] }
    >;
    missing?: string[];
  };
}

export interface CompareItem {
  id: string;
  nickname: string | null;
  tier: string;
  score: number | null;
  band: string | null;
  confidence: number | null;
  risk_level: string | null;
  roi_90d: number | null;
  mdd_90d: number | null;
  sharpe: number | null;
  win_rate_order: number | null;
  max_leverage: number | null;
  profit_factor: number | null;
  runtime_days: number | null;
  copier_pnl_90d: number | null;
  copy_aum: number | null;
  pnl_90d: number | null;
  top_symbol: string | null;
  windows: Record<string, { roi: number | null; mdd: number | null }>;
}

export interface CompareResponse {
  items: CompareItem[];
  series: Record<string, Array<{ date_time: number; value: number }>>;
  correlation: {
    ids: string[];
    matrix: Array<Array<number | null>>;
    sample_days: number;
    disclaimer: string;
  };
  missing: string[];
}

export interface RiskEventRow {
  trader_id: string;
  nickname: string | null;
  code: string;
  severity: string;
  label: string;
  evidence: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface RiskEventsResponse {
  items: RiskEventRow[];
  page: number;
  page_size: number;
  total: number;
}

export interface RiskSummary {
  total: number;
  by_severity: Record<string, number>;
}

export interface AIReportItem {
  id: number;
  trader_id: string;
  model_role: "primary" | "fallback" | "template";
  model_used: string;
  prompt_version: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  risk_flags: string[];
  missing_data: string[];
  evidence_ids: string[];
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cost_usd: number;
  latency_ms: number | null;
  status: string;
  created_at: string;
}

export interface AIReportsResponse {
  items: AIReportItem[];
  total: number;
}

export interface SettingsSnapshot {
  scoring: {
    version: number;
    weights: Record<string, number>;
    hard_filters: Record<string, unknown>;
    normalization: Record<string, unknown>;
  };
  ai: {
    model_primary: string;
    model_fallback: string;
    monthly_budget_usd: number;
    daily_budget_usd: number;
    enabled: boolean;
    key_configured: boolean;
    key_masked: string;
  };
  collector: {
    scan_interval_min: number;
    deep_interval_hours_watch: number;
    deep_interval_hours_qualified: number;
    deep_interval_hours_high: number;
  };
  system: { app_env: string; app_name: string; api_v1_prefix: string };
}

export interface SettingsVersion {
  version: number;
  is_active: boolean;
  weights: Record<string, number>;
  hard_filters: Record<string, unknown>;
  created_at: string;
}

export interface PreviewImpact {
  traders: number;
  changed_band: number;
  top_changes: Array<{
    id: string;
    old_score: number | null;
    new_score: number | null;
    old_band: string | null;
    new_band: string | null;
    delta: number;
  }>;
  weights: Record<string, number>;
}

export interface RankingItem {
  rank: number;
  id: string;
  nickname: string | null;
  tier: string;
  score: number | null;
  band: string | null;
  confidence: number | null;
  risk_level: string | null;
  roi_90d: number | null;
  mdd_90d: number | null;
  sharpe: number | null;
}

export interface RankingResponse {
  board: string;
  config_version: number | null;
  collected_at: string | null;
  items: RankingItem[];
  total: number;
}

export interface AuthUser {
  id: string;
  email: string;
  role: "admin" | "viewer";
}

export interface LoginResult {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

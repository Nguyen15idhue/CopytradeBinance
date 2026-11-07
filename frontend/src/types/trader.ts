export interface Metric {
  key: string;
  label: string;
  value: number | null;
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
    started_at: string;
    finished_at: string | null;
    error: string | null;
  }>;
  raw_archive: { files: number; bytes: number };
  generated_at: string;
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
  low_sample: boolean;
  filter_reasons: string[];
  breakdown: {
    components?: Record<
      string,
      { score: number; weight: number; contribution: number | null; missing?: string[] }
    >;
    missing?: string[];
  };
  computed_at: string | null;
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

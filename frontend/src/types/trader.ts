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

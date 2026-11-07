const STORAGE_KEY = "ct_screener_query";

export const SCREENER_DEFAULTS = {
  q: "",
  tier: "high_upper",
  include: "",
  risk: "",
  window: "90D",
  roi_min: "",
  mdd_max: "",
  sharpe_min: "",
  win_min: "",
  runtime_min: "",
  orders_min: "",
  lev_max: "",
  avg_lev_max: "",
  risk_score_max: "",
  copiers_min: "",
  copier_pnl_min: "",
  aum_min: "",
  pf_min: "",
  conf_min: "",
  min_copy_max: "",
  copy_aum_max: "",
  fee_max: "",
  sort: "score",
  dir: "desc",
  page: "1",
  size: "50",
} as const;

export type ScreenerParamKey = keyof typeof SCREENER_DEFAULTS;
export type ScreenerParams = Record<ScreenerParamKey, string>;

const TIER_ALL = "all";
const WINDOWS = ["7D", "30D", "90D", "180D"];
const DIRS = ["asc", "desc"];

function readTier(raw: string | null): string {
  if (raw === null) return SCREENER_DEFAULTS.tier;
  return raw === TIER_ALL ? "" : raw;
}

function writeTier(value: string): string | null {
  if (value === "") return TIER_ALL;
  if (value === SCREENER_DEFAULTS.tier) return null;
  return value;
}

export function parseScreenerQuery(search: URLSearchParams): ScreenerParams {
  const out = { ...SCREENER_DEFAULTS } as ScreenerParams;
  for (const key of Object.keys(SCREENER_DEFAULTS) as ScreenerParamKey[]) {
    if (key === "tier") continue;
    const raw = search.get(key);
    if (raw !== null) out[key] = raw;
  }
  out.tier = readTier(search.get("tier"));
  if (!WINDOWS.includes(out.window)) out.window = SCREENER_DEFAULTS.window;
  if (!DIRS.includes(out.dir)) out.dir = SCREENER_DEFAULTS.dir;
  const page = Number(out.page);
  out.page = Number.isFinite(page) && page >= 1 ? String(Math.floor(page)) : "1";
  const size = Number(out.size);
  out.size = Number.isFinite(size) && size >= 1 && size <= 100 ? String(size) : "50";
  return out;
}

export function serializeScreenerParams(params: ScreenerParams): URLSearchParams {
  const search = new URLSearchParams();
  for (const key of Object.keys(SCREENER_DEFAULTS) as ScreenerParamKey[]) {
    if (key === "tier") {
      const tier = writeTier(params.tier);
      if (tier !== null) search.set("tier", tier);
      continue;
    }
    const value = params[key];
    if (!value || value === SCREENER_DEFAULTS[key]) continue;
    search.set(key, value);
  }
  return search;
}

export function storeScreenerQuery(query: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, query);
  } catch {
    // sessionStorage có thể bị chặn; bỏ qua.
  }
}

export function storedScreenerQuery(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function screenerFallbackPath(): string {
  const stored = storedScreenerQuery();
  return stored ? `/screener?${stored}` : "/screener";
}

export const WINDOW_OPTIONS = WINDOWS;

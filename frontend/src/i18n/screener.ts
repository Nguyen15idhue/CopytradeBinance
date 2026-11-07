export const WINDOW_LABELS: Record<string, string> = {
  "7D": "7 ngày",
  "30D": "30 ngày",
  "90D": "90 ngày",
  "180D": "180 ngày",
};

export const WINDOW_OPTIONS = ["7D", "30D", "90D", "180D"] as const;
export type WindowKey = (typeof WINDOW_OPTIONS)[number];

export const FILTER_GROUPS = {
  performance: "Hiệu suất",
  scale: "Quy mô & phổ biến",
  risk: "Rủi ro & chất lượng",
} as const;

export const SCREENER_TEXTS = {
  windowLabel: "Khung thời gian",
  filtersActive: "bộ lọc đang bật",
  clearAll: "Xóa tất cả",
  noMatch: "Không có trader khớp bộ lọc.",
  windowMissing: "Khung này chưa có dữ liệu cho trader nào.",
  columns: {
    roi: "ROI",
    mdd: "MDD",
    sharpe: "Sharpe",
    winRate: "WinRate",
    copierPnl: "Copier PnL",
    copiers: "Số copier",
    aum: "AUM",
    copyAum: "Copy AUM",
    profitFactor: "Profit factor",
    confidence: "Độ tin cậy",
    avgLeverage: "Đòn bẩy TB",
    feeDrag: "Fee drag",
    positionWinRate: "WinRate vị thế",
    riskScore: "Điểm rủi ro",
  },
} as const;

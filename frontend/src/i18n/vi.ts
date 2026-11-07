/**
 * Nhãn hiển thị tiếng Việt cho toàn bộ UI.
 *
 * Quy ước:
 * - Backend/API vẫn dùng mã tiếng Anh (high_upper, published, primary...).
 * - UI chỉ hiển thị nhãn trong file này, không hiển thị mã thô.
 * - Thuật ngữ đặc thù (ROI, PnL, MDD, Sharpe, WinRate, AUM...) giữ nguyên.
 */

export const NAV_LABELS = {
  home: "Trader mẫu",
  dataHealth: "Sức khỏe dữ liệu",
  screener: "Bộ lọc trader",
  ranking: "Bảng xếp hạng",
  compare: "So sánh",
  risk: "Cảnh báo rủi ro",
  settings: "Cài đặt",
  help: "Hướng dẫn",
  technical: "Tài liệu kỹ thuật",
} as const;

export const TIER_LABELS: Record<string, string> = {
  high_upper: "Cao (A)",
  qualified_upper: "Đạt (B)",
  watch: "Theo dõi (C)",
  excluded: "Bị loại",
  unknown: "Chưa rõ",
};

export const BAND_LABELS: Record<string, string> = {
  excellent: "Xuất sắc",
  good: "Tốt",
  average: "Trung bình",
  weak: "Yếu",
  high_risk: "Rủi ro cao",
  none: "Chưa có",
};

export const RISK_LEVEL_LABELS: Record<string, string> = {
  critical: "Nghiêm trọng",
  high: "Cao",
  medium: "Trung bình",
  low: "Thấp",
  none: "Không có",
  unknown: "Chưa rõ",
  low_sample: "Mẫu nhỏ",
  confidence_penalty: "Trừ điểm tin cậy",
  insufficient: "Chưa đủ dữ liệu",
};

export const SEVERITY_LABELS: Record<string, string> = {
  critical: "Nghiêm trọng",
  high: "Cao",
  medium: "Trung bình",
  low: "Thấp",
  low_sample: "Mẫu nhỏ",
  confidence_penalty: "Trừ điểm tin cậy",
  insufficient: "Chưa đủ dữ liệu",
  unknown: "Chưa rõ",
};

export const MODEL_ROLE_LABELS: Record<string, string> = {
  primary: "Model chính",
  fallback: "Model dự phòng",
  template: "Mẫu tất định",
};

export const JOB_STATUS_LABELS: Record<string, string> = {
  success: "Thành công",
  running: "Đang chạy",
  skipped: "Bỏ qua",
  failed: "Thất bại",
  template: "Mẫu tất định",
};

export const JOB_KIND_LABELS: Record<string, string> = {
  scan: "Quét universe",
  deep: "Thu thập sâu",
};

export const SOURCE_LABELS: Record<string, string> = {
  published: "Binance công bố",
  derived: "Hệ thống tính",
  detail: "Chi tiết",
  estimated: "Ước tính",
  demo: "Dữ liệu demo",
  chartItems: "chartItems",
};

export const LAYER_LABELS: Record<string, string> = {
  L0: "L0 — Quét universe",
  L2: "L2 — Hiệu suất",
  L3: "L3 — Chi tiết + vị thế + nạp/rút",
  L4: "L4 — Toàn bộ giao dịch",
};

export const HARD_FLAG_LABELS: Record<string, string> = {
  hf01_not_active: "Tài khoản không ACTIVE",
  hf02_excluded: "Bị loại khỏi shortlist",
  hf03_runtime_lt_30: "Runtime < 30 ngày",
  hf04_low_orders: "Không đủ số lệnh",
  hf05_stale: "Dữ liệu cũ > 150 phút",
  hf06_low_confidence: "Độ tin cậy < 0,5",
};

export const FILTER_REASON_LABELS: Record<string, string> = {
  runtime_lt_30: "Runtime < 30 ngày",
  no_trade_7d: "Không giao dịch 7 ngày",
  roi_le_0: "ROI ≤ 0",
  pnl_le_0: "PnL ≤ 0",
  winrate_lt_40: "WinRate < 40%",
  mdd_gt_40: "MDD > 40%",
  aum_lt_5000: "AUM < 5.000",
  no_slots: "Hết slot copy",
  total_orders_lt_threshold: "Không đủ tổng số lệnh cho tier",
  not_in_universe: "Không có trong universe",
};

export const RISK_EVENT_LABELS: Record<string, string> = {
  R01: "Runtime < 30 ngày",
  R02: "MDD > 20%",
  R03: "MDD > 30%",
  R04: "Đòn bẩy tối đa > 10x",
  R05: "Đòn bẩy tối đa > 20x",
  R06: "ROI vị thế ≤ −80%",
  R07: "Tổng số lệnh < 20",
  R08: "Sharpe trống",
  R09: "Dữ liệu cũ > 150 phút",
  R10: "Copier PnL âm, lead dương",
  R11: "Copy AUM < 5% AUM",
};

export const GROUP_LABELS: Record<string, string> = {
  risk_management: "Quản trị rủi ro",
  consistency: "Độ ổn định",
  profitability: "Khả năng sinh lời",
  trading_quality: "Chất lượng giao dịch",
  copy_performance: "Hiệu quả copy",
  capital_efficiency: "Hiệu quả vốn",
  data_reliability: "Độ tin cậy dữ liệu",
};

export const BOARD_LABELS: Record<string, string> = {
  overall: "Tổng hợp",
  low_risk: "Rủi ro thấp",
  consistency: "Độ ổn định",
};

export const METRIC_LABELS: Record<string, string> = {
  roi_90d: "ROI 90D",
  mdd_90d: "MDD 90D",
  sharpe: "Sharpe",
  win_rate_order: "WinRate (lệnh)",
  profit_factor: "Profit Factor",
  max_leverage: "Đòn bẩy tối đa",
  avg_holding: "Thời gian giữ TB",
  copier_pnl: "Copier PnL",
  copy_aum: "Copy AUM",
  copiers: "Số copier",
};

export const PORTFOLIO_TYPE_LABELS: Record<string, string> = {
  PUBLIC: "Công khai",
  PRIVATE: "Riêng tư",
};

export const TRADER_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Đang hoạt động",
  INACTIVE: "Ngừng hoạt động",
};

export const TRANSFER_TYPE_LABELS: Record<string, string> = {
  TRANSFER_IN: "Nạp vào",
  TRANSFER_OUT: "Rút ra",
};

export const FLAG_LABELS: Record<string, string> = {
  missing_sharpe: "Thiếu Sharpe",
  missing_mdd: "Thiếu MDD",
  missing_benchmark: "Chưa có benchmark",
  no_copiers: "Không có copier",
  low_sample: "Mẫu giao dịch nhỏ",
  insufficient_positions: "Thiếu mẫu vị thế",
  missing_trades: "Chưa có lịch sử giao dịch",
  derived_unavailable: "Chỉ số derived chưa có",
  excluded: "Bị loại khỏi shortlist",
  open_positions_unavailable: "Không có dữ liệu vị thế đang mở",
  per_copier_unavailable: "Không có PnL từng copier",
  funding_unavailable: "Không có dữ liệu funding",
};

export function label(
  map: Record<string, string>,
  code: string | null | undefined,
  fallback = "Chưa rõ",
): string {
  if (!code) return fallback;
  return map[code] ?? fallback;
}

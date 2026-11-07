import type { ReactNode } from "react";

const box = "var(--panel)";
const elevated = "var(--elevated)";
const line = "var(--line)";
const body = "var(--text-body)";
const muted = "var(--text-muted)";
const accent = "var(--accent)";
const warn = "var(--warn)";
const info = "var(--info)";
const danger = "var(--danger)";

function Frame({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: ReactNode;
}) {
  return (
    <figure className="mt-3 overflow-hidden rounded-xl border border-line bg-app/40">
      <svg
        viewBox="0 0 720 220"
        role="img"
        aria-label={title}
        className="h-auto w-full"
      >
        <title>{title}</title>
        {children}
      </svg>
      <figcaption className="border-t border-line px-3 py-2 text-xs text-muted">
        {caption}
      </figcaption>
    </figure>
  );
}

export function CopyFlowDiagram() {
  return (
    <Frame
      title="Luồng copy trading"
      caption="Lead trader giao dịch → Binance khớp lệnh → tài khoản copy sao chép theo tỷ lệ. Kết quả có thể khác do trễ và trượt giá."
    >
      <rect x="20" y="60" width="180" height="80" rx="10" fill={elevated} stroke={line} />
      <text x="110" y="92" textAnchor="middle" fill={body} fontSize="13" fontWeight="600">
        Lead trader
      </text>
      <text x="110" y="112" textAnchor="middle" fill={muted} fontSize="11">
        mở / đóng vị thế
      </text>

      <rect x="260" y="60" width="200" height="80" rx="10" fill={box} stroke={line} />
      <text x="360" y="92" textAnchor="middle" fill={body} fontSize="13" fontWeight="600">
        Binance Futures
      </text>
      <text x="360" y="112" textAnchor="middle" fill={muted} fontSize="11">
        khớp lệnh, tính phí
      </text>

      <rect x="520" y="60" width="180" height="80" rx="10" fill={elevated} stroke={line} />
      <text x="610" y="92" textAnchor="middle" fill={body} fontSize="13" fontWeight="600">
        Tài khoản copy
      </text>
      <text x="610" y="112" textAnchor="middle" fill={muted} fontSize="11">
        sao chép theo tỷ lệ
      </text>

      <line x1="200" y1="100" x2="258" y2="100" stroke={accent} strokeWidth="1.5" markerEnd="url(#arrow)" />
      <line x1="460" y1="100" x2="518" y2="100" stroke={accent} strokeWidth="1.5" markerEnd="url(#arrow)" />

      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill={accent} />
        </marker>
      </defs>

      <rect x="150" y="165" width="130" height="26" rx="13" fill="none" stroke={warn} />
      <text x="215" y="182" textAnchor="middle" fill={warn} fontSize="11">
        có thể mất vốn
      </text>
      <rect x="295" y="165" width="150" height="26" rx="13" fill="none" stroke={warn} />
      <text x="370" y="182" textAnchor="middle" fill={warn} fontSize="11">
        không đảm bảo lợi nhuận
      </text>
      <rect x="460" y="165" width="120" height="26" rx="13" fill="none" stroke={danger} />
      <text x="520" y="182" textAnchor="middle" fill={danger} fontSize="11">
        trễ &amp; trượt giá
      </text>
    </Frame>
  );
}

export function FunnelDiagram() {
  const rows = [
    ["Universe (PUBLIC + SIGNAL)", 660, "11.124"],
    ["Theo dõi (C + B + A)", 420, "~515"],
    ["Đạt (B)", 210, "~109"],
    ["Cao (A)", 90, "~13"],
  ];
  return (
    <Frame
      title="Phễu sàng lọc"
      caption="Số minh hoạ từ Phase 0. Số thực tế thay đổi theo thị trường; luôn đọc từ Sức khỏe dữ liệu."
    >
      {rows.map(([label, width, value], index) => {
        const y = 24 + index * 46;
        return (
          <g key={String(label)}>
            <text x="16" y={y + 20} fill={body} fontSize="12">
              {label}
            </text>
            <rect
              x={300}
              y={y}
              width={Number(width)}
              height="30"
              rx="6"
              fill={index === 0 ? info : index === 3 ? accent : elevated}
              opacity={index === 0 ? 0.35 : 0.55}
              stroke={line}
            />
            <text x={310 + Number(width)} y={y + 20} fill={body} fontSize="12" fontWeight="600">
              {value}
            </text>
          </g>
        );
      })}
    </Frame>
  );
}

export function MetricAnatomyDiagram() {
  return (
    <Frame
      title="Cấu trúc một metric card"
      caption="Mỗi chỉ số phải cho biết nguồn (Binance công bố/hệ thống tính), cửa sổ (7D/30D/90D/180D) và cảnh báo mẫu nhỏ."
    >
      <rect x="30" y="25" width="300" height="150" rx="12" fill={elevated} stroke={line} />
      <text x="50" y="52" fill={muted} fontSize="11" letterSpacing="1">
        ROI 90D
      </text>
      <text x="50" y="90" fill="var(--text-strong)" fontSize="28" fontWeight="700">
        19,19%
      </text>
      <text x="50" y="114" fill={muted} fontSize="11">
        Binance công bố · 90D
      </text>
      <rect x="50" y="128" width="86" height="22" rx="11" fill="none" stroke={warn} />
      <text x="93" y="143" textAnchor="middle" fill={warn} fontSize="10">
        mẫu nhỏ
      </text>

      <line x1="330" y1="52" x2="430" y2="52" stroke={muted} strokeDasharray="4 4" />
      <text x="440" y="56" fill={body} fontSize="12">
        Nhãn chỉ số
      </text>
      <line x1="330" y1="90" x2="430" y2="90" stroke={muted} strokeDasharray="4 4" />
      <text x="440" y="94" fill={body} fontSize="12">
        Giá trị, N/A nếu null
      </text>
      <line x1="330" y1="114" x2="430" y2="114" stroke={muted} strokeDasharray="4 4" />
      <text x="440" y="118" fill={body} fontSize="12">
        Nguồn + cửa sổ
      </text>
      <line x1="330" y1="139" x2="430" y2="139" stroke={muted} strokeDasharray="4" />
      <text x="440" y="143" fill={body} fontSize="12">
        Badge cảnh báo (nếu có)
      </text>
    </Frame>
  );
}

export function RiskEvidenceDiagram() {
  return (
    <Frame
      title="Cảnh báo rủi ro và bằng chứng"
      caption="Cảnh báo rủi ro chỉ là tín hiệu, không tự loại trader. Mở bằng chứng để xem trường dữ liệu, giá trị và ngưỡng."
    >
      <rect x="20" y="40" width="200" height="120" rx="10" fill={elevated} stroke={line} />
      <text x="120" y="66" textAnchor="middle" fill={danger} fontSize="12" fontWeight="600">
        R03 · Nghiêm trọng
      </text>
      <text x="120" y="90" textAnchor="middle" fill={body} fontSize="12">
        MDD &gt; 30%
      </text>
      <text x="120" y="112" textAnchor="middle" fill={muted} fontSize="11">
        cảnh báo được tạo
      </text>

      <line x1="220" y1="100" x2="280" y2="100" stroke={muted} markerEnd="url(#arrow2)" />
      <defs>
        <marker id="arrow2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill={muted} />
        </marker>
      </defs>

      <rect x="290" y="30" width="240" height="140" rx="10" fill={box} stroke={line} />
      <text x="305" y="52" fill={muted} fontSize="10" letterSpacing="1">
        BẰNG CHỨNG JSON
      </text>
      <text x="305" y="74" fill={body} fontSize="11" fontFamily="monospace">
        {"{"}
      </text>
      <text x="315" y="92" fill={body} fontSize="11" fontFamily="monospace">
        "field": "mdd_90d",
      </text>
      <text x="315" y="110" fill={body} fontSize="11" fontFamily="monospace">
        "value": 31.34,
      </text>
      <text x="315" y="128" fill={body} fontSize="11" fontFamily="monospace">
        "threshold": 30
      </text>
      <text x="305" y="146" fill={body} fontSize="11" fontFamily="monospace">
        {"}"}
      </text>

      <rect x="560" y="60" width="140" height="80" rx="10" fill={elevated} stroke={line} />
      <text x="630" y="90" textAnchor="middle" fill={body} fontSize="12">
        Bạn quyết định
      </text>
      <text x="630" y="110" textAnchor="middle" fill={muted} fontSize="11">
        không tự động loại
      </text>
    </Frame>
  );
}

export function WorkflowDiagram() {
  const steps = ["Lọc", "Đọc chi tiết", "So sánh", "Xem rủi ro", "Tự quyết định"];
  return (
    <Frame
      title="Quy trình 5 bước"
      caption="Không bỏ qua bước rủi ro và không copy chỉ vì ROI cao."
    >
      {steps.map((label, index) => {
        const x = 20 + index * 140;
        return (
          <g key={label}>
            <circle cx={x + 45} cy="95" r="24" fill={index === 4 ? accent : elevated} stroke={line} />
            <text
              x={x + 45}
              y="100"
              textAnchor="middle"
              fill={index === 4 ? "var(--bg)" : body}
              fontSize="13"
              fontWeight="600"
            >
              {index + 1}
            </text>
            <text x={x + 45} y="145" textAnchor="middle" fill={body} fontSize="12">
              {label}
            </text>
            {index < steps.length - 1 ? (
              <line x1={x + 72} y1="95" x2={x + 128} y2="95" stroke={muted} strokeDasharray="4 4" />
            ) : null}
          </g>
        );
      })}
    </Frame>
  );
}

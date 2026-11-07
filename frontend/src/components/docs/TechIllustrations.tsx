import type { ReactNode } from "react";

const panel = "var(--panel)";
const elevated = "var(--elevated)";
const line = "var(--line)";
const body = "var(--text-body)";
const muted = "var(--text-muted)";
const accent = "var(--accent)";
const info = "var(--info)";
const warn = "var(--warn)";

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
    <figure className="mt-4 overflow-hidden rounded-xl border border-line bg-app/40">
      <svg viewBox="0 0 760 270" role="img" aria-label={title} className="h-auto w-full">
        <title>{title}</title>
        {children}
      </svg>
      <figcaption className="border-t border-line px-3 py-2 text-xs text-muted">
        {caption}
      </figcaption>
    </figure>
  );
}

function Box({
  x,
  y,
  w,
  h,
  label,
  sub,
  fill = elevated,
}: {
  x: number | string;
  y: number | string;
  w: number | string;
  h: number | string;
  label: string;
  sub?: string;
  fill?: string;
}) {
  const nx = Number(x);
  const ny = Number(y);
  const nw = Number(w);
  const nh = Number(h);
  return (
    <g>
      <rect x={nx} y={ny} width={nw} height={nh} rx="10" fill={fill} stroke={line} />
      <text x={nx + nw / 2} y={ny + (sub ? 26 : 32)} textAnchor="middle" fill={body} fontSize="12" fontWeight="600">
        {label}
      </text>
      {sub ? (
        <text x={nx + nw / 2} y={ny + 44} textAnchor="middle" fill={muted} fontSize="10">
          {sub}
        </text>
      ) : null}
    </g>
  );
}

export function SystemArchitectureDiagram() {
  return (
    <Frame
      title="Kiến trúc hệ thống"
      caption="Browser đi qua Nginx tới frontend và backend; backend dùng PostgreSQL, Redis, OpenRouter; worker thu thập dữ liệu Binance."
    >
      <Box x="20" y="95" w="120" h="60" label="Browser" sub="React UI" />
      <Box x="180" y="85" w="130" h="80" label="Nginx" sub=":8090" fill={panel} />
      <Box x="350" y="25" w="150" h="70" label="Frontend" sub="React/Vite" />
      <Box x="350" y="130" w="150" h="70" label="Backend" sub="FastAPI :8010" />
      <Box x="560" y="25" w="170" h="60" label="PostgreSQL" sub="trader, score, risk" />
      <Box x="560" y="105" w="170" h="60" label="Redis" sub="lock, coordination" fill={panel} />
      <Box x="560" y="185" w="170" h="60" label="OpenRouter" sub="AI report" />
      <Box x="180" y="200" w="130" h="55" label="Worker" sub="collector" fill={panel} />
      <Box x="20" y="200" w="120" h="55" label="Binance API" sub="BAPI" fill={info} />

      <line x1="140" y1="125" x2="178" y2="125" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="310" y1="110" x2="348" y2="75" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="310" y1="140" x2="348" y2="160" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="500" y1="55" x2="558" y2="55" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="500" y1="130" x2="558" y2="130" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="500" y1="175" x2="558" y2="210" stroke={accent} markerEnd="url(#arrow-tech)" />
      <line x1="140" y1="228" x2="178" y2="228" stroke={warn} markerEnd="url(#arrow-tech)" />
      <line x1="310" y1="228" x2="348" y2="175" stroke={warn} markerEnd="url(#arrow-tech)" />

      <defs>
        <marker id="arrow-tech" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill={accent} />
        </marker>
      </defs>
    </Frame>
  );
}

export function DataPipelineDiagram() {
  const rows = [
    ["L0", "Quét universe", "list công khai"],
    ["Tier", "Lọc A/B/C/Excluded", "pre-score"],
    ["L2", "Performance 7/30/90/180D", "published metrics"],
    ["L3", "Detail + position + transfer", "derived metrics"],
    ["L4", "Trade history", "fills, fee"],
    ["Score", "Chuẩn hoá + trọng số", "band + hard filter"],
  ];
  return (
    <Frame
      title="Luồng dữ liệu"
      caption="Collector đi từ universe đến trade history; sau đó quant/scoring tạo metric, score, risk và ranking."
    >
      {rows.map(([step, label, sub], index) => {
        const y = 18 + index * 39;
        return (
          <g key={step}>
            <rect x="20" y={y} width="58" height="28" rx="6" fill={index === 5 ? accent : elevated} stroke={line} />
            <text x="49" y={y + 19} textAnchor="middle" fill={index === 5 ? "var(--bg)" : body} fontSize="11" fontWeight="600">
              {step}
            </text>
            <text x="96" y={y + 19} fill={body} fontSize="12">
              {label}
            </text>
            <text x="560" y={y + 19} fill={muted} fontSize="11">
              {sub}
            </text>
            {index < rows.length - 1 ? (
              <line x1="49" y1={y + 28} x2="49" y2={y + 38} stroke={muted} markerEnd="url(#arrow-flow)" />
            ) : null}
          </g>
        );
      })}
      <defs>
        <marker id="arrow-flow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill={muted} />
        </marker>
      </defs>
    </Frame>
  );
}

export function ScoringPipelineDiagram() {
  return (
    <Frame
      title="Luồng scoring"
      caption="Metric thô được chuẩn hoá theo cohort, gom nhóm, nhân trọng số, cộng lại thành score và ánh xạ sang band."
    >
      <Box x="20" y="80" w="130" h="70" label="Raw metrics" sub="published + derived" />
      <Box x="190" y="80" w="130" h="70" label="Chuẩn hoá" sub="percentile, winsor" fill={panel} />
      <Box x="360" y="40" w="150" h="70" label="7 nhóm" sub="19 component" />
      <Box x="360" y="130" w="150" h="70" label="Trọng số" sub="config version" fill={panel} />
      <Box x="550" y="80" w="170" h="70" label="Score + band" sub="hard filter" fill={accent} />
      <line x1="150" y1="115" x2="188" y2="115" stroke={accent} markerEnd="url(#arrow-score)" />
      <line x1="320" y1="115" x2="358" y2="80" stroke={accent} markerEnd="url(#arrow-score)" />
      <line x1="320" y1="115" x2="358" y2="160" stroke={accent} markerEnd="url(#arrow-score)" />
      <line x1="510" y1="75" x2="548" y2="112" stroke={accent} markerEnd="url(#arrow-score)" />
      <line x1="510" y1="165" x2="548" y2="122" stroke={accent} markerEnd="url(#arrow-score)" />
      <text x="380" y="235" textAnchor="middle" fill={muted} fontSize="11">
        Missing component không bị coi là 0; hard filter chỉ quyết định có xếp hạng hay không
      </text>
      <defs>
        <marker id="arrow-score" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill={accent} />
        </marker>
      </defs>
    </Frame>
  );
}

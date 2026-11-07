import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  CopyFlowDiagram,
  FunnelDiagram,
  MetricAnatomyDiagram,
  RiskEvidenceDiagram,
  WorkflowDiagram,
} from "../components/help/HelpIllustrations";

interface Section {
  id: string;
  title: string;
  keywords: string;
  body: ReactNode;
}

const SECTIONS: Section[] = [
  {
    id: "copy-trading",
    title: "1. Copy trading là gì?",
    keywords: "copy trading lead copier rủi ro vốn trượt giá phí",
    body: (
      <>
        <p>
          Copy trading là cơ chế để tài khoản của bạn tự động sao chép lệnh của một trader khác
          (lead trader). Khi lead mở/đóng vị thế, tài khoản copy làm theo theo tỷ lệ bạn chọn.
        </p>
        <ul>
          <li>Bạn có thể mất một phần hoặc toàn bộ vốn.</li>
          <li>Hiệu suất quá khứ không đảm bảo tương lai.</li>
          <li>Không phải kênh đầu tư được bảo đảm lợi nhuận.</li>
          <li>Có độ trễ, trượt giá và phí; kết quả lead và copier không giống hệt nhau.</li>
        </ul>
        <CopyFlowDiagram />
      </>
    ),
  },
  {
    id: "system-scope",
    title: "2. Hệ thống làm gì và không làm gì?",
    keywords: "auto-trade paper copy tư vấn api giao dịch dữ liệu công khai",
    body: (
      <>
        <p>
          <strong>Làm:</strong> thu thập dữ liệu công khai Binance Futures, tính chỉ số hiệu suất,
          rủi ro, độ tin cậy; xếp hạng và so sánh trader.
        </p>
        <p>
          <strong>Không làm:</strong> không auto-trade, không kết nối API giao dịch của bạn,
          không paper copy, không đưa lời khuyên đầu tư, không hiển thị dữ liệu Binance không có
          (vị thế đang mở, PnL từng copier, funding).
        </p>
      </>
    ),
  },
  {
    id: "screens",
    title: "3. Cách đọc từng màn hình",
    keywords: "screener detail compare risk ranking data health màn hình bảng",
    body: (
      <>
        <ul>
        <li>
          <strong>Bộ lọc trader</strong> — lọc universe theo nhóm, ROI, MDD, Sharpe, WinRate,
          đòn bẩy, rủi ro.
        </li>
        <li>
          <strong>Chi tiết trader</strong> — 10 chỉ số, phân rã điểm, cảnh báo rủi ro, vị thế,
          giao dịch, nạp/rút.
        </li>
        <li>
          <strong>So sánh</strong> — so sánh 2–4 trader; tương quan là “ước tính”.
        </li>
        <li>
          <strong>Cảnh báo rủi ro</strong> — cảnh báo R01–R11 kèm bằng chứng.
        </li>
        <li>
          <strong>Bảng xếp hạng</strong> — Tổng hợp / Rủi ro thấp / Độ ổn định.
        </li>
        <li>
          <strong>Sức khỏe dữ liệu</strong> — độ phủ, lần chạy bộ thu thập, dữ liệu cũ.
        </li>
      </ul>
      <RiskEvidenceDiagram />
      </>
    ),
  },
  {
    id: "glossary",
    title: "4. Từ điển thuật ngữ",
    keywords: "roi pnl mdd sharpe winrate profit factor payoff aum leverage confidence low sample thuật ngữ",
    body: (
      <>
        <ul>
        <li>
          <strong>ROI</strong> — tỷ suất sinh lời 7/30/90/180 ngày.
        </li>
        <li>
          <strong>PnL</strong> — lợi nhuận/lỗ tuyệt đối (USDT).
        </li>
        <li>
          <strong>MDD</strong> — mức sụt giảm lớn nhất từ đỉnh, dùng số Binance công bố.
        </li>
        <li>
          <strong>Sharpe</strong> — lợi nhuận điều chỉnh biến động; null = chưa đủ dữ liệu.
        </li>
        <li>
          <strong>WinRate (order)</strong> — order thắng / tổng order đóng;{" "}
          <strong>WinRate (position)</strong> — vị thế thắng / tổng vị thế đóng.
        </li>
        <li>
          <strong>Profit Factor</strong> — tổng lãi / |tổng lỗ|; <strong>Payoff</strong> — lãi TB / |lỗ TB|.
        </li>
        <li>
          <strong>AUM</strong> — tổng tài sản quản lý; <strong>Copy AUM</strong> — vốn copier.
        </li>
        <li>
          <strong>Leverage</strong> — đòn bẩy từ position-history; <strong>Confidence</strong> — độ tin cậy 0–1.
        </li>
        <li>
          <strong>Mẫu nhỏ (Low sample)</strong> — mẫu nhỏ, kết luận kém tin cậy.
        </li>
      </ul>
      <MetricAnatomyDiagram />
      </>
    ),
  },
  {
    id: "tier",
    title: "5. Nhóm và lý do loại",
    keywords: "tier excluded watch qualified high reason runtime aum slot totalorder",
    body: (
      <>
        <p>
          Cao (A) / Đạt (B) / Theo dõi (C) / Bị loại. B và A ban đầu là giới hạn trên ở tầng list,
          sau đó được hạ theo tổng số lệnh.
        </p>
        <p>
          <strong>Bị loại không hẳn là trader xấu.</strong> Có thể chỉ vì số ngày hoạt động &lt; 30,
          AUM &lt; 5.000, không giao dịch 7 ngày, hết slot hoặc thiếu dữ liệu. Luôn đọc
          <em> lý do loại</em>.
        </p>
        <FunnelDiagram />
      </>
    ),
  },
  {
    id: "data",
    title: "6. Nguồn dữ liệu: Binance công bố, hệ thống tính, ước tính",
    keywords: "published derived estimated binance công bố hệ thống tính ước tính null open positions funding slippage nguồn dữ liệu",
    body: (
      <>
        <ul>
          <li>
            <strong>Binance công bố (Published)</strong> — Binance trả trực tiếp (ROI, MDD, Sharpe, WinRate…).
          </li>
          <li>
            <strong>Hệ thống tính (Derived)</strong> — tính từ vị thế/giao dịch (profit factor, thời gian giữ, chi phí…).
          </li>
          <li>
            <strong>Ước tính (Estimated)</strong> — ước tính từ chartItems (drawdown, tương quan): chỉ tham khảo.
          </li>
        </ul>
        <p>
          Không có dữ liệu: vị thế đang mở, PnL từng copier, funding, slippage, giá thanh lý.
          <strong> null</strong> nghĩa là không có dữ liệu, không phải 0.
        </p>
      </>
    ),
  },
  {
    id: "steps",
    title: "7. Quy trình 5 bước cho người mới",
    keywords: "quy trình checklist copy vốn 7 ngày lọc so sánh risk",
    body: (
      <>
        <ol>
          <li>Mở Bộ lọc trader, giữ bộ lọc mặc định (số ngày ≥ 30, số lệnh ≥ 20).</li>
          <li>Đọc Chi tiết trader: 10 chỉ số, phân rã điểm, cảnh báo rủi ro, dữ liệu còn thiếu.</li>
          <li>So sánh 2–4 ứng viên; xem tương quan và mức tập trung.</li>
          <li>Kiểm tra Cảnh báo rủi ro cho cảnh báo nghiêm trọng.</li>
          <li>Tự quyết định, bắt đầu nhỏ, theo dõi định kỳ.</li>
        </ol>
        <p className="font-medium text-strong">Checklist trước khi copy:</p>
        <ul>
          <li>Hiểu có thể mất vốn.</li>
          <li>Đã đọc MDD, leverage, worst position ROI.</li>
          <li>Biết dữ liệu nào đang thiếu.</li>
          <li>Không copy chỉ vì ROI cao.</li>
          <li>Đã xem lại sau ít nhất 7 ngày.</li>
        </ul>
        <WorkflowDiagram />
      </>
    ),
  },
  {
    id: "faq",
    title: "8. Câu hỏi thường gặp & miễn trừ trách nhiệm",
    keywords: "faq câu hỏi thường gặp sharpe roi điểm tương quan miễn trừ tư vấn n/a",
    body: (
      <>
        <p>
          <strong>Sharpe N/A?</strong> Chưa đủ mẫu hoặc Binance không công bố; không chấm 0.
        </p>
        <p>
          <strong>ROI cao vẫn bị loại?</strong> Có thể số ngày hoạt động ngắn, MDD cao, mẫu nhỏ
          hoặc thiếu dữ liệu.
        </p>
        <p>
          <strong>Điểm có phải khuyến nghị?</strong> Không. Điểm chỉ xếp hạng tương đối theo cấu hình.
        </p>
        <p>
          <strong>Tương quan dùng để chia vốn?</strong> Không. Đây là ước tính, bị ảnh hưởng bởi
          nạp/rút.
        </p>
        <p className="rounded-lg border border-warn/30 bg-warn/10 p-3 text-warn">
          Miễn trừ trách nhiệm: công cụ phân tích dữ liệu công khai, không phải tư vấn đầu tư.
          Copy trading có rủi ro mất toàn bộ vốn. Bạn tự chịu trách nhiệm với quyết định của mình.
        </p>
      </>
    ),
  },
];

export default function HelpPage() {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(SECTIONS[0].id);
  const [progress, setProgress] = useState(0);
  const [tocOpen, setTocOpen] = useState(false);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return SECTIONS;
    return SECTIONS.filter((section) =>
      `${section.title} ${section.keywords} ${String(section.id)}`
        .toLowerCase()
        .includes(needle),
    );
  }, [query]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries.find((entry) => entry.isIntersecting);
        if (hit) setActive(hit.target.id);
      },
      { rootMargin: "-25% 0px -60% 0px", threshold: 0 },
    );
    visible.forEach((section) => {
      const element = document.getElementById(section.id);
      if (element) observer.observe(element);
    });
    return () => observer.disconnect();
  }, [visible]);

  useEffect(() => {
    const onScroll = () => {
      const height = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(height > 0 ? Math.min(100, Math.round((window.scrollY / height) * 100)) : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="space-y-5">
      <div className="print-hidden sticky top-0 z-10 -mx-1 h-1 overflow-hidden rounded bg-line">
        <div
          className="h-full bg-accent transition-[width] duration-150"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="print-hidden">
        <h1 className="text-3xl font-semibold tracking-tight">Hướng dẫn</h1>
        <p className="mt-2 text-muted">
          Dành cho người chưa biết copy trading. Đọc 5–10 phút trước khi dùng Bộ lọc trader.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Tìm trong hướng dẫn..."
            aria-label="Tìm trong hướng dẫn"
            className="w-72 rounded-lg border border-line bg-app px-3 py-2 text-strong"
          />
          <Link to="/screener" className="rounded-lg border border-line px-3 py-2 text-sm text-body">
            Mở Bộ lọc trader
          </Link>
          <button
            type="button"
            onClick={() => window.print()}
            className="rounded-lg border border-line px-3 py-2 text-sm text-body"
          >
            In / lưu PDF
          </button>
          <button
            type="button"
            onClick={() => setTocOpen(!tocOpen)}
            className="rounded-lg border border-line px-3 py-2 text-sm text-body lg:hidden"
            aria-expanded={tocOpen}
          >
            {tocOpen ? "Ẩn mục lục" : "Mục lục"}
          </button>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[260px_1fr]">
        <nav
          className={`${tocOpen ? "block" : "hidden"} print-hidden h-fit rounded-2xl border border-line bg-panel p-4 lg:sticky lg:top-6 lg:block`}
          aria-label="Mục lục hướng dẫn"
        >
          <p className="text-xs uppercase tracking-wide text-faint">Mục lục</p>
          <ol className="mt-3 space-y-1 text-sm">
            {SECTIONS.map((section, index) => {
              const isActive = active === section.id;
              return (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    onClick={() => setTocOpen(false)}
                    aria-current={isActive ? "true" : undefined}
                    className={`flex items-start gap-2 rounded-lg border-l-2 px-2 py-1.5 transition ${
                      isActive
                        ? "border-accent bg-accent/10 text-accent"
                        : "border-transparent text-body hover:bg-elevated hover:text-strong"
                    }`}
                  >
                    <span className="mt-0.5 text-[10px] text-faint">{index + 1}</span>
                    <span>{section.title.replace(/^\d+\.\s*/, "")}</span>
                  </a>
                </li>
              );
            })}
          </ol>
          <p className="mt-4 border-t border-line pt-3 text-xs text-faint">
            Đã đọc {progress}% · cập nhật khi bạn cuộn
          </p>
        </nav>

        <article className="space-y-5">
          {visible.map((section) => (
            <section
              key={section.id}
              id={section.id}
              className="scroll-mt-24 rounded-2xl border border-line bg-panel p-5"
            >
              <h2 className="text-lg font-semibold text-strong">{section.title}</h2>
              <div className="mt-3 space-y-2 text-sm leading-6 text-body [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-5">
                {section.body}
              </div>
            </section>
          ))}
          {!visible.length ? (
            <p className="rounded-2xl border border-line bg-panel p-6 text-muted">
              Không tìm thấy mục phù hợp.
            </p>
          ) : null}
        </article>
      </div>

      {progress > 5 ? (
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="print-hidden fixed bottom-6 right-6 z-20 rounded-full border border-line bg-panel px-4 py-2 text-sm text-body shadow-lg hover:bg-elevated"
          aria-label="Về đầu trang"
        >
          ↑ Đầu trang
        </button>
      ) : null}
    </div>
  );
}

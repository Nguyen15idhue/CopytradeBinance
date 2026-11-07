import { Source } from "../ui";

const LIMITS: Array<[string, string[]]> = [
  [
    "Dữ liệu",
    [
      "Không có vị thế đang mở.",
      "Không có PnL từng copier.",
      "Không có funding, slippage, giá thanh lý.",
      "Không có lý do lead vào/ra lệnh.",
    ],
  ],
  [
    "AI",
    [
      "Primary model có lúc trả thiếu field/JSON lỗi.",
      "Fallback vẫn có thể sai.",
      "Không đảm bảo phát hiện mọi rủi ro.",
    ],
  ],
  ["Frontend", ["Bundle lớn do chart library.", "Cần code-split thêm ở phase sau."]],
  [
    "Vận hành",
    [
      "Recreate backend có thể cần restart nginx do cache DNS.",
      "Ranking snapshot cũ vẫn giữ; UI chỉ hiển thị bản mới nhất.",
      "Dữ liệu thô có thể tăng dung lượng; cần theo dõi.",
    ],
  ],
];

export default function GioiHanSection() {
  return (
    <div className="space-y-4">
      {LIMITS.map(([group, items]) => (
        <div key={group}>
          <h3 className="text-base font-semibold text-strong">{group}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-body">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
      <Source>SESSION.md, docs/kehoach/PHASE5-REPORT.md</Source>
    </div>
  );
}

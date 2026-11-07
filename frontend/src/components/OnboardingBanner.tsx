import { useState } from "react";
import { Link } from "react-router-dom";

const KEY = "ct_help_banner_dismissed";

export default function OnboardingBanner() {
  const [hidden, setHidden] = useState(() => localStorage.getItem(KEY) === "1");
  if (hidden) return null;

  return (
    <div className="print-hidden flex flex-wrap items-center gap-3 rounded-xl border border-info/30 bg-info/10 px-4 py-3 text-sm">
      <span className="text-body">
        Mới bắt đầu? Đọc hướng dẫn copy trading và cách đọc chỉ số trước khi lọc trader.
      </span>
      <Link to="/help" className="font-medium text-info hover:underline">
        Đọc hướng dẫn →
      </Link>
      <button
        type="button"
        onClick={() => {
          localStorage.setItem(KEY, "1");
          setHidden(true);
        }}
        className="ml-auto rounded border border-line px-2 py-1 text-xs text-muted hover:text-body"
      >
        Đã hiểu
      </button>
    </div>
  );
}

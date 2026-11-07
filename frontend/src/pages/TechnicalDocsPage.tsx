import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { TECH_GROUPS, TECH_SECTIONS } from "../content/technical";
import type { TocEntry } from "../content/technical/types";

const ALL_GROUPS = "Tất cả";

export default function TechnicalDocsPage() {
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState<string>(ALL_GROUPS);
  const [tocOpen, setTocOpen] = useState(false);
  const [active, setActive] = useState(TECH_SECTIONS[0].id);
  const [progress, setProgress] = useState(0);
  const [toc, setToc] = useState<TocEntry[]>([]);
  const articleRef = useRef<HTMLElement | null>(null);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return TECH_SECTIONS.filter((section) => {
      const inGroup = group === ALL_GROUPS || section.group === group;
      if (!inGroup) return false;
      if (!needle) return true;
      return `${section.title} ${section.keywords}`.toLowerCase().includes(needle);
    });
  }, [query, group]);

  const visibleGroups = useMemo(
    () =>
      TECH_GROUPS.map((name) => ({
        name,
        sections: visible.filter((section) => section.group === name),
      })).filter((item) => item.sections.length > 0),
    [visible],
  );

  useEffect(() => {
    const article = articleRef.current;
    if (!article) return;
    const headings = Array.from(article.querySelectorAll<HTMLElement>("h2[id], h3[id]"));
    setToc(
      headings.map((heading) => {
        const wrapper = heading.closest<HTMLElement>("[data-section-id]");
        return {
          id: heading.id,
          title: heading.textContent?.replace(/^#+\s*/, "").trim() ?? "",
          level: heading.tagName === "H2" ? 2 : 3,
          sectionId: wrapper?.dataset.sectionId ?? heading.id,
        };
      }),
    );
  }, [visible]);

  useEffect(() => {
    const article = articleRef.current;
    if (!article) return;
    const headings = Array.from(article.querySelectorAll<HTMLElement>("h2[id], h3[id]"));
    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries.find((entry) => entry.isIntersecting);
        if (hit) setActive(hit.target.id);
      },
      { rootMargin: "-20% 0px -65% 0px", threshold: 0 },
    );
    headings.forEach((heading) => observer.observe(heading));
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

  useEffect(() => {
    if (!window.location.hash) return;
    const id = decodeURIComponent(window.location.hash.slice(1));
    const frame = requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ block: "start" });
    });
    return () => cancelAnimationFrame(frame);
  }, [visible]);

  function resetFilters() {
    setQuery("");
    setGroup(ALL_GROUPS);
    setTocOpen(false);
  }

  return (
    <div className="space-y-5">
      <div className="print-hidden sticky top-0 z-10 -mx-1 h-1 overflow-hidden rounded bg-line">
        <div
          className="h-full bg-accent transition-[width] duration-150"
          style={{ width: `${progress}%` }}
        />
      </div>

      <header className="print-hidden flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">
            Tài liệu kỹ thuật
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">CopytradeBinance</h1>
          <p className="mt-2 max-w-3xl text-muted">
            Kiến trúc, dữ liệu, tier, chỉ số, scoring, risk, AI, API và vận hành. Nội dung tĩnh,
            không phụ thuộc dữ liệu live.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full border border-line px-3 py-1 text-muted">
            Phase 5 · 07/11/2026
          </span>
          <Link to="/help" className="rounded-lg border border-line px-3 py-2 text-body">
            Mở Hướng dẫn
          </Link>
          <button
            type="button"
            onClick={() => window.print()}
            className="rounded-lg border border-line px-3 py-2 text-body"
          >
            In / lưu PDF
          </button>
          <button
            type="button"
            onClick={() => setTocOpen(!tocOpen)}
            className="rounded-lg border border-line px-3 py-2 text-body lg:hidden"
            aria-expanded={tocOpen}
          >
            {tocOpen ? "Ẩn mục lục" : "Mục lục"}
          </button>
        </div>
      </header>

      <div className="print-hidden flex flex-wrap items-center gap-2">
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setTocOpen(false);
          }}
          placeholder="Tìm trong tài liệu..."
          aria-label="Tìm trong tài liệu kỹ thuật"
          className="w-full max-w-sm rounded-lg border border-line bg-app px-3 py-2 text-strong"
        />
        <div className="flex flex-wrap gap-1.5 text-xs">
          {[ALL_GROUPS, ...TECH_GROUPS].map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => {
                setGroup(name);
                setTocOpen(false);
              }}
              className={`rounded-full border px-3 py-1.5 ${
                group === name
                  ? "border-accent/40 bg-accent/10 text-accent"
                  : "border-line text-body"
              }`}
            >
              {name}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-faint">
          {visible.length}/{TECH_SECTIONS.length} mục
        </span>
      </div>

      <div className="grid gap-5 lg:grid-cols-[290px_1fr]">
        <nav
          className={`${tocOpen ? "block" : "hidden"} print-hidden h-fit rounded-2xl border border-line bg-panel p-4 lg:sticky lg:top-6 lg:block`}
          aria-label="Mục lục tài liệu kỹ thuật"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-faint">Mục lục</p>
            <span className="text-[10px] text-faint">{progress}%</span>
          </div>
          <div className="mt-3 max-h-[calc(100vh-9rem)] space-y-4 overflow-y-auto pr-1">
            {visibleGroups.map(({ name, sections }) => (
              <div key={name}>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-faint">
                  {name}
                </p>
                <ul className="space-y-0.5 text-sm">
                  {sections.map((section) => {
                    const isActive = active === section.id;
                    const children = toc.filter(
                      (item) => item.sectionId === section.id && item.level === 3,
                    );
                    return (
                      <li key={section.id}>
                        <a
                          href={`#${section.id}`}
                          onClick={() => setTocOpen(false)}
                          aria-current={isActive ? "location" : undefined}
                          className={`flex items-start gap-2 rounded-lg border-l-2 px-2 py-1.5 transition ${
                            isActive
                              ? "border-accent bg-accent/10 text-accent"
                              : "border-transparent text-body hover:bg-elevated hover:text-strong"
                          }`}
                        >
                          <span className="mt-0.5 text-[10px] text-faint">
                            {String(section.order).padStart(2, "0")}
                          </span>
                          <span>{section.title}</span>
                        </a>
                        {children.length ? (
                          <ul className="ml-6 space-y-0.5 border-l border-line pl-2">
                            {children.map((child) => (
                              <li key={child.id}>
                                <a
                                  href={`#${child.id}`}
                                  onClick={() => setTocOpen(false)}
                                  aria-current={active === child.id ? "location" : undefined}
                                  className={`block rounded px-1.5 py-1 text-xs ${
                                    active === child.id
                                      ? "text-accent"
                                      : "text-muted hover:text-body"
                                  }`}
                                >
                                  {child.title}
                                </a>
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
          <p className="mt-4 border-t border-line pt-3 text-xs text-faint">
            Đã đọc {progress}% · anchor cố định cho từng mục
          </p>
        </nav>

        <article ref={articleRef} className="tech-article min-w-0 space-y-5">
          {visible.length === 0 ? (
            <div className="rounded-2xl border border-line bg-panel p-8 text-center">
              <p className="text-body">Không có mục nào khớp từ khóa.</p>
              <button
                type="button"
                onClick={() => {
                  resetFilters();
                }}
                className="mt-3 rounded-lg border border-line px-3 py-1.5 text-sm text-body"
              >
                Xóa bộ lọc
              </button>
            </div>
          ) : (
            visible.map(({ id, title, order, Component }) => (
              <section
                key={id}
                data-section-id={id}
                className="tech-section min-w-0 scroll-mt-24 rounded-2xl border border-line bg-panel p-5"
              >
                <div className="flex items-start gap-3">
                  <span className="rounded-lg border border-line bg-elevated px-2 py-1 font-mono text-[10px] text-faint">
                    {String(order).padStart(2, "0")}
                  </span>
                  <h2 id={id} className="scroll-mt-24 text-xl font-semibold text-strong">
                    {title}
                  </h2>
                </div>
                <div className="mt-4">
                  <Component />
                </div>
              </section>
            ))
          )}
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

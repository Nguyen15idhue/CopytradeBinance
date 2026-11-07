import type { ReactNode } from "react";

export function Callout({
  tone = "info",
  title,
  children,
}: {
  tone?: "info" | "warn" | "danger" | "accent";
  title: string;
  children: ReactNode;
}) {
  const styles = {
    info: "border-info/30 bg-info/10",
    warn: "border-warn/30 bg-warn/10",
    danger: "border-danger/30 bg-danger/10",
    accent: "border-accent/30 bg-accent/10",
  }[tone];
  const titleStyles = {
    info: "text-info",
    warn: "text-warn",
    danger: "text-danger",
    accent: "text-accent",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 text-sm ${styles}`}>
      <p className={`text-xs font-semibold uppercase tracking-wide ${titleStyles}`}>{title}</p>
      <div className="mt-1 text-body">{children}</div>
    </div>
  );
}

export function Formula({ children }: { children: ReactNode }) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
      {children}
    </pre>
  );
}

export function Source({ children }: { children: ReactNode }) {
  return (
    <p className="mt-5 border-t border-line pt-2 text-[11px] text-faint">
      Nguồn: {children}
    </p>
  );
}

export function Table({ head, children }: { head: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="border-b border-line bg-elevated/60 text-xs uppercase tracking-wide text-faint">
          <tr>
            {head.map((item) => (
              <th key={item} className="px-3 py-2">
                {item}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
    </div>
  );
}

import { Fragment, type ReactNode } from "react";

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`|\[[^\]]+?\]\((?:https?:\/\/)[^)]+?\))/g;
  let last = 0;
  let index = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0;
    if (start > last) parts.push(text.slice(last, start));
    const token = match[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={`${keyPrefix}-${index}`}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      parts.push(
        <code key={`${keyPrefix}-${index}`} className="rounded bg-app px-1 text-[13px]">
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("[")) {
      const label = token.slice(1, token.indexOf("]"));
      const url = token.slice(token.indexOf("](") + 2, -1);
      parts.push(
        <a
          key={`${keyPrefix}-${index}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-info underline"
        >
          {label}
        </a>,
      );
    } else {
      parts.push(<em key={`${keyPrefix}-${index}`}>{token.slice(1, -1)}</em>);
    }
    index += 1;
    last = start + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function stripPipes(line: string): string {
  return line.trim().replace(/^\|+|\|+$/g, "");
}

function isTableDivider(line: string): boolean {
  const cells = stripPipes(line).split("|").map((cell: string) => cell.trim());
  return cells.length > 0 && cells.every((cell) => /^:?-+:?$/.test(cell));
}

export default function Markdown({ text }: { text: string }) {
  const lines = (text || "").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      const buf: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        buf.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push(
        <pre key={key++} className="overflow-x-auto rounded-lg bg-app p-2 text-xs">
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }
    if (
      trimmed.startsWith("|") &&
      i + 1 < lines.length &&
      isTableDivider(lines[i + 1])
    ) {
      const headers = stripPipes(trimmed).split("|").map((cell: string) => cell.trim());
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(stripPipes(lines[i]).split("|").map((cell: string) => cell.trim()));
        i += 1;
      }
      blocks.push(
        <div key={key++} className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                {headers.map((head, index) => (
                  <th key={index} className="border border-line bg-app px-2 py-1 text-left">
                    {renderInline(head, `th-${key}-${index}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {headers.map((_, cellIndex) => (
                    <td key={cellIndex} className="border border-line px-2 py-1">
                      {renderInline(row[cellIndex] ?? "", `td-${key}-${rowIndex}-${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      const content = renderInline(heading[2], `h-${key}`);
      const cls = "font-semibold text-strong " + (level <= 2 ? "text-sm" : "text-[13px]");
      blocks.push(<p key={key++} className={cls}>{content}</p>);
      i += 1;
      continue;
    }
    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      blocks.push(<hr key={key++} className="border-line" />);
      i += 1;
      continue;
    }
    if (/^([-*])\s+/.test(trimmed) || /^\d+[.)]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (
        i < lines.length &&
        (/^([-*])\s+/.test(lines[i].trim()) || /^\d+[.)]\s+/.test(lines[i].trim()))
      ) {
        items.push(lines[i].trim().replace(/^([-*]|\d+[.)])\s+/, ""));
        i += 1;
      }
      blocks.push(
        <ul key={key++} className="list-disc space-y-1 pl-5">
          {items.map((item, index) => (
            <li key={index}>{renderInline(item, `li-${key}-${index}`)}</li>
          ))}
        </ul>,
      );
      continue;
    }
    if (trimmed === "") {
      i += 1;
      continue;
    }
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trim().startsWith("|") &&
      !lines[i].trim().startsWith("#") &&
      !lines[i].trim().startsWith("```") &&
      !/^([-*])\s+/.test(lines[i].trim()) &&
      !/^\d+[.)]\s+/.test(lines[i].trim())
    ) {
      para.push(lines[i].trim());
      i += 1;
    }
    blocks.push(
      <p key={key++}>
        {para.map((part, index) => (
          <Fragment key={index}>
            {index > 0 ? <br /> : null}
            {renderInline(part, `p-${key}-${index}`)}
          </Fragment>
        ))}
      </p>,
    );
  }
  return <div className="space-y-2 text-sm leading-relaxed">{blocks}</div>;
}

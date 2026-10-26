/**
 * FormattedAnswer — minimal, safe renderer for AURA's plain-text answers.
 * Supports headings, paragraphs, bullets, numbered lists, inline code and
 * emphasis. No HTML injection: every token is a React element.
 */

import { Fragment, type ReactNode } from "react";

interface Block {
  type: "h" | "p" | "ul" | "ol" | "pre";
  lines: string[];
}

function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let current: Block | null = null;

  function flush() {
    if (current) {
      blocks.push(current);
      current = null;
    }
  }

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trimEnd();
    if (line.trim() === "") {
      flush();
      continue;
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line.trim());
    const bullet = /^([-*•])\s+(.+)$/.exec(line.trim());
    const numbered = /^\d+[.)]\s+(.+)$/.exec(line.trim());
    const fence = /^```/.test(line.trim());

    if (heading) {
      flush();
      blocks.push({ type: "h", lines: [heading[2]] });
    } else if (fence) {
      flush();
      current = { type: "pre", lines: [] };
    } else if (current?.type === "pre") {
      if (/^```/.test(line.trim())) flush();
      else current.lines.push(line);
    } else if (bullet) {
      if (current?.type !== "ul") {
        flush();
        current = { type: "ul", lines: [] };
      }
      current.lines.push(bullet[2]);
    } else if (numbered) {
      if (current?.type !== "ol") {
        flush();
        current = { type: "ol", lines: [] };
      }
      current.lines.push(numbered[1]);
    } else {
      if (current?.type === "ul" || current?.type === "ol") flush();
      if (current?.type !== "p") {
        flush();
        current = { type: "p", lines: [] };
      }
      current.lines.push(line);
    }
  }
  flush();
  return blocks;
}

function inline(text: string): ReactNode[] {
  // Split **bold**, *italic*, and `code` spans into React fragments.
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function FormattedAnswer({ text }: { text: string }) {
  const blocks = parseBlocks(text);
  return (
    <div className="answer-text">
      {blocks.map((block, i) => {
        if (block.type === "h") {
          return <h4 key={i}>{inline(block.lines[0])}</h4>;
        }
        if (block.type === "p") {
          return <p key={i}>{block.lines.map((l) => inline(l))}</p>;
        }
        if (block.type === "ul") {
          return (
            <ul key={i}>
              {block.lines.map((l, j) => (
                <li key={j}>{inline(l)}</li>
              ))}
            </ul>
          );
        }
        if (block.type === "ol") {
          return (
            <ol key={i}>
              {block.lines.map((l, j) => (
                <li key={j}>{inline(l)}</li>
              ))}
            </ol>
          );
        }
        return (
          <pre key={i}>
            <code>{block.lines.join("\n")}</code>
          </pre>
        );
      })}
    </div>
  );
}
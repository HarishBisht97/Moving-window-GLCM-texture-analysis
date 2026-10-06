import type { ReactNode } from "react";

/** Inline **bold** only; everything else is rendered as plain text (no HTML injection). */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-slate-900">
        {part.slice(2, -2)}
      </strong>
    ) : (
      part
    ),
  );
}

/** Minimal renderer for the backend's interpretation Markdown (### headings, - bullets, paragraphs). */
export function MarkdownText({ source }: { source: string }) {
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="ml-4 list-disc space-y-1.5">
          {bullets.map((b, i) => (
            <li key={i}>{inline(b)}</li>
          ))}
        </ul>,
      );
      bullets = [];
    }
  };
  for (const raw of source.split("\n")) {
    const line = raw.trim();
    if (!line) {
      flush();
    } else if (line.startsWith("### ")) {
      flush();
      blocks.push(
        <h4 key={`h-${blocks.length}`} className="pt-2 text-sm font-semibold text-slate-900">
          {line.slice(4)}
        </h4>,
      );
    } else if (line.startsWith("- ")) {
      bullets.push(line.slice(2));
    } else {
      flush();
      blocks.push(<p key={`p-${blocks.length}`}>{inline(line)}</p>);
    }
  }
  flush();
  return <div className="space-y-2 text-xs leading-relaxed text-slate-700">{blocks}</div>;
}

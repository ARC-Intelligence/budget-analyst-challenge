import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";

export type MessageData = {
  role: "user" | "assistant";
  content: string;
  error?: boolean;
};

const markdownComponents = {
  p: ({ children }: { children?: ReactNode }) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  ul: ({ children }: { children?: ReactNode }) => (
    <ul className="mb-2 list-disc space-y-1 pl-4 last:mb-0">{children}</ul>
  ),
  ol: ({ children }: { children?: ReactNode }) => (
    <ol className="mb-2 list-decimal space-y-1 pl-4 last:mb-0">{children}</ol>
  ),
  li: ({ children }: { children?: ReactNode }) => <li>{children}</li>,
  strong: ({ children }: { children?: ReactNode }) => (
    <strong className="font-semibold">{children}</strong>
  ),
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a href={href} className="underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }: { children?: ReactNode }) => (
    <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.9em]">
      {children}
    </code>
  ),
  pre: ({ children }: { children?: ReactNode }) => (
    <pre className="mb-2 overflow-x-auto rounded-md bg-muted p-2 font-mono text-xs last:mb-0">
      {children}
    </pre>
  ),
};

export function Message({ role, content, error }: MessageData) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg bg-muted px-3 py-2 text-sm whitespace-pre-wrap">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div
        className={
          error
            ? "max-w-[85%] rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
            : "max-w-[85%] text-sm"
        }
      >
        {error ? (
          content
        ) : content ? (
          <ReactMarkdown components={markdownComponents}>{content}</ReactMarkdown>
        ) : (
          <span className="text-muted-foreground">…</span>
        )}
      </div>
    </div>
  );
}

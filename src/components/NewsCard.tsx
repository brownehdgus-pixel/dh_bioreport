import type { NewsItem } from "@/data/types";
import { SECTION_LABELS } from "@/data/types";

function formatDate(dateStr: string) {
  const [y, m, d] = dateStr.split("-");
  return `${y}.${m}.${d}`;
}

type Props = {
  item: NewsItem;
};

export function NewsCard({ item }: Props) {
  return (
    <article className="rounded-lg border border-memo-border bg-memo-surface p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="rounded bg-memo-accentLight px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-memo-accent">
          {SECTION_LABELS[item.section]}
        </span>
        <span className="rounded border border-memo-border bg-memo-bg px-1.5 py-0.5 text-[10px] text-memo-muted">
          {item.eventType}
        </span>
        <span className="text-[11px] text-memo-muted">{item.source}</span>
        <span className="text-memo-border">·</span>
        <time dateTime={item.date} className="text-[11px] tabular-nums text-memo-muted">
          {formatDate(item.date)}
        </time>
      </div>

      <h2 className="font-serif text-[15px] font-semibold leading-snug text-memo-ink">
        {item.title}
      </h2>

      <div className="mt-3 space-y-3">
        <div>
          <h3 className="mb-1 text-[10px] font-bold uppercase tracking-wider text-memo-muted">
            요약
          </h3>
          <p className="text-[13px] leading-relaxed text-memo-ink/90">{item.summary}</p>
        </div>

        <div>
          <h3 className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-memo-muted">
            키워드
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {item.keywords.map((kw) => (
              <span
                key={kw}
                className="rounded border border-memo-border bg-memo-bg px-2 py-0.5 text-[11px] text-memo-muted"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      </div>

      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-md border border-memo-accent bg-memo-accent px-4 py-2.5 text-sm font-medium text-white transition-colors active:bg-memo-accent/90"
      >
        원문 보기
        <svg
          className="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
          />
        </svg>
      </a>
    </article>
  );
}

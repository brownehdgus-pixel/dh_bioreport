import type { DailyReport } from "@/data/types";
import { formatReportDate } from "@/data/types";

type Props = {
  report: DailyReport;
};

export function BriefingSection({ report }: Props) {
  const highlights = report.executiveHighlights;
  const useHighlights = highlights && highlights.length > 0;

  return (
    <section className="border-b border-memo-border bg-memo-surface px-4 pb-5 pt-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.2em] text-memo-accent">
            Daily Bio
          </p>
          <h1 className="mt-1 font-serif text-2xl font-semibold leading-snug text-memo-ink">
            {report.title}
          </h1>
        </div>
        <time
          dateTime={report.reportDate}
          className="shrink-0 rounded border border-memo-border bg-memo-bg px-2 py-1 text-[11px] text-memo-muted"
        >
          {formatReportDate(report.reportDate)}
        </time>
      </div>

      <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-memo-muted">
        Executive Highlights
      </p>

      {useHighlights ? (
        <ol className="space-y-4 border-l-2 border-memo-accent/30 pl-4">
          {highlights!.map((h) => (
            <li key={h.rank} className="relative">
              <span className="absolute -left-[calc(1rem+5px)] top-1.5 flex h-2 w-2 rounded-full bg-memo-accent" />
              <p className="text-[13px] font-semibold leading-snug text-memo-ink">
                <span className="mr-1.5 text-memo-accent">{h.rank}.</span>
                {h.headline}
              </p>
              <p className="mt-1 text-[13px] leading-relaxed text-memo-ink/85">
                {h.investmentTakeaway}
              </p>
            </li>
          ))}
        </ol>
      ) : (
        <ol className="space-y-3 border-l-2 border-memo-accent/30 pl-4">
          {report.summaryLines.map((line, index) => (
            <li key={index} className="relative text-[13px] leading-relaxed text-memo-ink">
              <span className="absolute -left-[calc(1rem+5px)] top-1.5 flex h-2 w-2 rounded-full bg-memo-accent" />
              <span className="mr-1.5 font-semibold text-memo-accent">{index + 1}.</span>
              {line}
            </li>
          ))}
        </ol>
      )}

      <p className="mt-4 text-[11px] italic text-memo-muted">
        Investment intelligence · 개인 열람용 · data/news.json
      </p>
    </section>
  );
}

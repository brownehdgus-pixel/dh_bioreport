import Link from "next/link";
import type { DailyReport } from "@/data/types";
import { formatReportDate } from "@/data/types";

const PREVIEW_LINES = 2;

type Props = {
  report: DailyReport;
};

export function ReportListCard({ report }: Props) {
  const previewLines = report.summaryLines.slice(0, PREVIEW_LINES);
  const newsCount = report.items.length;

  return (
    <li>
      <Link
        href={`/reports/${report.reportDate}`}
        className="block rounded-xl border border-memo-border bg-memo-surface p-4 shadow-sm transition-colors active:bg-memo-bg"
      >
        <div className="mb-2 flex items-start justify-between gap-3">
          <time
            dateTime={report.reportDate}
            className="shrink-0 rounded border border-memo-border bg-memo-bg px-2 py-1 text-[11px] font-medium text-memo-accent"
          >
            {formatReportDate(report.reportDate)}
          </time>
          <span className="rounded-full bg-memo-accentLight px-2.5 py-0.5 text-[11px] font-semibold text-memo-accent">
            {newsCount}건
          </span>
        </div>

        <h2 className="font-serif text-base font-semibold leading-snug text-memo-ink">
          {report.title}
        </h2>

        <ul className="mt-3 space-y-2 border-t border-memo-border pt-3">
          {previewLines.map((line, index) => (
            <li
              key={index}
              className="line-clamp-2 text-[13px] leading-relaxed text-memo-ink/85"
            >
              <span className="mr-1 font-semibold text-memo-accent">{index + 1}.</span>
              {line}
            </li>
          ))}
        </ul>

        {report.summaryLines.length > PREVIEW_LINES && (
          <p className="mt-2 text-[11px] text-memo-muted">
            +{report.summaryLines.length - PREVIEW_LINES}줄 더 보기
          </p>
        )}

        <span className="mt-3 flex items-center gap-1 text-xs font-medium text-memo-accent">
          리포트 열기
          <svg
            className="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </span>
      </Link>
    </li>
  );
}

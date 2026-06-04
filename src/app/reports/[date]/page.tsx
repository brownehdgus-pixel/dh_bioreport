import Link from "next/link";
import { notFound } from "next/navigation";
import { NewsFeed } from "@/components/NewsFeed";
import { getReportByDate, getReports } from "@/lib/getReports";

type Props = {
  params: Promise<{ date: string }>;
};

export async function generateStaticParams() {
  const reports = await getReports();
  return reports.map((report) => ({ date: report.reportDate }));
}

export default async function ReportDetailPage({ params }: Props) {
  const { date } = await params;
  const report = await getReportByDate(date);

  if (!report) {
    notFound();
  }

  return (
    <>
      <div className="mx-auto max-w-lg border-b border-memo-border bg-memo-bg px-4 py-2">
        <Link
          href="/reports"
          className="inline-flex items-center gap-1 text-xs font-medium text-memo-accent"
        >
          <svg
            className="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          리포트 목록
        </Link>
      </div>
      <NewsFeed report={report} />
    </>
  );
}

import { ReportListCard } from "@/components/ReportListCard";
import { getReports } from "@/lib/getReports";

export default async function ReportsPage() {
  const reports = await getReports();

  return (
    <div className="mx-auto min-h-dvh max-w-lg">
      <header className="border-b border-memo-border bg-memo-surface px-4 pb-5 pt-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-memo-accent">
          Bio Industry Memo
        </p>
        <h1 className="mt-1 font-serif text-xl font-semibold text-memo-ink">리포트 목록</h1>
        <p className="mt-2 text-[13px] text-memo-muted">
          날짜별 뉴스 리포트 · 최신순 · 총 {reports.length}개
        </p>
      </header>

      <main className="px-4 py-4">
        {reports.length === 0 ? (
          <p className="py-12 text-center text-sm text-memo-muted">
            등록된 리포트가 없습니다.
          </p>
        ) : (
          <ul className="space-y-3">
            {reports.map((report) => (
              <ReportListCard key={report.reportDate} report={report} />
            ))}
          </ul>
        )}
      </main>

      <footer className="border-t border-memo-border px-4 py-6 text-center text-[11px] text-memo-muted">
        <p>Bio Industry Daily Memo · v0.1</p>
        <a href="/admin" className="mt-2 inline-block text-memo-accent underline">
          뉴스 입력 (관리자)
        </a>
      </footer>
    </div>
  );
}

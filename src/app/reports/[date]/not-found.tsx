import Link from "next/link";

export default function ReportNotFound() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col items-center justify-center px-4 text-center">
      <p className="text-sm text-memo-muted">해당 날짜의 리포트를 찾을 수 없습니다.</p>
      <Link
        href="/reports"
        className="mt-4 rounded-md bg-memo-accent px-4 py-2 text-sm font-medium text-white"
      >
        리포트 목록으로
      </Link>
    </div>
  );
}

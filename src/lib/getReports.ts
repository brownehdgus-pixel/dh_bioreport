import newsData from "../../data/news.json";
import type { DailyReport, NewsReportsFile } from "@/data/types";

/**
 * 모든 리포트를 불러옵니다.
 * 현재: data/news.json 파일 (요약 한글화는 크롤러에서 OpenAI로 처리)
 * 이후 Supabase로 전환 시 이 함수 내부만 DB 조회로 교체하면 됩니다.
 */
export async function getReports(): Promise<DailyReport[]> {
  const data = newsData as NewsReportsFile;
  return [...data.reports].sort((a, b) =>
    b.reportDate.localeCompare(a.reportDate)
  );
}

/** 가장 최신 리포트 (기본 화면용) */
export async function getLatestReport(): Promise<DailyReport> {
  const reports = await getReports();
  if (reports.length === 0) {
    throw new Error("news.json에 리포트가 없습니다.");
  }
  return reports[0];
}

/** 특정 날짜 리포트 (YYYY-MM-DD) */
export async function getReportByDate(
  reportDate: string
): Promise<DailyReport | undefined> {
  const reports = await getReports();
  return reports.find((r) => r.reportDate === reportDate);
}

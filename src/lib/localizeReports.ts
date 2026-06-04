import type { DailyReport } from "@/data/types";
import { isMostlyEnglish, translateToKorean } from "@/lib/textLocale";

/** 리포트·뉴스 카드의 요약문(summary, summaryLines)을 한국어로 맞춥니다. */
export async function localizeReports(reports: DailyReport[]): Promise<DailyReport[]> {
  return Promise.all(reports.map(localizeReport));
}

async function localizeReport(report: DailyReport): Promise<DailyReport> {
  const items = await Promise.all(
    report.items.map(async (item) => {
      if (!isMostlyEnglish(item.summary)) return item;
      return {
        ...item,
        summary: await translateToKorean(item.summary),
      };
    })
  );

  const summaryLines = await Promise.all(
    report.summaryLines.map(async (line) => {
      if (!isMostlyEnglish(line)) return line;
      return translateToKorean(line);
    })
  );

  return { ...report, items, summaryLines };
}

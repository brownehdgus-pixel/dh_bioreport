export type NewsSection =
  | "domestic"
  | "global"
  | "regulatory"
  | "deal"
  | "modality"
  | "paper"
  | "general";

export type NewsOrigin = "domestic" | "global";

export type NewsItem = {
  id: string;
  title: string;
  source: string;
  date: string;
  origin?: NewsOrigin;
  section: NewsSection;
  eventType: string;
  summary: string;
  significance: string;
  investmentTakeaway?: string;
  keywords: string[];
  importanceScore: number;
  investorRelevanceScore?: number;
  koreaRelevanceScore: number;
  url: string;
};

export const NEWS_SECTIONS: NewsSection[] = [
  "domestic",
  "global",
  "regulatory",
  "deal",
  "modality",
  "paper",
];

export type ExecutiveHighlight = {
  rank: number;
  itemId: string;
  headline: string;
  investmentTakeaway: string;
};

export type DailyReport = {
  reportDate: string;
  title: string;
  executiveHighlights?: ExecutiveHighlight[];
  summaryLines: string[];
  sections: NewsSection[];
  items: NewsItem[];
};

export type NewsReportsFile = {
  reports: DailyReport[];
};

export type TabId = "all" | NewsSection;

export const TAB_LABELS: Record<TabId, string> = {
  all: "전체",
  domestic: "국내",
  global: "글로벌",
  regulatory: "Regulatory",
  deal: "Deal/Funding",
  modality: "Modality",
  paper: "Paper",
  general: "General",
};

export const SECTION_LABELS: Record<NewsSection, string> = {
  domestic: "국내",
  global: "글로벌",
  regulatory: "Regulatory",
  deal: "Deal/Funding",
  modality: "Modality",
  paper: "Paper",
  general: "General",
};

const WEEKDAY_KO = ["일", "월", "화", "수", "목", "금", "토"] as const;

/** ISO 날짜(YYYY-MM-DD)를 화면용 한국어 날짜로 변환 */
export function formatReportDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const weekday = WEEKDAY_KO[date.getDay()];
  return `${y}년 ${m}월 ${d}일 (${weekday})`;
}

/** v1 리포트 호환: origin 없으면 section으로 추정 */
export function itemOrigin(item: NewsItem): NewsOrigin {
  if (item.origin === "domestic" || item.origin === "global") {
    return item.origin;
  }
  if (item.section === "domestic") return "domestic";
  return "global";
}

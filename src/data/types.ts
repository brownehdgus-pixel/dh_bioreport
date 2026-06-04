export type NewsSection =
  | "domestic"
  | "global"
  | "regulatory"
  | "deal"
  | "modality"
  | "paper";

export type NewsItem = {
  id: string;
  title: string;
  source: string;
  date: string;
  section: NewsSection;
  eventType: string;
  summary: string;
  significance: string;
  keywords: string[];
  importanceScore: number;
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

export type DailyReport = {
  reportDate: string;
  title: string;
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
};

export const SECTION_LABELS: Record<NewsSection, string> = {
  domestic: "국내",
  global: "글로벌",
  regulatory: "Regulatory",
  deal: "Deal/Funding",
  modality: "Modality",
  paper: "Paper",
};

const WEEKDAY_KO = ["일", "월", "화", "수", "목", "금", "토"] as const;

/** ISO 날짜(YYYY-MM-DD)를 화면용 한국어 날짜로 변환 */
export function formatReportDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const weekday = WEEKDAY_KO[date.getDay()];
  return `${y}년 ${m}월 ${d}일 (${weekday})`;
}

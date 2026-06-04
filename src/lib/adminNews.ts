import type { NewsItem, NewsSection } from "@/data/types";

export type NewsItemDraft = {
  title: string;
  source: string;
  date: string;
  section: NewsSection;
  eventType: string;
  summary: string;
  significance: string;
  keywordsText: string;
  importanceScore: string;
  koreaRelevanceScore: string;
  url: string;
};

export const emptyDraft = (): NewsItemDraft => ({
  title: "",
  source: "",
  date: new Date().toISOString().slice(0, 10),
  section: "global",
  eventType: "",
  summary: "",
  significance: "",
  keywordsText: "",
  importanceScore: "5",
  koreaRelevanceScore: "5",
  url: "",
});

function parseKeywords(text: string): string[] {
  return text
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
}

function parseScore(value: string): number | undefined {
  const n = Number(value);
  if (Number.isNaN(n)) return undefined;
  return Math.min(10, Math.max(1, Math.round(n)));
}

export function draftToNewsItem(draft: NewsItemDraft, id: string): NewsItem | null {
  if (!draft.title.trim() || !draft.source.trim() || !draft.date.trim()) {
    return null;
  }

  const item: NewsItem = {
    id,
    title: draft.title.trim(),
    source: draft.source.trim(),
    date: draft.date.trim(),
    section: draft.section,
    eventType: draft.eventType.trim() || "general",
    summary: draft.summary.trim(),
    significance: draft.significance.trim(),
    keywords: parseKeywords(draft.keywordsText),
    url: draft.url.trim() || "#",
  };

  const importance = parseScore(draft.importanceScore);
  const koreaRelevance = parseScore(draft.koreaRelevanceScore);
  if (importance != null) item.importanceScore = importance;
  if (koreaRelevance != null) item.koreaRelevanceScore = koreaRelevance;

  return item;
}

export function draftToPreviewItem(draft: NewsItemDraft): NewsItem {
  return (
    draftToNewsItem(draft, "preview") ?? {
      id: "preview",
      title: draft.title.trim() || "(제목을 입력하세요)",
      source: draft.source.trim() || "(출처)",
      date: draft.date || "2026-01-01",
      section: draft.section,
      eventType: draft.eventType.trim() || "—",
      summary: draft.summary.trim() || "(요약을 입력하세요)",
      significance: draft.significance.trim() || "(의미를 입력하세요)",
      keywords: parseKeywords(draft.keywordsText),
      importanceScore: parseScore(draft.importanceScore),
      koreaRelevanceScore: parseScore(draft.koreaRelevanceScore),
      url: draft.url.trim() || "#",
    }
  );
}

export function itemsToJson(items: NewsItem[]): string {
  return JSON.stringify(items, null, 2);
}

export function createItemId(): string {
  return `item-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

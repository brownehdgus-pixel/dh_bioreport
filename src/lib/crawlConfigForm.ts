/**
 * Crawl config form state ↔ JSON 변환 및 Admin UI 검증 (한국어 메시지)
 */

import {
  formatCrawlConfigJson,
  parseCrawlConfigText,
  validateCrawlConfig,
} from "@/lib/crawlConfigSchema";

export const UI_LIMITS = {
  maxItemAgeDays: { min: 1, max: 60, label: "최근 N일" },
  maxItemsInReport: { min: 5, max: 100, label: "리포트 최대 기사 수" },
  maxSummaryLines: { min: 3, max: 10, label: "핵심 요약 줄 수" },
} as const;

export const EVENT_BOOST_KEYS = [
  "regulatory",
  "funding",
  "clinical",
  "partnership",
  "publication",
] as const;

export const EVENT_BOOST_LABELS: Record<(typeof EVENT_BOOST_KEYS)[number], string> = {
  regulatory: "Regulatory (규제·허가)",
  funding: "Funding (자금·M&A)",
  clinical: "Clinical (임상)",
  partnership: "Partnership (제휴·라이선스)",
  publication: "Publication (논문·학술)",
};

export type GoogleQueryRow = {
  id: string;
  query: string;
  enabled: boolean;
};

export type RssFeedRow = {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
};

export type KeywordBoostRow = {
  id: string;
  keywordsText: string;
  boost: number;
};

export type ClassificationRow = {
  id: string;
  keywordsText: string;
};

export type CrawlConfigFormState = {
  maxItemAgeDays: number;
  maxItemsInReport: number;
  maxSummaryLines: number;
  excludePreviouslyReported: boolean;
  excludeSameUrl: boolean;
  excludeSameTitle: boolean;
  googleQueries: GoogleQueryRow[];
  rssFeeds: RssFeedRow[];
  excludeKeywords: string[];
  eventTypeBoosts: Record<(typeof EVENT_BOOST_KEYS)[number], number>;
  keywordBoosts: KeywordBoostRow[];
  eventTypeKeywords: ClassificationRow[];
  sectionKeywords: ClassificationRow[];
};

let rowId = 0;
export function newRowId(): string {
  rowId += 1;
  return `row-${Date.now()}-${rowId}`;
}

function keywordsToText(keywords: unknown): string {
  if (!Array.isArray(keywords)) return "";
  return keywords.map((k) => String(k).trim()).filter(Boolean).join(", ");
}

function textToKeywords(text: string): string[] {
  return text
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

/** JSON config → 폼 상태 (eventSignificance 등 UI 밖 필드는 config에 보존) */
export function configToFormState(config: Record<string, unknown>): CrawlConfigFormState {
  const limits = asRecord(config.limits);
  const sources = asRecord(config.sources);
  const scoring = asRecord(config.scoring);
  const classification = asRecord(config.classification);
  const boosts = asRecord(scoring.eventTypeBoosts);

  const googleQueries: GoogleQueryRow[] = asArray(sources.googleNewsQueries).map((item) => {
    if (typeof item === "string") {
      return { id: newRowId(), query: item, enabled: true };
    }
    const row = asRecord(item);
    return {
      id: newRowId(),
      query: String(row.query || ""),
      enabled: row.enabled !== false,
    };
  });

  const rssFeeds: RssFeedRow[] = asArray(sources.rssFeeds).map((item) => {
    const row = asRecord(item);
    return {
      id: newRowId(),
      name: String(row.name || ""),
      url: String(row.url || ""),
      enabled: row.enabled !== false,
    };
  });

  const keywordBoosts: KeywordBoostRow[] = asArray(scoring.keywordBoosts).map((item) => {
    const row = asRecord(item);
    return {
      id: newRowId(),
      keywordsText: keywordsToText(row.keywords),
      boost: Number(row.boost) || 0,
    };
  });

  const eventTypeKeywords: ClassificationRow[] = asArray(classification.eventTypes).map((item) => {
    const row = asRecord(item);
    return {
      id: String(row.id || newRowId()),
      keywordsText: keywordsToText(row.keywords),
    };
  });

  const sectionKeywords: ClassificationRow[] = asArray(classification.sections).map((item) => {
    const row = asRecord(item);
    return {
      id: String(row.id || newRowId()),
      keywordsText: keywordsToText(row.keywords),
    };
  });

  const eventTypeBoosts = {} as Record<(typeof EVENT_BOOST_KEYS)[number], number>;
  for (const key of EVENT_BOOST_KEYS) {
    eventTypeBoosts[key] = Number(boosts[key]) || 0;
  }

  const dedup = asRecord(config.deduplication);

  return {
    maxItemAgeDays: Number(limits.maxItemAgeDays) || 14,
    maxItemsInReport: Number(limits.maxItemsInReport) || 40,
    maxSummaryLines: Number(limits.maxSummaryLines) || 5,
    excludePreviouslyReported: dedup.excludePreviouslyReported !== false,
    excludeSameUrl: dedup.excludeSameUrl !== false,
    excludeSameTitle: dedup.excludeSameTitle !== false,
    googleQueries,
    rssFeeds,
    excludeKeywords: asArray(config.excludeKeywords).map((k) => String(k).trim()).filter(Boolean),
    eventTypeBoosts,
    keywordBoosts,
    eventTypeKeywords,
    sectionKeywords,
  };
}

/** 폼 상태 → JSON config (기존 config 위에 merge) */
export function applyFormToConfig(
  base: Record<string, unknown>,
  form: CrawlConfigFormState
): Record<string, unknown> {
  const merged = structuredClone(base);
  const limits = asRecord(merged.limits);
  limits.maxItemAgeDays = form.maxItemAgeDays;
  limits.maxItemsInReport = form.maxItemsInReport;
  limits.maxSummaryLines = form.maxSummaryLines;
  merged.limits = limits;

  const sources = asRecord(merged.sources);
  sources.rssFeeds = form.rssFeeds.map((f) => {
    const existing = asArray(sources.rssFeeds)
      .map(asRecord)
      .find((r) => r.url === f.url || r.name === f.name);
    return {
      name: f.name.trim(),
      url: f.url.trim(),
      enabled: f.enabled,
      sourceType: String(existing?.sourceType || "rss"),
      queryKeyword: String(existing?.queryKeyword || ""),
    };
  });
  sources.googleNewsQueries = form.googleQueries.map((q) => ({
    query: q.query.trim(),
    enabled: q.enabled,
  }));
  merged.sources = sources;

  merged.excludeKeywords = form.excludeKeywords.map((k) => k.trim()).filter(Boolean);

  merged.deduplication = {
    excludePreviouslyReported: form.excludePreviouslyReported,
    excludeSameUrl: form.excludeSameUrl,
    excludeSameTitle: form.excludeSameTitle,
  };

  const scoring = asRecord(merged.scoring);
  const existingBoosts = asRecord(scoring.eventTypeBoosts);
  for (const key of EVENT_BOOST_KEYS) {
    existingBoosts[key] = form.eventTypeBoosts[key];
  }
  scoring.eventTypeBoosts = existingBoosts;
  scoring.keywordBoosts = form.keywordBoosts.map((g) => ({
    keywords: textToKeywords(g.keywordsText),
    boost: g.boost,
  }));
  merged.scoring = scoring;

  const classification = asRecord(merged.classification);
  const sectionOrder = asArray(classification.sectionOrder).map(String);
  classification.eventTypes = form.eventTypeKeywords.map((row) => ({
    id: row.id,
    keywords: textToKeywords(row.keywordsText),
  }));
  classification.sections = form.sectionKeywords.map((row) => ({
    id: row.id,
    keywords: textToKeywords(row.keywordsText),
  }));
  if (sectionOrder.length === 0) {
    classification.sectionOrder = ["domestic", "global", "regulatory", "deal", "modality", "paper"];
  }
  merged.classification = classification;

  return merged;
}

function inRange(n: number, min: number, max: number): boolean {
  return Number.isFinite(n) && n >= min && n <= max;
}

function isHttpUrl(url: string): boolean {
  const trimmed = url.trim();
  return trimmed.startsWith("http://") || trimmed.startsWith("https://");
}

/** Admin UI 저장 전 검증 — 한국어 오류 메시지 */
export function validateFormState(form: CrawlConfigFormState): string[] {
  const errors: string[] = [];

  if (!inRange(form.maxItemAgeDays, UI_LIMITS.maxItemAgeDays.min, UI_LIMITS.maxItemAgeDays.max)) {
    errors.push(
      `${UI_LIMITS.maxItemAgeDays.label}은(는) ${UI_LIMITS.maxItemAgeDays.min}~${UI_LIMITS.maxItemAgeDays.max} 사이여야 합니다.`
    );
  }
  if (!inRange(form.maxItemsInReport, UI_LIMITS.maxItemsInReport.min, UI_LIMITS.maxItemsInReport.max)) {
    errors.push(
      `${UI_LIMITS.maxItemsInReport.label}은(는) ${UI_LIMITS.maxItemsInReport.min}~${UI_LIMITS.maxItemsInReport.max} 사이여야 합니다.`
    );
  }
  if (!inRange(form.maxSummaryLines, UI_LIMITS.maxSummaryLines.min, UI_LIMITS.maxSummaryLines.max)) {
    errors.push(
      `${UI_LIMITS.maxSummaryLines.label}은(는) ${UI_LIMITS.maxSummaryLines.min}~${UI_LIMITS.maxSummaryLines.max} 사이여야 합니다.`
    );
  }

  form.googleQueries.forEach((q, i) => {
    if (!q.query.trim()) {
      errors.push(`Google News 검색어 ${i + 1}번: 검색어를 입력해 주세요.`);
    }
  });

  form.rssFeeds.forEach((f, i) => {
    if (!f.name.trim()) {
      errors.push(`RSS 피드 ${i + 1}번: 이름을 입력해 주세요.`);
    }
    if (!f.url.trim()) {
      errors.push(`RSS 피드 ${i + 1}번: URL을 입력해 주세요.`);
    } else if (!isHttpUrl(f.url)) {
      errors.push(`RSS 피드 ${i + 1}번: URL은 http:// 또는 https:// 로 시작해야 합니다.`);
    }
  });

  for (const key of EVENT_BOOST_KEYS) {
    const boost = form.eventTypeBoosts[key];
    if (!inRange(boost, -5, 5)) {
      errors.push(`${EVENT_BOOST_LABELS[key]} 가중치는 -5~5 사이여야 합니다.`);
    }
  }

  form.keywordBoosts.forEach((g, i) => {
    if (!g.keywordsText.trim()) {
      errors.push(`키워드 가중치 ${i + 1}번: 키워드를 입력해 주세요.`);
    }
    if (!inRange(g.boost, -5, 5)) {
      errors.push(`키워드 가중치 ${i + 1}번: boost는 -5~5 사이여야 합니다.`);
    }
  });

  form.eventTypeKeywords.forEach((row) => {
    if (!row.id.trim()) {
      errors.push("이벤트 유형 분류: id가 비어 있습니다.");
    }
  });

  form.sectionKeywords.forEach((row) => {
    if (!row.id.trim()) {
      errors.push("섹션 분류: id가 비어 있습니다.");
    }
  });

  return errors;
}

export function validateConfigForSave(config: Record<string, unknown>): string[] {
  const formErrors = validateFormState(configToFormState(config));
  const schema = validateCrawlConfig(config);
  const schemaErrors = schema.ok ? [] : schema.errors.map((e) => translateSchemaError(e));
  return [...formErrors, ...schemaErrors];
}

function translateSchemaError(msg: string): string {
  if (msg.includes("Invalid JSON") || msg.includes("JSON")) return "JSON 형식이 올바르지 않습니다.";
  return msg;
}

export function parseAndValidateJsonText(text: string): {
  ok: true;
  config: Record<string, unknown>;
} | {
  ok: false;
  errors: string[];
} {
  const parsed = parseCrawlConfigText(text);
  if (!parsed.ok) {
    return { ok: false, errors: ["JSON 형식이 올바르지 않습니다. 쉼표·따옴표를 확인해 주세요."] };
  }
  if (!parsed.data || typeof parsed.data !== "object" || Array.isArray(parsed.data)) {
    return { ok: false, errors: ["설정 파일의 최상위는 객체(JSON {})여야 합니다."] };
  }
  const config = parsed.data as Record<string, unknown>;
  const errors = validateConfigForSave(config);
  if (errors.length > 0) return { ok: false, errors };
  return { ok: true, config };
}

export function formToJsonText(base: Record<string, unknown>, form: CrawlConfigFormState): string {
  return formatCrawlConfigJson(applyFormToConfig(base, form));
}

export function defaultEmptyForm(): CrawlConfigFormState {
  return {
    maxItemAgeDays: 14,
    maxItemsInReport: 40,
    maxSummaryLines: 5,
    excludePreviouslyReported: true,
    excludeSameUrl: true,
    excludeSameTitle: true,
    googleQueries: [],
    rssFeeds: [],
    excludeKeywords: [],
    eventTypeBoosts: {
      regulatory: 2,
      funding: 2,
      clinical: 2,
      partnership: 1,
      publication: 1,
    },
    keywordBoosts: [],
    eventTypeKeywords: [],
    sectionKeywords: [],
  };
}

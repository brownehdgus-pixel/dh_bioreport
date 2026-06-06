/**
 * Crawl config validation — mirrors scripts/crawl_config.py rules.
 */

export type CrawlConfigValidationResult =
  | { ok: true; data: Record<string, unknown> }
  | { ok: false; errors: string[] };

function clampInt(value: unknown, lo: number, hi: number, name: string, errors: string[]): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    errors.push(`${name} must be a number`);
    return null;
  }
  const n = Math.trunc(value);
  if (n < lo || n > hi) {
    errors.push(`${name} must be between ${lo} and ${hi}`);
    return null;
  }
  return n;
}

function asBool(value: unknown, defaultValue: boolean): boolean {
  if (value === undefined || value === null) return defaultValue;
  return Boolean(value);
}

export function validateCrawlConfig(input: unknown): CrawlConfigValidationResult {
  const errors: string[] = [];

  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return { ok: false, errors: ["Root must be a JSON object"] };
  }

  const data = input as Record<string, unknown>;
  const limits = (data.limits as Record<string, unknown>) || {};
  const sources = (data.sources as Record<string, unknown>) || {};
  const scoring = (data.scoring as Record<string, unknown>) || {};
  const classification = (data.classification as Record<string, unknown>) || {};

  clampInt(limits.maxItemAgeDays, 1, 90, "limits.maxItemAgeDays", errors);
  clampInt(limits.maxItemsInReport, 1, 200, "limits.maxItemsInReport", errors);
  clampInt(limits.maxSummaryLines, 1, 20, "limits.maxSummaryLines", errors);
  clampInt(limits.reportRetentionDays, 7, 365, "limits.reportRetentionDays", errors);

  clampInt(scoring.baseImportance, 1, 10, "scoring.baseImportance", errors);
  const minImp = clampInt(scoring.minImportance, 1, 10, "scoring.minImportance", errors);
  const maxImp = clampInt(scoring.maxImportance, 1, 10, "scoring.maxImportance", errors);
  if (minImp !== null && maxImp !== null && minImp > maxImp) {
    errors.push("scoring.minImportance cannot exceed maxImportance");
  }

  const rssFeeds = sources.rssFeeds;
  if (rssFeeds !== undefined && !Array.isArray(rssFeeds)) {
    errors.push("sources.rssFeeds must be an array");
  } else if (Array.isArray(rssFeeds)) {
    rssFeeds.forEach((feed, i) => {
      if (!feed || typeof feed !== "object") {
        errors.push(`sources.rssFeeds[${i}] must be an object`);
        return;
      }
      const f = feed as Record<string, unknown>;
      if (!String(f.name || "").trim() || !String(f.url || "").trim()) {
        errors.push(`sources.rssFeeds[${i}] requires name and url`);
      }
      asBool(f.enabled, true);
    });
  }

  const googleQueries = sources.googleNewsQueries;
  if (googleQueries !== undefined && !Array.isArray(googleQueries)) {
    errors.push("sources.googleNewsQueries must be an array");
  } else if (Array.isArray(googleQueries)) {
    googleQueries.forEach((item, i) => {
      if (typeof item === "string") return;
      if (!item || typeof item !== "object") {
        errors.push(`sources.googleNewsQueries[${i}] invalid`);
        return;
      }
      const q = item as Record<string, unknown>;
      if (!String(q.query || "").trim()) {
        errors.push(`sources.googleNewsQueries[${i}] requires query`);
      }
      asBool(q.enabled, true);
    });
  }

  const exclude = data.excludeKeywords;
  if (exclude !== undefined && !Array.isArray(exclude)) {
    errors.push("excludeKeywords must be an array");
  }

  for (const key of ["eventTypes", "sections"] as const) {
    const rules = classification[key];
    if (rules === undefined) continue;
    if (!Array.isArray(rules)) {
      errors.push(`classification.${key} must be an array`);
      continue;
    }
    rules.forEach((rule, i) => {
      if (!rule || typeof rule !== "object") {
        errors.push(`classification.${key}[${i}] must be an object`);
        return;
      }
      const r = rule as Record<string, unknown>;
      if (!String(r.id || "").trim()) {
        errors.push(`classification.${key}[${i}] requires id`);
      }
      if (r.keywords !== undefined && !Array.isArray(r.keywords)) {
        errors.push(`classification.${key}[${i}].keywords must be an array`);
      }
    });
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return { ok: true, data: data as Record<string, unknown> };
}

export function formatCrawlConfigJson(data: Record<string, unknown>): string {
  return `${JSON.stringify(data, null, 2)}\n`;
}

export function parseCrawlConfigText(text: string): { ok: true; data: unknown } | { ok: false; error: string } {
  try {
    return { ok: true, data: JSON.parse(text) as unknown };
  } catch {
    return { ok: false, error: "Invalid JSON syntax" };
  }
}

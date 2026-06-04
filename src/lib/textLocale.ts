/** 영문 위주 텍스트인지 판별 (한글 비율이 낮으면 번역 대상) */
export function isMostlyEnglish(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) return false;

  const hangul = (trimmed.match(/[\uAC00-\uD7A3]/g) ?? []).length;
  const latin = (trimmed.match(/[A-Za-z]/g) ?? []).length;

  if (latin < 12) return false;
  return latin > hangul * 1.5;
}

const translationCache = new Map<string, string>();

/**
 * 영문 요약을 한국어로 번역합니다.
 * 실패 시 원문을 그대로 반환합니다.
 */
export async function translateToKorean(text: string): Promise<string> {
  const trimmed = text.trim();
  if (!trimmed || !isMostlyEnglish(trimmed)) return trimmed;

  const cached = translationCache.get(trimmed);
  if (cached) return cached;

  try {
    const { translate } = await import("google-translate-api-x");
    const result = await translate(trimmed, { from: "en", to: "ko" });
    const translated =
      typeof result === "string"
        ? result
        : Array.isArray(result)
          ? result.map((r) => r.text).join(" ")
          : result.text;

    const output = translated.trim() || trimmed;
    translationCache.set(trimmed, output);
    return output;
  } catch {
    return trimmed;
  }
}

"""Google Translate로 영문 텍스트를 한국어로 번역 (크롤러·일괄 변환 공용)."""

from __future__ import annotations

import re


def is_mostly_english(text: str) -> bool:
    trimmed = text.strip()
    if not trimmed:
        return False
    hangul = len(re.findall(r"[\uAC00-\uD7A3]", trimmed))
    latin = len(re.findall(r"[A-Za-z]", trimmed))
    if latin < 12:
        return False
    return latin > hangul * 1.5


def translate_to_korean(text: str) -> str:
    """영문 요약을 Google Translate로 한국어 번역. 실패 시 원문 반환."""
    trimmed = text.strip()
    if not trimmed or not is_mostly_english(trimmed):
        return trimmed

    try:
        from deep_translator import GoogleTranslator

        result = GoogleTranslator(source="auto", target="ko").translate(trimmed[:4500])
        out = (result or "").strip()
        return out or trimmed
    except Exception as exc:  # noqa: BLE001
        print(f"  [translate] Google Translate 실패 ({exc}) — 영문 유지")
        return trimmed

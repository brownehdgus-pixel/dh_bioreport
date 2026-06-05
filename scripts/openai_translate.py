"""OpenAI API로 영문 텍스트를 한국어로 번역 (크롤러·일괄 변환 공용)."""

from __future__ import annotations

import os
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
    """영문 요약을 OpenAI로 한국어 번역. 키 없으면 원문 반환."""
    trimmed = text.strip()
    if not trimmed or not is_mostly_english(trimmed):
        return trimmed

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("  [translate] OPENAI_API_KEY 없음 — 영문 유지")
        return trimmed

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 바이오·제약 뉴스 편집자입니다. "
                        "입력된 영문 요약을 자연스러운 한국어 1~2문장으로 번역하세요. "
                        "번역문만 출력하고 따옴표·설명은 넣지 마세요."
                    ),
                },
                {"role": "user", "content": trimmed[:4000]},
            ],
        )
        out = (response.choices[0].message.content or "").strip()
        return out or trimmed
    except Exception as exc:  # noqa: BLE001
        print(f"  [translate] OpenAI 실패 ({exc}) — 영문 유지")
        return trimmed

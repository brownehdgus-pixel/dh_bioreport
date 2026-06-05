#!/usr/bin/env python3
"""
data/news.json 안의 영문 요약(summary, summaryLines)을 한국어로 바꿉니다.

실행: python scripts/translate_news_summaries.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS_JSON = ROOT / "data" / "news.json"
NEWS_BACKUP = ROOT / "data" / "news.backup.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from openai_translate import is_mostly_english, translate_to_korean  # noqa: E402


def main() -> int:
    if not NEWS_JSON.exists():
        print("data/news.json not found")
        return 1

    shutil.copy2(NEWS_JSON, NEWS_BACKUP)
    data = json.loads(NEWS_JSON.read_text(encoding="utf-8"))
    translated_count = 0

    for report in data.get("reports", []):
        for item in report.get("items", []):
            summary = item.get("summary", "")
            if is_mostly_english(summary):
                item["summary"] = translate_to_korean(summary)
                translated_count += 1

        new_lines = []
        for line in report.get("summaryLines", []):
            if is_mostly_english(line):
                new_lines.append(translate_to_korean(line))
                translated_count += 1
            else:
                new_lines.append(line)
        report["summaryLines"] = new_lines

    NEWS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Done. Translated {translated_count} fields.")
    print(f"Backup: {NEWS_BACKUP.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

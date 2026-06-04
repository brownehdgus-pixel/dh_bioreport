#!/usr/bin/env python3
"""
Bio Industry Daily Memo — RSS 뉴스 수집 MVP.

실행: python scripts/collect_news.py

출력:
  raw_data/YYYY-MM-DD/raw_items.json
  raw_data/YYYY-MM-DD/deduplicated_items.json
  data/news.backup.json  (기존 news.json 백업)
  data/news.json         (웹앱 표시용, 기존 구조)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import feedparser

# ---------------------------------------------------------------------------
# 경로 · 설정
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw_data"
NEWS_JSON = DATA_DIR / "news.json"
NEWS_BACKUP = DATA_DIR / "news.backup.json"

USER_AGENT = "BioNewsReportCollector/0.1 (+https://github.com/local/bio-news-report)"
MAX_ITEM_AGE_DAYS = 14
MAX_ITEMS_IN_REPORT = 40
MAX_SUMMARY_LINES = 5

RSS_FEEDS: list[dict[str, str]] = [
    {
        "name": "Fierce Biotech",
        "url": "https://www.fiercebiotech.com/rss/xml",
        "source_type": "rss",
        "query_keyword": "",
    },
    {
        "name": "Fierce Pharma",
        "url": "https://www.fiercepharma.com/rss/xml",
        "source_type": "rss",
        "query_keyword": "",
    },
    {
        "name": "BioPharma Dive",
        "url": "https://www.biopharmadive.com/feeds/news/",
        "source_type": "rss",
        "query_keyword": "",
    },
    {
        "name": "Business Wire",
        "url": "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeGVtXWg==",
        "source_type": "rss",
        "query_keyword": "",
    },
]

GOOGLE_NEWS_QUERIES: list[str] = [
    "biotech FDA approval",
    "pharmaceutical merger acquisition",
    "gene therapy clinical trial",
    "Korea biopharma",
    "mRNA vaccine pharmaceutical",
]

SECTION_ORDER = [
    "domestic",
    "global",
    "regulatory",
    "deal",
    "modality",
    "paper",
]

EVENT_SIGNIFICANCE: dict[str, str] = {
    "regulatory": "규제·허가 이슈는 승인 일정과 경쟁사 파이프라인 밸류에이션에 직접적인 영향을 줄 수 있어 후속 공문·가이드라인을 확인할 필요가 있다.",
    "funding": "자금 조달·M&A 신호는 섹터 심리와 BD 협상 타이밍에 영향을 줄 수 있어 유사 딜의 조건을 비교해 볼 가치가 있다.",
    "clinical": "임상 마일스톤은 해당 모달리티·타깃의 리스크 프리미엄을 재조정할 수 있어 동일 적응증 경쟁사를 함께 모니터링하는 것이 좋다.",
    "publication": "학술·공개 데이터는 장기 기술·안전성 논쟁에 쓰이므로 규제 당국 코멘트와의 연계 여부를 추적할 필요가 있다.",
    "partnership": "공동개발·라이선스 구조는 권리·마일스톤 분배에 따라 수익성이 달라지므로 계약 요약을 확인하는 것이 좋다.",
    "policy": "정책·법안 변화는 reimbursement·심사 속도에 영향을 줄 수 있어 업종 전반의 규제 비용 가정을 점검할 시점이다.",
    "commercial": "상업화·마케팅 이슈는 매출 가이던스와 채널 전략에 연결되므로 경쟁 제품 점유율 데이터와 함께 보면 유용하다.",
    "market": "시장·주가 움직임은 단기 섹터 로테이션 신호일 수 있어 펀더멘털과의 괴리 여부를 함께 판단할 필요가 있다.",
    "general": "업계 동향 파악용 기사로, 파이프라인·규제·BD 맥락에서 후속 기사가 이어지는지 확인하면 된다.",
}

# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    query = parse_qs(parsed.query, keep_blank_values=False)
    for key in list(query.keys()):
        if key.lower().startswith("utm_") or key.lower() in {"fbclid", "gclid", "mc_cid", "mc_eid"}:
            del query[key]
    new_query = urlencode({k: v[0] if len(v) == 1 else v for k, v in query.items()}, doseq=True)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", new_query, ""))


def make_raw_id(normalized_url: str, title: str) -> str:
    base = f"{normalized_url}|{title.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def parse_published(entry: Any) -> str | None:
    if getattr(entry, "published_parsed", None):
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.date().isoformat()
    if getattr(entry, "updated_parsed", None):
        dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        return dt.date().isoformat()

    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not raw:
        return None

    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        pass

    for fmt in ("%b %d, %Y %I:%M%p", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def entry_to_payload(entry: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in entry.keys():
        val = entry[key]
        if isinstance(val, (str, int, float, bool)) or val is None:
            payload[key] = val
        elif isinstance(val, list) and all(isinstance(x, str) for x in val):
            payload[key] = val
    return payload


def google_news_rss_url(query: str) -> str:
    from urllib.parse import quote_plus

    q = quote_plus(query)
    return (
        f"https://news.google.com/rss/search?q={q}"
        "&hl=en-US&gl=US&ceid=US:en"
    )


# ---------------------------------------------------------------------------
# 수집
# ---------------------------------------------------------------------------


def fetch_feed(
    *,
    feed_url: str,
    source_name: str,
    source_type: str,
    query_keyword: str,
    collected_at: str,
) -> list[dict[str, Any]]:
    parsed = feedparser.parse(feed_url, agent=USER_AGENT)
    items: list[dict[str, Any]] = []

    for entry in parsed.entries:
        title = strip_html(getattr(entry, "title", None) or "").strip()
        link = getattr(entry, "link", None) or ""
        if not title or not link:
            continue

        norm = normalize_url(link)
        snippet = strip_html(
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
            or getattr(entry, "subtitle", None)
        )
        published = parse_published(entry)

        items.append(
            {
                "raw_id": make_raw_id(norm, title),
                "title": title,
                "source": source_name,
                "published_at": published,
                "collected_at": collected_at,
                "url": link,
                "normalized_url": norm,
                "snippet": snippet[:2000] if snippet else "",
                "query_keyword": query_keyword,
                "source_type": source_type,
                "raw_payload": entry_to_payload(entry),
            }
        )

    return items


def collect_all_raw(collected_at: str) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []

    for feed in RSS_FEEDS:
        try:
            batch = fetch_feed(
                feed_url=feed["url"],
                source_name=feed["name"],
                source_type=feed["source_type"],
                query_keyword=feed.get("query_keyword", ""),
                collected_at=collected_at,
            )
            all_items.extend(batch)
            print(f"  - {feed['name']}: {len(batch)} items")
        except Exception as exc:  # noqa: BLE001 — MVP: 한 소스 실패해도 계속
            print(f"  - {feed['name']}: FAILED ({exc})")

    for query in GOOGLE_NEWS_QUERIES:
        label = f"Google News ({query})"
        try:
            batch = fetch_feed(
                feed_url=google_news_rss_url(query),
                source_name="Google News",
                source_type="google_news_rss",
                query_keyword=query,
                collected_at=collected_at,
            )
            all_items.extend(batch)
            print(f"  - {label}: {len(batch)} items")
        except Exception as exc:  # noqa: BLE001
            print(f"  - {label}: FAILED ({exc})")

    return all_items


def filter_recent(items: list[dict[str, Any]], report_date: str) -> list[dict[str, Any]]:
    cutoff = datetime.strptime(report_date, "%Y-%m-%d").date() - timedelta(days=MAX_ITEM_AGE_DAYS)
    recent: list[dict[str, Any]] = []
    for item in items:
        pub = item.get("published_at")
        if not pub:
            recent.append(item)
            continue
        try:
            pub_date = datetime.strptime(pub, "%Y-%m-%d").date()
        except ValueError:
            recent.append(item)
            continue
        if pub_date >= cutoff:
            recent.append(item)
    return recent


def deduplicate_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for item in items:
        key = item.get("normalized_url") or item.get("url") or item["raw_id"]
        existing = by_url.get(key)
        if existing is None:
            by_url[key] = item
            continue
        # 더 최신 published_at 유지
        pub_new = item.get("published_at") or ""
        pub_old = existing.get("published_at") or ""
        if pub_new > pub_old:
            by_url[key] = item
    return list(by_url.values())


# ---------------------------------------------------------------------------
# 분류 · rule-based 텍스트
# ---------------------------------------------------------------------------


def classify_event_type(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    rules: list[tuple[str, list[str]]] = [
        ("regulatory", ["fda", "ema", "mfds", "approval", "approved", "designation", " orphan", "ind ", "nda", "regulatory", "clearance"]),
        ("funding", ["series a", "series b", "series c", "funding", "raised", "investment", "million", "billion", "financing"]),
        ("clinical", ["phase 1", "phase 2", "phase 3", "phase i", "phase ii", "phase iii", "clinical trial", "patient", "dosing"]),
        ("publication", ["nature", "science", "journal", "published in", "peer-reviewed", "study finds", "researchers report"]),
        ("partnership", ["partnership", "collaboration", "license", "licensing", "co-develop", "strategic agreement"]),
        ("policy", ["policy", "legislation", "bill", "congress", "senate", "regulation reform"]),
        ("commercial", ["launch", "commercial", "marketing", "revenue", "sales"]),
        ("market", ["stock", "shares", "nasdaq", "market cap", "index", "trading"]),
    ]
    for event_type, keywords in rules:
        if any(kw in text for kw in keywords):
            return event_type
    return "general"


def classify_section(title: str, snippet: str, source: str) -> str:
    text = f"{title} {snippet} {source}".lower()
    if any(
        kw in text
        for kw in [
            "korea",
            "korean",
            "south korea",
            "seoul",
            "mfds",
            "kosdaq",
            "hanmi",
            "celltrion",
            "samsung biologics",
            "sk bioscience",
            "yuhan",
            "국내",
            "한국",
        ]
    ):
        return "domestic"
    if any(kw in text for kw in ["fda", "ema", "mfds", "regulatory", "approval", "orphan drug", "breakthrough", "gmp", "ind ", "nda"]):
        return "regulatory"
    if any(kw in text for kw in ["acquisition", "merger", "funding", "series ", "investment", "deal", "licensing", "buyout", "raised"]):
        return "deal"
    if any(
        kw in text
        for kw in [
            "car-t",
            "cart",
            "mrna",
            "adc",
            "crispr",
            "gene therapy",
            "cell therapy",
            "antibody",
            "protein degradation",
            "protac",
            "rnai",
            "aav",
            "bispecific",
        ]
    ):
        return "modality"
    if any(kw in text for kw in ["nature", "science", "journal", "publication", "peer-reviewed", "lancet", "cell press", "study in"]):
        return "paper"
    return "global"


def extract_keywords(title: str, snippet: str, query_keyword: str) -> list[str]:
    text = f"{title} {snippet}"
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-/+]{2,}", text)
    seen: set[str] = set()
    keywords: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if low in seen or len(low) < 3:
            continue
        seen.add(low)
        keywords.append(tok if tok.isupper() else tok)
        if len(keywords) >= 6:
            break
    if query_keyword and query_keyword not in keywords:
        keywords.insert(0, query_keyword[:40])
    return keywords[:6] or ["biotech"]


def is_mostly_english(text: str) -> bool:
    if not text.strip():
        return False
    hangul = len(re.findall(r"[\uAC00-\uD7A3]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if latin < 12:
        return False
    return latin > hangul * 1.5


def translate_to_korean(text: str) -> str:
    """영문 요약을 한국어로 번역 (LLM 없음, Google Translate 경유)."""
    trimmed = text.strip()
    if not trimmed or not is_mostly_english(trimmed):
        return trimmed
    try:
        from deep_translator import GoogleTranslator

        chunk = trimmed[:4500]
        return GoogleTranslator(source="auto", target="ko").translate(chunk) or trimmed
    except Exception:
        return trimmed


def build_summary(title: str, snippet: str) -> str:
    base = snippet.strip() if snippet else title.strip()
    base = re.sub(r"\s+", " ", base)
    if not base:
        return title.strip()
    if base.lower().startswith(title.lower()[: min(20, len(title))]):
        combined = base
    else:
        combined = f"{title.strip()}. {base}"
    if len(combined) <= 220:
        return combined
    cut = combined[:220].rsplit(" ", 1)[0]
    return cut.rstrip(".,;") + "…"


def build_significance(event_type: str, section: str) -> str:
    base = EVENT_SIGNIFICANCE.get(event_type, EVENT_SIGNIFICANCE["general"])
    if section == "domestic":
        return f"{base} 국내 바이오·제약 업계 관점에서 공급망·파트너 영향을 함께 점검하면 좋다."
    return base


def score_importance(title: str, snippet: str, event_type: str) -> int:
    text = f"{title} {snippet}".lower()
    score = 5
    boosts = {
        "regulatory": 2,
        "funding": 2,
        "clinical": 2,
        "partnership": 1,
        "publication": 1,
    }
    score += boosts.get(event_type, 0)
    if any(kw in text for kw in ["fda", "breakthrough", "phase 3", "acquisition", "merger", "billion"]):
        score += 1
    return max(1, min(10, score))


def score_korea_relevance(title: str, snippet: str, section: str) -> int:
    if section == "domestic":
        return 8
    text = f"{title} {snippet}".lower()
    if any(kw in text for kw in ["korea", "korean", "mfds", "seoul", "asia pacific"]):
        return 6
    if section in {"regulatory", "deal"}:
        return 5
    return 4


def raw_to_news_item(raw: dict[str, Any], index: int, report_date: str) -> dict[str, Any]:
    title = raw["title"]
    snippet = raw.get("snippet") or ""
    section = classify_section(title, snippet, raw.get("source", ""))
    event_type = classify_event_type(title, snippet)
    item_date = raw.get("published_at") or report_date

    summary_en = build_summary(title, snippet)
    return {
        "id": f"{report_date}-{index:04d}",
        "title": title,
        "source": raw.get("source", "Unknown"),
        "date": item_date,
        "section": section,
        "eventType": event_type,
        "summary": translate_to_korean(summary_en),
        "significance": build_significance(event_type, section),
        "keywords": extract_keywords(title, snippet, raw.get("query_keyword", "")),
        "importanceScore": score_importance(title, snippet, event_type),
        "koreaRelevanceScore": score_korea_relevance(title, snippet, section),
        "url": raw.get("url") or "#",
    }


def build_daily_report(
    report_date: str,
    deduped: list[dict[str, Any]],
) -> dict[str, Any]:
    sorted_raw = sorted(
        deduped,
        key=lambda r: (
            -(score_importance(r["title"], r.get("snippet", ""), classify_event_type(r["title"], r.get("snippet", "")))),
            r.get("published_at") or "",
        ),
    )[:MAX_ITEMS_IN_REPORT]

    items = [raw_to_news_item(raw, i + 1, report_date) for i, raw in enumerate(sorted_raw)]
    used_sections = sorted(
        {item["section"] for item in items},
        key=lambda s: SECTION_ORDER.index(s) if s in SECTION_ORDER else 99,
    )

    summary_lines: list[str] = []
    for item in sorted(items, key=lambda x: -x["importanceScore"])[:MAX_SUMMARY_LINES]:
        line = item["summary"]
        if len(line) > 140:
            line = line[:137].rsplit(" ", 1)[0] + "…"
        summary_lines.append(line)

    if not summary_lines:
        summary_lines = ["수집된 기사가 없습니다. RSS 소스 연결 상태를 확인해 주세요."]

    return {
        "reportDate": report_date,
        "title": f"{report_date} 바이오 뉴스 브리핑",
        "summaryLines": summary_lines,
        "sections": used_sections if used_sections else ["global"],
        "items": items,
    }


def merge_reports(existing: list[dict[str, Any]], new_report: dict[str, Any]) -> list[dict[str, Any]]:
    by_date = {r["reportDate"]: r for r in existing if r.get("reportDate")}
    by_date[new_report["reportDate"]] = new_report
    return sorted(by_date.values(), key=lambda r: r["reportDate"], reverse=True)


def load_existing_reports() -> list[dict[str, Any]]:
    if not NEWS_JSON.exists():
        return []
    try:
        data = json.loads(NEWS_JSON.read_text(encoding="utf-8"))
        return data.get("reports", [])
    except json.JSONDecodeError:
        return []


def backup_news_json() -> None:
    if NEWS_JSON.exists():
        NEWS_BACKUP.write_text(NEWS_JSON.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup: {NEWS_BACKUP.relative_to(ROOT)}")
    else:
        print("No existing news.json - backup skipped")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def configure_stdout() -> None:
    """Windows 터미널(cp949)에서 한글·기호 출력 오류 방지."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def main() -> int:
    configure_stdout()
    report_date = datetime.now().date().isoformat()
    collected_at = utc_now_iso()
    day_dir = RAW_DIR / report_date
    raw_path = day_dir / "raw_items.json"
    dedup_path = day_dir / "deduplicated_items.json"

    print("=" * 60)
    print("Bio News Report - RSS collection")
    print(f"Report date: {report_date}")
    print("=" * 60)

    print("\n[1/4] Fetching RSS feeds...")
    raw_items = collect_all_raw(collected_at)
    raw_items = filter_recent(raw_items, report_date)
    write_json(raw_path, {"report_date": report_date, "collected_at": collected_at, "items": raw_items})
    print(f"  -> saved raw: {len(raw_items)} items")

    print("\n[2/4] Deduplicating...")
    deduped = deduplicate_items(raw_items)
    write_json(dedup_path, {"report_date": report_date, "collected_at": collected_at, "items": deduped})
    print(f"  -> saved deduplicated: {len(deduped)} items")

    print("\n[3/4] Building data/news.json...")
    existing = load_existing_reports()
    backup_news_json()
    daily = build_daily_report(report_date, deduped)
    merged = merge_reports(existing, daily)
    write_json(NEWS_JSON, {"reports": merged})

    print("\n[4/4] Done - files written:")
    created = [raw_path, dedup_path, NEWS_JSON]
    if NEWS_BACKUP.exists():
        created.insert(0, NEWS_BACKUP)
    for path in created:
        size_kb = path.stat().st_size / 1024 if path.exists() else 0
        print(f"  OK {path.relative_to(ROOT)}  ({size_kb:.1f} KB)")

    print("\nSummary:")
    print(f"  - raw items: {len(raw_items)}")
    print(f"  - after dedup: {len(deduped)}")
    print(f"  - today report news: {len(daily['items'])}")
    print(f"  - total reports in news.json: {len(merged)}")
    print("\nNext: npm run dev, then open /reports in the browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

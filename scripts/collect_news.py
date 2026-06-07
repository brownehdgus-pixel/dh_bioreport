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

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from google_translate import translate_to_korean  # noqa: E402
from env_local import load_env_local  # noqa: E402
from crawl_config import get_config, load_crawl_config  # noqa: E402

# ---------------------------------------------------------------------------
# 경로 · 설정
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw_data"
NEWS_JSON = DATA_DIR / "news.json"
NEWS_BACKUP = DATA_DIR / "news.backup.json"

USER_AGENT = "BioNewsReportCollector/0.1 (+https://github.com/local/bio-news-report)"

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
    cfg = get_config()
    all_items: list[dict[str, Any]] = []

    for feed in cfg.rss_feeds:
        if not feed.get("enabled", True):
            print(f"  - {feed['name']}: skipped (disabled)")
            continue
        try:
            batch = fetch_feed(
                feed_url=feed["url"],
                source_name=feed["name"],
                source_type=feed.get("sourceType", "rss"),
                query_keyword=feed.get("queryKeyword", ""),
                collected_at=collected_at,
            )
            all_items.extend(batch)
            print(f"  - {feed['name']}: {len(batch)} items")
        except Exception as exc:  # noqa: BLE001 — MVP: 한 소스 실패해도 계속
            print(f"  - {feed['name']}: FAILED ({exc})")

    for entry in cfg.google_news_queries:
        if not entry.get("enabled", True):
            print(f"  - Google News ({entry['query']}): skipped (disabled)")
            continue
        query = entry["query"]
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
    max_age = get_config().max_item_age_days
    cutoff = datetime.strptime(report_date, "%Y-%m-%d").date() - timedelta(days=max_age)
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


def filter_excluded(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keywords = get_config().exclude_keywords
    if not keywords:
        return items
    kept: list[dict[str, Any]] = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
        if any(kw in text for kw in keywords):
            continue
        kept.append(item)
    removed = len(items) - len(kept)
    if removed:
        print(f"  -> excluded {removed} item(s) by excludeKeywords")
    return kept


# ---------------------------------------------------------------------------
# 분류 · rule-based 텍스트
# ---------------------------------------------------------------------------


def classify_event_type(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    for event_type, kws in get_config().event_type_rules:
        if any(kw in text for kw in kws):
            return event_type
    return "general"


def classify_section(title: str, snippet: str, source: str) -> str:
    text = f"{title} {snippet} {source}".lower()
    for section_id, kws in get_config().section_rules:
        if any(kw in text for kw in kws):
            return section_id
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


def build_summary(title: str, snippet: str) -> str:
    """RSS snippet 기반 요약. 최대 ~8줄 분량(기존 220자 + 약 3줄)."""
    max_chars = 370
    base = snippet.strip() if snippet else title.strip()
    base = re.sub(r"\s+", " ", base)
    if not base:
        return title.strip()
    if base.lower().startswith(title.lower()[: min(20, len(title))]):
        combined = base
    else:
        combined = f"{title.strip()}. {base}"
    if len(combined) <= max_chars:
        return combined
    cut = combined[:max_chars].rsplit(" ", 1)[0]
    return cut.rstrip(".,;") + "…"


def build_significance(event_type: str, section: str) -> str:
    cfg = get_config()
    general = cfg.event_significance.get("general", "업계 동향 파악용 기사입니다.")
    base = cfg.event_significance.get(event_type, general)
    if section == "domestic":
        return f"{base} 국내 바이오·제약 업계 관점에서 공급망·파트너 영향을 함께 점검하면 좋다."
    return base


def score_importance(title: str, snippet: str, event_type: str) -> int:
    cfg = get_config()
    text = f"{title} {snippet}".lower()
    score = cfg.base_importance
    score += cfg.event_type_boosts.get(event_type, 0)
    for group in cfg.keyword_boosts:
        kws = [str(k).lower() for k in group.get("keywords") or []]
        boost = int(group.get("boost", 0))
        if boost and any(kw in text for kw in kws):
            score += boost
    return max(cfg.min_importance, min(cfg.max_importance, score))


def score_korea_relevance(title: str, snippet: str, section: str) -> int:
    cfg = get_config()
    if section == "domestic":
        return cfg.korea_domestic_score
    text = f"{title} {snippet}".lower()
    if any(kw in text for kw in cfg.korea_keywords):
        return cfg.korea_keyword_score
    if section in {"regulatory", "deal"}:
        return cfg.korea_regulatory_deal_score
    return cfg.korea_default_score


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
    cfg = get_config()
    sorted_raw = sorted(
        deduped,
        key=lambda r: (
            -(score_importance(r["title"], r.get("snippet", ""), classify_event_type(r["title"], r.get("snippet", "")))),
            r.get("published_at") or "",
        ),
    )[: cfg.max_items_in_report]

    items = [raw_to_news_item(raw, i + 1, report_date) for i, raw in enumerate(sorted_raw)]
    section_order = cfg.section_order
    used_sections = sorted(
        {item["section"] for item in items},
        key=lambda s: section_order.index(s) if s in section_order else 99,
    )

    summary_lines: list[str] = []
    for item in sorted(items, key=lambda x: -x["importanceScore"])[: cfg.max_summary_lines]:
        line = item["summary"]
        if len(line) > 290:
            line = line[:287].rsplit(" ", 1)[0] + "…"
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


def trim_reports_by_retention(
    reports: list[dict[str, Any]], anchor_date: str
) -> list[dict[str, Any]]:
    """news.json에 최근 reportRetentionDays 일만 유지."""
    retention = get_config().report_retention_days
    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    cutoff = anchor - timedelta(days=retention - 1)
    cutoff_str = cutoff.isoformat()
    trimmed = [r for r in reports if (r.get("reportDate") or "") >= cutoff_str]
    removed = len(reports) - len(trimmed)
    if removed:
        print(
            f"  -> retention: removed {removed} report(s) older than "
            f"{retention} days (before {cutoff_str})"
        )
    return trimmed


def prune_old_raw_data(anchor_date: str) -> None:
    """raw_data 폴더에서 보관 기간 지난 날짜 디렉터리 삭제."""
    if not RAW_DIR.exists():
        return
    retention = get_config().report_retention_days
    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    cutoff = anchor - timedelta(days=retention - 1)
    cutoff_str = cutoff.isoformat()
    removed = 0
    for child in RAW_DIR.iterdir():
        if not child.is_dir():
            continue
        if child.name < cutoff_str:
            import shutil

            shutil.rmtree(child)
            removed += 1
    if removed:
        print(f"  -> pruned {removed} raw_data folder(s) before {cutoff_str}")


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
    load_env_local()
    load_crawl_config()
    report_date = datetime.now().date().isoformat()
    collected_at = utc_now_iso()
    day_dir = RAW_DIR / report_date
    raw_path = day_dir / "raw_items.json"
    dedup_path = day_dir / "deduplicated_items.json"

    print("=" * 60)
    print("Bio News Report - RSS collection")
    print(f"Report date: {report_date}")
    print("=" * 60)

    print("\n[1/5] Fetching RSS feeds...")
    raw_items = collect_all_raw(collected_at)
    raw_items = filter_recent(raw_items, report_date)
    write_json(raw_path, {"report_date": report_date, "collected_at": collected_at, "items": raw_items})
    print(f"  -> saved raw: {len(raw_items)} items")

    print("\n[2/5] Deduplicating...")
    deduped = deduplicate_items(raw_items)
    deduped = filter_excluded(deduped)
    write_json(dedup_path, {"report_date": report_date, "collected_at": collected_at, "items": deduped})
    print(f"  -> saved deduplicated: {len(deduped)} items")

    print("\n[3/5] Building data/news.json...")
    existing = load_existing_reports()
    backup_news_json()
    daily = build_daily_report(report_date, deduped)
    merged = merge_reports(existing, daily)
    merged = trim_reports_by_retention(merged, report_date)
    write_json(NEWS_JSON, {"reports": merged})

    print("\n[4/5] Pruning old raw_data...")
    prune_old_raw_data(report_date)

    print("\n[5/5] Done - files written:")
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

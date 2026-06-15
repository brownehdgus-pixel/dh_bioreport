#!/usr/bin/env python3
"""
Bio Industry Daily Memo — RSS 뉴스 수집 MVP.

실행: python scripts/collect_news.py

출력:
  raw_data/YYYY-MM-DD/raw_items.json
  raw_data/YYYY-MM-DD/deduplicated_items.json
  raw_data/YYYY-MM-DD/selected_items.json
  data/news.backup.json  (기존 news.json 백업)
  data/news.json         (웹앱 표시용, 기존 구조)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
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

TRACKING_QUERY_KEYS = frozenset(
    {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "msclkid",
        "dclid",
        "igshid",
        "mkt_tok",
        "ref",
        "ref_src",
        "source",
        "vero_id",
        "vero_conv",
    }
)

_TITLE_PREFIX_RE = re.compile(
    r"^(?:breaking|exclusive|updated|update|watch|just in|analysis)\s*[:\-–—|]\s*",
    re.IGNORECASE,
)

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
    scheme = (parsed.scheme or "https").lower()
    if scheme == "http":
        scheme = "https"
    query = parse_qs(parsed.query, keep_blank_values=False)
    for key in list(query.keys()):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_QUERY_KEYS:
            del query[key]
    new_query = urlencode({k: v[0] if len(v) == 1 else v for k, v in query.items()}, doseq=True)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, parsed.netloc.lower(), path, "", new_query, ""))


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = unescape(title).strip().lower()
    t = re.sub(r"[\u2010-\u2015\u2212]", "-", t)
    t = re.sub(r"[\"'`´\u2018\u2019\u201c\u201d]", "", t)
    t = re.sub(r":+", " ", t)
    for _ in range(3):
        stripped = _TITLE_PREFIX_RE.sub("", t).strip()
        if stripped == t:
            break
        t = stripped
    for prefix in ("breaking ", "exclusive ", "updated ", "update "):
        if t.startswith(prefix):
            t = t[len(prefix) :].strip()
    t = re.sub(r"[^\w\s-]", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


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
# 과거 리포트 중복 제외 (historical dedup)
# ---------------------------------------------------------------------------


@dataclass
class HistoricalDedupStats:
    excluded_by_url: int = 0
    excluded_by_title: int = 0
    examples: list[str] = field(default_factory=list)


def report_date_of(report: dict[str, Any]) -> str:
    return str(report.get("reportDate") or report.get("report_date") or "")


def build_historical_index(
    reports: list[dict[str, Any]], exclude_report_date: str
) -> tuple[set[str], set[str], int]:
    """과거 리포트 URL/제목 인덱스. exclude_report_date(오늘) 리포트는 제외."""
    urls: set[str] = set()
    titles: set[str] = set()
    indexed_items = 0
    for report in reports:
        if report_date_of(report) == exclude_report_date:
            continue
        for item in report.get("items") or []:
            url = normalize_url(str(item.get("url") or ""))
            title = normalize_title(str(item.get("title") or ""))
            if url:
                urls.add(url)
            if title:
                titles.add(title)
            indexed_items += 1
    return urls, titles, indexed_items


def filter_historical_duplicates(
    items: list[dict[str, Any]],
    historical_urls: set[str],
    historical_titles: set[str],
) -> tuple[list[dict[str, Any]], HistoricalDedupStats]:
    dedup_cfg = get_config().deduplication
    if not dedup_cfg.exclude_previously_reported:
        return items, HistoricalDedupStats()

    selected: list[dict[str, Any]] = []
    stats = HistoricalDedupStats()

    for item in items:
        url = item.get("normalized_url") or normalize_url(str(item.get("url") or ""))
        title_norm = normalize_title(str(item.get("title") or ""))
        title_display = str(item.get("title") or "").strip()

        if dedup_cfg.exclude_same_url and url and url in historical_urls:
            stats.excluded_by_url += 1
            if len(stats.examples) < 5:
                stats.examples.append(title_display or url)
            continue
        if dedup_cfg.exclude_same_title and title_norm and title_norm in historical_titles:
            stats.excluded_by_title += 1
            if len(stats.examples) < 5:
                stats.examples.append(title_display or title_norm)
            continue
        selected.append(item)

    return selected, stats


def log_historical_dedup(indexed_items: int, stats: HistoricalDedupStats) -> None:
    dedup_cfg = get_config().deduplication
    if not dedup_cfg.exclude_previously_reported:
        print("  -> historical dedup: disabled (excludePreviouslyReported=false)")
        return
    print(f"  -> historical index: {indexed_items} past report item(s) (today excluded)")
    print(f"[HISTORICAL_DEDUP] excluded by url: {stats.excluded_by_url}")
    print(f"[HISTORICAL_DEDUP] excluded by title: {stats.excluded_by_title}")
    if stats.examples:
        print("[HISTORICAL_DEDUP] examples:")
        for example in stats.examples:
            print(f"  - {example}")


# ---------------------------------------------------------------------------
# v2: bio gate · origin · investor scoring · quota selection
# ---------------------------------------------------------------------------

NOISE_LICENSE_PHRASES = (
    "pilot license",
    "driver license",
    "driving license",
    "software license",
    "gaming license",
    "flying without",
    "proper license",
)

BIO_LICENSE_PHRASES = (
    "license agreement",
    "license out",
    "license in",
    "licensing deal",
    "licensing agreement",
    "exclusive license",
    "drug license",
    "pharma licensing",
)

CLINICAL_TOPLINE_PHRASES = (
    "topline results",
    "top-line results",
    "phase 3 topline",
    "phase 2 topline",
    "phase iii topline",
    "phase ii topline",
)


@dataclass
class BioGateStats:
    excluded_by_noise: int = 0
    excluded_by_no_bio_anchor: int = 0


@dataclass
class OriginStats:
    domestic: int = 0
    global_count: int = 0
    by_keyword: int = 0
    by_source: int = 0
    by_hangul: int = 0


@dataclass
class QuotaStats:
    paper: int = 0
    domestic: int = 0
    global_count: int = 0
    domestic_shortfall: bool = False


def combined_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("snippet") or ""),
        str(item.get("source") or ""),
        str(item.get("query_keyword") or ""),
    ]
    return " ".join(parts)


def hangul_ratio(text: str) -> float:
    if not text:
        return 0.0
    hangul = len(re.findall(r"[\uAC00-\uD7A3]", text))
    total = len(re.sub(r"\s", "", text))
    if total == 0:
        return 0.0
    return hangul / total


def has_bio_anchor(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in get_config().bio_gate.anchor_keywords)


def is_noise_license_context(text: str) -> bool:
    low = text.lower()
    if any(p in low for p in NOISE_LICENSE_PHRASES):
        return True
    if "license" in low and not any(p in low for p in BIO_LICENSE_PHRASES):
        if not has_bio_anchor(low):
            return True
    if "topline" in low or "top-line" in low or "top line" in low:
        if any(p in low for p in CLINICAL_TOPLINE_PHRASES):
            return False
        if not has_bio_anchor(low):
            return True
    return False


def is_noise_excluded(text: str) -> bool:
    low = text.lower()
    if any(kw in low for kw in get_config().bio_gate.noise_keywords):
        return True
    return is_noise_license_context(low)


def is_rss_trusted(source: str) -> bool:
    return source in get_config().bio_gate.rss_trust_sources


def passes_bio_gate(item: dict[str, Any]) -> bool:
    text = combined_text(item)
    if is_noise_excluded(text):
        return False
    source_type = str(item.get("source_type") or "")
    source = str(item.get("source") or "")
    if source_type != "google_news_rss" and is_rss_trusted(source):
        return True
    return has_bio_anchor(text)


def apply_bio_gate(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], BioGateStats]:
    stats = BioGateStats()
    eligible: list[dict[str, Any]] = []
    for item in items:
        text = combined_text(item)
        if is_noise_excluded(text):
            stats.excluded_by_noise += 1
            continue
        if not passes_bio_gate(item):
            stats.excluded_by_no_bio_anchor += 1
            continue
        eligible.append(item)
    return eligible, stats


def classify_origin(item: dict[str, Any]) -> tuple[str, str | None]:
    """Returns (origin, reason) where reason is keyword|source|hangul|None."""
    cfg = get_config().domestic
    text = combined_text(item)
    low = text.lower()
    source = str(item.get("source") or "")

    if any(kw in low for kw in cfg.keywords):
        return "domestic", "keyword"
    if source in cfg.source_allowlist:
        return "domestic", "source"
    if hangul_ratio(text) >= cfg.hangul_ratio_threshold and has_bio_anchor(low):
        return "domestic", "hangul"
    return "global", None


def classify_section(title: str, snippet: str, source: str) -> str:
    text = f"{title} {snippet} {source}".lower()
    skip = {"domestic", "global"}
    for section_id, kws in get_config().section_rules:
        if section_id in skip:
            continue
        if any(kw in text for kw in kws):
            return section_id
    return "general"


def extract_company_hint(title: str) -> str:
    title = title.strip()
    if not title:
        return "해당 기업"
    for sep in (" - ", " – ", " — ", " | ", ":"):
        if sep in title:
            return title.split(sep)[0].strip()[:60]
    match = re.match(r"^([A-Z][A-Za-z0-9&.\- ]{1,40})", title)
    if match:
        return match.group(1).strip()
    return title[:40].strip()


def score_investor_relevance(
    title: str,
    snippet: str,
    event_type: str,
    section: str,
    origin: str,
) -> int:
    cfg = get_config()
    text = f"{title} {snippet}".lower()
    score = cfg.base_importance
    score += cfg.event_type_boosts.get(event_type, 0)

    if origin == "domestic":
        score += 2
    if any(kw in text for kw in cfg.domestic.priority_keywords):
        score += 2

    global_boosts = ("fda", "ema", "phase 3", "phase iii", "acquisition", "billion", "merger")
    if any(kw in text for kw in global_boosts):
        score += 1

    if event_type == "market" and section != "deal":
        score -= 1

    if section == "paper":
        score = min(score, 7)

    return max(cfg.min_importance, min(cfg.max_importance, score))


def build_investment_takeaway(
    event_type: str,
    section: str,
    origin: str,
    title: str,
) -> str:
    company = extract_company_hint(title)
    if origin == "domestic":
        if event_type == "funding":
            return (
                f"국내 바이오 VC/창투의 후속 라운드·밸류에이션 벤치마크로 "
                f"활용 가능한 {company} 투자유치 이벤트."
            )
        if event_type in {"regulatory", "clinical"}:
            return (
                f"{company} 규제·임상 마일스톤은 국내 동종·동일 타깃 "
                f"파이프라인 리스크·타임라인 재평가에 참고할 만하다."
            )
        if event_type == "partnership" or section == "deal":
            return (
                f"국내 BD·기술이전 협상 시 딜 컴프 및 마일스톤 구조 "
                f"참고 사례로 {company} 거래를 모니터링할 필요가 있다."
            )
        return (
            f"국내 바이오·제약 포트폴리오·딜 소싱 관점에서 "
            f"{company} 관련 후속 공시·파트너 동향을 추적할 가치가 있다."
        )

    if event_type in {"regulatory", "clinical"} or section == "regulatory":
        agency = "FDA/EMA" if "fda" in title.lower() or "ema" in title.lower() else "글로벌 규제"
        return (
            f"동일 적응증·모달리티 국내 파이프라인의 규제 경로·타임라인 "
            f"재평가 트리거가 될 수 있는 {agency} 마일스톤."
        )
    if event_type == "partnership" or section == "deal":
        return (
            "국내 BD/라이선스 아웃·인 협상 시 딜 컴프 및 "
            "마일스톤 구조 참고 사례."
        )
    if event_type == "funding":
        return "글로벌 바이오 VC 센티먼트·밸류에이션 벤치마크로 활용 가능한 자금 조달 이벤트."
    if section == "modality":
        return "신규 모달리티·플랫폼 경쟁 구도 변화를 점검할 만한 기술·파이프라인 신호."
    if section == "paper":
        return "학술 데이터가 규제·BD 논의에 반영되는지 후속 코멘트를 확인할 가치가 있다."
    return "글로벌 바이오 섹터 동향·경쟁사 모니터링 맥락에서 투자 의사결정 참고 자료."


def enrich_raw_item(raw: dict[str, Any]) -> dict[str, Any]:
    title = raw["title"]
    snippet = raw.get("snippet") or ""
    origin, origin_reason = classify_origin(raw)
    section = classify_section(title, snippet, raw.get("source", ""))
    event_type = classify_event_type(title, snippet)
    score = score_investor_relevance(title, snippet, event_type, section, origin)
    enriched = dict(raw)
    enriched["origin"] = origin
    enriched["origin_reason"] = origin_reason
    enriched["section"] = section
    enriched["event_type"] = event_type
    enriched["investor_relevance_score"] = score
    return enriched


def _take_top(pool: list[dict[str, Any]], n: int, used: set[str]) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    for item in sorted(pool, key=lambda x: -x["investor_relevance_score"]):
        rid = item.get("raw_id") or item.get("normalized_url") or ""
        if rid in used:
            continue
        picked.append(item)
        used.add(rid)
        if len(picked) >= n:
            break
    return picked


def select_by_quota(enriched: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], QuotaStats]:
    cfg = get_config().quotas
    stats = QuotaStats()
    used: set[str] = set()
    selected: list[dict[str, Any]] = []

    paper_pool = [i for i in enriched if i.get("section") == "paper"]
    paper_picked = _take_top(paper_pool, cfg.paper_max, used)
    selected.extend(paper_picked)
    stats.paper = len(paper_picked)

    domestic_pool = [i for i in enriched if i.get("origin") == "domestic"]
    domestic_target = min(cfg.domestic_max, max(cfg.domestic_min, len(domestic_pool)))
    if len(domestic_pool) < cfg.domestic_min:
        domestic_target = len(domestic_pool)
        stats.domestic_shortfall = True
    domestic_picked = _take_top(domestic_pool, domestic_target, used)
    selected.extend(domestic_picked)
    stats.domestic = len(domestic_picked)

    global_pool = [i for i in enriched if i.get("origin") == "global"]
    remaining = cfg.total_items - len(selected)
    global_target = min(cfg.global_max, remaining, len(global_pool))
    if global_target < cfg.global_min and remaining >= cfg.global_min:
        global_target = min(remaining, len(global_pool))
    global_picked = _take_top(global_pool, global_target, used)
    selected.extend(global_picked)
    stats.global_count = len(global_picked)

    if len(selected) < cfg.total_items:
        filler = _take_top(enriched, cfg.total_items - len(selected), used)
        selected.extend(filler)

    selected = selected[: cfg.total_items]
    selected.sort(key=lambda x: -x["investor_relevance_score"])
    return selected, stats


def build_headline(title: str, max_len: int = 120) -> str:
    headline = title.strip()
    for sep in (" - ", " – ", " — ", " | "):
        if sep in headline:
            parts = headline.rsplit(sep, 1)
            if len(parts[0]) >= 20:
                headline = parts[0].strip()
                break
    if len(headline) > max_len:
        headline = headline[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return headline


def build_executive_highlights(
    items: list[dict[str, Any]], report_date: str
) -> list[dict[str, Any]]:
    cfg = get_config()
    pool = sorted(items, key=lambda x: -x["investorRelevanceScore"])
    highlights = pool[: cfg.max_summary_lines]

    domestic_in = [h for h in highlights if h.get("origin") == "domestic"]
    if not domestic_in and pool:
        best_domestic = next((i for i in pool if i.get("origin") == "domestic"), None)
        if best_domestic and len(highlights) >= cfg.max_summary_lines:
            highlights[-1] = best_domestic
        elif best_domestic:
            highlights.append(best_domestic)
        highlights = highlights[: cfg.max_summary_lines]

    result: list[dict[str, Any]] = []
    for rank, item in enumerate(highlights, start=1):
        result.append(
            {
                "rank": rank,
                "itemId": item["id"],
                "headline": build_headline(item["title"]),
                "investmentTakeaway": item.get("investmentTakeaway", ""),
            }
        )
    return result


def validate_report_quality(items: list[dict[str, Any]]) -> None:
    top10 = sorted(items, key=lambda x: -x["investorRelevanceScore"])[:10]
    domestic_top10 = sum(1 for i in top10 if i.get("origin") == "domestic")
    if domestic_top10 < 2:
        print(f"[VALIDATE] WARN top10 domestic={domestic_top10} (target >= 2)")
    for item in top10:
        raw_like = {
            "title": item["title"],
            "snippet": item.get("summary", ""),
            "source": item.get("source", ""),
            "source_type": "google_news_rss" if item.get("source") == "Google News" else "rss",
        }
        if is_noise_excluded(combined_text(raw_like)):
            print(f"[VALIDATE] WARN noise in top10: {item['title'][:80]}")


# ---------------------------------------------------------------------------
# 분류 · rule-based 텍스트
# ---------------------------------------------------------------------------


def classify_event_type(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    for event_type, kws in get_config().event_type_rules:
        if any(kw in text for kw in kws):
            return event_type
    return "general"


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


def build_significance(event_type: str, origin: str) -> str:
    """Deprecated — kept for JSON backward compat; mirrors investmentTakeaway."""
    cfg = get_config()
    general = cfg.event_significance.get("general", "업계 동향 파악용 기사입니다.")
    base = cfg.event_significance.get(event_type, general)
    if origin == "domestic":
        return f"{base} 국내 바이오·제약 업계 관점에서 공급망·파트너 영향을 함께 점검하면 좋다."
    return base


def raw_to_news_item(enriched: dict[str, Any], index: int, report_date: str) -> dict[str, Any]:
    title = enriched["title"]
    snippet = enriched.get("snippet") or ""
    section = enriched.get("section") or classify_section(title, snippet, enriched.get("source", ""))
    event_type = enriched.get("event_type") or classify_event_type(title, snippet)
    origin = enriched.get("origin") or "global"
    investor_score = enriched.get("investor_relevance_score") or score_investor_relevance(
        title, snippet, event_type, section, origin
    )
    item_date = enriched.get("published_at") or report_date
    takeaway = build_investment_takeaway(event_type, section, origin, title)

    summary_en = build_summary(title, snippet)
    return {
        "id": f"{report_date}-{index:04d}",
        "title": title,
        "source": enriched.get("source", "Unknown"),
        "date": item_date,
        "origin": origin,
        "section": section,
        "eventType": event_type,
        "summary": translate_to_korean(summary_en),
        "significance": build_significance(event_type, origin),
        "investmentTakeaway": takeaway,
        "keywords": extract_keywords(title, snippet, enriched.get("query_keyword", "")),
        "importanceScore": investor_score,
        "investorRelevanceScore": investor_score,
        "koreaRelevanceScore": 8 if origin == "domestic" else 4,
        "url": enriched.get("url") or "#",
    }


def build_daily_report(
    report_date: str,
    enriched_selected: list[dict[str, Any]],
) -> dict[str, Any]:
    cfg = get_config()
    items = [raw_to_news_item(raw, i + 1, report_date) for i, raw in enumerate(enriched_selected)]

    origins_present = {item["origin"] for item in items}
    content_sections = sorted(
        {item["section"] for item in items if item["section"] not in ("domestic", "global")},
        key=lambda s: cfg.section_order.index(s) if s in cfg.section_order else 99,
    )
    used_sections: list[str] = []
    if "domestic" in origins_present:
        used_sections.append("domestic")
    if "global" in origins_present:
        used_sections.append("global")
    used_sections.extend(s for s in content_sections if s not in used_sections)

    executive_highlights = build_executive_highlights(items, report_date)
    summary_lines = [h["investmentTakeaway"] for h in executive_highlights]
    if not summary_lines:
        summary_lines = ["수집된 기사가 없습니다. RSS 소스 연결 상태를 확인해 주세요."]

    validate_report_quality(items)

    return {
        "reportDate": report_date,
        "title": f"{report_date} 바이오 투자 인텔리전스",
        "executiveHighlights": executive_highlights,
        "summaryLines": summary_lines,
        "sections": used_sections if used_sections else ["global", "regulatory"],
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
    selected_path = day_dir / "selected_items.json"

    print("=" * 60)
    print("Bio News Report - RSS collection")
    print(f"Report date: {report_date}")
    print("=" * 60)

    print("\n[1/7] Fetching RSS feeds...")
    all_raw = collect_all_raw(collected_at)
    write_json(
        raw_path,
        {"report_date": report_date, "collected_at": collected_at, "items": all_raw},
    )
    print(f"  -> saved raw: {len(all_raw)} items")

    print("\n[2/7] Age filter...")
    raw_items = filter_recent(all_raw, report_date)
    after_age_filter = len(raw_items)
    print(f"  -> after age filter: {after_age_filter} items")

    print("\n[3/7] Deduplicating (within batch)...")
    deduped = deduplicate_items(raw_items)
    deduped = filter_excluded(deduped)
    after_url_dedup = len(deduped)
    write_json(
        dedup_path,
        {"report_date": report_date, "collected_at": collected_at, "items": deduped},
    )
    print(f"  -> saved deduplicated: {after_url_dedup} items")

    print("\n[4/7] Historical dedup (past reports)...")
    existing = load_existing_reports()
    hist_urls, hist_titles, hist_index_count = build_historical_index(existing, report_date)
    selected, hist_stats = filter_historical_duplicates(deduped, hist_urls, hist_titles)
    log_historical_dedup(hist_index_count, hist_stats)
    print(f"  -> after historical dedup: {len(selected)} items")

    print("\n[5/7] Bio gate + investor scoring + quota selection...")
    eligible, gate_stats = apply_bio_gate(selected)
    print(f"  -> after_bio_gate: {len(eligible)} items")
    print(f"  -> excluded_by_noise: {gate_stats.excluded_by_noise}")
    print(f"  -> excluded_by_no_bio_anchor: {gate_stats.excluded_by_no_bio_anchor}")

    enriched = [enrich_raw_item(item) for item in eligible]
    origin_stats = OriginStats()
    for item in enriched:
        if item.get("origin") == "domestic":
            origin_stats.domestic += 1
            reason = item.get("origin_reason")
            if reason == "keyword":
                origin_stats.by_keyword += 1
            elif reason == "source":
                origin_stats.by_source += 1
            elif reason == "hangul":
                origin_stats.by_hangul += 1
        else:
            origin_stats.global_count += 1
    print(
        f"[ORIGIN] domestic: {origin_stats.domestic} / global: {origin_stats.global_count} "
        f"(keyword={origin_stats.by_keyword}, source={origin_stats.by_source}, "
        f"hangul={origin_stats.by_hangul})"
    )

    quota_selected, quota_stats = select_by_quota(enriched)
    if quota_stats.domestic_shortfall:
        print(
            f"[QUOTA] WARN domestic shortfall: {quota_stats.domestic} "
            f"(target {get_config().quotas.domestic_min}-{get_config().quotas.domestic_max})"
        )
    print(
        f"  -> quota paper={quota_stats.paper}, domestic={quota_stats.domestic}, "
        f"global={quota_stats.global_count}"
    )
    write_json(
        selected_path,
        {"report_date": report_date, "collected_at": collected_at, "items": quota_selected},
    )
    print(f"  -> saved selected (quota): {len(quota_selected)} items")

    if len(quota_selected) == 0:
        print(
            "[WARN] No items left after bio gate / quota — today's report will be empty. "
            "Check crawl window, sources, or gate settings."
        )

    print("\n[6/7] Building data/news.json...")
    backup_news_json()
    daily = build_daily_report(report_date, quota_selected)
    final_report_items = len(daily["items"])
    merged = merge_reports(existing, daily)
    merged = trim_reports_by_retention(merged, report_date)
    write_json(NEWS_JSON, {"reports": merged})

    print("\n[7/7] Pruning old raw_data...")
    prune_old_raw_data(report_date)

    print("\nDone - files written:")
    created = [raw_path, dedup_path, selected_path, NEWS_JSON]
    if NEWS_BACKUP.exists():
        created.insert(0, NEWS_BACKUP)
    for path in created:
        size_kb = path.stat().st_size / 1024 if path.exists() else 0
        print(f"  OK {path.relative_to(ROOT)}  ({size_kb:.1f} KB)")

    print("\nSummary:")
    print(f"  - raw_items: {len(all_raw)}")
    print(f"  - after_age_filter: {after_age_filter}")
    print(f"  - after_url_dedup: {after_url_dedup}")
    print(f"  - excluded_by_historical_url: {hist_stats.excluded_by_url}")
    print(f"  - excluded_by_historical_title: {hist_stats.excluded_by_title}")
    print(f"  - after_bio_gate: {len(eligible)}")
    print(f"  - excluded_by_noise: {gate_stats.excluded_by_noise}")
    print(f"  - excluded_by_no_bio_anchor: {gate_stats.excluded_by_no_bio_anchor}")
    print(f"  - quota_domestic: {quota_stats.domestic}")
    print(f"  - quota_global: {quota_stats.global_count}")
    print(f"  - quota_paper: {quota_stats.paper}")
    print(f"  - selected_items: {len(quota_selected)}")
    print(f"  - final_report_items: {final_report_items}")
    print(f"  - executive_highlights: {len(daily.get('executiveHighlights', []))}")
    print(f"  - total reports in news.json: {len(merged)}")
    print("\nNext: npm run dev, then open /reports in the browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

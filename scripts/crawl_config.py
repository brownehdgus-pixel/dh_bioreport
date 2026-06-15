"""Load and validate data/crawl_config.json for the news crawler."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "crawl_config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "limits": {
        "maxItemAgeDays": 14,
        "maxItemsInReport": 40,
        "maxSummaryLines": 5,
        "reportRetentionDays": 90,
    },
    "sources": {"rssFeeds": [], "googleNewsQueries": []},
    "scoring": {
        "baseImportance": 5,
        "minImportance": 1,
        "maxImportance": 10,
        "eventTypeBoosts": {},
        "keywordBoosts": [],
        "koreaKeywords": ["korea", "korean", "mfds", "seoul", "asia pacific"],
        "koreaDomesticScore": 8,
        "koreaRegulatoryDealScore": 5,
        "koreaDefaultScore": 4,
        "koreaKeywordScore": 6,
    },
    "classification": {
        "sectionOrder": ["domestic", "global", "regulatory", "deal", "modality", "paper"],
        "eventTypes": [],
        "sections": [],
    },
    "excludeKeywords": [],
    "deduplication": {
        "excludePreviouslyReported": True,
        "excludeSameUrl": True,
        "excludeSameTitle": True,
    },
    "quotas": {
        "totalItems": 40,
        "paperMax": 3,
        "domesticMin": 8,
        "domesticMax": 12,
        "globalMin": 20,
        "globalMax": 24,
    },
    "domestic": {
        "keywords": [
            "korea", "korean", "south korea", "seoul", "mfds", "kosdaq", "kospi",
            "국내", "한국", "투자유치", "기술이전", "식약처", "코스닥", "kddf",
            "벤처", "창업", "공시", "병원창업", "교수창업",
        ],
        "sourceAllowlist": ["바이오스펙테이터", "히트뉴스"],
        "hangulRatioThreshold": 0.30,
        "priorityKeywords": [
            "투자유치", "기술이전", "식약처", "허가", "임상", "공시", "kddf", "창업",
        ],
    },
    "bioGate": {
        "anchorKeywords": [
            "biotech", "pharma", "therapeutics", "clinical", "fda", "ema", "mfds",
            "ind", "nda", "bla", "oncology", "gene therapy", "cell therapy",
            "adc", "tpd", "rna", "mrna", "diagnostic", "healthcare",
            "신약", "바이오", "제약", "임상", "식약처", "허가", "기술이전", "투자유치",
        ],
        "noiseKeywords": [
            "airline", "pilot", "air canada", "driver license", "flying without",
            "software license", "gaming license", "entertainment", "music", "movie",
            "actor", "sports", "crypto", "bitcoin", "nft",
        ],
        "rssTrustSources": [
            "Fierce Biotech", "Fierce Pharma", "BioPharma Dive", "Business Wire",
            "Endpoints News", "Labiotech", "바이오스펙테이터", "히트뉴스",
        ],
    },
    "eventSignificance": {"general": "업계 동향 파악용 기사입니다."},
}


@dataclass
class DeduplicationConfig:
    exclude_previously_reported: bool = True
    exclude_same_url: bool = True
    exclude_same_title: bool = True


@dataclass
class QuotaConfig:
    total_items: int = 40
    paper_max: int = 3
    domestic_min: int = 8
    domestic_max: int = 12
    global_min: int = 20
    global_max: int = 24


@dataclass
class DomesticConfig:
    keywords: list[str]
    source_allowlist: list[str]
    hangul_ratio_threshold: float
    priority_keywords: list[str]


@dataclass
class BioGateConfig:
    anchor_keywords: list[str]
    noise_keywords: list[str]
    rss_trust_sources: list[str]


@dataclass
class CrawlConfig:
    version: int
    max_item_age_days: int
    max_items_in_report: int
    max_summary_lines: int
    report_retention_days: int
    rss_feeds: list[dict[str, Any]]
    google_news_queries: list[dict[str, Any]]
    base_importance: int
    min_importance: int
    max_importance: int
    event_type_boosts: dict[str, int]
    keyword_boosts: list[dict[str, Any]]
    korea_keywords: list[str]
    korea_domestic_score: int
    korea_regulatory_deal_score: int
    korea_default_score: int
    korea_keyword_score: int
    section_order: list[str]
    event_type_rules: list[tuple[str, list[str]]]
    section_rules: list[tuple[str, list[str]]]
    exclude_keywords: list[str]
    event_significance: dict[str, str]
    deduplication: DeduplicationConfig
    quotas: QuotaConfig
    domestic: DomesticConfig
    bio_gate: BioGateConfig
    raw: dict[str, Any] = field(repr=False)


class ConfigValidationError(ValueError):
    pass


def _clamp_int(value: Any, lo: int, hi: int, name: str) -> int:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigValidationError(f"{name} must be a number")
    n = int(value)
    if n < lo or n > hi:
        raise ConfigValidationError(f"{name} must be between {lo} and {hi}")
    return n


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    return bool(value)


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], val)
        else:
            result[key] = val
    return result


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize config dict. Raises ConfigValidationError."""
    merged = _merge_dict(DEFAULT_CONFIG, data)

    limits = merged["limits"]
    limits["maxItemAgeDays"] = _clamp_int(
        limits.get("maxItemAgeDays"), 1, 90, "limits.maxItemAgeDays"
    )
    limits["maxItemsInReport"] = _clamp_int(
        limits.get("maxItemsInReport"), 1, 200, "limits.maxItemsInReport"
    )
    limits["maxSummaryLines"] = _clamp_int(
        limits.get("maxSummaryLines"), 1, 20, "limits.maxSummaryLines"
    )
    limits["reportRetentionDays"] = _clamp_int(
        limits.get("reportRetentionDays"), 7, 365, "limits.reportRetentionDays"
    )

    scoring = merged["scoring"]
    scoring["baseImportance"] = _clamp_int(
        scoring.get("baseImportance"), 1, 10, "scoring.baseImportance"
    )
    scoring["minImportance"] = _clamp_int(
        scoring.get("minImportance"), 1, 10, "scoring.minImportance"
    )
    scoring["maxImportance"] = _clamp_int(
        scoring.get("maxImportance"), 1, 10, "scoring.maxImportance"
    )
    if scoring["minImportance"] > scoring["maxImportance"]:
        raise ConfigValidationError("scoring.minImportance cannot exceed maxImportance")

    sources = merged["sources"]
    rss_feeds = sources.get("rssFeeds") or []
    if not isinstance(rss_feeds, list):
        raise ConfigValidationError("sources.rssFeeds must be an array")

    normalized_rss: list[dict[str, Any]] = []
    for i, feed in enumerate(rss_feeds):
        if not isinstance(feed, dict):
            raise ConfigValidationError(f"sources.rssFeeds[{i}] must be an object")
        name = str(feed.get("name", "")).strip()
        url = str(feed.get("url", "")).strip()
        if not name or not url:
            raise ConfigValidationError(f"sources.rssFeeds[{i}] requires name and url")
        normalized_rss.append(
            {
                "name": name,
                "url": url,
                "enabled": _as_bool(feed.get("enabled"), True),
                "sourceType": str(feed.get("sourceType", "rss")),
                "queryKeyword": str(feed.get("queryKeyword", "")),
            }
        )
    sources["rssFeeds"] = normalized_rss

    google_queries = sources.get("googleNewsQueries") or []
    if not isinstance(google_queries, list):
        raise ConfigValidationError("sources.googleNewsQueries must be an array")

    normalized_google: list[dict[str, Any]] = []
    for i, item in enumerate(google_queries):
        if isinstance(item, str):
            query = item.strip()
            enabled = True
        elif isinstance(item, dict):
            query = str(item.get("query", "")).strip()
            enabled = _as_bool(item.get("enabled"), True)
        else:
            raise ConfigValidationError(f"sources.googleNewsQueries[{i}] invalid")
        if query:
            normalized_google.append({"query": query, "enabled": enabled})
    sources["googleNewsQueries"] = normalized_google

    exclude = merged.get("excludeKeywords") or []
    if not isinstance(exclude, list):
        raise ConfigValidationError("excludeKeywords must be an array")
    merged["excludeKeywords"] = [str(k).strip().lower() for k in exclude if str(k).strip()]

    dedup = merged.get("deduplication")
    if dedup is None:
        dedup = {}
    if not isinstance(dedup, dict):
        raise ConfigValidationError("deduplication must be an object")
    merged["deduplication"] = {
        "excludePreviouslyReported": _as_bool(dedup.get("excludePreviouslyReported"), True),
        "excludeSameUrl": _as_bool(dedup.get("excludeSameUrl"), True),
        "excludeSameTitle": _as_bool(dedup.get("excludeSameTitle"), True),
    }

    classification = merged["classification"]
    for key in ("eventTypes", "sections"):
        rules = classification.get(key) or []
        if not isinstance(rules, list):
            raise ConfigValidationError(f"classification.{key} must be an array")
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ConfigValidationError(f"classification.{key}[{i}] must be an object")
            if not str(rule.get("id", "")).strip():
                raise ConfigValidationError(f"classification.{key}[{i}] requires id")
            kws = rule.get("keywords") or []
            if not isinstance(kws, list):
                raise ConfigValidationError(f"classification.{key}[{i}].keywords must be an array")

    section_order = classification.get("sectionOrder") or DEFAULT_CONFIG["classification"]["sectionOrder"]
    if not isinstance(section_order, list):
        raise ConfigValidationError("classification.sectionOrder must be an array")
    classification["sectionOrder"] = [str(s) for s in section_order]

    merged["version"] = int(merged.get("version", 1))
    return merged


def _to_crawl_config(data: dict[str, Any]) -> CrawlConfig:
    limits = data["limits"]
    scoring = data["scoring"]
    classification = data["classification"]
    sources = data["sources"]

    event_rules: list[tuple[str, list[str]]] = []
    for rule in classification.get("eventTypes") or []:
        event_rules.append(
            (str(rule["id"]), [str(k).lower() for k in rule.get("keywords") or []])
        )

    section_rules: list[tuple[str, list[str]]] = []
    for rule in classification.get("sections") or []:
        section_rules.append(
            (str(rule["id"]), [str(k).lower() for k in rule.get("keywords") or []])
        )

    event_boosts: dict[str, int] = {}
    for key, val in (scoring.get("eventTypeBoosts") or {}).items():
        event_boosts[str(key)] = int(val)

    dedup_raw = data.get("deduplication") or {}
    dedup_cfg = DeduplicationConfig(
        exclude_previously_reported=_as_bool(dedup_raw.get("excludePreviouslyReported"), True),
        exclude_same_url=_as_bool(dedup_raw.get("excludeSameUrl"), True),
        exclude_same_title=_as_bool(dedup_raw.get("excludeSameTitle"), True),
    )

    quotas_raw = data.get("quotas") or {}
    quotas_cfg = QuotaConfig(
        total_items=int(quotas_raw.get("totalItems", 40)),
        paper_max=int(quotas_raw.get("paperMax", 3)),
        domestic_min=int(quotas_raw.get("domesticMin", 8)),
        domestic_max=int(quotas_raw.get("domesticMax", 12)),
        global_min=int(quotas_raw.get("globalMin", 20)),
        global_max=int(quotas_raw.get("globalMax", 24)),
    )

    domestic_raw = data.get("domestic") or {}
    domestic_cfg = DomesticConfig(
        keywords=[str(k).lower() for k in domestic_raw.get("keywords") or []],
        source_allowlist=[str(s) for s in domestic_raw.get("sourceAllowlist") or []],
        hangul_ratio_threshold=float(domestic_raw.get("hangulRatioThreshold", 0.30)),
        priority_keywords=[str(k).lower() for k in domestic_raw.get("priorityKeywords") or []],
    )

    gate_raw = data.get("bioGate") or {}
    gate_cfg = BioGateConfig(
        anchor_keywords=[str(k).lower() for k in gate_raw.get("anchorKeywords") or []],
        noise_keywords=[str(k).lower() for k in gate_raw.get("noiseKeywords") or []],
        rss_trust_sources=[str(s) for s in gate_raw.get("rssTrustSources") or []],
    )

    return CrawlConfig(
        version=int(data.get("version", 1)),
        max_item_age_days=int(limits["maxItemAgeDays"]),
        max_items_in_report=int(limits["maxItemsInReport"]),
        max_summary_lines=int(limits["maxSummaryLines"]),
        report_retention_days=int(limits["reportRetentionDays"]),
        rss_feeds=list(sources.get("rssFeeds") or []),
        google_news_queries=list(sources.get("googleNewsQueries") or []),
        base_importance=int(scoring["baseImportance"]),
        min_importance=int(scoring["minImportance"]),
        max_importance=int(scoring["maxImportance"]),
        event_type_boosts=event_boosts,
        keyword_boosts=list(scoring.get("keywordBoosts") or []),
        korea_keywords=[str(k).lower() for k in scoring.get("koreaKeywords") or []],
        korea_domestic_score=int(scoring.get("koreaDomesticScore", 8)),
        korea_regulatory_deal_score=int(scoring.get("koreaRegulatoryDealScore", 5)),
        korea_default_score=int(scoring.get("koreaDefaultScore", 4)),
        korea_keyword_score=int(scoring.get("koreaKeywordScore", 6)),
        section_order=list(classification.get("sectionOrder") or []),
        event_type_rules=event_rules,
        section_rules=section_rules,
        exclude_keywords=list(data.get("excludeKeywords") or []),
        event_significance=dict(data.get("eventSignificance") or {}),
        deduplication=dedup_cfg,
        quotas=quotas_cfg,
        domestic=domestic_cfg,
        bio_gate=gate_cfg,
        raw=data,
    )


_CONFIG: CrawlConfig | None = None


def load_crawl_config(*, path: Path | None = None, force_reload: bool = False) -> CrawlConfig:
    global _CONFIG
    if _CONFIG is not None and not force_reload:
        return _CONFIG

    config_path = path or CONFIG_PATH
    data: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)

    if config_path.exists():
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = _merge_dict(data, loaded)
            else:
                print(f"  [config] {config_path.name} is not an object — using defaults")
        except json.JSONDecodeError as exc:
            print(f"  [config] JSON parse error ({exc}) — using defaults")
    else:
        print(f"  [config] {config_path.relative_to(ROOT)} not found — using defaults")

    try:
        validated = validate_config(data)
    except ConfigValidationError as exc:
        print(f"  [config] validation failed ({exc}) — using defaults")
        validated = validate_config(copy.deepcopy(DEFAULT_CONFIG))

    _CONFIG = _to_crawl_config(validated)
    return _CONFIG


def get_config() -> CrawlConfig:
    if _CONFIG is None:
        return load_crawl_config()
    return _CONFIG


def reset_config_cache() -> None:
    global _CONFIG
    _CONFIG = None

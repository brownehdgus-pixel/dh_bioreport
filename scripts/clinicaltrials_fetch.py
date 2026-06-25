"""
ClinicalTrials.gov API v2 연동.

한국 기업 스폰서 또는 한국 임상시험 사이트의 Phase 2/3 연구를 수집해
collect_news.py의 raw_item 포맷으로 변환한다.

공식 API: https://clinicaltrials.gov/api/v2/studies
인증 불필요, 무료.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from typing import Any

import requests

API_BASE = "https://clinicaltrials.gov/api/v2/studies"
USER_AGENT = "BioNewsReportCollector/0.1"

# 한국 바이오 관련 스폰서 키워드 (부분 매칭)
KOREA_SPONSOR_KEYWORDS = [
    "korea", "korean", "seoul", "yuhan", "hanmi", "boryung", "ildong",
    "daewoong", "chong kun dang", "ckd", "biontech korea", "hugel",
    "medytox", "celltrion", "samsung bioepis", "isu abxis", "inventisbio",
    "hugel", "alteogen", "abo bio", "ildong", "보령", "한미", "유한",
    "대웅", "종근당", "동아", "셀트리온", "삼성바이오",
]


def _is_korea_relevant(study: dict[str, Any]) -> bool:
    """한국 관련 임상인지 판단 (스폰서명 또는 사이트 국가)."""
    proto = study.get("protocolSection", {})

    # 스폰서명 체크
    sponsor = proto.get("sponsorCollaboratorsModule", {})
    lead = (sponsor.get("leadSponsor") or {}).get("name", "").lower()
    if any(kw in lead for kw in KOREA_SPONSOR_KEYWORDS):
        return True

    # 사이트 국가 체크
    contacts = proto.get("contactsLocationsModule", {})
    for loc in contacts.get("locations") or []:
        if (loc.get("country") or "").lower() in ("korea, republic of", "south korea", "korea"):
            return True

    return False


def _extract_phase(study: dict[str, Any]) -> str:
    phases = (study.get("protocolSection", {})
              .get("designModule", {})
              .get("phases") or [])
    return "/".join(p.replace("PHASE", "Phase ") for p in phases) or "N/A"


def _build_raw_item(study: dict[str, Any], collected_at: str) -> dict[str, Any]:
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    design = proto.get("designModule", {})
    conds = proto.get("conditionsModule", {})
    interventions = proto.get("armsInterventionsModule", {})
    sponsor = proto.get("sponsorCollaboratorsModule", {})
    desc = proto.get("descriptionModule", {})

    nct_id = ident.get("nctId", "")
    brief_title = ident.get("briefTitle", "")
    phase = _extract_phase(study)
    conditions = ", ".join((conds.get("conditions") or [])[:3])
    lead_sponsor = (sponsor.get("leadSponsor") or {}).get("name", "")
    overall_status = status_mod.get("overallStatus", "")
    brief_summary = (desc.get("briefSummary") or "").strip()[:400]

    # 날짜
    last_update = status_mod.get("lastUpdatePostDateStruct", {}).get("date", "")
    pub_date = last_update[:10] if last_update else datetime.now(timezone.utc).date().isoformat()

    title = f"[ClinicalTrials] {brief_title} ({phase}, {overall_status})"
    snippet = (
        f"NCT ID: {nct_id} | Sponsor: {lead_sponsor} | "
        f"Condition: {conditions} | Phase: {phase} | Status: {overall_status}. "
        f"{brief_summary}"
    )
    url = f"https://clinicaltrials.gov/study/{nct_id}"

    return {
        "raw_id": f"ct_{nct_id}",
        "title": title,
        "source": "ClinicalTrials.gov",
        "published_at": pub_date,
        "collected_at": collected_at,
        "url": url,
        "normalized_url": url,
        "snippet": snippet[:2000],
        "query_keyword": "ClinicalTrials.gov",
        "source_type": "api",
        "raw_payload": {},
    }


def fetch_clinicaltrials(
    collected_at: str,
    *,
    page_size: int = 50,
    max_age_days: int = 14,
) -> list[dict[str, Any]]:
    """
    최근 업데이트된 Phase 2/3 연구 중 한국 관련 항목 수집.
    반환: collect_news.py raw_item 포맷 리스트
    """
    cutoff = datetime.now(timezone.utc)
    cutoff_str = (cutoff.date().isoformat().replace("-", "/"))

    params = {
        "filter.advanced": (
            "AREA[Phase](PHASE2 OR PHASE3) "
            "AND AREA[OverallStatus](RECRUITING OR COMPLETED OR ACTIVE_NOT_RECRUITING)"
        ),
        "fields": (
            "NCTId,BriefTitle,Phase,OverallStatus,Condition,"
            "InterventionName,LeadSponsorName,BriefSummary,"
            "LastUpdatePostDate,LocationCountry"
        ),
        "pageSize": page_size,
        "sort": "LastUpdatePostDate:desc",
    }

    try:
        resp = requests.get(
            API_BASE,
            params=params,
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [ClinicalTrials] API 오류: {exc}")
        return []

    data = resp.json()
    studies = data.get("studies") or []

    items: list[dict[str, Any]] = []
    for study in studies:
        if not _is_korea_relevant(study):
            continue
        item = _build_raw_item(study, collected_at)
        items.append(item)

    print(f"  [ClinicalTrials] {len(studies)} studies fetched → {len(items)} Korea-relevant")
    return items


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    from env_local import load_env_local
    load_env_local()
    collected_at = datetime.now(timezone.utc).isoformat()
    results = fetch_clinicaltrials(collected_at)
    for item in results[:5]:
        print(f"\n{item['title']}")
        print(f"  {item['snippet'][:150]}")

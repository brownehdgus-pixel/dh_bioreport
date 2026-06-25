"""
OpenAI API를 사용해 뉴스 아이템별 투자 인사이트(investmentTakeaway)를 생성.

- 모델: gpt-4o-mini (비용 효율, 40건/일 기준 ~$0.003/일)
- 실패 시 기존 룰베이스 takeaway로 폴백
- 배치 처리로 API 호출 최소화
"""

from __future__ import annotations

import os
import time
from typing import Any

SYSTEM_PROMPT = """당신은 한국 기술특례상장 평가위원 및 바이오 VC 심사역을 위한 뉴스 triage 전문가입니다.
아래 뉴스 기사에 대해 정확히 4줄 구조로 한국어로 작성하세요.

출력 형식 (4줄, 각 줄은 레이블 포함):
[이벤트] 무엇이 발생했는가 — 회사명, 모달리티, 적응증, 단계, 금액 등 핵심 팩트만 1줄
[중요도] 왜 기술성/시장성/투자판단에 중요한가 — 성공/실패/규제/딜구조 중 해당 관점 1줄
[국내관련성] 국내 비상장·상장사·기술특례 후보 중 영향받는 곳 또는 활용 가능한 comp 1줄. 없으면 "국내 직접 관련성 낮음"
[액션] Watch / Wiki반영 / 딥다이브 / 제외 중 하나 + 이유 한 줄

규칙:
- 각 줄은 반드시 해당 레이블로 시작할 것 ([이벤트], [중요도], [국내관련성], [액션])
- 구체적인 회사명·모달리티·적응증·금액 반드시 포함
- "참고할 만하다", "추적할 가치가 있다" 같은 일반론 금지
- MOU·업무협약은 [이벤트]에 "구속력 없는 협약 단계"로 명시
- 임상 실패는 [이벤트]에 "실패" 명시, [액션]에 리스크 반영 여부 표시
- Negative signal(파산·임상실패·FDA CRL·안전성 이슈)은 [액션]에 반드시 "리스크 체크" 포함
- 응답은 4줄 외 추가 텍스트 없이"""


def _make_user_message(item: dict[str, Any]) -> str:
    return (
        f"제목: {item.get('title', '')}\n"
        f"출처: {item.get('source', '')}\n"
        f"요약: {item.get('snippet', '') or item.get('summary', '')}\n"
        f"이벤트 유형: {item.get('event_type', '')}\n"
        f"국내/글로벌: {item.get('origin', '')}"
    )


def generate_takeaways(
    items: list[dict[str, Any]],
    *,
    model: str = "gpt-4o-mini",
    retry_delay: float = 2.0,
) -> dict[str, str]:
    """
    items: enrich_raw_item() 결과 리스트 (raw_id, title, snippet, event_type, origin 포함)
    반환: {raw_id: takeaway_str}  — API 실패 항목은 키 없음 (폴백은 호출부에서 처리)
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[OPENAI] OPENAI_API_KEY 없음 — takeaway 생성 건너뜀")
        return {}

    try:
        from openai import OpenAI
    except ImportError:
        print("[OPENAI] openai 패키지 미설치 — pip install openai")
        return {}

    client = OpenAI(api_key=api_key)
    results: dict[str, str] = {}
    total = len(items)

    for idx, item in enumerate(items, start=1):
        raw_id = item.get("raw_id") or item.get("id") or str(idx)
        title_short = item.get("title", "")[:50]
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _make_user_message(item)},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            takeaway = response.choices[0].message.content or ""
            results[raw_id] = takeaway.strip()
            print(f"  [{idx}/{total}] OK: {title_short}…")
        except Exception as exc:  # noqa: BLE001
            print(f"  [{idx}/{total}] FAIL ({exc}): {title_short}…")
            if idx < total:
                time.sleep(retry_delay)

    print(f"[OPENAI] takeaway 생성 완료: {len(results)}/{total}")
    return results

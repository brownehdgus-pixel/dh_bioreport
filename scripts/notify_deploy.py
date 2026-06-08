#!/usr/bin/env python3
"""
크롤 commit/push 후 Vercel 배포 완료를 기다려 푸시 알림을 보냅니다.

지원:
  - ntfy.sh (휴대폰 푸시, 권장) - NTFY_TOPIC
  - Telegram - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID

선택 (Vercel 배포 완료 대기):
  - VERCEL_TOKEN + VERCEL_PROJECT_ID
  - VERCEL_PRODUCTION_URL (알림 본문 링크)
"""

from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request
from json import dumps
from pathlib import Path
from urllib.parse import quote, urlencode

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


from console_io import configure_stdio_utf8  # noqa: E402


def _post_json(url: str, payload: dict, headers: dict | None = None) -> bool:
    data = dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300
    except urllib.error.URLError as exc:
        print(f"Notify request failed: {exc}")
        return False


def send_ntfy(
    title: str,
    message: str,
    *,
    priority: str = "default",
    tags: str = "newspaper",
) -> bool:
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return False
    # title/priority/tags는 query param으로 전달 (한글 제목 등 UTF-8 안전; HTTP 헤더는 latin-1 제한)
    query = urlencode({"title": title, "priority": priority, "tags": tags})
    url = f"https://ntfy.sh/{quote(topic, safe='')}?{query}"
    body = message.encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ok = 200 <= resp.status < 300
            print(f"ntfy: {'OK' if ok else resp.status}")
            return ok
    except urllib.error.URLError as exc:
        print(f"ntfy failed: {exc}")
        return False


def send_telegram(title: str, message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False
    text = f"*{title}*\n\n{message}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = _post_json(
        url,
        {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
    )
    print(f"telegram: {'OK' if ok else 'FAILED'}")
    return ok


def wait_for_vercel_ready(max_wait_sec: int = 600) -> str | None:
    """최신 Vercel 배포가 READY 될 때까지 대기. URL 또는 None."""
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    project_id = os.environ.get("VERCEL_PROJECT_ID", "").strip()
    if not token or not project_id:
        print("Vercel token/project not set - skip deploy wait")
        return None

    api = f"https://api.vercel.com/v6/deployments?projectId={project_id}&limit=3"
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + max_wait_sec

    while time.time() < deadline:
        req = urllib.request.Request(api, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                import json

                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            print(f"Vercel API error: {exc}")
            time.sleep(15)
            continue

        deployments = data.get("deployments") or []
        if deployments:
            latest = deployments[0]
            state = latest.get("readyState") or latest.get("state")
            print(f"Vercel latest deployment: {state}")
            if state == "READY":
                return latest.get("url") or os.environ.get("VERCEL_PRODUCTION_URL")
            if state in ("ERROR", "CANCELED"):
                return None
        time.sleep(15)

    print("Vercel deploy wait timed out")
    return None


def main() -> int:
    configure_stdio_utf8()
    report_date = os.environ.get("REPORT_DATE", "").strip() or "today"
    production = os.environ.get("VERCEL_PRODUCTION_URL", "").strip()

    deploy_url = wait_for_vercel_ready()
    if deploy_url:
        title = "바이오 뉴스 리포트 배포 완료"
        link = production or f"https://{deploy_url}"
        message = (
            f"날짜: {report_date}\n"
            f"Vercel 배포가 완료되었습니다.\n"
            f"리포트 보기: {link}/reports"
        )
    else:
        title = "바이오 뉴스 데이터 업데이트"
        message = (
            f"날짜: {report_date}\n"
            "GitHub에 새 뉴스 데이터가 push되었습니다.\n"
        )
        if production:
            message += f"Vercel 배포 확인: {production}/reports\n"
        else:
            message += "Vercel 대시보드에서 배포 완료를 확인해 주세요.\n"

    sent = False
    if send_ntfy(title, message):
        sent = True
    if send_telegram(title, message):
        sent = True

    if not os.environ.get("NTFY_TOPIC") and not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print(
            "No notification channel configured. "
            "Set NTFY_TOPIC or TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env.local."
        )
        return 0

    if not sent:
        print("Notification failed on all configured channels")
        return 1

    print("Notification sent")
    return 0


def notify_failure(title: str, message: str) -> int:
    """실패 알림 (ntfy high / Telegram). 알림 채널 없으면 0 반환."""
    configure_stdio_utf8()
    sent = False
    if send_ntfy(title, message, priority="high", tags="warning"):
        sent = True
    if send_telegram(title, message):
        sent = True

    if not os.environ.get("NTFY_TOPIC") and not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print(
            "No notification channel configured. "
            "Set NTFY_TOPIC or TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env.local."
        )
        return 0

    if not sent:
        print("Failure notification failed on all configured channels")
        return 1

    print("Failure notification sent")
    return 0


if __name__ == "__main__":
    from env_local import load_env_local  # noqa: E402

    configure_stdio_utf8()
    load_env_local()
    sys.exit(main())

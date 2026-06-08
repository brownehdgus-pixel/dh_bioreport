#!/usr/bin/env python3
"""Daily crawl pipeline failure notification (ntfy / Telegram)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from env_local import load_env_local  # noqa: E402
from notify_deploy import notify_failure  # noqa: E402


def main() -> int:
    load_env_local()

    step = (sys.argv[1] if len(sys.argv) > 1 else "unknown").strip()
    exit_code = (sys.argv[2] if len(sys.argv) > 2 else "?").strip()
    log_file = (sys.argv[3] if len(sys.argv) > 3 else "").strip()

    report_date = date.today().isoformat()
    lines = [
        f"날짜: {report_date}",
        f"실패 단계: {step}",
        f"종료 코드: {exit_code}",
        "",
        "작업 스케줄러 또는 PC에서 logs/daily_crawl_날짜.log 를 확인하세요.",
    ]
    if log_file:
        lines.insert(3, f"로그 파일: {log_file}")

    if step == "python":
        lines.append("")
        lines.append("힌트: .env.local 에 PYTHON_EXECUTABLE=python.exe 전체 경로 설정")

    return notify_failure("바이오 뉴스 데일리 크롤 실패", "\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())

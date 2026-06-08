#!/usr/bin/env python3
"""
data/news.json 변경 시 Git commit/push 후 ntfy·Vercel 알림.

로컬 .env.local 에서 NTFY_TOPIC, VERCEL_* 등을 읽습니다.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from console_io import configure_stdio_utf8  # noqa: E402
from env_local import load_env_local  # noqa: E402


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def log_env_status() -> None:
    env_path = ROOT / ".env.local"
    if env_path.exists():
        print("[ENV] .env.local loaded")
    else:
        print("[ENV] .env.local missing")
    ntfy = "set" if os.environ.get("NTFY_TOPIC", "").strip() else "not set"
    vercel = "set" if os.environ.get("VERCEL_PRODUCTION_URL", "").strip() else "not set"
    print(f"[ENV] NTFY_TOPIC={ntfy}")
    print(f"[ENV] VERCEL_PRODUCTION_URL={vercel}")


def run_notify_after_push() -> int:
    """Run deploy notification. Git push already succeeded; always exit 0 here."""
    has_ntfy = bool(os.environ.get("NTFY_TOPIC", "").strip())
    has_telegram = bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip())

    if not has_ntfy and not has_telegram:
        print("[NOTIFY] skipped - NTFY_TOPIC not set (and no Telegram)")
        return 0

    from notify_deploy import main as notify_main  # noqa: E402

    notify_rc = notify_main()
    if notify_rc == 0:
        print("[NOTIFY] OK - notification sent")
        return 0

    print("[NOTIFY] failed - notification channels did not send (git push succeeded)")
    return 0


def main() -> int:
    configure_stdio_utf8()
    load_env_local()
    log_env_status()

    add = run_git(["add", "data/"])
    if add.returncode != 0:
        print(f"[GIT] add data/ failed: {add.stderr or add.stdout}")
        return add.returncode

    add_raw = run_git(["add", "-A", "raw_data/"])
    if add_raw.returncode != 0:
        print(f"[GIT] add raw_data/ failed: {add_raw.stderr or add_raw.stdout}")
        return add_raw.returncode

    diff = run_git(["diff", "--cached", "--quiet", "--", "data/news.json"])
    if diff.returncode == 0:
        print("[GIT] data/news.json unchanged - skipping commit and push")
        return 0

    commit = run_git(["commit", "-m", "chore: update daily bio news report"])
    if commit.returncode != 0:
        print(f"[GIT] commit failed: {commit.stderr or commit.stdout}")
        return commit.returncode
    print(f"[GIT] {commit.stdout.strip() or 'Committed.'}")

    push = run_git(["push"])
    if push.returncode != 0:
        detail = (push.stderr or push.stdout or "").strip()
        print(f"[GIT] push failed: {detail}")
        print("[GIT] Check GitHub login (Git Credential Manager / GitHub Desktop).")

        report_date = date.today().isoformat()
        message = (
            f"날짜: {report_date}\n"
            "news.json은 로컬에 commit되었으나 GitHub push에 실패했습니다.\n"
            "Git Credential Manager / GitHub Desktop 로그인을 확인하세요."
        )
        if detail:
            message += f"\n\n오류:\n{detail[:500]}"

        from notify_deploy import notify_failure  # noqa: E402

        notify_rc = notify_failure("바이오 뉴스 Git push 실패", message)
        if notify_rc != 0:
            print("[NOTIFY] failed - could not send git push failure alert")
        else:
            print("[NOTIFY] OK - git push failure alert sent")
        return push.returncode

    print(f"[GIT] {push.stdout.strip() or 'Pushed to GitHub.'}")

    os.environ.setdefault("REPORT_DATE", date.today().isoformat())
    return run_notify_after_push()


if __name__ == "__main__":
    sys.exit(main())

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


def main() -> int:
    load_env_local()

    add = run_git(["add", "data/"])
    if add.returncode != 0:
        print(add.stderr or add.stdout)
        return add.returncode

    add_raw = run_git(["add", "-A", "raw_data/"])
    if add_raw.returncode != 0:
        print(add_raw.stderr or add_raw.stdout)
        return add_raw.returncode

    diff = run_git(["diff", "--cached", "--quiet", "--", "data/news.json"])
    if diff.returncode == 0:
        print("data/news.json unchanged — skipping commit and push")
        return 0

    commit = run_git(["commit", "-m", "chore: update daily bio news report"])
    if commit.returncode != 0:
        print(commit.stderr or commit.stdout)
        return commit.returncode
    print(commit.stdout or "Committed.")

    push = run_git(["push"])
    if push.returncode != 0:
        print(push.stderr or push.stdout)
        print("Git push failed. Check GitHub login (Git Credential Manager / GitHub Desktop).")
        return push.returncode
    print(push.stdout or "Pushed to GitHub.")

    os.environ.setdefault("REPORT_DATE", date.today().isoformat())

    from notify_deploy import main as notify_main  # noqa: E402

    return notify_main()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Print absolute path to Python for Task Scheduler (PATH may differ from interactive shell)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_python_executable_from_env_local() -> str | None:
    path = ROOT / ".env.local"
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if key.strip() != "PYTHON_EXECUTABLE":
            continue
        value = value.strip().strip('"').strip("'")
        if value and Path(value).is_file():
            return value
    return None


def _py_launcher_executable() -> str | None:
    py = shutil.which("py")
    if not py:
        return None
    try:
        proc = subprocess.run(
            [py, "-3", "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    exe = (proc.stdout or "").strip()
    return exe if exe and Path(exe).is_file() else None


def _scan_windows_install_dirs() -> str | None:
    candidates: list[Path] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        base = Path(local) / "Programs" / "Python"
        if base.is_dir():
            candidates.extend(sorted(base.glob("Python*/python.exe"), reverse=True))
    for name in ("Python314", "Python313", "Python312", "Python311", "Python310"):
        p = Path(f"C:/Program Files/{name}/python.exe")
        if p.is_file():
            candidates.append(p)
    for exe in candidates:
        if exe.is_file():
            return str(exe)
    return None


def resolve_python() -> str | None:
    override = os.environ.get("PYTHON_EXECUTABLE", "").strip()
    if override and Path(override).is_file():
        return override

    from_env_file = _load_python_executable_from_env_local()
    if from_env_file:
        return from_env_file

    for name in ("python", "python3"):
        found = shutil.which(name)
        if found and Path(found).is_file():
            return found

    launcher = _py_launcher_executable()
    if launcher:
        return launcher

    return _scan_windows_install_dirs()


def main() -> int:
    exe = resolve_python()
    if not exe:
        return 1
    print(exe)
    return 0


if __name__ == "__main__":
    sys.exit(main())

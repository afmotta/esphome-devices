#!/usr/bin/env python3
"""Repo hygiene checks for tracked secrets and ESPHome build artifacts."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import PurePosixPath

FORBIDDEN_PATTERNS = (
    "*/secrets.yaml",
    "secrets.yaml",
    "*/.esphome/*",
    "*/.pioenvs/*",
    "*/.piolibdeps/*",
    "*.bin",
    "*.elf",
    "*.map",
)


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def is_forbidden(path: str) -> bool:
    normalized = PurePosixPath(path).as_posix()
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in FORBIDDEN_PATTERNS)


def main() -> int:
    offenders = [path for path in git_ls_files() if is_forbidden(path)]
    if offenders:
        print("Tracked secret/build artifacts are not allowed:", file=sys.stderr)
        for path in offenders:
            print(f"  - {path}", file=sys.stderr)
        print("Remove these from git and keep them ignored before committing.", file=sys.stderr)
        return 1
    print("repo hygiene: no tracked secrets or ESPHome build artifacts found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

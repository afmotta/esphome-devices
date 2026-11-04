#!/usr/bin/env python3
"""Check that relative links in tracked Markdown files point at existing files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], check=True, capture_output=True, text=True
    ).stdout
    return [Path(line) for line in out.splitlines() if line]


def broken_links(md: Path) -> list[str]:
    broken = []
    in_fence = False
    for number, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(INLINE_CODE.sub("", line)):
            if target.startswith(EXTERNAL):
                continue
            path = unquote(target.split("#", 1)[0])
            if path and not (md.parent / path).exists():
                broken.append(f"{md}:{number}: {target}")
    return broken


def main() -> int:
    broken = [item for md in tracked_markdown() for item in broken_links(md)]
    if broken:
        print("Broken relative Markdown links:", file=sys.stderr)
        for item in broken:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print("markdown links: all relative links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail if any tracked YAML declares `on_boot:` in mapping form (review R-18).

Why: ESPHome flattens `packages:` with config_helpers.merge_config(), and for
`esphome: on_boot:` the result depends on the *form* each side was written in:

  - mapping + mapping -> ONE trigger: the `then` lists concatenate and a single
    `priority` survives (the overlay's). Every other hook's declared priority,
    and any comment justifying it, is fiction.
  - list + list       -> the lists concatenate: one trigger per entry, each
    with its own priority.
  - mapping + list    -> the overlay's form wins and the other side is dropped
    entirely (a package's hook silently disappears).

So every `on_boot:` must be a list (`- priority: N` / `then:` per entry). This
check is purely textual (stdlib only, no ESPHome needed) and so runs in the
native battery, pre-commit and CI. The resolved-config counterpart is
scripts/check_on_boot_resolved.py.

Usage:
  python3 scripts/check_on_boot_form.py            # scan `git ls-files` YAML
  python3 scripts/check_on_boot_form.py FILE...    # scan the given files
  python3 scripts/check_on_boot_form.py --self-test
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# `on_boot:` as a YAML key (optionally a list item's first key). `enable_on_boot:`
# and friends do not match: the key must be exactly `on_boot`.
KEY_RE = re.compile(r"^(?P<indent>\s*(?:-\s+)?)on_boot:(?P<rest>.*)$")


def significant(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def check_text(text: str) -> list[tuple[int, str]]:
    """Return (1-based line, message) for each non-list `on_boot:` in `text`."""
    lines = text.splitlines()
    problems: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        match = KEY_RE.match(line)
        if not match:
            continue
        rest = match.group("rest").split(" #", 1)[0].strip()
        if rest:
            # Inline value: only a flow sequence (or an !include of one) is a list.
            if not (rest.startswith("[") or rest.startswith("!include")):
                problems.append((idx + 1, f"inline non-list value: {rest!r}"))
            continue
        key_indent = len(match.group("indent").replace("-", " "))
        nxt = next((l for l in lines[idx + 1 :] if significant(l)), None)
        if nxt is None:
            problems.append((idx + 1, "empty on_boot (no entries follow)"))
            continue
        nxt_indent = len(nxt) - len(nxt.lstrip())
        is_item = nxt.lstrip().startswith("- ") or nxt.strip() == "-"
        if not (is_item and nxt_indent >= key_indent):
            problems.append(
                (idx + 1, f"mapping form (next line {nxt.strip()!r}); use '- priority: N' list entries")
            )
            continue
        problems.extend(check_entries(lines, idx + 1, nxt_indent))
    return problems


def check_entries(lines: list[str], start: int, item_indent: int) -> list[tuple[int, str]]:
    """Each list entry (a '-' at `item_indent`) must carry an explicit `priority:`."""
    problems: list[tuple[int, str]] = []
    entry_start: int | None = None
    has_priority = False
    key_indent = item_indent + 2

    def close() -> None:
        if entry_start is not None and not has_priority:
            problems.append((entry_start + 1, "list entry without an explicit 'priority:'"))

    for offset in range(start, len(lines)):
        line = lines[offset]
        if not significant(line):
            continue
        indent = len(line) - len(line.lstrip())
        if indent < item_indent or (indent == item_indent and not line.lstrip().startswith("-")):
            break  # the on_boot list ended
        if indent == item_indent and line.lstrip().startswith("-"):
            close()
            entry_start, has_priority = offset, False
            if re.match(r"^\s*-\s+priority:", line):
                has_priority = True
        elif indent == key_indent and re.match(r"^\s*priority:", line):
            has_priority = True
    close()
    return problems


def tracked_yaml() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "*.yaml", "*.yml"], check=True, capture_output=True, text=True
    ).stdout
    return [p for p in out.splitlines() if p]


def self_test() -> int:
    ok_cases = [
        "esphome:\n  on_boot:\n    - priority: 1\n      then: []\n",
        "esphome:\n  on_boot:\n    - then: []\n      priority: 1\n    - priority: 2\n      then: []\nx: 1\n",
        "esphome:\n  on_boot:\n  # comment\n\n  - priority: 600\n    then: []\n",
        "esphome:\n  on_boot: []\n",
        "wifi:\n  enable_on_boot: true\n",
        "# on_boot:\n#   priority: 1\n",
    ]
    bad_cases = [
        "esphome:\n  on_boot:\n    priority: 1\n    then: []\n",
        "esphome:\n  on_boot:\n    then:\n      - delay: 1s\n",
        "esphome:\n  on_boot: {priority: 1}\n",
        "esphome:\n  on_boot:\n",
        "esphome:\n  on_boot:\n    # c\n    priority: -100\n",
        "esphome:\n  on_boot:\n    - then: []\n",
        "esphome:\n  on_boot:\n    - priority: 1\n      then: []\n    - then: []\n",
    ]
    failures = [c for c in ok_cases if check_text(c)] + [c for c in bad_cases if not check_text(c)]
    for case in failures:
        print(f"self-test FAILED on:\n{case}", file=sys.stderr)
    if failures:
        return 1
    print("check_on_boot_form self-test: ok")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--self-test"]:
        return self_test()
    files = argv or tracked_yaml()
    failed = False
    scanned = 0
    for name in files:
        path = Path(name)
        if not path.is_file():
            continue
        scanned += 1
        for lineno, message in check_text(path.read_text(encoding="utf-8")):
            failed = True
            print(f"{name}:{lineno}: on_boot {message}", file=sys.stderr)
    if failed:
        print(
            "\nEvery `on_boot:` must be a LIST with an explicit `priority` per entry.\n"
            "Package mappings merge into one trigger (one surviving priority) and mixing\n"
            "forms drops a hook: review R-18, docs/reviews/2026-10-25-repo-review.md.",
            file=sys.stderr,
        )
        return 1
    print(f"on_boot form: all {scanned} YAML files use list-form on_boot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Isolate whether the current install differs behaviourally or only textually.

The current install is a Chinese-localized repack, so its report *header*
("Text Compare" / "Mode:" / "Left file:") is translated and cannot match the
English golden bytes. This probe strips the header region and compares only the
comparison BODY (the data rows, markers, separators and summary lines), which is
what actually encodes diff behaviour.
"""
from __future__ import annotations

import pathlib

OUT = pathlib.Path(r"D:\Rea\tools\_audit\provenance")
GOLD = pathlib.Path(r"D:\Rea\verify\layouts")
BS = chr(92)  # backslash


def body(text: str) -> list[str]:
    """Drop the header region up to and including the file-name line."""
    lines = text.splitlines()
    cut = 0
    for i, line in enumerate(lines[:10]):
        if ":" in line and BS in line:
            cut = i + 1
    return lines[cut:]


def main() -> int:
    agree = differ = 0
    diffs = []
    for case in ["mixed", "insert", "similar", "orphans", "identical"]:
        for lay in ["side-by-side", "interleaved", "patch", "summary",
                    "statistics", "over-under"]:
            a = OUT / f"current-5.2.1.32035-{case}-{lay}.txt"
            g = GOLD / f"{case}-{lay}.txt"
            if not a.exists() or not g.exists():
                continue
            ta = a.read_text(encoding="utf-8", errors="replace")
            tg = g.read_text(encoding="utf-8", errors="replace")
            if body(ta) == body(tg):
                agree += 1
            else:
                differ += 1
                diffs.append((case, lay, body(ta), body(tg)))

    print(f"data-body comparison (header excluded): {agree} match / {differ} differ")
    for case, lay, x, y in diffs[:6]:
        print(f"--- {case}-{lay} ---")
        for i in range(max(len(x), len(y))):
            p = x[i] if i < len(x) else "<none>"
            q = y[i] if i < len(y) else "<none>"
            if p != q:
                print(f"   cur : {p!r}")
                print(f"   gold: {q!r}")
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

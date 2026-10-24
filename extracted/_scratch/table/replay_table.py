#!/usr/bin/env python3
"""Replay the table simulator against archived Oracle reports (free loop).

For each archived .out under m60/m61/m61b/m61c/m61d that came from a .csv
fixture with a known layout, extract the Oracle report BODY (everything after
the header frame) and compare it to simulate_table.body(...).  Header frame
lines (title/Produced/mode/file paths) are normalized away because they carry
machine-specific paths and timestamps.

Reports whose fixture extension is not .csv, or that used a layout the
simulator does not model yet, are SKIPPED (recorded, not silently passed).

Usage:  python replay_table.py [--verbose]
"""
from __future__ import annotations
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate_table as sim

REA = pathlib.Path(r"D:\Rea")
RUNS = REA / "product" / "verify" / "runs"

LAYOUT_RE = re.compile(r"layout:([a-z-]+)")

def oracle_body(text: str):
    lines = text.replace("\r\n", "\n").split("\n")
    # find the first body line: after Right file/左边文件 line
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("Right file:") or ln.startswith("右边文件"):
            start = i + 1
            break
    if start is None:
        return None
    # drop trailing empty line
    body = lines[start:]
    while body and body[-1] == "":
        body.pop()
    return body

def parse_fixture(p: pathlib.Path):
    return p.read_text(encoding="utf-8", newline="")

def main() -> int:
    verbose = "--verbose" in sys.argv
    total = passed = skipped = failed = 0
    fails = []
    # discover archived probe dirs; pair each .out with its fixture via the JSON
    for d in sorted(RUNS.glob("m6[01]*-*")):
        reports = d / "reports"
        fixtures = d / "fixtures"
        if not reports.is_dir():
            continue
        # load json to get left/right per tag
        meta = None
        for jf in d.glob("*.json"):
            meta = jf
            break
        if meta is None:
            continue
        import json
        data = json.loads(meta.read_text(encoding="utf-8"))
        for rec in data:
            tag = rec.get("tag") or rec.get("name")
            left_t = rec.get("left"); right_t = rec.get("right")
            if left_t is None or right_t is None:
                continue
            reps = rec.get("reports", {})
            for key, val in reps.items():
                lay = key.split("[")[0].strip()
                if lay not in ("side-by-side", "interleaved", "summary"):
                    # labels like "side-by-side options:..." -> take prefix
                    m = lay
                    if " " in lay: m = lay.split(" ")[0]
                    if m not in ("side-by-side", "interleaved", "summary"):
                        continue
                    lay = m
                body = val.get("body", "")
                if not body:
                    skipped += 1; continue
                # fixture extension: skip auto-detect (non-.csv) for now
                # reports whose fixture used auto-detect (non-.csv) are out of
                # M6.2 scope (docs/13 §4.5): .csv is the only fixed-comma path
                # the product models now.
                if rec.get("ext") and rec["ext"] != ".csv":
                    skipped += 1; continue
                # archived probes run the Chinese install -> Chinese labels
                lang = "zh" if "个" in body or "表格" in body else "en"
                ob = oracle_body(body)
                if ob is None:
                    skipped += 1; continue
                groups = sim.align(sim.split_records(left_t),
                                   sim.split_records(right_t))
                sb = sim.body(lay, groups, sim.split_records(left_t),
                              sim.split_records(right_t), lang)
                total += 1
                if sb == ob:
                    passed += 1
                else:
                    failed += 1
                    fails.append((tag, lay, sb, ob))
                if verbose and sb != ob:
                    print(f"== {tag} [{lay}]")
                    for a, b in zip(sb + [""] * len(ob), ob + [""] * len(sb)):
                        mark = "  " if a == b else "XX"
                        print(f"{mark} sim={a!r} oracle={b!r}")
    print(f"\nreplay: total={total} pass={passed} fail={failed} skip={skipped}")
    for tag, lay, sb, ob in fails:
        print(f"  FAIL {tag} [{lay}]")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())

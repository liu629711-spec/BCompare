#!/usr/bin/env python3
"""Bisect the anchor-engine vs band-engine router (serial, Oracle exclusive).

Established by gateb-mode/-modefine/-modebisect/-modeaxis/-modegrid (27 cells,
all in `runs/gateb-mode*`): small files take the ANCHOR shape (a~A `similar`
row, orphan head) and larger ones take the WINDOW shape (`b`,`A` right-orphans
then positional `different` pairs). Working rule from that data:

    ANCHOR  iff  R <= 12  OR  L <= 8      (L/R = sides incl. golden 2 rows)
    WINDOW  iff  L >= 9..12  AND  R >= 13  (L boundary in [9,12] unmeasured)

This probe pins the missing boundary cells and runs two controls:
  * RB-*   bisect L over {9,10,11} at R=15 and R=13, plus corners (8,13),(9,12),
           (8,12);
  * RB-C40 byte-size control: the (8,15) shape with every line 40 chars long --
           ANCHOR keeps the router count-based, WINDOW would make it size-based;
  * RB-CS  shape control: same-case keys (left `a`,`B`; right `B`,`a`) so the
           signature does not depend on case folding.

Usage (serial, Oracle exclusive):
  cd D:\\Rea\\product\\verify && python probes\\gateb_router_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

# (name, left_pad, right_pad, line_len, same_case)
# L/R below are sides INCLUDING the golden 2 rows (pad + 2).
# Known: (12,12) ANCHOR, (12,15) WINDOW, (8,15) ANCHOR, (13,13) WINDOW,
# (15,15) WINDOW, (22,12) ANCHOR, (12,22) WINDOW.
CASES = [
    # pin L_crit with R=15: expect WINDOW from some L in 9..12
    ("RB-9x15",   7, 13, 0, False),
    ("RB-10x15",  8, 13, 0, False),
    ("RB-11x15",  9, 13, 0, False),
    # pin R_crit with L=15: expect WINDOW from some R in 13..15
    ("RB-15x13", 13, 11, 0, False),
    ("RB-15x14", 13, 12, 0, False),
    ("RB-15x12", 13, 10, 0, False),
    # both-below corner + R=12 at L=12 control
    ("RB-8x12",   6, 10, 0, False),
    ("RB-9x12",   7, 10, 0, False),
    ("RB-12x13", 10, 11, 0, False),
    # controls: byte-size isolation and same-case shape
    ("RB-C40",    6, 13, 40, False),
    ("RB-CS",     6, 11, 0, True),
]

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')


def rows_of(body: str):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2)); rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def classify(rows):
    """ANCHOR signature: a `similar` row (golden swap) or, for the same-case
    control, ANY same/different pair that is NOT the positional L1~R3 zip;
    WINDOW signature: head right-orphans then positional `different`."""
    if any(r[0] == "similar" for r in rows):
        return "ANCHOR"
    head = [r[0] for r in rows[:3]]
    if head == ["rightorphan", "rightorphan", "different"]:
        return "WINDOW"
    if head[:2] == ["rightorphan", "rightorphan"]:
        return "WINDOW"
    return "ANCHOR"


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("gateb-router-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for name, pl, pr, llen, same_case in CASES:
        def pad(prefix, i):
            s = f"{prefix}{i}"
            return s + "x" * (llen - len(s)) if llen else s
        left = [pad("L", i) for i in range(pl)]
        right = [pad("R", i) for i in range(pr)]
        if same_case:
            left = left + ["a", "B"]
            right = ["B", "a"] + right
        else:
            g_a, g_B = ("a" * (llen or 1)), ("B" * (llen or 1))
            g_b, g_A = ("b" * (llen or 1)), ("A" * (llen or 1))
            left = left + [g_a, g_B]
            right = [g_b, g_A] + right
        tag = name
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        body = (o_out.read_bytes().decode("utf-8-sig", errors="replace")
                if run.report_exists else "")
        rows = rows_of(body)
        sig = classify(rows) if rows else "NO-REPORT"
        rec = {"case": tag, "L": len(left), "R": len(right), "line_len": llen,
               "signature": sig, "head": [list(r) for r in rows[:8]], "total_s": run.elapsed_s}
        results.append(rec)
        print(f"{tag:10} L={len(left):4} R={len(right):4} len={llen:3} -> {sig:7} "
              f"head={rows[:4]}")

    (run_dir / "router.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'router.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

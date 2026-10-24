#!/usr/bin/env python3
"""M2.6 model lab (OFFLINE): fit candidate pairing models to recorded BC output.

No Oracle, no product binary: every observation already exists on disk in the
golden corpus (verify/golden, 101 anchors) and the m26 run.  The lab replays
each recorded mapping and asks which candidate rule reproduces BC's rows.

Candidate rules
---------------
The product pairs inside an unmatched block with one of two strategies
(`align::pair_block`).  BC's own emission layer (FUN_140dc6a00/6b20/6c40)
records one-sided runs and only merges *adjacent* runs, so a block that has
both sides present is emitted as a zipper of the two runs -- i.e. BC pairs
positionally in document order (top-first).  That is candidate "positional".

The competing hypothesis is that BC pairs by *content closeness* among
content lines (its help calls this "Use closeness matching"), or that its
alignment keys make two comment lines equal (so Myers pairs them, giving the
observed shifted rows).  The lab distinguishes these by measuring, per
recorded case, which rule reproduces the mapping.

Usage (offline):
    python tools/_scratch/m26_model_lab.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

REA = pathlib.Path(r"D:\Rea")
GOLDEN = REA / "verify" / "golden"
M26_JSON = next(
    (REA / "product" / "verify" / "runs").glob(
        "m26-weighted-probe-*/m26-weighted-results.json"),
    None,
)

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(\d+)"')
RTID_RE = re.compile(r'rtid="(\d+)"')


def rows_of(body: str) -> list[tuple[str, str, str]]:
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), lt.group(1) if lt else "-", rt.group(1) if rt else "-"))
    return out


def read_lines(p) -> list[str]:
    p = pathlib.Path(p)
    if not p.exists():
        return []
    return p.read_bytes().decode("utf-8-sig", errors="replace").splitlines()


def collect() -> list[dict]:
    cases = []
    man = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    for cid, e in man.items():
        rep = pathlib.Path(e.get("report", ""))
        if not rep.exists():
            continue
        cases.append({
            "src": "golden", "id": cid,
            "left": read_lines(e["left"]), "right": read_lines(e["right"]),
            "rows": rows_of(rep.read_bytes().decode("utf-8-sig", errors="replace")),
        })
    if M26_JSON is not None and M26_JSON.exists():
        for r in json.loads(M26_JSON.read_text(encoding="utf-8"))["records"]:
            cases.append({
                "src": "m26", "id": r["case"],
                "left": r["left"], "right": r["right"],
                "rows": [tuple(x) for x in r["oracle_rows"]],
                "product_rows": [tuple(x) for x in r["product_rows"]],
            })
    return cases


# ----------------------------------------------------------------------
# Candidate model: reproduce a row list from a matched-pair list.
# ----------------------------------------------------------------------

def blocks_seen_by_bc(rows) -> list[tuple[int, int, int, int]]:
    """Recover the unmatched block rectangles that BC actually left unmatched.

    A block is a maximal run of rows that are not `same`.  Its rectangle is
    (left indices present, right indices present) in row order.
    """
    blocks = []
    cur = []
    for r in rows:
        if r[0] == "same":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(r)
    if cur:
        blocks.append(cur)
    return blocks


def summarize(rows):
    return [(r[0], r[1], r[2]) for r in rows]


def main() -> int:
    cases = collect()
    print(f"collected {len(cases)} recorded BC cases "
          f"({sum(1 for c in cases if c['src']=='golden')} golden, "
          f"{sum(1 for c in cases if c['src']=='m26')} m26)\n")

    # --- Which recorded cases contain a block where BOTH sides have lines? ---
    both = []
    for c in cases:
        for blk in blocks_seen_by_bc(c["rows"]):
            lefts = [r for r in blk if r[1] != "-"]
            rights = [r for r in blk if r[2] != "-"]
            if lefts and rights:
                both.append((c, blk))
                break
    print(f"cases with a two-sided unmatched block: {len(both)}\n")

    for c, blk_src in both:
        print(f"== {c['src']}/{c['id']}")
        print(f"   L={c['left']}")
        print(f"   R={c['right']}")
        # compact: print the matched pairs BC chose and the orphans
        pairs = [(r[1], r[2]) for r in c["rows"] if r[1] != "-" and r[2] != "-"]
        lo = [r[1] for r in c["rows"] if r[1] != "-" and r[2] == "-"]
        ro = [r[2] for r in c["rows"] if r[2] != "-" and r[1] == "-"]
        print(f"   BC pairs(1-based)={pairs}  L-orphan={lo}  R-orphan={ro}")
        if "product_rows" in c:
            ppairs = [(r[1], r[2]) for r in c["product_rows"] if r[1] != "-" and r[2] != "-"]
            plo = [r[1] for r in c["product_rows"] if r[1] != "-" and r[2] == "-"]
            pro = [r[2] for r in c["product_rows"] if r[2] != "-" and r[1] == "-"]
            print(f"   PRD pairs(1-based)={ppairs}  L-orphan={plo}  R-orphan={pro}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

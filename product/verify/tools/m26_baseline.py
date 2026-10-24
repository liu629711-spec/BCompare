#!/usr/bin/env python3
"""M2.6 baseline (OFFLINE): product vs every recorded BC text observation.

No Oracle runs here.  Every BC observation is already on disk (`verify/golden`,
`verify/disambig`, `verify/cases`, and the m26 probe's `.oracle.xml` reports);
this script replays the product binary over the same fixtures and compares the
*chosen pairing* (which left line pairs with which right line) plus the status
sequence.  That is the exact quantity M2.6 is about.

Layout and status parity for the golden corpus is already covered by
``cli/tools/offline_check.py``; this driver is narrower and stricter: it reports
pairing mismatches case by case, including cases outside the golden corpus.

Output: `product/verify/runs/m26-baseline-<ts>/m26-baseline.json`.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m26_baseline.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

REA = pathlib.Path(r"D:\Rea")
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(\d+)"')
RTID_RE = re.compile(r'rtid="(\d+)"')
FN_RE = re.compile(r"<filename([12])>(.*?)</filename[12]>", re.S)

SKIP_MARKERS = ("+iu", "-iu", "iu-", "ignore-unimportant",
                "display-matches", "display-mismatches", "display-context")
NOT_ORACLE = (".product.", "product.xml", ".reacmp.")


def is_oracle_report(rel: str) -> bool:
    low = rel.lower()
    if any(m in low for m in NOT_ORACLE):
        return False
    if ".oracle." in low:
        return True
    return "/runs/" not in low and "\\runs\\" not in low


def rows_of(body: str):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def pairs_of(rows):
    return sorted((lt - 1, rt - 1) for _s, lt, rt in rows if lt and rt)


def read_lines(p: pathlib.Path):
    try:
        return p.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None


def collect():
    roots = [REA / "verify" / "golden", REA / "verify" / "disambig",
             REA / "verify" / "cases", REA / "product" / "verify" / "runs"]
    cases, seen = [], set()
    for root in roots:
        if not root.exists():
            continue
        for xml in sorted(root.rglob("*.xml")):
            rel = str(xml.relative_to(REA)).replace("\\", "/")
            low = rel.lower()
            if any(m in low for m in SKIP_MARKERS) or not is_oracle_report(rel):
                continue
            if "/runs/" in low and "m26-weighted-probe" not in low:
                continue
            try:
                body = xml.read_bytes().decode("utf-8-sig", errors="replace")
            except OSError:
                continue
            fns = dict(FN_RE.findall(body))
            if "1" not in fns or "2" not in fns:
                continue
            lp, rp = pathlib.Path(fns["1"]), pathlib.Path(fns["2"])
            if not lp.exists() or not rp.exists():
                continue
            left, right = read_lines(lp), read_lines(rp)
            if left is None or right is None:
                continue
            rows = rows_of(body)
            if not rows:
                continue
            if sorted(lt for _s, lt, _r in rows if lt) != list(range(1, len(left) + 1)):
                continue          # not full coverage: not a pairing statement
            if sorted(rt for _s, _l, rt in rows if rt) != list(range(1, len(right) + 1)):
                continue
            key = (str(lp), str(rp), tuple(rows))
            if key in seen:
                continue
            seen.add(key)
            cases.append({"src": rel, "left_path": str(lp), "right_path": str(rp),
                          "left": left, "right": right,
                          "bc_rows": rows, "bc_pairs": pairs_of(rows),
                          "bc_statuses": [r[0] for r in rows]})
    return cases


def main() -> int:
    if not PRODUCT.exists():
        raise SystemExit(f"product binary missing: {PRODUCT}")
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m26-baseline-%Y%m%dT%H%M%SZ"))
    out_dir = run_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = collect()
    print(f"replaying {len(cases)} recorded BC observations through the product")
    print(f"run dir: {run_dir}\n")

    pair_fail, status_fail = [], []
    for idx, c in enumerate(cases):
        out = out_dir / f"case{idx:04d}.xml"
        proc = subprocess.run(
            [str(PRODUCT), c["left_path"], c["right_path"], str(out)],
            capture_output=True, timeout=120)
        c["product_exit"] = proc.returncode
        if proc.returncode == 0 and out.exists():
            rows = rows_of(out.read_bytes().decode("utf-8-sig", errors="replace"))
            c["product_rows"] = rows
            c["product_pairs"] = pairs_of(rows)
        else:
            c["product_rows"], c["product_pairs"] = [], []
        c["same_pairs"] = (c["product_pairs"] == c["bc_pairs"])
        c["same_statuses"] = ([r[0] for r in c["product_rows"]] == c["bc_statuses"])
        if not c["same_pairs"]:
            pair_fail.append(c)
        elif not c["same_statuses"]:
            status_fail.append(c)
        if not c["same_pairs"]:
            print(f"  DIFF [{idx:04d}] {c['src']}")

    print(f"\n=== pairing mismatches ({len(pair_fail)}) ===")
    for c in pair_fail:
        print(f"-- {c['src']}  (exit {c['product_exit']})")
        print(f"   L={c['left']}")
        print(f"   R={c['right']}")
        print(f"   BC   ={c['bc_rows']}")
        print(f"   prod ={c['product_rows']}")

    print(f"\n=== status-only mismatches ({len(status_fail)}) ===")
    for c in status_fail:
        print(f"-- {c['src']}")
        print(f"   BC   ={c['bc_statuses']}")
        print(f"   prod ={[r[0] for r in c['product_rows']]}")

    payload = {
        "product": str(PRODUCT),
        "cases": [{k: v for k, v in c.items()} for c in cases],
    }
    (run_dir / "m26-baseline.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\ncases                 : {len(cases)}")
    print(f"pairing mismatches    : {len(pair_fail)}")
    print(f"status-only mismatches: {len(status_fail)}")
    print(f"raw                   : {run_dir / 'm26-baseline.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

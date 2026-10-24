#!/usr/bin/env python3
"""U5g probe -- directory `<size>` display rules under partial expansion.

The reports observed so far show a directory row's `<size>` as `<size/>` in
some runs and an aggregate number in others:

    no expand            other, sub ......... `<size/>`
    expand all           other=4, sub=8 ..... aggregated
    expand "sub"         sub ............... `<size/>`  (!)  sub IS expanded
    filter "*.nomatch"   sub=8 ............. aggregated, but no child rows

The last two are the interesting ones: `sub` is expanded in the third case and
still empty, and the fourth case aggregates while hiding every child.  M4's
interpreter must reproduce whichever rule produces this, so this probe walks a
three-level tree through every expansion shape that could separate the models:

  H1  size shows only when the WHOLE subtree is expanded
  H2  size = sum of visible child sizes (empty when a child has none)
  H3  size is an independent property set at load time

It also measures:
  * whether `<size>` on a directory ignores the name filter (u5c suggested it
    does -- sub showed 8 with every child filtered out),
  * `expand <path>` for a nested path whose parent is not expanded,
  * repeated `expand` commands accumulating,
  * `load <default>` and `load create:all <path>`.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5g_dir_size_rules.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def structure(body: str) -> list[dict]:
    """Parse the report into an ordered list of rows with depth and own size."""
    rows: list[dict] = []
    # Row starts; then read the row's own <lt> name/size up to </rt>.
    pattern = re.compile(
        r"<(foldercomp|filecomp)(?: status=\"([a-z]+)\")?>"
        r"(.*?)"
        r"(?:<(foldercomp|filecomp))", re.S)
    # Simpler: walk line by line tracking depth, collecting the FIRST size after
    # each lt name (the row's own size).
    depth = 0
    cur: dict | None = None
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("<foldercomp") or s.startswith("<filecomp"):
            if cur is not None:
                rows.append(cur)
            kind = "folder" if s.startswith("<foldercomp") else "file"
            m = re.search(r'status="([a-z]+)"', s)
            cur = {"kind": kind, "status": m.group(1) if m else None,
                   "depth": depth, "name": None, "size": None,
                   "seen_lt_name": False}
            continue
        if s.startswith("</foldercomp") or s.startswith("</filecomp"):
            if cur is not None:
                rows.append(cur)
                cur = None
            depth -= 1
            continue
        if cur is not None:
            if s.startswith("<name>") and not cur["seen_lt_name"]:
                cur["name"] = s[6:-7]
                cur["seen_lt_name"] = True
            elif s.startswith("<size") and cur["size"] is None:
                cur["size"] = "EMPTY" if s == "<size/>" else s[6:-7]
            elif s.startswith("</rt>"):
                # The row's own lt/rt block is closed before its children.
                pass
        if s.startswith("<foldercomp") or s.startswith("<filecomp"):
            depth += 1
    if cur is not None:
        rows.append(cur)
    return rows


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5g-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    for side in ("L", "R"):
        (fx / side / "A" / "B").mkdir(parents=True, exist_ok=True)
        (fx / side / "C").mkdir(parents=True, exist_ok=True)
        (fx / side / "A" / "B" / "f.txt").write_bytes(b"fffff\n")
        (fx / side / "A" / "g.txt").write_bytes(b"ggg\n")
        (fx / side / "h.txt").write_bytes(b"hhhh\n")
        (fx / side / "C" / "i.txt").write_bytes(b"ii\n")
    L, R = fx / "L", fx / "R"
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, lines: list[str]) -> dict:
        out = run_dir / "reports" / f"{tag}.xml"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(L), str(R), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        rows = structure(body)
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes, "rows": rows, "report_body": body}
        records.append(rec)
        desc = " | ".join(
            f"{'  ' * r['depth']}{r['kind'][:4]}:{r['name']}={r['size']}"
            for r in rows)
        print(f"  {tag:<24} exit={run.exit_code:<4} {desc}")
        return rec

    rp = ['folder-report layout:xml output-to:"%3"']
    case("s1-no-expand", [f'load "{L}" "{R}"'] + rp)
    case("s2-expand-all", [f'load "{L}" "{R}"', "expand all"] + rp)
    case("s3-expand-A", [f'load "{L}" "{R}"', 'expand "A"'] + rp)
    case("s4-expand-A-B", [f'load "{L}" "{R}"', 'expand "A\\B"'] + rp)
    case("s5-expand-A-then-B", [f'load "{L}" "{R}"', 'expand "A"', 'expand "A\\B"'] + rp)
    case("s6-expand-A-and-C", [f'load "{L}" "{R}"', 'expand "A"', 'expand "C"'] + rp)
    case("s7-expand-all-filter", [f'load "{L}" "{R}"', "expand all",
                                  'filter "*.nomatch"'] + rp)
    case("s8-filter-then-expand", [f'load "{L}" "{R}"', 'filter "*.nomatch"',
                                   "expand all"] + rp)
    case("s9-expand-all-criteria", [f'load "{L}" "{R}"', "criteria size",
                                    "expand all"] + rp)
    # Documented forms that were never exercised.
    case("s10-load-default", ["load <default>"] + rp)
    case("s11-create-all", [f'load create:all "{fx / "new-L"}" "{fx / "new-R"}"',
                            "expand all"] + rp)

    (run_dir / "u5g-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5g-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

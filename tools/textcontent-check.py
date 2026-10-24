#!/usr/bin/env python3
"""Offline content gate: the product's ledger (reacmp-gui --dispatch --dump)
must equal an INDEPENDENT direct engine run, row by row, byte for byte
(status, both texts, both line ids) — plus the text-anchor check: every ledger
text equals the actual source line (ltid/rtid index into the input files).
With a display button (third arg) the product runs --display and the gate
runs the engine's FILTERING three-path form with the MEASURED option for that
button (filter-map.json button_to_option; the @script channel does not filter,
exec.rs ReportOptions::default() — see docs/19 §6.11).
This proves the GUI neither loses nor invents diff rows between engine and
window; the live pixel gate (uia-text-content-check.py) covers rendering.

Usage: python tools/textcontent-check.py <spec.json> <left> <right> [All|Diffs|Same] [ledger-out]
Exit 0 = identical; 1 = differences; 2 = launch/parse failure.
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
ENGINE = r"D:\Rea\product\cli\target\release\reacmp.exe"
ROOT_ORACLE = r"D:\Rea\extracted\live\textfilter2-en"


def main():
    spec, left, right = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    btn = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].endswith(".json") else None
    ledger = sys.argv[5] if btn and len(sys.argv) > 5 else (
        (sys.argv[4] if len(sys.argv) > 4 else None) or os.path.join(
            os.environ.get("TEMP", "."), "textcontent-ledger.json"))

    argv = ["dotnet", DLL, "--menu-spec", spec, "--dispatch", left, right, "--engine", ENGINE]
    if btn:
        argv += ["--display", btn]
    r = subprocess.run(argv + ["--dump", ledger], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        return 2

    # ground truth: the engine called directly. The @script channel does NOT
    # filter (measured, docs/19 §6.11); the display gate uses the FILTERING
    # three-path form, mirroring exactly what the GUI bridge calls.
    tmp = os.path.join(os.environ.get("TEMP", "."), f"tcheck-{os.getpid()}.xml")
    if btn:
        fm = json.load(open(os.path.join(ROOT_ORACLE, "filter-map.json"), encoding="utf-8"))
        opt = fm["button_to_option"][btn]
        argv = [ENGINE, left, right, tmp] + ([f"--opt={opt}"] if opt != "display-all" else [])
        subprocess.run(argv, check=True)
    else:
        script = os.path.join(os.environ.get("TEMP", "."), f"tcheck-{os.getpid()}.bcscript")
        with open(script, "w", encoding="utf-8") as f:
            f.write(f'text-report layout:xml output-to:"{tmp}" "{left}" "{right}"\n')
        subprocess.run([ENGINE, "@" + script], check=True)
        os.remove(script)
    grid = []
    for lc in ET.parse(tmp).getroot().iter("linecomp"):
        st = lc.get("status")
        row = {"status": st, "ltext": None, "rtext": None, "ltid": None, "rtid": None}
        for tx in lc.findall("text"):
            if tx.get("ltid"):
                row["ltext"] = tx.text or ""
                row["ltid"] = int(tx.get("ltid"))
            if tx.get("rtid"):
                row["rtext"] = tx.text or ""
                row["rtid"] = int(tx.get("rtid"))
        grid.append(row)
    md = ET.parse(tmp).getroot().find(".//filecomparison/mode")
    mode = md.text if md is not None else None
    os.remove(tmp)

    led = json.load(open(ledger, encoding="utf-8"))
    rows = led.get("content", {}).get("rows", [])
    problems = []
    if led.get("content", {}).get("mode") != mode:
        problems.append(f"mode: ledger={led.get('content', {}).get('mode')!r} engine={mode!r}")
    if len(rows) != len(grid):
        problems.append(f"row count: ledger={len(rows)} engine={len(grid)}")
    for i, (a, b) in enumerate(zip(rows, grid)):
        for key in ("status", "ltext", "rtext", "ltid", "rtid"):
            if a.get(key) != b[key]:
                problems.append(f"row {i} {key}: ledger={a.get(key)!r} engine={b[key]!r}")

    # text anchor: ledger texts ARE lines of the input files (ltid/rtid based)
    L = open(left, encoding="utf-8").read().split("\n")
    R = open(right, encoding="utf-8").read().split("\n")
    for i, a in enumerate(rows):
        if a.get("ltext") is not None and a["ltext"] != L[a["ltid"] - 1]:
            problems.append(f"row {i} left text not anchored to file line {a['ltid']}")
        if a.get("rtext") is not None and a["rtext"] != R[a["rtid"] - 1]:
            problems.append(f"row {i} right text not anchored to file line {a['rtid']}")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"OK: ledger {len(rows)} rows == engine rows (statuses+tids+texts), "
          f"all texts anchored to source lines; view={led['view']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

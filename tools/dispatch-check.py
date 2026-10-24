#!/usr/bin/env python3
"""Dispatch gate: replay the 7 MEASURED cells of the spec dispatch table
through reacmp-gui --dispatch (offline; no window), plus the task-only
rejection (exit 3) for the six file-routed-less views, plus the measured
title rule verbatim for the first cells.

Usage: python tools/dispatch-check.py [spec.json]
Exit 0 = every cell routes as measured and every reject fires.
"""
import json
import os
import subprocess
import sys

ROOT = r"D:\Rea"
DLL = os.path.join(ROOT, r"product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll")
ENGINE = os.path.join(ROOT, r"product\cli\target\release\reacmp.exe")

# corpus that EXISTS on disk: same inputs the Oracle cells were measured on
CORPUS = {
    ".txt": (r"D:\Rea\tools\textcolor\content-left.txt", r"D:\Rea\tools\textcolor\content-right.txt"),
    ".bin": (r"D:\Rea\verify\hex\h-int-600-L.bin", r"D:\Rea\verify\hex\h-int-600-R.bin"),
    ".csv": (r"D:\Rea\verify\table\t-dups-positional-L.csv", r"D:\Rea\verify\table\t-dups-positional-R.csv"),
    ".png": (r"D:\Rea\verify\pic\p-alpha-ignored-L.png", r"D:\Rea\verify\pic\p-alpha-ignored-R.png"),
    ".reg": (r"D:\Rea\verify\reg\r-casetie-sid-L.reg", r"D:\Rea\verify\reg\r-casetie-sid-R.reg"),
    ".zqq": (r"D:\Rea\verify\fb-L.zqq", r"D:\Rea\verify\fb-R.zqq"),
    "dirs": (r"D:\Rea\verify\dir\trees\L", r"D:\Rea\verify\dir\trees\R"),
}


def run(spec, a, b):
    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    r = subprocess.run(["dotnet", DLL, "--menu-spec", spec, "--dispatch", a, b,
                        "--engine", ENGINE], capture_output=True, text=True, env=env)
    return r


def main():
    spec = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, r"extracted\_scratch\menu-spec.json")
    sp = json.load(open(spec, encoding="utf-8"))
    disp = sp["dispatch"]
    problems = []
    ok = 0
    cells = list(disp["cells"]) + [disp["fallback"]]
    for cell in cells:
        exts = cell.get("match") or []
        key = "dirs" if cell.get("kind") == "dirs" else (exts[0] if exts else ".zqq")
        # fallback (measured .zqq probe) uses the .zqq corpus pair
        a, b = CORPUS[key]
        r = run(spec, a, b)
        line = next((l for l in r.stdout.splitlines() if l.startswith("DISPATCH: ")), "")
        got = line.split(" -> ")[1].split(" (")[0] if " -> " in line else f"rc={r.returncode}"
        if got != cell["view"] or r.returncode != 0:
            problems.append(f"cell {key}: want={cell['view']} got={got}")
        else:
            # title rule verbatim for the first three measured cells; D1
            # (docs/20): measured BC STRUCTURE kept, brand token = LiuCompare.
            tline = next((l for l in r.stdout.splitlines() if l.startswith("DISPATCH-TITLE: ")), "")
            expect = (os.path.basename(a) + " <--> " + os.path.basename(b) + " - " + cell["view"]
                      + " - LiuCompare")
            if tline[len("DISPATCH-TITLE: "):] != expect:
                problems.append(f"title {key}: want={expect!r} got={tline!r}")
            ok += 1
        print(f"{'OK ' if got == cell['view'] else 'FAIL'} {key} -> {got}")
    # task-only rejects, executed for real: inject a synthetic '.tonly' cell per
    # task-only view into a temp spec copy; --dispatch MUST exit 3 (no file
    # route there by measurement — the reject path is the contract, not a guess).
    for tv in disp["task_only"]:
        mod = json.loads(json.dumps(sp))
        mod["dispatch"]["cells"] = [c for c in mod["dispatch"]["cells"] if c["view"] != tv]
        mod["dispatch"]["cells"].insert(0, {"kind": "ext", "match": [".tonly"], "view": tv,
                                            "evidence": "synthetic reject probe"})
        tmp_spec = os.path.join(ROOT, "_tmp", f"reject-{tv.replace(' ', '')}.json")
        os.makedirs(os.path.dirname(tmp_spec), exist_ok=True)
        json.dump(mod, open(tmp_spec, "w", encoding="utf-8"))
        # route a real .tonly pair through the synthetic cell so the reject
        # path (exit 3) actually fires: the engine would never be reached.
        tpair = os.path.join(ROOT, "_tmp", "x.tonly")
        open(tpair, "w").write("a\n")
        r = run(tmp_spec, tpair, tpair)
        rejected = r.returncode == 3 and "DISPATCH-REJECT" in (r.stderr + r.stdout)
        if not rejected:
            problems.append(f"reject {tv}: expected exit 3, got rc={r.returncode} "
                            f"out={(r.stdout or '').strip()[:80]}")
        else:
            ok += 1
        print(f"{'OK ' if rejected else 'FAIL'} reject {tv} (exit {r.returncode})")
    print(f"\ndispatch: {ok} green (7 cells+titles, 6 task-only exits 3)")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

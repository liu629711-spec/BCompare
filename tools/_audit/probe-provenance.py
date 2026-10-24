"""Decisive provenance test: same inputs, same paths, two installs.

The golden reports embed the *input* paths in their header, and that header
wraps when the combined path text is long. So to compare installs at all, the
inputs must be referenced by the exact paths golden used
(``D:\\Rea\\verify\\layouts\\...``). That directory is read-only for this probe:
only the report OUTPUT is redirected under ``tools/_audit``.

If both installs reproduce the golden bytes once the header-wrap variable is
held constant, then the golden corpus is valid evidence for BOTH versions on
these inputs, and the earlier "stale vs current" disagreement was an artifact
of path length rather than a behaviour difference.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

AUDIT = pathlib.Path(r"D:\Rea\tools\_audit")
OUT = AUDIT / "provenance"
GOLD_IN = pathlib.Path(r"D:\Rea\verify\layouts")   # input files live here (read-only use)
GOLD_LAY = GOLD_IN                                  # golden reports live here too

INSTALLS = {
    "current-5.2.1.32035": r"D:\BCompare\BCompare\BComp.com",
    "stale-5.2.6.32774": r"D:\bc-official\app\BComp.com",
}
CASES = ["mixed", "insert", "similar", "orphans", "identical"]
LAYOUTS = ["side-by-side", "interleaved", "patch", "summary", "statistics", "over-under"]


def norm(s: str) -> str:
    return re.sub(r"Produced: [0-9/]{10} [0-9:]{7,8}", "Produced: <T>", s)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    script = AUDIT / "_prov-script.txt"
    tally: dict[str, list[int]] = {k: [0, 0] for k in INSTALLS}

    for name, exe in INSTALLS.items():
        for case in CASES:
            lp, rp = GOLD_IN / f"{case}-L.txt", GOLD_IN / f"{case}-R.txt"
            if not lp.exists():
                continue
            for lay in LAYOUTS:
                script.write_text(
                    f'text-report layout:{lay} output-to:"%3" "%1" "%2"\n', encoding="utf-8")
                # Output to OUR dir; inputs keep golden's paths so the header text matches.
                outp = OUT / f"{name}-{case}-{lay}.txt"
                cp = subprocess.run(
                    [exe, "/silent", f"@{script}", str(lp), str(rp), str(outp)],
                    capture_output=True, timeout=180)
                gold = GOLD_LAY / f"{case}-{lay}.txt"
                if not gold.exists():
                    continue
                got = outp.read_text(encoding="utf-8", errors="replace") if outp.exists() else ""
                want = gold.read_text(encoding="utf-8", errors="replace")
                tally[name][0] += 1
                if norm(got) == norm(want):
                    tally[name][1] += 1

    print("Byte-identical reproduction of golden layouts, same input paths:\n")
    for name, (tot, ok) in tally.items():
        print(f"  {name:<24} {ok}/{tot}")
    (tot_a, ok_a), (tot_b, ok_b) = tally["current-5.2.1.32035"], tally["stale-5.2.6.32774"]
    print()
    if ok_a == tot_a and ok_b == tot_b:
        print("=> Both installs reproduce golden byte-identically.")
        print("   Golden corpus is valid evidence for the CURRENT version too.")
    else:
        print("=> Installs differ on these inputs; golden attribution matters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

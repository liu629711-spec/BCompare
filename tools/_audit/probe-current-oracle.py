"""Audit probe: does the CURRENT install reproduce the golden oracle data?

Golden data was captured by `tools/bc-anchor-suite.py` / `bc-layout-capture.py`,
whose READMEs attribute it to "BCompare 5.2.6 / BComp.com". The declared project
target is 5.2.1.32035. This probe regenerates the same reports from both
installs and diffs them against the golden bytes after normalizing the two
volatile fields (timestamp, absolute path).

Read-only w.r.t. existing assets: writes only under tools/_audit/.
"""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re
import subprocess

TOOLS = pathlib.Path(r"D:\Rea\tools")
AUDIT = TOOLS / "_audit" / "oracle-current"
GOLD = pathlib.Path(r"D:\Rea\verify\layouts")

INSTALLS = {
    "current-5.2.1.32035": pathlib.Path(r"D:\BCompare\BCompare\BComp.com"),
    "stale-5.2.6.32774": pathlib.Path(r"D:\bc-official\app\BComp.com"),
}

CASES = {
    "mixed": (b"same line\ncase diff\nreal diff 1\nreal diff 2\ntail\n",
              b"same line\nCASE DIFF\nreal diff 9\ntail\n"),
    "insert": (b"a\nc\n", b"a\nb\nc\n"),
    "similar": (b"alpha\nbeta\n", b"ALPHA\nbeta\n"),
    "orphans": (b"only-left\nshared\n", b"shared\nonly-right\n"),
    "identical": (b"x\ny\n", b"x\ny\n"),
}
LAYOUTS = ["side-by-side", "interleaved", "patch", "summary", "statistics", "over-under"]


def normalize(s: str) -> str:
    """Blank the two volatile fields so byte comparison is meaningful."""
    s = re.sub(r"Produced: [0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{1,2}:[0-9]{2}:[0-9]{2}",
               "Produced: <T>", s)
    # collapse any absolute directory that appears in a Left/Right file: line
    s = re.sub(r"[A-Za-z]:\\[^\s]*\\", lambda m: "<D>" + "\\", s)
    return s


def run(bc: pathlib.Path, script: pathlib.Path, left: pathlib.Path,
        right: pathlib.Path, out: pathlib.Path) -> tuple[int, str]:
    cp = subprocess.run([str(bc), "/silent", f"@{script}", str(left), str(right), str(out)],
                        capture_output=True, timeout=120)
    text = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
    return cp.returncode, text


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    script = AUDIT / "_probe-script.txt"

    print("BComp.com identities")
    for name, p in INSTALLS.items():
        if not p.exists():
            print(f"  {name}: MISSING {p}")
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"  {name}: {p}\n    size={p.stat().st_size} sha256={h}")

    # Inputs are written once; both installs read the same bytes.
    for cname, (lb, rb) in CASES.items():
        (AUDIT / f"{cname}-L.txt").write_bytes(lb)
        (AUDIT / f"{cname}-R.txt").write_bytes(rb)

    agree = disagree = 0
    for inst_name, bc in INSTALLS.items():
        if not bc.exists():
            continue
        print(f"\n===== {inst_name} =====")
        for cname in CASES:
            lp = AUDIT / f"{cname}-L.txt"
            rp = AUDIT / f"{cname}-R.txt"
            for lay in LAYOUTS:
                script.write_text(
                    f'text-report layout:{lay} output-to:"%3" "%1" "%2"\n', encoding="utf-8")
                out = AUDIT / f"{inst_name}-{cname}-{lay}.txt"
                rc, got = run(bc, script, lp, rp, out)
                gold_file = GOLD / f"{cname}-{lay}.txt"
                if not gold_file.exists():
                    print(f"  {cname}-{lay:<12} rc={rc} NO-GOLDEN")
                    continue
                want = gold_file.read_text(encoding="utf-8", errors="replace")
                ok = normalize(got) == normalize(want)
                if ok:
                    agree += 1
                else:
                    disagree += 1
                    a = normalize(got).splitlines()
                    b = normalize(want).splitlines()
                    print(f"  {cname}-{lay:<12} rc={rc} MISMATCH")
                    for i in range(max(len(a), len(b))):
                        x = a[i] if i < len(a) else "<none>"
                        y = b[i] if i < len(b) else "<none>"
                        if x != y:
                            print(f"      line {i+1}: got={x!r}")
                            print(f"               gold={y!r}")
                            break
    print(f"\nTotals: {agree} match / {disagree} mismatch vs golden (normalized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

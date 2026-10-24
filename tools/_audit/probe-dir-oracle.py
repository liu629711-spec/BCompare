"""Prove the correct folder-report oracle recipe against the CURRENT install.

The pre-existing attempt in verify/dir/ failed with exit 106 and produced 0
bytes. Official help (help/scripting_reference.html, FOLDER-REPORT) shows why:
`folder-report` reports "the currently loaded base folders", so a `load` command
must come first -- unlike `text-report`, which takes its two paths as arguments.

This probe establishes a WORKING recipe on the current 5.2.1.32035 install,
reading the existing fixture trees in verify/dir/trees (read-only) and writing
only under tools/_audit.
"""
from __future__ import annotations

import pathlib
import subprocess

AUDIT = pathlib.Path(r"D:\Rea\tools\_audit")
TREES = pathlib.Path(r"D:\Rea\verify\dir\trees")
BC = r"D:\BCompare\BCompare\BComp.com"

VARIANTS = {
    # hypothesis A: load then folder-report, no %1/%2 args
    "load-then-report": 'load "%1" "%2"\n'
                        'folder-report layout:xml output-to:"%3"\n',
    # hypothesis B: expand all (to include subfolders) before reporting
    "load-expand-report": 'load "%1" "%2"\n'
                          'expand all\n'
                          'folder-report layout:xml output-to:"%3"\n',
    # hypothesis C: the form the old (failing) script used, for contrast
    "report-only": 'folder-report layout:xml output-to:"%3" "%1" "%2"\n',
}


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    left, right = TREES / "L", TREES / "R"
    print(f"fixtures: {left}  vs  {right}\n")
    for name, tmpl in VARIANTS.items():
        script = AUDIT / f"_dir-{name}.txt"
        script.write_text(tmpl, encoding="utf-8")
        outp = AUDIT / f"dir-{name}.xml"
        if outp.exists():
            outp.unlink()
        cp = subprocess.run(
            [BC, "/silent", f"@{script}", str(left), str(right), str(outp)],
            capture_output=True, timeout=180)
        size = outp.stat().st_size if outp.exists() else 0
        print(f"  {name:<20} exit={cp.returncode:<4} bytes={size}")
        if size:
            head = outp.read_text(encoding="utf-8", errors="replace")[:300]
            print("     " + head.replace("\n", "\n     ")[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

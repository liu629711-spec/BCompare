"""Establish the folder-compare CRITERIA model on the current install.

verify/dir/trees fixtures deliberately contain a content difference
(diff.txt = "aaaa" vs "bbbb") that the default report calls `same`. That implies
the default criteria is timestamp+size rather than content. This probe tests the
criteria commands named in help/scripting_reference.html to record which ones
change the verdict, so the feature matrix can state the default with evidence.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

AUDIT = pathlib.Path(r"D:\Rea\tools\_audit")
TREES = pathlib.Path(r"D:\Rea\verify\dir\trees")
BC = r"D:\BCompare\BCompare\BComp.com"

CRITERIA = {
    "default(no criteria)": "",
    "criteria timestamp": "criteria timestamp\n",
    "criteria size": "criteria size\n",
    "criteria crc": "criteria crc\n",
    "criteria content": "criteria content\n",
    "criteria binary-content": "criteria binary-content\n",
    "criteria rules-based": "criteria rules-based\n",
}


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    left, right = TREES / "L", TREES / "R"
    print("Does the fixture's content difference get detected under each criteria?\n")
    for name, crit in CRITERIA.items():
        script = AUDIT / "_crit-script.txt"
        script.write_text(
            f"{crit}load \"%1\" \"%2\"\n"
            f'folder-report layout:xml output-to:"%3"\n',
            encoding="utf-8")
        outp = AUDIT / "crit.xml"
        if outp.exists():
            outp.unlink()
        cp = subprocess.run(
            [BC, "/silent", f"@{script}", str(left), str(right), str(outp)],
            capture_output=True, timeout=180)
        if not outp.exists():
            print(f"  {name:<26} exit={cp.returncode}  <no output>")
            continue
        xml = outp.read_text(encoding="utf-8", errors="replace")
        # statuses of the two content-differing files
        pairs = re.findall(
            r'<filecomp status="([a-z]+)">(.*?)</filecomp>', xml, re.S)
        verdicts = {}
        for st, body in pairs:
            for fn in ("diff.txt", "samesize.bin"):
                if f"<name>{fn}</name>" in body:
                    verdicts[fn] = st
        print(f"  {name:<26} exit={cp.returncode}  diff.txt={verdicts.get('diff.txt')}"
              f"  samesize.bin={verdicts.get('samesize.bin')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

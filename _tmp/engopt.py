from PIL import Image
from collections import Counter
import subprocess, os, tempfile, xml.etree.ElementTree as ET

L = r"D:\Rea\tools\textcolor\content-left.txt"
R = r"D:\Rea\tools\textcolor\content-right.txt"

def eng(opt):
    script = os.path.join(tempfile.gettempdir(), "f.bcscript")
    out = os.path.join(tempfile.gettempdir(), "f.xml")
    open(script, "w", encoding="utf-8").write(
        f'text-report layout:xml options:{opt} output-to:"{out}" "{L}" "{R}"\n')
    rc = subprocess.run([r"D:\Rea\product\cli\target\release\reacmp.exe", "@" + script],
                        capture_output=True, text=True)
    if rc.returncode != 0:
        return f"rc={rc.returncode}: {rc.stderr.strip()[:80]}"
    root = ET.parse(out).getroot()
    md = root.find(".//filecomparison/mode")
    rows = [lc.get("status") for lc in root.iter("linecomp")]
    return len(rows), (md.text if md is not None else None), rows

for opt in ("display-all", "display-mismatches", "display-matches",
            "display-context", "ignore-unimportant"):
    r = eng(opt)
    print(f"{opt:18s}", r)

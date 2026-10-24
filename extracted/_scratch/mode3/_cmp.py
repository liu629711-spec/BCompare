import re, pathlib, sys, subprocess
import xml.etree.ElementTree as ET
REA = pathlib.Path(r"D:\Rea")
PROD = REA/"product/cli/target/release/reacmp.exe"
RUNS = REA/"product/verify/runs"
def find(tag):
    for d in sorted(RUNS.glob("gateb-*")):
        op=d/"reports"/f"{tag}.oracle.xml"
        if op.exists(): return d/"fixtures"/f"{tag}-L.txt", d/"fixtures"/f"{tag}-R.txt", op
def prod_rows(lp, rp, out):
    subprocess.run([str(PROD), str(lp), str(rp), str(out)], capture_output=True, timeout=300)
    body = out.read_bytes().decode("utf-8-sig", errors="replace")
    rows=[]
    for m in re.finditer(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', body, re.S):
        lt=re.search(r'ltid="(-?\d+)"', m.group(2)); rt=re.search(r'rtid="(-?\d+)"', m.group(2))
        rows.append((m.group(1), int(lt.group(1)) if lt else None, int(rt.group(1)) if rt else None))
    return rows
def orows(path):
    t=ET.parse(path); fc=t.getroot().find("filecomparison"); out=[]
    for el in fc:
        st=el.get("status")
        if st is None: continue
        l=r=None
        for c in el:
            if c.tag=="text":
                if c.get("ltid") is not None: l=int(c.get("ltid"))
                if c.get("rtid") is not None: r=int(c.get("rtid"))
        out.append((st,l,r))
    return out
for tag in sys.argv[1:]:
    lp, rp, op = find(tag)
    got = prod_rows(lp, rp, pathlib.Path(f"_prod_{tag}.xml"))
    want = orows(op)
    print(f"### {tag} {'PASS' if got==want else 'FAIL'}")
    if got != want:
        print("  want:", want[:6])
        print("  got :", got[:6])

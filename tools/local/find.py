import json, re, pathlib, sys, collections
ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]

def unit(a):
    v = FNS.get(a.lower())
    return v["unit"] if v else "?"

def load(a):
    a=a.lower().replace("0x","")
    p=PC/(a+".c")
    return p.read_text(encoding="utf-8",errors="replace") if p.exists() else None

def grep(pat, unitfilter=None, limit=60):
    rx=re.compile(pat)
    n=0
    for a,v in sorted(FNS.items(), key=lambda x:int(x[0],16)):
        if unitfilter and unitfilter not in v["unit"]: continue
        t=load(a)
        if not t: continue
        b=t.split("--------",1)[-1]
        for m in rx.finditer(b):
            line=b[:m.start()].count("\n")
            ln=b.splitlines()[line].strip()
            print("%s[%s] L%d: %s"%(a,v["unit"],line,ln[:150]))
            n+=1
            if n>=limit: return
if __name__=="__main__":
    grep(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None, int(sys.argv[3]) if len(sys.argv)>3 else 60)

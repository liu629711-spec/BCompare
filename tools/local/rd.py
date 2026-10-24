import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]
CALLRE = re.compile(r"\bFUN_([0-9a-f]{9,})\b")
STRRE = re.compile(r'L"([^"\n]*)"')
ASSRE = re.compile(r'L"Assertion failure",\s*L"([^"]+)",\s*(0x[0-9a-f]+)')


def unit(a):
    v = FNS.get(a.lower())
    return v["unit"] if v else "?"


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def body(a):
    t = load(a)
    if not t:
        return ""
    return t.split("--------", 1)[-1]


def show(a, start=0, end=10 ** 9, hdr=True, names=False):
    a = a.lower().replace("0x", "")
    t = load(a)
    if not t:
        print("MISSING", a)
        return
    b = body(a)
    lines = b.splitlines()
    if hdr:
        print("=" * 80)
        print("ADDR", a, "size", FNS.get(a, {}).get("size"), "unit", unit(a))
        ss = list(dict.fromkeys(STRRE.findall(t)))
        if ss:
            print("STR:", " | ".join(ss))
        for m in ASSRE.finditer(t):
            print("ASSERT", m.group(1).split("\\")[-1], int(m.group(2), 16))
        cs = collections.Counter()
        for c in CALLRE.findall(b):
            cs[(c, unit(c))] += 1
        print("CALLS:", ", ".join("%s[%s]x%d" % (c, u, n) for (c, u), n in cs.most_common()))
    print("-" * 80)
    for i, ln in enumerate(lines):
        if start <= i < end:
            print(ln)


if __name__ == "__main__":
    args = sys.argv[1:]
    for a in args:
        if ":" in a:
            a, rng = a.split(":")
            s, e = rng.split("-")
            show(a, int(s), int(e))
        else:
            show(a)

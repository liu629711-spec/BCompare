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
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def show(a, maxlen=100000):
    a = a.lower().replace("0x", "")
    t = load(a)
    if t is None:
        print("MISSING", a)
        return
    print("=" * 84)
    print("ADDR", a, "size", FNS.get(a, {}).get("size"), "unit", unit(a))
    ss = list(dict.fromkeys(STRRE.findall(t)))
    if ss:
        print("STRINGS:", " | ".join(ss))
    for m in ASSRE.finditer(t):
        print("ASSERT", m.group(1).split("\\")[-1], hex(int(m.group(2), 16)), int(m.group(2), 16))
    cs = collections.Counter()
    for c in CALLRE.findall(t):
        cs[(c, unit(c))] += 1
    print("CALLEES:", ", ".join("%s[%s]x%d" % (c, u, n) for (c, u), n in cs.most_common()))
    print("-" * 84)
    print(t[:maxlen])


if __name__ == "__main__":
    for a in sys.argv[1:]:
        show(a)

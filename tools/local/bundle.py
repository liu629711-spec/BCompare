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


def bundle(target):
    rows = sorted([(a, v) for a, v in FNS.items() if v["unit"] == target], key=lambda x: int(x[0], 16))
    print("#### ", target, len(rows), "fns", sum(r[1]["size"] for r in rows), "bytes")
    # external callee census
    ext = collections.Counter()
    extpairs = collections.Counter()
    allstr = collections.OrderedDict()
    asserts = []
    for a, v in rows:
        t = load(a)
        if not t:
            continue
        for c in set(CALLRE.findall(t)):
            u = unit(c)
            if u != target:
                ext[u] += 1
                extpairs[(u, c)] += 1
        for s in STRRE.findall(t):
            if s not in allstr:
                allstr[s] = a
        for m in ASSRE.finditer(t):
            asserts.append((a, m.group(1).split("\\")[-1], int(m.group(2), 16)))
    print("-- external callee units (target-fn count desc) --")
    for u, n in ext.most_common(25):
        print("   %-32s %d" % (u, n))
    print("-- strings (unique) --")
    for s, a in allstr.items():
        print("   %-34s @%s" % (s, a))
    print("-- assertions --")
    for a, f, ln in sorted(asserts, key=lambda x: x[2]):
        print("   %s  %s  line %d (0x%x)" % (a, f, ln, ln))


if __name__ == "__main__":
    for u in sys.argv[1:]:
        bundle(u)

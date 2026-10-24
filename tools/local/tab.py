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


def table(u, minsize=0):
    rows = sorted([(a, v) for a, v in FNS.items() if v["unit"] == u], key=lambda x: int(x[0], 16))
    for a, v in rows:
        if v["size"] < minsize:
            continue
        t = load(a)
        b = t.split("--------", 1)[-1] if t else ""
        ss = list(dict.fromkeys(STRRE.findall(t))) if t else []
        asrt = [int(m.group(2), 16) for m in ASSRE.finditer(t)] if t else []
        cs = collections.Counter()
        for c in set(CALLRE.findall(b)):
            cs[unit(c)] += 1
        ext = ",".join("%s:%d" % (k, n) for k, n in cs.most_common(6) if k != u)
        print("%s %5d %-16s | %-42s | A:%s | %s" % (
            a, v["size"], v["confidence"], ";".join(ss)[:42],
            ",".join(str(x) for x in asrt), ext))


if __name__ == "__main__":
    table(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)

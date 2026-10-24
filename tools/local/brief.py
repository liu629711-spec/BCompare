import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]
CALLRE = re.compile(r"\bFUN_([0-9a-f]{9,})\b")
STRRE = re.compile(r'L"([^"\n]*)"')
ASSRE = re.compile(r'L"Assertion failed?"[\s\S]{0,80}?0x([0-9a-f]+)')


def unit(a):
    v = FNS.get(a.lower())
    return v["unit"] if v else "?"


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def bodytext(t):
    lines = t.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("note:"):
            return "\n".join(lines[i + 1:])
    return t


def brief(a, nlines=14):
    t = load(a)
    if not t:
        print("MISSING", a)
        return
    b = bodytext(t)
    lines = [l.strip() for l in b.splitlines() if l.strip()]
    ss = list(dict.fromkeys(STRRE.findall(t)))
    asrt = [int(m.group(1), 16) for m in ASSRE.finditer(t)]
    print("### %s  sz=%d %s" % (a, FNS.get(a.lower(), {}).get("size", 0), unit(a)))
    if ss:
        print("    STR:", " | ".join(ss)[:150])
    if asrt:
        print("    ASSERT:", ",".join(str(x) for x in asrt))
    print("    " + " ".join(lines[:nlines])[:900])
    print()


if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a.startswith("-n"):
            pass
        brief(a)

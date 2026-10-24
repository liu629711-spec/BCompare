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
    return t.split("--------", 1)[-1] if t else ""


def skel(a, drop_decl=True):
    t = load(a)
    b = body(a)
    print("=" * 78)
    print("### %s  sz=%d  %s" % (a, FNS.get(a.lower(), {}).get("size", 0), unit(a)))
    ss = list(dict.fromkeys(STRRE.findall(t)))
    if ss:
        print("STR:", " | ".join(ss))
    for m in ASSRE.finditer(t):
        print("ASSERT", m.group(1).split("\\")[-1], int(m.group(2), 16))
    out = []
    for ln in b.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s in ("{", "}", "return;"):
            continue
        if drop_decl and re.match(r"^(undefined\d*|char|byte|short|int|uint|longlong|ulonglong|float|double|bool|code|void|long|undefined|_Bool|size_t|uint3|byte3|undefined3|undefined5|undefined6|undefined7|uint7|longlong3|undefined1)\s", s) and "=" not in s.split(";")[0]:
            continue
        if drop_decl and re.match(r"^undefined\d* [a-zA-Z_]\w* \[", s):
            continue
        out.append(s)
    print("\n".join(out))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        skel(a)

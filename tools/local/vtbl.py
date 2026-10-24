import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]

VTOFF = re.compile(r"\*\(\s*code\s*\*\*\s*\)\s*\(\s*\*\s*(\w+)\s*\+\s*(0x[0-9a-f]+)\s*\)")


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def body(a):
    t = load(a)
    return t.split("--------", 1)[-1] if t else ""


def census(u, var="param_1", topn=200):
    rows = sorted([(a, v) for a, v in FNS.items() if v["unit"] == u], key=lambda x: int(x[0], 16))
    agg = collections.defaultdict(list)
    for a, v in rows:
        b = body(a)
        for m in VTOFF.finditer(b):
            if m.group(1) != var:
                continue
            agg[int(m.group(2), 16)].append(a)
    print("#### %s vtbl offsets on %s : %d distinct" % (u, var, len(agg)))
    for o in sorted(agg):
        ex = sorted(set(agg[o]))
        print("  vtbl+0x%03x  n=%3d  %s" % (o, len(agg[o]), ",".join(ex[:5])))


if __name__ == "__main__":
    census(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "param_1")

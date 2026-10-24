import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]

CALLRE = re.compile(r"\bFUN_([0-9a-f]{9,})\b")
# accesses relative to a named pointer var
OFFRE = re.compile(r"\b(\w+)\s*\+\s*(0x[0-9a-f]+)\b")
IDXRE = re.compile(r"\b(\w+)\[([0-9a-fx]+)\]")


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def offsets(target, varname="param_1"):
    rows = sorted([(a, v) for a, v in FNS.items() if v["unit"] == target], key=lambda x: int(x[0], 16))
    agg = collections.Counter()
    who = collections.defaultdict(set)
    for a, v in rows:
        t = load(a)
        if not t:
            continue
        body = t.split("--------", 1)[-1]
        for m in OFFRE.finditer(body):
            if m.group(1) != varname:
                continue
            agg[int(m.group(2), 16)] += 1
            who[int(m.group(2), 16)].add(a)
        for m in IDXRE.finditer(body):
            if m.group(1) != varname:
                continue
            x = m.group(2)
            if x.startswith("0x"):
                o = int(x, 16) * 8
            else:
                try:
                    o = int(x) * 8
                except ValueError:
                    continue
            agg[o] += 1
            who[o].add(a)
    print("#### %s : %d offsets for %s" % (target, len(agg), varname))
    for o, n in sorted(agg.items()):
        ex = sorted(who[o])[:4]
        print("  +0x%03x  n=%4d  %s" % (o, n, ",".join(ex)))


if __name__ == "__main__":
    offsets(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "param_1")

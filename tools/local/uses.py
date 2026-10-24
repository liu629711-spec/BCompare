import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]


def unit(a):
    v = FNS.get(a.lower())
    return v["unit"] if v else "?"


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def uses(target, scope=None, maxex=6):
    """Find all call sites of target; print the surrounding context lines."""
    t = target.lower()
    rx = re.compile(r"\bFUN_" + t + r"\b")
    sites = []
    files = [a for a, v in FNS.items() if scope is None or v["unit"] == scope]
    for a in sorted(files, key=lambda x: int(x, 16)):
        b = load(a)
        if not b:
            continue
        b = b.split("--------", 1)[-1]
        for m in rx.finditer(b):
            st = b.rfind("\n", 0, m.start()) + 1
            en = b.find("\n", m.end())
            sites.append((a, unit(a), b[st:en].strip()))
    print("#### uses of %s : %d sites" % (t, len(sites)))
    # summarize the immediate call-line
    ctx = collections.Counter()
    for a, u, s in sites:
        # normalize variable names
        n = re.sub(r"\blocal_[0-9a-f]+\b", "LOC", s)
        n = re.sub(r"\b\w+Var\d+\b", "VAR", n)
        ctx[n] += 1
    for n, c in ctx.most_common(maxex * 4):
        print("   %4d  %s" % (c, n[:150]))
    print("-- raw samples --")
    for a, u, s in sites[:maxex]:
        print("   %s[%s] %s" % (a, u, s[:150]))


if __name__ == "__main__":
    scope = sys.argv[2] if len(sys.argv) > 2 else None
    uses(sys.argv[1], scope)

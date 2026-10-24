import json, re, pathlib, sys, collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
PC = ROOT / "pseudocode"
ATT = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
FNS = ATT["functions"]


def load(a):
    a = a.lower().replace("0x", "")
    p = PC / (a + ".c")
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def body(a):
    t = load(a)
    return t.split("--------", 1)[-1] if t else ""


# resolve rvalue access: *(type *)(var + 0xNN) or var[idx]
BSRE = re.compile(r"\*\(\s*(?:u?int|undefined\d*|char|byte|short|longlong|ulonglong|bool|code|long|_Bool)\s*\*+\s*\)\s*\(\s*(\w+)\s*\+\s*(0x[0-9a-f]+)\)")
IDXRE = re.compile(r"\b(\w+)\[([0-9a-fx]+)\]")


def census(u, var="param_1"):
    rows = sorted([(a, v) for a, v in FNS.items() if v["unit"] == u], key=lambda x: int(x[0], 16))
    agg = collections.defaultdict(lambda: {"rd": 0, "wr": 0, "ex": []})
    for a, v in rows:
        b = body(a)
        for i, ln in enumerate(b.splitlines()):
            s = ln.strip()
            offs = []
            for m in BSRE.finditer(s):
                if m.group(1) == var:
                    offs.append(int(m.group(2), 16))
            for m in IDXRE.finditer(s):
                if m.group(1) == var:
                    x = m.group(2)
                    offs.append(int(x, 16) * 8 if x.startswith("0x") else int(x) * 8)
            if not offs:
                continue
            for o in offs:
                e = agg[o]
                if s.startswith("*(byte *)(%s + 0x%x) =" % (var, o)) or s.startswith("*(int *)(%s + 0x%x) =" % (var, o)) \
                   or re.match(r"^\*\([^)]*\)\( ?" + re.escape(var) + r" \+ 0x%x\) =" % o, s) or "=" == s[:1]:
                    e["wr"] += 1
                elif "=" in s and s.index("=") < s.find(var):
                    e["wr"] += 1
                else:
                    e["rd"] += 1
                if len(e["ex"]) < 2:
                    e["ex"].append((a, s[:110]))
    print("#### %s var=%s  %d distinct offsets" % (u, var, len(agg)))
    for o in sorted(agg):
        e = agg[o]
        print(" +0x%03x r=%3d w=%3d  %s" % (o, e["rd"], e["wr"],
              " || ".join("%s:%s" % (x[0], x[1]) for x in e["ex"])))


if __name__ == "__main__":
    census(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "param_1")

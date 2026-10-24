#!/usr/bin/env python3
"""M6.5b (m68): the two remaining unprobed table residuals, closed.

docs/13 §8.1 left exactly two open surfaces:

1. `.csv` MIXED-extension pairs (one side .csv, one side other). The
   implemented rule is "either file .csv => fixed comma on BOTH files"
   (CS1 wording), but every archived cell had matching extensions. These
   cells separate the candidate rules:
     (i)  either-.csv pins comma on both sides;
     (ii) .csv pins only its own side, the other side still joint-detects;
     (iii) joint detection ignores extensions except as a pair gate.

   MX1  L=`a;b ` .txt / R=`a;b ` .csv, no comma anywhere.
        (i) => both sides ONE cell `a;b` (comma pinned, trim drops the
        trailing space); (ii)+(iii) => joint semi-split both sides with
        cell `a;b ` or trimmed. Header shape separates rawline (1 col)
        from semi (2 cols) directly.
   MX2  L=`a;b` .txt / R=`c d` .CSV (UPPER).
        (i)+(pin case-insensitive) => 1-col comma both sides;
        (iii, gate case-INsensitive, joint scan finds semi) => 2-col semi;
        pin NOT case-insensitive => R treated as extension-less, joint
        semi again. Pair with MX3 to isolate case sensitivity.
   MX3  L=`a;b` .TXT / R=`c d` .CSV upper-vs-lower twin of MX2's gate.
   MX4  L=`a,b` .txt / R=`c;d` .csv.
        (i) => comma pins both: L splits a/b, R one cell `c;d`.
        (ii)=> same result here; (i) vs (ii) is separated by MX1/MX6.
   MX6  L=`a;b` .csv / R=`a;b` .txt.
        (i) comma both sides (1 col, cells `a;b`); (ii) L pinned comma
        1-col, R joint semi-split => header per-side mismatch is the
        readout. Direct (i) vs (ii) discriminator.

   All MX cells run side-by-side (column count is the binding readout;
   interleaved runs for the shape cells below).

2. interleaved RAWLINE forms (IR). sbs rawline was pinned (m67); the
   interleaved renderer never saw a rawline pair end-to-end:
   IR1  L=` ab`/`cd` vs ` ab`/`cX` -- leading-space drop holds in
        interleaved? (sbs SP10 said `ab`; interleaved must match or the
        trims threading has a layout-specific bug)
   IR2  L=`a b `/`c d ` vs identical -- trailing space is data:
        identical rows `=`, and the printed row KEEPS the run?
   IR3  L=`1`/`2` vs `1`/`3` -- numeric rawline cells in interleaved:
        left-justified like delimited numbers (T19/T21) or padded?

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m68_mixed_ext_interleaved_probe.py
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def C(*rows):
    return "".join(r + "\n" for r in rows)


#: (tag, left_name, left text, right_name, right text, layouts, note)
CASES = [
    ("MX1", "MX1-L.txt", C("a;b "), "MX1-R.csv", C("a;b "),
     ("side-by-side",), "no comma; (i) 1col vs (ii)/(iii) semi 2col"),
    ("MX2", "MX2-L.txt", C("a;b"), "MX2-R.CSV", C("c d"),
     ("side-by-side",), "upper .CSV gate: (i)+CI => 1col, no CI => semi"),
    ("MX3", "MX3-L.TXT", C("a;b"), "MX3-R.CSV", C("c;d"),
     ("side-by-side",), "upper both sides"),
    ("MX4", "MX4-L.txt", C("a,b"), "MX4-R.csv", C("c;d"),
     ("side-by-side",), "(i) comma both => L 2col R 1col"),
    ("MX6", "MX6-L.csv", C("a;b"), "MX6-R.txt", C("a;b"),
     ("side-by-side",), "(i) 1col both vs (ii) L 1col R 2col"),
    ("IR1", "IR1-L.txt", C(" ab", "cd"), "IR1-R.txt", C(" ab", "cX"),
     ("interleaved", "side-by-side"), "leading space dropped in interleaved?"),
    ("IR2", "IR2-L.txt", C("a b ", "c d "), "IR2-R.txt", C("a b ", "c d "),
     ("interleaved",), "trailing space kept as data; identical => ="),
    ("IR3", "IR3-L.txt", C("1", "2"), "IR3-R.txt", C("1", "3"),
     ("interleaved",), "numeric rawline interleaved justification"),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m68-mixedext-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, lname, ltext, rname, rtext, lays, note in CASES:
        lp = fx / lname; rp = fx / rname
        lp.write_text(ltext, encoding="utf-8", newline="")
        rp.write_text(rtext, encoding="utf-8", newline="")
        rec = {"tag": tag, "note": note, "left": ltext, "right": rtext,
               "left_name": lname, "right_name": rname, "reports": {}}
        for lay in lays:
            line = f'data-report layout:{lay} output-to:"%3" "%1" "%2"'
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", [line])
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            r = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                        str(out.resolve()), timeout=120.0, script_text=line)
            body = out.read_bytes() if out.exists() else b""
            rec["reports"][lay] = {"exit": r.exit_code, "bytes": len(body),
                                   "sha256": hashlib.sha256(body).hexdigest()}
            print(f"{tag} [{lay}] exit={r.exit_code}")
            for ln in body.decode("utf-8-sig", errors="replace").splitlines()[6:]:
                if ln.strip():
                    print("   ", repr(ln))
        results.append(rec)

    (run_dir / "m68-mixedext.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

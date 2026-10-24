#!/usr/bin/env python3
"""M6.4 batch-7: auto-detect delimiter set and priority (non-.csv extensions).

Settled facts (batch-5/6 archive):
* .csv => FIXED comma, no detection (D2/D4/D12; S1 twin shows .csv keeps
  tab inside one cell while .txt splits comma first).
* .txt/.tsv/.TXT/no-ext => auto-detect among {comma, semicolon, pipe, space,
  tab}; comma beats tab (S1). S4 (space-only) rendered 'A  B' / 'a  b' (TWO
  spaces between columns) while D6 (tab) rendered 'A B' (one) -- the space
  path's width semantics differ and are NOT yet modelled.

Open, one clean fixture per cell (.txt unless stated), side-by-side; W/M also
interleaved:

  pairwise priority (both delimiters inside ONE row; cells 1 char so the
  header letters show the split directly):
    G-pc  'a,b|c'   comma vs pipe
    G-sc  'a;b,c'   semicolon vs comma
    G-tc  'a\tb,c'  tab vs comma
    G-wc  'a b,c'   space vs comma
    G-ps  'a|b;c'   pipe vs semicolon
    G-pt  'a\tb|c'  tab vs pipe
    G-pw  'a|b c'   pipe vs space
    G-st  'a\tb;c'  tab vs semicolon
    G-sw  'a;b c'   semicolon vs space
    G-tw  'a\tb c'  tab vs space
  semantics:
    Q1    '"a,b" c'   qualifier shields comma; space still splits?
    W1    'a  b' / R 'a b'   mixed single/double space widths (two spaces?)
    M1    'a,b c,d'   comma(2 cells) vs space(3): majority-vs-priority
    S1    'hello'     no candidate: one column
    C1    .csv twin of G-pc: fixed comma must keep 'b|c' inside one cell

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m65_autodetect_probe.py
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


CASES = [
    # (tag, ext, left, right, layouts)
    ("G-pc", ".txt", C("a,b|c"),          C("a,b|X"),          ("side-by-side",)),
    ("G-sc", ".txt", C("a;b,c"),          C("a;b,X"),          ("side-by-side",)),
    ("G-tc", ".txt", C("a\tb,c"),         C("a\tb,X"),         ("side-by-side",)),
    ("G-wc", ".txt", C("a b,c"),          C("a b,X"),          ("side-by-side",)),
    ("G-ps", ".txt", C("a|b;c"),          C("a|b;X"),          ("side-by-side",)),
    ("G-pt", ".txt", C("a\tb|c"),         C("a\tb|X"),         ("side-by-side",)),
    ("G-pw", ".txt", C("a|b c"),          C("a|b X"),          ("side-by-side",)),
    ("G-st", ".txt", C("a\tb;c"),         C("a\tb;X"),         ("side-by-side",)),
    ("G-sw", ".txt", C("a;b c"),          C("a;b X"),          ("side-by-side",)),
    ("G-tw", ".txt", C("a\tb c"),         C("a\tb X"),         ("side-by-side",)),
    ("Q1",   ".txt", C('"a,b" c'),        C('"a,b" X'),        ("side-by-side",)),
    ("W1",   ".txt", C("a  b"),           C("a b"),            ("side-by-side", "interleaved")),
    ("M1",   ".txt", C("a,b c,d"),        C("a,b c,X"),        ("side-by-side", "interleaved")),
    ("S1",   ".txt", C("hello", "world"), C("hello", "warld"), ("side-by-side",)),
    ("C1",   ".csv", C("a,b|c"),          C("a,b|X"),          ("side-by-side",)),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m65-autodetect-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, ext, left, right, lays in CASES:
        lp = fx / f"{tag}-L{ext}"; rp = fx / f"{tag}-R{ext}"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "ext": ext, "left": left, "right": right, "reports": {}}
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
                print("   ", repr(ln))
            print()
        results.append(rec)

    (run_dir / "m65-autodetect.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

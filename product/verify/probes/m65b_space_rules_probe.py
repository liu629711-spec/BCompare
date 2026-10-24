#!/usr/bin/env python3
"""M6.4 batch-7b: close the last auto-detect ambiguities from m65.

batch-7 settled the priority chain (pairwise, equal-column ties):
  COMMA > TAB > SEMICOLON > PIPE > SPACE
(comma beats tab/semi/pipe/space: G-tc/G-sc/G-pc/G-wc; tab beats semi/pipe/
space: G-st/G-pt/G-tw; semi beats pipe/space: G-ps/G-sw; pipe beats space: G-pw.)

Still ambiguous, one clean fixture each (.txt unless stated):

  SP1  space ragged two rows 'a b' / 'cc d': model "join with TWO spaces" vs
       "per-cell width+1, join one" DIFFER ('a  b' vs 'a   b '). S4 alone
       could not discriminate.
  SP3  one row without any space ('ab' + 'c d'): empty-tolerant ragged, or
       reject the space candidate?
  SP4  quoted file 'a "b c"': Q1 suggested qualifiers block the space
       candidate -- confirm the rule with a clean single case.
  SP5  trailing space 'a b ': display trim under the space format.
  SP6  double space in ONE row of a two-row file: global rejection (W1) was
       single-row; does one bad row veto everything?
  CS1  .csv with space-only content: the FIXED-comma path must NOT split.
  PF1  left 'a b' vs right 'c,d': is detection per-file or joint? priority
       comma present only in RIGHT -- what does the LEFT split into?
  PF2  left 'a,b' vs right 'c d': mirror of PF1.
  TN1  tab ragged two rows 'a\tb' / 'cc\td': tab-format join/gap semantics
       (expect the normal single-space renderer, but measure).

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m65b_space_rules_probe.py
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
    ("SP1", ".txt", C("a b", "cc d"),        C("a b", "cc X"),        ("side-by-side", "interleaved")),
    ("SP3", ".txt", C("ab", "c d"),          C("ab", "c X"),          ("side-by-side",)),
    ("SP4", ".txt", C('a "b c"'),            C('a "b X"'),            ("side-by-side",)),
    ("SP5", ".txt", C("a b "),               C("a X "),               ("side-by-side",)),
    ("SP6", ".txt", C("a b", "c  d"),        C("a b", "c d"),         ("side-by-side",)),
    ("CS1", ".csv", C("a b", "c d"),         C("a b", "c X"),         ("side-by-side",)),
    ("PF1", ".txt", C("a b"),                C("c,d"),                ("side-by-side",)),
    ("PF2", ".txt", C("a,b"),                C("c d"),                ("side-by-side",)),
    ("TN1", ".txt", C("a\tb", "cc\td"),      C("a\tb", "cc\tdX"),     ("side-by-side",)),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m65b-spacerules-%Y%m%dT%H%M%SZ"))
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
        results.append(rec)

    (run_dir / "m65b-spacerules.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

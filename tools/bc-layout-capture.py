"""Capture all text-report layouts from BC for representative cases.

Extends the anchor suite: the 45 xml anchors verify the diff engine; this
captures the *presentation* layer (TextOutput.pas) for the same inputs.
"""
import importlib.util
import json
import pathlib

TOOLS = pathlib.Path(r"D:\Rea\tools")
OUT = pathlib.Path(r"D:\Rea\verify\layouts")

_spec = importlib.util.spec_from_file_location("bc_oracle", TOOLS / "bc-oracle.py")
bc_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc_oracle)

LAYOUTS = ["side-by-side", "interleaved", "patch", "summary", "statistics", "over-under"]

# Representative pairs covering the interesting cases.
CASES = {
    "mixed": (b"same line\ncase diff\nreal diff 1\nreal diff 2\ntail\n",
              b"same line\nCASE DIFF\nreal diff 9\ntail\n"),
    "insert": (b"a\nc\n", b"a\nb\nc\n"),
    "similar": (b"alpha\nbeta\n", b"ALPHA\nbeta\n"),
    "orphans": (b"only-left\nshared\n", b"shared\nonly-right\n"),
    "identical": (b"x\ny\n", b"x\ny\n"),
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    total = fails = 0
    for cname, (lb, rb) in CASES.items():
        lp = OUT / f"{cname}-L.txt"
        rp = OUT / f"{cname}-R.txt"
        lp.write_bytes(lb)
        rp.write_bytes(rb)
        for layout in LAYOUTS:
            out = OUT / f"{cname}-{layout}.txt"
            r = bc_oracle.run_report(lp, rp, out, layout=layout)
            total += 1
            ok = r["exit_code"] == 0
            if not ok:
                fails += 1
            manifest[f"{cname}-{layout}"] = {
                "layout": layout, "case": cname, "exit_code": r["exit_code"],
                "bytes": len(r["output"]), "report": str(out),
            }
            print(f"  {'ok  ' if ok else 'FAIL'} {cname}-{layout:<12} exit={r['exit_code']} {len(r['output']):>4}B")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"\n{total - fails}/{total} layout reports captured -> {OUT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

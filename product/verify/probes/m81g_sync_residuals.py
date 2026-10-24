#!/usr/bin/env python3
"""M81g: three residual sync cells + the m81c criteria-timestamp anomaly.

  G1  `criteria timestamp:2sec` + folder-report ONLY (no sync) -- is the 105
      in m81c C1 sync-specific or criteria-specific?
  G2  `criteria timestamp:2sec` + `sync mirror:left->right` -- re-pin 105.
  G3  `criteria timestamp` (plain, no tolerance) + sync update -- which token
      form is the 105 trigger?
  G4  `sync create-empty update:left->right` with a source-only EMPTY dir --
      does create-empty also make UPDATE copy empty dirs? (m81f only pinned
      it for mirror.)
  G5  `sync visible create-empty update:left->right` -- both flags in the
      documented order: accepted (exit 0)?
  G6  half-load clean form `load "<L>"` (single folder, no `:left` modifier --
      u5e measured this exact form for reports) then `sync update:left->right`
      -- resolves m81d D4's ambiguity (106 there may have been the load token).
  G7  `sync update:lr` -- is `lr` an accepted abbreviation for `left->right`?
      (Usage shows the long form; if lr works, the direction grammar is wider.)

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81g_sync_residuals.py
"""
from __future__ import annotations

import hashlib, json, os, pathlib, subprocess, sys, tempfile, time
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

DAY = 24 * 3600


def mkfile(p, content, mtime):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    os.utime(str(p), (mtime, mtime))


def snap(d):
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(d)).replace("\\", "/")] = {
                "sha8": hashlib.sha256(p.read_bytes()).hexdigest()[:8],
                "mtime": int(st.st_mtime)}
        else:
            out[str(p.relative_to(d)).replace("\\", "/") + "/"] = "dir"
    return out


def kill_count():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq BCompare.exe"],
                           capture_output=True, text=True, timeout=15.0)
        return sum(1 for ln in r.stdout.splitlines() if "BCompare.exe" in ln)
    except Exception:
        return -1


def trees(base):
    L, R = base / "L", base / "R"
    L.mkdir(parents=True); R.mkdir(parents=True)
    return L, R


def std_pair(L, R):
    now = time.time()
    mkfile(L / "c.txt", "L-VERSION\n", now)
    mkfile(R / "c.txt", "R-VERSION\n", now - 5 * DAY)


def emptydir_case(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    (L / "srcEmpty").mkdir(exist_ok=True)


CASES = [
    ("G1-crit-ts-report", std_pair,
     lambda L, R: ["criteria timestamp:2sec", f'load "{L}" "{R}"', "expand all",
                   'folder-report layout:summary output-to:"%3"']),
    ("G2-crit-ts-mirror", std_pair,
     lambda L, R: ["criteria timestamp:2sec", f'load "{L}" "{R}"', "expand all",
                   "sync mirror:left->right"]),
    ("G3-crit-ts-plain-sync", std_pair,
     lambda L, R: ["criteria timestamp", f'load "{L}" "{R}"', "expand all",
                   "sync update:left->right"]),
    ("G4-createempty-update", emptydir_case,
     lambda L, R: [f'load "{L}" "{R}"', "expand all",
                   "sync create-empty update:left->right"]),
    ("G5-both-flags", emptydir_case,
     lambda L, R: [f'load "{L}" "{R}"', "expand all",
                   "sync visible create-empty update:left->right"]),
    ("G6-half-load-sync", emptydir_case,
     lambda L, R: [f'load "{L}"', "sync update:left->right"]),
    ("G7-dir-abbrev", std_pair,
     lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:lr"]),
]


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81g-syncriesiduals-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m81g-"))
        L, R = trees(base)
        build(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script, "exit": r.exit_code,
               "after": {"L": snap(L), "R": snap(R)},
               "report_bytes": r.report_bytes,
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m81g-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

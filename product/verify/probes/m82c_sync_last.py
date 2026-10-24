#!/usr/bin/env python3
"""M82c: the last four implementation cells for sync.

  K1  kind conflict REVERSED under mirror:lr -- source FILE `c` on L, dest
      DIRECTORY `c` (with a file) on R. m81h H3 measured dir-source/
      file-dest = dest file DELETED, source dir NOT copied. This cell is the
      other orientation: does mirror delete the dest directory, copy the
      source file, both, or neither?
  K2  kind conflict under mirror:rl -- source (R) FILE, dest (L) DIRECTORY
      (direction symmetry of H3/K1).
  K3  orphan dir with FILES *and* an inner EMPTY dir under plain update:lr --
      X5 pinned mirror (innerEmpty skipped); update needs its own cell.
  K4  `sync visible create-empty mirror:left->right` on L{onlyEmpty/} /
      R{roR.txt} -- visible disables create-empty (H1a for update); does the
      deletion still run (X2 for plain mirror)? Expect: roR deleted,
      onlyEmpty NOT created.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m82c_sync_last.py
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


def k1(L, R):
    now = time.time()
    mkfile(L / "c", "C-FILE\n", now - DAY)
    mkfile(R / "c" / "inner.txt", "INNER\n", now - DAY)


def k2(L, R):
    now = time.time()
    mkfile(R / "c", "C-FILE\n", now - DAY)
    mkfile(L / "c" / "inner.txt", "INNER\n", now - DAY)


def k3(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(L / "mixDir" / "f.txt", "F\n", now - DAY)
    (L / "mixDir" / "innerEmpty").mkdir(parents=True, exist_ok=True)


def k4(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    (L / "onlyEmpty").mkdir(exist_ok=True)
    mkfile(R / "roR.txt", "R-ONLY\n", now - DAY)


CASES = [
    ("K1-file-vs-dir-mirror-lr", k1, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                    "sync mirror:left->right"]),
    ("K2-dir-vs-file-mirror-rl", k2, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                    "sync mirror:right->left"]),
    ("K3-mixed-orphan-update", k3, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"]),
    ("K4-visible-ce-mirror", k4, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                               "sync visible create-empty mirror:left->right"]),
]


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m82c-synclast-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m82c-"))
        L, R = base / "L", base / "R"
        L.mkdir(); R.mkdir()
        build(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script, "exit": r.exit_code,
               "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   L: " + json.dumps(rec["after"]["L"]))
        print("   R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m82c-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

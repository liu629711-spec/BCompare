#!/usr/bin/env python3
"""M82b: the three cells the product implementation still needs.

  X1  control: plain `sync mirror:left->right` with a dest-only FILE and NO
      filter -- delete (already many times: A2/S1/H2a; this re-pins the exact
      fixture used below so the batch is internally consistent).
  X2  `sync visible mirror:left->right` on the SAME fixture with NO filter --
      does `visible` by itself suppress the destination deletion? (F4's
      non-deletion was confounded by the filter; H1a proved visible DISABLES
      create-empty, so the flag is not inert.) THE cell deciding whether the
      product's visible flag skips deletions.
  X3  plain mirror + filter matching the dest orphan (*.log orphan under
      `filter "*.log"`) -- filter-matched orphan IS deleted (completes the
      H2a/F4b triangle: filter skips what it does not match).
  X4  plain `sync update:left->right` with a dest-only FOLDER containing a
      file -- update never deletes folders either (m81b B5 pinned update kept
      roRdir; re-pin alongside X5 for the symmetric fixture).
  X5  plain mirror + source-only FOLDER that contains a FILE plus an EMPTY
      subfolder, NO create-empty -- are the files copied but the inner empty
      folder skipped? (H1c/H1d only had an all-empty subtree.)

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m82b_sync_cells.py
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


def pair_base(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)


def x_orphan_file(L, R):
    pair_base(L, R)
    mkfile(R / "roR.txt", "R-ONLY\n", time.time() - DAY)


def x_log_orphan(L, R):
    pair_base(L, R)
    mkfile(R / "gone.log", "R-ONLY-LOG\n", time.time() - DAY)


def x_dest_dir(L, R):
    pair_base(L, R)
    mkfile(R / "roDir" / "inner.txt", "INNER\n", time.time() - DAY)


def x_src_mixed(L, R):
    pair_base(L, R)
    now = time.time()
    mkfile(L / "mixedDir" / "file.txt", "F\n", now - DAY)
    (L / "mixedDir" / "innerEmpty").mkdir(parents=True, exist_ok=True)


CASES = [
    ("X1-plain-mirror", x_orphan_file, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                     "sync mirror:left->right"]),
    ("X2-visible-mirror", x_orphan_file, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                       "sync visible mirror:left->right"]),
    ("X3-filtermatch-mirror", x_log_orphan, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                          'filter "*.log"',
                                                          "sync mirror:left->right"]),
    ("X4-update-keeps-destdir", x_dest_dir, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                          "sync update:left->right"]),
    ("X5-mirror-src-mixed", x_src_mixed, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                       "sync mirror:left->right"]),
]


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m82b-synccells-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m82b-"))
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
    (run_dir / "m82b-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

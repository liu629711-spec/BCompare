#!/usr/bin/env python3
"""M81 sync channel measurement batch (Function 4: folder sync).

Disposable temp trees only. Serial Oracle runs with Job-Object containment.
Public-help claims to pin down with measured filesystem effects:
  - update  "copies newer files and orphans in the direction"
  - mirror  "makes target identical; orphans in the destination are deleted"

Cases (each on a fresh temp tree; exit + resulting trees + file CONTENTS are
the verdict, integer-only where needed):

  A1 update:lr   L{same,newerL,orphanL, olderL(old)}  R{same,olderR(new),
               orphanR}  -> which files land/change/delete on R?
  A2 mirror:lr   same fixture, fresh copy -> expect R == L exactly.
  A3 update:rl   mirror image of A1 in the other direction.
  A4 mirror:all  (public help says all invalid for mirror -> expect 105/106?)
  A5 update:all  (valid? -> copies newer+orphans BOTH directions?)
  A6 same-mtime-different-content + update:lr  (does "newer" fall back to
               size/content when timestamps are equal?)
  A7 sync without load (re-measure S5 from m80: exit 0? error?) -- keep parity.
  A8 mirror with subfolders (recursive effect on nested trees).
  A9 mirror:lr on IDENTICAL trees (no-op? still exit 0?)
  A10 nonexistent target dir for load (re-measure S6: 107) + nonexistent SOURCE.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m81_sync_measure_probe.py
"""
from __future__ import annotations

import hashlib, json, os, pathlib, subprocess, sys, tempfile, time
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

DAY = 24 * 3600


def mkfile(p: pathlib.Path, content: str, mtime: float) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    os.utime(str(p), (mtime, mtime))


def tree_state(d: pathlib.Path) -> dict:
    """Deterministic snapshot: relpath -> (sha8, mtime_bucket)."""
    now = time.time()
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(d)).replace("\\", "/")] = {
                "sha8": hashlib.sha256(p.read_bytes()).hexdigest()[:8],
                "age_h": round((now - st.st_mtime) / 3600, 1),
            }
    return out


def new_trees(base: pathlib.Path):
    L, R = base / "L", base / "R"
    L.mkdir(parents=True); R.mkdir(parents=True)
    return L, R


def build_update_fixture(L, R):
    """same / newer on L / older on L vs newer on R / one-sided orphans."""
    now = time.time()
    mkfile(L / "same.txt",      "IDENTICAL\n",  now - 10 * DAY)
    mkfile(R / "same.txt",      "IDENTICAL\n",  now - 10 * DAY)
    mkfile(L / "newerL.txt",    "L-VERSION\n",  now)            # L newer
    mkfile(R / "newerL.txt",    "R-VERSION\n",  now - 5 * DAY)  # R copy is old
    mkfile(L / "olderL.txt",    "L-OLD\n",      now - 5 * DAY)  # L older
    mkfile(R / "olderL.txt",    "R-NEW\n",      now)            # R newer
    mkfile(L / "orphanL.txt",   "ONLY-L\n",     now - 3 * DAY)
    mkfile(R / "orphanR.txt",   "ONLY-R\n",     now - 3 * DAY)


def kill_bcompare_count() -> int:
    """Return number of BCompare.exe processes still alive (should be 0)."""
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq BCompare.exe"],
                             capture_output=True, text=True, timeout=15.0)
        return sum(1 for ln in out.stdout.splitlines() if "BCompare.exe" in ln)
    except Exception:
        return -1


CASES = []


def add_case(tag, build, script_lines_fn, inspect_sides=("L", "R")):
    CASES.append((tag, build, script_lines_fn, inspect_sides))


# A1: update:left->right on the standard fixture
add_case("A1-update-lr", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:left->right"])
# A2: mirror:left->right on the standard fixture
add_case("A2-mirror-lr", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync mirror:left->right"])
# A3: update:right->left on the standard fixture
add_case("A3-update-rl", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:right->left"])
# A4: mirror:all -- public help says invalid; measure the refuse code
add_case("A4-mirror-all", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync mirror:all"])
# A5: update:all -- valid? bidirectional effect
add_case("A5-update-all", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:all"])
# A6: equal mtimes, different content + update:lr (tie-break probe)
def build_tie(L, R):
    now = time.time()
    mkfile(L / "tie.txt", "L-VERSION\n", now - 2 * DAY)
    mkfile(R / "tie.txt", "R-VERSION\n", now - 2 * DAY)
add_case("A6-tie-update-lr", build_tie,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:left->right"])
# A7: sync without load (re-pin m80 S5)
add_case("A7-no-load", build_update_fixture,
         lambda L, R: ["sync update:left->right"])
# A8: mirror with subfolders
def build_nested(L, R):
    now = time.time()
    mkfile(L / "sub" / "deep.txt", "DEEP-L\n", now)
    mkfile(L / "sub" / "empty-dir-keep.txt", "x\n", now)
    mkfile(R / "sub" / "orphan-deep.txt", "DEEP-R-ONLY\n", now - DAY)
    (R / "emptydir").mkdir(exist_ok=True)
add_case("A8-mirror-nested", build_nested,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync mirror:left->right"])
# A9: mirror on identical trees (no-op?)
def build_identical(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
add_case("A9-mirror-identical", build_identical,
         lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync mirror:left->right"])
# A10: load nonexistent RIGHT (error surface re-pin)
add_case("A10-load-missing-right", build_update_fixture,
         lambda L, R: [f'load "{L}" "{R}-NOPE"', "expand all", "sync update:left->right"],
         inspect_sides=("L",))


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81-sync-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, script_fn, sides in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81-{tag[:4]}-"))
        L, R = new_trees(base)
        build(L, R)
        script = script_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        # folder-sync cases usually have no report line; pass %3 = out anyway
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        state = {"L": tree_state(L), "R": tree_state(R)} if "R" in sides \
            else {"L": tree_state(L)}
        if "R" not in sides:
            state["R"] = "not-inspected(missing-right-case)"
        alive = kill_bcompare_count()
        rec = {"tag": tag, "exit": r.exit_code, "stdout": r.stdout[:500],
               "stderr": r.stderr[:500], "trees": state,
               "residue_alive": alive, "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code} residue_alive={alive}")
        for side, st in state.items():
            if isinstance(st, dict):
                print(f"   {side}: " + json.dumps(st, ensure_ascii=False))
        if r.exit_code == 104:
            raise SystemExit("fatal 104 -- abort batch")

    (run_dir / "m81-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

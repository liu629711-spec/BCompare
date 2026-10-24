#!/usr/bin/env python3
"""M81c: close the residual sync-model questions from m81/m81b.

Measured so far (m81 A1-A10, m81b B1-B9):
  - update:lr copies source-newer + source-orphans; never deletes; never
    touches R-older (A1 olderL stayed R-NEW); COPIES content-equal newer
    timestamps (B2 -- classification is timestamp-based).
  - mirror:lr = update's copies + deletes destination orphans, FILES (A2/S1)
    and NON-EMPTY FOLDERS (B6) recursively; source-only dirs copied whole
    (B4); WITHOUT `expand all` it still recursed into nested orphans (B7).
  - equal timestamps + different content: NEITHER update (A6) NOR mirror
    (B1) copies -- ties are "same"?? re-pin with size differences (C6/C7).
  - refuse surface: bare `sync`, bad mode, missing direction, trailing junk,
    `sync visible` without a mode, and mode-after-direction = all 106
    (B8-1..8 EXCEPT B8-7 `sync visible update:left->right` = exit 0!
     -> `visible` is a legal PRE-mode flag; no-op here because trees were
     already identical). Re-pin visible in C8.
  - `criteria:size-only` is 106 (colon form wrong; the folder channel uses
    space syntax `criteria <tokens>` -- u4).

This batch:
  C1  criteria obedience: `criteria size` (content-differs-equal-size, L
      newer stamp) and `criteria timestamp:2sec` control; then update:lr.
  C2  timestamp preservation under update (source 72h orphan + 0h newer).
  C3  same fixture under mirror.
  C4  empty source, non-empty dest: mirror deletes ALL dest files?
  C5  same fixture under update (keeps dest).
  C6  tie stamps + DIFFERENT sizes under mirror (does "different" use size
      when timestamps are equal?).
  C7  same fixture under update.
  C8  `sync visible mirror:left->right` vs `sync mirror:left->right` on a
      tree with one orphan -- does visible change the effect (it is the GUI
      "visible selection only" flag)?

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81c_sync_last_gaps.py
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


def tree_state(d):
    now = time.time()
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(d)).replace("\\", "/")] = {
                "sha8": hashlib.sha256(p.read_bytes()).hexdigest()[:8],
                "age_h": round((now - st.st_mtime) / 3600, 1),
            }
        else:
            out[str(p.relative_to(d)).replace("\\", "/") + "/"] = "dir"
    return out


def kill_count():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq BCompare.exe"],
                             capture_output=True, text=True, timeout=15.0)
        return sum(1 for ln in out.stdout.splitlines() if "BCompare.exe" in ln)
    except Exception:
        return -1


def trees(base):
    L, R = base / "L", base / "R"
    L.mkdir(parents=True); R.mkdir(parents=True)
    return L, R


CASES = []
def add(tag, build, lines_fn):
    CASES.append((tag, build, lines_fn))


# C1: criteria-size vs criteria-timestamp control on L-newer equal-size diff-content
def c1(L, R):
    now = time.time()
    mkfile(L / "c.txt", "L-VERSION\n", now)              # newer stamp, 10 bytes
    mkfile(R / "c.txt", "R-VERSION\n", now - 5 * DAY)    # older stamp, 10 bytes
for cform in ["criteria size", "criteria timestamp:2sec"]:
    add(f"C1-{cform.replace(' ', '_')}", c1,
        (lambda cf: lambda L, R: [cf, f'load "{L}" "{R}"', "expand all",
                                  "sync update:left->right"])(cform))

# C2/C3: timestamp preservation (distinct stamps)
def c23(L, R):
    now = time.time()
    mkfile(L / "orphanL-stamp3d.txt", "ONLY-L\n", now - 3 * DAY)
    mkfile(L / "newerL-stamp0.txt",  "L-NEW\n",  now)
    mkfile(R / "newerL-stamp0.txt",  "R-OLD\n",  now - 5 * DAY)
add("C2-stamps-update", c23, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync update:left->right"])
add("C3-stamps-mirror", c23, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync mirror:left->right"])

# C4/C5: empty source vs non-empty dest
def c45(L, R):
    now = time.time()
    mkfile(R / "d1.txt", "D1\n", now - DAY)
    mkfile(R / "d2.txt", "D2\n", now - DAY)
add("C4-empty-source-mirror", c45, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync mirror:left->right"])
add("C5-empty-source-update", c45, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"])

# C6/C7: tie stamps + different sizes
def c67(L, R):
    now = time.time()
    mkfile(L / "t.txt", "AAAAAAAAAAAA\n", now - 2 * DAY)  # 13 bytes
    mkfile(R / "t.txt", "BBBBBB\n",        now - 2 * DAY)  # 7 bytes, SAME stamp
add("C6-tie-diffsize-mirror", c67, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync mirror:left->right"])
add("C7-tie-diffsize-update", c67, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"])

# C8: visible flag on a tree WITH an effect
def c8(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(L / "orphanL.txt", "ONLY-L\n", now - DAY)
add("C8-visible-mirror", c8, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync visible mirror:left->right"])
add("C8b-plain-mirror", c8, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                          "sync mirror:left->right"])


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81c-synclast-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81c-{tag[:3]}-"))
        L, R = trees(base)
        build(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "op_line": script[-1], "pre_lines": script[:-1],
               "exit": r.exit_code,
               "trees": {"L": tree_state(L), "R": tree_state(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   R: " + json.dumps(rec["trees"]["R"], ensure_ascii=False))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m81c-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

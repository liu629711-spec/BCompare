#!/usr/bin/env python3
"""M81b: close the sync model gaps left by m81 (A1-A10).

Open questions, each one fresh temp tree, serial:

  B1  mirror:lr on the TIE fixture (equal mtimes, different content) -- does
      mirror copy "different" files (public help says yes) while update didn't
      (A6)? THE key discriminator between update and mirror beyond deletion.
  B2  identical content, L mtime newer, update:lr -- is it "same" (untouched)
      or "left newer" (copied, overwriting R's older mtime)? Pins whether
      comparison is timestamp-only or content-aware.
  B3  source-only FOLDER with files, update:lr -- copied recursively?
  B4  source-only folder, mirror:lr -- same (vs B3)?
  B5  dest-only FOLDER with files, update:lr (kept?) / mirror:lr (deleted?)
      -- folder-level orphan deletion (A8 already deleted an EMPTY dest-only
      dir under mirror; does mirror delete a NON-empty dest-only dir?).
  B6  mirror:lr nested orphan WITHOUT `expand all` -- does sync use the
      expansion state or always recurse? (load+expand vs load only).
  B7  refuse surface: `sync` bare, `sync bad:lr`, `sync update`,
      `sync update:left`, `sync update:left->right extra`, `sync visible`
      (no mode), `sync update:left->right visible` -- exit codes each.
  B8  dest file newer under mirror:lr, EQUAL-size contents (the "different"
      with dest-newer combo) -- covered by A2 but re-pin cleanly with
      a pure tie-content-differs-but-source-newer case.
  B9  criteria interaction: `criteria:size-only` then update:lr on two files
      same size different content, L newer by mtime only -- copied or not?

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m81b_sync_gaps_probe.py
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


def kill_bcompare_count() -> int:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq BCompare.exe"],
                             capture_output=True, text=True, timeout=15.0)
        return sum(1 for ln in out.stdout.splitlines() if "BCompare.exe" in ln)
    except Exception:
        return -1


CASES = []


def add(tag, build, script_fn):
    CASES.append((tag, build, script_fn))


def trees(base):
    L, R = base / "L", base / "R"
    L.mkdir(parents=True); R.mkdir(parents=True)
    return L, R


# B1: mirror on tie (equal mtime, different content, equal size)
def b1(L, R):
    now = time.time()
    mkfile(L / "tie.txt", "L-VERSION\n", now - 2 * DAY)
    mkfile(R / "tie.txt", "R-VERSION\n", now - 2 * DAY)
add("B1-mirror-tie", b1, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                       "sync mirror:left->right"])


# B2: identical content, L newer mtime, update:lr
def b2(L, R):
    now = time.time()
    mkfile(L / "same.txt", "IDENTICAL\n", now)            # L newer stamp
    mkfile(R / "same.txt", "IDENTICAL\n", now - 5 * DAY)  # R same content, older stamp
add("B2-samecontent-newerL-update", b2, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                      "sync update:left->right"])


# B3/B4: source-only folder with files
def b34(L, R):
    now = time.time()
    mkfile(L / "onlydir" / "in1.txt", "IN-1\n", now - DAY)
    mkfile(L / "onlydir" / "sub2" / "deep.txt", "DEEP\n", now - DAY)
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
add("B3-onlydir-update", b34, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                            "sync update:left->right"])
add("B4-onlydir-mirror", b34, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                             "sync mirror:left->right"])


# B5: dest-only non-empty folder
def b5(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(R / "roRdir" / "x.txt", "X\n", now - DAY)
add("B5-destdir-update", b5, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync update:left->right"])
add("B6-destdir-mirror", b5, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync mirror:left->right"])


# B7: nested orphan deletion WITHOUT expand
def b7(L, R):
    now = time.time()
    mkfile(L / "sub" / "keep.txt", "K\n", now - DAY)
    mkfile(R / "sub" / "keep.txt", "K\n", now - DAY)
    mkfile(R / "sub" / "roR.txt", "R-ONLY-NESTED\n", now - DAY)
add("B7-no-expand-mirror", b7, lambda L, R: [f'load "{L}" "{R}"',
                                              "sync mirror:left->right"])


# B8: refuse surface (each exit only; tree untouched = L has one file)
def b8(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
for n, line in enumerate([
        "sync",
        "sync bad:lr",
        "sync update",
        "sync update:left",
        "sync update:left->right extra",
        "sync visible",
        "sync visible update:left->right",
        "sync update:left->right visible",
], 1):
    add(f"B8-{n}", b8,
        (lambda l: (lambda L, R: [f'load "{L}" "{R}"', "expand all", l]))(line))


# B9: criteria:size-only + update:lr on mtime-newer equal-size different-content
def b9(L, R):
    now = time.time()
    mkfile(L / "c.txt", "L-VERSION\n", now)             # same 10 bytes as R? "L-VERSION\n"=10
    mkfile(R / "c.txt", "R-VERSION\n", now - 5 * DAY)   # 10 bytes, older stamp
add("B9-sizeonly-update", b9, lambda L, R: ["criteria:size-only",
                                            f'load "{L}" "{R}"', "expand all",
                                            "sync update:left->right"])


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81b-syncgaps-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, script_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81b-{tag[:3]}-"))
        L, R = trees(base)
        build(L, R)
        script = script_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs".replace(":", "-")
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out".replace(":", "-")
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script[2:] if len(script) > 2 else script,
               "exit": r.exit_code, "trees": {"L": tree_state(L), "R": tree_state(R)},
               "residue_alive": kill_bcompare_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   R: " + json.dumps(rec["trees"]["R"], ensure_ascii=False))
        if r.exit_code == 104:
            raise SystemExit("fatal 104 -- abort")

    (run_dir / "m81b-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

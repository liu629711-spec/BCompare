#!/usr/bin/env python3
"""M81h: four implementation-blocking cells from m81f/m81g.

  H1  flag order: `sync create-empty visible update:...` vs G5's
      `sync visible create-empty update:...` (which did NOT copy the empty
      source dir) -- is only ONE flag slot honored, or does `visible` first
      disable `create-empty`? Also H1c bare `sync create-empty update` with
      a source dir containing ONLY an empty subdir (does create-empty apply
      to nested empties in orphan-dir copies?).
  H2  filter scoping control: no-filter mirror deletes R-only hidden.log
      (F4b kept it under filter "*.txt"); plus H2b update under filter where
      an L-only file is .log -- copied or skipped? (filter scopes copies too?)
  H3  kind conflict (dir on one side, file on the other, same name) under
      mirror:lr and update:lr -- copied? deleted? refused? This decides
      whether the product walks these rows at all.
  H4  criteria timestamp tolerance under sync default is already pinned
      (E1/E2: delta 2s same, 3s newer); here pin the SAME tolerance applies
      to MIRROR's "different" classification: delta 2s + same size +
      different content -> mirror:lr copies or not? (Diff needs unequal
      timestamps >2s when sizes are equal?)

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81h_sync_blocking.py
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


CASES = []
def add(tag, build, lines_fn):
    CASES.append((tag, build, lines_fn))


# H1a: create-empty visible (order swapped vs G5)
def h1(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    (L / "srcEmpty").mkdir(exist_ok=True)
add("H1a-ce-visible", h1, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                         "sync create-empty visible update:left->right"])
add("H1b-visible-ce", h1, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                        "sync visible create-empty update:left->right"])
# H1c: create-empty with a nested empty dir inside a source-only folder
def h1c(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    (L / "orphanDir" / "innerEmpty").mkdir(parents=True, exist_ok=True)
add("H1c-ce-nested-empty", h1c, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync create-empty update:left->right"])
# H1d: plain update with the same nested-empty orphan dir (baseline: copied
# without innerEmpty, or the whole dir skipped?)
add("H1d-plain-nested-empty", h1c, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"])

# H2a: NO filter, mirror deletes the .log orphan (control for F4b)
def h2(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(R / "hidden.log", "HIDDEN\n", now - DAY)
add("H2a-nofilter-mirror-log", h2, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync mirror:left->right"])
# H2b: filter "*.txt", source orphan is a .log -> copied? (filter scopes
# update copies too?)
def h2b(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(L / "orphan.log", "ONLY-L-LOG\n", now - DAY)
add("H2b-filter-update-log", h2b, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                'filter "*.txt"',
                                                "sync update:left->right"])

# H3: kind conflict, dir on L vs file on R, name "c"
def h3(L, R):
    now = time.time()
    (L / "c").mkdir(exist_ok=True)
    mkfile(L / "c" / "inner.txt", "INNER\n", now - DAY)
    mkfile(R / "c", "C-FILE\n", now - DAY)
add("H3-kindconflict-mirror", h3, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync mirror:left->right"])
add("H3b-kindconflict-update", h3, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"])

# H4: delta 2s EXACT + same size + different content under mirror
def h4(L, R):
    now = time.time()
    mkfile(L / "p.txt", "L-NEW2S\n", now)
    mkfile(R / "p.txt", "R-OLD2S\n", now - 2)
add("H4-2s-mirror", h4, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                      "sync mirror:left->right"])
# H4b: delta 3s + same size + different content under mirror (LeftNewer +
# content diff: copies AND overwrites?)
def h4b(L, R):
    now = time.time()
    mkfile(L / "p.txt", "L-NEW3S\n", now)
    mkfile(R / "p.txt", "R-OLD3S\n", now - 3)
add("H4b-3s-mirror", h4b, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                        "sync mirror:left->right"])


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81h-syncblocking-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m81h-"))
        L, R = trees(base)
        build(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script[-1], "exit": r.exit_code,
               "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   L: " + json.dumps(rec["after"]["L"]))
        print("   R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m81h-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""M81f: the sync flag surface -- visible / create-empty / order.

  F1  `sync create-empty update:left->right` on L{a.txt,dirdel/} / R{a.txt}
      where L has NO new empty dirs but R has a dest-only empty dir: does
      create-empty make any measurable difference vs plain update (G6 re-run)
      or vs mirror?
  F2  order swap: `sync update:left->right visible` vs
      `sync update visible:left->right` vs `sync update:left->right visible`
      -- which orders are exit 0 (accepted)?
  F3  bare `sync create-empty update:left->right` where dest has an empty dir
      and SOURCE has an empty dir -- after mirror:lr WITH create-empty vs
      WITHOUT: is the source empty dir created in dest only with the flag?
      (help says create-empty is about folders sync; measure the delta.)
  F4  `sync visible mirror:left->right` where dest has files NOT shown due to
      filter: `filter "*.txt"` hides .log files -- does visible skip them?
      (filter only affects reports; sync ignores -- re-confirm the flag is
      inert in scripts.)
  F5  double sync: update:lr then update:lr again -- idempotent, exit 0?
  F6  `sync mirror:right->left` -- DELETION on L side confirmed already (E3);
      here add: L has a dest-newer PAIR -- mirror keeps L's newer copy (mirror
      direction right->left: source=R; a pair where L newer -> NOT copied,
      NOT deleted; re-pin in the other direction).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81f_sync_flags.py
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


# F1/F3: empty dirs
def f13(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(L / "L-empty-src.txt", "s\n", now - DAY)  # avoid truly-empty; see F3b
    (L / "emptyOnL").mkdir(exist_ok=True)            # source-only EMPTY dir
    (R / "emptyOnR").mkdir(exist_ok=True)            # dest-only EMPTY dir
add("F3-createempty-mirror", f13, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync create-empty mirror:left->right"])
add("F3b-plain-mirror", f13, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           "sync mirror:left->right"])

# F2: flag orders (effect identical if accepted; the exit code is the point)
for i, op in enumerate([
        "sync update:left->right visible",
        "sync update visible:left->right",
        "sync visible:create-empty mirror:left->right",
        "sync create-empty:yes update:left->right",
], 1):
    def f2(L, R):
        now = time.time()
        mkfile(L / "o.txt", "O\n", now)
        mkfile(R / "o.txt", "r\n", now - DAY)
    add(f"F2-{i}", f2, (lambda o: lambda L, R: [f'load "{L}" "{R}"', "expand all", o])(op))

# F4: filter + visible mirror
def f4(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now - DAY)
    mkfile(R / "a.txt", "A\n", now - DAY)
    mkfile(R / "hidden.log", "HIDDEN\n", now - DAY)   # dest orphan, filtered out
add("F4-visible-filter", f4, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                           'filter "*.txt"',
                                           "sync visible mirror:left->right"])
add("F4b-plain-filter-mirror", f4, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                 'filter "*.txt"',
                                                 "sync mirror:left->right"])

# F5: double update
def f5(L, R):
    now = time.time()
    mkfile(L / "d.txt", "D\n", now)
add("F5-double-update", f5, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                          "sync update:left->right",
                                          "sync update:left->right"])

# F6: mirror:rl with a pair newer on L (the DESTINATION side in this direction)
def f6(L, R):
    now = time.time()
    mkfile(L / "k.txt", "L-NEWER-KEEP\n", now)        # dest newer -> must survive
    mkfile(R / "k.txt", "R-OLDER\n", now - DAY)
    mkfile(R / "orphanR.txt", "R-ONLY\n", now - DAY)  # source orphan -> copies to L
add("F6-mirror-rl-destnewer", f6, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync mirror:right->left"])


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81f-syncflags-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81f-{tag[:2]}-"))
        L, R = trees(base)
        build(L, R)
        before = {"L": snap(L), "R": snap(R)}
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script, "exit": r.exit_code,
               "before": before, "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   L: " + json.dumps(rec["after"]["L"]))
        print("   R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m81f-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

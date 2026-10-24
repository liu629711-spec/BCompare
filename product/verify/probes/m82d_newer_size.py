#!/usr/bin/env python3
"""M82d: the last classification gap -- source-newer AND size-differs.

The engine classifies such a pair `diff` (a content criterion differs), but
BC's sync help says update copies "newer" files. Which classification wins?

  N1  update:lr  L "AAAAAA\n"(6b, now)  R "B\n"(2b, 5d old)   -> copied?
  N2  update:rl  same fixture flipped (source R now but SMALLER + newer) -> copied?
  N3  mirror:lr  same as N1 (mirror copies diff anyway -- expected copied)

If N1 copies: BC's update treats LeftNewer even with size differing -> the
product maps newer-ness directly, not engine Diff. If not: engine statuses
(exact) drive sync. Either way one measured rule, no guessing.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m82d_newer_size.py
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
                "size": st.st_size, "mtime": int(st.st_mtime)}
    return out


def kill_count():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq BCompare.exe"],
                           capture_output=True, text=True, timeout=15.0)
        return sum(1 for ln in r.stdout.splitlines() if "BCompare.exe" in ln)
    except Exception:
        return -1


def fixture(L, R):
    now = time.time()
    mkfile(L / "n.txt", "AAAAAA\n", now)        # source newer AND bigger
    mkfile(R / "n.txt", "B\n", now - 5 * DAY)


CASES = [
    ("N1-newer-size-update-lr", lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync update:left->right"]),
    ("N2-newer-size-update-rl", lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync update:right->left"]),
    ("N3-newer-size-mirror-lr", lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync mirror:left->right"]),
]


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m82d-newersize-%Y%m%dT%H%M%SZ"))
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    results = []
    for tag, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m82d-"))
        L, R = base / "L", base / "R"
        L.mkdir(); R.mkdir()
        fixture(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out" if (run_dir / "reports").mkdir(exist_ok=True) is None else run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "exit": r.exit_code, "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count()}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   L: " + json.dumps(rec["after"]["L"]))
        print("   R: " + json.dumps(rec["after"]["R"]))
    (run_dir / "m82d-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

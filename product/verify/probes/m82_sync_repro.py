#!/usr/bin/env python3
"""M82: reproduce the two contradictory cells before freezing the sync model.

Contradiction 1: a SINGLE L-newer pair (same size, different content, L 5d
newer) was COPIED by `sync update:left->right` in m81 A1 (multi-file fixture)
and m81c C2, but NOT copied in m81c C1-control-plain (single-pair fixture).
Hypotheses: (a) BC background-scan race (status.rs doc: hollow folders until
the scan completes) -- a script that syncs immediately after load may miss
rows; (b) multi-row vs single-row fixtures behave differently; (c) transient.

Contradiction 2: m81c `criteria timestamp:2sec` + update = 105, but m81g G2
same criteria + mirror = 0 and G3 `criteria timestamp` + update = 0.
Which token/exact-position triggers 105? Re-run both orders x2.

Cells:
  R1a..c  single pair + update:lr  (x3, fresh temp each)
  R2a..b  multi-pair A1 fixture + update:lr (x2)
  R3a..b  `criteria timestamp:2sec` + update:lr (x2)
  R4a..b  `criteria timestamp:2sec` + mirror:lr (x2)
  R5      criteria size + update on A1 fixture (re-pin C1-criteria_size)

If R1 copies sometimes and not others, race confirmed -> record as residual
unknown and the product keeps deterministic semantics (scan-complete model).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m82_sync_repro.py
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


def single_pair(L, R):
    now = time.time()
    mkfile(L / "c.txt", "L-VERSION\n", now)
    mkfile(R / "c.txt", "R-VERSION\n", now - 5 * DAY)


def a1_fixture(L, R):
    now = time.time()
    mkfile(L / "same.txt",    "IDENTICAL\n", now - 10 * DAY)
    mkfile(R / "same.txt",    "IDENTICAL\n", now - 10 * DAY)
    mkfile(L / "newerL.txt",  "L-VERSION\n", now)
    mkfile(R / "newerL.txt",  "R-VERSION\n", now - 5 * DAY)
    mkfile(L / "olderL.txt",  "L-OLD\n",     now - 5 * DAY)
    mkfile(R / "olderL.txt",  "R-NEW\n",     now)
    mkfile(L / "orphanL.txt", "ONLY-L\n",    now - 3 * DAY)
    mkfile(R / "orphanR.txt", "ONLY-R\n",    now - 3 * DAY)


CASES = [
    ("R1a-single-update", single_pair, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                     "sync update:left->right"]),
    ("R1b-single-update", single_pair, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                     "sync update:left->right"]),
    ("R1c-single-update", single_pair, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                     "sync update:left->right"]),
    ("R2a-a1-update", a1_fixture, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync update:left->right"]),
    ("R2b-a1-update", a1_fixture, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync update:left->right"]),
    ("R3a-critts-update", single_pair, lambda L, R: ["criteria timestamp:2sec",
                                                     f'load "{L}" "{R}"', "expand all",
                                                     "sync update:left->right"]),
    ("R3b-critts-update", single_pair, lambda L, R: ["criteria timestamp:2sec",
                                                     f'load "{L}" "{R}"', "expand all",
                                                     "sync update:left->right"]),
    ("R4a-critts-mirror", single_pair, lambda L, R: ["criteria timestamp:2sec",
                                                     f'load "{L}" "{R}"', "expand all",
                                                     "sync mirror:left->right"]),
    ("R4b-critts-mirror", single_pair, lambda L, R: ["criteria timestamp:2sec",
                                                     f'load "{L}" "{R}"', "expand all",
                                                     "sync mirror:left->right"]),
    ("R5-sizecrit-a1", a1_fixture, lambda L, R: ["criteria size",
                                                 f'load "{L}" "{R}"', "expand all",
                                                 "sync update:left->right"]),
]


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m82-syncrepro-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix="m82-"))
        L, R = base / "L", base / "R"
        L.mkdir(); R.mkdir()
        build(L, R)
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script[-1], "criteria": script[0] if script[0].startswith("criteria") else None,
               "exit": r.exit_code, "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        copied = "c.txt" in rec["after"]["R"] or "newerL.txt" in rec["after"]["R"]
        print(f"{tag}: exit={r.exit_code}")
        print("   R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m82-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

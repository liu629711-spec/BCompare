#!/usr/bin/env python3
"""M81e: pin the two last sync-model edges.

  E1  tolerance boundary: update:lr with lag 2s exactly (D3: 1s=same, 3s=newer;
      is 2s same or newer? BC's timestamp comparison default tolerance is
      "2 seconds" -- if 2s is SAME, tolerance is <=2s; if NEWER, boundary is
      <2s. This decides the product's constant).
  E2  same pair under mirror:lr at lag 2s (mirror follows the same class).
  E3  mirror:right->left deletes LEFT-side orphans (target=L) -- orphanL.txt
      on L must vanish; orphanR must copy to L. (mirror deletion is always
      DESTINATION-side, re-pinned in the opposite direction.)
  E4  criteria size + mirror on tie-same-size different-content: still skip?
      (criteria obeyed under mirror too, not just update?)
  E5  update:all bidirectional with BOTH orphans + one newer-on-L + one
      newer-on-R (m81 A5 re-pin with per-file stamps so each copy is
      attributable).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81e_sync_edges.py
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
def add(tag, build, lines_fn, pre=None):
    CASES.append((tag, build, lines_fn, pre or []))


# E1/E2: lag exactly 2 seconds
def e12(L, R):
    now = time.time()
    mkfile(L / "p.txt", "L-NEW\n", now)
    mkfile(R / "p.txt", "R-OLD\n", now - 2)
add("E1-lag2s-update", e12, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                          "sync update:left->right"])
add("E2-lag2s-mirror", e12, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                          "sync mirror:left->right"])

# E3: mirror:right->left with orphans on BOTH sides
def e3(L, R):
    now = time.time()
    mkfile(L / "orphanL.txt", "ONLY-L\n", now - DAY)
    mkfile(R / "orphanR.txt", "ONLY-R\n", now - DAY)
    mkfile(L / "same.txt", "S\n", now - DAY)
    mkfile(R / "same.txt", "S\n", now - DAY)
add("E3-mirror-rl-orphans", e3, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync mirror:right->left"])

# E4: criteria size + mirror, tie same-size different content
def e4(L, R):
    now = time.time()
    mkfile(L / "q.txt", "L-SAME-LEN\n", now - 2 * DAY)
    mkfile(R / "q.txt", "R-SAME-LEN\n", now - 2 * DAY)
add("E4-sizecriteria-mirror", e4, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync mirror:left->right"],
    pre=["criteria size"])

# E5: update:all full grid (per-file attributable stamps)
def e5(L, R):
    now = time.time()
    mkfile(L / "newerL.txt", "L-WINS\n", now)              # L newer
    mkfile(R / "newerL.txt", "R-LOSES\n", now - DAY)
    mkfile(L / "newerR.txt", "L-LOSES\n", now - DAY)       # R newer
    mkfile(R / "newerR.txt", "R-WINS\n", now)
    mkfile(L / "orphanL.txt", "ONLY-L\n", now - 3 * DAY)
    mkfile(R / "orphanR.txt", "ONLY-R\n", now - 3 * DAY)
add("E5-update-all-grid", e5, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                            "sync update:all"])


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81e-syncedges-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn, pre in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81e-{tag[:2]}-"))
        L, R = trees(base)
        build(L, R)
        before = {"L": snap(L), "R": snap(R)}
        script = pre + lines_fn(L, R)
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
    (run_dir / "m81e-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""M81d: final discriminators for the sync model.

Model so far (m81/m81b/m81c, all exit 0 unless noted):
  update:DIR  copies source-newer pairs + source orphans (recursive dirs);
              NEVER touches tie-pairs or dest-newer pairs; NEVER deletes.
  mirror:DIR  = update's copies + copies TIE different pairs in the chosen
              direction (C6: tie+diff-size -> source wins; B1: tie+same-size
              -> judged same) + deletes destination orphans (files AND
              non-empty folders; empty source wipes the destination).
              Did NOT overwrite a dest-newer pair (A2) -- RE-PIN here (D2).
  criteria    space syntax; `criteria size` makes equal-size pairs "same"
              (C1: newer stamp ignored) -- sync OBEYS criteria.
  refuse: all malformed sync forms 106; `visible` is a legal flag BEFORE the
              mode (B8-7/C8) with no measured effect.
  no load     -> sync silently no-ops exit 0 (A7/S4).

Open cells:
  D1  tie+diff-size under mirror:RIGHT->LEFT -- dest-newer side (R) wins on L?
  D2  dest-newer pair alone under mirror:lr -- R really keeps its newer copy?
  D3  timestamp tolerance: L 1s newer / 3s newer (equal size) -- copied?
      (pins whether "newer" uses a 2-sec-style tolerance; if 1s is judged
      same but 3s copies, tolerance ~2s confirmed.)
  D4  half-load: only `load:left` then sync update:left->right -- exit code,
      effect?
  D5  update:lr with source-newer AND same content (B2 said copied with
      stamp preserved) -- confirm the copied file's mtime EQUALS the source's
      (re-read both stat stamps in the same run).
  D6  mirror:lr tie+diff-size where L is SMALLER (C6 had L bigger) -- source
      still wins? (direction-only, not newer-based).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m81d_sync_final_probe.py
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
                "size": st.st_size,
                "mtime": int(st.st_mtime),
            }
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


# D1: tie + different sizes, mirror RIGHT->LEFT (R source wins on L?)
def d1(L, R):
    now = time.time()
    mkfile(L / "t.txt", "L-BIGGER-13\n", now - 2 * DAY)   # 12 bytes
    mkfile(R / "t.txt", "R-7\n",         now - 2 * DAY)   # 4 bytes
add("D1-tie-mirror-rl", d1, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                          "sync mirror:right->left"])

# D2: dest-newer pair alone under mirror:lr (re-pin A2)
def d2(L, R):
    now = time.time()
    mkfile(L / "x.txt", "L-OLD\n", now - 10 * DAY)
    mkfile(R / "x.txt", "R-NEW\n", now)
add("D2-destnewer-mirror-lr", d2, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                "sync mirror:left->right"])

# D3: tolerance ladder (equal size, content differs)
for delta in (1, 3, 10):
    def build(L, R, delta=delta):
        now = time.time()
        mkfile(L / "e.txt", "NEWER\n", now)
        mkfile(R / "e.txt", "OLDER\n", now - delta)
    add(f"D3-lag{delta}s", build,
        lambda L, R: [f'load "{L}" "{R}"', "expand all", "sync update:left->right"])

# D4: half-load (left only)
def d4(L, R):
    now = time.time()
    mkfile(L / "a.txt", "A\n", now)
add("D4-half-load", d4, lambda L, R: [f'load:left "{L}"', "expand all",
                                      "sync update:left->right"])

# D5: same-content source-newer copy preserves mtime exactly
def d5(L, R):
    now = time.time()
    mkfile(L / "s.txt", "IDENT\n", now - 7 * 60)     # 7 min ago
    mkfile(R / "s.txt", "IDENT\n", now - 4 * DAY)    # same content, older
add("D5-identcontent-copy", d5, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                              "sync update:left->right"])

# D6: tie + L smaller, mirror:lr (source-wins regardless of size direction?)
def d6(L, R):
    now = time.time()
    mkfile(L / "t.txt", "L-4\n",  now - 2 * DAY)     # 4 bytes
    mkfile(R / "t.txt", "R-BIGGER-13\n", now - 2 * DAY)  # 12 bytes
add("D6-tie-lsmaller-mirror-lr", d6, lambda L, R: [f'load "{L}" "{R}"', "expand all",
                                                   "sync mirror:left->right"])


def main():
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m81d-syncfinal-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, build, lines_fn in CASES:
        base = pathlib.Path(tempfile.mkdtemp(prefix=f"m81d-{tag[:2]}-"))
        L, R = trees(base)
        build(L, R)
        before = {"L": snap(L), "R": snap(R)}
        script = lines_fn(L, R)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, script)
        out = run_dir / "reports" / f"{tag}.out"
        r = orc.run(inst.oracle_path, sp, str(L), str(R), str(out),
                    timeout=120.0, script_text="\r\n".join(script))
        rec = {"tag": tag, "script": script[-1], "exit": r.exit_code,
               "before": before, "after": {"L": snap(L), "R": snap(R)},
               "residue_alive": kill_count(), "tmp": str(base)}
        results.append(rec)
        print(f"{tag}: exit={r.exit_code}")
        print("   after L: " + json.dumps(rec["after"]["L"]))
        print("   after R: " + json.dumps(rec["after"]["R"]))
        if r.exit_code == 104:
            raise SystemExit("fatal 104")
    (run_dir / "m81d-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

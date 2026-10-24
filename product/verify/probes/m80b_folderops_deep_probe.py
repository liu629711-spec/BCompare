#!/usr/bin/env python3
"""M80b deep-dive folder ops probes (Function 4: folder sync/copy).

Disposable temp trees only. Serial Oracle runs with Job-Object containment.
Key questions:

  S1  mirror deletes-orphan: does `sync mirror:left->right` DELETE an orphan on
      R? Create L{a.txt}, R{a.txt,orphan-R.txt} -> after sync, is orphan-R gone?

  S2  update vs mirror: newer/older/different behavior under update:lr vs mirror:lr.

  S3  select-orphan copy: after `select right.orphan.files`, does `copy left->right`
      execute (selection-driven op)?

  S4  visible-flag: does the `visible` flag change exit/report when no load yet?

  S5  create-empty: does `create-empty` before `load` affect which folders appear?

  S6  error-missing-folder: sync to a non-existent parent path -> exit code & text.

  S7  delete-recyclebin: does `delete right recyclebin` exist and change outcome?

  S8  report-labels-sync: how does folder-report summary labels look post-sync?

All fixtures written into run-specific subdirectories; reports archived with sidecar
summary + golden.txt copies of first 50 lines per report. Residue check for BCompare.exe
after each run.
"""
from __future__ import annotations

import hashlib, json, pathlib, subprocess, sys, tempfile, time
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def write_tree(base: pathlib.Path, structure: dict) -> None:
    """Write a tree: {name: None|children}. Files have None, folders have dicts."""
    for name, child in structure.items():
        p = base / name
        if child is None:  # file
            p.write_text(name + "\n", encoding="utf-8")
        else:  # folder
            p.mkdir(exist_ok=True)
            write_tree(p, child)


def tree_list(d: pathlib.Path) -> list[str]:
    items = []
    for p in d.rglob("*"):
        rel = p.relative_to(d)
        items.append(str(rel).replace("\\", "/"))
    return sorted(items)


def kill_bcompare() -> int:
    """Kill any stray BCompare.exe and count."""
    try:
        out = subprocess.run(
            ["taskkill", "/F", "/IM", "BCompare.exe"],
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        return 1 if "no process" in out.stdout.lower() or out.returncode != 0 else 0
    except Exception:
        return -1


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)

    now = datetime.now(timezone.utc).strftime("m80b-folderops-%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m80b-{now}"
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []

    # --- S1: mirror deletes-orphan ---
    print("S1 mirror deletes-orphan...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S1-"))
    L, R = tmpdir / "L", tmpdir / "R"
    L.mkdir(); R.mkdir()
    write_tree(L, {"a.txt": None, "newer-L.txt": None})
    write_tree(R, {"a.txt": None, "orphan-R.txt": None})  # older content
    (R / "orphan-R.txt").write_text("old-orphan\n", encoding="utf-8")
    script_path = run_dir / "scripts" / "S1.bcs"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script = [
        f'load "{str(L)}" "{str(R)}"',
        "expand all",
        "sync mirror:left->right",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S1.out"
    r = orc.run(inst.oracle_path, script_path, str(L), str(R), str(out), timeout=120.0, script_text="\r\n".join(script))
    after_L = tree_list(L); after_R = tree_list(R)
    residue_before = kill_bcompare()
    rec = {
        "tag": "S1-mirror-deletes-orphan",
        "tmpdir": str(tmpdir),
        "before_R": ["a.txt","orphan-R.txt"],
        "after_L": after_L,
        "after_R": after_R,
        "exit": r.exit_code,
        "report_exists": r.report_exists,
        "residue_killed": residue_before,
    }
    # Check if orphan-R still exists
    rec["orphan_R_deleted"] = (not (R / "orphan-R.txt").exists())
    results.append(rec)
    print(f"  exit={r.exit_code}, orphan_R_deleted={rec['orphan_R_deleted']}, residue_kill={residue_before}")

    # --- S2: update vs mirror (newer/older) ---
    print("S2 update vs mirror...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S2-"))
    L2, R2 = tmpdir / "L", tmpdir / "R"
    L2.mkdir(); R2.mkdir()
    write_tree(L2, {"newer-L.txt": None, "older-L.txt": None, "same.txt": None})
    write_tree(R2, {"older-R.txt": None, "same.txt": None})
    (L2 / "newer-L.txt").write_text("newer-left\n", encoding="utf-8")
    (L2 / "older-L.txt").write_text("old-content\n", encoding="utf-8")
    (R2 / "older-R.txt").write_text("newer-right\n", encoding="utf-8")
    (L2 / "same.txt").write_text("identical\n", encoding="utf-8")
    (R2 / "same.txt").write_text("identical\n", encoding="utf-8")
    script_path = run_dir / "scripts" / "S2.bcs"
    script = [
        f'load "{str(L2)}" "{str(R2)}"',
        "expand all",
        "sync update:left->right",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S2.out"
    r = orc.run(inst.oracle_path, script_path, str(L2), str(R2), str(out), timeout=120.0, script_text="\r\n".join(script))
    after_L2 = tree_list(L2); after_R2 = tree_list(R2)
    residue_before = kill_bcompare()
    results.append({
        "tag": "S2-update-lr",
        "exit": r.exit_code,
        "after_L": after_L2,
        "after_R": after_R2,
        "residue_killed": residue_before,
    })
    print(f"  update:left->right exit={r.exit_code}, residue={residue_before}")

    # --- S3: select-orphan copy ---
    print("S3 select+copy...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S3-"))
    L3, R3 = tmpdir / "L", tmpdir / "R"
    L3.mkdir(); R3.mkdir()
    write_tree(L3, {"src.txt": None})
    write_tree(R3, {"orphan-R3.txt": None})
    script_path = run_dir / "scripts" / "S3.bcs"
    script = [
        f'load "{str(L3)}" "{str(R3)}"',
        "expand all",
        "select right.orphan.files",
        "copy left->right",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S3.out"
    r = orc.run(inst.oracle_path, script_path, str(L3), str(R3), str(out), timeout=120.0, script_text="\r\n".join(script))
    after_R3 = tree_list(R3)
    residue_before = kill_bcompare()
    results.append({
        "tag": "S3-select-orphan-copy",
        "exit": r.exit_code,
        "after_R": after_R3,
        "residue_killed": residue_before,
    })
    print(f"  select+copy exit={r.exit_code}, residue={residue_before}")

    # --- S4: visible-flag ---
    print("S4 visible flag...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S4-"))
    L4, R4 = tmpdir / "L", tmpdir / "R"
    L4.mkdir(); R4.mkdir()
    write_tree(L4, {"a.txt": None})
    write_tree(R4, {"b.txt": None})
    script_path = run_dir / "scripts" / "S4.bcs"
    script = [
        "sync visible mirror:left->right",  # no load yet
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S4.out"
    r = orc.run(inst.oracle_path, script_path, str(L4), str(R4), str(out), timeout=120.0, script_text="\r\n".join(script))
    residue_before = kill_bcompare()
    results.append({"tag": "S4-visible-no-load", "exit": r.exit_code, "residue_killed": residue_before})
    print(f"  visible without load exit={r.exit_code}, residue={residue_before}")

    # --- S5: create-empty ---
    print("S5 create-empty...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S5-"))
    L5, R5 = tmpdir / "L", tmpdir / "R"
    L5.mkdir(); R5.mkdir()
    write_tree(L5, {"a.txt": None})
    write_tree(R5, {"b.txt": None})
    script_path = run_dir / "scripts" / "S5.bcs"
    script = [
        "create-empty",
        f'load "{str(L5)}" "{str(R5)}"',
        "expand all",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S5.out"
    r = orc.run(inst.oracle_path, script_path, str(L5), str(R5), str(out), timeout=120.0, script_text="\r\n".join(script))
    after_L5 = tree_list(L5); after_R5 = tree_list(R5)
    residue_before = kill_bcompare()
    results.append({
        "tag": "S5-create-empty",
        "exit": r.exit_code,
        "after_L": after_L5,
        "after_R": after_R5,
        "residue_killed": residue_before,
    })
    print(f"  create-empty exit={r.exit_code}, residue={residue_before}")

    # --- S6: error-missing-folder ---
    print("S6 missing-folder error...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S6-"))
    L6 = tmpdir / "L"; L6.mkdir()
    nonexist = tmpdir / "nonexistent";  # do NOT create
    script_path = run_dir / "scripts" / "S6.bcs"
    script = [
        f'load "{str(L6)}" "{str(nonexist)}"',
        "expand all",
        "sync mirror:left->right",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S6.out"
    r = orc.run(inst.oracle_path, script_path, str(L6), str(nonexist), str(out), timeout=120.0, script_text="\r\n".join(script))
    residue_before = kill_bcompare()
    results.append({"tag": "S6-missing-right-folder", "exit": r.exit_code, "residue_killed": residue_before})
    print(f"  missing-folder exit={r.exit_code}, residue={residue_before}")

    # --- S7: delete-recyclebin ---
    print("S7 delete-recyclebin...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S7-"))
    L7, R7 = tmpdir / "L", tmpdir / "R"
    L7.mkdir(); R7.mkdir()
    write_tree(R7, {"del-me.txt": None})
    script_path = run_dir / "scripts" / "S7.bcs"
    script = [
        f'load "{str(L7)}" "{str(R7)}"',
        "expand all",
        "delete right recyclebin",
        'folder-report layout:summary output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S7.out"
    r = orc.run(inst.oracle_path, script_path, str(L7), str(R7), str(out), timeout=120.0, script_text="\r\n".join(script))
    after_R7 = tree_list(R7)
    residue_before = kill_bcompare()
    results.append({
        "tag": "S7-delete-recyclebin",
        "exit": r.exit_code,
        "after_R": after_R7,
        "residue_killed": residue_before,
    })
    print(f"  delete recyclebin exit={r.exit_code}, residue={residue_before}")

    # --- S8: report-labels-sync ---
    print("S8 report labels post-sync...")
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="m80b-S8-"))
    L8, R8 = tmpdir / "L", tmpdir / "R"
    L8.mkdir(); R8.mkdir()
    write_tree(L8, {"same.txt": None, "only-L.txt": None})
    write_tree(R8, {"same.txt": None, "only-R.txt": None})
    script_path = run_dir / "scripts" / "S8.bcs"
    script = [
        f'load "{str(L8)}" "{str(R8)}"',
        "expand all",
        "sync mirror:left->right",
        'folder-report layout:xml output-to:"%3"',
    ]
    orc.write_script(script_path, script)
    out = run_dir / "reports" / "S8.out"
    r = orc.run(inst.oracle_path, script_path, str(L8), str(R8), str(out), timeout=120.0, script_text="\r\n".join(script))
    residue_before = kill_bcompare()
    body = out.read_bytes() if out.exists() else b""
    # Extract first few labels
    labels = [ln.strip() for ln in body.decode("utf-8", errors="replace").splitlines() if "<Folder" in ln][:10]
    results.append({
        "tag": "S8-report-labels",
        "exit": r.exit_code,
        "sample_labels": labels[:5],
        "residue_killed": residue_before,
    })
    print(f"  xml report exit={r.exit_code}, sample labels={labels[:3]}, residue={residue_before}")

    # Save JSON summary
    (run_dir / "m80b-summary.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    # Copy golden snapshots
    for rep in (run_dir / "reports").glob("*.out"):
        golden = run_dir / "golden" / rep.stem
        golden.mkdir(parents=True, exist_ok=True)
        body = rep.read_bytes() if rep.exists() else b""
        head_lines = body.decode("utf-8", errors="replace").splitlines()[:50]
        (golden / "head.txt").write_text("\r\n".join(head_lines) + "\r\n", encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

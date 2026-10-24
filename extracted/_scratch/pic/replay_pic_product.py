#!/usr/bin/env python3
"""M9 product replay: run the PRODUCT binary over every picture golden and
over every archived m83* probe cell, and compare against the Oracle truth.

Two tracks (the m71 hex-replay split, adapted):

  A. GOLDEN CONTENT (36 cells): for each ``verify/pic/manifest.json`` entry,
     invoke the product with the stored script + fixture paths and fold-
     compare the whole report against the golden through the harness
     normalizer itself (norm-4) -- the identical rule set the gate uses, so
     the replay verdict cannot disagree with the gate for a spurious reason.

  B. ARCHIVE EXIT SURFACE (every ``runs/m83*/scripts/*.bcs``): re-invoke the
     product with the archived script line.  Content comparison is the
     golden track's job (docs/16: the archived reports embed the probe's
     runs/ paths); this track verifies the COMMAND VERDICT: exit code where
     the probe archive recorded one (summary JSON or report presence), and
     "refused => no report written" everywhere.  The 106/107 exact codes are
     already pinned by the CLI integration tests (script_exec); where the
     archive shows only "non-zero" this replay requires only non-zero.

Fold caveat (reconfirmed by this project's display trap): report timestamps
are SLASH-separated on disk; never trust a console rendering of them.

Usage:
    python replay_pic_product.py [--verbose]
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import normalize as norm          # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
RUNS = REA / "product" / "verify" / "runs"
PIC_TREE = REA / "verify" / "pic"

BOM = "\ufeff"
SCRIPT_RE = re.compile(r"picture-report", re.I)
VALID_LAYOUTS = {"side-by-side", "summary"}
VALID_OPTS = {"display-mismatches", "display-matches", "ignore-unimportant"}

# labels observed on the picture reports (zh repack + en reference)
HEAD_LEFT = ("左边文件： ", "左边文件: ", "Left file: ")
HEAD_RIGHT = ("右边文件： ", "右边文件: ", "Right file: ")


def fixtures_from_report(text: str) -> tuple[str | None, str | None]:
    """The archived report's header paths, (left, right)."""
    got: list[str] = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        for labels in (HEAD_LEFT, HEAD_RIGHT):
            for lab in labels:
                if ln.startswith(lab):
                    got.append(ln[len(lab):].split("  右边文件：")[0]
                               .split(" Left file:")[0].strip())
                    break
    while len(got) < 2:
        got.append(None)
    return got[0], got[1]


def parse_bcs(text: str) -> dict:
    """The parts of the grammar the replay needs to classify the cell."""
    t = text.strip()
    out: dict = {}
    m = re.search(r"layout:([A-Za-z0-9_-]+)", t)
    out["layout"] = m.group(1).lower() if m else None
    m_opt = re.search(r"(?<!output-)options:([^\s]*)", t)
    out["options"] = m_opt.group(1) if m_opt else None
    out["has_outopts"] = "output-options:" in t
    # file arguments in script order: a quoted arg is a FILE only when it
    # does not directly follow a key colon (title:"PicTitle" is not a file,
    # output-to:"%3" is the report slot, "%1"/"%2" are the comparison slots).
    files: list[str] = []
    for m in re.finditer(r'"([^"]*)"', t):
        arg = m.group(1)
        prev = t[m.start() - 1] if m.start() else ""
        if prev == ":" or arg == "%3":
            continue
        files.append(arg)
    out["slots"] = files
    return out


def option_class(info: dict, resolved_files: list[str]) -> str:
    """content (exit 0 expected) / refused (non-zero expected).

    A resolved file path that does not exist on disk is refused (the 107
    class, measured m83 P10 / m83n O7/O8): classification happens only for
    cells whose archive recorded no exit code, and there the probe files
    are whatever the header line or the nope placeholder names."""
    if info["has_outopts"]:
        return "refused"          # m83 P7
    if info["layout"] not in VALID_LAYOUTS:
        return "refused"          # m83 P4/P5
    if info["options"] is not None:
        for tok in info["options"].split(","):
            if tok and tok not in VALID_OPTS:
                return "refused"  # m83b Q3-3/Q3-5, m83o C2
    if len(info["slots"]) not in (0, 2):
        return "refused"          # m83 P9 one / m83n O9 three
    for f in resolved_files:
        if f and not pathlib.Path(f).exists():
            return "refused"      # missing-file 107 cells
    return "content"


def probe_exits(run_dir: pathlib.Path) -> dict[str, int]:
    """tag -> recorded exit code, from the run's summary JSON when present."""
    exits: dict[str, int] = {}
    for j in sorted(run_dir.glob("*-summary.json")):
        try:
            data = json.loads(j.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        recs = data if isinstance(data, list) else data.get("results", [])
        for rec in recs:
            if isinstance(rec, dict) and "tag" in rec and "exit" in rec:
                exits[str(rec["tag"])] = int(rec["exit"])
    return exits


def run_product(script_text: str, files: list[str], out: pathlib.Path,
                tmp: pathlib.Path) -> subprocess.CompletedProcess:
    sp = tmp / "cell.bcs"
    sp.write_text(script_text.rstrip() + "\r\n", encoding="utf-8")
    # three positional slots like the harness candidate track: the shell
    # cells ran with empty left/right (the script references only %3), so
    # padding is "" -- the M91-gate-pic-03 path the product accepts.
    pos = list(files)
    while len(pos) < 2:
        pos.append("")
    cmd = [str(PRODUCT), "/silent", f"@{sp}", pos[0], pos[1], str(out.resolve())]
    return subprocess.run(cmd, capture_output=True, timeout=120)


def main() -> int:
    verbose = "--verbose" in sys.argv
    fails: list[str] = []
    counts = {"A": [0, 0], "B": [0, 0]}   # track -> [total, pass]

    # ---------------- track A: golden content ----------------
    manifest = json.loads((PIC_TREE / "manifest.json").read_text(encoding="utf-8"))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="reacmp-pic-replay-"))
    for name, info in manifest.items():
        counts["A"][0] += 1
        files = [p for p in (info.get("left"), info.get("right")) if p]
        out = tmp / f"{name}.out"
        try:
            proc = run_product(info["script"], files, out, tmp)
        except subprocess.TimeoutExpired:
            fails.append(f"A {name}: product timeout")
            continue
        if proc.returncode != 0:
            fails.append(f"A {name}: exit {proc.returncode} "
                         f"{proc.stderr.decode(errors='replace')[:120]}")
            continue
        got = norm.normalize_text(out.read_text(encoding="utf-8", errors="replace")
                                  ) if out.exists() else None
        if got is None or not out.stat().st_size:
            fails.append(f"A {name}: exit 0 but no report")
            continue
        want = norm.normalize_text(
            pathlib.Path(info["report"]).read_text(encoding="utf-8", errors="replace"))
        if got.structure == want.structure:
            counts["A"][1] += 1
            if verbose:
                print(f"A pass {name} ({len(got.structure)} lines)")
        else:
            d = next((i for i, (a, b) in enumerate(zip(got.structure, want.structure))
                      if a != b), min(len(got.structure), len(want.structure)))
            fails.append(f"A {name}: line {d}: got {got.structure[d:d+1]} "
                         f"want {want.structure[d:d+1]}")

    # ---------------- track B: archived exit surface ----------------
    for run_dir in sorted(RUNS.glob("m83*")):
        scripts = run_dir / "scripts"
        if not scripts.is_dir():
            continue
        exits = probe_exits(run_dir)
        # report presence for runs whose JSON has no per-cell exit codes
        present = {f.name[:-4] for f in (run_dir / "reports").glob("*.out")
                   if f.stat().st_size > 0} if (run_dir / "reports").is_dir() else set()

        for bcs in sorted(scripts.glob("*.bcs")):
            cell = bcs.name[:-4]
            text = bcs.read_text(encoding="utf-8", errors="replace")
            if not SCRIPT_RE.search(text):
                continue
            counts["B"][0] += 1
            info = parse_bcs(text)

            # resolve %1/%2 slots to real archived fixtures when the probe's
            # report survives (content cells); literal paths pass through.
            out_file = run_dir / "reports" / f"{cell}.out"
            if "%1" in text or "%2" in text:
                slot_files: list[str] = []
                if out_file.exists():
                    l, r = fixtures_from_report(
                        out_file.read_text(encoding="utf-8-sig", errors="replace"))
                    slot_files = [x for x in (l, r) if x]
                files = []
                for s in info["slots"]:
                    if s == "%1":
                        files.append(slot_files[0] if len(slot_files) == 2
                                     else r"Z:\nope-a")
                    elif s == "%2":
                        files.append(slot_files[1] if len(slot_files) == 2
                                     else r"Z:\nope-b")
                    else:
                        files.append(s)
            else:
                files = info["slots"]
            cls = option_class(info, files)

            want_exit = exits.get(cell)
            if want_exit is None:
                want_exit = 0 if cell in present else None

            out = tmp / f"B-{run_dir.name}-{cell}.out"
            proc = run_product(text, files, out, tmp)
            wrote = out.exists() and out.stat().st_size > 0

            # the recorded archive exit is the truth where present; the
            # grammar classification is only a fallback for cells whose
            # inline batch recorded no code.
            if want_exit is not None:
                ok = proc.returncode == want_exit and wrote == (want_exit == 0)
            else:
                ok = (proc.returncode == 0 and wrote) if cls == "content" \
                     else (proc.returncode != 0 and not wrote)
            if ok:
                counts["B"][1] += 1
                if verbose:
                    print(f"B pass {run_dir.name[:14]} {cell} "
                          f"[{cls} exit={proc.returncode}]")
            else:
                fails.append(f"B {run_dir.name} {cell}: {cls}, "
                             f"archive exit={want_exit}, product exit={proc.returncode} "
                             f"wrote={wrote}")

    a_t, a_p = counts["A"]
    b_t, b_p = counts["B"]
    print(f"TRACK A goldens:     {a_p}/{a_t}")
    print(f"TRACK B surface:     {b_p}/{b_t}")
    if fails:
        print("FAILS:")
        for f in fails:
            print("  " + f)
    print(f"TOTAL {a_t + b_t}: {a_p + b_p} pass, {len(fails)} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

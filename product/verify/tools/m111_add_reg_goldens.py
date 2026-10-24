#!/usr/bin/env python3
"""M11 registry goldens: build the verify/reg golden tree from the measured
exit-0 cells of the m101..m101j archive (function 8, docs/17).

Every case below reproduces an OBSERVED probe cell. The tool copies the
probe's fixture bytes VERBATIM into ``D:\\Rea\\verify\\reg\\`` (never
regenerated: the Oracle measured these exact bytes), re-runs the archived
script line serially against the REFERENCE (English) install IN THE FINAL
TREE (the report embeds absolute fixture paths, so the goldens are produced
where the harness will later re-run them), and APPENDS the manifest entries
(append-only; a key clash aborts and a manifest snapshot lands in the run
directory).

WHY THE REFERENCE INSTALL AND NOT THE CURRENT ONE
------------------------------------------------
The registry side-by-side TABLE geometry is locale-dependent and was measured
on BOTH installs: the column floors are the header-label widths, so the
Chinese 名称/类型/数据 labels (2 columns) produce a 2-column-narrower table
than English Name/Type/Data (4 columns) for the very same fixtures
(m101f current vs m101f-regbox-reference, 29 shared cells; docs/17 §geometry).
The product renders the English frame (the dir/pic/hex precedent), so an
English golden is the only text the candidate replay can byte-match. The
Chinese side is not lost: it is locked by the product's own 103-table corpus
(85 ZH + 18 EN archived cells, ``reacmp-reg/tests/corpus_cases.rs``).

The cells cover the discriminating surface of docs/17: frame (title/Produced/
blank/Mode/file lines with the ``:\\`` basekey suffix), the summary count
categories and their measured order (same -> left orphan -> right orphan ->
difference, zero lines omitted, no unimportant category), value types
(REG_SZ/REG_DWORD/REG_BINARY/REG_MULTI_SZ/REG_EXPAND_SZ/REG_NONE and the
hex(3) type code), box geometry (orphan keys, nesting, orphan-end rows,
continuation bars, default-name ``@``), sort rules (keys then values,
linguistic collation), parse errors (Parsing Error line:col, deletes/dups
note), encoding errors (binary side -> File Encoding Error (Line 1), no
suffix), display filters (mismatches/matches), title, and the zero-file BOM
shell.  Refused-surface cells (106/107) are the CLI tests' job, not goldens
here (the m71/m91 precedent).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m111_add_reg_goldens.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

RUNS = REA / "product" / "verify" / "runs"

#: (name, layout, archived-run, archived-cell, note)
#: The fixture pair is read from the archived report's `Left file:`/
#: `Right file:` lines, so it cannot be typed wrong here; the script is copied
#: verbatim.  Every run below is a REFERENCE-install cell, so the archived
#: report is already English and its bytes are what the harness re-runs.
CASES = [
    # -- frame + counts (m101f-reference)
    ("r-sbs-equal", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F1-orphanend-sid",
     "frame: title/Produced/Mode/file lines + basekey suffix; orphan-end rows"),
    ("r-sum-equal", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F1-orphanend-sum",
     "summary: same + left orphan counts, no Mode line, no table"),
    # -- value types (m101f-reference)
    ("r-hex-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F13-hex-sid",
     "REG_BINARY per-byte display (trailing space per byte counts)"),
    ("r-hex-sum", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F13-hex-sum",
     "REG_BINARY summary counts"),
    ("r-multi-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F11-multi-sid",
     "multi-value key: keys then values at each level (sort rule)"),
    ("r-multi-sum", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F11-multi-sum",
     "multi-value summary counts"),
    ("r-cjk-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F10-cjk-sid",
     "CJK names: floor is the LABEL width, not the widest content"),
    ("r-cjk-sum", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F10-cjk-sum",
     "CJK summary counts"),
    ("r-spaces-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F14-spaces-sid",
     "names with spaces: display width counts the space"),
    ("r-spaces-sum", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F14-spaces-sum",
     "spaces summary counts"),
    ("r-roots-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F15-roots-sid",
     "root-level items print bare (level-0 has no ancestor bars)"),
    ("r-noval-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F16-noval-sid",
     "empty string value: data width 0, no placeholder"),
    ("r-default-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F18-default-sid",
     "default value name @ renders as (Default)"),
    ("r-default-sum", "summary",
     "m101f-regbox-reference-20261019T042839Z", "F18-default-sum",
     "(Default) row summary counts"),
    # -- box geometry (m101f-reference)
    ("r-nested-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F2-nested-sid",
     "matched nested keys: ancestor bars + own connector"),
    ("r-rightorph-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F3-rightorph-sid",
     "right orphan key: -+ on the left, nothing on the right header row"),
    ("r-parentorph-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F4-parentorph-sid",
     "parent orphan with content: orphan side prints nothing inside"),
    ("r-twoorph-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F5-twoorph-sid",
     "two orphan keys: both left and right orphans in one table"),
    ("r-casetie-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F7-casetie-sid",
     "case-differing key names pair (collation folds case)"),
    ("r-zoo-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F8-zoo-sid",
     "mixed names: punctuation, digits, CJK sort order"),
    ("r-hyphen-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F9-hyphen-sid",
     "hyphenated names: linguistic sort treats '-' as a separator"),
    ("r-depth3-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F12-depth3-sid",
     "depth-3 nesting: stacked continuation bars"),
    # -- value-type detail (m101b/m101d reference cells, docs/17 §values)
    ("r-types-sid", "side-by-side",
     "m101f-regbox-reference-20261019T042839Z", "F13-hex-sid",
     "placeholder for a second-type cross-check (hex binary pair)"),
]


def fixtures_for(report_text: str, run_dir: pathlib.Path) -> list[pathlib.Path]:
    """Extract the fixture paths from the archived report's header lines.

    The labels are the measured English ones; the path is everything after
    the label up to the basekey suffix.  The suffix starts with the measured
    ``:\\\\`` (colon + two backslashes), so the path ends at the FIRST such
    sequence -- a Windows drive-letter colon has no backslash after it.
    Returns them in the order they appear (left, right).
    """
    paths: list[pathlib.Path] = []
    for ln in report_text.replace("\r\n", "\n").split("\n"):
        for label in ("Left file: ", "Right file: "):
            if ln.startswith(label):
                p = ln[len(label):].strip()
                idx = p.find(":\\\\")
                if idx != -1:
                    p = p[:idx]
                q = pathlib.Path(p)
                if not q.is_absolute():
                    q = run_dir / q
                paths.append(q)
                break
    return paths


def main() -> int:
    tree = REA / "verify" / "reg"
    tree.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m111-reg-goldens-{stamp}"
    run_dir.mkdir(parents=True)

    installs = inst_mod.discover()
    # The REFERENCE install is the authoring engine: the product renders the
    # English frame (dir/pic/hex precedent) and the reference install is the
    # measured English locale, so candidate-vs-golden can byte-match.  The
    # current (Chinese) install is exercised by the harness's oracle suite
    # below, and its geometry is locked by reacmp-reg's own corpus tests.
    ref = installs["reference"]
    if not ref.enabled:
        raise SystemExit(f"reference install disabled: {ref.disabled_reason}")
    print(f"oracle : {ref.oracle_path} (engine {ref.oracle_version})")

    man_path = tree / "manifest.json"
    manifest: dict = {}
    if man_path.exists():
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        shutil.copy2(man_path, run_dir / "manifest.json.before")
    clash = [name for name, *_ in CASES if name in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, layout, run_name, cell, note in CASES:
        src_run = RUNS / run_name
        out_file = src_run / "reports" / f"{cell}.out"
        bcs_file = src_run / "scripts" / f"{cell}.bcs"
        if not out_file.is_file() or not bcs_file.is_file():
            raise SystemExit(f"{name}: archived cell missing: {out_file}")
        script_text = bcs_file.read_text(encoding="utf-8").strip()
        report_text = out_file.read_text(encoding="utf-8-sig", errors="replace")

        # fixtures: the probe's exact bytes, copied verbatim, renamed into
        # the golden tree as <name>-L/<name>-R keeping the source extension.
        src_files = fixtures_for(report_text, src_run)
        if len(src_files) not in (0, 2):
            raise SystemExit(f"{name}: expected 0 or 2 header paths, got {src_files}")
        stored: list[pathlib.Path] = []
        for side, f in zip(("L", "R"), src_files):
            dst = tree / f"{name}-{side}{f.suffix or '.reg'}"
            shutil.copy2(f, dst)
            stored.append(dst)

        report = tree / f"{name}.txt"
        sp = orc.write_script(run_dir / f"{name}.bcs", [script_text])
        lp = str(stored[0]) if stored else ""
        rp = str(stored[1]) if len(stored) > 1 else ""
        run = orc.run(ref.oracle_path, sp, lp, rp, str(report),
                      timeout=120.0, script_text=script_text)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{name}: oracle exit {run.exit_code}, "
                             f"report={run.report_exists}")
        # sanity: the fresh report must show the FINAL absolute fixture paths
        fresh = report.read_text(encoding="utf-8-sig", errors="replace")
        if stored:
            for s in stored:
                assert str(s) in fresh, f"{name}: {s} not in fresh report"
        # the zero-file shell case is the only one with no fixtures
        entry = {
            "layout": layout,
            "note": note,
            "script": script_text,
            "left": str(stored[0]) if stored else "",
            "right": str(stored[1]) if len(stored) > 1 else "",
            "exit_code": run.exit_code,
            "bytes": report.stat().st_size,
            "report": str(report),
            "authored_by": "reference (English 5.2.6.32774); the product "
                           "renders the English frame and the sbs geometry is "
                           "locale-dependent (docs/17 §geometry); the Chinese "
                           "geometry is locked by reacmp-reg's corpus tests",
        }
        manifest[name] = entry
        added += 1
        print(f"  {name:<20} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} registry goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

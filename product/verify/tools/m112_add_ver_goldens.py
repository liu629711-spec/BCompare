#!/usr/bin/env python3
"""M112 version goldens: build the verify/ver golden tree from the measured
exit-0 cells of the m112/m112b archive (function 8's version-report half,
docs/18).

Every case below reproduces an OBSERVED probe cell. The tool copies the
probe's fixture bytes VERBATIM into ``D:\\Rea\\verify\\ver\\`` (never
regenerated: the Oracle measured these exact bytes), re-runs the archived
script line serially against the REFERENCE (English) install IN THE FINAL
TREE (the report embeds absolute fixture paths, so the goldens are produced
where the harness will later re-run them), and APPENDS the manifest entries
(append-only; a key clash aborts and a manifest snapshot lands in the run
directory).

WHY THE REFERENCE INSTALL AND NOT THE CURRENT ONE
------------------------------------------------
The version side-by-side TABLE labels are locale parameters (the registry
precedent, docs/17 §6): the Chinese 名称/值 labels and group headings render
differently from the English Name/Value ones for the very same fixtures. The
product renders the English frame (dir/pic/hex/registry precedent), so an
English golden is the only text the candidate replay can byte-match. The
Chinese side is not lost: it is locked by the product's own 18-cell corpus
(m112/m112b archived tables, ``reacmp-ver/tests/corpus_cases.rs``).

KNOWN RESIDUAL (U-ver-1): the `Data` size field's number is not the file
size, and no header-derived model reproduced it (raw size, SizeOfImage,
section sums, FileAlignment floors, cert table, debug dir all rejected on the
m112/m112b fixtures). The goldens therefore keep the Oracle's number VERBATIM
and the replay's candidate diff on that one row is folded by norm-6's
ver-size rule -- the row itself (name/marker/columns) must still match.

The cells cover the discriminating surface of docs/18: frame (title/Produced/
blank/Mode/file lines with the single-`File:` form when both paths agree),
the two layouts, the field groups (Code/Data, PE Header Info, Fixed,
Translation, Strings), markers (= <> +- -+ and the missing-side bars),
display filters, ignore-unimportant, title, and the zero-file BOM shell.
Refused-surface cells (106/107) are the CLI tests' job, not goldens here
(the m71/m91/m101 precedent).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m112_add_ver_goldens.py
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
#: The fixture pair is read from the archived report's `左边文件：`/
#: `右边文件：`/`文件：` lines (the m112 cells were measured on the Chinese
#: current install), so the paths cannot be typed wrong here; the script is
#: copied verbatim.  The goldens themselves are RE-RUN on the reference
#: install, so the committed report is English.
CASES = [
    # -- frame + both layouts (m112)
    ("v-sbs-equal", "side-by-side",
     "m112-versurface-20261019T135402Z", "V1-sbs-equal",
     "frame: title/Produced/blank/Mode/file lines + the full equal table"),
    ("v-sum-equal", "summary",
     "m112-versurface-20261019T135402Z", "V2-sum-equal",
     "summary: same count only, no Mode line, no table"),
    ("v-sbs-diff", "side-by-side",
     "m112-versurface-20261019T135402Z", "V3-sbs-diff",
     "a real two-engine pair: <> markers, 6 differing fields"),
    ("v-sum-diff", "summary",
     "m112-versurface-20261019T135402Z", "V4-sum-diff",
     "summary: same + difference counts"),
    # -- field-group coverage (m112)
    ("v-sbs-com", "side-by-side",
     "m112-versurface-20261019T135402Z", "V5-sbs-com",
     "exe vs .com: +-/-+ one-sided rows, unknown-key blanking"),
    ("v-sbs-ms", "side-by-side",
     "m112-versurface-20261019T135402Z", "V6-sbs-ms",
     "notepad vs cmd: Microsoft MUI fields, 图像版本 present"),
    ("v-sbs-plain-vs-pe", "side-by-side",
     "m112-versurface-20261019T135402Z", "V7-sbs-plain-vs-pe",
     "plain left side: the minimum left half, all -+ rows"),
    ("v-sbs-plain-both", "side-by-side",
     "m112-versurface-20261019T135402Z", "V8-sbs-plain-both",
     "both sides plain: the 10-dash shell table + the single File: line"),
    ("v-sbs-reg-pair", "side-by-side",
     "m112-versurface-20261019T135402Z", "V23-sbs-reg-pair",
     "BComp.com pair: the launcher's smaller resource set"),
    ("v-sbs-dll", "side-by-side",
     "m112-versurface-20261019T135402Z", "V24-sbs-dll",
     "exe vs DLL: \\文件类型 DLL, per-side connectors"),
    # -- options + title (m112)
    ("v-title", "side-by-side",
     "m112-versurface-20261019T135402Z", "V22-title",
     "title replaces the first line"),
    ("v-opt-ignore-unimp", "summary",
     "m112-versurface-20261019T135402Z", "V14-opt-ignore-unimp",
     "ignore-unimportant: the header line + folded Mode text"),
    ("v-opt-dmism", "summary",
     "m112-versurface-20261019T135402Z", "V15-opt-dmism",
     "display-mismatches accepted (no byte effect here)"),
    ("v-opt-dmatch", "summary",
     "m112-versurface-20261019T135402Z", "V16-opt-dmatch",
     "display-matches accepted (no byte effect here)"),
    # -- zero-file shell (m112 RAW)
    ("v-shell", "side-by-side",
     "m112-versurface-20261019T135402Z", "V21-zero-files",
     "zero-file BOM shell WITH the Mode line (registry precedent)"),
    # -- field-level detail (m112b)
    ("v-one-field", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W1-one-field",
     "the patch harness: one field differs, everything else equal"),
    ("v-w2a-filedescription", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W2a-filedescription",
     "FileDescription patched on one side"),
    ("v-w2b-originalfilename", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W2b-originalfilename",
     "OriginalFilename patched on one side"),
    ("v-w2c-legaltrademarks", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W2c-legaltrademarks",
     "LegalTrademarks patched: the known-key '|' rule on the right"),
    ("v-w3-blank-comments", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W3-blank-comments",
     "Comments patched empty: the present-side '|' marker"),
    ("v-w5-long-value", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W5-long-value",
     "a value longer than the column: the truncation ellipsis"),
    ("v-w7-same-res-diff-size", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W7-same-res-diff-size",
     "identical resources, different sizes: the U-ver-1 row in <> form"),
    ("v-w8-truncated-pe", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W8-truncated-pe",
     "a truncated PE: PE groups only on the left, resource groups blank"),
    ("v-w11-ignore-one-field", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W11-ignore-one-field",
     "ignore-unimportant over a one-field diff"),
    ("v-w12-tail-differs", "side-by-side",
     "m112b-verfields-20261019T153141Z", "W12-tail-differs",
     "a tail-only byte difference that the resource table shows"),
]


def fixtures_for(report_text: str, run_dir: pathlib.Path) -> list[pathlib.Path]:
    """Extract the fixture paths from the archived report's header lines.

    The m112 cells were measured on the Chinese current install, so the
    labels are the Chinese ones (plus the single `文件：` form).  Returns
    them in the order they appear.
    """
    paths: list[pathlib.Path] = []
    for ln in report_text.replace("\r\n", "\n").split("\n"):
        for label in ("左边文件： ", "右边文件： ", "文件： "):
            if ln.startswith(label):
                q = pathlib.Path(ln[len(label):].strip())
                if not q.is_absolute():
                    q = run_dir / q
                paths.append(q)
                break
    return paths


def main() -> int:
    tree = REA / "verify" / "ver"
    tree.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m112-ver-goldens-{stamp}"
    run_dir.mkdir(parents=True)

    installs = inst_mod.discover()
    # The REFERENCE install is the authoring engine: the product renders the
    # English frame (dir/pic/hex/registry precedent) and the reference
    # install is the measured English locale, so candidate-vs-golden can
    # byte-match.  The current (Chinese) install is exercised by the
    # harness's oracle suite below, and its geometry is locked by
    # reacmp-ver's own corpus tests.
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
        if len(src_files) not in (0, 1, 2):
            raise SystemExit(f"{name}: expected 0/1/2 header paths, got {src_files}")
        # V8's single `文件：` line names the SAME path twice -- the pair is
        # that one file on both sides.
        stored: list[pathlib.Path] = []
        pair = src_files[:2] if len(src_files) == 2 else ([src_files[0], src_files[0]] if len(src_files) == 1 else [])
        for side, f in zip(("L", "R"), pair):
            dst = tree / f"{name}-{side}{f.suffix or '.exe'}"
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
                           "renders the English frame and the labels are "
                           "locale parameters (docs/18 §6, the docs/17 "
                           "precedent); the Chinese rendering is locked by "
                           "reacmp-ver's corpus tests",
        }
        manifest[name] = entry
        added += 1
        print(f"  {name:<24} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} version goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

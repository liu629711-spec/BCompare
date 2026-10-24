#!/usr/bin/env python3
"""M9 picture goldens: build the verify/pic golden tree from the measured
exit-0 cells of the m83..m83o archive (function 7, docs/16).

Every case below reproduces an OBSERVED probe cell. The tool copies the
probe's fixture bytes VERBATIM into ``D:\\Rea\\verify\\pic\\`` (never
regenerated: the Oracle measured these exact bytes), re-runs the archived
script line serially against the current install IN THE FINAL TREE (the
report embeds absolute fixture paths, so the goldens are produced where the
harness will later re-run them), and APPENDS the manifest entries (append-
only; a key clash aborts and a manifest snapshot lands in the run directory).

The cells cover the discriminating surface of docs/16: frame (title/Produced/
blank/file lines), summary count categories and their measured order (same ->
unimportant -> left orphan -> right orphan -> important, zero lines omitted),
the 25-vs-26 importance boundary, per-channel-not-summed deltas, alpha ignored,
gray colour type, BMP input, GIF Invalid-image handling, size surplus on one
and BOTH sides, options (display-* inert, ignore-unimportant header + renamed
label, multi-token valid list), the BOM zero-file shell, error lines, and
title.  Refused-surface cells (106/107) are the CLI tests' job, not goldens
here (the m71 precedent).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m91_add_pic_goldens.py
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

#: (name, layout, archived-report, archived-script, note)
#: The fixture pair is read from the archived report's `左边文件：/右边文件：`
#: lines, so it cannot be typed wrong here; the script is copied verbatim.
CASES = [
    # -- frame + basic counts (m83, m83b)
    ("p-sbs-equal", "side-by-side",
     "m83-picture-20261018T165527Z", "P1-sbs-equal",
     "P1: frame-only side-by-side on identical images; no count lines"),
    ("p-sbs-diff", "side-by-side",
     "m83-picture-20261018T165527Z", "P2-sbs-diff",
     "P2/Q4: side-by-side on DIFFERING images is still frame-only"),
    ("p-sum-diff", "summary",
     "m83-picture-20261018T165527Z", "P3-sum-diff",
     "P3: summary adds the important count line (d=255 delta)"),
    ("p-sum-equal", "summary",
     "m83b-picturemodel-20261018T165610Z", "Q1-summary-equal",
     "Q1: identical pair -> only the same count line"),
    ("p-title", "side-by-side",
     "m83-picture-20261018T165527Z", "P11-title",
     "P11: title: replaces frame line 1"),
    # -- count categories and order (m83b, m83g, m83h, m83i, m83j, m83c)
    ("p-sum-4px", "summary",
     "m83b-picturemodel-20261018T165610Z", "Q2-summary-4px",
     "Q2: 60 same + 4 important; zero categories omitted"),
    ("p-mixed-order", "summary",
     "m83h-picorder4-20261019T011521Z", "F.all4",
     "m83h: same -> unimportant -> left orphan -> important measured order"),
    ("p-rightonly-order", "summary",
     "m83i-piclast-20261019T011613Z", "V1-rightonly-order",
     "m83i V1: right orphan sorts BEFORE important"),
    ("p-both-surplus", "summary",
     "m83j-bothsurplus-20261019T011719Z", "BS",
     "m83j: 6x8 vs 8x6 -> 36 same + 12L + 12R, left-before-right"),
    ("p-left-surplus", "summary",
     "m83c-picthresh-20261018T165700Z", "R7-size",
     "R7: left-only surplus counted alone"),
    ("p-half-order", "summary",
     "m83g-picorder-20261019T011433Z", "ORDER-mixed",
     "m83g: same then left orphan in the half-difference pair"),
    ("p-right-only", "summary",
     "m83g-picorder-20261019T011433Z", "RIGHT-only",
     "m83g: same then right orphan"),
    # -- importance boundary rules (m83c, m83e, m83f)
    ("p-bound-25", "summary",
     "m83e-picrule-20261018T165816Z", "U4-25",
     "U4: delta 25 is unimportant (the measured boundary)"),
    ("p-bound-26", "summary",
     "m83f-picbound-20261018T165834Z", "b26",
     "m83f b26: delta 26 is important (the exact boundary counterpart)"),
    ("p-half-diff", "summary",
     "m83c-picthresh-20261018T165700Z", "R5-half",
     "R5: half-same half-important pair"),
    ("p-alpha-ignored", "summary",
     "m83e-picrule-20261018T165816Z", "U8-alpha32",
     "U8: alpha differs only -> 64 same (alpha is ignored)"),
    ("p-gray-delta", "summary",
     "m83e-picrule-20261018T165816Z", "U9-gray32",
     "U9: gray colour type, delta 32 -> important"),
    ("p-perchannel", "summary",
     "m83e-picrule-20261018T165816Z", "U7-minusplus",
     "U7: per-channel max, not sum (+16/-16 on different channels)"),
    # -- formats (m83b, m83e, m83i, m83, m83g)
    ("p-bmp-diff", "summary",
     "m83b-picturemodel-20261018T165610Z", "Q5-bmp-summary",
     "Q5: 24-bit uncompressed BMP pair decodes and counts"),
    ("p-bmp32", "summary",
     "m83e-picrule-20261018T165816Z", "U10-bmp32",
     "U10: BMP at delta 32 -> important"),
    ("p-gif-invalid", "summary",
     "m83i-piclast-20261019T011613Z", "V3a-gif-equal",
     "V3a: GIF signature -> both sides Invalid image, no counts"),
    ("p-nonimage", "side-by-side",
     "m83-picture-20261018T165527Z", "P12-nonimage",
     "P12: non-image payload -> both sides Unsupported Type"),
    ("p-unsupported-both", "summary",
     "m83g-picorder-20261019T011433Z", "BOTH-error",
     "m83g: Unsupported Type on both sides; summary has no count lines"),
    ("p-mixed-error", "summary",
     "m83b-picturemodel-20261018T165610Z", "Q7-mixed",
     "Q7: healthy PNG vs non-image -> right error + left orphan surplus"),
    # -- options semantics (m83, m83b, m83n, m83g, m83i, m83o)
    ("p-opt-dmism", "summary",
     "m83n-picoptions-20261019T015624Z", "O2-display-mismatches",
     "O2: display-mismatches accepted, byte-identical to default (O1)"),
    ("p-opt-dmatch", "summary",
     "m83n-picoptions-20261019T015624Z", "O3-display-matches",
     "O3: display-matches accepted, byte-identical to default"),
    ("p-opt-ignore", "summary",
     "m83n-picoptions-20261019T015624Z", "O4-ignore",
     "O4: ignore-unimportant adds the header and renames the label"),
    ("p-ignore-line", "summary",
     "m83g-picorder-20261019T011433Z", "IGNORE-line",
     "m83g: the header line sits BEFORE the file lines"),
    ("p-ignore-order", "summary",
     "m83i-piclast-20261019T011613Z", "V2-ignore-unimp",
     "m83i V2: ignored-unimportant label with full four-category order"),
    ("p-opt-two-valid", "summary",
     "m83o-picopts2-20261019T015710Z", "C1-two-valid",
     "m83o C1: options:display-mismatches,ignore-unimportant is valid"),
    ("p-opt-empty", "summary",
     "m83o-picopts2-20261019T015710Z", "C3-empty",
     "m83o C3: options: (empty value) is accepted like the default"),
    ("p-layout-case", "summary",
     "m83o-picopts2-20261019T015710Z", "C4-two-case",
     "m83o C4: layout:SUMMARY (uppercase) is accepted"),
    ("p-opt-default", "summary",
     "m83n-picoptions-20261019T015624Z", "O1-default",
     "O1: default summary counts on the mixed-importance pair"),
    ("p-sbs-opt-dm", "side-by-side",
     "m83-picture-20261018T165527Z", "P6-options",
     "P6: side-by-side + display-mismatches is still frame-only"),
    # -- zero-file BOM shell (m83, m83n)
    ("p-shell-sbs", "side-by-side",
     "m83-picture-20261018T165527Z", "P8-zero-files",
     "P8: zero files -> BOM shell with Base folder line (side-by-side form)"),
    ("p-shell-sum", "summary",
     "m83n-picoptions-20261019T015624Z", "O5-sum-zero",
     "O5: zero files summary form is the same shell shape"),
]





def fixtures_for(report_text: str, run_dir: pathlib.Path) -> list[pathlib.Path]:
    """Extract the fixture paths from the archived report's header lines.

    The labels are the measured Chinese ones; the path is everything after
    the label. Returns them in the order they appear (left, right)."""
    paths: list[pathlib.Path] = []
    for ln in report_text.replace("\r\n", "\n").split("\n"):
        for label in ("左边文件： ", "右边文件： "):
            if ln.startswith(label):
                p = pathlib.Path(ln[len(label):].strip())
                if not p.is_absolute():
                    p = run_dir / p
                paths.append(p)
                break
    return paths


def main() -> int:
    tree = REA / "verify" / "pic"
    tree.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m91-pic-goldens-{stamp}"
    run_dir.mkdir(parents=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")

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
            dst = tree / f"{name}-{side}{f.suffix or '.bin'}"
            shutil.copy2(f, dst)
            stored.append(dst)

        report = tree / f"{name}.txt"
        sp = orc.write_script(run_dir / f"{name}.bcs", [script_text])
        lp = str(stored[0]) if stored else ""
        rp = str(stored[1]) if len(stored) > 1 else ""
        run = orc.run(cur.oracle_path, sp, lp, rp, str(report),
                      timeout=120.0, script_text=script_text)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{name}: oracle exit {run.exit_code}, "
                             f"report={run.report_exists}")
        # sanity: the fresh report must show the FINAL absolute fixture paths
        fresh = report.read_text(encoding="utf-8-sig", errors="replace")
        if stored:
            for s in stored:
                assert str(s) in fresh, f"{name}: {s} not in fresh report"
        entry = {
            "layout": layout,
            "note": note,
            "script": script_text,
            "left": str(stored[0]) if stored else "",
            "right": str(stored[1]) if len(stored) > 1 else "",
            "exit_code": run.exit_code,
            "bytes": report.stat().st_size,
            "report": str(report),
        }
        manifest[name] = entry
        added += 1
        print(f"  {name:<20} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} picture goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

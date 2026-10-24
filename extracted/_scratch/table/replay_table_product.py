#!/usr/bin/env python3
"""M6.3+ product replay: run the PRODUCT binary over every archived table
fixture and compare its report against the stored Oracle report.

M6.4 upgrade (2026-10-18): the comparison is now **whole-frame**, not
body-only.  The frame carries the title line, the `Produced:` stamp, the
`Mode:` line and the two file paths; the dash/slash stamp misread (docs/13 §6
correction) was invisible to body-only replay, which is exactly why the frame
joined the acceptance surface.  Folded before comparison:

* the `Produced:`/`已产生：` stamp line -> `Produced: TIME` (wall clock),
* measured zh label lines -> their English twins (the title, `Mode:`, the
  two file-path labels, and the count lines' suffixes),
* the path lines are passed through verbatim -- the replay re-invokes with
  the archived fixture paths, so they must agree byte-for-byte.

Layouts/titles/options come from each archived `.bcs` (the exact invocation
is replayed), not from filename guessing.  Error-surface cells (options:,
output-options:, xml, missing files, wrong file counts, empty layout) are
replayed for EXIT CODE + output presence, not content: the archived exit is
the truth (measured surface, docs/13 §6).

Scope: `.csv` fixtures only (the product models the fixed-comma format; the
auto-detect path cells are skipped and listed).  Offline: no Oracle calls;
products write to a temp dir; archives are read-only.

Usage:  python replay_table_product.py [--verbose]

M6.4-b: the auto-detect path is now implemented (comma > tab > semicolon >
pipe, joint over both files; no candidate -> rawline verbatim). Non-.csv
archives join the comparison, EXCEPT the space-split cells whose acceptance
rule the archive contradicts: the product falls back to rawline there and
the diff is reported as KNOWN (listed, never silently passed). m67
(docs/13 §8) localized the core contradiction to H5 -- byte-identical first
rows rendered `<>` in the Oracle -- and added two shape cells (H4/H8: BC
splits, product rawlines) to the same KNOWN family.
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys, tempfile

REA = pathlib.Path(r"D:\Rea")
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
RUNS = REA / "product" / "verify" / "runs"

#: The space-format cells the engine does not model (docs/13 §7 residual):
#: BC splits aligned space runs into cells (S4 `a b`/`c d` -> two columns);
#: the product falls back to rawline there. Keyed by (run prefix, tag); a
#: hit that mismatches counts as KNOWN, is LISTED, and never silently
#: passes. A KNOWN cell that PASSES anyway is also fine (listed separately).
KNOWN_SPACE_CELLS = {
    ("m62-autodetect", "S4-space"),
    ("m65b-spacerules", "SP6"),
    ("m65c-spacemodel", "SP7"),
    ("m65c-spacemodel", "SP8"),
    ("m65c-spacemodel", "SP9"),
    # m67/m68: the attack round localized the contradiction (docs/13 §8).
    # H8/H4 = BC splits aligned runs (cells keep them); product rawlines.
    # H5 = the core contradiction: byte-identical first rows render `<>`,
    # which no split-and-compare model produces.
    ("m67-spaceattack", "H4"),
    ("m67-spaceattack", "H5"),
    ("m67-spaceattack", "H8"),
    # m68 IR2: identical `a b `/`c d ` files -> Oracle header is 2 columns
    # (space-split fired); same family as H8/SP8.
    ("m68-mixedext", "IR2"),
}

# Measured zh->en label pairs for the table channel (current 5.2.1 repack vs
# the reference install's English twins, captured in runs/m62-reflabels-*):
ZH_FRAME = {
    "表格比较(B)": "Table Compare",
    "模式：  全部": "Mode:  All",
}
ZH_PREFIX = (
    ("左边文件： ", "Left file: "),
    ("右边文件： ", "Right file: "),
)
ZH_TO_EN = {
    "个相同排": "same row(s)",
    "个重要差异排": "important difference row(s)",
    "个重要的左边独有排": "important left orphan row(s)",
    "个重要右边独有排": "important right orphan row(s)",
}
COUNT_RE = re.compile(r"^(\d+) (个[^\d]*)$")
STAMP_ZH = "已产生："
STAMP_EN = "Produced:"


def fold_lines(text: str) -> list[str]:
    """Whole-frame fold: labels to English, stamp to TIME, trailing blank kept
    exactly once (the report body ends with one final line)."""
    out = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if ln.startswith(STAMP_ZH) or ln.startswith(STAMP_EN):
            out.append("Produced: TIME")
            continue
        if ln in ZH_FRAME:
            out.append(ZH_FRAME[ln])
            continue
        hit = False
        for zh, en in ZH_PREFIX:
            if ln.startswith(zh):
                out.append(en + ln[len(zh):])
                hit = True
                break
        if hit:
            continue
        m = COUNT_RE.match(ln)
        if m and m.group(2) in ZH_TO_EN:
            out.append(f"{m.group(1)} {ZH_TO_EN[m.group(2)]}")
            continue
        out.append(ln)
    # drop the single artifact line produced by the final \r\n
    if out and out[-1] == "":
        out.pop()
    return out


BCS_RE = re.compile(r"data-report|table-report", re.I)


def parse_bcs(script_text: str) -> dict:
    """Extract layout/title/options/output-options and comparison arity from
    one archived script line (single-line table probes; folder lines absent)."""
    t = script_text.strip()
    m = re.search(r"layout:([A-Za-z0-9-]+)", t)
    out = {"layout": m.group(1).lower() if m else None}
    m = re.search(r'title:"([^"]*)"', t)
    out["title"] = m.group(1) if m else None
    out["has_options"] = "options:" in t.replace("output-options:", "")
    out["has_outopts"] = "output-options:" in t
    out["files"] = len(re.findall(r'"%[123]"|"[^"%][^"]*"', t))  # rough arity
    return out


def fixture_pair(d: pathlib.Path, tag: str):
    """Resolve the archived fixture pair for a tag, any extension (m60/m63
    shared pairs keep their tag conventions; m61b P10 names them bare;
    m68 mixes extensions per side, e.g. MX1-L.txt / MX1-R.csv)."""
    suffixes = (".csv", ".CSV", ".txt", ".TXT", ".tsv", ".xyz", "")
    for ls in suffixes:
        la = d / "fixtures" / f"{tag}-L{ls}"
        if not la.is_file():
            continue
        for rs in suffixes:
            lb = d / "fixtures" / f"{tag}-R{rs}"
            if lb.is_file():
                return la, lb
    for suffix in suffixes:
        la, lb = d / "fixtures" / f"{tag}-L{suffix}", d / "fixtures" / f"{tag}-R{suffix}"
        if la.is_file() and lb.is_file():
            return la, lb
    # m60 shared pair (T-a/T-b) and m63 shared pair (X-L/X-R)
    for a, b in (("T-a.csv", "T-b.csv"), ("X-L.csv", "X-R.csv")):
        la, lb = d / "fixtures" / a, d / "fixtures" / b
        if la.is_file() and lb.is_file():
            return la, lb
    # m61b P10: bare-name pair 'P10a.tsv' vs 'R-P10a.tsv'
    la, lb = d / "fixtures" / tag, d / "fixtures" / f"R-{tag}"
    if la.is_file() and lb.is_file():
        return la, lb
    return None, None


def main() -> int:
    verbose = "--verbose" in sys.argv
    total = passed = skipped = 0
    exitcells = known_fail = 0
    fails = []
    knowns = []
    known_pass = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="reacmp-table-replay-"))
    for d in sorted(RUNS.glob("m6*-*")):
        reports = d / "reports"
        if not reports.is_dir():
            continue
        for out_file in sorted(reports.glob("*.out")):
            stem = out_file.name[:-4]
            tag, _, lay = stem.rpartition(".")
            if lay not in ("side-by-side", "interleaved", "summary"):
                # m60/m62/m63 archives name the report by tag only
                tag, lay = stem, None
            bcs = out_file.parent / (out_file.name.replace(".out", ".bcs"))
            if not bcs.exists():
                skipped += 1
                continue
            script_text = bcs.read_text(encoding="utf-8", errors="replace")
            info = parse_bcs(script_text)
            if not BCS_RE.search(script_text):
                skipped += 1            # text-report / file-report / load probes
                continue
            lay = info["layout"] or (lay if lay in
                    ("side-by-side", "interleaved", "summary") else None)
            if lay is None:
                skipped += 1
                continue
            # fixtures: tag-based stems, any extension (m60/m63 shared pairs
            # keep their tag conventions).
            lp, rp = fixture_pair(d, tag)
            if lp is None:
                skipped += 1
                continue
            oracle_exit = None
            # archived exit code: prefer the JSON meta, else trust the file.
            meta = next(iter(sorted(d.glob("*.json"))), None)
            if meta is not None:
                try:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        for rec in data:
                            if rec.get("tag") == tag:
                                if "exit" in rec:
                                    oracle_exit = rec["exit"]
                                rr = rec.get("reports")
                                if isinstance(rr, dict) and lay in rr:
                                    oracle_exit = rr[lay].get("exit")
                                break
                except (json.JSONDecodeError, KeyError):
                    pass
            else:
                data = None

            out = tmp / f"{d.name}.{stem}.out"
            script = tmp / f"{d.name}.{stem}.bcs"
            script.write_text(script_text, encoding="utf-8")
            proc = subprocess.run(
                [str(PRODUCT), "/silent", f"@{script}",
                 str(lp.resolve()), str(rp.resolve()), str(out.resolve())],
                capture_output=True, timeout=120)
            total += 1

            error_surface = (info["has_options"] or info["has_outopts"]
                             or lay == "xml" or oracle_exit not in (0, None))
            if error_surface:
                exitcells += 1
                want = oracle_exit if oracle_exit is not None else proc.returncode
                wrote = out.exists() and out.stat().st_size > 0
                # 0-byte archives count as "no report"
                empty_truth = False
                if meta and isinstance(data, list):
                    for rec in data:
                        if rec.get("tag") == tag:
                            rb = rec.get("report_bytes") or (rec.get("reports") or {}) \
                                .get(lay, {}).get("body", "x")
                            if rb == 0:
                                empty_truth = True
                expect_wrote = (want == 0) and not empty_truth
                if proc.returncode != want or wrote != expect_wrote:
                    fails.append((d.name, stem, f"exit surface: want exit {want} "
                                  f"wrote={expect_wrote}, got exit {proc.returncode} "
                                  f"wrote={wrote}"))
                continue

            if not (out.exists() and out.stat().st_size > 0):
                fails.append((d.name, stem, f"product produced no report (exit "
                              f"{proc.returncode})"))
                continue
            got = fold_lines(out.read_text(encoding="utf-8-sig", errors="replace"))
            want_lines = fold_lines(
                out_file.read_text(encoding="utf-8-sig", errors="replace"))
            # run-prefix key: m62-autodetect, m65b-spacerules, m65c-spacemodel...
            run_prefix = "-".join(d.name.split("-")[:2])
            is_known = (run_prefix, tag) in KNOWN_SPACE_CELLS
            if got == want_lines:
                if is_known:
                    known_pass.append(f"{d.name}/{stem}")
                passed += 1
            elif is_known:
                known_fail += 1
                knowns.append((d.name, stem, "space-split known difference"))
                if verbose:
                    print(f"== KNOWN {d.name} / {stem}")
                    for i, (a, b) in enumerate(zip(got + [""] * len(want_lines),
                                                   want_lines + [""] * len(got))):
                        if a != b:
                            print(f"  line {i}\n   product={a!r}\n   oracle ={b!r}")
            else:
                fails.append((d.name, stem, "frame+body mismatch"))
                if verbose:
                    print(f"== {d.name} / {stem}")
                    for i, (a, b) in enumerate(zip(got + [""] * len(want_lines),
                                                   want_lines + [""] * len(got))):
                        if a != b:
                            print(f"  line {i}\n   product={a!r}\n   oracle ={b!r}")

    print(f"\nproduct replay: total={total} pass={passed} fail={len(fails)} "
          f"known-space={known_fail} skip={skipped} (exit-surface cells={exitcells})")
    for d, stem, why in knowns[:10]:
        print(f"  KNOWN(space residual) {d} / {stem}")
    for d, stem, why in fails[:30]:
        print(f"  FAIL {d} / {stem}: {why}")
    if known_pass:
        print(f"  NOTE: {len(known_pass)} KNOWN-listed cells passed anyway "
              f"(rawline coincides with BC there): {known_pass}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

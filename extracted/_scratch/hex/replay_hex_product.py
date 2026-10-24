#!/usr/bin/env python3
"""M7 product replay: run the PRODUCT binary over every archived hex fixture
and compare its report against the stored Oracle report, whole-frame.

Frame fold (measured label pairs, runs/m70e/m70e2 current-vs-reference):
  16 进制比较(H) -> Hex Compare ; 已产生： -> Produced: TIME ;
  模式：  全部 -> Mode:  All ; 左边文件： /右边文件： -> Left/Right file: ;
  summary count lines 个相同字节/个左边独有字节/个右边独有字节/个差异字节
  -> same/left orphan/right orphan/difference byte(s).
Paths pass through verbatim: the replay re-invokes with the archived fixture
paths, so they must agree byte-for-byte.

The archived runs are the Oracle truth (docs/14). Error-surface cells
(options:, output-options:, bogus/missing layout, wrong file counts, missing
files) are replayed for EXIT CODE + output presence, not content.

Usage:  python replay_hex_product.py [--verbose]
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys, tempfile

REA = pathlib.Path(r"D:\Rea")
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
RUNS = REA / "product" / "verify" / "runs"

ZH_FRAME = {"16 进制比较(H)": "Hex Compare", "模式：  全部": "Mode:  All"}
ZH_PREFIX = (("左边文件： ", "Left file: "), ("右边文件： ", "Right file: "))
ZH_TO_EN = {
    "个相同字节": "same byte(s)",
    "个左边独有字节": "left orphan byte(s)",
    "个右边独有字节": "right orphan byte(s)",
    "个差异字节": "difference byte(s)",
}
COUNT_RE = re.compile(r"^(\d+) (个[^\d]*)$")
STAMP_ZH = "已产生："
STAMP_EN = "Produced:"


def fold_lines(text: str) -> list[str]:
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
    if out and out[-1] == "":
        out.pop()
    return out


BCS_RE = re.compile(r"hex-report", re.I)


def parse_bcs(script_text: str) -> dict:
    t = script_text.strip()
    m = re.search(r"layout:([A-Za-z0-9-]+)", t)
    out = {"layout": m.group(1).lower() if m else None}
    m = re.search(r'title:"([^"]*)"', t)
    out["title"] = m.group(1) if m else None
    out["has_options"] = bool(re.search(r"(?<!output-)options:", t))
    out["has_outopts"] = "output-options:" in t
    # comparison slots in SCRIPT ORDER: "%1"/"%2" or a literal path
    # (m70g/V2 error cells deliberately pass 0/1/3 files or Z:\nope paths;
    # the replay must reproduce that exact arity, not a fixed pair)
    out["slots"] = [s.lower() for s in
                    re.findall(r'"(%[12]|[A-Za-z]:\\[^"]*)"', t)]
    return out


def fixture_pair(d: pathlib.Path, tag: str):
    """Resolve the archived fixture pair: per-tag `<tag>-L.bin`, then the
    tag's dash prefixes (V5-current -> V5), then the batch's shared pair
    (m70 wrote one B- pair for all H cells, m70d one V1- pair, m70e one
    E- pair)."""
    cands = [tag]
    parts = tag.split("-")
    cands += ["-".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]
    for t in cands:
        la, lb = d / "fixtures" / f"{t}-L.bin", d / "fixtures" / f"{t}-R.bin"
        if la.is_file() and lb.is_file():
            return la, lb
    for a, b in (("B-L.bin", "B-R.bin"), ("V1-L.bin", "V1-R.bin"),
                 ("E-L.bin", "E-R.bin"), ("V5-L.bin", "V5-R.bin")):
        la, lb = d / "fixtures" / a, d / "fixtures" / b
        if la.is_file() and lb.is_file():
            return la, lb
    return None, None


def main() -> int:
    verbose = "--verbose" in sys.argv
    total = passed = skipped = 0
    exitcells = 0
    fails = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="reacmp-hex-replay-"))
    for d in sorted(RUNS.glob("m70*-*")):
        reports = d / "reports"
        if not reports.is_dir():
            continue
        for out_file in sorted(reports.glob("*.out")):
            stem = out_file.name[:-4]
            tag, _, lay = stem.rpartition(".")
            if lay not in ("side-by-side", "interleaved", "summary"):
                tag, lay = stem, None
            bcs = out_file.parent / (out_file.name.replace(".out", ".bcs"))
            if not bcs.exists():
                skipped += 1
                continue
            script_text = bcs.read_text(encoding="utf-8", errors="replace")
            if not BCS_RE.search(script_text):
                skipped += 1
                continue
            info = parse_bcs(script_text)
            if lay not in ("side-by-side", "interleaved", "summary"):
                tag, lay = stem, None
            lay = info["layout"] or lay
            oracle_exit = 0 if out_file.stat().st_size > 0 else None
            # archived exit code: prefer the per-run JSON, else the session
            # sidecar (inline probe batches), else trust the file size
            meta = next(iter(sorted(d.glob("m6*.json")) + sorted(d.glob("m7*.json"))),
                        None)
            if meta is not None:
                try:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    if meta.name == "m70-session-exits.json":
                        oracle_exit = data.get("exits", {}).get(tag, oracle_exit)
                    else:
                        recs = data if isinstance(data, list) else data.get("results", [])
                        for rec in recs:
                            if rec.get("tag") == tag:
                                if "exit" in rec:
                                    oracle_exit = rec["exit"]
                                rr = rec.get("reports")
                                if isinstance(rr, dict):
                                    for v in rr.values():
                                        if isinstance(v, dict) and "exit" in v:
                                            oracle_exit = v["exit"]
                                break
                except (json.JSONDecodeError, AttributeError):
                    pass

            error_surface = (info["has_options"] or info["has_outopts"]
                             or lay not in ("side-by-side", "interleaved", "summary")
                             or oracle_exit not in (0, None))
            lp, rp = fixture_pair(d, tag)
            total += 1

            out = tmp / f"{d.name}.{stem}.out"
            script = tmp / f"{d.name}.{stem}.bcs"
            script.write_text(script_text, encoding="utf-8")
            files = []
            for s in info["slots"]:
                if s == "%1":
                    files.append(str(lp.resolve()) if lp else r"Z:\nope-a.bin")
                elif s == "%2":
                    files.append(str(rp.resolve()) if rp else r"Z:\nope-b.bin")
                else:
                    files.append(s)  # literal path as archived
            proc = subprocess.run(
                [str(PRODUCT), "/silent", f"@{script}"] + files + [str(out.resolve())],
                capture_output=True, timeout=120)

            if error_surface:
                exitcells += 1
                want = oracle_exit if oracle_exit is not None else proc.returncode
                wrote = out.exists() and out.stat().st_size > 0
                expect_wrote = (want == 0)
                if proc.returncode != want or wrote != expect_wrote:
                    fails.append((d.name, stem, f"exit surface: want exit {want} "
                                  f"wrote={expect_wrote}, got exit {proc.returncode} "
                                  f"wrote={wrote}"))
                continue

            if not (lp and rp):
                skipped += 1
                continue
            if not (out.exists() and out.stat().st_size > 0):
                fails.append((d.name, stem, f"product produced no report (exit "
                              f"{proc.returncode})"))
                continue
            got = fold_lines(out.read_text(encoding="utf-8-sig", errors="replace"))
            want_lines = fold_lines(
                out_file.read_text(encoding="utf-8-sig", errors="replace"))
            if got == want_lines:
                passed += 1
            else:
                fails.append((d.name, stem, "frame+body mismatch"))
                if verbose:
                    print(f"== {d.name} / {stem}")
                    for i, (a, b) in enumerate(zip(got + [""] * len(want_lines),
                                                   want_lines + [""] * len(got))):
                        if a != b:
                            print(f"  line {i}\n   product={a!r}\n   oracle ={b!r}")

    print(f"\nhex product replay: total={total} pass={passed} "
          f"fail={len(fails)} skip={skipped} (exit-surface cells={exitcells})")
    for d, stem, why in fails[:40]:
        print(f"  FAIL {d} / {stem}: {why}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

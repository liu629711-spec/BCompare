"""Drive Beyond Compare's scriptable report generation as a gold-standard oracle.

BC ships BComp.com, a console program that runs script files headlessly. The
verified invocation pattern — established by reading the official CHM scripting
reference and confirmed against error level 107 — is:

    BComp.com /silent @<script> <left> <right> <output>

where the script's `text-report` command takes the files as %1/%2 and writes to
%3. Note that `load` only accepts folders, so file comparisons must not use it.

This module turns that into a repeatable oracle: given two files and a set of
layout/option combinations, produce BC's own reports for later comparison with a
reimplementation's output.
"""
import pathlib
import subprocess
import time

BC = pathlib.Path(r"D:\bc-official\app\BComp.com")
WORK = pathlib.Path(r"D:\Rea\verify")

# All layouts BC documents for text-report.
LAYOUTS = ["side-by-side", "summary", "interleaved", "patch", "statistics", "xml"]


def run_report(left: pathlib.Path, right: pathlib.Path, out: pathlib.Path,
               layout: str = "side-by-side", options: str | None = None,
               log: pathlib.Path | None = None) -> dict:
    """Generate one BC text-report. Returns exit code, log text and output text."""
    out.parent.mkdir(parents=True, exist_ok=True)
    script = WORK / "_oracle-script.txt"

    lines = []
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        lines.append(f'log verbose "{log}"')
    option_part = f" options:{options}" if options else ""
    lines.append(f'text-report layout:{layout}{option_part} output-to:"%3" "%1" "%2"')
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")

    started = time.time()
    completed = subprocess.run(
        [str(BC), "/silent", f"@{script}", str(left), str(right), str(out)],
        capture_output=True, timeout=120,
    )
    elapsed = time.time() - started

    return {
        "exit_code": completed.returncode,
        "seconds": round(elapsed, 3),
        "stdout": completed.stdout.decode("utf-8", "replace"),
        "stderr": completed.stderr.decode("utf-8", "replace"),
        "log": log.read_text(encoding="utf-8", errors="replace") if log and log.exists() else "",
        "output_exists": out.exists(),
        "output": out.read_text(encoding="utf-8", errors="replace") if out.exists() else "",
    }


if __name__ == "__main__":
    left = WORK / "left.txt"
    right = WORK / "right.txt"
    results_dir = WORK / "oracle"
    results_dir.mkdir(exist_ok=True)

    print("BC oracle: generating reports for every documented layout\n")
    for layout in LAYOUTS:
        out = results_dir / f"report-{layout}.txt"
        log = results_dir / f"log-{layout}.txt"
        result = run_report(left, right, out, layout=layout, log=log)
        size = len(result["output"])
        print(f"  {layout:<14} exit={result['exit_code']:<3} {size:>6} bytes  {result['seconds']}s")

    # Option variations that change what lines appear.
    print("\nBC oracle: option variations (side-by-side)\n")
    for option in ["display-all", "display-mismatches", "display-context",
                   "display-matches", "ignore-unimportant"]:
        out = results_dir / f"option-{option}.txt"
        result = run_report(left, right, out, layout="side-by-side", options=option)
        size = len(result["output"])
        print(f"  {option:<20} exit={result['exit_code']:<3} {size:>6} bytes")

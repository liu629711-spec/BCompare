"""Build a persistent Ghidra project for BCompare, then decompile any function instantly.

REA's Ghidra provider re-imports and re-analyzes the target on every call
(`ephemeral-source-immutable` + `-deleteProject`), which costs ~25-33 minutes each
time. A plain Ghidra project keeps the analyzed database on disk, so analysis is
paid once and later queries are seconds.

This driver does two things:
  build   -- create/analyze the project (one time, ~15-20 min)
  decompile <address> -- dump one function's C to a file (seconds)

Only Ghidra's own analyzeHeadless is used here; REA is not involved, which is
exactly why the analysis survives between invocations.
"""
import argparse
import pathlib
import subprocess
import sys
import time

GHIDRA = pathlib.Path(r"D:\Ghidra\ghidra_12.1.4_PUBLIC")
HEADLESS = GHIDRA / "support" / "analyzeHeadless.bat"
TARGET = pathlib.Path(r"D:\bc-official\app\BCompare.exe")
PROJECT_DIR = pathlib.Path(r"D:\Rea\ghidra-project")
PROJECT_NAME = "bcompare"
SCRIPTS = pathlib.Path(r"D:\Rea\tools\ghidra-scripts")


def run_headless(args: list[str], timeout: int) -> int:
    command = [str(HEADLESS), str(PROJECT_DIR), PROJECT_NAME, *args]
    print(f"[{time.strftime('%H:%M:%S')}] {' '.join(command[:6])} ...", flush=True)
    started = time.time()
    completed = subprocess.run(command, timeout=timeout)
    print(f"[{time.strftime('%H:%M:%S')}] exit={completed.returncode} in {time.time() - started:.0f}s", flush=True)
    return completed.returncode


def build() -> int:
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    return run_headless(["-import", str(TARGET)], timeout=5400)


def decompile(address: str, out_path: pathlib.Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "DumpDecomp.java", address, str(out_path),
    ], timeout=900)


def function_list(out_path: pathlib.Path) -> int:
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "ListFunctions.java", str(out_path),
    ], timeout=1800)


def string_index(out_path: pathlib.Path, min_length: int = 6) -> int:
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "BuildStringIndex.java", str(out_path), str(min_length),
    ], timeout=3600)


def batch_decompile(address_file: pathlib.Path, out_dir: pathlib.Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "BatchDecompile.java", str(out_dir), str(address_file),
    ], timeout=7200)


def read_pointers(pairs: list[str], out_path: pathlib.Path) -> int:
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "ReadPointers.java", str(out_path), *pairs,
    ], timeout=900)


def follow_pointers(addresses: list[str], out_path: pathlib.Path) -> int:
    return run_headless([
        "-process", TARGET.name,
        "-noanalysis",
        "-scriptPath", str(SCRIPTS),
        "-postScript", "FollowPointers.java", str(out_path), *addresses,
    ], timeout=900)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="create and analyze the persistent project")
    dec = sub.add_parser("decompile", help="dump one function as C")
    dec.add_argument("address")
    dec.add_argument("--out", default=None)
    fns = sub.add_parser("list-functions", help="export all function names and entry points")
    fns.add_argument("--out", default=r"D:\Rea\extracted\functions.tsv")
    bat = sub.add_parser("batch", help="decompile every function listed in a file")
    bat.add_argument("address_file")
    bat.add_argument("--out-dir", default=r"D:\Rea\extracted\pseudocode")
    ptr = sub.add_parser("read-pointers", help="resolve data locations and their vtables")
    ptr.add_argument("pairs", nargs="+", help="label=address")
    ptr.add_argument("--out", default=r"D:\Rea\extracted\pointers.txt")
    fp = sub.add_parser("follow-pointers", help="follow pointer chains and dump vtables")
    fp.add_argument("addresses", nargs="+")
    fp.add_argument("--out", default=r"D:\Rea\extractedollowed-pointers.txt")
    idx = sub.add_parser("string-index", help="map every string to its referencing functions")
    idx.add_argument("--out", default=r"D:\Rea\extracted\string-function-index.tsv")
    idx.add_argument("--min-length", type=int, default=6)

    args = parser.parse_args()
    if args.command == "build":
        return build()
    if args.command == "decompile":
        out = pathlib.Path(args.out) if args.out else pathlib.Path(rf"D:\Rea\extracted\pseudocode\{args.address}.c")
        return decompile(args.address, out)
    if args.command == "list-functions":
        return function_list(pathlib.Path(args.out))
    if args.command == "string-index":
        return string_index(pathlib.Path(args.out), args.min_length)
    if args.command == "follow-pointers":
        return follow_pointers(args.addresses, pathlib.Path(args.out))
    if args.command == "read-pointers":
        return read_pointers(args.pairs, pathlib.Path(args.out))
    if args.command == "batch":
        return batch_decompile(pathlib.Path(args.address_file), pathlib.Path(args.out_dir))
    return 2


if __name__ == "__main__":
    sys.exit(main())

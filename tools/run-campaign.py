"""Run the full reverse-engineering campaign batch queue.

Processes every batch file produced by build-campaign.py in order, invoking
Ghidra once per batch and updating a progress ledger after each one. Designed to
run unattended for hours: failures are logged and skipped, completed batches are
never repeated, and the ledger is the resumable state.

Usage:  python tools/run-campaign.py [--phase 01-foundation] [--dry-run]
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(r"D:\Rea")
QUEUE = ROOT / "extracted" / "campaign"
OUT = ROOT / "extracted" / "pseudocode"
LEDGER = QUEUE / "progress.json"
DRIVER = ROOT / "tools" / "ghidra-persistent.py"


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"completed": {}, "failed": {}}


def save_ledger(ledger: dict) -> None:
    ledger["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")


def run_batch(batch: pathlib.Path, out_dir: pathlib.Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(DRIVER), "batch", str(batch), "--out-dir", str(out_dir)],
        capture_output=True, timeout=3600,
    )
    output = result.stdout.decode("utf-8", "replace") + result.stderr.decode("utf-8", "replace")
    ok = result.returncode == 0 and "decompiled" in output
    return ok, output[-1200:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default=None, help="only run batches of this phase")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    batches = sorted(QUEUE.glob("*-batch*.txt"))
    if args.phase:
        batches = [b for b in batches if b.name.startswith(args.phase)]
    if not batches:
        print("no batches to run")
        return 1

    ledger = load_ledger()
    print(f"campaign: {len(batches)} batches, {len(ledger['completed'])} already done")

    for number, batch in enumerate(batches, 1):
        key = batch.name
        if key in ledger["completed"]:
            print(f"[{number}/{len(batches)}] {key}: already completed, skipping")
            continue

        started = time.time()
        if args.dry_run:
            count = len([l for l in batch.read_text(encoding="utf-8").splitlines() if l.strip()])
            print(f"[{number}/{len(batches)}] {key}: {count} items (dry run)")
            continue

        ok, output = run_batch(batch, OUT)
        elapsed = time.time() - started
        if ok:
            ledger["completed"][key] = {"seconds": round(elapsed), "at": time.strftime("%H:%M:%S")}
            print(f"[{number}/{len(batches)}] {key}: ok in {elapsed:.0f}s")
        else:
            ledger["failed"][key] = {"at": time.strftime("%H:%M:%S"), "tail": output}
            print(f"[{number}/{len(batches)}] {key}: FAILED\n{output}")
        save_ledger(ledger)

    total_files = len(list(OUT.glob("*.c")))
    print(f"\ncampaign status: {total_files} pseudocode files on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

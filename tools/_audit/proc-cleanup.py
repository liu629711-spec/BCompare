"""Total-control cleanup: stop ONLY the stuck harness processes.

Safety: matches on command line, not just image name, and requires the command
line to reference this project's harness/temp paths. Unrelated BCompare
processes the user may be running are left alone.

Default is dry-run; pass --apply to actually stop.
"""
from __future__ import annotations

import argparse
import json
import subprocess

PS_LIST = r"""
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'BComp|python' } |
  Select-Object ProcessId, ParentProcessId, Name, CommandLine |
  ConvertTo-Json -Depth 3
"""

# Our harness invocations always reference one of these.
MARKERS = ("reflay-", "pytest-of-", "product\\verify", "product/verify",
           "verify\\layouts", "verify/layouts", "verify\\golden", "verify/golden")
PYTEST_MARKER = "pytest product/verify/tests"


def snapshot() -> list[dict]:
    cp = subprocess.run(["powershell", "-NoProfile", "-Command", PS_LIST],
                        capture_output=True, text=True, timeout=90)
    out = cp.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    return data if isinstance(data, list) else [data]


def classify(procs: list[dict]) -> tuple[list[dict], list[dict]]:
    mine, other = [], []
    for p in procs:
        cmd = p.get("CommandLine") or ""
        if p["Name"] == "python.exe":
            (mine if PYTEST_MARKER in cmd else other).append(p)
        elif any(m in cmd for m in MARKERS):
            mine.append(p)
        else:
            other.append(p)
    return mine, other


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually stop them")
    args = ap.parse_args()

    procs = snapshot()
    mine, other = classify(procs)

    print(f"total BComp/python processes: {len(procs)}")
    print(f"  ours (harness/pytest) : {len(mine)}")
    print(f"  unrelated (left alone) : {len(other)}")
    print()
    for p in mine:
        print(f"  [{p['Name']}] pid={p['ProcessId']} ppid={p['ParentProcessId']}")
        print(f"      {(p.get('CommandLine') or '')[:150]}")
    for p in other:
        print(f"  [UNRELATED, keep] pid={p['ProcessId']} {p['Name']} "
              f"{(p.get('CommandLine') or '')[:80]}")

    if not args.apply:
        print("\n(dry run; re-run with --apply to stop the 'ours' list)")
        return 0

    # Kill children first (BCompare.exe), then parents.
    for p in sorted(mine, key=lambda x: x["Name"] != "BCompare.exe"):
        subprocess.run(["taskkill", "/PID", str(p["ProcessId"]), "/F", "/T"],
                       capture_output=True, text=True, timeout=60)
        print(f"  stopped pid={p['ProcessId']} {p['Name']}")

    print("\nremaining:")
    for p in snapshot():
        print(f"  {p['Name']} pid={p['ProcessId']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

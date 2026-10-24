"""Total-control diagnostic: snapshot the BC/python process tree.

Read-only. Writes nothing outside stdout.
"""
from __future__ import annotations

import subprocess

PS = r"""
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'BComp|python|pytest' } |
  Select-Object ProcessId, ParentProcessId, Name, CreationDate, CommandLine |
  ConvertTo-Json -Depth 3
"""


def main() -> int:
    cp = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                        capture_output=True, text=True, timeout=60)
    print(cp.stdout.strip() or "(no matching processes)")
    if cp.stderr.strip():
        print("STDERR:", cp.stderr.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

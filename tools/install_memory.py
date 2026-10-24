#!/usr/bin/env python3
"""Install the repo-shipped ZCode memory (memory-export/*.md) into this
machine's ZCode persistent-memory directory for the workspace it runs in.

Why this exists: the memory files live OUTSIDE the git repo on the original
device (C:\\Users\\<user>\\.zcode\\...). On a new device you cannot copy them
from a user-profile dir — so they were committed under memory-export/, and
this script places them where ZCode expects them.

The destination folder name is `rea-<hash>`, derived from the WORKSPACE PATH
(we reproduce ZCode's project-key convention: sha256 over the normalized
workspace path; if the existing convention differs, the script FALLS BACK to
writing memory-export/ contents next to an auto-created .zcode/memories/
workspace directory AND prints where it put them, so nothing is lost).

Run from anywhere inside the repo:  python tools/install_memory.py [D:\\Rea]
Idempotent: overwrites same-name files, never deletes foreign ones.
"""
import hashlib
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT = ROOT / "memory-export"


def workspace_key(ws: pathlib.Path) -> str:
    # ZCode project-dir convention observed on the source device:
    #   projects/<name>-<16hex>  e.g. rea-7a160a47489c005e
    # name = workspace folder lowercased; hash = first 16 of sha256 over the
    # normalized path (backslashes, no trailing sep, lowercased drive).
    norm = str(ws).replace("\\", "/").rstrip("/").lower()
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def main() -> int:
    ws = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    home = pathlib.Path.home()
    cand = home / ".zcode" / "cli" / "memories" / "projects"
    # if this workspace already has a keyed dir (e.g. cloned to D:\Rea on a
    # same-path device), reuse it — the hash rule is best-effort
    target = None
    name_guess = ws.name.lower()
    if cand.exists():
        for d in cand.iterdir():
            if d.name == f"{name_guess}-{workspace_key(ws)}":
                target = d / "memory"
                break
        if target is None:
            # any existing key starting with the workspace name wins (the
            # machine already knows this project)
            for d in sorted(cand.iterdir()):
                if d.name.startswith(name_guess + "-"):
                    target = d / "memory"
                    break
    if target is None:
        target = cand / f"{name_guess}-{workspace_key(ws)}" / "memory"
    target.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(EXPORT.glob("*.md")):
        shutil.copy2(f, target / f.name)
        n += 1
    print(f"installed {n} memory files -> {target}")
    print("restart the ZCode session on this device for them to load.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Reconstruct the third-party binary test fixtures from a LOCAL install.

The committed repo deliberately excludes every byte-for-byte copy of a
non-owned binary (verify/FIXTURE-MANIFEST.json lists them by sha256):
  * BCompare.exe / BComp.com copies — the Oracle's own binaries, used
    VERBATIM as version-compare fixtures ("the Oracle measured these exact
    bytes"; see product/docs/18, product/verify/tools/m112_add_ver_goldens.py);
  * cmd.exe / notepad.exe copies from C:\Windows\System32;
  * tools/ghidra/ghidra_11.2.1.zip (OSS download, fetch from
    https://github.com/NationalSecurityAgency/ghidra/releases).

This script copies them back from the local reference installs so the
replay harness works after a fresh clone. It NEVER touches the network and
copies are byte-verified against the manifest sha256.

Usage:  python tools/fetch_fixtures.py          # restore all
        python tools/fetch_fixtures.py --verify # hash-check only, no writes
        python tools/fetch_fixtures.py --source BCompare-official="E:\path\BCompare.exe"
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "verify", "FIXTURE-MANIFEST.json")

# source keys -> local candidate paths (first existing wins; --source
# KEY=PATH appends the caller's path to the front of its list)
SOURCES = {
    "BCompare-5.2.6": [r"D:\BCompare\BCompare\BCompare.exe"],
    "BCompare-official": [r"D:\bc-official\app\BCompare.exe"],
    "BComp.com": [r"D:\BCompare\BCompare\BComp.com"],
    "cmd.exe": [r"C:\Windows\System32\cmd.exe"],
    "notepad.exe": [r"C:\Windows\System32\notepad.exe"],
}


def parse_source_overrides(argv):
    for i, a in enumerate(argv):
        if a == "--source" and i + 1 < len(argv):
            key, _, path = argv[i + 1].partition("=")
            if key in SOURCES and path:
                SOURCES[key].insert(0, path)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    parse_source_overrides(sys.argv)
    verify_only = "--verify" in sys.argv
    entries = json.load(open(MANIFEST, encoding="utf-8"))
    missing_src = {}
    ok = copied = bad = already = 0
    for rel, meta in entries.items():
        target = os.path.join(ROOT, rel.replace("/", os.sep))
        want = meta["sha256"]
        if want is None:  # ghidra zip: document, don't fetch
            print(f"[download] {rel}: fetch ghidra 11.2.1 release zip manually")
            continue
        if os.path.exists(target) and sha(target) == want:
            already += 1
            continue
        if verify_only:
            bad += 1
            print(f"[MISSING] {rel} (source {meta['source']})")
            continue
        src = next((p for p in SOURCES.get(meta["source"], []) if os.path.exists(p)), None)
        if not src:
            missing_src.setdefault(meta["source"], []).append(rel)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(src, target)
        if sha(target) == want:
            copied += 1
        else:
            os.remove(target)
            bad += 1
            print(f"[BAD HASH after copy] {rel} from {src}", file=sys.stderr)
    print(f"fixtures: {already} present+verified, {copied} restored, {bad} failed")
    for k, v in missing_src.items():
        print(f"[NO LOCAL SOURCE] {k}: {len(v)} files (install the reference at "
              f"{SOURCES[k]} or re-produce via the m112 harness)", file=sys.stderr)
    return 0 if not (bad or missing_src) else 1


if __name__ == "__main__":
    sys.exit(main())

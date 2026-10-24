#!/usr/bin/env python3
"""U4 probe -- the five unlocked folder criteria (task: open criteria round).

`version`, `owner`, `group`, `permissions`, `ignore-unimportant` are accepted
by the live Oracle (exit 0, observed in `A3-folder-gate-serial-04`) but the
product refuses them as not-probed.  This probe pins each one's observable
semantics before implementation:

  * **version** -- folder criteria acting on a .dll whose PE version resource
    differs between sides; does the file row flip to `diff`, and does the
    comparison ignore size/timestamp while it does?
  * **owner / group** -- the help says "Unix owner/group".  On Windows these
    may be inert.  Probe with a file whose NTFS owner is SYSTEM (D:\\ has
    system-owned files we can reference read-only... actually we need WRITABLE
    fixtures, so we test: (a) a copy with a different ARCHIVE bit; (b) whether
    an ACL difference (deny ACE) changes the row).  Since `icacls /setowner`
    needs elevation, owner differences are made only if possible; otherwise
    the probe records that the observable surface is inert on Windows.
  * **permissions** -- an ACL difference (extra deny ACE) on one side only.
  * **ignore-unimportant** -- a pair that differs only in a way that is
    "unimportant" for folders (empty dir vs missing dir? a file whose content
    differs but size/timestamp criteria are off?) plus the report element.

Everything runs serially through `harness.oracle` (in-place cwd, Job Object,
timeout).  Raw outputs land in `product/verify/runs/u4-probe-<ts>/`.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4_folder_criteria.py
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: (case name, criteria string, extra setup key).  Setup functions build the
#: L/R trees; keep every tree tiny and self-describing.
STATUS_RE = re.compile(r'<filecomp status="([a-z]+)">|(<filecomp>)')


def write_tree(root: pathlib.Path, files: dict[str, bytes], dirs: list[str] = ()) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def set_version_resource(path: pathlib.Path, version: str) -> None:
    """Rewrite the fixed file-info version fields of a PE without a resource
    compiler: locate the VS_FIXEDFILEINFO (0xFEEF04BD) inside the version
    resource and patch its four version words."""
    data = bytearray(path.read_bytes())
    sig = struct.pack("<I", 0xFEEF04BD)
    i = data.find(sig)
    if i < 0:
        raise SystemExit(f"no VS_FIXEDFILEINFO in {path}")
    parts = [int(x) for x in version.split(".")]
    for k, part in enumerate(parts[:4]):
        struct.pack_into("<H", data, i + 8 + k * 4, part)      # FileVersionMS/LS words
        struct.pack_into("<H", data, i + 16 + k * 4, part)     # ProductVersionMS/LS words
    path.write_bytes(bytes(data))


def icacls_deny_everyone(path: pathlib.Path) -> bool:
    r = subprocess.run(
        ["icacls", str(path), "/deny", "*S-1-1-0:(R)"],
        capture_output=True, text=True)
    return r.returncode == 0


def icacls_setowner_system(path: pathlib.Path) -> bool:
    r = subprocess.run(
        ["icacls", str(path), "/setowner", "SYSTEM"],
        capture_output=True, text=True)
    return r.returncode == 0


CASES: list[tuple[str, str, str]] = [
    ("version-default-baseline", "", "same files, no criteria"),
    ("version-dll-only", "version", "dll versions differ; sizes/timestamps equal"),
    ("version-dll-size-differs", "version", "dll versions differ AND sizes differ"),
    ("owner-equal-files", "owner", "identical files, same owner"),
    ("group-equal-files", "group", "identical files, same group"),
    ("permissions-equal-files", "permissions", "identical files, same ACL"),
    ("permissions-acl-differs", "permissions", "one side has an extra deny ACE"),
    ("ignore-unimportant-empty-vs-missing", "ignore-unimportant",
     "empty dir on both sides vs one missing"),
    ("ignore-unimportant-on-default", "ignore-unimportant",
     "baseline tree, default criteria plus ignore-unimportant"),
    ("version-plus-size", "version size", "dll versions differ, both tokens given"),
]


def build_fixture(name: str, root: pathlib.Path) -> None:
    """Create the L/R trees for one probe."""
    left = root / "L"
    right = root / "R"
    if name.startswith("version-"):
        # A tiny valid PE: copy a real system DLL? No -- keep it local and
        # writable: use a synthetic file with a genuine VS_FIXEDFILEINFO.
        base = _synthetic_versioned_dll()
        write_tree(left, {"app.dll": base})
        write_tree(right, {"app.dll": base})
        set_version_resource(right / "app.dll", "9.9.9.9")
        if name == "version-dll-size-differs":
            with (right / "app.dll").open("ab") as f:
                f.write(b"\x00" * 16)
    elif name == "permissions-acl-differs":
        write_tree(left, {"x.txt": b"same"})
        write_tree(right, {"x.txt": b"same"})
        if not icacls_deny_everyone(right / "x.txt"):
            raise SystemExit("cannot set deny ACE (need rights on the fixture dir)")
    elif name in ("owner-equal-files", "group-equal-files", "permissions-equal-files"):
        write_tree(left, {"x.txt": b"same"})
        write_tree(right, {"x.txt": b"same"})
    elif name == "ignore-unimportant-empty-vs-missing":
        write_tree(left, {}, dirs=["emptydir"])
        write_tree(right, {})
    else:  # baselines / ignore-unimportant-on-default
        write_tree(left, {"x.txt": b"same"})
        write_tree(right, {"x.txt": b"same"})


def _synthetic_versioned_dll() -> bytes:
    """The smallest blob that carries a real VS_FIXEDFILEINFO signature.

    BC's version reader keys on the resource layout; whether it accepts this
    synthetic blob is part of what the probe learns.  If it does not, the
    probe's `version-*` rows will be `same`, which is itself evidence (and the
    alternative -- a real signed DLL copy -- may not be writable here).
    """
    src = pathlib.Path(r"D:\BCompare\BCompare\BCompare.exe")
    if src.is_file():
        # Prefer a real PE whose version resource BC surely reads; copy a
        # *small* system DLL instead of the 30 MB exe to keep runs fast.
        for cand in (r"C:\Windows\System32\version.dll", r"C:\Windows\System32\winver.exe"):
            p = pathlib.Path(cand)
            if p.is_file() and p.stat().st_size < 8_000_000:
                return p.read_bytes()
    raise SystemExit("no source PE found for the version probe")


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    print(f"run dir: {run_dir}\n")

    records = []
    for name, criteria, desc in CASES:
        root = run_dir / "fixtures" / name
        try:
            build_fixture(name, root)
        except SystemExit as e:
            print(f"  {name:<38} SKIP: {e}")
            records.append({"probe": name, "criteria": criteria, "desc": desc,
                            "skipped": str(e)})
            continue
        left, right = root / "L", root / "R"
        out = run_dir / "reports" / f"{name}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{left}" "{right}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(cur.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        records.append({"probe": name, "criteria": criteria, "desc": desc,
                        "exit": run.exit_code, "statuses": statuses,
                        "report_bytes": len(body),
                        "containment": run.containment})
        print(f"  {name:<38} exit={run.exit_code} bytes={len(body):<6} statuses={statuses}")

    (run_dir / "u4-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw results: {run_dir / 'u4-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

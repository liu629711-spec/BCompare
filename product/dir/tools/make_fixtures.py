#!/usr/bin/env python3
"""Generate the M3 folder-comparison fixture corpus.

Deterministic by construction:

* every file's **modification time is set explicitly** from a fixed epoch, so the
  corpus does not depend on when it was built (the default criteria compares
  timestamps, so a drifting mtime would change the verdicts);
* directory mtimes are set last, after their children, because creating a child
  updates its parent's mtime;
* file bytes are literals from the spec below.

Run:

    python D:\\Rea\\product\\dir\\tools\\make_fixtures.py            # create/refresh
    python D:\\Rea\\product\\dir\\tools\\make_fixtures.py --check     # verify only

`--check` reports any file whose content or mtime differs from the spec and exits
non-zero; the fixture runner uses it to detect a drifted corpus.

Everything this script writes lives under `D:\\Rea\\product\\dir\\fixtures\\`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
TREES = FIXTURES / "trees"

# Fixed epoch so every rendered `<modified>` is stable. 2026-01-01 00:00:00 UTC.
# Chosen after the fixtures used by the audit (2026-10-13) so an accidental mix
# with those read-only trees cannot be mistaken for a match.
EPOCH = 1_767_225_600

# Offsets in seconds from EPOCH, named so the spec reads as behaviour.
T0 = 0                # base
T_PLUS_30 = 30        # inside a 60 s tolerance
T_PLUS_60 = 60        # exactly at a 60 s tolerance boundary
T_PLUS_3600 = 3600    # exactly 1 hour (the documented IgnoreDST case)
T_PLUS_7200 = 7200    # 2 hours (outside IgnoreDST)
T_OLD = -86400        # one day earlier


#: The real, structurally valid PE the `versioned` tree is built from.
#:
#: U4h measured that the Oracle requires a genuine PE with a resource
#: directory: a synthetic blob carrying only the VS_FIXEDFILEINFO signature is
#: treated as version-less (every row `same`), while a real system DLL with the
#: same patched version fields reports `ltnewer`/`rtnewer`. Generation
#: therefore patches a real DLL, so the fixture exercises the comparison rather
#: than the reader's tolerance.
VERSION_BASE_PE = pathlib.Path("C:/Windows/System32/version.dll")


def _pe_blob(fv: tuple[int, int, int, int], pv: tuple[int, int, int, int]) -> bytes:
    """A real PE whose FileVersion/ProductVersion are the given values."""
    import struct

    src = VERSION_BASE_PE
    if not src.is_file():
        raise SystemExit(
            f"the versioned fixture needs a real PE base at {src}; the Oracle "
            "ignores version resources outside a valid PE (U4h)"
        )
    data = bytearray(src.read_bytes())
    sig = (0xFEEF04BD).to_bytes(4, "little")
    i = data.find(sig)
    if i < 0:
        raise SystemExit(f"{src} has no VS_FIXEDFILEINFO")
    ms = (fv[0] << 16) | fv[1]
    ls = (fv[2] << 16) | fv[3]
    pms = (pv[0] << 16) | pv[1]
    pls = (pv[2] << 16) | pv[3]
    struct.pack_into("<I", data, i + 8, ms)
    struct.pack_into("<I", data, i + 12, ls)
    struct.pack_into("<I", data, i + 16, pms)
    struct.pack_into("<I", data, i + 20, pls)
    return bytes(data)


def file_node(data: bytes, mtime: int) -> dict:
    return {"kind": "file", "data": data, "mtime": EPOCH + mtime}


def dir_node(mtime: int, children: dict) -> dict:
    return {"kind": "dir", "mtime": EPOCH + mtime, "children": children}


def junction_node(target: str, mtime: int) -> dict:
    return {"kind": "junction", "target": target, "mtime": EPOCH + mtime}


def _write_tree(root: pathlib.Path, spec: dict) -> list[str]:
    """Create one tree; return the relative paths written, deepest last."""
    problems: list[str] = []
    dirs_to_stamp: list[tuple[pathlib.Path, int]] = []

    def walk(node: dict, path: pathlib.Path, rel: str) -> None:
        for name, child in sorted(node["children"].items()):
            child_path = path / name
            child_rel = f"{rel}/{name}" if rel else name
            if child["kind"] == "dir":
                child_path.mkdir(parents=True, exist_ok=True)
                walk(child, child_path, child_rel)
                dirs_to_stamp.append((child_path, child["mtime"]))
            elif child["kind"] == "file":
                existing = child_path.read_bytes() if child_path.is_file() else None
                if existing != child["data"]:
                    child_path.parent.mkdir(parents=True, exist_ok=True)
                    child_path.write_bytes(child["data"])
                os.utime(child_path, (child["mtime"], child["mtime"]))
            elif child["kind"] == "junction":
                if not _is_junction(child_path):
                    child_path.parent.mkdir(parents=True, exist_ok=True)
                    _make_junction(child_path, child["target"])
            else:
                problems.append(f"{child_rel}: unknown node kind {child['kind']!r}")

    root.mkdir(parents=True, exist_ok=True)
    walk(spec, root, "")

    # Parents last: writing a child bumps the parent's mtime, so stamping the
    # directory before its contents would silently lose the intended value.
    for path, mtime in sorted(dirs_to_stamp, key=lambda p: -len(p[0].parts)):
        os.utime(path, (mtime, mtime))
    return problems


def _is_junction(path: pathlib.Path) -> bool:
    """True when `path` exists and is a reparse point (junction or symlink).

    `os.path.islink` is **false** for an NTFS junction in this Python build
    (measured), so the reparse-point attribute bit is the reliable probe. Using
    only `islink` made `make_fixtures.py --check` try to re-create existing
    junctions, which then failed with "Cannot create a file when that file
    already exists".
    """
    try:
        st = os.lstat(path)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", 0)
    if attrs & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
        return True
    return os.path.islink(path)


def _make_junction(link: pathlib.Path, target: pathlib.Path) -> None:
    """Create an NTFS junction.

    A junction rather than a symbolic link because creating a symlink needs
    `SeCreateSymbolicLinkPrivilege`, which this host does not grant (measured:
    WinError 1314). A junction needs no privilege, and BC's documented
    `follow-symlinks` covers "symbolic links **and NTFS junctions**"
    (help/scripting_reference.html, CRITERIA) — so it exercises the same
    behaviour.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        raise RuntimeError(f"junction target does not exist: {target}")
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"could not create junction {link} -> {target}: "
            f"{result.stdout.strip()} {result.stderr.strip()}"
        )


# ---------------------------------------------------------------------------
# The corpus. Each entry is a tree pair; cases (below) attach criteria to them.
# ---------------------------------------------------------------------------

def build_trees() -> dict[str, dict]:
    """Return {pair_name: {"L": spec, "R": spec, "note": str}}."""

    trees: dict[str, dict] = {}

    # ---- baseline: every top-level status the report vocabulary has ----------
    trees["baseline"] = {
        "note": "one entry per top-level status token",
        "L": dir_node(T0, {
            "diff.txt": file_node(b"aaaa\r\n", T0),
            "same.txt": file_node(b"hello\r\n", T0),
            "leftonly.txt": file_node(b"only left\r\n", T0),
            "leftnewer.txt": file_node(b"payload\r\n", T_PLUS_3600),
            "older.txt": file_node(b"payload\r\n", T_OLD),
            "sub": dir_node(T0, {"inner.txt": file_node(b"x\r\n", T0)}),
            "emptydir_here": dir_node(T0, {}),
        }),
        "R": dir_node(T0, {
            "diff.txt": file_node(b"bbbb\r\n", T0),
            "same.txt": file_node(b"hello\r\n", T0),
            "rightonly.txt": file_node(b"only right\r\n", T0),
            "leftnewer.txt": file_node(b"payload\r\n", T0),
            "older.txt": file_node(b"payload\r\n", T0),
            "sub": dir_node(T0, {"inner.txt": file_node(b"x\r\n", T0)}),
            "emptydir_here": dir_node(T0, {}),
            "emptydir_other": dir_node(T0, {}),
        }),
    }
    trees["baseline"]["R"]["children"]["same.txt"] = file_node(b"hello\r\n", T0)

    # ---- criteria: the audit's exact shape (same size + same mtime, content
    #      differs) plus controls that must NOT be judged different -----------
    trees["criteria"] = {
        "note": "same-size+same-mtime content difference, with controls",
        "L": dir_node(T0, {
            "samesize_text.txt": file_node(b"aaaa\r\n", T0),
            "samesize_bin.bin": file_node(bytes([1, 2, 3, 4]), T0),
            "identical.txt": file_node(b"identical\r\n", T0),
            "sizediffers.txt": file_node(b"short\r\n", T0),
        }),
        "R": dir_node(T0, {
            "samesize_text.txt": file_node(b"bbbb\r\n", T0),
            "samesize_bin.bin": file_node(bytes([1, 2, 3, 5]), T0),
            "identical.txt": file_node(b"identical\r\n", T0),
            "sizediffers.txt": file_node(b"a much longer payload\r\n", T0),
        }),
    }

    # ---- tolerance: 30 s / 60 s / 1 h / 2 h differences ---------------------
    trees["tolerance"] = {
        "note": "timestamp differences at and around the documented tolerances",
        "L": dir_node(T0, {
            "d30.txt": file_node(b"x", T0),
            "d60.txt": file_node(b"x", T0),
            "d3600.txt": file_node(b"x", T0),
            "d7200.txt": file_node(b"x", T0),
            "d0.txt": file_node(b"x", T0),
        }),
        "R": dir_node(T0, {
            "d30.txt": file_node(b"x", T_PLUS_30),
            "d60.txt": file_node(b"x", T_PLUS_60),
            "d3600.txt": file_node(b"x", T_PLUS_3600),
            "d7200.txt": file_node(b"x", T_PLUS_7200),
            "d0.txt": file_node(b"x", T0),
        }),
    }

    # ---- deep: nesting beyond the legacy MAX_PATH limit ---------------------
    # A factory rather than a shared literal: `dict(deep)` is a *shallow* copy, so
    # both sides would share the same nested dictionaries and editing the right
    # side's leaf silently edited the left side's too (measured: that made both
    # sides `DIFFERENT` and every expected `diff` came out `same`).
    def deep_chain(leaf_bytes: bytes) -> dict:
        root: dict = {}
        node = root
        for i in range(12):
            key = "level_%02d" % i
            node[key] = dir_node(T0, {})
            node = node[key]["children"]
        node["leaf.txt"] = file_node(leaf_bytes, T0)
        return root

    trees["deep"] = {
        "note": "12 levels of nesting; the leaf path exceeds the legacy MAX_PATH",
        "L": dir_node(T0, deep_chain(b"deep")),
        # The right side's leaf differs in size, so the difference aggregates up
        # through all twelve directories.
        "R": dir_node(T0, deep_chain(b"DIFFERENT")),
    }

    # ---- empty: empty directories on both sides and on one side -------------
    trees["empty"] = {
        "note": "empty directories: present on both sides, and on one side only",
        "L": dir_node(T0, {
            "empty_both": dir_node(T0, {}),
            "empty_left": dir_node(T0, {}),
            "nonempty": dir_node(T0, {"f.txt": file_node(b"x", T0)}),
        }),
        "R": dir_node(T0, {
            "empty_both": dir_node(T0, {}),
            "empty_right": dir_node(T0, {}),
            "nonempty": dir_node(T0, {"f.txt": file_node(b"x", T0)}),
        }),
    }

    # ---- conflict: the same name is a file on one side, a directory on the other
    trees["conflict"] = {
        "note": "same-name file-versus-directory conflicts",
        "L": dir_node(T0, {
            "name": file_node(b"i am a file", T0),
            "other": dir_node(T0, {"deep.txt": file_node(b"x", T0)}),
        }),
        "R": dir_node(T0, {
            "name": dir_node(T0, {"inside.txt": file_node(b"x", T0)}),
            "other": file_node(b"now a file", T0),
        }),
    }

    # ---- many: enough siblings that a hand-written expectation would be unwise
    many_l: dict = {}
    many_r: dict = {}
    for i in range(60):
        name = f"f{i:03d}.txt"
        many_l[name] = file_node(f"payload {i}\n".encode(), T0)
        # Every third file is left-only, every fourth right-only, and every
        # seventh differs in size — a mix that exercises alignment at scale.
        if i % 3 == 0:
            continue
        if i % 4 == 0:
            many_r[f"r{i:03d}.txt"] = file_node(f"right {i}\n".encode(), T0)
            continue
        if i % 7 == 0:
            many_r[name] = file_node(f"payload {i} longer\n".encode(), T0)
        else:
            many_r[name] = file_node(f"payload {i}\n".encode(), T0)
    trees["many"] = {
        "note": "60 siblings with a mix of same, diff, ltonly and rtonly rows",
        "L": dir_node(T0, many_l),
        "R": dir_node(T0, many_r),
    }

    # ---- attributes: hidden / read-only / system differences ---------------
    trees["attributes"] = {
        "note": "DOS attribute differences (attrib: criteria only)",
        "L": dir_node(T0, {
            "hidden_left.txt": file_node(b"same bytes", T0),
            "readonly_both.txt": file_node(b"same bytes", T0),
            "system_left.txt": file_node(b"same bytes", T0),
            "plain.txt": file_node(b"same bytes", T0),
        }),
        "R": dir_node(T0, {
            "hidden_left.txt": file_node(b"same bytes", T0),
            "readonly_both.txt": file_node(b"same bytes", T0),
            "system_left.txt": file_node(b"same bytes", T0),
            "plain.txt": file_node(b"same bytes", T0),
        }),
    }
    trees["attributes"]["_attributes"] = {
        # (relative path, side) -> the attributes to apply with `attrib`
        "hidden": [("L/hidden_left.txt", True)],
        "system": [("L/system_left.txt", True)],
        "readonly": [("L/readonly_both.txt", True), ("R/readonly_both.txt", True)],
    }

    # ---- links: junctions ------------------------------------------------
    trees["links"] = {
        "note": "NTFS junctions; BC documents follow-symlinks as covering junctions too",
        "L": dir_node(T0, {
            "real_dir": dir_node(T0, {"inside.txt": file_node(b"payload", T0)}),
            "plainfile.txt": file_node(b"payload", T0),
        }),
        "R": dir_node(T0, {
            "real_dir": dir_node(T0, {"inside.txt": file_node(b"payload", T0)}),
            "plainfile.txt": file_node(b"payload", T0),
        }),
        "_junctions": [
            # A junction to the sibling directory, present on both sides.
            ("L/link_to_dir", "real_dir"),
            ("R/link_to_dir", "real_dir"),
            # A junction present on the left only.
            ("L/link_left_only", "real_dir"),
        ],
    }

    # ---- orphan-dirs: one-sided directory trees --------------------------
    trees["orphan-dirs"] = {
        "note": "directory present on one side only, with nested content",
        "L": dir_node(T0, {
            "shared": dir_node(T0, {"a.txt": file_node(b"a", T0)}),
            "left_tree": dir_node(T0, {
                "nested": dir_node(T0, {"deep.txt": file_node(b"deep", T0)}),
                "top.txt": file_node(b"top", T0),
            }),
        }),
        "R": dir_node(T0, {
            "shared": dir_node(T0, {"a.txt": file_node(b"a", T0)}),
            "right_tree": dir_node(T0, {
                "nested": dir_node(T0, {"deep.txt": file_node(b"deep", T0)}),
            }),
        }),
    }

    # ---- names: characters that stress XML escaping ----------------------
    # Two platform constraints were measured while building this pair, and both
    # are recorded because they limit what a corpus on Windows can express:
    #
    #  * Windows forbids `< > : " / \ | ? *` in a file name (writing `lt<gt>.txt`
    #    raises `OSError: [Errno 22] Invalid argument`), so the XML-escaping cases
    #    reachable here are `&` (the one that matters — an unescaped `&` makes the
    #    report unparseable) and the single quote.
    #  * Windows **strips a trailing dot**: the spec name `trailing.dot.` is
    #    created on disk as `trailing.dot` (measured). The fixture therefore uses
    #    the name Windows actually stores, so the spec and the tree agree; the
    #    engine's obligation to round-trip whatever name it is given is covered by
    #    the unit tests instead.
    trees["names"] = {
        "note": "names requiring XML escaping plus other legal-but-awkward names",
        "L": dir_node(T0, {
            "amp&name.txt": file_node(b"a\r\n", T0),
            "amp&name&2.txt": file_node(b"a2\r\n", T0),
            "quote'.txt": file_node(b"c\r\n", T0),
            "space name.txt": file_node(b"e\r\n", T0),
            "hash#percent%.txt": file_node(b"f\r\n", T0),
            "brace[1]{2}.txt": file_node(b"g\r\n", T0),
            "plus+semi;eq=.txt": file_node(b"h\r\n", T0),
            "UPPER.TXT": file_node(b"i\r\n", T0),
            "no_extension": file_node(b"j\r\n", T0),
            "ünïcødé_中文.txt": file_node(b"k\r\n", T0),
            "trailing.dot": file_node(b"l\r\n", T0),
            "  leading_spaces.txt": file_node(b"m\r\n", T0),
        }),
        "R": dir_node(T0, {
            "amp&name.txt": file_node(b"a\r\n", T0),
            "amp&name&2.txt": file_node(b"a2\r\n", T0),
            "quote'.txt": file_node(b"c\r\n", T0),
            "space name.txt": file_node(b"e\r\n", T0),
            "hash#percent%.txt": file_node(b"f\r\n", T0),
            "brace[1]{2}.txt": file_node(b"g\r\n", T0),
            "plus+semi;eq=.txt": file_node(b"h\r\n", T0),
            "UPPER.TXT": file_node(b"DIFFERENT\r\n", T0),
            "no_extension": file_node(b"j\r\n", T0),
            "ünïcødé_中文.txt": file_node(b"k\r\n", T0),
            "trailing.dot": file_node(b"l\r\n", T0),
            "  leading_spaces.txt": file_node(b"m\r\n", T0),
        }),
    }

    # ---------------------------------------------------------------------
    # M2 criteria round: `version` and `rules-based ignore-unimportant`.
    #
    # Both are shapes the U4 probe series measured (probes/U4-FINDINGS.md).
    # The versioned blobs carry a real VS_FIXEDFILEINFO signature so the
    # engine's PE reader and the Oracle's version reader both find it.
    # ---------------------------------------------------------------------
    trees["versioned"] = {
        "note": "PE version resources: equal, higher-on-left, higher-on-right, one side unversioned",
        "L": dir_node(T0, {
            "equal.dll": file_node(_pe_blob((1, 2, 3, 4), (1, 2, 3, 4)), T0),
            "left_higher.dll": file_node(_pe_blob((9, 9, 9, 9), (9, 9, 9, 9)), T0),
            "right_higher.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)), T0),
            "one_sided.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)), T0),
            "plain.txt": file_node(b"alpha\r\n", T0),
            "padded.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)), T0),
        }),
        "R": dir_node(T0, {
            "equal.dll": file_node(_pe_blob((1, 2, 3, 4), (1, 2, 3, 4)) + b"\x00" * 8, T0),
            "left_higher.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)), T0),
            "right_higher.dll": file_node(_pe_blob((9, 9, 9, 9), (9, 9, 9, 9)), T0),
            "one_sided.dll": file_node(b"not a pe at all\r\n", T0),
            "plain.txt": file_node(b"beta\r\n", T0),
            "padded.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)) + b"\x00" * 4096, T0),
        }),
    }
    # U9: the version criterion applies only to a measured extension set, so the
    # same PE content must be read under an admitted name and ignored under any
    # other. `masked.*` are real PEs whose difference must go unreported;
    # `included.*` are admitted names no intuition-based list would contain.
    for _tree, _ver in (("L", (9, 9, 9, 9)), ("R", (1, 0, 0, 0))):
        _side = trees["versioned"][_tree]["children"]
        for _name in ("masked.txt", "masked.cpl", "masked.efi", "masked.exe2",
                      "masked.zip", "masked"):
            _side[_name] = file_node(_pe_blob(_ver, _ver), T0)
        for _name in ("included.vxd", "included.386"):
            _side[_name] = file_node(_pe_blob(_ver, _ver), T0)
    trees["versioned"]["note"] += (
        "; masked.* are real PEs outside the measured extension gate and must be "
        "reported `same` (U9), included.vxd/.386 are admitted names"
    )

    trees["rules-based"] = {
        "note": "C files differing by comment only, whitespace only, and a real change",
        "L": dir_node(T0, {
            "comment_only.c": file_node(b"int x; // old note\r\n", T0),
            "whitespace_only.c": file_node(b"int  x;\r\n", T0),
            "real_change.c": file_node(b"int x = 1;\r\n", T0),
            "identical.c": file_node(b"int y;\r\n", T0),
            "plain.txt": file_node(b"alpha beta\r\n", T0),
        }),
        "R": dir_node(T0, {
            "comment_only.c": file_node(b"int x; // new note\r\n", T0),
            "whitespace_only.c": file_node(b"int x;\r\n", T0),
            "real_change.c": file_node(b"int x = 2;\r\n", T0),
            "identical.c": file_node(b"int y;\r\n", T0),
            "plain.txt": file_node(b"alpha  beta\r\n", T0),
        }),
    }

    trees["posix-metadata"] = {
        "note": "sizes/mtimes equal, only ACL/owner shapes differ: the inert trio",
        "L": dir_node(T0, {
            "same_size.bin": file_node(b"0123456789", T0),
            "size_differs.bin": file_node(b"0123456789", T0),
        }),
        "R": dir_node(T0, {
            "same_size.bin": file_node(b"0123456789", T0),
            "size_differs.bin": file_node(b"0123456789" + b"\x00" * 2048, T0),
        }),
    }

    return trees


def _tree_spec(spec: dict) -> dict:
    """Strip the bookkeeping keys that are not tree nodes."""
    return {k: v for k, v in spec.items() if not k.startswith("_")}


def apply_attributes(trees: dict) -> list[str]:
    """Apply the DOS attributes declared by `_attributes`, before stamping mtimes."""
    problems: list[str] = []
    for pair, spec in trees.items():
        declared = spec.get("_attributes")
        if not declared:
            continue
        for letter, entries in declared.items():
            for rel, _value in entries:
                path = TREES / pair / rel
                flag = {"hidden": "+h", "system": "+s", "readonly": "+r"}[letter]
                result = subprocess.run(
                    ["attrib", flag, str(path)], capture_output=True, text=True
                )
                if result.returncode != 0:
                    problems.append(f"attrib {flag} {path}: {result.stderr.strip()}")
    return problems


def apply_junctions(trees: dict) -> list[str]:
    problems: list[str] = []
    for pair, spec in trees.items():
        for rel, target in spec.get("_junctions", []):
            link = TREES / pair / rel
            # The target is a sibling inside the *same side's* tree, not beside
            # the pair directory.
            side_root = TREES / pair / rel.split("/")[0]
            target_path = side_root / target
            if _is_junction(link):
                continue
            try:
                _make_junction(link, target_path)
            except RuntimeError as exc:
                problems.append(str(exc))
            # The junction's own timestamp is deliberately not stamped: this
            # platform reports `os.utime(..., follow_symlinks=False)` as
            # `NotImplementedError`, and a junction is not followed by default
            # anyway, so its mtime is not a compared property. The `links` cases
            # therefore do not assert a timestamp for the link rows.
    return problems


def expected_tree(
    pair: str,
    side: str,
    spec: dict,
    junctions: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str, int, int]]:
    """The (relative path, kind, size, mtime) rows a spec *should* produce.

    Computed from the spec alone, without touching disk. This is what makes
    `--check` a real check: an earlier version regenerated the trees first and
    then compared their digests, which is circular — writing the trees made the
    digests agree by construction, so drift could never be detected. Measured on
    the negative control: tampering a fixture's mtime did not fail `--check`.

    `junctions` is the pair-level `_junctions` list (`[(relative path, target)]`),
    which lives beside the two sides rather than inside either one.
    """
    rows: list[tuple[str, str, int, int]] = []

    def walk(node: dict, rel: str) -> None:
        for name, child in sorted(node["children"].items()):
            child_rel = f"{rel}/{name}" if rel else name
            if child["kind"] == "dir":
                rows.append((child_rel, "dir", 0, child["mtime"]))
                walk(child, child_rel)
            elif child["kind"] == "file":
                rows.append((child_rel, "file", len(child["data"]), child["mtime"]))
            else:
                raise ValueError(f"{child_rel}: unknown node kind {child['kind']!r}")

    walk(spec, "")

    # Junctions are declared in a separate pair-level list, so they are added here.
    # Their mtime is recorded as 0: this platform reports
    # `os.utime(..., follow_symlinks=False)` as `NotImplementedError`, so a
    # junction's own timestamp cannot be stamped to a fixed value, and it is not a
    # compared property anyway (a junction is not followed by default).
    prefix = f"{side}/"
    for rel, _target in junctions or []:
        if rel.startswith(prefix):
            rows.append((rel[len(prefix):], "junction", 0, 0))

    return sorted(rows)


def digest_rows(rows: list[tuple[str, str, int, int]]) -> str:
    blob = "\n".join(f"{r}|{k}|{s}|{m}" for r, k, s, m in rows) + "\n"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def hash_tree(pair: str, side: str) -> str:
    """A stable digest over one tree's on-disk (path, kind, size, mtime) rows."""
    root = TREES / pair / side
    rows: list[tuple[str, str, int, int]] = []

    # `rglob` is deliberately not used: it **descends through a junction**, so the
    # `links` trees came out with an extra `<junction>/inside.txt` row on each side
    # and the digest could never match the spec. `os.scandir` is used explicitly
    # so a junction is recorded as one entry and not traversed — which is also how
    # the engine reads it (a junction is not followed by default).
    def scan(directory: pathlib.Path, rel: str) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name)
        except OSError:
            return
        for entry in entries:
            child_rel = f"{rel}/{entry.name}" if rel else entry.name
            st = os.lstat(entry.path)
            attrs = getattr(st, "st_file_attributes", 0)
            is_reparse = bool(attrs & 0x400) or os.path.islink(entry.path)
            if is_reparse:
                rows.append((child_rel, "junction", 0, 0))
            elif entry.is_dir(follow_symlinks=False):
                rows.append((child_rel, "dir", 0, int(st.st_mtime)))
                scan(pathlib.Path(entry.path), child_rel)
            else:
                rows.append((child_rel, "file", st.st_size, int(st.st_mtime)))

    scan(root, "")
    return digest_rows(sorted(rows))


def generate() -> tuple[list[str], dict]:
    trees = build_trees()
    problems: list[str] = []
    TREES.mkdir(parents=True, exist_ok=True)

    for pair, spec in sorted(trees.items()):
        for side in ("L", "R"):
            problems.extend(
                f"{pair}/{side}: {p}" for p in _write_tree(TREES / pair / side, _tree_spec(spec[side]))
            )
    problems.extend(apply_attributes(trees))
    problems.extend(apply_junctions(trees))

    manifest = {
        "pair": {
            name: {
                "note": spec["note"],
                "left": f"trees/{name}/L",
                "right": f"trees/{name}/R",
                "tree_sha256": {"L": hash_tree(name, "L"), "R": hash_tree(name, "R")},
            }
            for name, spec in sorted(trees.items())
        }
    }
    return problems, manifest


def check() -> int:
    """Verify the corpus on disk against the spec — reading only, never writing.

    Two checks that together catch the ways a corpus drifts:

    1. **digest drift** — each tree's on-disk digest must equal the value recorded
       in `tree-digests.json`, which was written when the corpus was created;
    2. **spec drift** — each tree's on-disk digest must equal the digest the
       current spec implies, so editing a fixture definition without regenerating
       is caught even if the recorded digest is edited too.
    """
    recorded_path = FIXTURES / "tree-digests.json"
    if not recorded_path.is_file():
        print(f"FAIL: {recorded_path} is missing; run make_fixtures.py first")
        return 1

    problems: list[str] = []
    trees = build_trees()

    if not TREES.is_dir():
        print(f"FAIL: the tree corpus {TREES} does not exist; run make_fixtures.py first")
        return 1

    recorded = json.loads(recorded_path.read_text(encoding="utf-8"))

    for name, spec in sorted(trees.items()):
        for side in ("L", "R"):
            root = TREES / name / side
            if not root.is_dir():
                problems.append(f"missing tree directory: {root}")
                continue
            on_disk = hash_tree(name, side)

            rec = recorded.get(name, {}).get("tree_sha256", {}).get(side)
            if rec is None:
                problems.append(f"{name}/{side}: no recorded digest")
            elif rec != on_disk:
                problems.append(
                    f"{name}/{side}: on-disk digest {on_disk[:16]}… != recorded "
                    f"{rec[:16]}… (the corpus was modified or created elsewhere)"
                )

            spec_digest = digest_rows(
                expected_tree(name, side, _tree_spec(spec[side]), spec.get("_junctions"))
            )
            if spec_digest != on_disk:
                problems.append(
                    f"{name}/{side}: on-disk digest {on_disk[:16]}… != spec digest "
                    f"{spec_digest[:16]}… (the fixture definition changed without a "
                    "regeneration)"
                )

    extra = sorted(set(recorded) - set(trees))
    for name in extra:
        problems.append(f"{name}: recorded but not in the current spec")

    for line in problems:
        print(f"PROBLEM: {line}")
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    print(
        f"OK: {len(trees)} tree pair(s) match both their recorded digests and the "
        "current fixture spec"
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only, do not write")
    args = parser.parse_args(argv)

    if args.check:
        return check()

    problems, manifest = generate()
    if problems:
        for line in problems:
            print(f"PROBLEM: {line}", file=sys.stderr)
        return 1

    (FIXTURES / "tree-digests.json").write_text(
        json.dumps(manifest["pair"], indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    files = links = 0
    for name in manifest["pair"]:
        for side in ("L", "R"):
            for path in (TREES / name / side).rglob("*"):
                if _is_junction(path):
                    links += 1
                elif path.is_file():
                    files += 1
    print(
        f"wrote {len(manifest['pair'])} tree pair(s): {files} files + {links} junctions "
        f"= {files + links} entries under {TREES}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

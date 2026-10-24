#!/usr/bin/env python3
"""Generate `fixtures/cases.json`, the machine-readable case manifest.

# Where the expectations come from — read this before quoting any number

There is **no golden folder report** in this workspace.
`product/verify/README.md` section 9 says so explicitly:

> There is **no golden folder report** to compare against ... The few folder
> fixtures **do not imply folder compatibility**.

and it lists the uncovered scope:

> Folder criteria modes (size/timestamp/CRC/binary/rules-based), timestamp
> tolerance, attributes, symlinks, deep/empty structures, `newer`/`older`/
> `orphan`/`hollow` statuses: **not covered**.

Task A-3 is forbidden from invoking the Oracle, so expectations come from exactly
two places:

* **`observed`** — read out of an Oracle artifact or a measurement recorded in
  `product/docs/00-current-state.md` section 6. These are the anchor facts:
  with a same-size, same-timestamp, different-content pair, the default / `size` /
  `timestamp` verdicts are `same`, `CRC` / `binary` / `rules-based` are `diff`, and
  `content` / `binary-content` exit 106.
* **`predicted`** — computed by this file's **independent reference model**, which
  walks the generated trees with Python's own `os`/`stat` and re-derives the
  expected statuses from scratch. It is a second implementation in a different
  language reading the same bytes on disk, so a transcription slip in the Rust
  engine shows up as a difference between two independently written models.

`predicted` expectations are therefore **this project's committed behaviour under
the observed criteria model** — not a measured BC parity claim. The project lead's
serial Oracle pass is what upgrades a case from `predicted` to `verified`.

Run:

    python D:\\Rea\\product\\dir\\tools\\make_cases.py
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIR_CRATE = HERE.parent
FIXTURES = DIR_CRATE / "fixtures"
TREES = FIXTURES / "trees"
AUDIT_TREES = pathlib.Path(r"D:\Rea\verify\dir\trees")

FILE_ATTRIBUTE_READONLY = 0x01
FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_SYSTEM = 0x04
FILE_ATTRIBUTE_ARCHIVE = 0x20
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

ATTR_LETTERS = {
    "a": FILE_ATTRIBUTE_ARCHIVE,
    "s": FILE_ATTRIBUTE_SYSTEM,
    "h": FILE_ATTRIBUTE_HIDDEN,
    "r": FILE_ATTRIBUTE_READONLY,
}


# ===========================================================================
# The reference model
# ===========================================================================

class Criteria:
    """Parse a `criteria` argument string the way the engine documents it."""

    def __init__(self, spec: str) -> None:
        self.content: list[str] = ["size", "timestamp"]
        self.tolerance = 0
        self.ignore_dst = False
        self.attributes: str = ""
        self.follow_symlinks = False
        self.tz_ignore = False
        self.error: str | None = None
        self.error_class: str | None = None

        self.ignore_unimportant = False
        # MEASURED (u4i): the default size+timestamp pair applies ONLY when no
        # token is given. Naming ANY token clears the set first -- every
        # modifier-shaped token (`timezone:ignore`, `follow-symlinks`,
        # `attrib:z`, `ignore-unimportant`) reported `same` for a pair whose
        # size differed by 2048 bytes and whose timestamp differed by 2 hours.
        content_seen = not spec.split()
        if not content_seen:
            self.content = []
        for token in spec.split():
            low = token.lower()
            if low == "ignore-unimportant":
                self.ignore_unimportant = True
                continue
            if low in ("version", "owner", "group", "permissions"):
                # The set was already cleared above when the spec was non-empty;
                # mark it seen so a LATER size/timestamp token APPENDS rather
                # than clearing the list this token just joined (U4f
                # `version size` compares both).
                if low not in self.content:
                    self.content.append(low)
                content_seen = True
                continue
            if low in ("content", "binary-content"):
                self.error, self.error_class = token, "invalid_criteria"
                return
            if low == "follow-symlinks":
                self.follow_symlinks = True
                continue
            if low.startswith("attrib:"):
                body = low[len("attrib:"):]
                # OBSERVED (F5): the live Oracle accepts `attrib:z` with exit 0,
                # so unknown letters are inert, not an error. Naming an
                # attribute set also REPLACES the default size+timestamp pair
                # (F5's report shows a timestamp-newer file `same` under
                # `attrib:z` alone); a later size/timestamp/CRC token appends.
                if any(not ch.isalpha() and ch not in "+-" for ch in body):
                    self.error, self.error_class = token, "invalid_criteria"
                    return
                self.attributes = "".join(ch for ch in body if ch in "ashr")
                self.content, content_seen = [], True
                continue
            if low.startswith("timezone:"):
                body = low[len("timezone:"):]
                # OBSERVED (A3-folder-gate-serial-04 FINDINGS F3): the live
                # Oracle exits 106 for every shifted form; the script command
                # accepts only `ignore`.
                if body == "ignore":
                    self.tz_ignore = True
                    continue
                self.error, self.error_class = token, "invalid_criteria"
                return
            if low == "timestamp":
                if not content_seen:
                    self.content, content_seen = [], True
                self.content.append("timestamp")
                continue
            if low.startswith("timestamp:"):
                body = low[len("timestamp:"):]
                parts = body.split(";")
                first = parts[0]
                if first and not first.endswith("sec"):
                    self.error, self.error_class = token, "invalid_criteria"
                    return
                if first:
                    self.tolerance = int(first[:-3])
                for opt in parts[1:]:
                    if opt == "ignoredst":
                        self.ignore_dst = True
                    elif opt:
                        self.error, self.error_class = token, "invalid_criteria"
                        return
                if not content_seen:
                    self.content, content_seen = [], True
                if "timestamp" not in self.content:
                    self.content.append("timestamp")
                continue
            if low in ("size", "crc", "binary", "rules-based"):
                if not content_seen:
                    self.content, content_seen = [], True
                if low not in self.content:
                    self.content.append(low)
                continue
            self.error, self.error_class = token, "invalid_criteria"
            return

    @property
    def needs_content(self) -> bool:
        return any(c in ("crc", "binary", "rules-based", "version") for c in self.content)

    def tz_offsets(self) -> tuple[int, int]:
        # Shifted timezone forms are rejected (F3); nothing shifts a side.
        return (0, 0)


VS_FFI_SIGNATURE = (0xFEEF04BD).to_bytes(4, "little")


def rules_based_only_unimportant(a: bytes, b: bytes, name: str) -> bool:
    """Independent reference for `rules-based ignore-unimportant`.

    Written from the U1/U2 behaviour table, NOT from the engine: a changed
    line is unimportant iff every difference on it is a comment or whitespace
    difference. The model strips comment text and all whitespace and compares
    what remains. Line counts must match; the extension decides whether
    comments exist at all (unknown extensions are plain text, u2 `foo-*`).
    A line whose difference survives that stripping is important.
    """
    try:
        at = a.decode("utf-8")
        bt = b.decode("utf-8")
    except UnicodeDecodeError:
        return False
    al = at.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10)).split(chr(10))
    bl = bt.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10)).split(chr(10))
    if len(al) != len(bl):
        return False
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    syntax = ext in ("c", "cc", "cpp", "cs", "h", "hpp", "m", "py", "js")
    for x, y in zip(al, bl):
        if x == y:
            continue
        if syntax:
            # Comment-only difference: compare with comment text removed.
            if _strip_comments(x) == _strip_comments(y):
                continue
        # Whitespace-only difference, but only outside string literals --
        # whitespace inside a string is content (u2 `string-internal-ws`).
        # MEASURED for plain text too (u4g: `plain.txt` "alpha beta" vs
        # "alpha  beta" folds to `same` under rules-based ignore-unimportant),
        # so this check is NOT gated on `syntax`.
        if '"' not in x and "'" not in x and '"' not in y and "'" not in y:
            if "".join(x.split()) == "".join(y.split()):
                continue
        if not syntax:
            # Plain text also folds a case-only difference (the `case-txt`
            # anchor's rule); everything else is important.
            if x.lower() == y.lower():
                continue
            return False
        return False
    return True


def _strip_comments(line: str) -> str:
    """Remove `//`-to-EOL and `/* */` portions, then all whitespace."""
    out = []
    i = 0
    in_block = False
    while i < len(line):
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                break
            i = j + 2
            in_block = False
            continue
        if line.startswith("//", i):
            break
        if line.startswith("/*", i):
            in_block = True
            i += 2
            continue
        out.append(line[i])
        i += 1
    return "".join(c for c in "".join(out) if not c.isspace())


#: Extensions for which BC reads a version resource, measured in U9
#: (`product/verify/probes/U9-FINDINGS.md`). BC returns `same` for every other
#: name even when the file is a real PE, so the name is an admission test and
#: the resource is only the value source.
VERSION_EXTENSIONS = ("exe", "dll", "ocx", "scr", "sys", "drv", "vxd", "386")


def version_applies_to(name: str) -> bool:
    """True when BC would read a version resource for a file with this name."""
    file = name.replace("\\", "/").rsplit("/", 1)[-1]
    if "." not in file:
        return False
    ext = file.rsplit(".", 1)[1]
    if not ext:
        return False
    return ext.lower() in VERSION_EXTENSIONS


def pe_file_version(path: pathlib.Path) -> tuple[int, int, int, int] | None:
    """Read the PE FileVersion like the engine's `reacmp_vfs::pe`.

    A second, independent implementation (this one over the raw bytes with
    struct-style slicing) so a mistake in either shows up as a model
    disagreement. Returns None when no VS_FIXEDFILEINFO is present.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    i = data.find(VS_FFI_SIGNATURE)
    if i < 0 or i + 16 > len(data):
        return None
    ms = int.from_bytes(data[i + 8:i + 12], "little")
    ls = int.from_bytes(data[i + 12:i + 16], "little")
    return (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)


class Node:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.name = path.name
        st = os.lstat(path)
        attrs = getattr(st, "st_file_attributes", 0)
        self.is_reparse = bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT) or os.path.islink(path)
        if self.is_reparse:
            self.kind = "symlink"
        elif stat.S_ISDIR(st.st_mode):
            self.kind = "dir"
        elif stat.S_ISREG(st.st_mode):
            self.kind = "file"
        else:
            self.kind = "unknown"
        self.attrs = attrs
        self.mtime = int(st.st_mtime)
        self.size = st.st_size if self.kind == "file" else None
        self.target: str | None = None
        if self.is_reparse:
            try:
                self.target = os.readlink(path)
            except OSError:
                self.target = None
        self.children: list[Node] = []
        if self.kind == "dir" and not self.is_reparse:
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                self.children.append(Node(child))

    def resolved(self, follow: bool) -> "Node":
        """The node as the engine would see it under a symlink policy."""
        if self.kind != "symlink" or not follow:
            return self
        try:
            st = os.stat(self.path)
        except OSError:
            return self
        clone = Node.__new__(Node)
        clone.path = self.path
        clone.name = self.name
        clone.is_reparse = True
        if stat.S_ISDIR(st.st_mode):
            clone.kind = "dir"
            clone.size = None
            clone.children = [
                Node(c) for c in sorted(self.path.iterdir(), key=lambda p: p.name)
            ]
        elif stat.S_ISREG(st.st_mode):
            clone.kind = "file"
            clone.size = st.st_size
            clone.children = []
        else:
            clone.kind = "unknown"
            clone.size = None
            clone.children = []
        clone.attrs = self.attrs
        clone.mtime = int(st.st_mtime)
        clone.target = self.target
        return clone


def ref_compare(left: pathlib.Path, right: pathlib.Path, criteria: Criteria) -> dict[str, str]:
    """Independent reference implementation of the folder comparison.

    Returns {relative path: status token} for every row the report would contain,
    including directory rows.
    """
    out: dict[str, str] = {}
    lo, ro = criteria.tz_offsets()

    def file_pair(l: Node | None, r: Node | None) -> str:
        if l is not None and r is None:
            return "ltonly"
        if l is None and r is not None:
            return "rtonly"
        if l is None and r is None:
            return "same"

        assert l is not None and r is not None

        # Unfollowed links: compare the recorded target text. Derived, not probed.
        if l.kind == "symlink" and r.kind == "symlink":
            target_differs = l.target != r.target
            ts_differs_local: bool | None = None
            if "timestamp" in criteria.content:
                diff = abs((l.mtime + lo) - (r.mtime + ro))
                if criteria.tz_ignore and diff % 3600 == 0:
                    ts_differs_local = False
                elif criteria.ignore_dst and diff == 3600:
                    ts_differs_local = False
                else:
                    ts_differs_local = diff > criteria.tolerance
            # A link has no size and no bytes, so a size/content criterion does
            # not apply. OBSERVED (F7): the live Oracle judges an unfollowed
            # junction pair by its targets even under the default
            # size+timestamp criteria.
            if target_differs:
                return "diff"
            if ts_differs_local:
                return "ltnewer" if (l.mtime + lo) > (r.mtime + ro) else "rtnewer"
            return "same"

        ts_differs: bool | None = None
        other_differs = False

        version_newer: Node | None = None

        for c in criteria.content:
            if c == "timestamp":
                a, b = l.mtime + lo, r.mtime + ro
                diff = abs(a - b)
                if criteria.tz_ignore and diff % 3600 == 0:
                    ts_differs = False
                elif criteria.ignore_dst and diff == 3600:
                    ts_differs = False
                else:
                    ts_differs = diff > criteria.tolerance
            elif c == "size":
                if l.size is None or r.size is None:
                    return "unknown"
                if l.size != r.size:
                    other_differs = True
            elif c == "version":
                # u4c/u4f: directional FileVersion comparison. A side with no
                # version resource is older than a side with one; both empty
                # means equal. The direction is carried out through
                # `version_newer` because it is not a plain diff.
                #
                # U9: the criterion only applies to the measured extension set.
                # A name outside it contributes nothing at all, so the row falls
                # through as equal even when the file is a real PE.
                if l.kind != "file" or r.kind != "file":
                    continue
                if not (version_applies_to(l.name)
                        and version_applies_to(r.name)):
                    continue
                va = pe_file_version(l.path)
                vb = pe_file_version(r.path)
                if va != vb:
                    if va is None:
                        version_newer = r
                    elif vb is None:
                        version_newer = l
                    else:
                        version_newer = l if va > vb else r
            elif c in ("owner", "group", "permissions"):
                # Measured inert on Windows (u4/u4b/u4e): accepted, no effect.
                continue
            else:  # crc / binary / rules-based
                # The size shortcut applies to crc/binary only. MEASURED (u4g):
                # under `rules-based` BC compares content by rules, so two files
                # whose sizes differ but whose lines differ only in whitespace
                # are a MATCH with ignore-unimportant (`plain.txt`,
                # `whitespace_only.c` -> `same`), which a size short-circuit
                # would have made impossible.
                if c in ("crc", "binary") and l.size is not None                         and r.size is not None and l.size != r.size:
                    other_differs = True
                else:
                    try:
                        a_bytes = l.path.read_bytes()
                        b_bytes = r.path.read_bytes()
                        if a_bytes != b_bytes:
                            if c == "rules-based" and criteria.ignore_unimportant:
                                if not rules_based_only_unimportant(a_bytes, b_bytes, l.path.name):
                                    other_differs = True
                            else:
                                other_differs = True
                    except OSError:
                        return "unknown"

        # OBSERVED (F6): the live Oracle ignores the attribute comparison when
        # a content criterion (CRC/binary/rules-based) is present.
        if criteria.attributes and not criteria.needs_content:
            mask = 0
            for letter in criteria.attributes:
                mask |= ATTR_LETTERS[letter]
            a = l.attrs & mask
            b = r.attrs & mask
            # Per-attribute: any named attribute clear on one side and set on the
            # other is a difference.
            for letter, bit in ATTR_LETTERS.items():
                if letter not in criteria.attributes:
                    continue
                if bool(a & bit) != bool(b & bit):
                    other_differs = True

        # A version difference outranks every other criterion (gate serial-06
        # `crit-version-size`: a versioned file vs a truncated one is `ltnewer`
        # even though the sizes differ).
        if version_newer is l:
            return "ltnewer"
        if version_newer is r:
            return "rtnewer"
        if other_differs:
            return "diff"
        if ts_differs:
            return "ltnewer" if (l.mtime + lo) > (r.mtime + ro) else "rtnewer"
        return "same"

    def emit_one_sided(node: Node, prefix: str, status: str) -> None:
        # Children of a one-sided directory carry the same one-sided status,
        # recursing through nested directories (the structure the gate's
        # conflict and orphan artifacts show).
        for c in node.children:
            c_path = f"{prefix}/{c.name}"
            out[c_path] = status
            c_res = c.resolved(criteria.follow_symlinks)
            if c_res is not None and c_res.kind == "dir":
                emit_one_sided(c_res, c_path, status)

    def dir_pair(l: Node | None, r: Node | None, prefix: str) -> None:
        path = prefix
        if l is not None and r is None:
            out[path] = "ltonly"
            emit_one_sided(l, path, "ltonly")
        elif l is None and r is not None:
            out[path] = "rtonly"
            emit_one_sided(r, path, "rtonly")
        else:
            child_statuses = []
            sub = []
            lnodes = {c.name: c for c in (l.children if l else [])}
            rnodes = {c.name: c for c in (r.children if r else [])}
            names = sorted(
                set(lnodes) | set(rnodes),
                key=lambda n: (
                    not (
                        (lnodes.get(n) is not None and lnodes[n].kind == "dir")
                        or (rnodes.get(n) is not None and rnodes[n].kind == "dir")
                    ),
                    n,
                ),
            )
            for name in names:
                sub.append(name)
            for name in sub:
                lc = lnodes.get(name)
                rc = rnodes.get(name)
                child_path = f"{path}/{name}" if path else name
                lc_r = lc.resolved(criteria.follow_symlinks) if lc else None
                rc_r = rc.resolved(criteria.follow_symlinks) if rc else None
                ldir = lc_r is not None and lc_r.kind == "dir"
                rdir = rc_r is not None and rc_r.kind == "dir"
                if (ldir or rdir) and not (
                    lc_r is not None and rc_r is not None and lc_r.kind != rc_r.kind
                ):
                    dir_pair(lc_r, rc_r, child_path)
                    child_statuses.append(out[child_path])
                elif lc_r is not None and rc_r is not None and lc_r.kind != rc_r.kind:
                    out[child_path] = "diff"
                    child_statuses.append("diff")
                else:
                    s = file_pair(lc_r, rc_r)
                    out[child_path] = s
                    child_statuses.append(s)
            if any(s != "same" for s in child_statuses):
                out[path] = "diff"
            else:
                out[path] = "same"

    root_l = Node(left)
    root_r = Node(right)
    # The two roots are rows of their own only conceptually; the engine reports
    # their children at the top level.
    lnodes = {c.name: c for c in root_l.children}
    rnodes = {c.name: c for c in root_r.children}
    names = sorted(
        set(lnodes) | set(rnodes),
        key=lambda n: (
            not (
                (lnodes.get(n) is not None and lnodes[n].kind == "dir")
                or (rnodes.get(n) is not None and rnodes[n].kind == "dir")
            ),
            n,
        ),
    )
    for name in names:
        lc = lnodes.get(name)
        rc = rnodes.get(name)
        lc_r = lc.resolved(criteria.follow_symlinks) if lc else None
        rc_r = rc.resolved(criteria.follow_symlinks) if rc else None
        ldir = lc_r is not None and lc_r.kind == "dir"
        rdir = rc_r is not None and rc_r.kind == "dir"
        if (ldir or rdir) and not (
            lc_r is not None and rc_r is not None and lc_r.kind != rc_r.kind
        ):
            dir_pair(lc_r, rc_r, name)
        elif lc_r is not None and rc_r is not None and lc_r.kind != rc_r.kind:
            # OBSERVED (F1): each side is emitted separately — the directory
            # side as an expanded one-sided row, the other side one-sided. The
            # same-name dict key ends up holding the non-directory row, exactly
            # as the independent XML reader's insertion order does.
            if lc_r.kind == "dir":
                dir_pair(lc_r, None, name)
            elif rc_r.kind == "dir":
                dir_pair(None, rc_r, name)
            out[name] = "ltonly" if lc_r.kind != "dir" else "rtonly"
        else:
            out[name] = file_pair(lc_r, rc_r)
    return out


# ===========================================================================
# The corpus of cases
# ===========================================================================

def pair_paths(pair: str) -> tuple[pathlib.Path, pathlib.Path] | None:
    if pair == "verify-dir-trees":
        if not AUDIT_TREES.is_dir():
            return None
        return AUDIT_TREES / "L", AUDIT_TREES / "R"
    left, right = TREES / pair / "L", TREES / pair / "R"
    if not left.is_dir() or not right.is_dir():
        return None
    return left, right


def _parse_oracle_xml(xml: str) -> dict[str, str]:
    """Read {relative path: status} out of the audit's stored Oracle report.

    This is an *independent* reader of the observed artifact, deliberately
    separate from the engine's writer, so that agreement between the two is
    evidence and not a tautology.
    """
    stack: list[dict] = []
    root_open = False
    top: list[dict] = []
    for line in xml.splitlines():
        s = line.strip()
        if s == "<foldercomp>":
            if not root_open:
                root_open = True
                continue
            stack.append({"kind": "dir", "name": "", "children": [], "sides": set()})
            continue
        if s == "</foldercomp>":
            if not stack:
                continue
            entry = stack.pop()
            (stack[-1]["children"] if stack else top).append(entry)
            continue
        m = re.match(r"<name>(.*)</name>$", s)
        if m and stack:
            # Unescape like the fixture runner does: the manifest and the
            # reference model carry literal names, while the report escapes
            # & as &amp; (the gate caught exactly this on amp&name.txt).
            stack[-1]["name"] = (
                m.group(1).replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", chr(34)).replace("&apos;", chr(39))
                .replace("&#39;", chr(39)).replace("&amp;", "&"))
            continue
        if s in ("<lt>", "<rt>"):
            for entry in stack:
                entry["sides"].add(s[1:3])
            continue
        m = re.match(r'<filecomp status="([a-z]+)">$', s)
        if m:
            stack.append({"kind": "file", "name": "", "status": m.group(1),
                          "children": [], "sides": set()})
            continue
        if s == "</filecomp>":
            if not stack:
                continue
            entry = stack.pop()
            (stack[-1]["children"] if stack else top).append(entry)
            continue

    out: dict[str, str] = {}

    def status_of(entry: dict) -> str:
        if entry["kind"] == "file":
            return entry["status"] or "unknown"
        sides = entry["sides"]
        if sides and sides != {"lt", "rt"}:
            return "ltonly" if sides == {"lt"} else "rtonly"
        if any(status_of(c) != "same" for c in entry["children"]):
            return "diff"
        return "same"

    def emit(entry: dict, prefix: str) -> None:
        path = f"{prefix}/{entry['name']}" if prefix else entry["name"]
        out[path] = status_of(entry)
        for child in entry["children"]:
            emit(child, path)

    for entry in top:
        emit(entry, "")
    return out


#: The observed Oracle artifact for the audit tree pair, with its wall-clock
#: `created` attribute removed so the file is byte-stable. This file is READ-ONLY
#: evidence owned by the audit; it is read here, never regenerated.
ORACLE_XML_CANDIDATES = [
    pathlib.Path(r"D:\Rea\tools\_audit\dir-load-expand-report.xml"),
    pathlib.Path(r"D:\Rea\product\verify\runs\A1-final\raw\folder-current-trees.xml"),
]


def _validate_observed_anchors() -> list[str]:
    """Check the reference model against what the Oracle actually produced.

    Three independent checks, each of which must hold:

    1. every Oracle report on disk for the audit tree pair reads back as the same
       status map;
    2. the reference model reproduces that map under the default criteria;
    3. the criteria matrix recorded in `00-current-state.md` section 6 is
       reproduced by the reference model on the `criteria` fixture pair.

    A failure here means the reference model has drifted from the observed
    evidence, and the manifest must not be regenerated until it is fixed.
    """
    problems: list[str] = []

    oracle_maps: list[tuple[str, dict[str, str]]] = []
    for path in ORACLE_XML_CANDIDATES:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            problems.append(f"cannot read {path}: {exc}")
            continue
        oracle_maps.append((str(path), _parse_oracle_xml(text)))

    if not oracle_maps:
        problems.append(
            "no stored Oracle folder report was found at any of "
            f"{[str(p) for p in ORACLE_XML_CANDIDATES]}; the observed anchor cannot "
            "be re-checked"
        )
        return problems

    base_name, base_map = oracle_maps[0]
    for other_name, other_map in oracle_maps[1:]:
        if other_map != base_map:
            diff = {
                k: (base_map.get(k), other_map.get(k))
                for k in set(base_map) | set(other_map)
                if base_map.get(k) != other_map.get(k)
            }
            problems.append(
                f"the stored Oracle reports disagree: {base_name} vs {other_name}: {diff}"
            )

    # Check 4 -- the A-3 serial gate artifacts: every xml case the live Oracle
    # ran in `product/verify/runs/A3-folder-gate-serial-04/` is anchored, so a
    # manifest regeneration cannot drift from measured BC behaviour.
    gate_dir = pathlib.Path(r"D:\Rea\product\verify\runs\A3-folder-gate-serial-04")
    gate_payload = gate_dir / "gate-results.json"
    gate_checked = 0
    if gate_payload.is_file():
        try:
            gate = json.loads(gate_payload.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            gate = None
            problems.append(f"cannot read {gate_payload}: {exc}")
        if gate:
            for rec in gate["results"]:
                if rec.get("class") != "xml-parity":
                    continue
                art = gate_dir / "oracle" / f"{rec['id']}.out"
                if not art.is_file():
                    continue
                criteria_txt = rec.get("bc_criteria") or rec.get("criteria") or ""
                crit = Criteria(criteria_txt)
                if crit.error is not None:
                    problems.append(
                        f"gate anchor {rec['id']}: criteria {criteria_txt!r} "
                        f"rejected by the reference model ({crit.error_class})")
                    continue
                paths_g = pair_paths(rec["pair"])
                if paths_g is None:
                    problems.append(
                        f"gate anchor {rec['id']}: pair {rec['pair']!r} not on disk")
                    continue
                oracle_map = _parse_oracle_xml(art.read_text(encoding="utf-8-sig"))
                model_map = ref_compare(paths_g[0], paths_g[1], crit)
                if model_map != oracle_map:
                    diff = {
                        k: (oracle_map.get(k), model_map.get(k))
                        for k in set(oracle_map) | set(model_map)
                        if oracle_map.get(k) != model_map.get(k)
                    }
                    problems.append(
                        f"gate anchor {rec['id']}: the reference model no longer "
                        f"reproduces the live-Oracle map: {diff}")
                gate_checked += 1
            if gate_checked == 0:
                problems.append(
                    "the gate run directory exists but no xml artifact was "
                    "validated; the corpus may have been renamed")
    else:
        problems.append(
            f"the A-3 serial gate run directory is missing ({gate_dir}); its "
            "artifacts anchor this corpus and must not be deleted")

    paths = pair_paths("verify-dir-trees")
    if paths is None:
        problems.append("the audit tree pair is not on disk")
        return problems

    model_map = ref_compare(paths[0], paths[1], Criteria(""))
    if model_map != base_map:
        diff = {
            k: (base_map.get(k), model_map.get(k))
            for k in set(base_map) | set(model_map)
            if base_map.get(k) != model_map.get(k)
        }
        problems.append(
            "the reference model does not reproduce the observed Oracle report for "
            f"the audit tree pair under the default criteria: {diff}"
        )

    # Check 3: the criteria matrix from 00-current-state.md section 6.
    crit_paths = pair_paths("criteria")
    if crit_paths is not None:
        expectations = [
            ("", "samesize_text.txt", "same"),
            ("", "samesize_bin.bin", "same"),
            ("size", "samesize_text.txt", "same"),
            ("timestamp", "samesize_text.txt", "same"),
            ("CRC", "samesize_text.txt", "diff"),
            ("CRC", "samesize_bin.bin", "diff"),
            ("binary", "samesize_text.txt", "diff"),
            ("binary", "samesize_bin.bin", "diff"),
            ("rules-based", "samesize_text.txt", "diff"),
            ("rules-based", "samesize_bin.bin", "diff"),
        ]
        for spec, name, want in expectations:
            got = ref_compare(crit_paths[0], crit_paths[1], Criteria(spec)).get(name)
            if got != want:
                problems.append(
                    f"observed criteria anchor violated: criteria {spec!r} on {name} "
                    f"should be {want!r} but the reference model says {got!r}"
                )

    return problems


def build_cases() -> tuple[list[dict], list[str]]:
    cases: list[dict] = []
    problems: list[str] = _validate_observed_anchors()

    def add(
        cid: str,
        pair: str,
        spec: str,
        *,
        note: str,
        evidence: str = "predicted",
        layout: str = "xml",
        expected_exit: int = 0,
        expected_error: str | None = None,
        extra: dict | None = None,
        skip_reference: bool = False,
    ) -> None:
        criteria = Criteria(spec)
        if criteria.error is not None:
            if expected_error is None:
                problems.append(
                    f"{cid}: reference model rejects {spec!r} as {criteria.error_class} "
                    "but the case does not declare expected_error"
                )
            cases.append({
                "id": cid,
                "pair": pair,
                "criteria": spec,
                "layout": layout,
                "expected_exit": expected_exit,
                "expected_error": expected_error,
                "evidence": evidence,
                "evidence_note": note,
                "expected_statuses": {},
                "extra": extra or {},
            })
            return

        if expected_error is not None:
            if criteria.error is None and expected_error != "unknown_layout":
                # An `unknown_layout` rejection is about the layout argument, not
                # the criteria, so an accepted criteria is expected there.
                problems.append(f"{cid}: declares expected_error but the model accepts {spec!r}")
            cases.append({
                "id": cid,
                "pair": pair,
                "criteria": spec,
                "layout": layout,
                "expected_exit": expected_exit,
                "expected_error": expected_error,
                "evidence": evidence,
                "evidence_note": note,
                "expected_statuses": {},
                "extra": extra or {},
            })
            return

        statuses: dict[str, str] = {}
        if not skip_reference:
            # A case may exercise the CLI-flag form of an option (extra.cli_flag)
            # instead of the criteria token. The reference model only knows the
            # token form, so the flag's equivalent token is appended for the
            # EXPECTATION computation: the expected map describes what the
            # engine emits under that flag, and the serial gate renders the
            # same token into the Oracle script (bc_criteria).
            ref_criteria = criteria
            cli_flag = (extra or {}).get("cli_flag")
            if cli_flag and cli_flag.startswith("--"):
                token = cli_flag[2:]
                ref_criteria = Criteria(spec + " " + token)
            paths = pair_paths(pair)
            if paths is None:
                problems.append(f"{cid}: fixture pair {pair!r} is not on disk")
            else:
                try:
                    statuses = ref_compare(paths[0], paths[1], ref_criteria)
                except Exception as exc:  # noqa: BLE001
                    problems.append(f"{cid}: reference model failed: {type(exc).__name__}: {exc}")

        cases.append({
            "id": cid,
            "pair": pair,
            "criteria": spec,
            "layout": layout,
            "expected_exit": expected_exit,
            "expected_error": expected_error,
            "evidence": evidence,
            "evidence_note": note,
            "expected_statuses": statuses,
            "extra": extra or {},
        })

    # ---------------------------------------------------------------------
    # Group 1 — the observed criteria model, on the audit's own fixture shape
    # ---------------------------------------------------------------------
    OBS = (
        "OBSERVED ANCHOR — product/docs/00-current-state.md section 6: with a "
        "same-size, same-timestamp pair whose content differs, the default / size / "
        "timestamp verdicts are `same` and CRC / binary / rules-based are `diff`. "
        "`criteria content` and `criteria binary-content` exit 106. "
        "`_validate_observed_anchors` re-checks the reference model against these "
        "facts on every regeneration."
    )
    for cid, spec in [
        ("crit-default", ""),
        ("crit-size", "size"),
        ("crit-timestamp", "timestamp"),
        ("crit-crc", "CRC"),
        ("crit-binary", "binary"),
        ("crit-rules-based", "rules-based"),
    ]:
        add(cid, "criteria", spec, note=OBS, evidence="observed")
    for name in ("content", "binary-content"):
        add(
            f"crit-invalid-{name}", "criteria", name,
            note=OBS, evidence="observed",
            expected_exit=106, expected_error="invalid_criteria",
        )

    # The audit's own tree pair, which the Oracle actually produced a report for.
    AUDIT = (
        "OBSERVED — tools/_audit/dir-load-expand-report.xml is the Oracle's XML for "
        "exactly this tree pair under the default criteria, and "
        "product/docs/00-current-state.md section 6 records the CRC/binary/"
        "rules-based verdicts for the same tree. The statuses below are read out of "
        "those artifacts and re-checked by `_validate_observed_anchors`."
    )
    for cid, spec in [
        ("audit-trees-default", ""),
        ("audit-trees-crc", "CRC"),
        ("audit-trees-binary", "binary"),
        ("audit-trees-rules-based", "rules-based"),
    ]:
        add(cid, "verify-dir-trees", spec, note=AUDIT, evidence="observed")
    for cid, layout in [
        ("audit-trees-side-by-side", "side-by-side"),
        ("audit-trees-summary", "summary"),
    ]:
        add(cid, "verify-dir-trees", "", layout=layout, note=AUDIT, evidence="observed")

    # ---------------------------------------------------------------------
    # Group 2 — status coverage
    # ---------------------------------------------------------------------
    STATUS = (
        "predicted by the reference model; grounded in "
        "extracted/pseudocode/140fd1e90.c, which shows the report writer emitting "
        "exactly same / diff / ltonly / rtonly / ltnewer / rtnewer. The trigger "
        "boundary for the two `newer` tokens has not been Oracle-probed."
    )
    for cid, spec in [
        ("status-baseline-default", ""),
        ("status-baseline-size", "size"),
        ("status-baseline-timestamp", "timestamp"),
        ("status-baseline-crc", "CRC"),
        ("status-baseline-binary", "binary"),
        ("status-baseline-rules-based", "rules-based"),
    ]:
        add(cid, "baseline", spec, note=STATUS)

    # ---------------------------------------------------------------------
    # Group 3 — timestamp tolerance
    # ---------------------------------------------------------------------
    TOL = (
        "predicted; the documented grammar is `timestamp[:[<seconds>sec][;IgnoreDST]]` "
        "and `IgnoreDST` \"considers differences of exactly 1 hour as matches\" "
        "(help/scripting_reference.html, O). Whether a difference of exactly N "
        "seconds counts as inside a tolerance of N is NOT probed."
    )
    for cid, spec in [
        ("tol-default", ""),
        ("tol-30sec", "timestamp:30sec"),
        ("tol-60sec", "timestamp:60sec"),
        ("tol-7200sec", "timestamp:7200sec"),
        ("tol-1sec", "timestamp:1sec"),
        ("tol-ignore-dst-0sec", "timestamp:0sec;IgnoreDST"),
        ("tol-ignore-dst-30sec", "timestamp:30sec;IgnoreDST"),
        ("tol-timestamp-only-ignore-dst", "timestamp:0sec;IgnoreDST"),
    ]:
        add(cid, "tolerance", spec, note=TOL)

    # ---------------------------------------------------------------------
    # Group 4 — structural boundaries
    # ---------------------------------------------------------------------
    STRUCT = (
        "predicted by the reference model; help/dir_how_to_compare.html (O) says "
        "\"Folders are compared by aggregating the comparisons of files within "
        "them\", so a directory's result is an aggregate and never its own timestamp."
    )
    add("struct-deep-nesting-default", "deep", "", note=STRUCT)
    add("struct-deep-nesting-crc", "deep", "CRC", note=STRUCT)
    add("struct-empty-dirs-default", "empty", "", note=STRUCT)
    add("struct-empty-dirs-content", "empty", "binary", note=STRUCT)
    add("struct-file-vs-dir-conflict-default", "conflict", "", note=(
        STRUCT + " A name that is a file on one side and a directory on the other is "
        "a kind conflict; extracted/pseudocode/140f4b8b0.c records the comparison "
        "core returning its code 9 (different) for the mismatched-kind arm."
    ))
    add("struct-file-vs-dir-conflict-crc", "conflict", "CRC", note=(
        "predicted; a kind conflict cannot be decided by content either, so it stays "
        "`diff`"
    ))
    add("struct-many-siblings-default", "many", "", note=(
        "predicted by the reference model over 60+ sibling names; the point is "
        "alignment at scale"
    ))
    add("struct-many-siblings-crc", "many", "CRC", note=(
        "predicted; the same pair under a content criterion"
    ))
    add("struct-orphan-directory-trees", "orphan-dirs", "", note=STRUCT)
    add("struct-orphan-directory-trees-crc", "orphan-dirs", "CRC", note=STRUCT)
    add("struct-names-xml-escaping", "names", "", note=(
        "predicted; `&` in a name is the XML-escaping case that matters, because an "
        "unescaped `&` makes the report unparseable. Windows forbids `< > : \" / \\ | "
        "? *` in a file name (measured: writing `lt<gt>.txt` raises OSError errno 22), "
        "so those cannot appear in a corpus built on this platform."
    ))
    add("struct-names-xml-escaping-side-by-side", "names", "",
        layout="side-by-side", note="the same pair in the side-by-side layout")
    add("struct-names-xml-escaping-summary", "names", "",
        layout="summary", note="the same pair in the summary layout")

    # ---------------------------------------------------------------------
    # Group 5 — attributes
    # ---------------------------------------------------------------------
    ATTR = (
        "predicted; help/scripting_reference.html (O) documents `attrib:` as comparing "
        "the named DOS attributes (letters a/s/h/r). The comparison is evaluated "
        "per attribute, because two entries that each fail to have *all* of a set "
        "would otherwise compare equal. The `extra.attributes` field records the "
        "attribute bits measured on the generated files, so the expectation can be "
        "re-checked against the corpus."
    )
    for cid, spec in [
        ("attrib-none-default", ""),
        ("attrib-hidden", "attrib:h size timestamp"),
        ("attrib-system", "attrib:s size timestamp"),
        ("attrib-readonly", "attrib:r size timestamp"),
        ("attrib-archive", "attrib:a size timestamp"),
        ("attrib-hidden-and-system", "attrib:hs size timestamp"),
        ("attrib-all-letters", "attrib:ashr size timestamp"),
    ]:
        add(cid, "attributes", spec, note=ATTR)
    add(
        "attrib-combined-with-crc", "attributes", "attrib:h CRC",
        note="OBSERVED (A3-folder-gate-serial-04, FINDINGS F6): the live Oracle "
             "judges every file `same` under `criteria attrib:h CRC` — the "
             "hidden-bit difference that `attrib:h` alone flags is NOT flagged "
             "once a content criterion is present. A content criterion "
             "replaces the attribute comparison.",
        evidence="observed",
    )

    # ---------------------------------------------------------------------
    # Group 6 — junctions
    # ---------------------------------------------------------------------
    LINK = (
        "OBSERVED (A3-folder-gate-serial-04, FINDINGS F7): the live Oracle "
        "renders an unfollowed junction row with its own mtime and "
        "`<size>0</size>`, and judges a junction pair whose targets differ as "
        "`diff` even under the default size+timestamp criteria "
        "(links-not-followed-default). Directory junctions are used because "
        "creating a symbolic link requires SeCreateSymbolicLinkPrivilege, "
        "which this host does not grant (measured: WinError 1314). "
        "U-M3-10 is settled for junctions."
    )
    add("links-not-followed-default", "links", "", note=LINK)
    add("links-followed", "links", "size timestamp follow-symlinks", note=LINK)
    add(
        "links-followed-via-cli-flag", "links", "size timestamp", note=LINK,
        extra={"cli_flag": "--follow-symlinks"},
    )
    add("links-followed-crc", "links", "CRC follow-symlinks", note=LINK)

    # ---------------------------------------------------------------------
    # Group 7 — timezone
    # ---------------------------------------------------------------------
    TZ = (
        "OBSERVED (A3-folder-gate-serial-04, tz-ignore case): the live Oracle "
        "accepts `timezone:ignore` and suppresses whole-hour differences — the "
        "1 h and 2 h fixture files both compare `same` under "
        "`criteria timestamp timezone:ignore`. U-M3-4 is settled for the "
        "ignore form."
    )
    add("tz-ignore", "tolerance", "timestamp timezone:ignore", note=TZ)
    TZ_REJ = (
        "OBSERVED (A3-folder-gate-serial-04, FINDINGS F3): the live Oracle "
        "exits 106 for every shifted timezone form — "
        "`criteria timestamp timezone:left+1` was rejected — although the help "
        "text documents the syntax. The script command does not take it, so "
        "the engine refuses it exactly like the Oracle. Upgraded from the "
        "engine's earlier accepted-and-shifted guess, which the gate proved "
        "wrong."
    )
    add("tz-left-plus-1", "tolerance", "timestamp timezone:left+1", note=TZ_REJ,
        expected_exit=106, expected_error="invalid_criteria", skip_reference=True)
    add("tz-left-minus-1", "tolerance", "timestamp timezone:left-1", note=TZ_REJ,
        expected_exit=106, expected_error="invalid_criteria", skip_reference=True)
    add("tz-right-plus-2", "tolerance", "timestamp timezone:right+2", note=TZ_REJ,
        expected_exit=106, expected_error="invalid_criteria", skip_reference=True)
    add("tz-right-minus-2", "tolerance", "timestamp timezone:right-2", note=TZ_REJ,
        expected_exit=106, expected_error="invalid_criteria", skip_reference=True)

    # ---------------------------------------------------------------------
    # Group 8 — rejection cases
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # Group 9 — the U4 probe series: the five formerly-unlocked criteria
    # ---------------------------------------------------------------------
    U4 = (
        "OBSERVED (probes/U4-FINDINGS.md; runs u4-probe-*, u4b-*, u4c-*, "
        "u4d-*, u4e-*, u4f-*): measured with the live Oracle. "
    )
    for cid, spec in (
        ("crit-version-equal", "version"),
        ("crit-version-size", "version size"),
    ):
        add(
            cid, "versioned", spec,
            note=U4 + "`version` compares the PE FileVersion field (product-version-only "
                      "differences are ignored) and REPLACES the default size+timestamp "
                      "pair; a later size token re-activates it.",
            evidence="observed",
        )
    for cid, spec in (
        ("crit-owner", "owner"),
        ("crit-group", "group"),
        ("crit-permissions", "permissions"),
        ("crit-owner-size", "owner size"),
    ):
        add(
            cid, "posix-metadata", spec,
            note=U4 + "owner/group/permissions are measured INERT on Windows: the token "
                      "is accepted and contributes nothing, and it still REPLACES the "
                      "default size+timestamp pair (the size-differs row is `same`).",
            evidence="observed",
        )
    for cid, spec in (
        ("crit-rb-iu-scope", "rules-based"),
        ("crit-rb-iu-fold", "rules-based ignore-unimportant"),
    ):
        add(
            cid, "rules-based", spec,
            note=U4 + "`ignore-unimportant` folds an unimportant-only difference (comment "
                      "or whitespace, per the M2 engine) to a match, and only under a "
                      "rules-based content comparison; a real change stays `diff`.",
            evidence="observed",
        )
    add(
        "crit-ignore-unimportant-alone", "rules-based", "ignore-unimportant",
        note=U4 + "`ignore-unimportant` alone is a MODIFIER: it does not replace the "
                  "default size+timestamp pair (u4f `f-iu-alone-size`).",
        evidence="observed",
    )
    for token in ("sizee", "timestamp:5min", "timezone:left6", "timezone:left+13",
                  "--size", "content", "binary-content"):
        slug = re.sub(r"[^a-z0-9]+", "-", token.lower()).strip("-")
        add(
            f"reject-malformed-{slug}", "baseline", token,
            note="A malformed or invalid criteria token must be an explicit error, "
                 "never a silent fallback to the default.",
            expected_exit=106, expected_error="invalid_criteria", skip_reference=True,
        )
    add(
        "attrib-z-inert", "baseline", "attrib:z",
        note="OBSERVED (A3-folder-gate-serial-04, FINDINGS F5): the live Oracle "
             "accepts `criteria attrib:z` with exit 0 and a full report, so "
             "unknown attribute letters are accepted and inert. The report also "
             "shows `leftnewer.txt` as `same`, proving that naming an attribute "
             "set REPLACES the default size+timestamp pair.",
        evidence="observed",
    )
    for name in ("html", "interleaved", "csv", "text"):
        add(
            f"reject-layout-{name}", "baseline", "",
            note="help/scripting_reference.html (O): the folder-report layouts are "
                 "side-by-side, summary and xml only.",
            layout=name, expected_exit=106, expected_error="unknown_layout",
            skip_reference=True,
        )

    return cases, problems


def main(argv: list[str]) -> int:
    out = FIXTURES / "cases.json"
    cases, problems = build_cases()

    if problems:
        for line in problems:
            print(f"PROBLEM: {line}", file=sys.stderr)
        return 1

    if len(cases) < 40:
        print(f"FAIL: only {len(cases)} cases; the M3 target is >= 40", file=sys.stderr)
        return 1

    ids = [c["id"] for c in cases]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        print(f"FAIL: duplicate case ids: {dupes}", file=sys.stderr)
        return 1

    payload = {
        "manifest_version": 1,
        "generated_by": "product/dir/tools/make_cases.py",
        "case_count": len(cases),
        "honesty_boundary": (
            "There is NO golden folder report in this workspace "
            "(product/verify/README.md section 9), and task A-3 is forbidden from "
            "invoking the Oracle. Every `expected_statuses` map is therefore either "
            "(a) read out of the one Oracle artifact that exists for the audit tree "
            "pair plus the criteria measurement in product/docs/00-current-state.md "
            "section 6, or (b) computed by this file's independent Python reference "
            "model over the same generated bytes. Neither is a measured BC parity "
            "claim: the cases record THIS ENGINE'S committed behaviour under the "
            "observed criteria model. The project lead's serial Oracle pass is what "
            "upgrades a case from predicted to verified."
        ),
        "reference_model": (
            "tools/make_cases.py::ref_compare — a second implementation in Python "
            "over the same files, used so a transcription slip in the Rust engine "
            "surfaces as a disagreement between two independently written models."
        ),
        "cases": cases,
    }
    out.write_text(
        json.dumps(payload, indent=1, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {len(cases)} case(s) to {out}")
    with_status = sum(1 for c in cases if c["expected_statuses"])
    rejects = sum(1 for c in cases if c["expected_error"])
    layouts: dict[str, int] = {}
    for c in cases:
        layouts[c["layout"]] = layouts.get(c["layout"], 0) + 1
    print(f"  with status assertions: {with_status}")
    print(f"  rejection cases:        {rejects}")
    for layout, n in sorted(layouts.items()):
        print(f"  layout {layout:<14} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

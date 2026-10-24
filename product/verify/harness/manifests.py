"""Loaders for the read-only fixture manifests.

The manifests under ``D:\\Rea\\verify`` are **read-only inputs**.  This module
only reads them; it never rewrites, regenerates or relocates them.

Four sets exist today:

* ``verify/golden/manifest.json``  -- text anchors (XML reports).
  Per-anchor options are recovered from the entry's ``note`` field, which is
  written as ``options:<name>`` (e.g. ``"options:display-matches on mixed pair"``).
* ``verify/layouts/manifest.json`` -- text-layout reports.
  Cases reference shared ``<case>-L.txt`` / ``<case>-R.txt`` fixture pairs.
* ``verify/table/manifest.json``   -- table (CSV) goldens (M6.4, docs/13
  §7.3). Append-only; fixture pairs are ``<name>-L.<ext>`` / ``<name>-R.<ext>``.
  The tree is written ONLY by ``tools/m64_add_table_goldens.py`` (serial
  Oracle); this loader reads it and never rewrites.
* ``verify/hex/manifest.json``     -- hex (binary) goldens (M7, docs/14).
  Append-only; fixture pairs are ``<name>-L.bin`` / ``<name>-R.bin``. Written
  ONLY by ``tools/m71_add_hex_goldens.py`` (serial Oracle).
* ``verify/pic/manifest.json``     -- picture goldens (M9, docs/16).
  Append-only; fixtures carry their real image extension (.png/.bmp/.gif/
  .bin), so the manifest stores explicit ``left``/``right`` paths and the
  exact probe ``script`` line.  Written ONLY by
  ``tools/m91_add_pic_goldens.py`` (serial Oracle).
* ``verify/reg/manifest.json``     -- registry (.reg) goldens (M11, docs/17).
  Append-only; fixtures are ``<name>-L.reg`` / ``<name>-R.reg`` and the
  manifest stores the exact probe ``script`` line.  Written ONLY by
  ``tools/m111_add_reg_goldens.py`` (serial Oracle, REFERENCE install --
  see :class:`RegCase` for why).
* ``verify/dir/``                  -- folder fixtures (``trees/L``, ``trees/R``).
  The stored ``reports/manifest.json`` records the *old broken* invocation
  (exit 106, 0 bytes); it is retained as-is and reported, never overwritten.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field

GOLDEN_DIR = pathlib.Path(r"D:\Rea\verify\golden")
LAYOUTS_DIR = pathlib.Path(r"D:\Rea\verify\layouts")
DIR_DIR = pathlib.Path(r"D:\Rea\verify\dir")
TABLE_DIR = pathlib.Path(r"D:\Rea\verify\table")
HEX_DIR = pathlib.Path(r"D:\Rea\verify\hex")
PIC_DIR = pathlib.Path(r"D:\Rea\verify\pic")
REG_DIR = pathlib.Path(r"D:\Rea\verify\reg")
VER_DIR = pathlib.Path(r"D:\Rea\verify\ver")

_OPTION_RE = re.compile(r"options:([A-Za-z0-9+\-]+)")


@dataclass
class AnchorCase:
    """One text anchor from the golden manifest."""

    name: str
    unit: str
    note: str
    left: pathlib.Path
    right: pathlib.Path
    golden_report: pathlib.Path
    statuses: list[str]
    options: str | None
    golden_exit_code: int | None = None
    golden_seconds: float | None = None

    @property
    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right, self.golden_report)
                if not p.exists()]


@dataclass
class LayoutCase:
    """One text-layout case."""

    name: str
    layout: str
    case: str
    left: pathlib.Path
    right: pathlib.Path
    golden_report: pathlib.Path
    golden_exit_code: int | None = None
    golden_bytes: int | None = None
    #: Fixture extension. The original five cases are .txt; M2 added a .c one.
    ext: str = "txt"

    @property
    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right, self.golden_report)
                if not p.exists()]


@dataclass
class TableCase:
    """One table (CSV) golden case from the verify/table manifest.

    The table channel has no XML layout (docs/13 §1), so the golden is a
    text report compared line-wise after label/time/path normalization --
    the same mechanism as the layout suite. The fixtures carry their own
    extension (`.csv` for the fixed-comma path, `.txt` for auto-detect).
    """

    name: str
    layout: str
    ext: str
    left: pathlib.Path
    right: pathlib.Path
    golden_report: pathlib.Path
    golden_exit_code: int | None = None
    golden_bytes: int | None = None
    note: str = ""
    #: Right-side fixture extension when it differs from the left (m68
    #: pinned the mixed `.txt`/`.csv` pair: either side .csv pins comma).
    #: When set, the manifest stores explicit "left"/"right" filenames
    #: instead of the derived `<name>-L/R.<ext>` pair.
    ext_right: str = ""
    #: Optional `title:` for the script (X4: the title REPLACES the frame's
    #: first line; only one golden uses it).
    title: str | None = None

    @property
    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right, self.golden_report)
                if not p.exists()]


@dataclass
class FolderCase:
    """One folder-comparison case."""

    name: str
    left: pathlib.Path
    right: pathlib.Path
    stored_report_manifest: pathlib.Path | None = None
    stored_manifest_entries: dict = field(default_factory=dict)

    @property
    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right) if not p.exists()]


def option_of(note: str | None) -> str | None:
    """Recover ``options:<name>`` from an anchor's note field."""
    m = _OPTION_RE.search(note or "")
    return m.group(1) if m else None


def load_anchors(path: pathlib.Path | None = None) -> list[AnchorCase]:
    man = json.loads((path or (GOLDEN_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[AnchorCase] = []
    for name, info in man.items():
        out.append(AnchorCase(
            name=name,
            unit=info.get("unit", ""),
            note=info.get("note", ""),
            left=pathlib.Path(info["left"]),
            right=pathlib.Path(info["right"]),
            golden_report=pathlib.Path(info["report"]),
            statuses=list(info.get("statuses", [])),
            options=option_of(info.get("note")),
            golden_exit_code=info.get("exit_code"),
            golden_seconds=info.get("seconds"),
        ))
    return out


def load_layouts(path: pathlib.Path | None = None) -> list[LayoutCase]:
    man = json.loads((path or (LAYOUTS_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[LayoutCase] = []
    for name, info in man.items():
        case = info["case"]
        # Entries added from M2 carry an explicit "ext" so a .c case can be
        # referenced; the original five cases default to .txt as before.
        ext = info.get("ext", "txt")
        out.append(LayoutCase(
            name=name,
            layout=info["layout"],
            case=case,
            ext=ext,
            left=LAYOUTS_DIR / f"{case}-L.{ext}",
            right=LAYOUTS_DIR / f"{case}-R.{ext}",
            golden_report=pathlib.Path(info["report"]),
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
        ))
    return out


def load_table_cases(path: pathlib.Path | None = None) -> list[TableCase]:
    """Load the table golden cases from ``verify/table/manifest.json``.

    Manifest shape (append-only, like the anchor manifest):

    .. code-block:: json

       { "t-sbs-changed": {
           "layout": "side-by-side", "ext": "csv", "note": "…",
           "exit_code": 0, "bytes": 414,
           "report": "D:\\Rea\\verify\\table\\t-sbs-changed.csv" } }

    The fixture pair is derived from the case name (``<name>-L.<ext>`` /
    ``<name>-R.<ext>``) so a layout added for one pair cannot drift its
    inputs -- the layouts-suite convention (MANIFEST-FORMAT §1.2). A case
    with per-side extensions (m68's mixed ``.txt``/``.csv`` pin) stores
    ``ext_right`` and the loader derives ``<name>-R.<ext_right>``.
    """
    man = json.loads((path or (TABLE_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[TableCase] = []
    for name, info in man.items():
        ext = info["ext"]
        ext_right = info.get("ext_right", "")
        out.append(TableCase(
            name=name,
            layout=info["layout"],
            ext=ext,
            left=TABLE_DIR / f"{name}-L.{ext}",
            right=TABLE_DIR / f"{name}-R.{ext_right or ext}",
            golden_report=pathlib.Path(info["report"]),
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
            note=info.get("note", ""),
            ext_right=ext_right,
            title=info.get("title") or None,
        ))
    return out


@dataclass
class HexCase:
    """One hex (binary) golden case from the verify/hex manifest.

    Like the table suite, the channel has no XML layout (docs/14), so the
    golden is a text report compared line-wise after label/time/path
    normalization. The fixtures are ``<name>-L.bin`` / ``<name>-R.bin``.
    """

    name: str
    layout: str
    left: pathlib.Path
    right: pathlib.Path
    golden_report: pathlib.Path
    golden_exit_code: int | None = None
    golden_bytes: int | None = None
    note: str = ""
    title: str | None = None

    @property
    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right, self.golden_report)
                if not p.exists()]


def load_hex_cases(path: pathlib.Path | None = None) -> list[HexCase]:
    """Load the hex golden cases from ``verify/hex/manifest.json``.

    Manifest shape (append-only, like the table manifest):

    .. code-block:: json

       { "h-sbs-equal": {
           "layout": "side-by-side", "note": "…",
           "exit_code": 0, "bytes": 823,
           "report": "D:\\Rea\\verify\\hex\\h-sbs-equal.txt" } }

    The fixture pair is derived from the case name (``<name>-L.bin`` /
    ``<name>-R.bin``); ``title`` (when present) goes into the script's
    ``title:`` (V3/Y11).
    """
    man = json.loads((path or (HEX_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[HexCase] = []
    for name, info in man.items():
        out.append(HexCase(
            name=name,
            layout=info["layout"],
            left=HEX_DIR / f"{name}-L.bin",
            right=HEX_DIR / f"{name}-R.bin",
            golden_report=pathlib.Path(info["report"]),
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
            note=info.get("note", ""),
            title=info.get("title") or None,
        ))
    return out


@dataclass
class PicCase:
    """One picture golden case from the verify/pic manifest (M9, docs/16).

    Like the hex/table suites the channel has no XML layout; the golden is a
    text report compared line-wise after label/time/path normalization
    (norm-4).  Fixtures carry real image extensions (.png/.bmp/.gif/.bin), so
    the manifest names left/right explicitly and stores the exact probe
    ``script`` line -- the same bytes the Oracle was measured with.
    """

    name: str
    layout: str
    left: pathlib.Path | None
    right: pathlib.Path | None
    golden_report: pathlib.Path
    script: str
    golden_exit_code: int | None = None
    golden_bytes: int | None = None
    note: str = ""

    @property
    def missing(self) -> list[str]:
        paths = [p for p in (self.left, self.right, self.golden_report)
                 if p is not None]
        return [str(p) for p in paths if not p.exists()]


def load_pic_cases(path: pathlib.Path | None = None) -> list[PicCase]:
    """Load the picture golden cases from ``verify/pic/manifest.json``.

    Manifest shape (append-only, like the hex manifest):

    .. code-block:: json

       { "p-sum-equal": {
           "layout": "summary", "note": "…", "script": "picture-report …",
           "left": "…p-sum-equal-L.png", "right": "…p-sum-equal-R.png",
           "exit_code": 0, "bytes": 258,
           "report": "D:\\Rea\\verify\\pic\\p-sum-equal.txt" } }

    ``left``/``right`` are absolute stored paths (the extension varies by
    fixture); a zero-file cell stores ``""`` and loads as ``None``, which the
    runner passes to the Oracle as the empty argument the probe used.
    """
    man = json.loads((path or (PIC_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[PicCase] = []
    for name, info in man.items():
        out.append(PicCase(
            name=name,
            layout=info["layout"],
            left=pathlib.Path(info["left"]) if info.get("left") else None,
            right=pathlib.Path(info["right"]) if info.get("right") else None,
            golden_report=pathlib.Path(info["report"]),
            script=info["script"],
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
            note=info.get("note", ""),
        ))
    return out


@dataclass
class RegCase:
    """One registry (.reg) golden case from the verify/reg manifest (M11).

    Like the hex/table/pic suites the channel has no XML layout; the golden
    is a text report compared line-wise after label/time/path normalization
    (norm-5).  Fixtures carry the ``.reg`` extension and are named
    ``<name>-L.reg`` / ``<name>-R.reg``; the manifest stores the exact probe
    ``script`` line.

    The goldens are AUTHORED FROM THE REFERENCE (English) INSTALL: the
    side-by-side table geometry is locale-dependent (the column floors are
    the header-label widths, so the Chinese 名称/类型/数据 labels produce a
    narrower table than English Name/Type/Data for the same fixtures), and
    the product renders the English frame (the dir/pic/hex precedent).  The
    Chinese geometry is locked by ``reacmp-reg/tests/corpus_cases.rs``
    instead of by goldens.
    """

    name: str
    layout: str
    left: pathlib.Path | None
    right: pathlib.Path | None
    golden_report: pathlib.Path
    script: str
    golden_exit_code: int | None = None
    golden_bytes: int | None = None
    note: str = ""

    @property
    def missing(self) -> list[str]:
        paths = [p for p in (self.left, self.right, self.golden_report)
                 if p is not None]
        return [str(p) for p in paths if not p.exists()]


def load_reg_cases(path: pathlib.Path | None = None) -> list[RegCase]:
    """Load the registry golden cases from ``verify/reg/manifest.json``.

    Manifest shape (append-only, like the pic manifest)::

       { "r-sbs-equal": {
           "layout": "side-by-side", "note": "…", "script": "registry-report …",
           "left": "…r-sbs-equal-L.reg", "right": "…r-sbs-equal-R.reg",
           "exit_code": 0, "bytes": 414,
           "report": "D:\\Rea\\verify\\reg\\r-sbs-equal.txt" } }

    ``left``/``right`` are absolute stored paths; a zero-file cell stores
    ``""`` and loads as ``None``, which the runner passes to the Oracle as
    the empty argument the probe used.
    """
    man = json.loads((path or (REG_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[RegCase] = []
    for name, info in man.items():
        out.append(RegCase(
            name=name,
            layout=info["layout"],
            left=pathlib.Path(info["left"]) if info.get("left") else None,
            right=pathlib.Path(info["right"]) if info.get("right") else None,
            golden_report=pathlib.Path(info["report"]),
            script=info["script"],
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
            note=info.get("note", ""),
        ))
    return out



def load_folder_cases(root: pathlib.Path | None = None) -> list[FolderCase]:
    """Discover folder cases.

    The existing fixture set is a single pair (``trees/L`` vs ``trees/R``).
    Discovery is directory-based so that new fixtures added under
    ``verify/dir/trees/`` are found automatically -- but the loader does not
    write anything, and the stored (broken) report manifest is preserved and
    surfaced as historical evidence rather than regenerated.
    """
    root = root or DIR_DIR
    trees = root / "trees"
    out: list[FolderCase] = []
    stored_manifest = root / "reports" / "manifest.json"
    stored: dict = {}
    if stored_manifest.exists():
        try:
            stored = json.loads(stored_manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stored = {}
    if trees.is_dir():
        ldir, rdir = trees / "L", trees / "R"
        if ldir.is_dir() or rdir.is_dir():
            out.append(FolderCase(
                name="trees",
                left=ldir,
                right=rdir,
                stored_report_manifest=stored_manifest if stored_manifest.exists() else None,
                stored_manifest_entries=stored,
            ))
    return out


def statuses_from_xml(xml_text: str) -> list[str]:
    """Extract the ``linecomp/@status`` sequence.

    Kept as a regex rather than a parse so it still works on the three golden
    reports that contain XML-illegal control-character references (SsXML emits
    decimal refs for control codes; a conforming parser rejects them).
    """
    return re.findall(r'<linecomp status="([a-z]+)"', xml_text)


class VerCase:
    """One version golden (docs/18 §9), mirroring :class:`RegCase`."""

    __slots__ = ("name", "layout", "left", "right", "golden_report",
                 "script", "golden_exit_code", "golden_bytes", "note")

    def __init__(self, *, name: str, layout: str, left: pathlib.Path | None,
                 right: pathlib.Path | None, golden_report: pathlib.Path,
                 script: str, golden_exit_code: int | None,
                 golden_bytes: int | None, note: str = "") -> None:
        self.name = name
        self.layout = layout
        self.left = left
        self.right = right
        self.golden_report = golden_report
        self.script = script
        self.golden_exit_code = golden_exit_code
        self.golden_bytes = golden_bytes
        self.note = note


    def missing(self) -> list[str]:
        return [str(p) for p in (self.left, self.right, self.golden_report)
                if p is not None and not p.exists()]


def load_ver_cases(path: pathlib.Path | None = None) -> list[VerCase]:
    """Load the version golden cases from ``verify/ver/manifest.json``.

    Same manifest shape as the registry one (append-only).  ``left``/
    ``right`` are absolute stored paths; the zero-file shell cell stores
    ``""`` and loads as ``None``.
    """
    man = json.loads((path or (VER_DIR / "manifest.json")).read_text(encoding="utf-8"))
    out: list[VerCase] = []
    for name, info in man.items():
        out.append(VerCase(
            name=name,
            layout=info["layout"],
            left=pathlib.Path(info["left"]) if info.get("left") else None,
            right=pathlib.Path(info["right"]) if info.get("right") else None,
            golden_report=pathlib.Path(info["report"]),
            script=info["script"],
            golden_exit_code=info.get("exit_code"),
            golden_bytes=info.get("bytes"),
            note=info.get("note", ""),
        ))
    return out


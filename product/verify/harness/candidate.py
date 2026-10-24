"""Candidate adapter -- the reserved entry point for the future product.

The product under construction (task A-2 / A-3) does not exist yet.  What this
module provides is the *seam*: a declarative, file-driven description of how to
turn a test case into a candidate command, so that wiring in the real
``reacmp`` binary later is a config change rather than a harness change.

The one candidate wired up today is the old Rust prototype
``D:\\Rea\\clone\\target\\debug\\bcx.exe``.  It is **not the product**; it is
used only to prove the adapter works end to end.  Its identity is recorded on
every result and every report it produces is labelled ``subject=candidate``.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Any

#: Default candidate registry.  Adding the real product later means adding an
#: entry here (or passing a different config file), not editing the runner.
DEFAULT_CANDIDATES: dict[str, dict[str, Any]] = {
    "bcx-prototype": {
        "label": "bcx.exe (old Rust prototype, 661 lines, NOT the product)",
        "kind": "prototype",
        "is_product": False,
        "path": r"D:\Rea\clone\target\debug\bcx.exe",
        "note": (
            "Spec-level validator from the earlier phase. cargo test runs 0 "
            "tests; its 45/45 came from tools/bcx-verify.py. Kept only to "
            "exercise the adapter."
        ),
        # CLI shape: bcx <left> <right> [out.xml] [--opt=<options>] [--layout=<layout>]
        # Verified against src/main.rs: when argv[3] is present and does not
        # start with "--", the report is written to that file; otherwise it goes
        # to stdout. The adapter therefore always passes an output path.
        "argv": ["{path}", "{left}", "{right}", "{output}"],
        "option_flag": "--opt={options}",
        "layout_flag": "--layout={layout}",
        "writes_report_file": True,
        "report_on_stdout": False,
        "text_script_unsupported": True,
        "folder_unsupported": True,
    },
}

#: The real product.  Task A-2 (milestone M1) built it at the seam path, so it
#: is wired in with zero harness changes; the runner reports it with
#: ``subject=candidate`` and ``is_product=True``.
RESERVED_PRODUCT_ENTRY: dict[str, Any] = {
    "reacmp": {
        "label": "reacmp (product CLI, built by task A-2 / milestone M1)",
        "kind": "product",
        "is_product": True,
        "path": r"D:\Rea\product\cli\target\release\reacmp.exe",
        "note": "Product text-comparison CLI. Before M1 this entry was "
                "declared-but-absent and reported as not_run; test_runner's "
                "not_run coverage now uses a synthetic absent candidate.",
        "argv": ["{path}", "{left}", "{right}", "{output}"],
        "option_flag": "--opt={options}",
        "layout_flag": "--layout={layout}",
        "writes_report_file": True,
        "report_on_stdout": False,
        "text_script_unsupported": False,
        "folder_unsupported": False,
        # M6.4: data-report graduated into the product CLI, so the table
        # suite can script-invoke it exactly like the Oracle.
        "supports_table": True,
        # M7: hex-report graduated the same way (docs/14).
        "supports_hex": True,
        # M9: picture-report (docs/16), same script-vs-script mechanism.
        "supports_pic": True,
        # M11: registry-report (docs/17), same script-vs-script mechanism.
        # The goldens are the English (reference-install) form, which is what
        # the product renders, so the comparison is byte-level.
        "supports_reg": True,
        # M112: version-report (docs/18), same script-vs-script mechanism;
        # same English-golden reasoning.
        "supports_ver": True,
    },
}


@dataclass
class CandidateAdapter:
    key: str
    label: str
    kind: str
    is_product: bool
    path: str
    note: str = ""
    argv: list[str] = field(default_factory=lambda: ["{path}", "{left}", "{right}", "{output}"])
    option_flag: str = "--opt={options}"
    layout_flag: str = "--layout={layout}"
    writes_report_file: bool = True
    report_on_stdout: bool = False
    text_script_unsupported: bool = False
    folder_unsupported: bool = False
    #: Script-invocation argv used by the M6.4 table suite: the product's
    #: data-report runs ONLY inside a @script (BC-faithful), so the harness
    #: writes the identical script the Oracle gets and the candidate is
    #: invoked as `/silent @<script> <left> <right> <out>` -- a true
    #: script-vs-script comparison of the archived golden.
    script_argv: list[str] = field(default_factory=lambda:
                                  ["{path}", "/silent", "@{script}",
                                   "{left}", "{right}", "{output}"])
    supports_table: bool = False
    #: M7: the same script-vs-script mechanism for the hex channel.
    supports_hex: bool = False
    #: M9: the picture channel.  The golden set has a zero-file cell whose
    #: script takes NO comparison arguments at all, so `pic_argv` omits the
    #: positional left/right of `script_argv` and instead interpolates
    #: `{files}` -- the case's joined comparison list ("" for the shell).
    #: Callers use `pic_script_command`.
    supports_pic: bool = False
    pic_argv: list[str] = field(default_factory=lambda:
                                ["{path}", "/silent", "@{script}",
                                 "{files}", "{output}"])
    #: M11: the registry channel.  Same script-vs-script mechanism as
    #: table/hex/pic; the product's registry-report graduated in M11, and the
    #: golden set's zero-file shell cells reuse `pic_argv` (the comparison
    #: arguments are the case's joined file list).
    supports_reg: bool = False
    #: M112: the version channel (docs/18); same script-vs-script mechanism
    #: as registry, reusing `pic_argv` for the zero-file shell cell.
    supports_ver: bool = False
    available: bool = False
    version: str = ""

    def script_command(self, *, script: str, left: str, right: str,
                       output: str) -> list[str]:
        subs = {"path": self.path, "script": str(script), "left": str(left),
                "right": str(right), "output": str(output)}
        return [part.format(**subs) for part in self.script_argv]

    def pic_script_command(self, *, script: str, files: list[str],
                           output: str) -> list[str]:
        """The M9 picture form: the comparison arguments are exactly the
        ``files`` list (0 or 2 entries), joined verbatim -- the zero-file
        shell golden must reach the candidate with no file arguments."""
        subs = {"path": self.path, "script": str(script),
                "output": str(output)}
        cmd: list[str] = []
        for part in self.pic_argv:
            if "{files}" in part:
                cmd.extend(files)
            else:
                cmd.append(part.format(**subs))
        return cmd

    def command(self, *, left: str, right: str, output: str,
                options: str | None = None, layout: str | None = None) -> list[str]:
        """Build the candidate's command line for one case."""
        subs = {
            "path": self.path, "left": str(left), "right": str(right),
            "output": str(output),
            "options": options or "", "layout": layout or "",
        }
        cmd = [part.format(**subs) for part in self.argv]
        if options and self.option_flag:
            cmd.append(self.option_flag.format(**subs))
        if layout and self.layout_flag:
            cmd.append(self.layout_flag.format(**subs))
        return cmd

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def load_candidates(config_path: str | pathlib.Path | None = None,
                    *, include_reserved: bool = True) -> dict[str, CandidateAdapter]:
    """Load candidate definitions from a JSON config, else the built-in set."""
    entries: dict[str, dict[str, Any]] = {}
    if config_path is not None:
        p = pathlib.Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"candidate config not found: {p}")
        entries.update(json.loads(p.read_text(encoding="utf-8")))
    else:
        entries.update(DEFAULT_CANDIDATES)
    if include_reserved:
        for k, v in RESERVED_PRODUCT_ENTRY.items():
            entries.setdefault(k, v)

    out: dict[str, CandidateAdapter] = {}
    for key, cfg in entries.items():
        cfg = dict(cfg)
        cfg.setdefault("key", key)
        ad = CandidateAdapter(
            key=key,
            label=cfg.get("label", key),
            kind=cfg.get("kind", "candidate"),
            is_product=bool(cfg.get("is_product", False)),
            path=cfg.get("path", ""),
            note=cfg.get("note", ""),
            argv=list(cfg.get("argv", ["{path}", "{left}", "{right}", "{output}"])),
            option_flag=cfg.get("option_flag", "--opt={options}"),
            layout_flag=cfg.get("layout_flag", "--layout={layout}"),
            writes_report_file=bool(cfg.get("writes_report_file", True)),
            report_on_stdout=bool(cfg.get("report_on_stdout", False)),
            text_script_unsupported=bool(cfg.get("text_script_unsupported", False)),
            folder_unsupported=bool(cfg.get("folder_unsupported", False)),
            script_argv=list(cfg.get("script_argv",
                                     ["{path}", "/silent", "@{script}",
                                      "{left}", "{right}", "{output}"])),
            supports_table=bool(cfg.get("supports_table", False)),
            supports_hex=bool(cfg.get("supports_hex", False)),
            supports_pic=bool(cfg.get("supports_pic", False)),
            supports_reg=bool(cfg.get("supports_reg", False)),
            supports_ver=bool(cfg.get("supports_ver", False)),
            pic_argv=list(cfg.get("pic_argv",
                                  ["{path}", "/silent", "@{script}",
                                   "{files}", "{output}"])),
        )
        ad.available = bool(ad.path) and pathlib.Path(ad.path).exists()
        if ad.available and ad.path.lower().endswith((".exe", ".dll", ".com")):
            from .installs import pe_file_version
            ad.version = pe_file_version(ad.path)
        out[key] = ad
    return out


def candidate_report(cands: dict[str, CandidateAdapter]) -> str:
    lines = ["Candidate adapters", ""]
    for key, c in cands.items():
        tag = "PRODUCT" if c.is_product else "prototype"
        lines.append(f"[{key}] ({tag}) {c.label}")
        lines.append(f"    path={c.path}")
        lines.append(f"    available={c.available}  version={c.version or 'n/a'}")
        if c.note:
            lines.append(f"    note={c.note}")
        lines.append("")
    return "\n".join(lines)

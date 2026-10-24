"""Install identity discovery.

Version identity is read from the actual files, never inferred from directory
names.  Hashes are computed in-process; when printed they must be emitted in
8-hex-digit groups, because this environment's tool output renders long
contiguous hex strings as an all-zero placeholder (see
``product/docs/00-current-state.md`` section 7).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import struct
from dataclasses import dataclass, field, asdict
from typing import Any


def sha256_file(path: str | pathlib.Path, chunk: int = 1 << 20) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            d.update(block)
    return d.hexdigest()


def grouped_hex(hexstr: str, group: int = 8) -> str:
    """Render a long hex string in groups so it survives the display quirk."""
    return " ".join(hexstr[i:i + group] for i in range(0, len(hexstr), group))


def pe_file_version(path: str | pathlib.Path) -> str:
    """Read the PE resource FileVersion with the standard library only.

    ``win32api``/``powershell`` are avoided so the harness runs anywhere and so
    the value is measured rather than shelled out for.

    The RT_VERSION blob is located by its ``VS_VERSION_INFO`` key rather than by
    walking the three-level resource directory tree: the tree walk needs
    per-level offset-base rules and silently returns wrong bytes when a level is
    misread, whereas the key plus its ``wValueLength`` (always 52, the size of
    VS_FIXEDFILEINFO) is self-validating.

    Returns ``""`` when the resource is absent or malformed.  Callers must treat
    an empty version as *unknown*, never as a match.
    """
    try:
        data = pathlib.Path(path).read_bytes()
    except OSError:
        return ""
    if len(data) < 0x40 or data[:2] != b"MZ":
        return ""
    key = "VS_VERSION_INFO".encode("utf-16-le") + b"\x00\x00"
    sig = struct.pack("<I", _VS_SIGNATURE)
    start = 0
    while True:
        at = data.find(key, start)
        if at < 0:
            return ""
        start = at + 2
        if at < 6:
            continue
        _w_len, w_val_len, w_type = struct.unpack_from("<HHH", data, at - 6)
        if w_val_len != 52 or w_type != 0:
            continue                      # not the version resource
        at_sig = data.find(sig, at + len(key), at + len(key) + 16)
        if at_sig < 0:
            continue
        return _format_version(data, at_sig)


def _format_version(data: bytes, at_sig: int) -> str:
    struc_version = struct.unpack_from("<I", data, at_sig + 4)[0]
    if struc_version != 0x00010000:
        return ""
    ms, ls = struct.unpack_from("<II", data, at_sig + 8)
    if ms == 0 and ls == 0:
        return ""
    return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"


#: VS_FIXEDFILEINFO.dwSignature.  It is the one unambiguous anchor inside a
#: RT_VERSION blob, so the fixed-file-info is located by searching for it
#: rather than by walking the (word-aligned, length-prefixed) VS_VERSIONINFO
#: tree -- fewer assumptions, same answer.
_VS_SIGNATURE = 0xFEEF04BD


@dataclass
class InstallIdentity:
    """One Beyond Compare installation, identified by measurement."""

    key: str                     # stable short key used in reports
    label: str                   # human label incl. version + locale
    oracle_path: str             # BComp.com (the console Oracle)
    app_path: str                # BCompare.exe (the engine host)
    oracle_version: str = ""     # version read from the file itself
    app_version: str = ""
    oracle_sha256: str = ""
    app_sha256: str = ""
    oracle_size: int = 0
    app_size: int = 0
    locale: str = "unknown"      # "en" | "zh" | "unknown"
    localization_evidence: list[str] = field(default_factory=list)
    enabled: bool = True
    disabled_reason: str = ""

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["oracle_sha256_grouped"] = grouped_hex(self.oracle_sha256)
        d["app_sha256_grouped"] = grouped_hex(self.app_sha256)
        return d


#: Locale detection is by the presence of the translation resource that the
#: Chinese repack ships and the official English build does not.  Both installs
#: are otherwise structurally identical, so the file presence is the only
#: reliable discriminator available before running anything.
def _detect_locale(app_dir: pathlib.Path) -> tuple[str, list[str]]:
    ev: list[str] = []
    tr = app_dir / "BCompare.tr"
    if tr.exists():
        ev.append(f"{tr.name} present ({tr.stat().st_size} bytes)")
        return "zh", ev
    ev.append("no BCompare.tr translation resource")
    return "en", ev


def describe_install(key: str, label: str, oracle_path: str, app_path: str) -> InstallIdentity:
    inst = InstallIdentity(key=key, label=label,
                           oracle_path=oracle_path, app_path=app_path)
    op, ap = pathlib.Path(oracle_path), pathlib.Path(app_path)
    if op.exists():
        inst.oracle_version = pe_file_version(op)
        inst.oracle_sha256 = sha256_file(op)
        inst.oracle_size = op.stat().st_size
    else:
        inst.enabled = False
        inst.disabled_reason = f"oracle not found: {oracle_path}"
    if ap.exists():
        inst.app_version = pe_file_version(ap)
        inst.app_sha256 = sha256_file(ap)
        inst.app_size = ap.stat().st_size
    else:
        inst.enabled = False
        inst.disabled_reason = (inst.disabled_reason + f"; app not found: {app_path}").strip("; ")
    loc, ev = _detect_locale(ap.parent if ap.exists() else pathlib.Path(app_path).parent)
    inst.locale = loc
    inst.localization_evidence = ev
    return inst


#: The two installs this workspace knows about.  The CURRENT target is the
#: declared project target; the reference install exists only to supply English
#: label text (see product/docs/05-acceptance-strategy.md section 5).
DEFAULT_INSTALLS = {
    "current": dict(
        label="current 5.2.1.32035 (Chinese repack) - project target",
        oracle_path=r"D:\BCompare\BCompare\BComp.com",
        app_path=r"D:\BCompare\BCompare\BCompare.exe",
    ),
    "reference": dict(
        label="reference 5.2.6.32774 (English) - label reference only",
        oracle_path=r"D:\bc-official\app\BComp.com",
        app_path=r"D:\bc-official\app\BCompare.exe",
    ),
}


def discover(only: str | None = None) -> dict[str, InstallIdentity]:
    out: dict[str, InstallIdentity] = {}
    for key, kw in DEFAULT_INSTALLS.items():
        if only and key != only:
            continue
        out[key] = describe_install(key, **kw)
    return out


def identity_report(installs: dict[str, InstallIdentity]) -> str:
    lines = ["Install identity (measured from the files, not the directory names)", ""]
    for key, i in installs.items():
        lines.append(f"[{key}] {i.label}")
        lines.append(f"    oracle (BComp.com) : {i.oracle_path}")
        lines.append(f"      version={i.oracle_version or 'UNKNOWN'}  size={i.oracle_size}")
        lines.append(f"      sha256 ={grouped_hex(i.oracle_sha256)}")
        lines.append(f"    engine (BCompare.exe): {i.app_path}")
        lines.append(f"      version={i.app_version or 'UNKNOWN'}  size={i.app_size}")
        lines.append(f"      sha256 ={grouped_hex(i.app_sha256)}")
        lines.append(f"    locale={i.locale}  evidence={i.localization_evidence}")
        if not i.enabled:
            lines.append(f"    DISABLED: {i.disabled_reason}")
        lines.append("")
    return "\n".join(lines)


def write_identity(installs: dict[str, InstallIdentity], path: str | pathlib.Path) -> None:
    payload = {k: v.to_json() for k, v in installs.items()}
    pathlib.Path(path).write_text(json.dumps(payload, indent=1, ensure_ascii=False),
                                  encoding="utf-8")

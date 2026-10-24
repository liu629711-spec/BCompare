"""Versioned, reviewable report normalisation.

Design constraints (from the A-1 task statement and
``product/docs/02-version-and-evidence.md``):

* Only **confirmed** label pairs, explicitly identified report titles / count
  labels, and volatile time + header path fields are handled.  Every rule below
  carries the observation that justified it.
* Reports are **structurally parsed**; only confirmed tags/attributes are
  normalised.  Difference status, ordering, left/right content, line numbers and
  the report body are preserved verbatim.
* Text layouts: only explicitly identified header/label lines are rewritten.
  There are **no** broad regexes that blank out body lines.
* Anything the rules do not recognise raises :class:`NormalizerRefusal` instead
  of being guessed at or silently dropped.

Rule-set version is ``norm-1``.  Bump it whenever a rule is added or changed;
the version string is recorded on every test result so a historical run can be
traced to the exact rule set that produced it.
"""

from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable

from .taxonomy import NormalizerRefusal

RULESET_VERSION = "norm-6"
# norm-2 (M6.4): the table channel joined the harness, adding its title,
# header and count labels below. The added rules only fire on strings the
# text channel never emits (表格比较(B)/...排), so every norm-1 anchor and
# layout verdict is unchanged under norm-2 -- the gate re-run confirms this.
# norm-3 (M7): the hex channel joins; it adds the hex title (16 进制比较(H))
# and the byte-count labels (…字节, runs/m70e + m70e2 measured on both
# installs). The same "text channel never emits these" argument holds, so
# anchor/layout/table verdicts are unchanged under norm-3 (gate re-run:
# M71-gate-01).
# norm-4 (M9): the picture channel joins; it adds its title (图片比较(P)),
# the ignoring-unimportant header, the base-folder shell line, the two
# error-line forms (…不被支持的类型 / …无效图像) and the pixel-count labels
# (…像素, runs/m83..m83o measured on the current install and corroborated
# in English by the reference install in runs/m83k-m83m). All are strings no
# earlier channel emits, so existing verdicts are unchanged under norm-4
# (gate re-run: M91-gate-01).
# norm-5 (M11): the registry channel joins; it adds its title (注册表比较(R)),
# the two extra Mode lines (差异/相同), the error-line patterns (解析错误 with
# the line:col data, 删除/重复跳过, and the encoding form, which is the SAME
# text as picture's File Encoding Error -- matched by a prefix pattern rather
# than a label pair because it carries the line number) and the item-count
# labels (…项, runs/m101/m101c/m101f measured on the current install and
# corroborated in English by the reference install in
# m101f-regbox-reference, 29 shared cells). The table BODY geometry is
# locale-dependent (the column floors are the header-label widths), so the
# registry goldens are authored from the reference install and the Chinese
# geometry is locked by the product's own corpus tests instead; the new
# count/error rules are what let a Chinese-install re-run fold onto them.
# All are strings no earlier channel emits, so existing verdicts are
# unchanged under norm-5 (gate re-run: M111-gate-01).


# --------------------------------------------------------------------------
# Rule 1 -- confirmed localisation label pairs
# --------------------------------------------------------------------------
# Every pair below was OBSERVED by running the current 5.2.1.32035 (Chinese
# repack) and the reference 5.2.6.32774 (English) installs on the SAME
# fixtures and diffing their reports.  No pair is inferred from documentation.
#
# XML label pairs (element text of a known element).
XML_LABEL_PAIRS: dict[tuple[str, str], tuple[str, str]] = {
    # (tag, chinese) -> english      observed in
    ("mode", "差异"): ("mode", "Differences"),                       # opt-display-mismatches
    ("mode", "相同"): ("mode", "Same"),                              # opt-display-matches
    ("mode", "差异, 带上下文"): ("mode", "Differences, With Context"),  # opt-display-context
}

# <error1> is "文件编码错误 (第 N 行)" / "File Encoding Error (Line N)".
# N is DATA (the failing line number) and must survive normalisation.
XML_ERROR1_PATTERNS = (
    re.compile(r"^文件编码错误 \(第 (\d+) 行\)$"),
    re.compile(r"^File Encoding Error \(Line (\d+)\)$"),
)

# --------------------------------------------------------------------------
# Rule 2b -- registry error lines (norm-5, M11, docs/17)
# --------------------------------------------------------------------------
# The registry channel's error lines carry DATA (the parse position, the
# encoding line number), so they are matched as whole-line patterns rather
# than as label-pair keys.  Observed forms, both installs:
#   左边错误： 解析错误 (L： C)   / Left error: Parsing Error (L: C)
#   右边错误： 删除/重复跳过      / Right error: Deletes/Duplicates Skipped
#   左边错误： 文件编码错误 (第 N 行) / Left error: File Encoding Error (Line N)
# The side label is a prefix (左边/右边 + fullwidth colon + one ASCII space);
# everything after it is matched by the side-specific payload pattern.
# The Unsupported Type text is identical to picture's and is already in
# TEXT_LABEL_PAIRS.
_REG_SIDE = r"(?P<side>左边|右边)错误： "
REG_TEXT_ERROR_PATTERNS = (
    # Parsing Error: line and column are DATA.  The Chinese form uses a
    # FULLWIDTH colon between them (measured: 解析错误 (3： 38)).
    (re.compile(_REG_SIDE + r"解析错误 \((?P<line>\d+)： (?P<col>\d+)\)$"),
     r"{side_en} error: Parsing Error ({line}: {col})"),
    (re.compile(_REG_SIDE + r"Parsing Error \((?P<line>\d+): (?P<col>\d+)\)$"),
     r"{side_en} error: Parsing Error ({line}: {col})"),
    # Deletes/Duplicates Skipped: no data.
    (re.compile(_REG_SIDE + r"删除/重复跳过$"),
     r"{side_en} error: Deletes/Duplicates Skipped"),
    (re.compile(_REG_SIDE + r"Deletes/Duplicates Skipped$"),
     r"{side_en} error: Deletes/Duplicates Skipped"),
    # File Encoding Error (Line N): N is DATA.  The Chinese parenthesised
    # form uses the same spacing as picture's 文件编码错误 (第 N 行).
    (re.compile(_REG_SIDE + r"文件编码错误 \(第 (?P<line>\d+) 行\)$"),
     r"{side_en} error: File Encoding Error (Line {line})"),
    (re.compile(_REG_SIDE + r"File Encoding Error \(Line (?P<line>\d+)\)$"),
     r"{side_en} error: File Encoding Error (Line {line})"),
)

# Version channel (m112 on the current install; every English form is
# corroborated by the verify/ver goldens authored on the reference install).
# These are PREFIX rules: the label is the leading text of a frame/table line
# and the rest of the line (paths, values, markers, padding) is DATA that
# must survive.  A prefix here is only added after both forms were observed
# on the same fixture -- the v-sbs-equal golden is the ZH/EN twin.
VER_LINE_PREFIXES: tuple[tuple[str, str], ...] = (
    # frame file lines (the path payload survives)
    ("左边文件： ", "Left file: "),
    ("右边文件： ", "Right file: "),
    ("文件： ", "File: "),
    # group headings: bare rows, but a prefix swap is still safe because the
    # heading occupies the whole cell and every longer line starts with a
    # connector (fixed by the m112 corpus: no group heading is a prefix of a
    # value row in either locale).
    ("代码", "Code"),
    ("PE 头信息", "PE Header"),
    ("固定", "Fixed"),
    ("翻译", "Translation"),
    ("变化", "Variable"),
    # value rows
    ("\数据", "\Data"),
    ("+操作系统", "+Operating System"),
    ("+处理器", "+Processor"),
    ("+创建日期", "+Creation Date"),
    ("+标志", "+Flags"),
    ("+链接器版本", "+Linker Version"),
    ("+图像库", "+Image Base"),
    ("+图像版本", "+Image Version"),
    ("+校验", "+Checksum"),
    ("+用户界面", "+User Interface"),
    ("\DLL 旗帜", "\DLL Flags"),
    ("+文件版本", "+File Version"),
    ("+产品版本", "+Product Version"),
    ("\文件类型", "\File Type"),
    ("\语言", "\Languages"),
    ("+语言", "+Language"),
)

# Text layout label pairs (whole line, after time/path normalisation).
TEXT_LABEL_PAIRS: dict[str, str] = {
    "文本比较(T)": "Text Compare",
    "表格比较(B)": "Table Compare",          # table channel title (m62-reflabels)
    "16 进制比较(H)": "Hex Compare",          # hex channel title (m70e, both installs)
    "图片比较(P)": "Picture Compare",         # picture channel title (m83, current install)
    "正在忽略不重要": "Ignoring Unimportant",  # picture options:ignore-unimportant header (m83b Q3-4, m83g IGNORE-line, m83n O4; English form in m83k)
    "基点文件夹： ": "Base folder: ",           # picture zero-file shell line, trailing space observed (m83 P8, m83n O5)
    # Picture error lines (m83 P12 / m83l EN-mixed-error; fullwidth colon +
    # one ASCII space observed on the current install, English pair on the
    # reference install).
    "左边错误： 不被支持的类型": "Left error: Unsupported Type",
    "右边错误： 不被支持的类型": "Right error: Unsupported Type",
    "左边错误： 无效图像": "Left error: Invalid image",
    "右边错误： 无效图像": "Right error: Invalid image",
    # Registry channel (m101/m101c/m101f, both installs).  The Mode line
    # mirrors picture's fullwidth-colon + two-ASCII-space form; the error
    # lines use the same 左边/右边错误： + one ASCII space shape, and the
    # static texts are identical to picture's (不被支持的类型) -- both map to
    # the SAME English line, which is fine because the labels are whole-line
    # keys.  Deletes/Duplicates Skipped and the Parsing Error form carry data
    # (line:col) or are dynamic, so they are matched by the dedicated
    # REGISTRY_LINE rules below, not here.
    "注册表比较(R)": "Registry Compare",           # registry title (m101 R1)
    "模式：  差异": "Mode:  Differences",           # display-mismatches (I4)
    "模式：  相同": "Mode:  Same",                  # display-matches (I12)
    # Version channel (m112 on the current install; the English wording is
    # corroborated by the verify/ver goldens authored on the reference
    # install).  The ver labels ride the same whole-line pairs.
    "版本比较(V)": "Version Compare",               # version title (m112 V1)
    "模式：  全部, 正在忽略不重要": "Mode:  All, Ignoring Unimportant",  # ver options:ignore-unimportant (m112b W11)
    "已产生：": "Produced:",
    "模式：  全部": "Mode:  All",
    # statistics CSV header
    "源文件,比较文件,I最初,I添加,I删除,I改变,U最初,U添加,U删除,U改变,来源错误,比较错误,错误":
        "SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,"
        "UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error",
}

# Count labels.  The NUMBER is data and must survive; only the wording moves.
# e.g. "2 个相同行" <-> "2 same line(s)"
#
# IMPORTANT: every key below was OBSERVED.  Note that the translation is itself
# inconsistent in the repack -- "重要的左边独有行" carries 的 but
# "重要右边独有行" does not.  Unobserved variants (e.g. a hypothetical
# "重要的右边独有行") are deliberately NOT listed: they must surface as
# ``unparseable`` so the rule set gets extended from evidence rather than from
# a guess.
TEXT_COUNT_LABELS: dict[str, str] = {
    "个相同行": "same line(s)",
    "个不重要的差异行": "unimportant difference line(s)",
    "个重要的左边独有行": "important left orphan line(s)",
    "个重要右边独有行": "important right orphan line(s)",
    "个重要差异行": "important difference line(s)",
    # Observed in u3/u3b (M2): one-sided unimportant lines have their own
    # summary counts, ordered BEFORE the unimportant-difference count.
    "个不重要的左边独有行": "unimportant left orphan line(s)",
    "个不重要的右边独有行": "unimportant right orphan line(s)",
    "个差异部分": "difference section(s)",
    # Table channel counts (m62-reflabels, observed on both installs). The
    # repack's `的` asymmetry mirrors the text channel: left carries it,
    # right does not. 排 = row.
    "个相同排": "same row(s)",
    "个重要差异排": "important difference row(s)",
    "个重要的左边独有排": "important left orphan row(s)",
    "个重要右边独有排": "important right orphan row(s)",
    # Hex channel counts (m70e/m70e2, observed on BOTH installs, full four
    # categories: 56/31/1/1). 字节 = byte.
    "个相同字节": "same byte(s)",
    "个左边独有字节": "left orphan byte(s)",
    "个右边独有字节": "right orphan byte(s)",
    "个差异字节": "difference byte(s)",
    # Picture channel counts (m83/m83h/m83i on the current install; every
    # English wording below corroborated on the reference install in
    # m83k-m83m). 像素 = pixel.  Unlike the line/row series, the observed
    # pixel labels carry no 的-asymmetry; only these exact strings are
    # listed -- unobserved variants must surface as unparseable.
    "个相同像素": "same pixel(s)",
    "个不重要的差异像素": "unimportant difference pixel(s)",
    "个忽略的不重要差异像素": "ignored unimportant difference pixel(s)",
    "个左边独有像素": "left orphan pixel(s)",
    "个右边独有像素": "right orphan pixel(s)",
    "个重要差异像素": "important difference pixel(s)",
    # Registry channel counts (m101/m101c/m101f on the current install; every
    # English wording corroborated on the reference install in
    # m101f-regbox-reference, 29 shared cells). 项 = item. The repack's 的
    # asymmetry mirrors the line/row series: the left-orphan label carries 的,
    # the right-orphan one does not -- and, unlike the line series, the
    # *difference* label carries 的 as well ("重要的差异项"). Only these exact
    # strings are listed; unobserved variants must surface as unparseable.
    "个相同项": "same item(s)",
    "个重要的左边独有项": "important left orphan item(s)",
    "个重要右边独有项": "important right orphan item(s)",
    "个重要的差异项": "important difference item(s)",
}
TEXT_COUNT_RE = re.compile(r"^(\d+) (个[^\d]*)$")
#: Already-English count labels are recognised (so a new English wording is not
#: mistaken for body text) but never rewritten.
TEXT_COUNT_EN_RE = re.compile(
    r"^\d+ (?:"
    r"same line\(s\)|"
    r"unimportant difference line\(s\)|"
    r"unimportant left orphan line\(s\)|"
    r"unimportant right orphan line\(s\)|"
    r"important difference line\(s\)|"
    r"important left orphan line\(s\)|"
    r"important right orphan line\(s\)|"
    r"difference section\(s\)|"
    r"same row\(s\)|"
    r"important difference row\(s\)|"
    r"important left orphan row\(s\)|"
    r"important right orphan row\(s\)|"
    r"same byte\(s\)|"
    r"left orphan byte\(s\)|"
    r"right orphan byte\(s\)|"
    r"difference byte\(s\)|"
    r"same pixel\(s\)|"
    r"unimportant difference pixel\(s\)|"
    r"ignored unimportant difference pixel\(s\)|"
    r"left orphan pixel\(s\)|"
    r"right orphan pixel\(s\)|"
    r"important difference pixel\(s\)|"
    r"same item\(s\)|"
    r"important left orphan item\(s\)|"
    r"important right orphan item\(s\)|"
    r"important difference item\(s\)"
    r")$"
)

# Report header field labels.
TEXT_HEADER_LEFT = ("左边文件：", "Left file:")
TEXT_HEADER_RIGHT = ("右边文件：", "Right file:")

# Volatile time.  Two observed spellings; both are LABELS + a timestamp value.
# The timestamp value itself is data we deliberately drop (it is wall-clock).
# The replacement token is deliberately XML-safe and unmistakably synthetic, so
# it survives attribute serialization without escaping and cannot be confused
# with a real report value.
TIME_PLACEHOLDER = "TIME"
TEXT_TIME_PATTERNS = (
    (re.compile(r"^已产生： (\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d)$"),
     f"Produced: {TIME_PLACEHOLDER}"),
    (re.compile(r"^Produced: (\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d)$"),
     f"Produced: {TIME_PLACEHOLDER}"),
)
XML_TIME_ATTRS = {
    ("bcreport", "created"),
    ("filecomparison", "created"),
    ("foldercomp", "created"),
    ("filecomp", "created"),
}
XML_TIME_VALUE_RE = re.compile(r"^\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d$")


# --------------------------------------------------------------------------
# Known report vocabulary -- anything else is a refusal, never a guess.
# --------------------------------------------------------------------------
# XML element names observed in the golden corpus + current-install output.
# ``filters`` is the M4 script ``filter`` echo: observed in
# ``runs/u5i-probe-20261014T032235Z/reports/xml-filter-only.out`` and
# ``xml-filter-and-iu.out``, where it sits between ``<rtpath>`` and the first
# row (after ``<ignoreunimportant/>`` when a `criteria ... ignore-unimportant`
# was also issued).  Its **text is data** -- the script's own mask string,
# echoed verbatim, including a trailing backslash rendered as ``\\``
# (``u5h``/``u5i``) -- so it is validated as present and passed through
# unchanged, exactly like the left/right text content.
KNOWN_XML_TAGS = {
    "bcreport", "ltpath", "rtpath", "filecomparison", "filename1", "filename2",
    "linecomp", "text", "mode", "error1", "error2", "ignoreunimportant",
    "foldercomp", "lt", "rt", "name", "size", "modified", "filecomp",
    "filters",
}
# Attributes observed on those tags.
# ``filecomp/@status`` observed in the folder recipe output; ``linecomp/@status``
# in the text XML reports; ``created`` on the four containers that carry a
# wall-clock stamp.
KNOWN_XML_ATTRS = {
    ("bcreport", "created"),
    ("filecomparison", "created"),
    ("foldercomp", "created"),
    ("filecomp", "created"),
    ("filecomp", "status"),
    ("linecomp", "status"),
    ("text", "ltid"),
    ("text", "rtid"),
}
#: ``linecomp/@status`` values observed across both installs and the corpus.
#: A census over every archived report (M0..M4) finds exactly these seven:
#: ``different`` 1720, ``leftorphan`` 307, ``leftsimilar`` 178,
#: ``rightorphan`` 264, ``rightsimilar`` 22, ``same`` 3143, ``similar`` 893.
#: ``leftsimilar``/``rightsimilar`` are one-sided lines whose content is
#: entirely unimportant (u2/u2b, M2).  The ``leftnewer``/``leftolder``/
#: ``*orphanimportant`` spellings listed here before the census were never
#: observed in any report; they are gone so the set states what has actually
#: been seen rather than what might exist.
KNOWN_LINECOMP_STATUS = {
    "same", "similar", "different",
    "leftorphan", "rightorphan",
    "leftsimilar", "rightsimilar",
}
#: ``filecomp/@status`` values observed in the folder recipe.  The census over
#: every archived report (M0..M4 runs) finds exactly these six: ``diff`` 687,
#: ``ltnewer`` 61, ``ltonly`` 1213, ``rtnewer`` 396, ``rtonly`` 561,
#: ``same`` 3067.  The ``leftnewer``/``rightnewer`` spellings that were listed
#: here before the census are **not** among them — the token is ``lt``/``rt``,
#: matching the ``ltonly``/``rtonly`` pair — so they are gone rather than kept
#: as speculative members (the M4 gate hit this as a refusal on a real report).
KNOWN_FILECOMP_STATUS = {
    "same", "diff", "ltonly", "rtonly", "ltnewer", "rtnewer",
}

# Text-layout line kinds we are allowed to touch.
_TXT_HEADER_PREFIXES = ("左边文件：", "左边文件:", "Left file:", "右边文件：", "右边文件:", "Right file:")
_TXT_BODY_MARKERS = ("diff -r ",)


@dataclass
class NormalizationResult:
    """Post-normalization view plus the audit trail of which rules fired."""

    text: str
    rules_applied: list[str] = field(default_factory=list)
    structure: object | None = None   # parsed comparison key (XML) / line list
    raw_text: str = ""
    raw_structure: object | None = None

    @property
    def changed(self) -> bool:
        """True when normalisation actually altered the comparison structure.

        Comparing structures rather than the rendered text keeps this honest:
        the rendered text is re-serialised (line endings, XML escaping) and
        would otherwise report spurious changes.
        """
        if self.raw_structure is None:
            return self.text != self.raw_text
        return self.structure != self.raw_structure


def _note(res: NormalizationResult, rule: str) -> None:
    if rule not in res.rules_applied:
        res.rules_applied.append(rule)


# ==========================================================================
# XML
# ==========================================================================

def _parse_xml(text: str) -> ET.Element:
    """Parse XML, repairing only the confirmed control-character references.

    Beyond Compare's SsXML engine emits *decimal character references for
    control characters* (``&#1;``, ``&#7;``, ``&#26;``, ``&#0;``).  Those are
    not legal XML 1.0 and every conforming parser rejects them -- including
    ``xml.etree.ElementTree``.  This was observed on anchors ``xml-ctrl-chars``,
    ``enc-ctrlz-eof`` and ``enc-nul-binary`` in the golden corpus itself.

    The repair is surgical: only ``&#N;`` where N is an XML-illegal code point
    is rewritten to a private-use escape, and only inside text content.  The
    substitution is recorded as a rule so it is visible in the audit trail.
    Nothing else is touched.
    """
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise NormalizerRefusal(
            "xml_parse_error",
            f"{exc}; report head={text[:120]!r}",
        ) from exc


def _illegal_char_refs(text: str) -> bool:
    for m in re.finditer(r"&#(\d+);", text):
        n = int(m.group(1))
        legal = n in (9, 10, 13) or 0x20 <= n <= 0xD7FF or 0xE000 <= n <= 0xFFFD
        if not legal:
            return True
    return False


def _protect_illegal_refs(text: str) -> tuple[str, int]:
    """Rewrite XML-illegal numeric character references to PUA escapes.

    Returns the rewritten text and how many references were rewritten.  The
    mapping is lossless and reversible: ``&#1;`` -> ``\\ue0n1;``.
    """
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        n = int(m.group(1))
        legal = n in (9, 10, 13) or 0x20 <= n <= 0xD7FF or 0xE000 <= n <= 0xFFFD
        if legal:
            return m.group(0)
        count += 1
        return f"\\ue0n{n};"

    return re.sub(r"&#(\d+);", repl, text), count


def _restore_illegal_refs(text: str) -> str:
    return re.sub(r"\\ue0n(\d+);", lambda m: f"&#{m.group(1)};", text)


def _check_vocabulary(root: ET.Element, res: NormalizationResult) -> None:
    for el in root.iter():
        if el.tag not in KNOWN_XML_TAGS:
            raise NormalizerRefusal(
                "unknown_xml_tag",
                f"<{el.tag}> is not in the confirmed vocabulary; "
                f"normalizer update required",
            )
        for attr in el.attrib:
            if (el.tag, attr) not in KNOWN_XML_ATTRS:
                raise NormalizerRefusal(
                    "unknown_xml_attribute",
                    f"<{el.tag} {attr}=...> is not in the confirmed vocabulary",
                )


def _norm_xml_element(el: ET.Element, res: NormalizationResult) -> None:
    tag = el.tag

    # -- volatile creation timestamps --------------------------------
    if (tag, "created") in XML_TIME_ATTRS and "created" in el.attrib:
        val = el.attrib["created"]
        if not XML_TIME_VALUE_RE.match(val):
            raise NormalizerRefusal(
                "unexpected_timestamp_format",
                f"<{tag} created={val!r}> is not the observed timestamp format",
            )
        el.set("created", TIME_PLACEHOLDER)
        _note(res, "xml:volatile-timestamp")

    # -- confirmed localisation of <mode> ----------------------------
    if tag == "mode":
        raw = (el.text or "").strip()
        key = (tag, raw)
        if key in XML_LABEL_PAIRS:
            el.text = XML_LABEL_PAIRS[key][1]
            _note(res, "xml:label-pair:mode")
        elif raw not in ("Differences", "Same", "Differences, With Context"):
            raise NormalizerRefusal(
                "unknown_mode_label",
                f"<mode>{raw}</mode> is not a confirmed label; "
                f"normalizer update required",
            )

    # -- confirmed localisation of <errorN> (line number is DATA) ----
    if tag.startswith("error"):
        raw = (el.text or "").strip()
        for pat in XML_ERROR1_PATTERNS:
            m = pat.match(raw)
            if m:
                el.text = f"File Encoding Error (Line {m.group(1)})"
                _note(res, "xml:label-pair:error1-line-number-preserved")
                break
        else:
            raise NormalizerRefusal(
                "unknown_error_label",
                f"<{tag}>{raw}</{tag}> is not a confirmed label",
            )

    # -- status vocabulary: never rewritten, only validated ----------
    if tag == "linecomp":
        st = el.attrib.get("status")
        if st is not None and st not in KNOWN_LINECOMP_STATUS:
            raise NormalizerRefusal(
                "unknown_linecomp_status",
                f'status={st!r} is not a confirmed status value',
            )
    if tag == "filecomp":
        st = el.attrib.get("status")
        if st is not None and st not in KNOWN_FILECOMP_STATUS:
            raise NormalizerRefusal(
                "unknown_filecomp_status",
                f'status={st!r} is not a confirmed status value',
            )


def normalize_xml(text: str, *, keep_structure: bool = True) -> NormalizationResult:
    """Normalize a Beyond Compare XML report.

    Preserves: difference status, element ordering, left/right content, line
    numbers (``ltid``/``rtid``), and every body element.  Only confirmed label
    text and confirmed volatile timestamps are rewritten.
    """
    res = NormalizationResult(text=text, raw_text=text)

    protected, n_refs = _protect_illegal_refs(text)
    if n_refs:
        _note(res, f"xml:ssxml-illegal-control-char-refs({n_refs})")
    # The BOM the folder recipe sometimes emits is not part of the document.
    protected = protected.lstrip("\ufeff")

    root = _parse_xml(protected)
    _check_vocabulary(root, res)
    # Snapshot the pre-normalization key so ``changed`` is measured against the
    # parsed structure rather than the re-serialized text.
    if keep_structure:
        res.raw_structure = _xml_key(root)
    for el in root.iter():
        _norm_xml_element(el, res)

    if keep_structure:
        res.structure = _xml_key(root)

    res.text = _restore_illegal_refs(_serialize(root))
    return res


def _serialize(root: ET.Element) -> str:
    """Deterministic serialization of the normalized tree.

    Only used for the *normalized* view; the raw report is retained untouched
    on disk so the exact pre-normalization bytes remain traceable.
    """
    ET.indent(root, space="\t")
    return ET.tostring(root, encoding="unicode")


def _xml_key(root: ET.Element) -> tuple:
    """Structural comparison key: tags, attributes and text, in document order.

    This is what "the reports agree" means for XML: identical element sequence,
    identical statuses, identical ids, identical content.  Timestamps and
    confirmed labels have already been folded by the rules above, so any
    remaining difference here is a real difference.
    """
    out: list[tuple] = []

    def walk(el: ET.Element) -> None:
        out.append((el.tag, tuple(sorted(el.attrib.items()))))
        txt = (el.text or "").strip()
        if txt:
            out.append(("__text__", txt))
        for child in el:
            walk(child)

    walk(root)
    return tuple(out)


# ==========================================================================
# Text layouts
# ==========================================================================

def _norm_text_header_line(line: str, res: NormalizationResult) -> str:
    """Normalize a ``Left file: ...  Right file: ...`` header line.

    Two jobs, both required:

    * label translation (左边文件：/右边文件： -> Left file:/Right file:)
    * column-padding normalisation, because the header wraps onto two lines
      when the combined path text is long -- the wrap depends on path length,
      NOT on any env var (verified: ``COLUMNS`` has no effect).  Padding
      therefore must be collapsed to a single canonical form or two runs of the
      same comparison can disagree purely because of where the fixtures live.

    The two paths are DATA and are preserved verbatim.  Note the labels end in
    either a fullwidth colon (Chinese) or an ASCII colon (English); the fields
    must be split on the *label*, never on the first colon, because Windows
    drive letters contain one.
    """
    left_label = "Left file:"
    right_label = "Right file:"

    left_tokens = ("左边文件：", "左边文件:", "Left file:")
    right_tokens = ("右边文件：", "右边文件:", "Right file:")

    stripped = line
    matched_left = None
    for tok in left_tokens:
        if stripped.startswith(tok):
            matched_left = tok
            stripped = stripped[len(tok):]
            break

    if matched_left is not None:
        # "Left file: <path> Right file: <path>" or "Left file: <path>" (wrapped)
        for tok in right_tokens:
            idx = stripped.find(tok)
            if idx != -1:
                left_path = stripped[:idx].strip()
                right_path = stripped[idx + len(tok):].strip()
                _note(res, "text:header-label+padding")
                return f"{left_label} {left_path} {right_label} {right_path}"
        left_path = stripped.strip()
        _note(res, "text:header-wrap")
        return f"{left_label} {left_path}"

    for tok in right_tokens:
        if stripped.startswith(tok):
            right_path = stripped[len(tok):].strip()
            _note(res, "text:header-label+padding")
            return f"{right_label} {right_path}"

    return line


def _norm_text_line(line: str, res: NormalizationResult) -> str:
    # 1. volatile timestamp
    for pat, repl in TEXT_TIME_PATTERNS:
        if pat.match(line):
            _note(res, "text:volatile-timestamp")
            return repl

    # 2. header (label + padding / wrap)
    if line.startswith(_TXT_HEADER_PREFIXES):
        return _norm_text_header_line(line, res)

    # 3. whole-line label pairs (titles, statistics CSV header, Mode line)
    if line in TEXT_LABEL_PAIRS:
        _note(res, f"text:label-pair:{line!r}")
        return TEXT_LABEL_PAIRS[line]

    # 3a-0. version-channel table header (norm-6): the header line carries
    # only labels and geometry padding -- no data.  The measured form starts
    # with 名称 and carries 值 in both table halves; swap the two labels
    # in place so the padding (geometry) survives (m112 V1 vs the EN golden).
    if line.startswith("名称") and "值" in line and "Name" not in line:
        _note(res, "text:ver-header")
        return line.replace("名称", "Name").replace("值", "Value")

    # 3a. version-channel prefixes (norm-6): the label plus a DATA payload.
    # The English form is matched too (already-English reports pass through
    # unchanged), and a swap is only applied when the prefix actually fits.
    for zh, en in VER_LINE_PREFIXES:
        if line.startswith(zh):
            _note(res, "text:ver-prefix")
            return en + line[len(zh):]

    # 3b. registry error lines (norm-5): the side label plus a payload that
    # carries data (parse position, encoding line number).  The English form
    # is matched too, so an already-English report is recognised rather than
    # mistaken for body text.
    for pat, repl in REG_TEXT_ERROR_PATTERNS:
        m = pat.match(line)
        if m:
            gd = m.groupdict()
            side_en = "Left" if gd.get("side") == "左边" else "Right"
            _note(res, "text:reg-error-line")
            return repl.format(side_en=side_en, **{k: v for k, v in gd.items()
                                                  if k != "side"})

    # 4. count labels -- NUMBER IS DATA, must survive
    m = TEXT_COUNT_RE.match(line)
    if m:
        num, zh = m.group(1), m.group(2)
        en = TEXT_COUNT_LABELS.get(zh)
        if en is None:
            raise NormalizerRefusal(
                "unknown_count_label",
                f"{line!r}: suffix {zh!r} is not a confirmed count label; "
                f"normalizer update required",
            )
        _note(res, "text:count-label")
        return f"{num} {en}"

    # Already-English count labels are accepted as-is but must be recognised,
    # so a new English wording is not silently treated as body text.
    if TEXT_COUNT_EN_RE.match(line):
        return line

    return line


def normalize_text(text: str) -> NormalizationResult:
    """Normalize a Beyond Compare text-layout report.

    Line structure is preserved exactly (same number of lines, same order) with
    one deliberate exception: a *wrapped* file header is re-joined onto a single
    line.

    Why the exception is safe and necessary: the header wraps when the combined
    path text is long, and the wrap depends only on path length (verified --
    ``COLUMNS`` has no effect).  Without re-joining, two runs of the same
    comparison would differ in *line count* purely because of where the
    fixtures live, which is exactly the false-difference trap recorded in
    ``product/docs/02-version-and-evidence.md`` section 3.5.  The join is only
    applied inside the header region (the first few lines, before any body
    content) and only when the two lines are unambiguously the left and right
    header fields.

    Only lines that are positively identified as headers, titles, count labels
    or timestamps are rewritten.  Body lines -- including diff markers, line
    numbers, ``<``/``>`` prefixes and blank lines -- pass through untouched.

    A leading UTF-8 BOM (U+FEFF) is stripped first, exactly as normalize_xml
    does (the picture channel's zero-file shells are the first text goldens
    that carry one; both Oracle and candidate write it, and no existing text
    golden starts with it, so no earlier verdict changes).
    """
    res = NormalizationResult(text=text, raw_text=text)
    if text.startswith("\ufeff"):
        text = text[1:]
        res.rules_applied.append("text:bom-stripped")
    lines = text.splitlines(keepends=False)
    res.raw_structure = tuple(lines)

    # --- header re-join pass (structure normalisation, header region only) ---
    joined: list[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if (i < _HEADER_REGION_LINES and nxt is not None
                and _is_header_only(cur, "left") and _is_header_only(nxt, "right")):
            res.rules_applied.append("text:header-rewrap-join")
            joined.append(cur.rstrip() + " " + nxt.lstrip())
            i += 2
            continue
        joined.append(cur)
        i += 1

    out = [_norm_text_line(ln, res) for ln in joined]
    res.text = "\n".join(out)
    res.structure = tuple(out)
    res.rules_applied = sorted(set(res.rules_applied))
    return res


#: A wrapped header can only appear in the report preamble; restricting the
#: re-join to this many leading lines keeps the rule away from the body.
_HEADER_REGION_LINES = 8


def _is_header_only(line: str, side: str) -> bool:
    """True when ``line`` holds exactly one header field and no path-shaped tail
    that would indicate a body line."""
    tokens = (TEXT_HEADER_LEFT if side == "left" else TEXT_HEADER_RIGHT)
    for tok in tokens:
        if line.startswith(tok):
            tail = line[len(tok):].strip()
            # A wrapped header's tail is a path; a body line would not begin
            # with the label at all.  Require a non-empty tail and no second
            # label on the same line.
            if not tail:
                return False
            for other in TEXT_HEADER_LEFT + TEXT_HEADER_RIGHT:
                if other in tail:
                    return False
            return True
    return False


# ==========================================================================
# Dispatch
# ==========================================================================

def read_report(path: str | pathlib.Path) -> str:
    """Read a report byte-faithfully.

    ``Path.read_text`` performs universal-newline translation, which silently
    turns CRLF reports into LF and would hide a genuine line-ending difference.
    Reports are therefore read in binary and decoded with ``newline=""``
    semantics (i.e. no translation), preserving exactly what the Oracle wrote.
    """
    raw = pathlib.Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8", errors="replace")
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be", errors="replace")
    return raw.decode("utf-8", errors="replace")


def detect_kind(text: str, *, path: str = "") -> str:
    """Return ``"xml"`` or ``"text"`` for a report, or raise a refusal."""
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("<?xml") or stripped.startswith("<bcreport"):
        return "xml"
    if stripped.startswith("<"):
        raise NormalizerRefusal(
            "unrecognised_report_head",
            f"{path or '<memory>'}: starts with '<' but is neither XML "
            f"declaration nor <bcreport>: {stripped[:80]!r}",
        )
    return "text"


def normalize(text: str, *, kind: str | None = None, path: str = "") -> NormalizationResult:
    kind = kind or detect_kind(text, path=path)
    if kind == "xml":
        return normalize_xml(text)
    if kind == "text":
        return normalize_text(text)
    raise NormalizerRefusal("unknown_report_kind", repr(kind))

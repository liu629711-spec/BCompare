"""Unit tests for the normalizer.

The load-bearing property these tests must prove is **negative**: normalisation
must NOT erase real differences.  Specifically it must not erase

* left/right text content,
* line numbers (``ltid``/``rtid``) or body line ordering,
* diff status,

while it *must* erase confirmed localisation labels and volatile fields.

Run:  python -m pytest product\\verify\\tests -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harness import normalize as N            # noqa: E402
from harness.taxonomy import NormalizerRefusal  # noqa: E402


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------
XML_EN = (
    '<?xml version="1.0" encoding="utf-8"?>\r\n'
    '<bcreport created="2026/10/13 9:24:23">\r\n'
    '\t<ltpath/>\r\n\t<rtpath/>\r\n'
    '\t<filecomparison created="2026/10/13 9:24:23">\r\n'
    '\t\t<filename1>D:\\Rea\\verify\\golden\\x-L.txt</filename1>\r\n'
    '\t\t<filename2>D:\\Rea\\verify\\golden\\x-R.txt</filename2>\r\n'
    '\t\t<linecomp status="same">\r\n'
    '\t\t\t<text ltid="1" rtid="1">a</text>\r\n'
    '\t\t</linecomp>\r\n'
    '\t\t<linecomp status="rightorphan">\r\n'
    '\t\t\t<text rtid="2">b</text>\r\n'
    '\t\t</linecomp>\r\n'
    '\t</filecomparison>\r\n'
    '</bcreport>\r\n'
)
XML_ZH = XML_EN.replace("2026/10/13 9:24:23", "2026/10/13 00:00:00")

TXT_ZH = (
    "文本比较(T)\r\n"
    "已产生： 2026/10/13 00:00:00\r\n"
    "\r\n"
    "模式：  全部\r\n"
    "左边文件： D:\\Rea\\verify\\layouts\\mixed-L.txt     "
    "右边文件： D:\\Rea\\verify\\layouts\\mixed-R.txt\r\n"
    "same line   =  same line\r\n"
    "--------------------------\r\n"
    "case diff   <> CASE DIFF\r\n"
    "real diff 1    real diff 9\r\n"
)
TXT_EN = (
    "Text Compare\r\n"
    "Produced: 2026/10/13 9:43:07\r\n"
    "\r\n"
    "Mode:  All\r\n"
    "Left file: D:\\Rea\\verify\\layouts\\mixed-L.txt     "
    "Right file: D:\\Rea\\verify\\layouts\\mixed-R.txt\r\n"
    "same line   =  same line\r\n"
    "--------------------------\r\n"
    "case diff   <> CASE DIFF\r\n"
    "real diff 1    real diff 9\r\n"
)


# --------------------------------------------------------------------------
# 1. localisation label pairs
# --------------------------------------------------------------------------
def test_chinese_and_english_labels_normalize_to_same_result():
    zh = N.normalize_text(TXT_ZH)
    en = N.normalize_text(TXT_EN)
    assert zh.structure == en.structure


def test_chinese_mode_label_maps_to_english():
    for zh, en in (("差异", "Differences"),
                   ("相同", "Same"),
                   ("差异, 带上下文", "Differences, With Context")):
        got = N.normalize_xml(f"<bcreport><mode>{zh}</mode></bcreport>")
        want = N.normalize_xml(f"<bcreport><mode>{en}</mode></bcreport>")
        assert got.structure == want.structure, zh


def test_error_label_maps_and_preserves_line_number():
    got = N.normalize_xml("<bcreport><error1>文件编码错误 (第 3 行)</error1></bcreport>")
    want = N.normalize_xml("<bcreport><error1>File Encoding Error (Line 3)</error1></bcreport>")
    assert got.structure == want.structure
    assert "Line 3" in got.text


def test_error_label_different_line_number_still_differs():
    a = N.normalize_xml("<bcreport><error1>文件编码错误 (第 3 行)</error1></bcreport>")
    b = N.normalize_xml("<bcreport><error1>File Encoding Error (Line 4)</error1></bcreport>")
    assert a.structure != b.structure


def test_count_labels_map_and_preserve_the_count():
    got = N.normalize_text("2 个相同行")
    want = N.normalize_text("2 same line(s)")
    assert got.structure == want.structure


def test_count_label_different_number_still_differs():
    a = N.normalize_text("2 个相同行")
    b = N.normalize_text("3 个相同行")
    assert a.structure != b.structure


def test_statistics_csv_header_maps():
    zh = N.normalize_text(
        "源文件,比较文件,I最初,I添加,I删除,I改变,U最初,U添加,U删除,U改变,来源错误,比较错误,错误")
    en = N.normalize_text(
        "SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,"
        "UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error")
    assert zh.structure == en.structure


# --------------------------------------------------------------------------
# 2. volatile fields
# --------------------------------------------------------------------------
def test_volatile_timestamp_is_normalised_in_both_languages():
    a = N.normalize_text("已产生： 2026/10/13 00:00:00")
    b = N.normalize_text("Produced: 2026/10/13 9:43:07")
    expected = (f"Produced: {N.TIME_PLACEHOLDER}",)
    assert a.structure == b.structure == expected
    assert "text:volatile-timestamp" in a.rules_applied


def test_volatile_timestamp_normalised_in_xml():
    a = N.normalize_xml(XML_EN)
    b = N.normalize_xml(XML_ZH)
    assert a.structure == b.structure
    assert N.TIME_PLACEHOLDER in a.text
    assert "2026/10/13" not in a.text


def test_header_padding_and_wrap_are_normalised():
    """The same comparison reported from a long path must not differ."""
    one_line = N.normalize_text(TXT_EN)
    wrapped = N.normalize_text(
        TXT_EN.replace(
            "Left file: D:\\Rea\\verify\\layouts\\mixed-L.txt     "
            "Right file: D:\\Rea\\verify\\layouts\\mixed-R.txt",
            "Left file: D:\\Rea\\verify\\layouts\\mixed-L.txt\r\n"
            "Right file: D:\\Rea\\verify\\layouts\\mixed-R.txt"))
    assert one_line.structure == wrapped.structure


def test_header_paths_are_preserved_as_data():
    got = N.normalize_text(TXT_EN)
    assert "D:\\Rea\\verify\\layouts\\mixed-L.txt" in got.text
    assert "D:\\Rea\\verify\\layouts\\mixed-R.txt" in got.text


def test_different_header_paths_still_differ():
    a = N.normalize_text(TXT_EN)
    b = N.normalize_text(TXT_EN.replace("mixed-L.txt", "other-L.txt"))
    assert a.structure != b.structure


# --------------------------------------------------------------------------
# 3. NEGATIVE: real differences must survive normalisation
# --------------------------------------------------------------------------
def test_changed_left_text_is_still_different():
    a = N.normalize_xml(XML_EN)
    b = N.normalize_xml(XML_EN.replace(">a<", ">Z<"))
    assert a.structure != b.structure


def test_changed_right_text_is_still_different():
    a = N.normalize_xml(XML_EN)
    b = N.normalize_xml(XML_EN.replace(">b<", ">Q<"))
    assert a.structure != b.structure


def test_changed_status_is_still_different():
    a = N.normalize_xml(XML_EN)
    b = N.normalize_xml(XML_EN.replace('status="same"', 'status="different"'))
    assert a.structure != b.structure


def test_changed_line_numbers_are_still_different():
    a = N.normalize_xml(XML_EN)
    b = N.normalize_xml(XML_EN.replace('ltid="1" rtid="1"', 'ltid="1" rtid="2"'))
    assert a.structure != b.structure
    c = N.normalize_xml(XML_EN.replace('ltid="1"', 'ltid="7"'))
    assert a.structure != c.structure


def test_changed_line_order_is_still_different():
    swapped = XML_EN.replace(
        '\t\t<linecomp status="same">\r\n'
        '\t\t\t<text ltid="1" rtid="1">a</text>\r\n'
        '\t\t</linecomp>\r\n'
        '\t\t<linecomp status="rightorphan">\r\n'
        '\t\t\t<text rtid="2">b</text>\r\n'
        '\t\t</linecomp>\r\n',
        '\t\t<linecomp status="rightorphan">\r\n'
        '\t\t\t<text rtid="2">b</text>\r\n'
        '\t\t</linecomp>\r\n'
        '\t\t<linecomp status="same">\r\n'
        '\t\t\t<text ltid="1" rtid="1">a</text>\r\n'
        '\t\t</linecomp>\r\n')
    assert swapped != XML_EN, "fixture substitution failed"
    assert N.normalize_xml(XML_EN).structure != N.normalize_xml(swapped).structure


def test_text_body_line_changes_survive():
    a = N.normalize_text(TXT_EN)
    b = N.normalize_text(TXT_EN.replace("real diff 9", "real diff 8"))
    assert a.structure != b.structure


def test_text_body_line_order_changes_survive():
    lines = TXT_EN.split("\r\n")
    lines[5], lines[6] = lines[6], lines[5]
    b = N.normalize_text("\r\n".join(lines))
    assert N.normalize_text(TXT_EN).structure != b.structure


def test_text_body_line_count_changes_survive():
    a = N.normalize_text(TXT_EN)
    b = N.normalize_text(TXT_EN + "extra body line\r\n")
    assert a.structure != b.structure


def test_diff_markers_are_never_stripped():
    got = N.normalize_text(TXT_EN)
    assert "case diff   <> CASE DIFF" in got.text
    assert "same line   =  same line" in got.text
    assert "--------------------------" in got.text


# --------------------------------------------------------------------------
# 4. refusal / explicit outcomes -- never guess, never silently drop
# --------------------------------------------------------------------------
def test_unknown_xml_tag_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml("<bcreport><brandnewtag>x</brandnewtag></bcreport>")
    assert ei.value.reason == "unknown_xml_tag"


def test_unknown_xml_attribute_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml('<bcreport><linecomp status="same" mystery="1"/></bcreport>')
    assert ei.value.reason == "unknown_xml_attribute"


def test_unknown_linecomp_status_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml('<bcreport><linecomp status="wat"/></bcreport>')
    assert ei.value.reason == "unknown_linecomp_status"


def test_unknown_mode_label_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml("<bcreport><mode>Nuevo</mode></bcreport>")
    assert ei.value.reason == "unknown_mode_label"


def test_unknown_count_label_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_text("5 个全新种类行")
    assert ei.value.reason == "unknown_count_label"


def test_malformed_xml_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml("<bcreport><linecomp></bcreport>")
    assert ei.value.reason == "xml_parse_error"


def test_unexpected_timestamp_format_is_refused():
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_xml('<bcreport created="yesterday">x</bcreport>')
    assert ei.value.reason == "unexpected_timestamp_format"


def test_empty_text_is_not_a_refusal():
    got = N.normalize_text("")
    assert got.structure == ()


def test_ssxml_control_char_refs_are_handled_not_dropped():
    """SsXML emits decimal refs for control codes; XML forbids them.

    The normalizer must accept them (they are real, observed output) and must
    preserve the code point -- not silently delete the character.
    """
    src = '<bcreport><linecomp status="different">' \
          '<text ltid="2">c&#7;d</text><text rtid="2">c&#26;d</text>' \
          '</linecomp></bcreport>'
    got = N.normalize_xml(src)
    assert "&#7;" in got.text and "&#26;" in got.text
    assert any("illegal-control-char-refs" in r for r in got.rules_applied)

    other = N.normalize_xml(src.replace("&#26;", "&#27;"))
    assert got.structure != other.structure, "control-char change must survive"


def test_bom_is_tolerated():
    got = N.normalize_xml("\ufeff" + XML_EN)
    assert got.structure == N.normalize_xml(XML_EN).structure


# --------------------------------------------------------------------------
# 5. rule-set is versioned and auditable
# --------------------------------------------------------------------------
def test_ruleset_version_is_present_and_stable():
    # norm-6 (M112): the version channel's title plus its frame/table label
    # prefixes (VER_LINE_PREFIXES: file lines, group headings, value rows).
    # Every English form is corroborated on the verify/ver goldens.
    # norm-5 (M11): the registry channel's title, the two extra Mode lines,
    # the error-line patterns (parsing/duplicates/encoding) and the
    # item-count labels joined the rule set (runs/m101..m101f; English
    # wording corroborated on the reference install in
    # m101f-regbox-reference, 29 shared cells).  The bump is the point of
    # this test -- a rule change must be a deliberate, recorded version
    # change, never a silent edit.
    assert N.RULESET_VERSION == "norm-6"


def test_picture_channel_labels_fold():
    # Measured pairs: zh strings verbatim from runs/m83*/reports, en strings
    # from runs/m83k-m83m on the reference install.
    zh = "图片比较(P)\r\n已产生： 2026/10/19 0:55:28\r\n\r\n正在忽略不重要\r\n" \
         "64 个相同像素\r\n16 个不重要的差异像素\r\n16 个忽略的不重要差异像素\r\n" \
         "12 个左边独有像素\r\n12 个右边独有像素\r\n4 个重要差异像素\r\n" \
         "左边错误： 不被支持的类型\r\n右边错误： 无效图像\r\n基点文件夹： \r\n"
    en = "Picture Compare\r\nProduced: 2026/10/19 0:55:28\r\n\r\nIgnoring Unimportant\r\n" \
         "64 same pixel(s)\r\n16 unimportant difference pixel(s)\r\n16 ignored unimportant difference pixel(s)\r\n" \
         "12 left orphan pixel(s)\r\n12 right orphan pixel(s)\r\n4 important difference pixel(s)\r\n" \
         "Left error: Unsupported Type\r\nRight error: Invalid image\r\nBase folder: \r\n"
    a = N.normalize_text(zh)
    b = N.normalize_text(en)
    assert a.structure == b.structure
    # the English labels must not be rewritten into anything else
    for line in ("64 same pixel(s)", "16 ignored unimportant difference pixel(s)",
                 "4 important difference pixel(s)"):
        assert line in "\n".join(b.structure)


def test_picture_shell_bom_folds_to_the_base_folder_form():
    # m83 P8 / m83n O5: the zero-file shell carries a leading BOM and the
    # `Base folder: ` line.  Both the Oracle shell (BOM + zh) and the
    # candidate shell (BOM + en) must fold to the SAME structure, and the
    # BOM rule must be auditable.  The stamp is the measured SLASH form
    # (the display layer rewrites separators -- od-verified).
    shell_zh = "﻿图片比较(P)\r\n已产生： 2026/10/19 11:04:55\r\n\r\n基点文件夹： \r\n"
    shell_en = "﻿Picture Compare\r\nProduced: 2026/10/19 11:04:55\r\n\r\nBase folder: \r\n"
    a = N.normalize_text(shell_zh)
    b = N.normalize_text(shell_en)
    assert a.structure == b.structure
    assert "text:bom-stripped" in a.rules_applied


def test_table_channel_labels_fold():
    # Measured pairs from runs/m62-reflabels-* (zh current vs en reference).
    zh = "表格比较(B)\r\n已产生： 2026/10/18 1:45:48\r\n模式：  全部\r\n" \
         "2 个相同排\r\n1 个重要的左边独有排\r\n"
    en = "Table Compare\r\nProduced: 2026/10/18 0:36:32\r\nMode:  All\r\n" \
         "2 same row(s)\r\n1 important left orphan row(s)\r\n"
    a = N.normalize_text(zh)
    b = N.normalize_text(en)
    assert a.structure == b.structure
    # the `的` asymmetry is a repack quirk both installs share; the en twin
    # must NOT be rewritten
    c = N.normalize_text("1 个重要右边独有排")
    assert c.structure == tuple(["1 important right orphan row(s)"])


def test_every_normalisation_reports_which_rules_fired():
    got = N.normalize_text(TXT_ZH)
    assert got.rules_applied, "normalisation must be auditable"
    assert any("label-pair" in r for r in got.rules_applied)
    assert any("volatile-timestamp" in r for r in got.rules_applied)


def test_raw_text_is_retained_alongside_normalized():
    got = N.normalize_text(TXT_ZH)
    assert got.raw_text == TXT_ZH
    assert got.text != got.raw_text
    assert got.changed is True


def test_unchanged_input_reports_no_change():
    plain = "a =  a\n"
    got = N.normalize_text(plain)
    assert got.changed is False
    assert got.rules_applied == []


# --------------------------------------------------------------------------
# 6. dispatch
# --------------------------------------------------------------------------
def test_detect_kind():
    assert N.detect_kind(XML_EN) == "xml"
    assert N.detect_kind(TXT_EN) == "text"
    assert N.detect_kind("\ufeff" + XML_EN) == "xml"


def test_detect_kind_refuses_unknown_markup():
    with pytest.raises(NormalizerRefusal) as ei:
        N.detect_kind("<html><body>x</body></html>")
    assert ei.value.reason == "unrecognised_report_head"


# --------------------------------------------------------------------------
# 7. generalisation: rules are label tables, not fixture memorisation
# --------------------------------------------------------------------------
def test_count_label_rules_generalise_over_counts_never_seen():
    """The corpus only contains '1 ...' and '2 ...'; 7 and 9 must work too."""
    for n in (7, 9, 123):
        zh = N.normalize_text(f"{n} 个相同行")
        en = N.normalize_text(f"{n} same line(s)")
        assert zh.structure == en.structure == (f"{n} same line(s)",)


def test_unobserved_chinese_variant_is_refused_not_guessed():
    """The repack's own translation is inconsistent; an unobserved variant must
    surface as a refusal so the table is extended from evidence."""
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_text("1 个重要的右边独有行")
    assert ei.value.reason == "unknown_count_label"


def test_english_count_label_is_left_alone():
    got = N.normalize_text("7 important right orphan line(s)")
    assert got.structure == ("7 important right orphan line(s)",)


def test_body_text_containing_label_words_is_not_rewritten():
    """A body line that merely resembles a label must pass through untouched."""
    for body in ("2 same line(s) of output",
                 "the 1 important difference line(s) count",
                 "not a label at all"):
        got = N.normalize_text(body)
        assert got.structure == (body,), body


def test_registry_channel_labels_fold():
    # norm-5 (M11).  Measured pairs: zh strings verbatim from
    # runs/m101*/reports, en strings from runs/m101f-regbox-reference (29
    # shared cells).  The Parsing Error line:col and the encoding line
    # number are DATA and must survive; the 删除/重复跳过 note is static.
    zh = "注册表比较(R)\r\n已产生： 2026/10/19 12:10:44\r\n\r\n模式：  全部\r\n" \
         "1 个相同项\r\n2 个重要的左边独有项\r\n1 个重要右边独有项\r\n3 个重要的差异项\r\n" \
         "左边错误： 解析错误 (3： 38)\r\n右边错误： 删除/重复跳过\r\n" \
         "左边错误： 文件编码错误 (第 1 行)\r\n"
    en = "Registry Compare\r\nProduced: 2026/10/19 12:10:44\r\n\r\nMode:  All\r\n" \
         "1 same item(s)\r\n2 important left orphan item(s)\r\n1 important right orphan item(s)\r\n" \
         "3 important difference item(s)\r\n" \
         "Left error: Parsing Error (3: 38)\r\nRight error: Deletes/Duplicates Skipped\r\n" \
         "Left error: File Encoding Error (Line 1)\r\n"
    a = N.normalize_text(zh)
    b = N.normalize_text(en)
    assert a.structure == b.structure
    # the DATA inside the error lines must survive on both sides
    for line in ("Left error: Parsing Error (3: 38)",
                 "Left error: File Encoding Error (Line 1)"):
        assert line in "\n".join(b.structure), line


def test_registry_mode_lines_fold():
    # m101c I4 (差异 -> Differences) and I12 (相同 -> Same): the sbs Mode
    # line follows picture's fullwidth-colon + two-ASCII-space form.
    for zh, en in (("模式：  差异", "Mode:  Differences"),
                   ("模式：  相同", "Mode:  Same"),
                   ("模式：  全部", "Mode:  All")):
        assert N.normalize_text(zh).structure == N.normalize_text(en).structure == (en,)


def test_registry_unobserved_variant_is_refused_not_guessed():
    """The repack's own translation is inconsistent; an unobserved variant
    must surface as a refusal so the table is extended from evidence."""
    with pytest.raises(NormalizerRefusal) as ei:
        N.normalize_text("1 个重要的右边独有项")
    assert ei.value.reason == "unknown_count_label"


def test_registry_body_lines_are_not_rewritten():
    """The registry sbs TABLE body is data: names, types, markers and the
    data text must pass through untouched (the geometry is locale-dependent
    and is locked by the product's corpus tests, not by the normalizer)."""
    for body in ("Name Type   Data    Name Type   Data",
                 "\a   REG_SZ 1    +-",
                 "m    REG_SZ 0    =  m    REG_SZ 0",
                 "h0  REG_NONE   (zero-length binary value) = h0  REG_NONE   (zero-length binary value)"):
        got = N.normalize_text(body)
        assert got.structure == (body,), body

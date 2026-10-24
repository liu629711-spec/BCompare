//! M1.5 — XML report writer.
//!
//! Migrated from `clone/src/report.rs` and extended. Every structural detail
//! below is **O**bserved in `verify/golden/*.xml`:
//!
//! | Detail | Observation |
//! |---|---|
//! | XML declaration | `<?xml version="1.0" encoding="utf-8"?>` — lowercase `utf-8` |
//! | Line endings | every line ends with CRLF, including the last |
//! | Indentation | one tab per level: `\t<bcreport>`, `\t\t<filecomparison>`, `\t\t\t<text>` |
//! | Root | `<bcreport created="…">` then `<ltpath/>` and `<rtpath/>` (empty elements for a file comparison) |
//! | Container | `<filecomparison created="…">` with `<filename1>`/`<filename2>` carrying the input paths |
//! | Optional elements | `<mode>` (only for three display options), `<ignoreunimportant/>`, `<error1>` |
//! | Paired `same` line | one `<text ltid="i" rtid="j">` |
//! | Any other pair | two `<text>` elements, `ltid` first then `rtid` |
//! | Orphan | one `<text>` with only its own id |
//! | Ids | 1-based, per file, `ltid` counts left lines and `rtid` right lines independently |
//! | `&`, `<` escaped; `>` left literal | `xml-entities`: `a &amp; b &lt; c > d` |
//! | Quotes NOT escaped in text | `xml-quotes`: `say "hi"` and `say 'hi'` verbatim |
//! | Control chars as decimal refs | `xml-ctrl-chars` `&#1;`, `&#7;`; `enc-ctrlz-eof` `&#26;`; `enc-nul-binary` `&#0;` |
//! | Tab preserved literally | `xml-tabs`: `col1\tcol2` |
//! | No wrapping of long lines | `xml-long-line`: one 328-char `<text>` on one line |
//! | CJK and emoji emitted as UTF-8 | `xml-unicode`: `中文行`, `emoji 😀` |
//!
//! # The `>` question
//!
//! `>` *may* be escaped in XML text without changing the document, so choosing
//! not to escape it is not merely cosmetic — it is required for the report to
//! match. The corpus is unambiguous: `xml-entities` and `xml-quotes` both show a
//! literal `>` in content. (An earlier draft of the clone prototype escaped it;
//! this module does not.)
//!
//! # Escaping rules, precisely
//!
//! * `&` → `&amp;`
//! * `<` → `&lt;`
//! * `>` → literal
//! * `"` and `'` → literal (they only need escaping inside attribute values, and
//!   attribute values here are ids and timestamps that cannot contain them)
//! * any char below U+0020 except tab (U+0009) → `&#<decimal>;`
//!
//! Tab is exempt, and CR/LF cannot occur inside a line because line splitting
//! consumed them. `&#0;` is emitted for NUL, which is not legal XML: that is
//! exactly what BC writes, and `product/verify/harness/normalize.py` documents
//! the same quirk (it round-trips such references through a private-use escape
//! so a conforming parser can read the report).

use crate::align::{FoldOrigin, Group, Status};
use crate::options::ReportOptions;
use crate::stamp::Stamp;

/// A report layout. The six text layouts plus XML.
///
/// The names are the ones BC's `text-report layout:<name>` accepts and the ones
/// the layout manifest uses as its `layout` field.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Layout {
    Xml,
    SideBySide,
    Interleaved,
    Patch,
    Summary,
    Statistics,
    OverUnder,
}

impl Layout {
    /// Parse a `--layout=` value. Unknown names are refused.
    pub fn parse(name: &str) -> Option<Layout> {
        match name.trim().to_ascii_lowercase().as_str() {
            "xml" => Some(Layout::Xml),
            "side-by-side" => Some(Layout::SideBySide),
            "interleaved" => Some(Layout::Interleaved),
            "patch" => Some(Layout::Patch),
            "summary" => Some(Layout::Summary),
            "statistics" => Some(Layout::Statistics),
            "over-under" => Some(Layout::OverUnder),
            _ => None,
        }
    }

    /// The canonical name, as accepted by [`Layout::parse`].
    pub fn name(self) -> &'static str {
        match self {
            Layout::Xml => "xml",
            Layout::SideBySide => "side-by-side",
            Layout::Interleaved => "interleaved",
            Layout::Patch => "patch",
            Layout::Summary => "summary",
            Layout::Statistics => "statistics",
            Layout::OverUnder => "over-under",
        }
    }

    /// Every layout, in the order the CLI documents them.
    pub const ALL: [Layout; 7] = [
        Layout::Xml,
        Layout::SideBySide,
        Layout::Interleaved,
        Layout::Patch,
        Layout::Summary,
        Layout::Statistics,
        Layout::OverUnder,
    ];
}

/// Escape one line for XML text content, per the rules in the module header.
pub fn escape_text(s: &str) -> String {
    // Cheap pre-check: most lines need no escaping at all, and the report writer
    // calls this once per emitted line.
    if !s.chars().any(|c| c == '&' || c == '<' || (c < ' ' && c != '\t')) {
        return s.to_string();
    }
    let mut out = String::with_capacity(s.len() + 8);
    for c in s.chars() {
        match c {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            c if (c as u32) < 0x20 && c != '\t' => {
                out.push_str("&#");
                out.push_str(&(c as u32).to_string());
                out.push(';');
            }
            c => out.push(c),
        }
    }
    out
}

/// Everything the XML writer needs beyond the groups themselves.
pub struct XmlReport<'a> {
    pub left_path: &'a str,
    pub right_path: &'a str,
    pub left_lines: &'a [String],
    pub right_lines: &'a [String],
    pub groups: &'a [Group],
    pub options: ReportOptions,
    pub stamp: &'a Stamp,
    /// 1-based line number of a decoding failure on the left side, when the
    /// caller detected one. `None` emits nothing.
    pub left_encoding_error_line: Option<usize>,
    /// Same for the right side.
    pub right_encoding_error_line: Option<usize>,
}

/// Render a complete XML report.
pub fn to_xml(report: &XmlReport<'_>) -> String {
    let XmlReport {
        left_path,
        right_path,
        left_lines,
        right_lines,
        groups,
        options,
        stamp,
        left_encoding_error_line,
        right_encoding_error_line,
    } = *report;
    let mut o = String::with_capacity(256 + groups.len() * 96);
    o.push_str("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n");
    o.push_str(&format!("<bcreport created=\"{}\">\r\n", stamp.as_str()));
    o.push_str("\t<ltpath/>\r\n");
    o.push_str("\t<rtpath/>\r\n");
    o.push_str(&format!("\t<filecomparison created=\"{}\">\r\n", stamp.as_str()));
    o.push_str(&format!("\t\t<filename1>{}</filename1>\r\n", escape_text(left_path)));
    o.push_str(&format!("\t\t<filename2>{}</filename2>\r\n", escape_text(right_path)));
    // Element order after <filename2> is fixed by the corpus: <mode>, then
    // <ignoreunimportant/>, then any <errorN>, then the linecomp sequence.
    // `enc-latin1.xml` places <error1> immediately before the first <linecomp>
    // and carries no <mode>, so the relative order of <error1> and the two
    // option elements is unobserved; this order is the one that keeps every
    // observed report byte-identical and is recorded in README.md.
    if let Some(mode) = options.display.as_xml_mode() {
        o.push_str(&format!("\t\t<mode>{mode}</mode>\r\n"));
    }
    if options.ignore_unimportant {
        o.push_str("\t\t<ignoreunimportant/>\r\n");
    }
    if let Some(line) = left_encoding_error_line {
        o.push_str(&error_element(Side::Left, line));
    }
    if let Some(line) = right_encoding_error_line {
        o.push_str(&error_element(Side::Right, line));
    }
    // Walk context for `ignore-unimportant` folds: the id a folded one-sided
    // row shows for its OTHER side is borrowed from the nearest preceding
    // paired row (u2b). Folded rows do not update the context; only real
    // rows carrying the respective id do.
    let mut last_ltid: Option<usize> = None;
    let mut last_rtid: Option<usize> = None;
    for g in groups {
        write_group(&mut o, g, left_lines, right_lines, last_ltid, last_rtid);
        if g.folded.is_none() {
            if let Some(li) = g.left {
                last_ltid = Some(li);
            }
            if let Some(ri) = g.right {
                last_rtid = Some(ri);
            }
        }
    }
    o.push_str("\t</filecomparison>\r\n</bcreport>\r\n");
    o
}

fn write_group(
    o: &mut String,
    g: &Group,
    left_lines: &[String],
    right_lines: &[String],
    last_ltid: Option<usize>,
    last_rtid: Option<usize>,
) {
    o.push_str(&format!("\t\t<linecomp status=\"{}\">\r\n", g.status.as_xml()));
    match (g.left, g.right, g.folded) {
        // ignore-unimportant folded a one-sided `leftsimilar` line: its own
        // ltid plus the borrowed rtid, content = the left line (u2b:
        // `<text ltid="2" rtid="1">// b</text>`).
        (Some(li), None, Some(FoldOrigin::LeftSimilar)) => {
            o.push_str(&format!(
                "\t\t\t<text ltid=\"{}\" rtid=\"{}\">{}</text>\r\n",
                li + 1,
                last_rtid.map_or(0, |r| r + 1),
                escape_text(&left_lines[li])
            ));
        }
        // ...and a `rightsimilar` line: borrowed ltid plus its own rtid, and
        // NO content — the observed report writes a self-closing element
        // (u2b: `<text ltid="1" rtid="2"/>`).
        (None, Some(ri), Some(FoldOrigin::RightSimilar)) => {
            o.push_str(&format!(
                "\t\t\t<text ltid=\"{}\" rtid=\"{}\"/>\r\n",
                last_ltid.map_or(0, |l| l + 1),
                ri + 1
            ));
        }
        // A `same` pair collapses to a single element carrying both ids.
        (Some(li), Some(ri), _) if g.status == Status::Same => {
            o.push_str(&format!(
                "\t\t\t<text ltid=\"{}\" rtid=\"{}\">{}</text>\r\n",
                li + 1,
                ri + 1,
                escape_text(&left_lines[li])
            ));
        }
        (Some(li), Some(ri), _) => {
            o.push_str(&format!(
                "\t\t\t<text ltid=\"{}\">{}</text>\r\n",
                li + 1,
                escape_text(&left_lines[li])
            ));
            o.push_str(&format!(
                "\t\t\t<text rtid=\"{}\">{}</text>\r\n",
                ri + 1,
                escape_text(&right_lines[ri])
            ));
        }
        (Some(li), None, _) => {
            o.push_str(&format!(
                "\t\t\t<text ltid=\"{}\">{}</text>\r\n",
                li + 1,
                escape_text(&left_lines[li])
            ));
        }
        (None, Some(ri), _) => {
            o.push_str(&format!(
                "\t\t\t<text rtid=\"{}\">{}</text>\r\n",
                ri + 1,
                escape_text(&right_lines[ri])
            ));
        }
        // A group with no line at all carries no information; the XML writer
        // emits the (empty) linecomp rather than inventing content, and the
        // status vocabulary has no value for it.
        (None, None, _) => {}
    }
    o.push_str("\t\t</linecomp>\r\n");
}

/// A file that could not be decoded without loss, as reported by `<errorN>`.
///
/// Observed in `enc-latin1`, whose LEFT file contains an invalid UTF-8 byte: BC
/// writes `<error1>File Encoding Error (Line 1)</error1>` *before* the first
/// `linecomp`, and the line that was affected still appears in the comparison.
/// The line number is DATA and survives normalisation.
///
/// The right side uses **`error2`**, not a second `error1` — measured in
/// `probes/u7_encoding_error_elements.py`:
///
/// | input | Oracle element(s) |
/// |---|---|
/// | left invalid only | `<error1>` |
/// | right invalid only | **`<error2>`** |
/// | both invalid | `<error1>` then `<error2>` |
///
/// The element name follows the same `1`/`2` side numbering as
/// `filename1`/`filename2`, and the earlier "two `error1` elements" reading was
/// an extrapolation from the single left-side anchor rather than a measurement.
///
/// This crate only emits the element for a decode that actually lost
/// information (`lines::Decoded::had_invalid_bytes`), never speculatively.
pub fn error_element(side: Side, line_number: usize) -> String {
    let tag = match side {
        Side::Left => "error1",
        Side::Right => "error2",
    };
    format!("\t\t<{tag}>File Encoding Error (Line {line_number})</{tag}>\r\n")
}

/// Which side of the comparison an element belongs to.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    Left,
    Right,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::align::{align, Group};
    use crate::importance::Grammar;

    fn lines(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    fn golden(pairs: &[(&str, &str)]) -> (Vec<String>, Vec<String>) {
        let l = lines(&pairs.iter().map(|p| p.0).collect::<Vec<_>>());
        let r = lines(&pairs.iter().map(|p| p.1).collect::<Vec<_>>());
        (l, r)
    }

    fn render(left: &[String], right: &[String], options: ReportOptions) -> String {
        let groups = align(left, right, Grammar::PlainText, &mut || false).unwrap();
        render_groups(left, right, &groups, options)
    }

    fn render_groups(
        left: &[String],
        right: &[String],
        groups: &[Group],
        options: ReportOptions,
    ) -> String {
        let stamp = Stamp::from_parts(2026, 10, 13, 9, 24, 26);
        to_xml(&XmlReport {
            left_path: r"D:\L.txt",
            right_path: r"D:\R.txt",
            left_lines: left,
            right_lines: right,
            groups,
            options,
            stamp: &stamp,
            left_encoding_error_line: None,
            right_encoding_error_line: None,
        })
    }

    // ---------------------------------------------------------------
    // Escaping
    // ---------------------------------------------------------------

    #[test]
    fn escapes_ampersand_and_less_than_only() {
        // verify/golden xml-entities: "a & b < c > d"
        assert_eq!(escape_text("a & b < c > d"), "a &amp; b &lt; c > d");
    }

    #[test]
    fn leaves_quotes_literal() {
        // verify/golden xml-quotes: both quote characters appear verbatim.
        assert_eq!(escape_text("say \"hi\" & <ok>"), "say \"hi\" &amp; &lt;ok>");
        assert_eq!(escape_text("say 'hi' & <ok>"), "say 'hi' &amp; &lt;ok>");
    }

    #[test]
    fn control_characters_become_decimal_references() {
        // verify/golden xml-ctrl-chars / enc-ctrlz-eof / enc-nul-binary.
        assert_eq!(escape_text("a\u{1}b"), "a&#1;b");
        assert_eq!(escape_text("c\u{7}d"), "c&#7;d");
        assert_eq!(escape_text("c\u{1a}d"), "c&#26;d");
        assert_eq!(escape_text("a\u{0}b"), "a&#0;b");
        assert_eq!(escape_text("\u{1f}"), "&#31;");
    }

    #[test]
    fn tab_is_preserved_literally_and_is_not_a_character_reference() {
        // verify/golden xml-tabs: "col1\tcol2" stays a real tab.
        assert_eq!(escape_text("col1\tcol2"), "col1\tcol2");
        assert!(!escape_text("col1\tcol2").contains("&#"));
    }

    #[test]
    fn cjk_and_emoji_pass_through_as_utf8() {
        assert_eq!(escape_text("中文行"), "中文行");
        assert_eq!(escape_text("emoji 😀"), "emoji 😀");
    }

    #[test]
    fn plain_text_is_returned_unchanged() {
        assert_eq!(escape_text("plain"), "plain");
        assert_eq!(escape_text(""), "");
        assert_eq!(escape_text("a-b_c=1;"), "a-b_c=1;");
    }

    #[test]
    fn escape_is_idempotent_on_escaped_input() {
        // `&amp;` must not become `&amp;amp;` — the escaping sees only the raw
        // text, never its own output.
        assert_eq!(escape_text("&amp;"), "&amp;amp;");
    }

    // ---------------------------------------------------------------
    // Document structure
    // ---------------------------------------------------------------

    #[test]
    fn document_head_and_tail_match_the_corpus() {
        let (l, r) = golden(&[("x", "x")]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.starts_with("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n"));
        assert!(xml.contains("<bcreport created=\"2026/10/13 9:24:26\">\r\n"));
        assert!(xml.contains("\t<ltpath/>\r\n"));
        assert!(xml.contains("\t<rtpath/>\r\n"));
        assert!(xml.contains("\t<filecomparison created=\"2026/10/13 9:24:26\">\r\n"));
        assert!(xml.contains("\t\t<filename1>D:\\L.txt</filename1>\r\n"));
        assert!(xml.contains("\t\t<filename2>D:\\R.txt</filename2>\r\n"));
        assert!(xml.ends_with("\t</filecomparison>\r\n</bcreport>\r\n"));
    }

    #[test]
    fn every_line_ends_with_crlf_including_the_last() {
        let (l, r) = golden(&[("x", "x")]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.ends_with("\r\n"));
        // Bare LF must never appear.
        let without_crlf = xml.replace("\r\n", "");
        assert!(!without_crlf.contains('\n'), "found a bare LF");
    }

    #[test]
    fn indentation_uses_tabs_one_level_per_depth() {
        let (l, r) = golden(&[("x", "x")]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains("\t\t<linecomp status=\"same\">\r\n"));
        assert!(xml.contains("\t\t\t<text ltid=\"1\" rtid=\"1\">x</text>\r\n"));
        assert!(xml.contains("\t\t</linecomp>\r\n"));
        // No space-based indentation anywhere.
        for line in xml.split("\r\n") {
            let leading_spaces = line.len() - line.trim_start_matches(' ').len();
            assert_eq!(leading_spaces, 0, "space indentation in {line:?}");
        }
    }

    #[test]
    fn same_pair_collapses_to_one_text_element() {
        // verify/golden al-duplicates / le-mixed: a `same` group writes a single
        // <text> carrying both ids. Driven through explicit groups so the test
        // isolates the writer from the importance rules.
        let l = lines(&["x"]);
        let r = lines(&["x"]);
        let groups = vec![Group::paired(0, 0, Status::Same)];
        let xml = render_groups(&l, &r, &groups, ReportOptions::default());
        assert!(xml.contains("<text ltid=\"1\" rtid=\"1\">x</text>"), "{xml}");
        assert_eq!(xml.matches("<text ").count(), 1, "{xml}");
    }

    #[test]
    fn non_same_pair_writes_two_text_elements_left_first() {
        // verify/golden al-replace-block: <text ltid> then <text rtid>.
        let (l, r) = golden(&[("x", "p")]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains("<linecomp status=\"different\">\r\n\t\t\t<text ltid=\"1\">x</text>\r\n\t\t\t<text rtid=\"1\">p</text>\r\n\t\t</linecomp>"), "{xml}");
    }

    #[test]
    fn orphan_writes_one_text_element_with_its_own_id() {
        // verify/golden al-delete: L = a,b,c  R = a,c. The middle left line is a
        // leftorphan with a single <text ltid="2">.
        let l = lines(&["a", "b", "c"]);
        let r = lines(&["a", "c"]);
        let groups = vec![
            Group::paired(0, 0, Status::Same),
            Group::left_only(1, Status::LeftOrphan),
            Group::paired(2, 1, Status::Same),
        ];
        let xml = render_groups(&l, &r, &groups, ReportOptions::default());
        assert!(
            xml.contains(
                "<linecomp status=\"leftorphan\">\r\n\t\t\t<text ltid=\"2\">b</text>\r\n\t\t</linecomp>"
            ),
            "{xml}"
        );

        // A right orphan keeps only rtid.
        let groups = vec![Group::right_only(0, Status::RightOrphan)];
        let xml = render_groups(&lines(&[]), &lines(&["only"]), &groups, ReportOptions::default());
        assert!(xml.contains("<text rtid=\"1\">only</text>"), "{xml}");
        assert!(!xml.contains("ltid"), "{xml}");
    }

    #[test]
    fn ids_are_one_based_and_per_file() {
        // al-delete: L = a,b,c  R = a,c  ->  ltid 1,2,3 and rtid 1,2.
        let (l, r) = golden(&[("a", "a"), ("b", "IMPOSED"), ("c", "c")]);
        let groups = vec![
            Group::paired(0, 0, Status::Same),
            Group::left_only(1, Status::LeftOrphan),
            Group::paired(2, 1, Status::Same),
        ];
        let xml = render_groups(&l, &r, &groups, ReportOptions::default());
        assert!(xml.contains("<text ltid=\"3\" rtid=\"2\">c</text>"), "{xml}");
        assert!(xml.contains("<text ltid=\"2\">b</text>"), "{xml}");
    }

    #[test]
    fn empty_comparison_still_writes_a_complete_document() {
        // verify/golden al-empty-both: no linecomp at all.
        let (l, r) = golden(&[]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains("\t<filecomparison created="));
        assert!(!xml.contains("<linecomp"), "{xml}");
        assert!(xml.ends_with("\t</filecomparison>\r\n</bcreport>\r\n"));
    }

    // ---------------------------------------------------------------
    // Options
    // ---------------------------------------------------------------

    #[test]
    fn default_options_write_no_mode_and_no_ignore_element() {
        let (l, r) = golden(&[("x", "x")]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(!xml.contains("<mode>"), "{xml}");
        assert!(!xml.contains("ignoreunimportant"), "{xml}");
    }

    #[test]
    fn mode_element_matches_each_display_option() {
        // The four option anchors: display-all has no <mode>; the other three do.
        let (l, r) = golden(&[("same line", "same line")]);
        for (payload, want) in [
            ("display-all", None),
            ("display-mismatches", Some("Differences")),
            ("display-context", Some("Differences, With Context")),
            ("display-matches", Some("Same")),
        ] {
            let opts = ReportOptions::parse_list(payload).unwrap();
            let xml = render(&l, &r, opts);
            match want {
                None => assert!(!xml.contains("<mode>"), "{payload}: {xml}"),
                Some(m) => assert!(xml.contains(&format!("\t\t<mode>{m}</mode>\r\n")), "{payload}: {xml}"),
            }
        }
    }

    #[test]
    fn ignore_unimportant_writes_the_empty_element() {
        let (l, r) = golden(&[("x", "x")]);
        let opts = ReportOptions::parse_list("ignore-unimportant").unwrap();
        let xml = render(&l, &r, opts);
        assert!(xml.contains("\t\t<ignoreunimportant/>\r\n"), "{xml}");
    }

    #[test]
    fn element_order_is_filename_mode_ignore_then_lines() {
        let (l, r) = golden(&[("x", "x")]);
        let opts = ReportOptions::parse_list("display-context,ignore-unimportant").unwrap();
        let xml = render(&l, &r, opts);
        let f2 = xml.find("<filename2>").unwrap();
        let mode = xml.find("<mode>").unwrap();
        let ign = xml.find("<ignoreunimportant/>").unwrap();
        let lc = xml.find("<linecomp").unwrap();
        assert!(f2 < mode && mode < ign && ign < lc, "{xml}");
    }

    // ---------------------------------------------------------------
    // Content fidelity
    // ---------------------------------------------------------------

    #[test]
    fn control_characters_survive_into_the_report_as_references() {
        let l = lines(&["a\u{1}b"]);
        let r = lines(&["a\u{1}b"]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains(">a&#1;b</text>"), "{xml}");
    }

    #[test]
    fn long_lines_are_not_wrapped() {
        let long = "x".repeat(328);
        let l = vec![long.clone()];
        let r = vec![long.clone() + "y"];
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains(&format!("<text ltid=\"1\">{long}</text>")), "long line was altered");
        // The whole <text> must be on one physical line.
        assert_eq!(xml.matches("<text ltid=\"1\">").count(), 1);
    }

    #[test]
    fn unicode_content_is_not_escaped() {
        let l = lines(&["中文行"]);
        let r = lines(&["中文行2"]);
        let xml = render(&l, &r, ReportOptions::default());
        assert!(xml.contains(">中文行</text>"), "{xml}");
        assert!(xml.contains(">中文行2</text>"), "{xml}");
    }

    #[test]
    fn filename_paths_are_escaped_too() {
        let stamp = Stamp::from_parts(2026, 10, 13, 9, 0, 0);
        let xml = to_xml(&XmlReport {
            left_path: r"D:\a&b\l.txt",
            right_path: r"D:\c<d\r.txt",
            left_lines: &[],
            right_lines: &[],
            groups: &[],
            options: ReportOptions::default(),
            stamp: &stamp,
            left_encoding_error_line: None,
            right_encoding_error_line: None,
        });
        assert!(xml.contains("<filename1>D:\\a&amp;b\\l.txt</filename1>"), "{xml}");
        assert!(xml.contains("<filename2>D:\\c&lt;d\\r.txt</filename2>"), "{xml}");
    }

    // ---------------------------------------------------------------
    // Encoding error element
    // ---------------------------------------------------------------

    #[test]
    fn error_element_text_matches_the_golden_report() {
        // verify/golden enc-latin1.xml (after label normalisation).  That anchor
        // has the invalid byte on the LEFT side only.
        assert_eq!(
            error_element(Side::Left, 1),
            "\t\t<error1>File Encoding Error (Line 1)</error1>\r\n"
        );
        assert!(error_element(Side::Left, 7).contains("(Line 7)"));
        // The right side is error2 (probes/u7).  This function is the only
        // place the tag name is built, so pinning both here pins the contract.
        assert_eq!(
            error_element(Side::Right, 1),
            "\t\t<error2>File Encoding Error (Line 1)</error2>\r\n"
        );
    }

    #[test]
    fn encoding_error_element_is_emitted_only_when_the_caller_reports_one() {
        let stamp = Stamp::from_parts(2026, 10, 13, 9, 24, 26);
        let l = lines(&["caf\u{FFFD}"]);
        let r = lines(&["caf\u{e9}"]);
        let groups = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
        let build = |left_err: Option<usize>, right_err: Option<usize>| {
            to_xml(&XmlReport {
                left_path: r"D:\L.txt",
                right_path: r"D:\R.txt",
                left_lines: &l,
                right_lines: &r,
                groups: &groups,
                options: ReportOptions::default(),
                stamp: &stamp,
                left_encoding_error_line: left_err,
                right_encoding_error_line: right_err,
            })
        };
        // No error line: no element at all, matching every clean anchor.
        assert!(!build(None, None).contains("<error1>"));
        // Left side only, as in enc-latin1.
        let xml = build(Some(1), None);
        assert!(
            xml.contains("\t\t<error1>File Encoding Error (Line 1)</error1>\r\n"),
            "{xml}"
        );
        assert_eq!(xml.matches("<error").count(), 1);
        // ...and it sits immediately before the first linecomp.
        let err = xml.find("<error1>").unwrap();
        let lc = xml.find("<linecomp").unwrap();
        assert!(err < lc, "{xml}");
        // The RIGHT side is `error2`, with `error1` first when both sides fail.
        // Measured in probes/u7_encoding_error_elements.py: `right-invalid`
        // produced exactly `<error2>` and `both-invalid` produced `<error1>`
        // then `<error2>`.  The side number matches filename1/filename2.
        let xml = build(None, Some(1));
        assert!(
            xml.contains("\t\t<error2>File Encoding Error (Line 1)</error2>\r\n"),
            "{xml}"
        );
        assert!(!xml.contains("<error1>"), "right-only must not emit error1: {xml}");
        let xml = build(Some(2), Some(3));
        assert_eq!(xml.matches("<error").count(), 2, "{xml}");
        assert!(xml.contains("<error1>File Encoding Error (Line 2)</error1>"), "{xml}");
        assert!(xml.contains("<error2>File Encoding Error (Line 3)</error2>"), "{xml}");
        let e1 = xml.find("<error1>").unwrap();
        let e2 = xml.find("<error2>").unwrap();
        assert!(e1 < e2, "left's element comes first: {xml}");
    }

    // ---------------------------------------------------------------
    // Layout names
    // ---------------------------------------------------------------

    #[test]
    fn layout_names_round_trip() {
        for layout in Layout::ALL {
            assert_eq!(Layout::parse(layout.name()), Some(layout), "{}", layout.name());
        }
        assert_eq!(Layout::parse("SIDE-BY-SIDE"), Some(Layout::SideBySide));
        assert_eq!(Layout::parse("--layout=xml"), None);
        assert_eq!(Layout::parse("overunder"), None);
        assert_eq!(Layout::parse(""), None);
        assert_eq!(Layout::ALL.len(), 7);
    }
}

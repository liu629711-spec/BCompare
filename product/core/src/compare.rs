//! The comparison pipeline: decode → align → classify → render.
//!
//! This is the single entry point the CLI (and any future engine) calls, so the
//! ordering of the pipeline exists in exactly one place.
//!
//! ```
//! use reacmp_core::{compare_bytes, ReportOptions, Layout};
//! let outcome = compare_bytes(
//!     b"a\nb\n", b"a\nc\n",
//!     "L.txt", "R.txt",
//!     ReportOptions::default(),
//!     &mut || false,
//! ).unwrap();
//! assert_eq!(outcome.statuses(), vec!["same", "different"]);
//! ```

use crate::align::{self, FoldOrigin, Group, Status};
use crate::importance::{self, Grammar, Verdict};
use crate::layouts;
use crate::lines::{self, Encoding};
use crate::myers::DiffError;
use crate::options::ReportOptions;
use crate::stamp::Stamp;
use crate::xml::{self, Layout, XmlReport};

use std::fmt;
use std::path::{Path, PathBuf};

/// What is known about one input file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FileInfo {
    /// The path exactly as it was supplied. Reports echo this, so it must not be
    /// canonicalised (the harness compares `Left file:` paths verbatim, and
    /// `02-version-and-evidence.md` §3.5 makes the same point about the header).
    pub path: String,
    pub bytes: usize,
    pub lines: usize,
    pub encoding: Encoding,
    /// True when decoding replaced at least one byte sequence with U+FFFD.
    pub had_invalid_bytes: bool,
    /// The 1-based first line with invalid UTF-8 bytes, when the file was
    /// decoded as UTF-8 and such a line exists. Drives the `<error1>` element
    /// (`verify/golden/enc-latin1.xml`). `None` when there is nothing to report,
    /// which includes UTF-16 input: a UTF-16 file's code units are not "invalid
    /// UTF-8 lines", and BC emits no `<error1>` for them (`enc-utf16le` /
    /// `enc-utf16be` carry no such element).
    pub encoding_error_line: Option<usize>,
}

/// A completed comparison.
#[derive(Debug, Clone)]
pub struct Comparison {
    pub left: FileInfo,
    pub right: FileInfo,
    pub left_lines: Vec<String>,
    pub right_lines: Vec<String>,
    /// Per-left-line "no important content" mask. Only the `statistics`
    /// layout consumes it (`IOriginal` vs `UOriginal`, m52 probe).
    pub left_unimportant: Vec<bool>,
    pub groups: Vec<Group>,
    /// The grammar the importance rules ran under, derived from the left path.
    pub grammar: Grammar,
    pub options: ReportOptions,
    /// True when a grammar was chosen because the extension is one of the
    /// observed plain-text ones.
    pub stamp: Stamp,
    /// The number of `different` sections, cached because both the summary
    /// layout and the CLI's exit-status decision need it.
    pub difference_sections: usize,
}

impl Comparison {
    /// The `linecomp/@status` sequence **as the report would emit it**, i.e.
    /// after `ignore-unimportant` collapsing and display filtering.
    ///
    /// This is the number the harness compares against the golden `statuses`
    /// list, so it must be the post-option sequence: `opt-display-mismatches`
    /// expects three statuses, not six.
    pub fn statuses(&self) -> Vec<&'static str> {
        self.effective_groups().iter().map(|g| g.status.as_xml()).collect()
    }

    /// The `linecomp/@status` sequence before any option is applied.
    pub fn raw_statuses(&self) -> Vec<&'static str> {
        self.groups.iter().map(|g| g.status.as_xml()).collect()
    }

    /// Number of groups with a given status, over the **raw** comparison (i.e.
    /// independent of display filtering).
    pub fn count(&self, status: Status) -> usize {
        self.groups.iter().filter(|g| g.status == status).count()
    }

    /// True when no group carries a difference (nothing but `same`).
    pub fn is_all_same(&self) -> bool {
        self.groups.iter().all(|g| g.status == Status::Same)
    }

    /// True when every difference is an **unimportant** one: every group is
    /// `same`, `similar`, or a one-sided row whose content is entirely
    /// unimportant (`leftsimilar`/`rightsimilar`).
    ///
    /// This is the predicate that decides BC's `/qc` code between "Similar" and
    /// "rules-based differences", measured in `probes/u6_qc_orphans.py`:
    ///
    /// | input | report statuses | `/qc` |
    /// |---|---|---|
    /// | trailing-whitespace-only change | `similar` | 12 |
    /// | one-sided comment line | `leftsimilar` | 12 |
    /// | one-sided blank line | `leftsimilar` | 12 |
    /// | one-sided code line | `leftorphan` | 13 |
    /// | an important in-line change | `different` | 13 |
    ///
    /// `is_all_same` is too strict for that decision (it calls a
    /// trailing-whitespace-only pair "different"), and so is "all same or
    /// similar" on its own — a one-sided *comment* line is unimportant while a
    /// one-sided code line is not. The distinction that matters is this one.
    pub fn differences_are_all_unimportant(&self) -> bool {
        self.groups.iter().all(|g| {
            matches!(
                g.status,
                Status::Same | Status::Similar | Status::LeftSimilar | Status::RightSimilar
            )
        })
    }

    /// Render one layout.
    ///
    /// Filtering (`display-mismatches` / `display-matches`) and the
    /// `ignore-unimportant` collapse are applied here, so every layout sees the
    /// same effective group list. The `xml` layout renders with the un-collapsed
    /// statuses so that `<ignoreunimportant/>` can be reported alongside the
    /// real per-line verdicts, which is exactly what `opt-ignore-unimportant`
    /// shows: the element is present AND the collapsed statuses are emitted.
    pub fn render(&self, layout: Layout) -> String {
        let groups = self.effective_groups();
        match layout {
            Layout::Xml => xml::to_xml(&XmlReport {
                left_path: &self.left.path,
                right_path: &self.right.path,
                left_lines: &self.left_lines,
                right_lines: &self.right_lines,
                groups: &groups,
                options: self.options,
                stamp: &self.stamp,
                left_encoding_error_line: self.left.encoding_error_line,
                right_encoding_error_line: self.right.encoding_error_line,
            }),
            Layout::SideBySide => layouts::side_by_side(
                &groups,
                &self.left_lines,
                &self.right_lines,
                &self.left.path,
                &self.right.path,
                &self.stamp,
            ),
            Layout::Interleaved | Layout::OverUnder => layouts::interleaved(
                &groups,
                &self.left_lines,
                &self.right_lines,
                &self.left.path,
                &self.right.path,
                &self.stamp,
            ),
            Layout::Patch => layouts::patch(
                &groups,
                &self.left_lines,
                &self.right_lines,
                &self.left.path,
                &self.right.path,
            ),
            Layout::Summary => {
                layouts::summary(&groups, &self.left.path, &self.right.path, &self.stamp)
            }
            Layout::Statistics => {
                // Statistics is booked from the UNFOLDED groups and the full
                // line mask: the m52 probe shows `options:ignore-unimportant`
                // changes nothing in the CSV (BC keeps booking the folded
                // rows in their I/U columns), and `IOriginal`/`UOriginal`
                // split the left lines by importance, which the group list
                // alone cannot answer.
                layouts::statistics(
                    &self.groups,
                    &self.left_unimportant,
                    &self.left_lines,
                    &self.left.path,
                    &self.right.path,
                    &self.stamp,
                )
            }
        }
    }

    /// The group list after `ignore-unimportant` and display filtering.
    ///
    /// `ignore-unimportant` turns every foldable status into `same` (observed
    /// in `opt-ignore-unimportant` for `similar`, and in u2b for the one-sided
    /// `leftsimilar`/`rightsimilar`, whose rows then carry a BORROWED id from
    /// the nearest preceding paired row — see `align::FoldOrigin`).
    /// Display filtering then drops `same` or non-`same` groups.
    fn effective_groups(&self) -> Vec<Group> {
        let mut groups = self.groups.clone();
        if self.options.ignore_unimportant {
            for g in groups.iter_mut() {
                if g.status.folds_to_same() {
                    g.folded = match g.status {
                        Status::LeftSimilar => Some(FoldOrigin::LeftSimilar),
                        Status::RightSimilar => Some(FoldOrigin::RightSimilar),
                        _ => g.folded,
                    };
                    g.status = Status::Same;
                }
            }
        }
        let keep_same = self.options.display.keeps_same();
        let keep_diff = self.options.display.keeps_different();
        if !(keep_same && keep_diff) {
            groups.retain(|g| {
                let same = g.status == Status::Same;
                if same {
                    keep_same
                } else {
                    keep_diff
                }
            });
        }
        groups
    }
}

/// A failure while comparing.
#[derive(Debug)]
pub enum CompareError {
    /// Reading an input failed. Carries the path and the OS error text.
    Io { path: PathBuf, message: String },
    /// The alignment failed. `Cancelled` is an explicit outcome, never an empty
    /// report.
    Diff(DiffError),
}

impl fmt::Display for CompareError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CompareError::Io { path, message } => {
                write!(f, "cannot read {}: {message}", path.display())
            }
            CompareError::Diff(e) => write!(f, "{e}"),
        }
    }
}

impl std::error::Error for CompareError {}

impl From<DiffError> for CompareError {
    fn from(e: DiffError) -> Self {
        CompareError::Diff(e)
    }
}

/// Compare two in-memory buffers.
///
/// `left_path` / `right_path` are used for grammar selection *and* echoed into
/// the report, so they must be the paths the caller wants to see.
pub fn compare_bytes(
    left_bytes: &[u8],
    right_bytes: &[u8],
    left_path: &str,
    right_path: &str,
    options: ReportOptions,
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Comparison, CompareError> {
    compare_bytes_at(
        left_bytes,
        right_bytes,
        left_path,
        right_path,
        options,
        Stamp::now_utc(),
        cancel,
    )
}

/// Compare with an explicit report timestamp. Used by tests and by any caller
/// that needs reproducible output.
pub fn compare_bytes_at(
    left_bytes: &[u8],
    right_bytes: &[u8],
    left_path: &str,
    right_path: &str,
    options: ReportOptions,
    stamp: Stamp,
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Comparison, CompareError> {
    let (dl, left_err) = decode_side(left_bytes, left_path);
    let (dr, right_err) = decode_side(right_bytes, right_path);
    // `Decoded::text` preserves separators for every encoding, including a
    // declared code page (where the byte-level scan has already applied the
    // lead-byte rule), so one splitter serves them all.
    let left_lines = lines::split_text(&dl.text);
    let right_lines = lines::split_text(&dr.text);

    // Grammar selection uses the LEFT path only. The corpus never mixes a
    // `.txt` left with a `.c` right, so the mixed case is unobserved; using the
    // left path is the conservative choice and is recorded in README.md.
    let grammar = Grammar::for_path(left_path);

    let groups = align::align(&left_lines, &right_lines, grammar, cancel)?;
    let difference_sections = align::difference_sections(&groups);
    let left_unimportant = importance::Plan::unimportant_mask(&left_lines, grammar);

    let left = FileInfo {
        path: left_path.to_string(),
        bytes: left_bytes.len(),
        lines: left_lines.len(),
        encoding: dl.encoding,
        had_invalid_bytes: dl.had_invalid_bytes,
        encoding_error_line: left_err,
    };
    let right = FileInfo {
        path: right_path.to_string(),
        bytes: right_bytes.len(),
        lines: right_lines.len(),
        encoding: dr.encoding,
        had_invalid_bytes: dr.had_invalid_bytes,
        encoding_error_line: right_err,
    };

    Ok(Comparison {
        left,
        right,
        left_lines,
        right_lines,
        left_unimportant,
        groups,
        grammar,
        options,
        stamp,
        difference_sections,
    })
}

/// Compare two files on disk.
pub fn compare_files(
    left: &Path,
    right: &Path,
    options: ReportOptions,
) -> Result<Comparison, CompareError> {
    let lb = read(left)?;
    let rb = read(right)?;
    compare_bytes(
        &lb,
        &rb,
        &left.to_string_lossy(),
        &right.to_string_lossy(),
        options,
        &mut || false,
    )
}

fn read(path: &Path) -> Result<Vec<u8>, CompareError> {
    std::fs::read(path).map_err(|e| CompareError::Io {
        path: path.to_path_buf(),
        message: e.to_string(),
    })
}

/// Decode one side, returning its text and the `<errorN>` line number if any.
///
/// The two travel together because for a declared code page they come from a
/// **single** byte-level pass: that pass owns both the decode and the validity
/// judgement, and re-deriving them separately would risk the two disagreeing
/// about where the lines are (measured, `U8-FINDINGS.md` §3.4 — a lead byte
/// swallows a following newline, so the separator positions are part of the
/// validity question, not independent of it).
///
/// For UTF-8/UTF-16 the pair is computed as before: `lines::decode` for the text
/// and `first_invalid_utf8_line` for the number. UTF-16 reports no error, which
/// `verify/golden/enc-utf16le.xml` / `enc-utf16be.xml` confirm is BC's behaviour
/// for those files rather than an omission.
fn decode_side(raw: &[u8], _path: &str) -> (lines::Decoded, Option<usize>) {
    let d = lines::decode(raw);
    match d.encoding {
        Encoding::CodePage(cp) => crate::codepage::decode_declared(cp, raw),
        Encoding::Utf8 | Encoding::Utf8Bom => {
            let err = lines::first_invalid_utf8_line(raw);
            (d, err)
        }
        Encoding::Utf16Le | Encoding::Utf16Be => (d, None),
    }
}

/// Re-classify a pair without running an alignment. Exposed for the CLI's
/// diagnostics and for tests that want to assert a single verdict.
pub fn classify_pair(left: &str, right: &str, grammar: Grammar) -> Verdict {
    let l = vec![left.to_string()];
    let r = vec![right.to_string()];
    crate::importance::Plan::build(&l, &r, grammar).verdict(0, 0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lines::Encoding;

    fn opts(s: &str) -> ReportOptions {
        ReportOptions::parse_list(s).unwrap()
    }

    fn cmp(left: &[u8], right: &[u8], options: ReportOptions) -> Comparison {
        compare_bytes_at(
            left,
            right,
            r"D:\x\L.txt",
            r"D:\x\R.txt",
            options,
            Stamp::from_parts(2026, 10, 13, 9, 43, 7),
            &mut || false,
        )
        .unwrap()
    }

    fn statuses(left: &[u8], right: &[u8], options: ReportOptions) -> Vec<&'static str> {
        cmp(left, right, options).statuses()
    }


    // ---------------------------------------------------------------
    // Anchor parity for the whole pipeline (mirrors the manifest).
    // ---------------------------------------------------------------

    #[test]
    fn anchor_sequences_via_the_full_pipeline() {
        let cases: [(&[u8], &[u8], &[&str]); 22] = [
            (b"a\r\nb\r\n", b"a\nb\n", &["same", "same"]),
            (b"a\r\r\nb\r\r\n", b"a\r\nb\r\n", &["same", "same"]),
            (b"a\r\nb\nc\rd", b"a\nb\nc\nd", &["same", "same", "same", "same"]),
            (b"a\nb", b"a\nb\n", &["same", "same"]),
            (b"\xef\xbb\xbfa\nb\n", b"a\nb\n", &["same", "same"]),
            (b"a \nb\n", b"a\nb\n", &["similar", "same"]),
            (b"  a\nb\n", b"a\nb\n", &["similar", "same"]),
            (b"a\tb\n", b"a b\n", &["similar"]),
            (b"void main( )\n", b"void main()\n", &["similar"]),
            (b"alpha\n", b"ALPHA\n", &["similar"]),
            (b"a\nc\n", b"a\nb\nc\n", &["same", "rightorphan", "same"]),
            (b"a\nb\nc\n", b"a\nc\n", &["same", "leftorphan", "same"]),
            (
                b"h1\nx\ny\nz\nh2\n",
                b"h1\np\nq\nr\nh2\n",
                &["same", "different", "different", "different", "same"],
            ),
            (b"a\nb\nc\nd\n", b"a\nc\nd\nb\n", &["same", "leftorphan", "same", "same", "rightorphan"]),
            (
                b"a\nb\nc\nd\n",
                b"c\nd\na\nb\n",
                &["leftorphan", "leftorphan", "same", "same", "rightorphan", "rightorphan"],
            ),
            (b"x\nx\nx\n", b"x\nx\n", &["same", "same", "leftorphan"]),
            (b"x\ny\n", b"x\ny\n", &["same", "same"]),
            (b"", b"only\n", &["rightorphan"]),
            (b"", b"", &[]),
            (b"same\nbeta\ndiff1\n", b"same\nBETA\ndiff2\n", &["same", "similar", "different"]),
            (b"a\x01b\nc\x07d\n", b"a\x01b\nc\x1ad\n", &["same", "different"]),
            (b"col1\tcol2\n", b"col1\tcol3\n", &["different"]),
        ];
        for (l, r, want) in cases {
            assert_eq!(statuses(l, r, ReportOptions::default()), want, "{l:?} vs {r:?}");
        }
    }

    #[test]
    fn syntax_anchors_use_the_left_path_extension() {
        // Same bytes, different grammar: the extension decides.
        let c = compare_bytes_at(
            b"int Abc = 1;\n",
            b"int abc = 1;\n",
            r"D:\x\a.c",
            r"D:\x\b.c",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || false,
        )
        .unwrap();
        assert_eq!(c.statuses(), vec!["different"]);
        assert_eq!(c.grammar, Grammar::Cpp);

        let t = compare_bytes_at(
            b"int Abc = 1;\n",
            b"int abc = 1;\n",
            r"D:\x\a.txt",
            r"D:\x\b.txt",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || false,
        )
        .unwrap();
        assert_eq!(t.statuses(), vec!["similar"]);
        assert_eq!(t.grammar, Grammar::PlainText);
    }

    #[test]
    fn comment_anchor_under_syntax_grammar() {
        let c = compare_bytes_at(
            b"// old note\nx;\n",
            b"// new note\nx;\n",
            r"D:\x\a.c",
            r"D:\x\b.c",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || false,
        )
        .unwrap();
        assert_eq!(c.statuses(), vec!["similar", "same"]);
    }

    // ---------------------------------------------------------------
    // Option semantics
    // ---------------------------------------------------------------

    #[test]
    fn display_options_select_the_golden_sequences() {
        let l = b"same line\ncase diff\nCase Diff\nws diff \nreal diff 1\nreal diff 2\n";
        let r = b"same line\ncase diff\nCASE DIFF\nws diff\nreal diff 9\nreal diff 2\n";
        assert_eq!(
            statuses(l, r, opts("display-all")),
            vec!["same", "same", "similar", "similar", "different", "same"]
        );
        assert_eq!(
            statuses(l, r, opts("display-mismatches")),
            vec!["similar", "similar", "different"]
        );
        assert_eq!(
            statuses(l, r, opts("display-context")),
            vec!["same", "same", "similar", "similar", "different", "same"]
        );
        assert_eq!(statuses(l, r, opts("display-matches")), vec!["same", "same", "same"]);
        assert_eq!(
            statuses(l, r, opts("ignore-unimportant")),
            vec!["same", "same", "same", "same", "different", "same"]
        );
    }

    #[test]
    fn ignore_unimportant_merges_ids_onto_one_text_element() {
        // opt-ignore-unimportant: ltid=3 and rtid=3 share a single <text>.
        let l = b"same line\ncase diff\nCase Diff\nws diff \nreal diff 1\nreal diff 2\n";
        let r = b"same line\ncase diff\nCASE DIFF\nws diff\nreal diff 9\nreal diff 2\n";
        let xml = cmp(l, r, opts("ignore-unimportant")).render(Layout::Xml);
        assert!(xml.contains("<text ltid=\"3\" rtid=\"3\">Case Diff</text>"), "{xml}");
        assert!(xml.contains("<text ltid=\"4\" rtid=\"4\">ws diff </text>"), "{xml}");
        assert!(xml.contains("<ignoreunimportant/>"), "{xml}");
        // The genuinely different line still has two elements.
        assert!(xml.contains("<text ltid=\"5\">real diff 1</text>"), "{xml}");
        assert!(xml.contains("<text rtid=\"5\">real diff 9</text>"), "{xml}");
    }

    #[test]
    fn statistics_is_invariant_under_ignore_unimportant() {
        // m52 `iu-both-sides`: BC's statistics CSV is identical with and
        // without `options:ignore-unimportant`, so the layout renders from the
        // un-collapsed groups even though every other layout sees the folded
        // ones. The paths name .c so the comments are unimportant lines.
        let l = b"int a;\n// c1\n// c2\n";
        let r = b"int b;\n// c3\n";
        let build = |options| {
            compare_bytes_at(
                l,
                r,
                r"D:\x\L.c",
                r"D:\x\R.c",
                options,
                Stamp::from_parts(2026, 10, 13, 9, 43, 7),
                &mut || false,
            )
            .unwrap()
        };
        let plain = build(opts("")).render(Layout::Statistics);
        let folded = build(opts("ignore-unimportant")).render(Layout::Statistics);
        assert_eq!(plain, folded);
        // m52 `both-sides` row: IOriginal=1 (the code line), UOriginal=2 (the
        // two left comments, whether paired or not), UChanged=1 (the similar
        // comment pair), UDeleted=1 (the leftover left comment).
        let row = folded.split("\r\n").nth(3).unwrap();
        assert!(row.ends_with(",1,0,0,1,2,0,1,1"), "{row}");
    }

    #[test]
    fn display_mismatches_xml_matches_the_golden_body() {
        let l = b"same line\ncase diff\nCase Diff\nws diff \nreal diff 1\nreal diff 2\n";
        let r = b"same line\ncase diff\nCASE DIFF\nws diff\nreal diff 9\nreal diff 2\n";
        let xml = cmp(l, r, opts("display-mismatches")).render(Layout::Xml);
        assert!(xml.contains("\t\t<mode>Differences</mode>\r\n"), "{xml}");
        assert!(!xml.contains("same line"), "{xml}");
        assert!(xml.contains("<text ltid=\"3\">Case Diff</text>"), "{xml}");
    }

    // ---------------------------------------------------------------
    // File information
    // ---------------------------------------------------------------

    #[test]
    fn file_info_records_size_lines_encoding_and_path_verbatim() {
        let c = compare_bytes_at(
            b"\xff\xfea\x00\n\x00",
            b"a\n",
            r"D:\a\L.txt",
            r"D:\b\R.txt",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || false,
        )
        .unwrap();
        assert_eq!(c.left.bytes, 6);
        assert_eq!(c.left.lines, 1);
        assert_eq!(c.left.encoding, Encoding::Utf16Le);
        assert!(!c.left.had_invalid_bytes);
        assert_eq!(c.right.encoding, Encoding::Utf8);
        // Paths are echoed exactly, not canonicalised.
        assert_eq!(c.left.path, r"D:\a\L.txt");
        assert_eq!(c.right.path, r"D:\b\R.txt");
    }

    #[test]
    fn invalid_utf8_is_recorded_on_the_side_that_has_it() {
        let c = compare_bytes_at(
            b"caf\xe9\n",
            b"caf\xc3\xa9\n",
            r"D:\x\L.txt",
            r"D:\x\R.txt",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || false,
        )
        .unwrap();
        assert!(c.left.had_invalid_bytes, "left holds caf\\xE9");
        assert!(!c.right.had_invalid_bytes, "right is valid UTF-8");
        assert_eq!(c.statuses(), vec!["different"]);
    }

    #[test]
    fn counts_and_all_same_agree_with_the_groups() {
        let c = cmp(b"a\nb\n", b"a\nc\n", ReportOptions::default());
        assert_eq!(c.count(Status::Same), 1);
        assert_eq!(c.count(Status::Different), 1);
        assert_eq!(c.count(Status::LeftOrphan), 0);
        assert!(!c.is_all_same());
        assert_eq!(c.difference_sections, 1);

        let c = cmp(b"a\nb\n", b"a\nb\n", ReportOptions::default());
        assert!(c.is_all_same());
        assert_eq!(c.difference_sections, 0);
    }

    /// The `/qc` predicate, against the cells measured in
    /// `probes/u6_qc_orphans.py`. Each case names the `/qc` code the Oracle
    /// returned for the same input, so a change in this predicate that would
    /// change the product's exit code fails here.
    ///
    /// The C-text cases use a `.c` path because that is the grammar the probe
    /// used: in plain text a `// note` line is real content (an important
    /// one-sided line, `/qc` = 13), while under the C grammar it is a comment
    /// (unimportant, `/qc` = 12). The path is an input to the verdict, so the
    /// test must carry the same one the measurement did.
    #[test]
    fn unimportant_only_differences_match_the_measured_qc_codes() {
        struct Case {
            left: &'static [u8],
            right: &'static [u8],
            path: &'static str,
            qc: i32,
            why: &'static str,
        }
        let cases = [
            // identical: `/qc` = 1 (handled before this predicate, but the
            // predicate must not call it "important")
            Case { left: b"x = 1\n", right: b"x = 1\n", path: "L.txt", qc: 1,
                   why: "identical" },
            // trailing whitespace only: `/qc` = 12
            Case { left: b"x = 1   \n", right: b"x = 1\n", path: "L.txt", qc: 12,
                   why: "trailing whitespace" },
            // one-sided comment line: `/qc` = 12 (u6 `extra-comment-left`)
            Case { left: b"// note\nint a;\n", right: b"int a;\n", path: "L.c",
                   qc: 12, why: "extra left comment" },
            Case { left: b"int a;\n", right: b"// note\nint a;\n", path: "L.c",
                   qc: 12, why: "extra right comment" },
            // one-sided blank line: `/qc` = 12 (u6 `extra-blank-left`)
            Case { left: b"int a;\n\nint b;\n", right: b"int a;\nint b;\n",
                   path: "L.c", qc: 12, why: "extra blank" },
            // one-sided code line: `/qc` = 13 (u6 `extra-code-left`)
            Case { left: b"int b;\nint a;\n", right: b"int a;\n", path: "L.c",
                   qc: 13, why: "extra left code" },
            Case { left: b"int a;\n", right: b"int b;\nint a;\n", path: "L.c",
                   qc: 13, why: "extra right code" },
            // an important in-line change: `/qc` = 13
            Case { left: b"x = 1\n", right: b"x = 2\n", path: "L.txt", qc: 13,
                   why: "important change" },
        ];
        for c in &cases {
            let got = compare_bytes_at(
                c.left,
                c.right,
                &format!(r"D:\x\{}", c.path),
                &format!(r"D:\x\R{}", &c.path[1..]),
                ReportOptions::default(),
                Stamp::from_parts(2026, 10, 13, 9, 43, 7),
                &mut || false,
            )
            .unwrap();
            let expected = c.qc == 1 || c.qc == 12;
            assert_eq!(
                got.differences_are_all_unimportant(),
                expected,
                "{}: report statuses {:?}, /qc={}",
                c.why,
                got.raw_statuses(),
                c.qc
            );
        }
    }

    #[test]
    fn every_layout_renders_without_placeholder_text() {
        let c = cmp(b"a\nb\n", b"a\nc\n", ReportOptions::default());
        for layout in Layout::ALL {
            let text = c.render(layout);
            assert!(!text.is_empty(), "{layout:?} produced nothing");
            assert!(!text.contains("TODO"), "{layout:?} contains a TODO");
            assert!(!text.contains("unimplemented"), "{layout:?} is a stub");
        }
    }

    #[test]
    fn errors_are_explicit_never_silent() {
        // A missing file must be an error, not an empty comparison.
        let err = compare_files(
            Path::new(r"D:\definitely\not\here\L.txt"),
            Path::new(r"D:\definitely\not\here\R.txt"),
            ReportOptions::default(),
        )
        .unwrap_err();
        match &err {
            CompareError::Io { path, .. } => assert!(path.to_string_lossy().contains("L.txt")),
            other => panic!("expected an Io error, got {other:?}"),
        }
        assert!(err.to_string().contains("cannot read"));
    }

    #[test]
    fn cancellation_propagates_as_an_error_not_an_empty_report() {
        let l: Vec<u8> = (0..300).map(|i| format!("{i}\n")).collect::<String>().into_bytes();
        let r: Vec<u8> = (0..300).map(|i| format!("{}\n", i + 1)).collect::<String>().into_bytes();
        let err = compare_bytes_at(
            &l,
            &r,
            "L.txt",
            "R.txt",
            ReportOptions::default(),
            Stamp::from_parts(2026, 1, 1, 0, 0, 0),
            &mut || true,
        )
        .unwrap_err();
        assert!(matches!(err, CompareError::Diff(DiffError::Cancelled)));
    }

    #[test]
    fn classify_pair_is_exposed_for_diagnostics() {
        assert_eq!(classify_pair("a", "a", Grammar::PlainText), Verdict::Same);
        assert_eq!(classify_pair("a ", "a", Grammar::PlainText), Verdict::Similar);
        assert_eq!(classify_pair("A", "a", Grammar::PlainText), Verdict::Similar);
        assert_eq!(classify_pair("A", "a", Grammar::Cpp), Verdict::Different);
        // u2: string interiors stay important; mixed lines fold on comments.
        assert_eq!(
            classify_pair("char *a = \"a b\";", "char *a = \"a  b\";", Grammar::Cpp),
            Verdict::Different
        );
        assert_eq!(
            classify_pair("x = 1; // note", "x = 1; // other", Grammar::Cpp),
            Verdict::Similar
        );
    }
}

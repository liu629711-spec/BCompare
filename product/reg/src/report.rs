//! Frame assembly for the registry channel (docs/17 §frame). The product
//! emits ENGLISH frame text — the same split as `reacmp-dir`/`reacmp-pic`
//! (the Oracle's Chinese is folded onto English by the harness normalizer,
//! norm-5). English label spellings are corroborated by the reference
//! install's archived frames (runs/m101f-regbox-reference, m101i-reference).
//!
//! Frame lines, in order, each CRLF-terminated:
//!
//! ```text
//! [title | "Registry Compare"]
//! Produced: <stamp>            (slash dates on disk; display rewrites)
//! <empty>
//! [Mode:  <All|Differences|Same>]   sbs ONLY, when a display option was given
//! [Left file: <L>[:\\<basekey>]]    suffix only while a key survived (G3)
//! [Right file: <R>[:\\<basekey>]]
//! [Left error: <msg>]          Parsing Error (l: c) / Unsupported Type /
//! [Right error: <msg>]          Deletes/Duplicates Skipped /
//!                               File Encoding Error (Line 1)
//! <table>                      sbs only: header, rule, body, rule
//! <count lines>                both layouts; zero categories omitted;
//!                               order same → left orphan → right orphan → diff
//! ```

use crate::engine::{
    compare_sbs, compute_geometry, render_header, render_line, render_rule, Counts, Locale,
    Marker, SbsRow,
};
use crate::parse::{ParseNote, RegError, RegFile};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Layout {
    SideBySide,
    Summary,
}

impl Layout {
    pub const NAMES: &'static str = "side-by-side, summary";
    pub fn parse(word: &str) -> Option<Layout> {
        match word.to_ascii_lowercase().as_str() {
            "side-by-side" => Some(Layout::SideBySide),
            "summary" => Some(Layout::Summary),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Display {
    All,
    Mismatches,
    Matches,
}

impl Display {
    /// (measured R8: `display-all` shows the Mode line `Mode:  All` even for
    /// the default; plain sbs without options has NO Mode line (R1/G-series)
    /// -- wait: 92 sbs tables all carry `模式：  全部` (G/i series sbs).
    /// Re-checked against the corpus: EVERY sbs table has the Mode line; the
    /// summary cells (G*-sum, I*) never do. display-mismatches/matches set
    /// the value (I4 差异 / I12 相同).)
    pub fn from_options(options: &[String]) -> Display {
        let mut d = Display::All;
        for o in options {
            match o.to_ascii_lowercase().as_str() {
                "display-mismatches" => d = Display::Mismatches,
                "display-matches" => d = Display::Matches,
                _ => {}
            }
        }
        d
    }
}

pub fn mode_text(d: Display) -> &'static str {
    match d {
        Display::All => "All",
        Display::Mismatches => "Differences",
        Display::Matches => "Same",
    }
}

/// One side's frame error text (measured EN forms in the reference
/// archives): Parsing Error (l: c), Unsupported Type, Deletes/Duplicates
/// Skipped, File Encoding Error (Line 1) -- the last is carried by
/// [`RegError::Encoding`] when the raw bytes fail the encoding sniff
/// (R19/I7 PNG pair).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SideError {
    Parsing { line: usize, col: usize },
    UnsupportedType,
    DeletedDup,
    Encoding { line: usize },
}

impl SideError {
    pub fn text(&self) -> String {
        match self {
            SideError::Parsing { line, col } => format!("Parsing Error ({line}: {col})"),
            SideError::UnsupportedType => "Unsupported Type".to_string(),
            SideError::DeletedDup => "Deletes/Duplicates Skipped".to_string(),
            SideError::Encoding { line } => format!("File Encoding Error (Line {line})"),
        }
    }

    pub fn from_parse(e: Option<&RegError>, note: Option<ParseNote>) -> Option<SideError> {
        match e {
            Some(RegError::Parsing { line, col }) => {
                Some(SideError::Parsing { line: *line, col: *col })
            }
            Some(RegError::UnsupportedType) => Some(SideError::UnsupportedType),
            Some(RegError::Encoding { line }) => Some(SideError::Encoding { line: *line }),
            None => note.map(|_| SideError::DeletedDup),
        }
    }
}

/// zh form (for the record and probe cross-checks only; the report writes
/// English). Parsing coordinates render with the fullwidth colon in the
/// Chinese Oracle: `解析错误 (5： 1)`.
pub fn error_text_zh(e: &RegError) -> String {
    match e {
        RegError::Parsing { line, col } => format!("解析错误 ({line}： {col})"),
        RegError::UnsupportedType => "不被支持的类型".to_string(),
        RegError::Encoding { line } => format!("文件编码错误 (第 {line} 行)"),
    }
}

/// Count lines (measured order same → important left orphan → important
/// right orphan → important difference; zero omitted; no unimportant
/// category -- I1/I2). EN forms corroborated by the reference archive's
/// count lines (`1 important left orphan item(s)` F4-sum reference).
pub fn count_lines(c: &Counts) -> Vec<String> {
    let mut v = Vec::new();
    if c.same > 0 {
        v.push(format!("{} same item(s)", c.same));
    }
    if c.left_orphan > 0 {
        v.push(format!("{} important left orphan item(s)", c.left_orphan));
    }
    if c.right_orphan > 0 {
        v.push(format!("{} important right orphan item(s)", c.right_orphan));
    }
    if c.diff > 0 {
        v.push(format!("{} important difference item(s)", c.diff));
    }
    v
}

/// Apply a display filter to the sbs rows (measured I4: mismatches drop the
/// matched `=` rows and keep orphans; I12: matches keeps ONLY the `=` rows
/// -- both drop every header/orphan). Key-pair headers survive mismatches
/// only when their side's group still renders rows above them (measured I4:
/// `Kx` header kept for its two +- rows). Simplified to the measured shape:
/// the row stream is a full traversal, so I4's kept set =
/// {orphans, headers before/around orphans, diffs} and I12's kept set =
/// {same rows}. Key-pair rows ride with the following group only if some
/// later row (before the next key-pair header at the same level) is kept:
/// for the measured corpus, mismatches drops Same rows only -- I4 has no
/// matched headers at all; matches drops everything but Same rows.
pub fn filter_rows(rows: &[SbsRow], d: Display) -> Vec<SbsRow> {
    match d {
        Display::All => rows.to_vec(),
        Display::Mismatches => rows.iter().filter(|r| r.marker != Marker::Same).cloned().collect(),
        Display::Matches => rows.iter().filter(|r| r.marker == Marker::Same).cloned().collect(),
    }
}

/// File line with the basekey suffix: `<path>:\\<basekey>` (double
/// backslash measured; NO suffix when the side kept no key: G3 orphan side,
/// N10, N4/N9, I7 PNG).
fn file_line(label: &str, path: &str, f: &RegFile) -> String {
    match &f.basekey {
        Some(b) => format!("{label}{path}:\\\\{b}"),
        None => format!("{label}{path}"),
    }
}

/// The frame's scalar inputs bundled so the renderer signature stays
/// clippy-clean (the picture channel accepts one too-many-args warning;
/// this crate does not).
#[derive(Debug, Clone, Copy)]
pub struct ReportFrame<'a> {
    pub layout: Layout,
    pub display: Display,
    pub left_path: &'a str,
    pub right_path: &'a str,
    pub stamp: &'a str,
    pub title: Option<&'a str>,
    pub locale: &'a Locale,
}

/// Assemble the full report text for one registry comparison. The sides
/// come from [`crate::parse::parse_reg`] (raw bytes), which already carries
/// the encoding-sniff error (R19/I7); the paths are printed verbatim.
pub fn render_registry_report(frame: &ReportFrame<'_>, left: &RegFile, right: &RegFile) -> String {
    let ReportFrame { layout, display, left_path, right_path, stamp, title, locale: loc } = *frame;
    let mut lines: Vec<String> = Vec::new();
    lines.push(title.unwrap_or("Registry Compare").to_string());
    lines.push(format!("Produced: {stamp}"));
    lines.push(String::new());
    if layout == Layout::SideBySide {
        lines.push(format!("Mode:  {}", mode_text(display)));
    }
    lines.push(file_line("Left file: ", left_path, left));
    lines.push(file_line("Right file: ", right_path, right));
    let le = SideError::from_parse(left.error.as_ref(), left.note);
    let re = SideError::from_parse(right.error.as_ref(), right.note);
    if let Some(e) = &le {
        lines.push(format!("Left error: {}", e.text()));
    }
    if let Some(e) = &re {
        lines.push(format!("Right error: {}", e.text()));
    }

    let res = compare_sbs(left, right, loc);
    let kept = filter_rows(&res.rows, display);
    match layout {
        // sbs: frame + Mode + files + errors + table; NO count lines (the
        // archived *-sid reports end at the rule line -- G1-sid/G8-sid bytes).
        Layout::SideBySide => {
            let g = compute_geometry(&kept, loc);
            lines.push(render_header(&g, loc));
            lines.push(render_rule(&g));
            for r in &kept {
                lines.push(render_line(r, &g));
            }
            lines.push(render_rule(&g));
        }
        // summary: frame + files + errors + count lines; no table, no Mode
        // line (G*-sum/C*-sum).
        Layout::Summary => {
            for c in count_lines(&res.counts) {
                lines.push(c);
            }
        }
    }
    lines.join("\r\n") + "\r\n"
}

/// The zero-file shell (measured R11/G11: 99 bytes, BOM, and the
/// `模式：  全部` line that picture's shell does NOT have):
/// `Registry Compare\r\nProduced: <stamp>\r\n\r\nMode:  All\r\nBase folder: \r\n`
/// -- the zh shell is `注册表比较(R)\r\n已产生： <slash>\r\n\r\n模式：  全部\r\n基点文件夹： \r\n`
/// with the same BOM; EN form per the reference install convention (norm-5
/// folds). BOM as leading U+FEFF (executor writes the three bytes).
pub fn render_registry_shell(stamp: &str, title: Option<&str>, mode: Display) -> String {
    format!(
        "\u{feff}{}\r\nProduced: {stamp}\r\n\r\nMode:  {}\r\nBase folder: \r\n",
        title.unwrap_or("Registry Compare"),
        mode_text(mode)
    )
}

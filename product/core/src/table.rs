//! M6 — the table (CSV) comparison engine and its three report layouts.
//!
//! Every rule in this module is **O**bserved in the archived Oracle reports
//! under `product/verify/runs/{m60-table-probe,m61-rowalign,m61b-pairing,
//! m61c-detect,m61d-residual,m62b-width}-*` and recorded in
//! `product/docs/13-m6-table-channel.md` §4/§5. The offline simulator
//! `extracted/_scratch/table/simulate_table.py` reproduces 56/56 archived
//! report bodies with this model; unit tests below transcribe the
//! discriminating fixtures verbatim from the Oracle archives.
//!
//! # Channel facts
//!
//! * The table engine has **no `xml` layout** (`layout:xml` -> BC exit 106;
//!   probe T2). [`TableError::XmlUnsupported`] makes the CLI fail closed.
//! * `data-report` refuses **every** `options:` payload with BC exit 105
//!   (probes P6-P9) — the table channel has no display filtering. Option
//!   validation is therefore the CLI's job; this module renders the default
//!   (display-all) shape only.
//! * `*.csv` hits the built-in CSV format: delimiter **fixed comma**, qualifier
//!   `"` (docs/13 §4.5, batch-5: tab/;/| stay inside cells). Auto-detection
//!   for other extensions is out of M6 scope; the caller must route only the
//!   fixed-comma format here.
//!
//! # Row model (docs/13 §4.1)
//!
//! A row is a parsed CSV record; a newline inside a quoted cell does **not**
//! end the row (T21: interleaved numbers the quoted 2-line cell as ONE row).
//! The final empty segment after a trailing newline is dropped (the same
//! "no phantom row" convention the archived fixtures were generated under;
//! W4's double-trailing-newline shape is a recorded residual, docs/13 §5).
//!
//! # Alignment (docs/13 §4.2-§4.3)
//!
//! Content LCS over the whole file via the shared [`crate::myers`] core, with
//! gap zip: rows between consecutive anchors pair positionally to `<>`,
//! leftovers become `+-`/`-+` (P1: a 2x2 all-different gap yields two `<>`
//! pairs, not four orphans — there is no closeness/similarity pairing).
//! [`crate::myers::diff_matches`] returns only anchor pairs; the group list
//! is then built by sweeping the unanchored regions — one pass, O(n+m).
//!
//! # Equality and display (docs/13 §4.4)
//!
//! Two rows match when their cell lists are equal after trimming each cell;
//! interior whitespace is significant (P4). Rendered display text is the
//! trimmed cell with any embedded newline mapped to NUL (measured raw bytes
//! of the T21 report); a numeric cell (`-?\d+(\.\d+)?` whole) is
//! right-justified in side-by-side columns; interleaved left-justifies
//! everything (T19/T21/W1 measured).

use crate::myers::{diff_matches, map_ids};
use crate::stamp::Stamp;
use std::fmt;

const CRLF: &str = "\r\n";

/// The layouts the table channel accepts (measured: T1/T4/T3 exit 0;
/// T2 `xml` exit 106).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TableLayout {

    SideBySide,
    Interleaved,
    Summary,
}

impl TableLayout {
    /// Parse a `layout:<name>` token. `over-under` is not accepted here:
    /// the table help lists only three layouts and no alias is observed.
    pub fn parse(name: &str) -> Option<TableLayout> {
        match name {
            "side-by-side" => Some(TableLayout::SideBySide),
            "interleaved" => Some(TableLayout::Interleaved),
            "summary" => Some(TableLayout::Summary),
            _ => None,
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            TableLayout::SideBySide => "side-by-side",
            TableLayout::Interleaved => "interleaved",
            TableLayout::Summary => "summary",
        }
    }
}

/// Failure modes of the table engine. All explicit; none yields a placeholder.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TableError {
    /// `layout:xml` on a table report: the table engine has no XML layout
    /// (BC exit 106, probe T2). The CLI maps this to the command error.
    XmlUnsupported,
    /// Inputs exceed the alignment diagonal limit (propagated from myers).
    TooLarge { needed: usize, limit: usize },
    /// The alignment search could not complete (propagated; unreachable by
    /// Myers' theorem, kept explicit so a defect surfaces loudly).
    Alignment(&'static str),
}

impl fmt::Display for TableError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TableError::XmlUnsupported => write!(
                f,
                "the table report has no xml layout (layouts: side-by-side, \
                 interleaved, summary)"
            ),
            TableError::TooLarge { needed, limit } => write!(
                f,
                "inputs too large: {needed} combined rows exceed the {limit}-row \
                 alignment diagonal limit"
            ),
            TableError::Alignment(what) => write!(f, "alignment failed: {what}"),
        }
    }
}

impl std::error::Error for TableError {}

// ---------------------------------------------------------------- parsing

/// Parse `text` as rows delimited by `delim` with `"` qualifiers (RFC-4180
/// semantics, the built-in CSV format's measured shape): quoted cells may
/// contain the delimiter and newlines; `""` is an escaped quote; a row ends
/// at a newline outside quotes; the empty segment after the final newline is
/// dropped.
pub fn split_records_delim(text: &str, delim: char) -> Vec<Vec<String>> {
    let mut rows: Vec<Vec<String>> = Vec::new();
    let mut row: Vec<String> = Vec::new();
    let mut field = String::new();
    let mut in_quotes = false;
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if in_quotes {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    field.push('"');
                    chars.next();
                } else {
                    in_quotes = false;
                }
            } else {
                field.push(c);
            }
            continue;
        }
        match c {
            // A quote only starts a qualified cell at a cell boundary; mid
            // cell it is literal (the qualifier marks the cell, not content).
            '"' if field.trim().is_empty() => in_quotes = true,
            c if c == delim => {
                row.push(std::mem::take(&mut field));
            }
            '\n' => {
                row.push(std::mem::take(&mut field));
                rows.push(std::mem::take(&mut row));
            }
            '\r' => {
                if chars.peek() == Some(&'\n') {
                    chars.next();
                }
                row.push(std::mem::take(&mut field));
                rows.push(std::mem::take(&mut row));
            }
            c => field.push(c),
        }
    }
    if !field.is_empty() || !row.is_empty() {
        row.push(field);
        rows.push(row);
    }
    rows
}

/// The fixed-comma entry point (the `.csv` built-in format, docs/13 §4.5).
pub fn split_records(text: &str) -> Vec<Vec<String>> {
    split_records_delim(text, ',')
}

/// The auto-detect candidates in the measured priority order (m65 batch-7:
/// ten pairwise cells, every result consistent with exactly this total
/// order): comma > tab > semicolon > pipe.
const DETECT_PRIORITY: &[char] = &[',', '\t', ';', '|'];

/// The row structure the table engine applies to one comparison.
///
/// Measured (docs/13 §4.5, batches 5/6/7): `.csv` pins the built-in CSV
/// format (fixed comma, no detection — D2/D4/D12/CS1 keep tab, semicolon,
/// pipe and space inside cells); any other extension (and none, S6; uppercase
/// .TXT counts as non-csv, S7) auto-detects **jointly over both sides**
/// (PF1/PF2: comma present only in the right file splits BOTH sides);
/// when no candidate occurs outside quotes anywhere (Q1/SP1/SP3/SP5/S1/W1),
/// BC does not split at all and keeps each line verbatim as one cell —
/// the rawline shape, trailing spaces included (SP5 `a b ` renders width 4).
///
/// The SPACE candidate is deliberately NOT implemented: its acceptance
/// evidence is contradictory in the archive (S4 `a b`/`c d` splits into
/// `A  B`, but SP1 `a b`/`cc d` — one wider cell, same shape — does not;
/// W1 rejects double-space, SP6 renders something between) and the rule is
/// a recorded residual (docs/13 §7). Falling back to rawline reproduces
/// the S1/W1/SP*/Q1 shape; S4 is the one archived cell it cannot, and it is
/// listed as a known difference in the table replay, never silently dropped.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TableFormat {
    /// Comma/`"` qualified parsing, cells trimmed for display (docs/13 §4.4).
    Delimited(char),
    /// One cell per physical line, verbatim, no qualifier handling.
    RawLine,
}

impl TableFormat {
    fn split(self, text: &str) -> Vec<Vec<String>> {
        match self {
            TableFormat::Delimited(d) => split_records_delim(text, d),
            TableFormat::RawLine => split_lines_verbatim(text),
        }
    }

    /// Whether the display layer trims each cell (docs/13 §4.4 P3/P4 for the
    /// delimited formats; rawline keeps cells verbatim — SP5).
    fn trims(self) -> bool {
        matches!(self, TableFormat::Delimited(_))
    }
}

/// Rawline rows: every line is one cell; the bytes are kept except that the
/// cell's LEADING whitespace is dropped (measured m65c SP10: ' ab' renders
/// 'ab') while interior and trailing whitespace survive (W1 `a  b` double
/// space, SP5 `a b ` trailing space). The empty segment after the final
/// newline is dropped like everywhere else (m64 E1).
fn split_lines_verbatim(text: &str) -> Vec<Vec<String>> {
    let mut rows: Vec<Vec<String>> = Vec::new();
    let mut cur = String::new();
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '\n' => rows.push(vec![take_leading_trimmed(&mut cur)]),
            '\r' => {
                if chars.peek() == Some(&'\n') {
                    chars.next();
                }
                rows.push(vec![take_leading_trimmed(&mut cur)]);
            }
            c => cur.push(c),
        }
    }
    if !cur.is_empty() {
        rows.push(vec![take_leading_trimmed(&mut cur)]);
    }
    rows
}

fn take_leading_trimmed(cur: &mut String) -> String {
    let t = cur.trim_start();
    let out = t.to_string();
    cur.clear();
    out
}

/// Does `delim` occur outside quotes anywhere in `text`? The qualifier
/// shields a delimiter from making it a candidate (measured Q1/SP4: a comma
/// living only inside `"..."` does not win detection). The quote rule mirrors
/// [`split_records_delim`] exactly: a quote opens a qualified cell only while
/// the current field is blank (start / after delimiter / after newline).
fn candidate_present(text: &str, delim: char) -> bool {
    let mut in_quotes = false;
    let mut field_blank = true;
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if in_quotes {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    chars.next();
                } else {
                    in_quotes = false;
                }
            }
            continue;
        }
        match c {
            '"' if field_blank => in_quotes = true,
            c if c == delim => return true,
            '\n' | '\r' => field_blank = true,
            c => field_blank = c.is_whitespace(),
        }
    }
    false
}

/// The measured joint-detection rule (PF1/PF2: one delimiter is chosen for
/// BOTH sides from the combined corpus): `.csv` (case-insensitive, either
/// side — mixed-extension pairs are unmeasured, recorded residual) keeps the
/// built-in fixed comma with no detection (CS1/D2/D4/D12 — tab, semicolon,
/// pipe and space stay inside cells); every other extension (and none, S6;
/// uppercase .TXT counts as non-csv, S7) walks the priority chain over BOTH
/// texts, and the first candidate seen outside quotes in either side wins.
/// With no candidate anywhere, BC does not split at all — rawline (Q1/SP3/
/// S1/W1, quotes kept verbatim).
pub fn detect_format(left_text: &str, right_text: &str,
                     left_path: &str, right_path: &str) -> TableFormat {
    if extension_of(left_path).eq_ignore_ascii_case("csv")
        || extension_of(right_path).eq_ignore_ascii_case("csv")
    {
        return TableFormat::Delimited(',');
    }
    for &d in DETECT_PRIORITY {
        if candidate_present(left_text, d) || candidate_present(right_text, d) {
            return TableFormat::Delimited(d);
        }
    }
    TableFormat::RawLine
}

fn extension_of(path: &str) -> &str {
    // Only the FILE part may carry an extension: dots inside directory names
    // are not it (measured S6: an extension-less name detects).
    let file = path.rsplit(['/', '\\']).next().unwrap_or(path);
    match file.rsplit_once('.') {
        Some((stem, ext)) if !stem.is_empty() => ext,
        _ => "",
    }
}

/// The alignment key of a row. Delimited formats compare cells TRIMMED
/// (docs/13 §4.4 P3/P4: interior whitespace significant, edges dropped);
/// rawline compares VERBATIM (measured m65b SP9: `c d ` vs `c d` is `<>`,
/// the trailing space is content).
fn row_key<'a>(row: &'a [String], trims: bool) -> Vec<&'a str> {
    row.iter().map(|c| if trims { c.trim() } else { c.as_str() }).collect()
}

// ---------------------------------------------------------------- alignment

/// One rendered table row entry.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RowStatus {
    Same,
    Changed,
    LeftOrphan,
    RightOrphan,
}

/// An aligned group, mirroring the Oracle report row order.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TableGroup {
    pub left: Option<usize>,
    pub right: Option<usize>,
    pub status: RowStatus,
}

/// Align rows: content LCS via the shared myers core, then gap zip.
///
/// `diff_matches` yields the anchor pairs; between consecutive anchors the
/// unanchored rows pair positionally to [`RowStatus::Changed`] (P1/P2/P12),
/// and the leftovers become orphans. The tie direction (which of two equal
/// LCS paths wins) is the one `crate::myers` implements — the same engine the
/// text channel uses, measured equivalent on T12/T13/T14 (docs/13 §4.2).
pub fn align_rows(
    left: &[Vec<String>],
    right: &[Vec<String>],
    trims: bool,
) -> Result<Vec<TableGroup>, TableError> {
    let keys_l: Vec<Vec<&str>> = left.iter().map(|r| row_key(r, trims)).collect();
    let keys_r: Vec<Vec<&str>> = right.iter().map(|r| row_key(r, trims)).collect();
    let (ids_l, ids_r) = map_ids(&keys_l, &keys_r);
    let pairs = diff_matches(&ids_l, &ids_r).map_err(|e| match e {
        crate::myers::DiffError::TooLarge { needed, limit } => {
            TableError::TooLarge { needed, limit }
        }
        other => TableError::Alignment(match other {
            crate::myers::DiffError::Cancelled => "cancelled",
            crate::myers::DiffError::SearchExhausted => "search exhausted",
            crate::myers::DiffError::NoProgress => "no progress",
            crate::myers::DiffError::TooLarge { .. } => "too large",
        }),
    })?;
    let mut out: Vec<TableGroup> = Vec::new();
    let mut pi = 0usize;
    let mut pj = 0usize;
    fn zip_gap(
        pi: usize,
        pj: usize,
        li: usize,
        lj: usize,
        out: &mut Vec<TableGroup>,
    ) {
        let lefts: Vec<usize> = (pi..li).collect();
        let rights: Vec<usize> = (pj..lj).collect();
        let n = lefts.len().min(rights.len());
        for t in 0..n {
            out.push(TableGroup {
                left: Some(lefts[t]),
                right: Some(rights[t]),
                status: RowStatus::Changed,
            });
        }
        for t in n..lefts.len() {
            out.push(TableGroup {
                left: Some(lefts[t]),
                right: None,
                status: RowStatus::LeftOrphan,
            });
        }
        for t in n..rights.len() {
            out.push(TableGroup {
                left: None,
                right: Some(rights[t]),
                status: RowStatus::RightOrphan,
            });
        }
    }
    for &(i, j) in &pairs {
        zip_gap(pi, pj, i, j, &mut out);
        out.push(TableGroup {
            left: Some(i),
            right: Some(j),
            status: RowStatus::Same,
        });
        pi = i + 1;
        pj = j + 1;
    }
    zip_gap(pi, pj, left.len(), right.len(), &mut out);
    Ok(out)
}

// ---------------------------------------------------------------- rendering

/// True for a fully numeric cell: `-?\d+(\.\d+)?` exactly.
///
/// ASCII digits only: Python's `\d` in the simulator would also match
/// Unicode digits, but no archived report contains one, so the Unicode
/// behaviour is a recorded unknown (docs/13 §5) and the stricter rule is
/// what the evidence supports.
fn numeric(s: &str) -> bool {
    let t = s.strip_prefix('-').unwrap_or(s);
    if t.is_empty() {
        return false;
    }
    let mut digits = 0usize;
    let mut dots = 0usize;
    for c in t.chars() {
        match c {
            '0'..='9' => digits += 1,
            '.' => dots += 1,
            _ => return false,
        }
    }
    digits > 0 && dots <= 1 && !t.starts_with('.') && !t.ends_with('.')
}

/// Rendered display text. Delimited formats TRIM the cell and map embedded
/// newlines to NUL (measured T21 raw bytes; docs/13 §4.4 P3/P4). Rawline
/// drops only the LEADING whitespace (measured m65c SP10: line ` ab` renders
/// as `ab`) and keeps the rest verbatim (W1 `a  b` interior double,
/// m65b SP5 `a b ` trailing single).
fn display(cell: &str, trims: bool) -> String {
    let base = if trims {
        cell.trim()
    } else {
        cell.trim_start()
    };
    base.replace('\n', "\u{0}")
}

/// Column count: the max cell count over the rows the report shows.
fn column_count(groups: &[TableGroup], rows: &[Vec<String>], side: u8) -> usize {
    groups
        .iter()
        .filter_map(|g| match side {
            0 => g.left,
            _ => g.right,
        })
        .map(|i| rows[i].len())
        .max()
        .unwrap_or(0)
}

/// Per-side column widths over a global column count: each side's own rows
/// (None rows contribute the empty display); the header letter forces a
/// floor (1 for A..Z, 2 for AA.. measured m64 C2-29narrow). No cross-side
/// forcing (measured m62b W1/W2).
fn side_widths(
    groups: &[TableGroup],
    rows: &[Vec<String>],
    side: u8,
    ncols: usize,
    trims: bool,
) -> Vec<usize> {
    (0..ncols)
        .map(|c| {
            groups
                .iter()
                .filter_map(|g| match side {
                    0 => g.left,
                    _ => g.right,
                })
                .map(|i| {
                    let v = rows
                        .get(i)
                        .and_then(|r| r.get(c))
                        .map(|s| display(s, trims))
                        .unwrap_or_default();
                    v.chars().count()
                })
                .max()
                .unwrap_or(0)
                .max(column_letter(c).chars().count())
        })
        .collect()
}

/// The header letter for column `c` (0-based). Measured (m64 C1-28col and
/// C2-29narrow, runs/m64-residual-*, m64c2-letters-*): A..Z for the first 26
/// columns, then Excel-style double letters `AA`, `AB`, `AC`... — the earlier
/// `#` placeholder and its "unobserved" residual are closed.
fn column_letter(c: usize) -> String {
    let mut n = c;
    let mut letters = Vec::new();
    loop {
        letters.push((b'A' + (n % 26) as u8) as char);
        if n < 26 {
            break;
        }
        n = n / 26 - 1;
    }
    letters.reverse();
    letters.into_iter().collect()
}

/// Cells padded to their column widths (empty cells included) and joined by
/// a single space; the string is NOT right-trimmed — the caller rstrips the
/// whole report line once (measured F1 `a   c <> a b c`).
fn render_cells(
    rows: &[Vec<String>],
    gi: Option<usize>,
    ws: &[usize],
    num_right: bool,
    trims: bool,
) -> String {
    ws.iter()
        .enumerate()
        .map(|(c, &w)| {
            let raw = match gi {
                Some(i) => rows
                    .get(i)
                    .and_then(|r| r.get(c))
                    .map(|s| s.as_str())
                    .unwrap_or(""),
                None => "",
            };
            let d = display(raw, trims);
            // Numeric right-justification is a measured property of the
            // DELIMITED formats (docs/13 §5); rawline cells are unmeasured
            // (S1/W1/SP* have no numeric lines) and stay left-justified.
            let right = trims && num_right && !raw.is_empty() && numeric(raw.trim());
            pad(&d, w, right)
        })
        .collect::<Vec<_>>()
        .join(" ")
}

fn pad(s: &str, w: usize, right: bool) -> String {
    let n = s.chars().count();
    if n >= w {
        return s.to_string();
    }
    if right {
        format!("{}{}", " ".repeat(w - n), s)
    } else {
        format!("{}{}", s, " ".repeat(w - n))
    }
}

/// Column letters, padded exactly like cells (measured: widths [2,1] ->
/// 'A  B'; [1,3,1] -> 'A B   C'). `rstrip` false keeps the trailing column
/// padding (the side-by-side header's left block).
fn render_header(ws: &[usize], rstrip: bool) -> String {
    let out = ws
        .iter()
        .enumerate()
        .map(|(c, &w)| pad(&column_letter(c), w, false))
        .collect::<Vec<_>>()
        .join(" ");
    if rstrip {
        out.trim_end().to_string()
    } else {
        out
    }
}

fn marker_field(status: RowStatus, all_same: bool) -> &'static str {
    match status {
        RowStatus::Same if all_same => " = ",
        RowStatus::Same => " =  ",
        RowStatus::Changed => " <> ",
        RowStatus::LeftOrphan => " +- ",
        RowStatus::RightOrphan => " -+ ",
    }
}

fn rstrip(s: String) -> String {
    s.trim_end().to_string()
}

/// `side-by-side` body rows (frame excluded). Every row is
/// `left_cells + marker + right_cells` — an orphan's missing side renders as
/// the full-width blank cell field — then the line is rstripped once.
pub fn side_by_side_body(
    groups: &[TableGroup],
    left: &[Vec<String>],
    right: &[Vec<String>],
    trims: bool,
) -> Vec<String> {
    let ncols = column_count(groups, left, 0).max(column_count(groups, right, 1));
    let lw = side_widths(groups, left, 0, ncols, trims);
    let rw = side_widths(groups, right, 1, ncols, trims);
    let all_same = groups.iter().all(|g| g.status == RowStatus::Same);
    // Measured (m65b SP5, runs/m65b-spacerules-*): the rule width counts
    // the line BEFORE the final rstrip (a rawline cell's trailing spaces are
    // display content). All 100 delimited archive cells agree either way
    // because their trailing columns never pad past the content; keep the
    // raw line for width, rstrip once for the emitted row.
    let raws: Vec<String> = groups
        .iter()
        .map(|g| {
            let lt = render_cells(left, g.left, &lw, true, trims);
            let rt = render_cells(right, g.right, &rw, true, trims);
            format!("{}{}{}", lt, marker_field(g.status, all_same), rt)
        })
        .collect();
    let blank = if all_same { "   " } else { "    " };
    let raw_header = format!(
        "{}{}{}",
        render_header(&lw, false),
        blank,
        render_header(&rw, true)
    );
    let header = rstrip(raw_header.clone());
    let width = std::iter::once(raw_header.chars().count())
        .chain(raws.iter().map(|r| r.chars().count()))
        .max()
        .unwrap_or(0);
    let rows: Vec<String> = raws.into_iter().map(rstrip).collect();
    let rule = "-".repeat(width);
    let mut out = vec![header, rule.clone()];
    out.extend(rows);
    out.push(rule);
    out
}

/// `interleaved` body rows. Shared column widths (per-column max of both
/// sides); a 2-field number gutter (`<left> <right>`, rjust by the digit
/// count of the last number on each side); every group is its own block and
/// a `<>` pair is one two-line block; rules between all blocks, leading and
/// trailing rule included.
pub fn interleaved_body(
    groups: &[TableGroup],
    left: &[Vec<String>],
    right: &[Vec<String>],
    trims: bool,
) -> Vec<String> {
    let ncols = column_count(groups, left, 0).max(column_count(groups, right, 1));
    let lw = side_widths(groups, left, 0, ncols, trims);
    let rw = side_widths(groups, right, 1, ncols, trims);
    let ws: Vec<usize> = lw
        .iter()
        .zip(rw.iter())
        .map(|(a, b)| *a.max(b))
        .collect();
    let mut lnum = vec![0usize; left.len()];
    let mut rnum = vec![0usize; right.len()];
    let mut li = 0usize;
    let mut ri = 0usize;
    for g in groups {
        if let Some(i) = g.left {
            li += 1;
            lnum[i] = li;
        }
        if let Some(j) = g.right {
            ri += 1;
            rnum[j] = ri;
        }
    }
    let lw_ = li.to_string().len();
    let rw_ = ri.to_string().len();
    let header = rstrip(format!(
        "{} {} {}",
        " ".repeat(lw_),
        " ".repeat(rw_),
        render_header(&ws, true)
    ));
    let row = |l: Option<usize>, r: Option<usize>| -> String {
        // Measured (m62b W3-2digit): each number is RIGHT-justified in its
        // own field, whose width is the digit count of the LAST number on
        // that side -- ` 1  1` with 12 left rows, not `1 1`.
        let a = match l {
            Some(i) => pad(&lnum[i].to_string(), lw_, true),
            None => " ".repeat(lw_),
        };
        let b = match r {
            Some(j) => pad(&rnum[j].to_string(), rw_, true),
            None => " ".repeat(rw_),
        };
        let (rows, idx) = match (l, r) {
            (Some(i), _) => (left, Some(i)),
            (None, Some(j)) => (right, Some(j)),
            (None, None) => (left, None),
        };
        let cells = render_cells(rows, idx, &ws, false, trims);
        rstrip(format!("{a} {b} {cells}"))
    };
    let mut lines: Vec<String> = Vec::new();
    for g in groups {
        if g.status == RowStatus::Changed {
            lines.push(row(g.left, None));
            lines.push(row(None, g.right));
        } else {
            lines.push(row(g.left, g.right));
        }
        lines.push(String::new()); // block separator placeholder
    }
    let width = std::iter::once(header.chars().count())
        .chain(lines.iter().filter(|l| !l.is_empty()).map(|l| l.chars().count()))
        .max()
        .unwrap_or(0);
    let rule = "-".repeat(width);
    let mut out = vec![header, rule.clone()];
    for l in lines {
        out.push(if l.is_empty() { rule.clone() } else { l });
    }
    out
}

/// `summary` body rows: the measured four count lines, in order, zeros
/// omitted (G1/G2/G3/G4/E7/F3). Labels are the reference install's English
/// wording corroborated by runs/m62-reflabels-*.
pub fn summary_body(groups: &[TableGroup]) -> Vec<String> {
    // Measured order (m66b O4-all, runs/m66b-summaryorder-*: the first
    // fixture carrying all four categories at once; corroborated by
    // verify/table/t-summary-mixed with three): SAME, then the LEFT orphan,
    // then the RIGHT orphan, then the difference rows. The §4.6 note drafted
    // before any multi-category cell existed and listed diff second — the
    // table golden gate caught it on its first run.
    let mut counts = [(0u64, 0u64), (0, 0), (0, 0), (0, 0)];
    for g in groups {
        match g.status {
            RowStatus::Same => counts[0].0 += 1,
            RowStatus::LeftOrphan => counts[1].0 += 1,
            RowStatus::RightOrphan => counts[2].0 += 1,
            RowStatus::Changed => counts[3].0 += 1,
        }
    }
    let labels = [
        "same row(s)",
        "important left orphan row(s)",
        "important right orphan row(s)",
        "important difference row(s)",
    ];
    counts
        .iter()
        .zip(labels)
        .filter(|(c, _)| c.0 > 0)
        .map(|(c, l)| format!("{} {}", c.0, l))
        .collect()
}

/// The complete table report: frame + body, CRLF, no BOM (measured: table
/// reports carry no BOM; each file path sits on its OWN line — no
/// HEADER_GAP join; the `Produced:` stamp uses the same slash date as the
/// text channel (frame census of 2026-10-18: 114/114 archive reports, both
/// installs); and a `title:` REPLACES the first frame line entirely
/// (measured X4 in runs/m63-clisurface-*: the report begins with `MyTitle`)
/// — all against the installed reports).
pub fn render_report(
    layout: TableLayout,
    left_text: &str,
    right_text: &str,
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
    title: Option<&str>,
) -> Result<String, TableError> {
    let format = detect_format(left_text, right_text, left_path, right_path);
    let left = format.split(left_text);
    let right = format.split(right_text);
    let trims = format.trims();
    let groups = align_rows(&left, &right, trims)?;
    let body = match layout {
        TableLayout::SideBySide => side_by_side_body(&groups, &left, &right, trims),
        TableLayout::Interleaved => interleaved_body(&groups, &left, &right, trims),
        TableLayout::Summary => summary_body(&groups),
    };
    let mut lines: Vec<String> = vec![
        title.unwrap_or("Table Compare").to_string(),
        // Slash date, same as the text channel. Measured: every archived table
        // frame (114 reports across the Chinese and English installs) shows
        // `Produced: yyyy/mm/dd h:nn:ss`; the earlier dash claim was a misread
        // caught by the frame census of 2026-10-18 (docs/13 §6 correction).
        format!("Produced: {stamp}"),
        String::new(),
    ];
    if layout != TableLayout::Summary {
        lines.push("Mode:  All".to_string());
    }
    lines.push(format!("Left file: {left_path}"));
    lines.push(format!("Right file: {right_path}"));
    lines.extend(body);
    Ok(lines.join(CRLF) + CRLF)
}

// ================================================================ tests

#[cfg(test)]
mod tests {
    use super::*;

    fn rows(t: &str) -> Vec<Vec<String>> {
        split_records(t)
    }

    // -- parsing (docs/13 §4.1: quoted newline stays ONE row, T21) --------

    #[test]
    fn quoted_cell_keeps_embedded_newline_in_one_row() {
        let r = rows("k,\"x\ny\",2\nz,3,4\n");
        assert_eq!(r.len(), 2);
        assert_eq!(r[0], vec!["k", "x\ny", "2"]);
        assert_eq!(r[1], vec!["z", "3", "4"]);
    }

    #[test]
    fn quoted_commas_are_one_cell() {
        // E5 / T20
        let r = rows("a,\"b;c\",d\n");
        assert_eq!(r, vec![vec!["a", "b;c", "d"]]);
    }

    #[test]
    fn fixed_comma_keeps_tab_semicolon_pipe_inside_cells() {
        // batch-5 D2/D3/D4/D12: .csv never splits on anything but comma
        assert_eq!(rows("a\tb\n"), vec![vec!["a\tb"]]);
        assert_eq!(rows("a;b\n"), vec![vec!["a;b"]]);
        assert_eq!(rows("a|b\n"), vec![vec!["a|b"]]);
    }

    // -- auto-detect (docs/13 §7, batch-7 m65) ------------------------------

    #[test]
    fn csv_extension_pins_comma_and_skips_detection() {
        // CS1: space content on .csv stays ONE cell; D12: semicolon too.
        assert_eq!(
            detect_format("a b\n", "a X\n", "L.csv", "R.csv"),
            TableFormat::Delimited(',')
        );
        assert_eq!(
            detect_format("a;b\n", "a;b\n", "D:\\x\\L.CSV", "R.csv"),
            TableFormat::Delimited(',')
        );
    }

    #[test]
    fn priority_chain_is_comma_tab_semicolon_pipe() {
        // m65 pairwise: comma beats all (G-pc/G-sc/G-tc/G-wc); tab beats
        // semi/pipe (G-st/G-pt); semi beats pipe (G-ps); pipe last.
        assert_eq!(detect_format("a,b|c\n", "a,b|X\n", "L.txt", "R.txt"),
                   TableFormat::Delimited(','));
        assert_eq!(detect_format("a\tb;c\n", "a\tb;X\n", "L.txt", "R.txt"),
                   TableFormat::Delimited('\t'));
        assert_eq!(detect_format("a;b|c\n", "a;b|X\n", "L.txt", "R.txt"),
                   TableFormat::Delimited(';'));
        assert_eq!(detect_format("a|b\n", "a|X\n", "L.txt", "R.txt"),
                   TableFormat::Delimited('|'));
    }

    #[test]
    fn detection_is_joint_over_both_sides() {
        // PF1/PF2: a delimiter present only in ONE file decides BOTH sides.
        assert_eq!(detect_format("a b\n", "c,d\n", "L.txt", "R.txt"),
                   TableFormat::Delimited(','));
        assert_eq!(detect_format("a,b\n", "c d\n", "L.txt", "R.txt"),
                   TableFormat::Delimited(','));
    }

    #[test]
    fn qualifier_shields_a_delimiter_from_detection() {
        // Q1: a comma living only inside a quoted cell is not a candidate;
        // with no other candidate the format falls back to rawline.
        assert_eq!(detect_format("\"a,b\" c\n", "\"a,b\" X\n", "L.txt", "R.txt"),
                   TableFormat::RawLine);
        // S1: no candidate at all -> rawline, one cell per line.
        assert_eq!(detect_format("hello\nworld\n", "hello\nwarld\n", "L.txt", "R.txt"),
                   TableFormat::RawLine);
    }

    #[test]
    fn rawline_cells_keep_interior_and_trailing_whitespace() {
        // W1/SP5: verbatim except the leading run (SP10 measured ' ab' -> 'ab').
        assert_eq!(split_lines_verbatim("a  b\nc d \n"),
                   vec![vec!["a  b".to_string()], vec!["c d ".to_string()]]);
        assert_eq!(split_lines_verbatim(" ab\ncd\n"),
                   vec![vec!["ab".to_string()], vec!["cd".to_string()]]);
        // m64 E1: the empty final segment after the last newline drops.
        assert_eq!(split_lines_verbatim("a\nb\n"), vec![vec!["a".to_string()], vec!["b".to_string()]]);
        assert_eq!(split_lines_verbatim("a\nb\n\n"),
                   vec![vec!["a".to_string()], vec!["b".to_string()], vec!["".to_string()]]);
    }

    #[test]
    fn rawline_row_equality_is_verbatim_after_leading_trim() {
        // m65b SP9: `c d ` vs `c d` is a difference (trailing space is data).
        let l = split_lines_verbatim("a b\nc d \n");
        let r = split_lines_verbatim("a b\nc d\n");
        let g = align_rows(&l, &r, false).unwrap();
        assert_eq!(
            g.iter().map(|x| x.status).collect::<Vec<_>>(),
            vec![RowStatus::Same, RowStatus::Changed]
        );
    }

    // -- alignment (docs/13 §4.2/§4.3) -------------------------------------

    #[test]
    fn gap_zip_pairs_positionally_not_four_orphans() {
        // P1-2x2: two fully different rows still pair to two `<>`
        let g = align_rows(&rows("aaa,1\nzz,9\n"), &rows("bbb,2\nqq,8\n"), true).unwrap();
        assert_eq!(
            g.iter().map(|x| x.status).collect::<Vec<_>>(),
            vec![RowStatus::Changed; 2]
        );
    }

    #[test]
    fn swap_tie_direction_pins_the_earlier_right_match() {
        // T12-swap measured: `x +-` / `y =` / `-+ x` (the LEFT row is
        // orphaned first; the shared match anchors at the earlier right row).
        let g = align_rows(&rows("x,1\ny,2\n"), &rows("y,2\nx,1\n"), true).unwrap();
        assert_eq!(
            g.iter()
                .map(|x| (x.left, x.right, x.status))
                .collect::<Vec<_>>(),
            vec![
                (Some(0), None, RowStatus::LeftOrphan),
                (Some(1), Some(0), RowStatus::Same),
                (None, Some(1), RowStatus::RightOrphan),
            ]
        );
    }

    #[test]
    fn swap_tie_direction_k4_case() {
        // T13-cont measured: k1=,k2=,k3+-,k4=,-+k3 -- same direction rule.
        let g = align_rows(
            &rows("k1,a\nk2,b\nk3,c\nk4,d\n"),
            &rows("k1,a\nk2,b\nk4,d\nk3,c\n"),
            true,
        )
        .unwrap();
        let sig: Vec<_> = g
            .iter()
            .map(|x| (x.left, x.right, format!("{:?}", x.status)))
            .collect();
        assert_eq!(
            sig,
            vec![
                (Some(0), Some(0), "Same".to_string()),
                (Some(1), Some(1), "Same".to_string()),
                (Some(2), None, "LeftOrphan".to_string()),
                (Some(3), Some(2), "Same".to_string()),
                (None, Some(3), "RightOrphan".to_string()),
            ]
        );
    }

    #[test]
    fn duplicates_consume_positionally() {
        // T14-dup: three identical vs two -> first two `=`, third `+-`.
        let g = align_rows(&rows("k,v\nr,1\nr,1\nr,1\nz,9\n"), &rows("k,v\nr,1\nr,1\nz,9\n"), true).unwrap();
        assert_eq!(
            g.iter().map(|x| x.status).collect::<Vec<_>>(),
            vec![
                RowStatus::Same,
                RowStatus::Same,
                RowStatus::Same,
                RowStatus::LeftOrphan,
                RowStatus::Same,
            ]
        );
    }

    #[test]
    fn row_equality_trims_cells_and_keeps_interior_whitespace() {
        // P3: quoted decode equals raw; P4: `a  b` != `a b`; trailing space
        // drops out.
        let g = align_rows(&rows("k,\"a b\",1\n"), &rows("k,a b,1\n"), true).unwrap();
        assert_eq!(g[0].status, RowStatus::Same);
        let g = align_rows(&rows("k,a  b,1\nn,1 \n"), &rows("k,a b,1\nn,1\n"), true).unwrap();
        assert_eq!(
            g.iter().map(|x| x.status).collect::<Vec<_>>(),
            vec![RowStatus::Changed, RowStatus::Same]
        );
    }

    #[test]
    fn blank_row_participates_as_row() {
        // F4-blank: h,1 / <blank> / b,2 vs h,1 / <blank> / b,9
        // -> =, = (the blank pair), <>
        let g = align_rows(&rows("h,1\n\nb,2\n"), &rows("h,1\n\nb,9\n"), true).unwrap();
        assert_eq!(
            g.iter().map(|x| x.status).collect::<Vec<_>>(),
            vec![RowStatus::Same, RowStatus::Same, RowStatus::Changed]
        );
    }

    // -- side-by-side bodies (transcribed from the Oracle archives) --------

    fn sbs(left: &str, right: &str) -> Vec<String> {
        side_by_side_body(&align_rows(&rows(left), &rows(right), true).unwrap(), &rows(left), &rows(right), true)
    }

    #[test]
    fn sbs_insert_orphan_blank_field_and_widths() {
        // T10-ins measured body (dash 12 = widest row).
        assert_eq!(
            sbs("a,1\nb,2\nd,3\n", "a,1\nb,2\nc,2.5\nd,3\n"),
            vec![
                "A B    A B",
                "------------",
                "a 1 =  a   1",
                "b 2 =  b   2",
                "    -+ c 2.5",
                "d 3 =  d   3",
                "------------",
            ]
        );
    }

    #[test]
    fn sbs_numeric_right_justify_and_widest_row() {
        // T15-close measured (dash 18, header 'A  B       A  B').
        assert_eq!(
            sbs("id,1000\n", "id,1001\n"),
            vec![
                "A  B       A  B",
                "------------------",
                "id 1000 <> id 1001",
                "------------------",
            ]
        );
    }

    #[test]
    fn sbs_ragged_column_count_is_global_with_empty_cells() {
        // T18-cols: left renders the right-only C column as an empty cell
        // at width 1; the row is only rstripped ONCE at the line end.
        assert_eq!(
            sbs("a,1\n", "a,1,x\n"),
            vec![
                "A B C    A B C",
                "--------------",
                "a 1   <> a 1 x",
                "--------------",
            ]
        );
    }

    #[test]
    fn sbs_all_same_header_uses_three_wide_blank_field() {
        // P3-raw: all-same single row -> field widths 3 (header blank too).
        assert_eq!(
            sbs("k,\"a b\",1\n", "k,a b,1\n"),
            vec![
                "A B   C   A B   C",
                "-----------------",
                "k a b 1 = k a b 1",
                "-----------------",
            ]
        );
    }

    #[test]
    fn sbs_blank_row_renders_padding_marker() {
        // F4-blank measured: the blank pair is '    =' (4 spaces + '=').
        assert_eq!(
            sbs("h,1\n\nb,2\n", "h,1\n\nb,9\n"),
            vec![
                "A B    A B",
                "----------",
                "h 1 =  h 1",
                "    =",
                "b 2 <> b 9",
                "----------",
            ]
        );
    }

    #[test]
    fn sbs_empty_cell_inside_row_and_orphan_rstrip() {
        // F1-empty measured.
        assert_eq!(
            sbs("a,,c\nx,y\n", "a,b,c\nx,y\n"),
            vec![
                "A B C    A B C",
                "--------------",
                "a   c <> a b c",
                "x y   =  x y",
                "--------------",
            ]
        );
    }

    #[test]
    fn sbs_nul_display_for_quoted_newline_cell() {
        // T21-nl measured (raw bytes show 0x00 in place of the newline).
        assert_eq!(
            sbs("k,\"x\ny\",2\nz,3,4\n", "k,\"x\ny\",2\nz,3,5\n"),
            vec![
                "A B   C    A B   C",
                "------------------",
                "k x\u{0}y 2 =  k x\u{0}y 2",
                "z   3 4 <> z   3 5",
                "------------------",
            ]
        );
    }

    // -- interleaved bodies ------------------------------------------------

    fn ilv(left: &str, right: &str) -> Vec<String> {
        interleaved_body(&align_rows(&rows(left), &rows(right), true).unwrap(), &rows(left), &rows(right), true)
    }

    #[test]
    fn interleaved_shows_both_numbers_on_equal_rows_one_per_side_else() {
        // G5-mixed measured body (reference install, English frame stripped):
        // every group is its own block; '=' carries both numbers; text is
        // ljust in the interleaved columns too (q  1 keeps width 2 column).
        assert_eq!(
            ilv("h1,h2
q,1
r,2
s,3
", "h1,h2
r,2
q,9
s,3
t,4
"),
            vec![
                "    A  B",
                "---------",
                "1 1 h1 h2",
                "---------",
                "2   q  1",
                "---------",
                "3 2 r  2",
                "---------",
                "  3 q  9",
                "---------",
                "4 4 s  3",
                "---------",
                "  5 t  4",
                "---------",
            ]
        );
    }

    #[test]
    fn interleaved_pair_shares_one_block_two_lines() {
        // P5-anchor measured: the `<>` pair is ONE block (left line, right
        // line) between rules.
        assert_eq!(
            ilv("a,1
b,2
c,3
", "a,1
x,9
c,3
"),
            vec![
                "    A B",
                "-------",
                "1 1 a 1",
                "-------",
                "2   b 2",
                "  2 x 9",
                "-------",
                "3 3 c 3",
                "-------",
            ]
        );
    }

    #[test]
    fn interleaved_number_fields_rjust_to_digit_width() {
        // m62b W3-2digit (found by the PRODUCT replay, missed by the 56-case
        // simulator set): with 12 left rows the number fields are two wide
        // and right-justified -- ' 1  1 a1  1', and the trailing right
        // orphan shows '   13 x   13'.
        let l = (1..=12)
            .map(|i| format!("a{i},{i}"))
            .collect::<Vec<_>>()
            .join("\n")
            + "\n";
        let r = l.clone() + "x,13\n";
        let body = ilv(&l, &r);
        assert_eq!(body[0], "      A   B");
        assert_eq!(body[2], " 1  1 a1  1");
        assert_eq!(body[4], " 2  2 a2  2");
        assert_eq!(body[20], "10 10 a10 10");
        assert_eq!(body[24], "12 12 a12 12");
        assert_eq!(body[26], "   13 x   13");
    }

    // -- summary body (English reference labels, m62-reflabels) ------------

    fn summ(left: &str, right: &str) -> Vec<String> {
        summary_body(&align_rows(&rows(left), &rows(right), true).unwrap())
    }

    #[test]
    fn summary_counts_in_measured_order_zeros_omitted() {
        assert_eq!(summ("h,1
a,2
", "h,1
a,2
"), vec!["2 same row(s)"]);
        assert_eq!(
            summ("h,1
a,2
", "h,1
a,9
"),
            vec!["1 same row(s)", "1 important difference row(s)"]
        );
        assert_eq!(
            summ("h,1
a,2
b,3
", "h,1
a,2
"),
            vec!["2 same row(s)", "1 important left orphan row(s)"]
        );
        assert_eq!(
            summ("h,1
a,2
", "h,1
a,2
q,9
"),
            vec!["2 same row(s)", "1 important right orphan row(s)"]
        );
        // O4-all (runs/m66b-summaryorder-*): all four categories at once pin
        // the full order -- same, LEFT orphan, RIGHT orphan, then difference.
        assert_eq!(
            summ("a,1
m,2
c,3
n,4
", "a,1
c,3
p,4
q,5
"),
            vec![
                "2 same row(s)",
                "1 important left orphan row(s)",
                "1 important right orphan row(s)",
                "1 important difference row(s)"
            ]
        );
    }

    // -- frame --------------------------------------------------------------

    #[test]
    fn column_letters_continue_aa_ab_ac() {
        // Measured (m64 C2-29narrow, runs/m64c2-letters-*): after Z the letters
        // are AA, AB, AC (Excel-style), and a 2-letter label raises that
        // column's minimum width to 2 even when every cell is 1 char wide.
        assert_eq!(column_letter(25), "Z");
        assert_eq!(column_letter(26), "AA");
        assert_eq!(column_letter(27), "AB");
        assert_eq!(column_letter(28), "AC");
    }

    #[test]
    fn header_28col_wide_and_narrow_shapes() {
        // C1 (runs/m64-residual-*): cells c1..c9 are 2 wide, c10..c28 are 3,
        // so the letters A..I sit in width-2 fields, J..Z, AA, AB in width-3.
        // Transcribed from the Oracle header line (left block, un-rstripped):
        let ws = std::iter::repeat(2).take(9)
            .chain(std::iter::repeat(3).take(19))
            .collect::<Vec<_>>();
        let h = render_header(&ws, true);
        assert_eq!(
            h,
            "A  B  C  D  E  F  G  H  I  J   K   L   M   N   O   P   Q   R   \
             S   T   U   V   W   X   Y   Z   AA  AB"
        );
        // C2 (runs/m64c2-letters-*): every cell is one char, so the letters
        // themselves set the floor (1 for A..Z, 2 for AA+).
        let ws2 = (0..29).map(|c| column_letter(c).chars().count()).collect::<Vec<_>>();
        let h2 = render_header(&ws2, true);
        assert_eq!(
            h2,
            "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AA AB AC"
        );
    }

    #[test]
    fn frame_is_crlf_no_gap_and_slashed_stamp() {
        // Slash date measured: every archived table frame across both installs
        // writes `Produced: 2026-10-18 ...` (frame census 2026-10-18; the
        // earlier dash claim was a misread -- see render_report's note).
        let stamp = Stamp::from_parts(2026, 10, 18, 0, 36, 32);
        let text = render_report(
            TableLayout::Summary,
            "a,1\n",
            "a,1\n",
            "L.csv",
            "R.csv",
            &stamp,
            None,
        )
        .unwrap();
        let want =
            "Table Compare\r\nProduced: 2026/10/18 0:36:32\r\n\r\nLeft file: L.csv\r\nRight file: R.csv\r\n";
        assert!(text.starts_with(want), "got {text:?}");
        assert!(!text.contains("Mode:")); // summary has no Mode line
    }

    #[test]
    fn title_replaces_the_first_frame_line() {
        // Measured X4 (runs/m63-clisurface-*): `title:"MyTitle"` on a summary
        // report starts the file with `MyTitle`, no `Table Compare` line.
        let stamp = Stamp::from_parts(2026, 10, 18, 2, 19, 26);
        let text = render_report(
            TableLayout::Summary,
            "k,1\n",
            "k,2\n",
            "L.csv",
            "R.csv",
            &stamp,
            Some("MyTitle"),
        )
        .unwrap();
        assert!(text.starts_with("MyTitle\r\n"), "got {text:?}");
        assert!(!text.contains("Table Compare"));
    }
}

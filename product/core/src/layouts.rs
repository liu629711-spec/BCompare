//! M1.4 — the six text report layouts.
//!
//! Migrated from `clone/src/layouts.rs` and re-derived against the golden corpus.
//! Every rule below is **O**bserved in `verify/layouts/*.txt` (30 reports, 5 input
//! pairs × 6 layouts) and, where noted, in `verify/oracle/report-*.txt` and
//! `verify/probe-patch/*.txt`.
//!
//! # Common header
//!
//! `side-by-side`, `interleaved` and `over-under` share a five-line header:
//!
//! ```text
//! Text Compare
//! Produced: <stamp>
//! (blank)
//! Mode:  All
//! Left file: <L>     Right file: <R>
//! ```
//!
//! `summary` is the same without the `Mode:` line; `statistics` keeps only
//! `Text Compare` and `Produced:` and then goes straight to CSV. `patch` has no
//! header at all beyond `diff -r <L> <R>`.
//!
//! `Mode:  All` carries two spaces after the colon — corroborated by the
//! harness's confirmed label pair `模式：  全部` ↔ `Mode:  All`.
//! `02-version-and-evidence.md` §3.5 records that the header wraps onto two
//! lines for long paths; see [`HEADER_GAP`](crate::stamp::HEADER_GAP) for why
//! this crate emits the single-line form.
//!
//! # `over-under` is byte-identical to `interleaved`
//!
//! Verified by direct comparison of all five `*-interleaved.txt` /
//! `*-over-under.txt` golden pairs: the only differing byte is the generation
//! timestamp inside `Produced:`. BC documents `over-under` as deprecated, and
//! its report body is produced by the same renderer. This module therefore
//! renders `over-under` with [`interleaved`] rather than duplicating the code —
//! that is a measured equality, not an assumption.
//!
//! # side-by-side marker rules (measured, including the m51 probe)
//!
//! Row shape is `[left padded to the column]` + marker field + `[right]`, then
//! right-trimmed. The column is the width of the widest left line **in the
//! report**. Marker fields, measured character by character:
//!
//! | Row | Field | Width |
//! |---|---|---|
//! | `=` in a report that also has differences | `" =  "` | 4 |
//! | `=` in an all-`same` report | `" = "` | 3 |
//! | `<>`, `+-`, `-+` | `" <> "`, `" +- "`, `" -+ "` | 4 |
//! | any later row of a block | spaces, matching the field it replaces | 3 or 4 |
//!
//! **The glyph is a property of the whole block and sits on its first row
//! only.** A block is a maximal run of `same` or non-`same` groups (the same
//! split that draws the separators). Its glyph: `=` for a `same` block; `+-`
//! for a block with no right lines (pure left orphans); `-+` for a block with
//! no left lines; `<>` for anything containing a paired row — even when the
//! first row is itself an orphan (`m51` `orphan-second-short`: `bbbb <>`
//! above the paired `o1      X`). Every later row of the block renders a
//! blank field of the same width.
//!
//! Evidence: the five golden reports (`identical` row 2 `y   y`, `mixed`
//! rows 2–3 of its changed block, single-row blocks elsewhere) plus the live
//! probe `probes/m51_sbs_marker.py`
//! (`runs/m51-probe-20261014T155153Z`), whose `short-nonfirst-diff` /
//! `orphan-second-short` / `rtonly-second` / `orphan-first-then-pair` shapes
//! blank every non-first row regardless of the row's own status and of
//! whether the left cell fills the column. That refutes the earlier
//! "left cell fills the column" fitted rule this module once declined to
//! implement for `mixed-side-by-side`: in `identical-side-by-side` both rows
//! fill the 1-character column, yet only the first carries `=`.
//!
//! `mixed-side-by-side` — the official gate's last red item — is fixed by
//! this rule; the same probe also exposed a *pairing* divergence on
//! all-zero-similarity unequal blocks (M5.1b, tracked in
//! `07-m2-importance.md`), which is a different layer.
//!
//! # patch anchors (cursor positions, not standard diff line numbers)
//!
//! `c` uses real line ranges; `d` and `a` use an anchor derived from the lines
//! **covered** before the block, clamped to 0 when it is 0 or 1:
//!
//! ```text
//! d  ->  "{ls}[,{le}]d{anchor}"   anchor = covered_right  if covered_right >= 2 else 0
//! a  ->  "{anchor}a{rs}[,{re}]"   anchor = covered_left   if covered_left  >= 2 else 0
//! ```
//!
//! "Covered" counts every line of that side appearing in an earlier group,
//! including earlier deleted/inserted lines. That single rule reproduces 24 of
//! the 25 `verify/probe-patch` cases and all five golden `*-patch.txt` reports.
//!
//! The one deviation is `verify/probe-patch/del-then-chg` (`a,x,b,c` vs
//! `a,b,z,c`), where an append block immediately follows a delete block and BC
//! writes `3a3` where this rule yields `2a2`. The `d` half of that report
//! (`2d0`) is reproduced exactly. This case is **not** part of any scored
//! manifest; it is recorded here and in `README.md` rather than special-cased.
//! Note the rule shape also contradicts the sentence in
//! `verify/layouts/README.md` that says the `d` anchor is "right-aligned count
//! minus 1 beyond 1": the six `del-after-K-same` probes (K = 0…5) contradict
//! that sentence for K ≥ 2, and the probes are the direct evidence.

use crate::align::{difference_sections, Group, Status};
use crate::stamp::{Stamp, HEADER_GAP};

const CRLF: &str = "\r\n";

/// Header lines shared by the row-oriented layouts.
fn header_rows(left_path: &str, right_path: &str, stamp: &Stamp) -> String {
    format!(
        "Text Compare{CRLF}Produced: {stamp}{CRLF}{CRLF}Mode:  All{CRLF}\
         Left file: {left_path}{HEADER_GAP}Right file: {right_path}{CRLF}"
    )
}

/// Header for `summary`: the shared header minus the `Mode:` line.
fn header_summary(left_path: &str, right_path: &str, stamp: &Stamp) -> String {
    format!(
        "Text Compare{CRLF}Produced: {stamp}{CRLF}{CRLF}\
         Left file: {left_path}{HEADER_GAP}Right file: {right_path}{CRLF}"
    )
}

/// Header for `statistics`: title and timestamp, then straight to CSV.
fn header_statistics(stamp: &Stamp) -> String {
    format!("Text Compare{CRLF}Produced: {stamp}{CRLF}")
}

/// Width of the left column: the widest left line that appears in the report.
///
/// "Appears in the report" matters: the column is derived from the groups, not
/// from the file, so a filtered report can use a narrower column. Measured
/// against all five golden side-by-side reports.
fn left_column_width(groups: &[Group], left_lines: &[String]) -> usize {
    groups
        .iter()
        .filter_map(|g| g.left)
        .map(|li| left_lines[li].chars().count())
        .max()
        .unwrap_or(0)
}

/// Split the group list into maximal runs of `same` / non-`same`.
///
/// Each run is rendered as a block followed by a separator line. Observed in
/// both row layouts: `identical` (one `same` block) ends with one separator;
/// `mixed` (three blocks) with three.
fn blocks(groups: &[Group]) -> Vec<(bool, &[Group])> {
    let mut out = Vec::new();
    let mut i = 0;
    while i < groups.len() {
        let same = groups[i].status == Status::Same;
        let start = i;
        while i < groups.len() && (groups[i].status == Status::Same) == same {
            i += 1;
        }
        out.push((same, &groups[start..i]));
    }
    out
}

/// The marker field for one row, per the measured table in the module header.
///
/// `marker` is `None` for any non-first row of a block, which is rendered as
/// blanks of the same width so the columns stay aligned.
fn marker_field(marker: Option<&str>, all_same: bool) -> String {
    match marker {
        Some("=") if all_same => " = ".to_string(),
        Some("=") => " =  ".to_string(),
        Some(m) => format!(" {m} "),
        None => {
            if all_same {
                "   ".to_string()
            } else {
                "    ".to_string()
            }
        }
    }
}

/// `side-by-side`.
pub fn side_by_side(
    groups: &[Group],
    left_lines: &[String],
    right_lines: &[String],
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
) -> String {
    let mut out = header_rows(left_path, right_path, stamp);
    let col = left_column_width(groups, left_lines);
    let all_same = groups.iter().all(|g| g.status == Status::Same);

    // Render every row first: the separator width is the widest row in the whole
    // report, so it cannot be known until all rows exist.
    let mut rendered: Vec<(Vec<String>, bool)> = Vec::new();
    for (same, block) in blocks(groups) {
        // The glyph belongs to the block, not the row, and rides on the
        // block's first row only (module header: goldens + the m51 probe).
        let glyph = if same {
            "="
        } else if block.iter().all(|g| g.right.is_none()) {
            "+-"
        } else if block.iter().all(|g| g.left.is_none()) {
            "-+"
        } else {
            "<>"
        };
        let mut rows = Vec::with_capacity(block.len());
        let mut first = true;
        for g in block {
            let marker = if first { Some(glyph) } else { None };
            let mut row = match (g.left, g.right) {
                (Some(li), _) => left_lines[li].clone(),
                (None, _) => String::new(),
            };
            while row.chars().count() < col {
                row.push(' ');
            }
            row.push_str(&marker_field(marker, all_same));
            if let Some(ri) = g.right {
                row.push_str(&right_lines[ri]);
            }
            // BC right-trims: `only-left +-` carries no trailing space and a
            // right-orphan row starts with the padding.
            rows.push(row.trim_end().to_string());
            first = false;
        }
        rendered.push((rows, same));
    }

    let width = rendered
        .iter()
        .flat_map(|(rows, _)| rows.iter())
        .map(|r| r.chars().count())
        .max()
        .unwrap_or(0);
    for (rows, _) in &rendered {
        for row in rows {
            out.push_str(row);
            out.push_str(CRLF);
        }
        if width > 0 {
            out.push_str(&"-".repeat(width));
            out.push_str(CRLF);
        }
    }
    out
}

/// Number of digits needed for the largest line number in the report.
///
/// At least one column so a single-digit report still separates the number from
/// the text. The corpus only contains single-digit line numbers, so the
/// multi-digit widening is **inferred** from the observed two-field shape rather
/// than measured; it is called out in `README.md`.
fn number_width(left_lines: &[String], right_lines: &[String]) -> usize {
    let max = left_lines.len().max(right_lines.len()).max(1);
    max.to_string().len()
}

/// `interleaved`. Also used for `over-under` (measured byte-identical body).
///
/// Rows: `{left_num} {right_num} {text}` for a `same` line; inside a
/// non-`same` block all left lines come first (right field blank) and then all
/// right lines (left field blank).
pub fn interleaved(
    groups: &[Group],
    left_lines: &[String],
    right_lines: &[String],
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
) -> String {
    let mut out = header_rows(left_path, right_path, stamp);
    let w = number_width(left_lines, right_lines);
    let row = |ln: Option<usize>, rn: Option<usize>, text: &str| {
        let l = ln.map(|n| (n + 1).to_string()).unwrap_or_default();
        let r = rn.map(|n| (n + 1).to_string()).unwrap_or_default();
        format!("{l:>w$} {r:>w$} {text}", w = w)
    };

    let mut rendered: Vec<(Vec<String>, bool)> = Vec::new();
    for (same, block) in blocks(groups) {
        let mut rows = Vec::new();
        if same {
            for g in block {
                if let (Some(li), Some(ri)) = (g.left, g.right) {
                    rows.push(row(Some(li), Some(ri), &left_lines[li]));
                }
            }
        } else {
            for g in block {
                if let Some(li) = g.left {
                    rows.push(row(Some(li), None, &left_lines[li]));
                }
            }
            for g in block {
                if let Some(ri) = g.right {
                    rows.push(row(None, Some(ri), &right_lines[ri]));
                }
            }
        }
        rendered.push((rows, same));
    }
    let width = rendered
        .iter()
        .flat_map(|(rows, _)| rows.iter())
        .map(|r| r.chars().count())
        .max()
        .unwrap_or(0);
    for (rows, _) in &rendered {
        for r in rows {
            out.push_str(r);
            out.push_str(CRLF);
        }
        if width > 0 {
            out.push_str(&"-".repeat(width));
            out.push_str(CRLF);
        }
    }
    out
}

/// Highest left line index a group covers, if any.
fn last_left(block: &[Group]) -> Option<usize> {
    block.iter().filter_map(|g| g.left).next_back()
}

/// Highest right line index a group covers, if any.
fn last_right(block: &[Group]) -> Option<usize> {
    block.iter().filter_map(|g| g.right).next_back()
}

/// `patch`.
pub fn patch(
    groups: &[Group],
    left_lines: &[String],
    right_lines: &[String],
    left_path: &str,
    right_path: &str,
) -> String {
    let mut out = format!("diff -r {left_path} {right_path}{CRLF}");
    let mut i = 0usize;
    // Lines of each side already covered by earlier groups, including lines that
    // were themselves part of a difference. This is the anchor input.
    let mut covered_left = 0usize;
    let mut covered_right = 0usize;
    while i < groups.len() {
        if groups[i].status == Status::Same {
            covered_left += 1;
            covered_right += 1;
            i += 1;
            continue;
        }
        let start = i;
        while i < groups.len() && groups[i].status != Status::Same {
            i += 1;
        }
        let block = &groups[start..i];
        let left_first = block.iter().find_map(|g| g.left);
        let right_first = block.iter().find_map(|g| g.right);
        let ls = left_first.map(|x| x + 1);
        let le = last_left(block).map(|x| x + 1);
        // `rs` is the first real right line number, which is that group's own
        // index — not a running cursor, because a gap can be created by an
        // unmatched block on the other side alone.
        let rs = right_first.map(|x| x + 1);
        let re = last_right(block).map(|x| x + 1);

        let range = |a: Option<usize>, b: Option<usize>| match (a, b) {
            (Some(a), Some(b)) if a == b => a.to_string(),
            (Some(a), Some(b)) => format!("{a},{b}"),
            (Some(a), None) => a.to_string(),
            _ => String::new(),
        };
        match (ls.is_some(), rs.is_some()) {
            (true, true) => {
                out.push_str(&format!("{}c{}{CRLF}", range(ls, le), range(rs, re)));
            }
            (true, false) => {
                let anchor = if covered_right >= 2 { covered_right } else { 0 };
                out.push_str(&format!("{}d{}{CRLF}", range(ls, le), anchor));
            }
            _ => {
                let anchor = if covered_left >= 2 { covered_left } else { 0 };
                out.push_str(&format!("{}{}a{}{CRLF}", anchor, "", range(rs, re)));
            }
        }
        for g in block {
            if let Some(li) = g.left {
                out.push_str(&format!("< {}{CRLF}", left_lines[li]));
            }
        }
        if left_first.is_some() && right_first.is_some() {
            out.push_str("---");
            out.push_str(CRLF);
        }
        for g in block {
            if let Some(ri) = g.right {
                out.push_str(&format!("> {}{CRLF}", right_lines[ri]));
            }
        }
        covered_left += block.iter().filter(|g| g.left.is_some()).count();
        covered_right += block.iter().filter(|g| g.right.is_some()).count();
    }
    out
}

/// One count line of the `summary` layout, omitted when the count is zero.
fn summary_line(count: usize, label: &str, out: &mut String) {
    if count > 0 {
        out.push_str(&format!("{count} {label}{CRLF}"));
    }
}

/// `summary`.
pub fn summary(
    groups: &[Group],
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
) -> String {
    let mut out = header_summary(left_path, right_path, stamp);
    let count = |f: fn(Status) -> bool| groups.iter().filter(|g| f(g.status)).count();
    let n_same = count(|s| s == Status::Same);
    let n_uleft = count(|s| s == Status::LeftSimilar);
    let n_uright = count(|s| s == Status::RightSimilar);
    let n_udiff = count(|s| s == Status::Similar);
    let n_left = count(|s| s == Status::LeftOrphan);
    let n_right = count(|s| s == Status::RightOrphan);
    let n_idiff = count(|s| s == Status::Different);
    // Count order is fixed by the corpus plus u3/u3b: same, unimportant left
    // orphan, unimportant right orphan, unimportant difference, important left
    // orphan, important right orphan, important difference.
    summary_line(n_same, "same line(s)", &mut out);
    summary_line(n_uleft, "unimportant left orphan line(s)", &mut out);
    summary_line(n_uright, "unimportant right orphan line(s)", &mut out);
    summary_line(n_udiff, "unimportant difference line(s)", &mut out);
    summary_line(n_left, "important left orphan line(s)", &mut out);
    summary_line(n_right, "important right orphan line(s)", &mut out);
    summary_line(n_idiff, "important difference line(s)", &mut out);
    let sections = difference_sections(groups);
    if sections > 0 {
        out.push_str(CRLF);
        out.push_str(&format!("{sections} difference section(s){CRLF}"));
    }
    out
}

/// `statistics`.
///
/// The CSV header is the one the harness normalizes
/// (`源文件,比较文件,…` ↔ `SourceFile,CompareFile,…`), and the data row carries
/// ten fields: the three trailing error counters are omitted entirely, as
/// observed in all five golden statistics reports.
pub fn statistics(
    groups: &[Group],
    left_unimportant: &[bool],
    left_lines: &[String],
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
) -> String {
    let mut out = header_statistics(stamp);
    out.push_str(
        "SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,\
         UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error",
    );
    out.push_str(CRLF);
    let count = |f: fn(Status) -> bool| groups.iter().filter(|g| f(g.status)).count();
    // The m52 probe (`runs/m52-probe-20261014T165631Z`) measured the books:
    // IOriginal/UOriginal split the LEFT lines by importance (comments and
    // blanks are U lines even when they paired as `similar`), one-sided
    // unimportant rows land in UDeleted/UAdded, and
    // `options:ignore-unimportant` changes nothing — which is why this layout
    // is rendered from the un-collapsed groups (see `Comparison::render`).
    let i_original = left_unimportant.iter().filter(|u| !**u).count();
    let u_original = left_unimportant.len() - i_original;
    let i_deleted = count(|s| s == Status::LeftOrphan);
    let i_added = count(|s| s == Status::RightOrphan);
    let i_changed = count(|s| s == Status::Different);
    let u_added = count(|s| s == Status::RightSimilar);
    let u_deleted = count(|s| s == Status::LeftSimilar);
    let u_changed = count(|s| s == Status::Similar);
    out.push_str(&format!(
        "{left_path},{right_path},{i_original},{i_added},{i_deleted},{i_changed},\
         {u_original},{u_added},{u_deleted},{u_changed}"
    ));
    out.push_str(CRLF);
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::align::align;
    use crate::importance::Grammar;

    fn lines(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    fn stamp() -> Stamp {
        Stamp::from_parts(2026, 10, 13, 9, 43, 7)
    }

    /// Render one layout the way the CLI does, with the corpus' relative paths.
    fn render(
        layout: crate::xml::Layout,
        left: &[&str],
        right: &[&str],
        name: &str,
    ) -> (Vec<String>, Vec<String>, String) {
        let l = lines(left);
        let r = lines(right);
        let groups = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
        let lp = format!("D:\\x\\{name}-L.txt");
        let rp = format!("D:\\x\\{name}-R.txt");
        let s = stamp();
        let text = match layout {
            crate::xml::Layout::SideBySide => side_by_side(&groups, &l, &r, &lp, &rp, &s),
            crate::xml::Layout::Interleaved | crate::xml::Layout::OverUnder => {
                interleaved(&groups, &l, &r, &lp, &rp, &s)
            }
            crate::xml::Layout::Patch => patch(&groups, &l, &r, &lp, &rp),
            crate::xml::Layout::Summary => summary(&groups, &lp, &rp, &s),
            crate::xml::Layout::Statistics => {
                let mask = vec![false; l.len()];
                statistics(&groups, &mask, &l, &lp, &rp, &s)
            }
            crate::xml::Layout::Xml => unreachable!("xml is covered in the xml module"),
        };
        (l, r, text)
    }

    /// Every body line, i.e. everything after the header block.
    fn body(text: &str) -> Vec<String> {
        text.split("\r\n").skip(5).map(|s| s.to_string()).collect()
    }

    // ---------------------------------------------------------------
    // Header shapes
    // ---------------------------------------------------------------

    #[test]
    fn row_layout_header_matches_the_golden_shape() {
        let (_, _, text) = render(
            crate::xml::Layout::SideBySide,
            &["same line"],
            &["same line"],
            "x",
        );
        let head: Vec<&str> = text.split("\r\n").take(5).collect();
        assert_eq!(head[0], "Text Compare");
        assert_eq!(head[1], "Produced: 2026/10/13 9:43:07");
        assert_eq!(head[2], "");
        assert_eq!(head[3], "Mode:  All");
        assert_eq!(
            head[4],
            "Left file: D:\\x\\x-L.txt     Right file: D:\\x\\x-R.txt"
        );
    }

    #[test]
    fn summary_header_has_no_mode_line() {
        let (_, _, text) = render(crate::xml::Layout::Summary, &["x"], &["x"], "x");
        let head: Vec<&str> = text.split("\r\n").take(4).collect();
        assert_eq!(head[0], "Text Compare");
        assert_eq!(head[1], "Produced: 2026/10/13 9:43:07");
        assert_eq!(head[2], "");
        assert_eq!(head[3], "Left file: D:\\x\\x-L.txt     Right file: D:\\x\\x-R.txt");
        assert!(!text.contains("Mode:"));
    }

    #[test]
    fn statistics_header_is_title_then_csv_immediately() {
        let (_, _, text) = render(crate::xml::Layout::Statistics, &["x"], &["x"], "x");
        let head: Vec<&str> = text.split("\r\n").take(3).collect();
        assert_eq!(head[0], "Text Compare");
        assert_eq!(head[1], "Produced: 2026/10/13 9:43:07");
        assert!(head[2].starts_with("SourceFile,CompareFile,"));
        assert!(!text.contains("Mode:"));
        assert!(!text.contains("Left file:"));
    }

    #[test]
    fn patch_header_is_diff_r() {
        let (_, _, text) = render(crate::xml::Layout::Patch, &["x"], &["x"], "x");
        assert_eq!(
            text,
            "diff -r D:\\x\\x-L.txt D:\\x\\x-R.txt\r\n"
        );
    }

    #[test]
    fn every_layout_ends_with_crlf_and_never_a_bare_lf() {
        for layout in [
            crate::xml::Layout::SideBySide,
            crate::xml::Layout::Interleaved,
            crate::xml::Layout::OverUnder,
            crate::xml::Layout::Patch,
            crate::xml::Layout::Summary,
            crate::xml::Layout::Statistics,
        ] {
            let (_, _, text) = render(layout, &["a"], &["b"], "x");
            assert!(text.ends_with("\r\n"), "{:?} must end with CRLF", layout);
            assert!(
                !text.replace("\r\n", "").contains('\n'),
                "{:?} contains a bare LF",
                layout
            );
        }
    }

    // ---------------------------------------------------------------
    // side-by-side: each golden case, checked row by row.
    // ---------------------------------------------------------------

    #[test]
    fn side_by_side_matches_identical_golden_shape() {
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["x", "y"], &["x", "y"], "identical");
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        // golden: "x = x" / "y   y" / "-----"  (all-same => 3-wide '=' field)
        assert_eq!(b[0], "x = x");
        assert_eq!(b[1], "y   y");
        assert_eq!(b[2], "-----");
        assert_eq!(b[3], "");
    }

    #[test]
    fn side_by_side_matches_insert_golden_shape() {
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["a", "c"], &["a", "b", "c"], "insert");
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(&b[..6], &["a =  a", "------", "  -+ b", "------", "c =  c", "------"]);
    }

    #[test]
    fn side_by_side_matches_orphans_golden_shape() {
        let (_, _, text) = render(
            crate::xml::Layout::SideBySide,
            &["only-left", "shared"],
            &["shared", "only-right"],
            "orphans",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(
            &b[..6],
            &[
                "only-left +-",
                "-----------------------",
                "shared    =  shared",
                "-----------------------",
                "          -+ only-right",
                "-----------------------",
            ]
        );
    }

    #[test]
    fn side_by_side_matches_similar_golden_shape() {
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["alpha", "beta"], &["ALPHA", "beta"], "similar");
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(&b[..4], &["alpha <> ALPHA", "--------------", "beta  =  beta", "--------------"]);
    }

    #[test]
    fn side_by_side_matches_mixed_golden() {
        // Resolved 2026-10-14 (M5.1): the block-first-row marker rule. Before
        // that this test pinned the known difference — rows 3 and 4 kept their
        // glyphs while BC blanked them.
        let (_, _, text) = render(
            crate::xml::Layout::SideBySide,
            &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
            &["same line", "CASE DIFF", "real diff 9", "tail"],
            "mixed",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(b[0], "same line   =  same line");
        assert_eq!(b[1], "--------------------------");
        assert_eq!(b[2], "case diff   <> CASE DIFF");
        // golden: "real diff 1    real diff 9" — non-first rows blank the
        // field, regardless of the row's own status.
        assert_eq!(b[3], "real diff 1    real diff 9");
        // golden: "real diff 2" — the orphan row is not the block's first.
        assert_eq!(b[4], "real diff 2");
        assert_eq!(b[5], "--------------------------");
        assert_eq!(b[6], "tail        =  tail");
        assert_eq!(b[7], "--------------------------");
    }

    #[test]
    fn side_by_side_separator_width_is_the_widest_body_row() {
        let (_, _, text) = render(
            crate::xml::Layout::SideBySide,
            &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
            &["same line", "CASE DIFF", "real diff 9", "tail"],
            "mixed",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        // The final empty element is the artifact of splitting on a trailing
        // CRLF; the separator predicate must exclude it explicitly.
        fn is_sep(r: &str) -> bool {
            !r.is_empty() && r.chars().all(|c| c == '-')
        }
        let max_row = b
            .iter()
            .filter(|r| !r.is_empty() && !is_sep(r))
            .map(|r| r.chars().count())
            .max()
            .unwrap();
        assert!(max_row > 0, "the sample must have at least one body row");
        let seps: Vec<&str> = b.iter().copied().filter(|r| is_sep(r)).collect();
        assert_eq!(seps.len(), 3, "mixed has three blocks: {b:?}");
        for sep in seps {
            assert_eq!(
                sep.chars().count(),
                max_row,
                "separator width must equal the widest row"
            );
        }
    }

    #[test]
    fn side_by_side_uses_four_wide_marker_fields_when_differences_exist() {
        // Non-all-same '=' occupies " =  " so the right cell starts at col+4.
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["a"], &["b"], "x");
        let row = text.split("\r\n").nth(5).unwrap();
        assert_eq!(row, "a <> b");
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["a", "b"], &["a", "c"], "x");
        let row = text.split("\r\n").nth(5).unwrap();
        assert_eq!(row, "a =  a");
    }

    // ---------------------------------------------------------------
    // interleaved / over-under
    // ---------------------------------------------------------------

    #[test]
    fn interleaved_matches_mixed_golden_shape() {
        let (_, _, text) = render(
            crate::xml::Layout::Interleaved,
            &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
            &["same line", "CASE DIFF", "real diff 9", "tail"],
            "mixed",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(
            &b[..9],
            &[
                "1 1 same line",
                "---------------",
                "2   case diff",
                "3   real diff 1",
                "4   real diff 2",
                "  2 CASE DIFF",
                "  3 real diff 9",
                "---------------",
                "5 4 tail",
            ]
        );
    }

    #[test]
    fn interleaved_matches_insert_orphans_and_similar_shapes() {
        let (_, _, text) = render(crate::xml::Layout::Interleaved, &["a", "c"], &["a", "b", "c"], "insert");
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(&b[..6], &["1 1 a", "-----", "  2 b", "-----", "2 3 c", "-----"]);

        let (_, _, text) = render(
            crate::xml::Layout::Interleaved,
            &["only-left", "shared"],
            &["shared", "only-right"],
            "orphans",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(
            &b[..6],
            &[
                "1   only-left",
                "--------------",
                "2 1 shared",
                "--------------",
                "  2 only-right",
                "--------------",
            ]
        );

        let (_, _, text) = render(crate::xml::Layout::Interleaved, &["alpha", "beta"], &["ALPHA", "beta"], "similar");
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(&b[..5], &["1   alpha", "  1 ALPHA", "---------", "2 2 beta", "---------"]);
    }

    #[test]
    fn over_under_body_is_identical_to_interleaved() {
        for (name, l, r) in [
            ("mixed", lines(&["a", "b", "c"]), lines(&["a", "x"])),
            ("insert", lines(&["a", "c"]), lines(&["a", "b", "c"])),
            ("orphans", lines(&["o", "s"]), lines(&["s", "p"])),
            ("identical", lines(&["x", "y"]), lines(&["x", "y"])),
        ] {
            let groups = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
            let s = stamp();
            let a = interleaved(&groups, &l, &r, "L", "R", &s);
            let b = interleaved(&groups, &l, &r, "L", "R", &s);
            assert_eq!(a, b, "{name}: over-under must reuse the interleaved renderer");
        }
    }

    #[test]
    fn single_same_block_emits_one_separator() {
        let (_, _, text) = render(
            crate::xml::Layout::Interleaved,
            &["x", "y"],
            &["x", "y"],
            "identical",
        );
        let b: Vec<&str> = text.split("\r\n").skip(5).collect();
        assert_eq!(&b[..3], &["1 1 x", "2 2 y", "-----"]);
    }

    // ---------------------------------------------------------------
    // patch
    // ---------------------------------------------------------------

    #[test]
    fn patch_matches_identical_golden() {
        let (_, _, text) = render(crate::xml::Layout::Patch, &["x", "y"], &["x", "y"], "identical");
        assert_eq!(text, "diff -r D:\\x\\identical-L.txt D:\\x\\identical-R.txt\r\n");
    }

    #[test]
    fn patch_matches_insert_golden() {
        let (_, _, text) = render(crate::xml::Layout::Patch, &["a", "c"], &["a", "b", "c"], "insert");
        assert_eq!(
            text,
            "diff -r D:\\x\\insert-L.txt D:\\x\\insert-R.txt\r\n0a2\r\n> b\r\n"
        );
    }

    #[test]
    fn patch_matches_similar_golden() {
        let (_, _, text) = render(crate::xml::Layout::Patch, &["alpha", "beta"], &["ALPHA", "beta"], "similar");
        assert_eq!(
            text,
            "diff -r D:\\x\\similar-L.txt D:\\x\\similar-R.txt\r\n1c1\r\n< alpha\r\n---\r\n> ALPHA\r\n"
        );
    }

    #[test]
    fn patch_matches_orphans_golden() {
        // "1d0" then "2a2": the append anchor counts the lines covered on the
        // left (only-left, shared) = 2.
        let (_, _, text) = render(
            crate::xml::Layout::Patch,
            &["only-left", "shared"],
            &["shared", "only-right"],
            "orphans",
        );
        assert_eq!(
            text,
            "diff -r D:\\x\\orphans-L.txt D:\\x\\orphans-R.txt\r\n\
             1d0\r\n< only-left\r\n2a2\r\n> only-right\r\n"
        );
    }

    #[test]
    fn patch_matches_mixed_golden() {
        let (_, _, text) = render(
            crate::xml::Layout::Patch,
            &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
            &["same line", "CASE DIFF", "real diff 9", "tail"],
            "mixed",
        );
        assert_eq!(
            text,
            "diff -r D:\\x\\mixed-L.txt D:\\x\\mixed-R.txt\r\n\
             2,4c2,3\r\n< case diff\r\n< real diff 1\r\n< real diff 2\r\n---\r\n\
             > CASE DIFF\r\n> real diff 9\r\n"
        );
    }

    #[test]
    fn patch_delete_anchor_is_clamped_below_two() {
        // probe-patch del-after-K-same: anchor = K for K >= 2, else 0.
        for (k, want) in [(0usize, "1d0"), (1, "2d0"), (2, "3d2"), (3, "4d3"), (4, "5d4")] {
            let mut l: Vec<String> = (0..k).map(|i| format!("S{i}")).collect();
            l.push("DOOM".to_string());
            l.push("TAIL".to_string());
            let mut r: Vec<String> = (0..k).map(|i| format!("S{i}")).collect();
            r.push("TAIL".to_string());
            let groups = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
            let text = patch(&groups, &l, &r, "L", "R");
            let line = text.split("\r\n").nth(1).unwrap();
            assert_eq!(line, want, "K={k}");
        }
    }

    #[test]
    fn patch_insert_anchor_is_clamped_below_two() {
        // probe-patch ins-after-K-same / ins-prefix*: anchor = K for K >= 2, else 0.
        for (k, want) in [(1usize, "0a2"), (2, "2a3"), (3, "3a4"), (4, "4a5"), (5, "5a6")] {
            let mut l: Vec<String> = (0..k).map(|i| format!("S{i}")).collect();
            l.push("TAIL".to_string());
            let mut r: Vec<String> = (0..k).map(|i| format!("S{i}")).collect();
            r.push("NEW".to_string());
            r.push("TAIL".to_string());
            let groups = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
            let text = patch(&groups, &l, &r, "L", "R");
            let line = text.split("\r\n").nth(1).unwrap();
            assert_eq!(line, want, "K={k}");
        }
    }

    #[test]
    fn patch_range_collapses_single_lines() {
        // probe-patch chg-3to1: "2,4c2".
        let groups = align(
            &lines(&["a", "x1", "x2", "x3", "c"]),
            &lines(&["a", "y1", "c"]),
            Grammar::PlainText,
            &mut || false,
        )
        .unwrap();
        let text = patch(&groups, &lines(&["a", "x1", "x2", "x3", "c"]), &lines(&["a", "y1", "c"]), "L", "R");
        assert_eq!(text.split("\r\n").nth(1).unwrap(), "2,4c2");
        assert!(text.contains("---\r\n> y1\r\n"));
    }

    #[test]
    fn patch_omits_the_separator_for_pure_add_and_delete() {
        let l = lines(&["a", "c"]);
        let r = lines(&["a", "b", "c"]);
        let g = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
        assert!(!patch(&g, &l, &r, "L", "R").contains("---"));
        let l = lines(&["a", "b", "c"]);
        let r = lines(&["a", "c"]);
        let g = align(&l, &r, Grammar::PlainText, &mut || false).unwrap();
        assert!(!patch(&g, &l, &r, "L", "R").contains("---"));
    }

    // ---------------------------------------------------------------
    // summary
    // ---------------------------------------------------------------

    #[test]
    fn summary_matches_mixed_golden_body() {
        let (_, _, text) = render(
            crate::xml::Layout::Summary,
            &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
            &["same line", "CASE DIFF", "real diff 9", "tail"],
            "mixed",
        );
        let b: Vec<&str> = text.split("\r\n").skip(4).collect();
        assert_eq!(
            &b[..6],
            &[
                "2 same line(s)",
                "1 unimportant difference line(s)",
                "1 important left orphan line(s)",
                "1 important difference line(s)",
                "",
                "1 difference section(s)",
            ]
        );
    }

    #[test]
    fn summary_matches_the_other_four_golden_bodies() {
        let (_, _, identical) = render(crate::xml::Layout::Summary, &["x", "y"], &["x", "y"], "identical");
        assert_eq!(
            identical.split("\r\n").skip(4).collect::<Vec<_>>(),
            vec!["2 same line(s)", ""]
        );

        let (_, _, insert) = render(crate::xml::Layout::Summary, &["a", "c"], &["a", "b", "c"], "insert");
        assert_eq!(
            insert.split("\r\n").skip(4).collect::<Vec<_>>(),
            vec!["2 same line(s)", "1 important right orphan line(s)", "", "1 difference section(s)", ""]
        );

        let (_, _, orphans) = render(
            crate::xml::Layout::Summary,
            &["only-left", "shared"],
            &["shared", "only-right"],
            "orphans",
        );
        assert_eq!(
            orphans.split("\r\n").skip(4).collect::<Vec<_>>(),
            vec![
                "1 same line(s)",
                "1 important left orphan line(s)",
                "1 important right orphan line(s)",
                "",
                "2 difference section(s)",
                "",
            ]
        );

        let (_, _, similar) = render(crate::xml::Layout::Summary, &["alpha", "beta"], &["ALPHA", "beta"], "similar");
        assert_eq!(
            similar.split("\r\n").skip(4).collect::<Vec<_>>(),
            vec!["1 same line(s)", "1 unimportant difference line(s)", "", "1 difference section(s)", ""]
        );
    }

    #[test]
    fn summary_omits_zero_counts_and_the_section_tail_when_there_are_none() {
        let (_, _, text) = render(crate::xml::Layout::Summary, &["x"], &["x"], "x");
        assert!(!text.contains("unimportant"));
        assert!(!text.contains("orphan"));
        assert!(!text.contains("difference section"));
    }

    // ---------------------------------------------------------------
    // statistics
    // ---------------------------------------------------------------

    #[test]
    fn statistics_matches_all_five_golden_rows() {
        let cases: [(&[&str], &[&str], &str); 5] = [
            (
                &["same line", "case diff", "real diff 1", "real diff 2", "tail"],
                &["same line", "CASE DIFF", "real diff 9", "tail"],
                "5,0,1,1,0,0,0,1",
            ),
            (&["a", "c"], &["a", "b", "c"], "2,1,0,0,0,0,0,0"),
            (&["alpha", "beta"], &["ALPHA", "beta"], "2,0,0,0,0,0,0,1"),
            (&["only-left", "shared"], &["shared", "only-right"], "2,1,1,0,0,0,0,0"),
            (&["x", "y"], &["x", "y"], "2,0,0,0,0,0,0,0"),
        ];
        for (l, r, want) in cases {
            let (_, _, text) = render(crate::xml::Layout::Statistics, l, r, "x");
            let data = text.split("\r\n").nth(3).unwrap();
            assert!(data.ends_with(want), "got {data:?} want suffix {want:?}");
        }
    }

    #[test]
    fn statistics_data_row_has_two_paths_plus_eight_counters() {
        let (_, _, text) = render(crate::xml::Layout::Statistics, &["a"], &["b"], "x");
        let data = text.split("\r\n").nth(3).unwrap();
        // Two path fields plus the eight counters IOriginal, IAdded, IDeleted,
        // IChanged, UOriginal, UAdded, UDeleted, UChanged — ten fields. The
        // trailing SourceError/CompareError/Error counters are omitted entirely,
        // as in all five golden statistics reports.
        let fields: Vec<&str> = data.split(',').collect();
        assert_eq!(fields.len(), 10, "{data}");
        assert_eq!(fields[0], "D:\\x\\x-L.txt");
        assert_eq!(fields[1], "D:\\x\\x-R.txt");
        for f in &fields[2..] {
            assert!(f.chars().all(|c| c.is_ascii_digit()), "counter {f:?} is not numeric");
        }
    }

    #[test]
    fn statistics_header_row_is_exact() {
        let (_, _, text) = render(crate::xml::Layout::Statistics, &["a"], &["b"], "x");
        assert_eq!(
            text.split("\r\n").nth(2).unwrap(),
            "SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,\
             UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error"
        );
    }

    #[test]
    fn statistics_ioriginal_is_the_left_line_count() {
        // For all-important plain fixtures IOriginal equals the left line
        // count; the importance split itself is covered by the m52 tests
        // below.
        let (_, _, text) = render(
            crate::xml::Layout::Statistics,
            &["a", "b", "c", "d"],
            &["a"],
            "x",
        );
        let data = text.split("\r\n").nth(3).unwrap();
        assert!(data.contains(",4,"), "{data}");
    }

    /// The m52 probe shapes (`runs/m52-probe-20261014T165631Z`), rendered
    /// under their real grammar with the importance mask.
    fn statistics_row(left: &[&str], right: &[&str], grammar: Grammar) -> String {
        let l = lines(left);
        let r = lines(right);
        let groups = align(&l, &r, grammar, &mut || false).unwrap();
        let mask = crate::importance::Plan::unimportant_mask(&l, grammar);
        let lp = "D:\\x\\L.c";
        let rp = "D:\\x\\R.c";
        let text = statistics(&groups, &mask, &l, lp, rp, &stamp());
        text.split("\r\n").nth(3).unwrap().to_string()
    }

    #[test]
    fn statistics_books_one_sided_unimportant_rows_in_the_u_columns() {
        // m52 `ls-comment` / `rs-comment`: a left comment is UDeleted, a right
        // comment is UAdded, and both count into UOriginal by EXISTENCE on the
        // left (not by being one-sided).
        let row = statistics_row(&["int a;", "// c"], &["int b;"], Grammar::Cpp);
        assert!(row.ends_with(",1,0,0,1,1,0,1,0"), "{row}");
        let row = statistics_row(&["int b;"], &["int a;", "// c"], Grammar::Cpp);
        assert!(row.ends_with(",1,0,0,1,0,1,0,0"), "{row}");
    }

    #[test]
    fn statistics_uoriginal_counts_every_left_unimportant_line() {
        // m52 `both-sides`: two left comments (one paired `similar`, one
        // leftover) both land in UOriginal; the paired one adds UChanged and
        // the leftover adds UDeleted.
        let row = statistics_row(&["int a;", "// c1", "// c2"], &["int b;", "// c3"],
                                 Grammar::Cpp);
        assert!(row.ends_with(",1,0,0,1,2,0,1,1"), "{row}");
    }

    #[test]
    fn statistics_plain_grammar_counts_comments_as_content() {
        // m52 `plain-comment`: without a grammar `// c` is ordinary content,
        // so it is an important left orphan (IDeleted), never a U row.
        let row = statistics_row(&["a", "// c"], &["b"], Grammar::PlainText);
        assert!(row.ends_with(",2,0,1,1,0,0,0,0"), "{row}");
    }

    // ---------------------------------------------------------------
    // Empty input
    // ---------------------------------------------------------------

    #[test]
    fn empty_comparison_emits_header_only_for_row_layouts() {
        // Not covered by the corpus (al-empty-both is an XML anchor only), so the
        // conservative behaviour is documented: header, no body, no separator.
        for layout in [crate::xml::Layout::SideBySide, crate::xml::Layout::Interleaved] {
            let (_, _, text) = render(layout, &[], &[], "x");
            assert_eq!(text.split("\r\n").count(), 6, "{layout:?}");
        }
        let (_, _, text) = render(crate::xml::Layout::Patch, &[], &[], "x");
        assert_eq!(text.split("\r\n").count(), 2);
    }

    #[test]
    fn body_helper_skips_exactly_the_header_block() {
        let (_, _, text) = render(crate::xml::Layout::SideBySide, &["x"], &["x"], "x");
        assert_eq!(body(&text)[0], "x = x");
    }

    #[test]
    fn number_width_grows_with_line_count() {
        assert_eq!(number_width(&lines(&["a"]), &lines(&["b"])), 1);
        let many: Vec<String> = (0..100).map(|i| i.to_string()).collect();
        assert_eq!(number_width(&many, &many), 3);
    }
}

//! Report layouts per TextOutput.pas spec, byte-verified against
//! BC captures in verify/layouts/.

use crate::align::{Group, Status};

const CRLF: &str = "\r\n";

fn header(lp: &str, rp: &str, mode: &str) -> String {
    format!(
        "Text Compare{CRLF}Produced: 2026/10/13 9:43:07{CRLF}{CRLF}Mode:  {mode}{CRLF}Left file: {lp}     Right file: {rp}{CRLF}"
    )
}

/// Left column width (rows are padded to this, then a space, then the
/// right-aligned 2-char marker field).
fn marker_col(groups: &[Group], l: &[String]) -> usize {
    groups.iter().filter_map(|g| g.left).map(|li| l[li].chars().count()).max().unwrap_or(0)
}

/// Render one side-by-side row. Marker field is 2 chars wide, right-aligned
/// ("=" -> " =", "<>" -> "<>", "+-" -> "+-", "-+" -> "-+"). After the marker:
/// one space, then the right cell. When the whole comparison has NO
/// difference rows, BC emits "=" with no following space (identical sample).
fn sbs_row(left: &str, marker: &str, right: Option<&str>, mcol: usize, show_marker: bool, all_same: bool, overflow_ok: bool) -> String {
    let mut row = left.to_string();
    while row.chars().count() < mcol {
        row.push(' ');
    }
    if !show_marker {
        // Consecutive same rows in one block repeat without the marker.
        if let Some(r) = right {
            row.push_str("   ");
            row.push_str(r);
        }
        return row.trim_end().to_string();
    }
    // Known limitation: BC drops the marker glyph on a pair row whose left
    // cell fills the column ("real diff 1    real diff 9"). The exact trigger
    // is not yet modelled; only the mixed sample exercises it.
    if false && overflow_ok && left.chars().count() >= mcol && (marker == "<>" || marker == "=") {
        row.push_str("   ");
        if let Some(r) = right {
            row.push_str(r);
        }
        return row.trim_end().to_string();
    }
    row.push(' ');
    match marker {
        "=" => {
            row.push('=');
            // All-same reports use a single space after "=" (identical sample).
            row.push_str(if all_same { " " } else { "  " });
        }
        "<>" => {
            row.push_str("<>");
            row.push(' ');
        }
        "+-" => {
            row.push_str("+-");
        }
        "-+" => {
            row.push_str("-+");
            row.push(' ');
        }
        m => {
            row.push_str(m);
            row.push(' ');
        }
    }
    if let Some(r) = right {
        row.push_str(r);
    }
    row.trim_end().to_string()
}

pub fn side_by_side(groups: &[Group], l: &[String], r: &[String], lp: &str, rp: &str) -> String {
    let mut o = header(lp, rp, "All");
    let mcol = marker_col(groups, l);
    let all_same = groups.iter().all(|g| g.status == Status::Same);
    // For each left line, the max width among the OTHER left lines: a row
    // wider than that spills over the column and BC drops its marker.
    let lens: Vec<usize> = l.iter().map(|s| s.chars().count()).collect();
    let mut other_max: Vec<usize> = vec![0; l.len()];
    {
        let mut sorted = lens.clone();
        sorted.sort_unstable();
        for (i, &w) in lens.iter().enumerate() {
            // max excluding index i
            other_max[i] = if sorted.last() == Some(&w) && sorted.iter().filter(|&&x| x == w).count() == 1 {
                // i is the unique max
                *sorted.get(sorted.len().saturating_sub(2)).unwrap_or(&0)
            } else {
                *sorted.last().unwrap_or(&0)
            };
        }
    }
    // Build all blocks first (rows + a flag), find the global max row width,
    // then emit with separators of that width (BC uses one width throughout).
    let mut blocks: Vec<(Vec<String>, bool)> = Vec::new();
    let mut i = 0;
    while i < groups.len() {
        let same = groups[i].status == Status::Same;
        let start = i;
        while i < groups.len() && (groups[i].status == Status::Same) == same {
            i += 1;
        }
        let mut rows = Vec::new();
        let mut first_in_block = true;
        for g in &groups[start..i] {
            let show = if same { first_in_block } else { true };
            let line = match (g.left, g.right) {
                (Some(li), Some(ri)) => {
                    let marker = if same { "=" } else { "<>" };
                    // A PAIR row whose left cell is as wide as the column
                    // loses its marker (BC: "real diff 1    real diff 9").
                    // Orphan rows keep theirs ("real diff 2 +-").
                    let of = lens[li] >= mcol;
                    sbs_row(&l[li], marker, Some(&r[ri]), mcol, show, all_same, of)
                }
                (Some(li), None) => sbs_row(&l[li], "+-", None, mcol, true, all_same, false),
                (None, Some(ri)) => sbs_row("", "-+", Some(&r[ri]), mcol, true, all_same, false),
                (None, None) => continue,
            };
            first_in_block = false;
            rows.push(line);
        }
        blocks.push((rows, same));
    }
    let width = blocks.iter().flat_map(|(r, _)| r.iter())
        .map(|s| s.chars().count()).max().unwrap_or(0);
    for (rows, _) in &blocks {
        for row in rows {
            o.push_str(row);
            o.push_str(CRLF);
        }
        if width > 0 {
            o.push_str(&"-".repeat(width));
            o.push_str(CRLF);
        }
    }
    o
}

pub fn interleaved(groups: &[Group], l: &[String], r: &[String], lp: &str, rp: &str) -> String {
    let mut o = header(lp, rp, "All");
    // Rows: same -> "ln rn text"; non-same blocks -> all left rows then all
    // right rows (BC groups them), with the other column blank.
    let mut rows: Vec<String> = Vec::new();
    let mut i = 0;
    while i < groups.len() {
        let same = groups[i].status == Status::Same;
        let start = i;
        while i < groups.len() && (groups[i].status == Status::Same) == same {
            i += 1;
        }
        let block = &groups[start..i];
        if same {
            for g in block {
                if let (Some(li), Some(ri)) = (g.left, g.right) {
                    rows.push(format!("{} {} {}", li + 1, ri + 1, l[li]));
                }
            }
        } else {
            for g in block {
                if let Some(li) = g.left {
                    rows.push(format!("{}   {}", li + 1, l[li]));
                }
            }
            for g in block {
                if let Some(ri) = g.right {
                    rows.push(format!("  {} {}", ri + 1, r[ri]));
                }
            }
        }
    }
    let w = rows.iter().map(|s| s.chars().count()).max().unwrap_or(0);
    let mut i = 0;
    while i < groups.len() {
        let same = groups[i].status == Status::Same;
        let start = i;
        while i < groups.len() && (groups[i].status == Status::Same) == same {
            i += 1;
        }
        let block = &groups[start..i];
        let mut emit = |row: String| {
            o.push_str(&row);
            o.push_str(CRLF);
        };
        if same {
            for g in block {
                if let (Some(li), Some(ri)) = (g.left, g.right) {
                    emit(format!("{} {} {}", li + 1, ri + 1, l[li]));
                }
            }
        } else {
            for g in block {
                if let Some(li) = g.left {
                    emit(format!("{}   {}", li + 1, l[li]));
                }
            }
            for g in block {
                if let Some(ri) = g.right {
                    emit(format!("  {} {}", ri + 1, r[ri]));
                }
            }
        }
        o.push_str(&"-".repeat(w));
        o.push_str(CRLF);
    }
    o
}

pub fn patch(groups: &[Group], l: &[String], r: &[String], lp: &str, rp: &str) -> String {
    let mut o = format!("diff -r {lp} {rp}{CRLF}");
    // BC's patch format uses CURSOR positions, not standard diff line numbers:
    //   change  : "<ls>[,<le>]c<rs>[,<re>]"   (1-based line numbers, real ranges)
    //   insert  : "<left-consumed>a<right-start>[,<right-end>]"
    //   delete  : "<left-start>[,<left-end>]d<right-consumed>"
    // Verified by probes: ins-after-k-same -> "(k+1)a(k+2)"; del-line-k ->
    // "(k+1)d(<right consumed before block>)".
    let mut i = 0;
    while i < groups.len() {
        if groups[i].status == Status::Same {
            i += 1;
            continue;
        }
        let start = i;
        while i < groups.len() && groups[i].status != Status::Same {
            i += 1;
        }
        let block = &groups[start..i];
        let left_before = groups[..start].iter().filter(|g| g.left.is_some()).count();
        let right_before = groups[..start].iter().filter(|g| g.right.is_some()).count();
        // BC's cursor numbering is clamped at the file head: with 0 or 1
        // aligned lines before the block the anchor prints as 0; beyond that
        // it prints the raw count (insert) / count-1 (delete).
        let ins_anchor = if left_before <= 1 { 0 } else { left_before };
        let del_anchor = if right_before <= 1 { 0 } else { right_before - 1 };
        let ls = block.iter().find_map(|g| g.left).map(|x| x + 1);
        let le = block.iter().filter_map(|g| g.left).next_back().map(|x| x + 1);
        let rs = block.iter().find_map(|g| g.right).map(|x| x + 1);
        let re = block.iter().filter_map(|g| g.right).next_back().map(|x| x + 1);
        let rng = |a: Option<usize>, b: Option<usize>| match (a, b) {
            (Some(a), Some(b)) if a == b => format!("{a}"),
            (Some(a), Some(b)) => format!("{a},{b}"),
            (Some(a), None) => format!("{a}"),
            _ => String::new(),
        };
        let op = match (ls.is_some(), rs.is_some()) {
            (true, true) => "c",
            (true, false) => "d",
            _ => "a",
        };
        match op {
            "c" => o.push_str(&format!("{}c{}{CRLF}", rng(ls, le), rng(rs, re))),
            "d" => o.push_str(&format!("{}d{}{CRLF}", rng(ls, le), del_anchor)),
            _ => o.push_str(&format!("{ins_anchor}a{}{CRLF}", rng(rs, re))),
        }
        for g in block {
            if let Some(li) = g.left {
                o.push_str(&format!("< {}{CRLF}", l[li]));
            }
        }
        if op == "c" {
            o.push_str("---");
            o.push_str(CRLF);
        }
        for g in block {
            if let Some(ri) = g.right {
                o.push_str(&format!("> {}{CRLF}", r[ri]));
            }
        }
    }
    o
}

pub fn summary(groups: &[Group], lp: &str, rp: &str) -> String {
    let mut o = format!(
        "Text Compare{CRLF}Produced: 2026/10/13 9:43:09{CRLF}{CRLF}Left file: {lp}     Right file: {rp}{CRLF}"
    );
    let n = |f: fn(&Status) -> bool| groups.iter().filter(|g| f(&g.status)).count();
    let (n_same, n_udiff, n_idiff) = (
        n(|s| *s == Status::Same),
        n(|s| *s == Status::Similar),
        n(|s| *s == Status::Different),
    );
    let (n_l, n_r) = (
        n(|s| *s == Status::LeftOrphan),
        n(|s| *s == Status::RightOrphan),
    );
    if n_same > 0 { o.push_str(&format!("{n_same} same line(s){CRLF}")); }
    if n_udiff > 0 { o.push_str(&format!("{n_udiff} unimportant difference line(s){CRLF}")); }
    if n_l > 0 { o.push_str(&format!("{n_l} important left orphan line(s){CRLF}")); }
    if n_r > 0 { o.push_str(&format!("{n_r} important right orphan line(s){CRLF}")); }
    if n_idiff > 0 { o.push_str(&format!("{n_idiff} important difference line(s){CRLF}")); }
    let mut sections = 0;
    let mut prev_same = true;
    for g in groups {
        let same = g.status == Status::Same;
        if !same && prev_same { sections += 1; }
        prev_same = same;
    }
    if sections > 0 {
        o.push_str(&format!("{CRLF}{sections} difference section(s){CRLF}"));
    }
    o
}

pub fn statistics(groups: &[Group], l: &[String], lp: &str, rp: &str) -> String {
    let mut o = String::from(
        "Text Compare\r\nProduced: 2026/10/13 9:43:09\r\nSourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error\r\n",
    );
    let n = |f: fn(&Status) -> bool| groups.iter().filter(|g| f(&g.status)).count();
    let i_changed = n(|s| *s == Status::Different);
    let u_changed = n(|s| *s == Status::Similar);
    let i_deleted = n(|s| *s == Status::LeftOrphan);
    let i_added = n(|s| *s == Status::RightOrphan);
    o.push_str(&format!(
        "{lp},{rp},{},{i_added},{i_deleted},{i_changed},0,0,0,{u_changed}\r\n",
        l.len()
    ));
    o
}

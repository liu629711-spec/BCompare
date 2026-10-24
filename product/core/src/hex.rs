//! M7: the hex/binary comparison channel (`hex-report`).
//!
//! Every rule below is transcribed from the Oracle archives
//! `runs/m70-hexsurface-*`, `runs/m70b-hexmodel-*`, `runs/m70c-hexorphan-*`,
//! `runs/m70d-hexresidual-*`, `runs/m70e-hexreflabels-*`,
//! `runs/m70e2-hexcounts-*`, `runs/m70f-hexshapes-*` (docs/14). Geometry was
//! read from integer ordinals, never display text (docs/12 §3).
//!
//! The model:
//! * bytes align with the existing Myers byte diff (equal bytes only);
//! * between matches, a gap (gl x gr) yields `min(gl,gr)` paired-change
//!   slots first, then one-sided orphan slots, then the match pair — this
//!   reproduces Y2's row-0 geometry (inserted byte at slot 4, both sides'
//!   continuation aligned in the same slots) and Z8's paired change@0;
//! * slots chunk into rows of 8; a row is a diff row when any slot is not a
//!   matched pair; blocks are maximal same-kind runs, so a leftover row
//!   mixing matched pairs with orphan slots renders as ONE `<>` block
//!   (Y11: `38..3F <> 38..3B`, four same pairs + four left orphans);
//! * side-by-side: line = lcol + `' '` + marker-padded(w) + `' '` + rcol,
//!   trimmed. The marker text (`=`/`<>`) appears ONLY on the first row of
//!   each block (Y5). lcol/rcol are the 33-col field padded, or collapse to
//!   `""` when that side has NO byte anywhere in the report (Y13).
//!   w = 2 iff the report has any diff row, else 1 (Y1 vs Y2). A dash rule
//!   closes every block at the GLOBAL max row length (Y4: rule 70 while the
//!   block's own row is 36).
//! * interleaved: no marker column; same rows merge into
//!   `offL(8 hex) + ' ' + offR(8 hex) + ' ' + field(33)`; a diff block
//!   emits in TWO passes — every row with left bytes, then every row with
//!   right bytes (V3's trailing block: left rows 0x38/0x40/0x48 print
//!   before the right line, not interleaved). Offsets are that side's
//!   first byte index in the row (Y6: `00000007 00000008`; Z4/Z5 blanks;
//!   Z7 keeps 8 digits past 0xFFFF).
//! * summary: byte counts in order same, left orphan, right orphan,
//!   difference; a paired-change slot counts as ONE difference byte; zero
//!   lines omitted (Y7/Z1-Z3, m70d V1, m70e2 V5 both installs).
//! * frame: `Hex Compare` / `Produced: <slash stamp>` / blank /
//!   `Mode:  All` (summary drops it) / the two file lines; `title:` replaces
//!   frame line 1 (Y11, V3). No body lines for empty-empty (Z6).

use crate::myers::{diff_matches, map_ids};
use crate::stamp::Stamp;

const CRLF: &str = "\r\n";
const ROW_SLOTS: usize = 8;
/// One rendered field column: 23 hex-zone chars + 2 spaces + 8 ascii chars.
const FIELD_LEN: usize = 23 + 2 + ROW_SLOTS;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HexLayout {
    SideBySide,
    Interleaved,
    Summary,
}

impl HexLayout {
    pub fn parse(name: &str) -> Option<Self> {
        match name.to_ascii_lowercase().as_str() {
            "side-by-side" => Some(Self::SideBySide),
            "interleaved" => Some(Self::Interleaved),
            "summary" => Some(Self::Summary),
            _ => None,
        }
    }
    pub fn name(self) -> &'static str {
        match self {
            Self::SideBySide => "side-by-side",
            Self::Interleaved => "interleaved",
            Self::Summary => "summary",
        }
    }
}

pub const HEX_LAYOUT_NAMES: &str = "side-by-side, interleaved, summary";

#[derive(Debug, Clone)]
pub enum HexError {
    Diff(crate::myers::DiffError),
}

impl std::fmt::Display for HexError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Diff(e) => write!(f, "byte alignment failed: {e}"),
        }
    }
}

/// One alignment slot: at most one byte per side. `matched` marks an LCS
/// equal pair; a both-sides slot without `matched` is a paired change.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Slot {
    l: Option<usize>,
    r: Option<usize>,
    matched: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HexRow {
    pub slots: Vec<Slot>,
    pub diff: bool,
}

/// GUI-facing flat slot with byte VALUES (the `--hex3` data channel feeds the
/// Hex Compare view; the view regroups the stream into 16-byte rows itself —
/// the VIEW's measured row is 16 bytes in two 8 groups, unlike the report's
/// 8-slot rows, so the chunking stays with each consumer).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ByteSlot {
    pub l: Option<u8>,
    pub r: Option<u8>,
    pub matched: bool,
}

/// Align two byte files into the flat slot stream (byte values).
pub fn align_slots(left: &[u8], right: &[u8]) -> Result<Vec<ByteSlot>, HexError> {
    let rows = align_bytes(left, right)?;
    let lb = left;
    let rb = right;
    let mut out = Vec::new();
    for row in &rows {
        for s in &row.slots {
            out.push(ByteSlot {
                l: s.l.map(|i| lb[i]),
                r: s.r.map(|i| rb[i]),
                matched: s.matched,
            });
        }
    }
    Ok(out)
}

impl HexRow {
    fn first_l(&self) -> Option<usize> {
        self.slots.iter().find_map(|s| s.l)
    }
    fn first_r(&self) -> Option<usize> {
        self.slots.iter().find_map(|s| s.r)
    }
    fn has_l(&self) -> bool {
        self.first_l().is_some()
    }
    fn has_r(&self) -> bool {
        self.first_r().is_some()
    }
}

/// Align two byte files into the slot stream, chunked into 8-slot rows.
pub fn align_bytes(left: &[u8], right: &[u8]) -> Result<Vec<HexRow>, HexError> {
    let (li, ri) = map_ids(left, right);
    let matches = diff_matches(&li, &ri).map_err(HexError::Diff)?;

    let mut slots: Vec<Slot> = Vec::new();
    let mut lp = 0usize;
    let mut rp = 0usize;
    for &(ml, mr) in &matches {
        // gap [lp..ml) x [rp..mr): paired changes first, then orphans
        let paired = (ml - lp).min(mr - rp);
        for k in 0..paired {
            slots.push(Slot { l: Some(lp + k), r: Some(rp + k), matched: false });
        }
        lp += paired;
        rp += paired;
        while lp < ml {
            slots.push(Slot { l: Some(lp), r: None, matched: false });
            lp += 1;
        }
        while rp < mr {
            slots.push(Slot { l: None, r: Some(rp), matched: false });
            rp += 1;
        }
        slots.push(Slot { l: Some(ml), r: Some(mr), matched: true });
        lp = ml + 1;
        rp = mr + 1;
    }
    let paired = (left.len() - lp).min(right.len() - rp);
    for k in 0..paired {
        slots.push(Slot { l: Some(lp + k), r: Some(rp + k), matched: false });
    }
    lp += paired;
    rp += paired;
    for i in lp..left.len() {
        slots.push(Slot { l: Some(i), r: None, matched: false });
    }
    for j in rp..right.len() {
        slots.push(Slot { l: None, r: Some(j), matched: false });
    }

    Ok(slots
        .chunks(ROW_SLOTS)
        .map(|chunk| {
            let diff = chunk
                .iter()
                .any(|s| !(s.matched && s.l.is_some() && s.r.is_some()));
            HexRow { slots: chunk.to_vec(), diff }
        })
        .collect())
}

/// Byte counts for `summary` (m70e2 V5 pinned the pairing model: a
/// paired-change slot counts as ONE difference byte; V1's
/// 60 same / 18 left / 2 diff is reproduced only by that pairing).
pub fn hex_counts(rows: &[HexRow]) -> [usize; 4] {
    let mut c = [0usize; 4];
    for row in rows {
        for s in &row.slots {
            match (s.l, s.r) {
                (Some(_), Some(_)) if s.matched => c[0] += 1,
                (Some(_), None) => c[1] += 1,
                (None, Some(_)) => c[2] += 1,
                (Some(_), Some(_)) => c[3] += 1,
                (None, None) => {}
            }
        }
    }
    c
}

/// Same census over the flat GUI slot stream (identical pairing model: a
/// paired-change slot counts as ONE difference byte).
pub fn slot_counts(slots: &[ByteSlot]) -> [usize; 4] {
    let mut c = [0usize; 4];
    for s in slots {
        match (s.l, s.r) {
            (Some(_), Some(_)) if s.matched => c[0] += 1,
            (Some(_), None) => c[1] += 1,
            (None, Some(_)) => c[2] += 1,
            (Some(_), Some(_)) => c[3] += 1,
            (None, None) => {}
        }
    }
    c
}

fn ascii_of(b: u8) -> char {
    if (0x20..=0x7E).contains(&b) {
        b as char
    } else {
        '.'
    }
}

/// One side's field for a row, padded to FIELD_LEN (33): hex zone (each of
/// slots 0..6 three chars, slot 7 two), two spaces, 8 ascii columns (empty
/// slot -> space).
fn field(bytes: &[u8], row: &HexRow, side_left: bool) -> String {
    let picks: Vec<Option<usize>> = (0..ROW_SLOTS)
        .map(|k| row.slots.get(k).and_then(|s| if side_left { s.l } else { s.r }))
        .collect();
    let mut out = String::with_capacity(FIELD_LEN);
    for (k, idx) in picks.iter().enumerate() {
        match idx {
            Some(i) => {
                out.push_str(&format!("{:02X}", bytes[*i]));
                if k + 1 < ROW_SLOTS {
                    out.push(' ');
                }
            }
            None if k + 1 < ROW_SLOTS => out.push_str("   "),
            None => out.push_str("  "),
        }
    }
    out.push_str("  ");
    for idx in &picks {
        out.push(match idx {
            Some(i) => ascii_of(bytes[*i]),
            None => ' ',
        });
    }
    debug_assert_eq!(out.chars().count(), FIELD_LEN);
    out
}

fn offset(bytes: Option<usize>) -> String {
    match bytes {
        Some(i) => format!("{i:08X}"),
        None => " ".repeat(8),
    }
}

fn blocks(rows: &[HexRow]) -> Vec<(usize, usize)> {
    let mut out = Vec::new();
    let mut i = 0;
    while i < rows.len() {
        let kind = rows[i].diff;
        let mut j = i + 1;
        while j < rows.len() && rows[j].diff == kind {
            j += 1;
        }
        out.push((i, j));
        i = j;
    }
    out
}

fn sbs_body(left: &[u8], right: &[u8], rows: &[HexRow]) -> Vec<String> {
    if rows.is_empty() {
        return Vec::new(); // Z6: empty-empty prints no body rows at all
    }
    let lhas = rows.iter().any(HexRow::has_l);
    let rhas = rows.iter().any(HexRow::has_r);
    let w = if rows.iter().any(|r| r.diff) { 2 } else { 1 };
    let mut lines: Vec<String> = Vec::new();
    let mut max_len = 0usize;
    for (i, j) in blocks(rows) {
        for (k, row) in rows[i..j].iter().enumerate() {
            let mut line = if lhas { field(left, row, true) } else { String::new() };
            // zone: ' ' + marker padded to w + ' '; marker text only on the
            // block's first row (Y5's two-row diff block: second row blank)
            let marker = match (k == 0, row.diff) {
                (true, true) => "<>",
                (true, false) => "=",
                _ => "",
            };
            line.push(' ');
            line.push_str(&format!("{marker:<w$}"));
            line.push(' ');
            if rhas {
                line.push_str(&field(right, row, false));
            }
            let line = line.trim_end().to_string();
            max_len = max_len.max(line.chars().count());
            lines.push(line);
        }
        lines.push(String::new()); // rule placeholder
    }
    let mut out: Vec<String> = Vec::new();
    for l in lines {
        if l.is_empty() {
            out.push("-".repeat(max_len)); // rules at GLOBAL max (Y4)
        } else {
            out.push(l);
        }
    }
    out
}

fn interleaved_body(left: &[u8], right: &[u8], rows: &[HexRow]) -> Vec<String> {
    // A diff block emits in TWO passes: every row with left bytes first,
    // then every row with right bytes (V3: rows 0x38/0x40/0x48 are left-
    // only inside a block whose last line carries right bytes — the right
    // line closes the block, it does not interleave). Same rows merge.
    let mut out: Vec<String> = Vec::new();
    let mut max_len = 0usize;
    let mut block_rules: Vec<usize> = Vec::new(); // insert index after block
    for (i, j) in blocks(rows) {
        for row in &rows[i..j] {
            if row.diff {
                if let Some(o) = row.first_l() {
                    let l = format!("{} {} {}", offset(Some(o)), offset(None), field(left, row, true));
                    max_len = max_len.max(l.trim_end().chars().count());
                    out.push(l.trim_end().to_string());
                }
            } else {
                let lo = row.first_l();
                let ro = row.first_r();
                let f = if lo.is_some() { field(left, row, true) } else { field(right, row, false) };
                let l = format!("{} {} {}", offset(lo), offset(ro), f);
                max_len = max_len.max(l.trim_end().chars().count());
                out.push(l.trim_end().to_string());
            }
        }
        for row in &rows[i..j] {
            if row.diff {
                if let Some(o) = row.first_r() {
                    let l = format!("{} {} {}", offset(None), offset(Some(o)), field(right, row, false));
                    max_len = max_len.max(l.trim_end().chars().count());
                    out.push(l.trim_end().to_string());
                }
            }
        }
        block_rules.push(out.len());
    }
    let mut res: Vec<String> = Vec::new();
    let mut next = 0usize;
    for (k, l) in out.into_iter().enumerate() {
        res.push(l);
        if next < block_rules.len() && block_rules[next] == k + 1 {
            res.push("-".repeat(max_len));
            next += 1;
        }
    }
    res
}

fn summary_body(rows: &[HexRow]) -> Vec<String> {
    let [same, left_or, right_or, diff] = hex_counts(rows);
    let mut out = Vec::new();
    if same > 0 {
        out.push(format!("{same} same byte(s)"));
    }
    if left_or > 0 {
        out.push(format!("{left_or} left orphan byte(s)"));
    }
    if right_or > 0 {
        out.push(format!("{right_or} right orphan byte(s)"));
    }
    if diff > 0 {
        out.push(format!("{diff} difference byte(s)"));
    }
    out
}

/// The complete hex report: frame + body, CRLF, no BOM.
pub fn render_hex_report(
    layout: HexLayout,
    left: &[u8],
    right: &[u8],
    left_path: &str,
    right_path: &str,
    stamp: &Stamp,
    title: Option<&str>,
) -> Result<String, HexError> {
    let rows = align_bytes(left, right)?;
    let body = match layout {
        HexLayout::SideBySide => sbs_body(left, right, &rows),
        HexLayout::Interleaved => interleaved_body(left, right, &rows),
        HexLayout::Summary => summary_body(&rows),
    };
    let mut lines: Vec<String> = vec![
        title.unwrap_or("Hex Compare").to_string(),
        format!("Produced: {stamp}"),
        String::new(),
    ];
    if layout != HexLayout::Summary {
        lines.push("Mode:  All".to_string());
    }
    lines.push(format!("Left file: {left_path}"));
    lines.push(format!("Right file: {right_path}"));
    lines.extend(body);
    Ok(lines.join(CRLF) + CRLF)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn seq(n: usize) -> Vec<u8> {
        (0..n).map(|i| (i & 0xFF) as u8).collect()
    }

    fn stamp() -> Stamp {
        Stamp::from_parts(2026, 10, 18, 0, 0, 0)
    }

    fn report_rows(layout: HexLayout, l: &[u8], r: &[u8]) -> Vec<String> {
        let text = render_hex_report(layout, l, r, "L", "R", &stamp(), None).unwrap();
        let skip = if layout == HexLayout::Summary { 5 } else { 6 };
        let mut rows: Vec<String> = text
            .replace("\r\n", "\n")
            .split('\n')
            .skip(skip)
            .map(|s| s.to_string())
            .collect();
        // the trailing CRLF of the report yields one empty artifact line
        if rows.last().map(|l| l.is_empty()).unwrap_or(false) {
            rows.pop();
        }
        rows
    }

    #[test]
    fn align_slots_crossvalidates_rows_and_probe_fixture() {
        // docs/19 §6.19: the flat GUI slot stream must agree with the report
        // row model row-for-row, and reproduce the live hex-view probe
        // fixture (paired change at 0x08..0x0B, L-only tail 0x30..0x33,
        // R-only tail 0xF0..0xF1 — extracted/live/hexview-en).
        let mut l: Vec<u8> = (0x00..0x30).collect();
        l[8..12].copy_from_slice(&[0xAA, 0xBB, 0xCC, 0xDD]);
        l.extend_from_slice(&[0x30, 0x31, 0x32, 0x33]);
        let mut r: Vec<u8> = (0x00..0x30).collect();
        r[8..12].copy_from_slice(&[0x11, 0x22, 0x33, 0x44]);
        r.extend_from_slice(&[0xF0, 0xF1]);
        let slots = align_slots(&l, &r).unwrap();
        // stream length = the aligned slot count = rows*8 of align_bytes
        let rows = align_bytes(&l, &r).unwrap();
        assert_eq!(slots.len(), rows.iter().map(|r| r.slots.len()).sum::<usize>());
        for (k, row) in rows.iter().enumerate() {
            for (j, s) in row.slots.iter().enumerate() {
                let b = slots[k * 8 + j];
                assert_eq!(b.l.map(|v| v as usize), s.l.map(|i| l[i] as usize));
                assert_eq!(b.r.map(|v| v as usize), s.r.map(|i| r[i] as usize));
                assert_eq!(b.matched, s.matched);
            }
        }
        // paired change at 0x08..0x0B: 4 non-matched both-sides slots
        let changed: Vec<_> = slots[8..12].iter().collect();
        assert!(changed.iter().all(|s| !s.matched && s.l.is_some() && s.r.is_some()));
        assert_eq!(changed[0].l, Some(0xAA));
        assert_eq!(changed[0].r, Some(0x11));
        // tail gap gl=4 x gr=2 -> min() paired changes FIRST (M7 model,
        // docs/14 §2), then single-side orphans:
        //   slots 48/49 = paired change (0x30<->0xF0, 0x31<->0xF1)
        //   slots 50/51 = left orphans (0x32, 0x33)
        assert_eq!(slots[48].l, Some(0x30));
        assert_eq!(slots[48].r, Some(0xF0));
        assert!(!slots[48].matched);
        assert_eq!(slots[50].l, Some(0x32));
        assert_eq!(slots[50].r, None);
        // counts: 44 same (0x00..0x07 + 0x0C..0x2F) / 2 L / 0 R / 6 diff
        assert_eq!(slot_counts(&slots), [44, 2, 0, 6]);
        // the equal prefix renders identical to the report model
        assert!(!rows[0].slots[0].matched == false);
    }

    #[test]
    fn slot_geometry_insertion_keeps_row_positions() {
        // Y2: R inserts one byte at 0x04 -> orphan slot at row 0 slot 4,
        // continuation aligned in the SAME slots on both sides.
        let l = seq(16);
        let mut r = l[..4].to_vec();
        r.push(0x41);
        r.extend_from_slice(&l[4..]);
        let rows = align_bytes(&l, &r).unwrap();
        assert_eq!(rows.len(), 3); // 17 slots
        assert!(rows[0].diff);
        assert_eq!(rows[0].slots[4], Slot { l: None, r: Some(4), matched: false });
        assert!(!rows[1].diff && !rows[2].diff);
    }

    #[test]
    fn paired_change_before_orphans() {
        // Z8: R = FF + L[1..61): change@0 paired, then right runs dry.
        let l = seq(64);
        let mut r: Vec<u8> = vec![0xFF];
        r.extend_from_slice(&l[1..60]);
        let rows = align_bytes(&l, &r).unwrap();
        assert_eq!(rows[0].slots[0], Slot { l: Some(0), r: Some(0), matched: false });
    }

    #[test]
    fn sbs_all_same_uses_width_one_marker() {
        // Y1: no diff rows anywhere -> zone 1: ` = ` once, blank '   ' after
        let l = seq(32);
        let r = l.clone();
        let body = report_rows(HexLayout::SideBySide, &l, &r);
        assert_eq!(
            body[0],
            "00 01 02 03 04 05 06 07  ........ = 00 01 02 03 04 05 06 07  ........"
        );
        assert_eq!(
            body[1],
            "08 09 0A 0B 0C 0D 0E 0F  ........   08 09 0A 0B 0C 0D 0E 0F  ........"
        );
        let rules: Vec<&String> = body.iter().filter(|l| l.starts_with('-')).collect();
        assert_eq!(rules.len(), 1); // single block, single closing rule
        assert_eq!(rules[0].chars().count(), 69);
    }

    #[test]
    fn sbs_marker_on_block_head_only() {
        // Y5-many: two-row diff block: '<>' only on the first row
        let l = seq(32);
        let mut r = l.clone();
        r[4] = 0xFF;
        r[12] = 0xFF;
        let body = report_rows(HexLayout::SideBySide, &l, &r);
        assert!(body[0].contains("<>"));
        assert!(!body[1].contains("<>"));
        assert_eq!(body[1].chars().count(), 70); // w=2 continuation keeps width
    }

    #[test]
    fn sbs_rule_width_is_global_max() {
        // Y4: orphan-only diff row (36 wide) inside a report whose full rows
        // are 70 wide -> its block rule is 70, not 36.
        let l = seq(32);
        let mut r = l[..16].to_vec();
        r.extend_from_slice(&l[24..]);
        let body = report_rows(HexLayout::SideBySide, &l, &r);
        let rules: Vec<&String> = body.iter().filter(|l| l.starts_with('-')).collect();
        for rule in &rules {
            assert_eq!(rule.chars().count(), 70, "{:?}", rule);
        }
    }

    #[test]
    fn sbs_empty_side_collapses_column() {
        // Y13: left has no bytes at all -> no left column; zone w=2 diff row
        let r = seq(16);
        let body = report_rows(HexLayout::SideBySide, &[], &r);
        assert_eq!(body[0], " <> 00 01 02 03 04 05 06 07  ........");
        assert_eq!(body[1], "    08 09 0A 0B 0C 0D 0E 0F  ........");
        assert_eq!(body[2].chars().count(), 37);
    }

    #[test]
    fn sbs_short_row_keeps_slot_spacing() {
        // Y2 row 0 geometry: L shows 00 01 02 03 _ 04 05 06; R 00 01 02 03
        // 41 04 05 06, ascii strips `.... ...` vs `....A...`.
        let l = seq(64);
        let mut r = l[..4].to_vec();
        r.push(0x41);
        r.extend_from_slice(&l[4..]);
        let body = report_rows(HexLayout::SideBySide, &l, &r);
        assert_eq!(
            body[0],
            "00 01 02 03    04 05 06  .... ... <> 00 01 02 03 41 04 05 06  ....A..."
        );
    }

    #[test]
    fn interleaved_merges_same_rows_splits_diff_rows() {
        // Y6: diff block first row -> two lines, then merged same rows with
        // per-side offsets (00000007 / 00000008).
        let l = seq(16);
        let mut r = l[..4].to_vec();
        r.push(0x41);
        r.extend_from_slice(&l[4..]);
        let body = report_rows(HexLayout::Interleaved, &l, &r);
        // transcribed from runs/m70b Y6-inter (integer audit): the L row
        // carries the slot-4 gap; the R row leads with the blank offset
        assert_eq!(body[0], "00000000          00 01 02 03    04 05 06  .... ...");
        assert_eq!(
            body[1],
            "         00000000 00 01 02 03 41 04 05 06  ....A..."
        );
        assert!(body[3].starts_with("00000007 00000008 07 08 09 0A"), "{:?}", body[3]);
        let rules: Vec<&String> = body.iter().filter(|l| l.starts_with('-')).collect();
        assert_eq!(rules[0].chars().count(), 51);
    }

    #[test]
    fn interleaved_offset_column_is_eight_always() {
        // Z7 (600+1 bytes, right appended at 0x258): offsets stay 8 digits
        let l = seq(600);
        let mut r = l.clone();
        r.push(0xFF);
        let body = report_rows(HexLayout::Interleaved, &l, &r);
        let diff_row = body.iter().find(|l| l.contains("00000258")).unwrap();
        assert!(diff_row.starts_with("         00000258 FF"), "{diff_row:?}");
    }

    #[test]
    fn summary_order_and_zero_omission() {
        // Y7: one paired change -> same + difference lines only, in order.
        let l = seq(64);
        let mut r = l.clone();
        r[4] = 0xFF;
        let body = report_rows(HexLayout::Summary, &l, &r);
        assert_eq!(body[0], "63 same byte(s)");
        assert_eq!(body[1], "1 difference byte(s)");
        assert_eq!(body.len(), 2);
    }

    #[test]
    fn summary_v5_full_four_categories() {
        // runs/m70e2 V5: 56 / 31 / 1 / 1 — pairing model: min(gl,gr) paired
        // changes before orphans is what makes the tail right byte count as
        // one difference instead of left+right orphans.
        let mut l = seq(80);
        l.extend_from_slice(&seq(8));
        let mut r: Vec<u8> = vec![0xFF];
        r.extend_from_slice(&seq(48));
        r.push(0x7E);
        r.extend_from_slice(&seq(8));
        let body = report_rows(HexLayout::Summary, &l, &r);
        assert_eq!(body.len(), 4, "{body:?}");
        assert_eq!(body[0], "56 same byte(s)");
        assert_eq!(body[1], "31 left orphan byte(s)");
        assert_eq!(body[2], "1 right orphan byte(s)");
        assert_eq!(body[3], "1 difference byte(s)");
    }

    #[test]
    fn empty_empty_has_no_body_rows() {
        let body = report_rows(HexLayout::SideBySide, &[], &[]);
        // frame only + final CRLF artifact
        assert!(body.iter().all(|l| l.is_empty()), "{body:?}");
    }

    #[test]
    fn title_replaces_frame_line_one() {
        let l = seq(16);
        let r = seq(16);
        let text = render_hex_report(
            HexLayout::SideBySide,
            &l,
            &r,
            "L",
            "R",
            &stamp(),
            Some("HexTitle"),
        )
        .unwrap();
        assert!(text.starts_with("HexTitle\r\n"));
    }

    #[test]
    fn summary_frame_drops_the_mode_line() {
        let l = seq(16);
        let r = seq(16);
        let text = render_hex_report(
            HexLayout::Summary,
            &l,
            &r,
            "L",
            "R",
            &stamp(),
            None,
        )
        .unwrap();
        assert!(!text.contains("Mode:"));
    }

    #[test]
    fn interleaved_diff_block_emits_left_then_right() {
        // V3 (m70d): the trailing block holds three left-only rows and one
        // right line; the Oracle prints ALL left rows of the block first,
        // then the right line — not interleaved per row.
        // m70d V1 fixtures exactly (integer audit): L = seq(64)+seq(16)
        // (80 bytes); R = FF + seq(59) + 0x41 (62 bytes)
        let mut l: Vec<u8> = (0..64).map(|i| i as u8).collect();
        l.extend_from_slice(&(0..16).map(|i| i as u8).collect::<Vec<_>>());
        let mut r: Vec<u8> = vec![0xFF];
        r.extend_from_slice(&(0..59).map(|i| i as u8).collect::<Vec<_>>());
        r.push(0x41);
        let body = report_rows(HexLayout::Interleaved, &l, &r);
        // The last block's four left-only rows print before the right line
        // (V3 archive line 16-19); a per-row interleave would swap 16/17.
        let last_block: Vec<&String> = body
            .iter()
            .skip(10)
            .take_while(|l| !l.starts_with("----"))
            .collect();
        assert_eq!(last_block.len(), 5, "{:?}", last_block);
        for l in &last_block[..4] {
            assert!(l.starts_with("000000"), "{l}");
        }
        assert!(last_block[4].starts_with("         00000038 "), "{:?}", last_block);
    }

    #[test]
    fn layout_parse_names() {
        assert_eq!(HexLayout::parse("SIDE-BY-SIDE"), Some(HexLayout::SideBySide));
        assert_eq!(HexLayout::parse("interleaved"), Some(HexLayout::Interleaved));
        assert_eq!(HexLayout::parse("summary"), Some(HexLayout::Summary));
        assert_eq!(HexLayout::parse("bogus"), None); // Y8: refused upstream
    }
}

//! The report frame (docs/18 §2/§5).
//!
//! Measured line order (m112 V1/V2, m112b W1):
//!
//! ```text
//! <title | 版本比较(V)>
//! 已产生： <slash date>
//! <blank>
//! [模式：  全部]                       side-by-side ONLY
//! [正在忽略不重要]                      options:ignore-unimportant, before the file lines
//! 左边文件： <L>   /   文件： <path>    (the single-line form when both sides agree)
//! 右边文件： <R>
//! [table: header / rule / rows / rule]  side-by-side ONLY
//! [count lines]                         summary ONLY
//! ```
//!
//! Zero-file shell (m112 V21, 96 bytes): BOM + title + Produced + blank +
//! `模式：  全部` + `基点文件夹： ` -- the same shape as picture's and
//! registry's shell.

use crate::engine::{build_fields, count, Field, Locale, Marker};
use crate::{read_version, VerError, VersionInfo};

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
    /// The `<mode>` word of the Mode line (m112: 全部 / 差异 / 相同, and
    /// `全部, 正在忽略不重要` when ignore-unimportant is set -- m112b W11).
    pub fn mode_text(&self, loc: &Locale, ignore_unimportant: bool) -> String {
        let base = match self {
            Display::All => if loc.is_zh { "全部" } else { "All" },
            Display::Mismatches => if loc.is_zh { "差异" } else { "Differences" },
            Display::Matches => if loc.is_zh { "相同" } else { "Same" },
        };
        if ignore_unimportant {
            let ign = if loc.is_zh { "正在忽略不重要" } else { "Ignoring Unimportant" };
            format!("{base}, {ign}")
        } else {
            base.to_string()
        }
    }
}

/// Everything the frame needs. Grouped in one struct (the registry precedent)
/// so the render functions stay under clippy's argument limit.
pub struct ReportFrame<'a> {
    pub layout: Layout,
    pub display: Display,
    pub ignore_unimportant: bool,
    pub left_path: &'a str,
    pub right_path: &'a str,
    pub stamp: &'a str,
    pub title: Option<&'a str>,
    pub locale: &'a Locale,
}

/// Render the version-report body (frame + table/counts).
pub fn render_version_report(frame: &ReportFrame<'_>, left: &[u8], right: &[u8]) -> String {
    let l = read_version(left).ok();
    let r = read_version(right).ok();
    let fields = build_fields(l.as_ref(), r.as_ref(), frame.locale);
    let kept: Vec<&Field> = filter(&fields, frame.display);
    let counts = count(&fields);
    let loc = frame.locale;

    let mut out: Vec<String> = Vec::new();
    out.push(frame.title.unwrap_or(if loc.is_zh { "版本比较(V)" } else { "Version Compare" }).to_string());
    out.push(format!("{}: {}", if loc.is_zh { "已产生" } else { "Produced" }, frame.stamp));
    out.push(String::new());
    // The ver channel folds ignore-unimportant INTO the sbs Mode line
    // (m112b W11: `模式：  全部, 正在忽略不重要`); the SUMMARY layout has
    // no Mode line and prints a STANDALONE `Ignoring Unimportant` line
    // instead (the v-opt-ignore-unimp golden, lines 0-4).
    if frame.layout == Layout::SideBySide {
        out.push(format!("{}  {}", mode_label(loc), frame.display.mode_text(loc, frame.ignore_unimportant)));
    } else if frame.ignore_unimportant {
        out.push(if loc.is_zh { "正在忽略不重要" } else { "Ignoring Unimportant" }.to_string());
    }
const FILE_LINE_GAP: &str = "     ";

    // The single-line `文件：` form when BOTH sides are the same path
    // (m112 V8).  Otherwise the two file lines PACK onto one line joined by
    // the shared 5-space HEADER_GAP when the combined length fits the
    // pack budget, and split into two lines when it does not:
    //   packed:  hex ZH 83, pic ZH 87, ver EN 98 and 108 (goldens
    //            v-sbs-equal / v-sbs-plain-both)
    //   split:   ver ZH 91+87=178 (m112 V1), reg EN 86+87=173, pic EN 225
    // The exact threshold is an OPEN residual only in general; THIS corpus
    // pins it exactly: v-sbs-plain-both packs at 108 and v-sbs-plain-vs-pe
    // splits at 110, so the boundary is 109.  (The earlier 173/225 splits
    // are consistent; U-ver-2 keeps only the question of which side an
    // exactly-109 line takes.)
    if frame.left_path == frame.right_path {
        out.push(format!("{}{}", file_label(loc), frame.left_path));
    } else {
        let packed = format!(
            "{}{}{}{}{}",
            left_label(loc),
            frame.left_path,
            FILE_LINE_GAP,
            right_label(loc),
            frame.right_path
        );
        if packed.chars().count() <= 109 {
            out.push(packed);
        } else {
            out.push(format!("{}{}", left_label(loc), frame.left_path));
            out.push(format!("{}{}", right_label(loc), frame.right_path));
        }
    }
    match frame.layout {
        Layout::SideBySide => {
            let g = Geometry::compute(&kept, loc.name, loc.value, loc.is_zh);
            out.push(g.header(loc));
            // An EMPTY table (m112 V8: both sides plain) renders the header
            // and a single 10-dash rule, not rule/rows/rule.
            if kept.is_empty() {
                out.push(g.rule());
            } else {
                out.push(g.rule());
                for f in &kept {
                    out.push(g.row(f));
                }
                out.push(g.rule());
            }
        }
        Layout::Summary => {
            for line in count_lines(&counts, loc) {
                out.push(line);
            }
        }
    }
    out.join("\r\n") + "\r\n"
}

/// The zero-file shell (m112 V21).
pub fn render_version_shell(stamp: &str, title: Option<&str>, display: Display, loc: &Locale) -> String {
    let mut out: Vec<String> = Vec::new();
    out.push(format!("\u{feff}{}", title.unwrap_or(if loc.is_zh { "版本比较(V)" } else { "Version Compare" })));
    out.push(format!("{}: {}", if loc.is_zh { "已产生" } else { "Produced" }, stamp));
    out.push(String::new());
    out.push(format!("{}  {}", mode_label(loc), display.mode_text(loc, false)));
    out.push(if loc.is_zh { "基点文件夹： " } else { "Base folder: " }.to_string());
    out.join("\r\n") + "\r\n"
}

fn mode_label(loc: &Locale) -> &'static str {
    if loc.is_zh { "模式：" } else { "Mode:" }
}
fn left_label(loc: &Locale) -> &'static str {
    if loc.is_zh { "左边文件： " } else { "Left file: " }
}
fn right_label(loc: &Locale) -> &'static str {
    if loc.is_zh { "右边文件： " } else { "Right file: " }
}
fn file_label(loc: &Locale) -> &'static str {
    if loc.is_zh { "文件： " } else { "File: " }
}

/// The count lines (m112 V2/V4: "26 个相同项" / "16 个相同项" +
/// "10 个重要的差异项"). Zero categories are omitted.
pub fn count_lines(c: &crate::engine::Counts, loc: &Locale) -> Vec<String> {
    let mut v = Vec::new();
    if c.same > 0 {
        v.push(if loc.is_zh {
            format!("{} 个相同项", c.same)
        } else {
            format!("{} same item(s)", c.same)
        });
    }
    if c.diff > 0 {
        v.push(if loc.is_zh {
            format!("{} 个重要的差异项", c.diff)
        } else {
            format!("{} important difference item(s)", c.diff)
        });
    }
    v
}

fn filter(fields: &[Field], display: Display) -> Vec<&Field> {
    match display {
        Display::All => fields.iter().collect(),
        // Group headers must survive or the table loses its structure.
        Display::Mismatches => fields
            .iter()
            .filter(|f| f.is_group || f.marker != Marker::Same)
            .collect(),
        Display::Matches => fields
            .iter()
            .filter(|f| f.is_group || f.marker == Marker::Same)
            .collect(),
    }
}

/// The solved geometry (docs/18 §6).
///
/// All four columns are CHARACTER indices (not display columns): m112's rows
/// align the right-hand name at the same character index on every row of a
/// table, and the widest glyphs are two columns wide, so a display-column
/// model cannot reproduce the archive.
///
/// The stage identities hold on every archived cell:
///   `rn = ld + LV + 1`, `rd = rn + RN + 1`, `rule = rd + RV`
/// where LV/RN/RV are the VISIBLE maxima of the value / right-name / right
/// value columns, and `ld = LN + 1`.  Two cell families break the `ld` and
/// `rule` identities, and both are the same effect: the side whose value
/// column is the wide one gets a value column derived from the OTHER side's
/// name column.  V5/V24 (left name short, left value 71 wide) show it on
/// `ld`; W8 (left name short, right value 38 wide) shows it on `rule`.
struct Geometry {
    ld: usize,
    /// Where the two-character marker field ends; the marker is right-aligned
    /// inside it, so '=' sits at `mcol - 1` and '<>' at `mcol - 2`.
    mcol: usize,
    rn: usize,
    rd: usize,
    rule: usize,
}

impl Geometry {
    fn compute(fields: &[&Field], loc_name: &str, loc_value: &str, is_zh: bool) -> Geometry {
        let mut ln = 0usize;
        let mut lv = 0usize;
        let mut rnc = 0usize;
        let mut rv = 0usize;
        let mut wide_marker = false;
        let mut any_left = false;
        for f in fields {
            if f.is_group {
                ln = ln.max(f.name.chars().count());
                // A group heading prints in BOTH columns, and each side of the
                // table widens to hold it (m112: `PE 头信息` widens the 名称
                // column on both sides of V1's table).
                rnc = rnc.max(f.name.chars().count());
                continue;
            }
            // A row whose LEFT side is absent contributes nothing to the left
            // columns (m112 V7: a plain-text left side leaves the left half at
            // its minimum: 名称@0, 值@3).
            if f.marker == Marker::LeftSideAbsent {
                rnc = rnc.max(f.name.chars().count());
                rv = rv.max(f.right.chars().count());
                wide_marker = true; // '-+' renders two characters
                continue;
            }
            any_left = true;
            ln = ln.max(f.name.chars().count());
            lv = lv.max(f.left.chars().count());
            // The RIGHT name column only has to hold names that have a right
            // side: a left-only row prints nothing in the right name column
            // (m112 V5: the .com side has no PE header at all, so the right
            // name column is 7 wide while the left one is 25).
            if !matches!(f.marker, Marker::LeftOnly | Marker::LeftAbsent) {
                rnc = rnc.max(f.name.chars().count());
            }
            rv = rv.max(f.right.chars().count());
            if matches!(f.marker, Marker::Diff | Marker::LeftOnly | Marker::RightOnly | Marker::LeftSideAbsent) {
                wide_marker = true;
            }
        }
        // A table that renders no marker at all still needs a slot, and an
        // empty side still needs one column for its name.
        // The measured minimums are the LABEL widths: a name column holds
        // the header label plus one (`名称 ` = 3, `Name ` = 5) and a value
        // column at least the value label's display width (`值` = 2,
        // `Value` = 5) -- m112 V7/V8 vs the verify/ver goldens.
        let name_floor = loc_name.chars().count() + 1;
        let value_floor = dispw(loc_value);
        let ld = if any_left { ln.max(name_floor) + 1 } else { name_floor };
        if fields.is_empty() {
            // V8's shell (header-only) and V7's absent-left table share the
            // minimum header.  Measured value slot: chars(value label) + 2
            // for a narrow-marker table (V8 ZH: 3, V8 EN: 7) and + 4 when a
            // wide marker renders (V7 ZH: 5, V7 EN: 9 -- the '-+' is two
            // characters).  The right name starts at ld+vslot (ZH V8 6, EN
            // V8 12, ZH V7 8, EN V7 14), the right value slot =
            // chars(name)+1 (V8 ZH 9, EN 17), and the rule = rd + rv for
            // V7 (content) / rd + chars(value) for V8.
            let extra = if wide_marker { 2 } else { 0 };
            let vslot = loc_value.chars().count() + 2 + extra;
            let rn0 = ld + vslot;
            let rd0 = rn0 + loc_name.chars().count() + 1;
            return Geometry { ld, mcol: ld, rn: rn0, rd: rd0, rule: rd0 + loc_value.chars().count() };
        }
        // The marker is LEFT-aligned one column after the value text
        // (m112 V1: '=' at 26+68+1 = 95; V6: '<>' at 8+45+1 = 54).
        let lv_min = if any_left { lv.max(value_floor) } else { value_floor };
        // A normal cell leaves one blank column between the value and the
        // marker (V1: 26+68+1=95); an absent-side table packs them (V7:
        // 3+2=5, no blank).
        // The absent-left tables measure a value slot of dispw(value) for
        // ZH (V7: 3+2=5) but dispw(value)+1 for EN (V7: 5+5+1=11) -- an
        // unresolved one-column asymmetry, recorded as U-ver-3 (docs/18).
        let mcol = if any_left {
            ld + lv_min + 1
        } else {
            ld + lv_min + if is_zh { 0 } else { 1 }
        };
        // The right name starts one column past the WIDEST marker the table
        // renders (m112 V1, only '=': 95+1+1 = 97; V3/V6, '<>' present:
        // 95+2+1 = 98 / 54+2+1 = 57; W8 '='-and-'<>': 47+2+1 = 50).  The
        // absent-left tables have no +1: V7's '-+' sits at mcol and the
        // right name is mcol+2 past the marker itself (ZH 5+2+1=8 with a
        // 2-wide marker? measured 8: marker 2 + one gap).
        // The absent-left tables measure a different right-name start:
        // V7 ZH Name@8 = 3 + 1 + 2 + 2 (ld + chars(value) + gap + wide
        // marker) and V7 EN Name@14 = 5 + 5 + 2 + 2 -- the same identity
        // the V8 empty header measures without the wide term (V8 ZH 6 =
        // 3+1+2, V8 EN 12 = 5+5+2).  The any_left tables instead hang the
        // right name off the marker column (V1/V3/V6/W8 above).
        let rn = if any_left {
            mcol + if wide_marker { 2 } else { 1 } + 1
        } else {
            // V7: the marker left-aligns at mcol and the right name starts
            // 3 columns later (ZH '-+'@5 Name@8; EN '-+'@11 Name@14).
            mcol + 3
        };
        let rd = rn + rnc.max(loc_name.chars().count()) + 1;
        let rule = rd + rv;
        Geometry { ld, mcol, rn, rd, rule }
    }

    fn header(&self, loc: &Locale) -> String {
        let mut s = String::new();
        push(&mut s, 0, loc.name);
        push(&mut s, self.ld, loc.value);
        push(&mut s, self.rn, loc.name);
        push(&mut s, self.rd, loc.value);
        trim_end(&mut s);
        s
    }

    fn rule(&self) -> String {
        "-".repeat(self.rule)
    }

    fn row(&self, f: &Field) -> String {
        let mut s = String::new();
        if f.is_group {
            // A group header prints its name in BOTH columns (m112); an
            // ABSENT side renders nothing there (m112b W8: the truncated
            // left side shows a blank before 固定/翻译/变化).  build_fields
            // encodes "absent" as an empty left name or a blank right name.
            if !f.name.is_empty() {
                push(&mut s, 0, &f.name);
            }
            if !f.rname.is_empty() {
                push(&mut s, self.rn, &f.rname);
            }
            trim_end(&mut s);
            return s;
        }
        // A one-sided row prints a bare '|' in the MISSING side's name
        // column: a right-only row has `|` on the left (m112 V5: `|  -+
        // +注释 …`), a left-only row has it on the right (m112b W3:
        // `+注释 … +- |`).
        match f.marker {
            Marker::RightOnly => {
                push(&mut s, 0, "|");
                push(&mut s, self.ld, "");
            }
            // An ABSENT left side leaves the whole left half blank, not even
            // the name (m112b W8's 固定/翻译/变化 rows).
            Marker::LeftSideAbsent => {}
            _ => {
                push(&mut s, 0, &f.name);
                push(&mut s, self.ld, &f.left);
            }
        }
        let marker = match f.marker {
            Marker::Same => "=",
            Marker::Diff => "<>",
            Marker::LeftOnly | Marker::LeftAbsent => "+-",
            Marker::RightOnly | Marker::LeftSideAbsent => "-+",
            Marker::None => "",
        };
        // Every marker is LEFT-aligned at `mcol` (m112 V1 '=' at 95 = ld 26 +
        // value 68 + 1; V6 '<>' at 54; V5's RightOnly '-+' and LeftOnly '+-'
        // also start at the same column).  The right name starts one column
        // past the widest marker.
        if !marker.is_empty() {
            push(&mut s, self.mcol, marker);
        }
        match f.marker {
            // A present-but-empty right side renders '|' in its name column
            // (m112b W3); an ABSENT side leaves the whole right half blank
            // (m112 V5).
            Marker::LeftOnly => push(&mut s, self.rn, "|"),
            Marker::LeftAbsent => {}
            _ => push(&mut s, self.rn, if f.rname.is_empty() { &f.name } else { &f.rname }),
        }
        push(&mut s, self.rd, &f.right);
        trim_end(&mut s);
        s
    }
}

/// The terminal width of a string: CJK glyphs occupy two columns.
///
/// The measured cells prove the Oracle pads by DISPLAY width, not by char
/// count (m112 V1: the widest value is 34 chars / 68 display columns).
pub fn dispw(s: &str) -> usize {
    s.chars().map(|c| if is_wide(c) { 2 } else { 1 }).sum()
}

/// Whether the glyph is rendered double-width (m112: every CJK and
/// fullwidth form the corpus carries).
fn is_wide(c: char) -> bool {
    matches!(c,
        | '\u{1100}'..='\u{115f}'
        | '\u{2e80}'..='\u{a4cf}'
        | '\u{ac00}'..='\u{d7a3}'
        | '\u{f900}'..='\u{faff}'
        | '\u{fe30}'..='\u{fe6f}'
        | '\u{ff00}'..='\u{ff60}'
        | '\u{ffe0}'..='\u{ffe6}')
}

fn push(s: &mut String, col: usize, text: &str) {
    while s.chars().count() < col {
        s.push(' ');
    }
    s.push_str(text);
}

fn trim_end(s: &mut String) {
    while s.ends_with(' ') {
        s.pop();
    }
}

/// Why a side produced no fields at all (m112 V7/V8).
pub fn side_error(bytes: &[u8]) -> Option<VerError> {
    read_version(bytes).err()
}

/// Convenience for the CLI: the VersionInfo of one side, or None.
pub fn info_of(bytes: &[u8]) -> Option<VersionInfo> {
    read_version(bytes).ok()
}



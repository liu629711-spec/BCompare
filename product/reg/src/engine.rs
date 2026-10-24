//! Registry sbs engine: side merge, linguistic order, box-prefix rows,
//! counts, exact column geometry, line assembly. The model is pinned by
//! `tests/corpus_cases.rs` against the 89 archived m101 sbs tables
//! (docs/17 §sbs/§geometry).
//!
//! Bar/connectors model (all measured):
//! * Level 0 = items directly under the (per-side) basekey. Its key headers
//!   print BARE (no connector); orphan level-0 headers too (`Kx`, `Zx`,
//!   `Mid`, F16 `Empty`, T7 `Ky`).
//! * Level >= 1 items print their CONNECTOR: `+` when not the last merged
//!   item of the level, `\` when last (J1 `+K2`/`\x1`, S6 `\B`, F2 `+Deep`).
//! * Ancestor bars when a side prints its OWN content: every stack entry at
//!   level >= 1 with its own connector: '+' -> '|', '\' -> ' '
//!   (J1 `||\x3`/`|\x2`, T6 `||\c`, T9 ` \a`, KG ` \b`, M5 ` \v`). Level-0
//!   ancestors never draw bars on own-content rows (J1 `+K2`, E2 `+Kx`).
//! * The side with NO content on a row inside a matched ancestor that is
//!   still '+'-open draws the continuation: '|' per MATCHED ancestor at ANY
//!   level with side connector '+' (E2 `+Kx              |`, `|\a +- |`);
//!   orphan-branch ancestors do not contribute (T6 `|+Dp2` right blank).
//!   Spaces-only -> blank (T3 `Mid` has no right bar: its only ancestors
//!   are the base, not a matched key).
//! * Key/value order within a level: keys (sorted) THEN values (sorted)
//!   (S2/G8/E5/F8/F9/F10/F11); the level-0 default row `x0`/`top` sorts as
//!   a value AFTER keys (G8/J1).

use crate::collation;
use crate::parse::{KeyNode, RegFile, ValueItem};
use crate::values::Value;

pub const PLACEHOLDER_ZERO: &str = "(零长度二进制值)";
pub const DEFAULT_NAME: &str = "(默认)";

/// The frame's label vocabulary. The Oracle's table geometry floors the
/// name/type/data columns at the HEADER LABEL widths (docs/17 §geometry):
/// the Chinese install uses 2-char labels (floor 2), the English reference
/// install 4-char ones (floor 4) -- measured identically in both installs
/// (zh corpus m101*; EN m101f-regbox-reference F1-orphanend `Name Type
/// Data`). The corpus tests run [`Locale::ZH`] byte-exact; the CLI emits
/// [`Locale::EN`] like the dir/pic channels (norm-5 folds a Chinese golden
/// report onto the English product text).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Locale {
    pub name: &'static str,
    pub type_: &'static str,
    pub data: &'static str,
    pub placeholder_zero: &'static str,
    pub default_name: &'static str,
}

impl Locale {
    pub const ZH: Locale = Locale {
        name: "名称",
        type_: "类型",
        data: "数据",
        placeholder_zero: PLACEHOLDER_ZERO,
        default_name: DEFAULT_NAME,
    };
    pub const EN: Locale = Locale {
        name: "Name",
        type_: "Type",
        data: "Data",
        placeholder_zero: "(zero-length binary value)",
        default_name: "(Default)",
    };
}

/// Data-column text with the MEASURED column width baked in (F13/T1/S1/I8):
/// binary-ish render `XX ` per byte (trailing space counts); EMPTY binary
/// or REG_NONE use the locale placeholder; every other type is plain
/// display text (NUL counts one char: J3 `abc\0` -> 4).
pub fn data_text(v: &Value, loc: &Locale) -> String {
    match v {
        Value::Str(_) | Value::Dword(_) => v.display_text().unwrap_or_default(),
        Value::Binary(b) => {
            if b.is_empty() {
                loc.placeholder_zero.to_string()
            } else {
                b.iter().map(|x| format!("{x:02X} ")).collect()
            }
        }
        Value::Typed { code, bytes } if !matches!(code, 1 | 2 | 7 | 4) => {
            if bytes.is_empty() {
                loc.placeholder_zero.to_string()
            } else {
                bytes.iter().map(|x| format!("{x:02X} ")).collect()
            }
        }
        other => other.display_text().unwrap_or_else(|| loc.placeholder_zero.to_string()),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Marker {
    /// matched key header row (both bare names, no marker text)
    KeyPair,
    /// single-side key header (orphan) row, possibly a continuation bar
    Orphan,
    Same,
    Diff,
    LeftOnly,
    RightOnly,
}

/// One merged table row. Name columns carry the box prefix; type/data only
/// exist on value rows.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SbsRow {
    pub left: Option<Side>,
    pub marker: Marker,
    pub right: Option<Side>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Side {
    pub name: String,
    pub type_: Option<String>,
    pub data: Option<String>,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Counts {
    pub same: usize,
    pub left_orphan: usize,
    pub right_orphan: usize,
    pub diff: usize,
}

#[derive(Debug, Clone)]
pub struct SbsResult {
    pub rows: Vec<SbsRow>,
    pub counts: Counts,
}

fn empty_node() -> KeyNode {
    KeyNode { name: String::new(), values: Vec::new(), children: Vec::new() }
}

enum Item {
    Key { name: String, l: Option<KeyNode>, r: Option<KeyNode> },
    Val { name: String, l: Option<ValueItem>, r: Option<ValueItem> },
}

fn merge_level(l: &KeyNode, r: &KeyNode) -> Vec<Item> {
    let mut keys: Vec<Item> = Vec::new();
    let mut seen: Vec<String> = Vec::new();
    for c in &l.children {
        let f = c.name.to_uppercase();
        if seen.contains(&f) {
            continue;
        }
        seen.push(f);
        let mate = r.children.iter().find(|x| collation::same_name(&x.name, &c.name));
        keys.push(Item::Key { name: c.name.clone(), l: Some(c.clone()), r: mate.cloned() });
    }
    for c in &r.children {
        let f = c.name.to_uppercase();
        if seen.contains(&f) {
            continue;
        }
        seen.push(f);
        keys.push(Item::Key { name: c.name.clone(), l: None, r: Some(c.clone()) });
    }
    keys.sort_by(|a, b| match (a, b) {
        (Item::Key { name: x, .. }, Item::Key { name: y, .. }) => collation::compare(x, y),
        _ => std::cmp::Ordering::Equal,
    });
    let mut vals: Vec<Item> = Vec::new();
    let mut vseen: Vec<String> = Vec::new();
    for v in &l.values {
        let f = v.name.to_uppercase();
        if vseen.contains(&f) {
            continue;
        }
        vseen.push(f);
        let mate = r.values.iter().find(|x| collation::same_name(&x.name, &v.name));
        vals.push(Item::Val { name: v.name.clone(), l: Some(v.clone()), r: mate.cloned() });
    }
    for v in &r.values {
        let f = v.name.to_uppercase();
        if vseen.contains(&f) {
            continue;
        }
        vseen.push(f);
        vals.push(Item::Val { name: v.name.clone(), l: None, r: Some(v.clone()) });
    }
    vals.sort_by(|a, b| match (a, b) {
        (Item::Val { name: x, .. }, Item::Val { name: y, .. }) => collation::compare(x, y),
        _ => std::cmp::Ordering::Equal,
    });
    keys.extend(vals);
    keys
}

/// One ancestor frame on the walk stack.
#[derive(Debug, Clone, Copy)]
struct Anc {
    /// matched on both sides (orphan branches contribute nothing)
    matched: bool,
    /// the shared connector the matched header printed ('+' / '\')
    conn: char,
    /// per side: does that side itself have more items at that level after
    /// this one (only matters for matched, both sides agree by construction
    /// when merged order is used -- stored per side anyway)
    l_open: bool,
    r_open: bool,
}

/// own-content bars: stack entries at level >= 1 (`stack[0]` is the
/// level-0 frame); matched with '+' -> '|', otherwise ' '. Orphan frames
/// contribute bars from THEIR side only.
fn own_bars(stack: &[Anc], side_right: bool, in_orphan_left: bool, in_orphan_right: bool) -> String {
    stack
        .iter()
        .enumerate()
        .skip(1)
        .map(|(_, a)| {
            if a.matched {
                if a.conn == '+' { '|' } else { ' ' }
            } else if in_orphan_left && !side_right {
                // our own orphan branch: bar from its '+' connector
                if a.conn == '+' { '|' } else { ' ' }
            } else if in_orphan_right && side_right {
                if a.conn == '+' { '|' } else { ' ' }
            } else {
                ' '
            }
        })
        .collect()
}

/// continuation for a side with no content: '|' per matched ancestor at any
/// level whose side-open box is '+' (E2). Orphan ancestors contribute
/// nothing.
fn cont_bars(stack: &[Anc], side_right: bool) -> Option<String> {
    let s: String = stack
        .iter()
        .map(|a| {
            if a.matched && a.conn == '+' && if side_right { a.r_open } else { a.l_open } {
                '|'
            } else {
                ' '
            }
        })
        .collect();
    if s.trim().is_empty() {
        None
    } else {
        Some(s)
    }
}

#[derive(Debug, Clone, Copy)]
struct Region {
    /// the current descent sits inside a left-only orphan branch
    in_left_orphan: bool,
    in_right_orphan: bool,
}

/// Build one side's column for a row. The walk context is deliberately flat
/// (stack + region + this row's fields + the locale): bundling it further
/// would obscure the per-row reads. (The same trade the picture channel's
/// `render_picture_report` makes.)
#[allow(clippy::too_many_arguments)]
fn side(
    stack: &[Anc],
    reg: Region,
    depth: usize,
    conn: char,
    side_right: bool,
    name: String,
    v: Option<&Value>,
    loc: &Locale,
) -> Side {
    let name = if name == "@" { loc.default_name.to_string() } else { name };
    let content = if depth == 0 {
        name.clone()
    } else {
        format!("{}{conn}{name}", own_bars(stack, side_right, reg.in_left_orphan, reg.in_right_orphan))
    };
    match v {
        Some(val) => Side {
            name: content,
            type_: Some(val.type_name()),
            data: Some(data_text(val, loc)),
        },
        None => Side { name: content, type_: None, data: None },
    }
}

pub fn compare_sbs(left: &RegFile, right: &RegFile, loc: &Locale) -> SbsResult {
    let mut rows = Vec::new();
    let mut counts = Counts::default();
    walk(
        &side_root(left),
        &side_root(right),
        &mut rows,
        &mut counts,
        &mut Vec::new(),
        0,
        Region { in_left_orphan: false, in_right_orphan: false },
        loc,
    );
    SbsResult { rows, counts }
}

fn side_root(f: &RegFile) -> KeyNode {
    // level 0 = the side's OWN basekey node (G1-sid: left base A vs right
    // base B still align their values); basekey None (error side with no
    // surviving key) -> an empty subtree (G3-sid prints the intact side).
    let rel: Vec<String> = match &f.basekey {
        Some(abs) => abs.split('\\').skip(1).map(|s| s.to_string()).collect(),
        None => return empty_node(),
    };
    if rel.is_empty() {
        return side_root_hive(f);
    }
    match f.node(&rel) {
        Some(n) => n.clone(),
        None => empty_node(),
    }
}

fn side_root_hive(f: &RegFile) -> KeyNode {
    KeyNode { name: String::new(), values: f.base_values.clone(), children: f.roots.clone() }
}

/// Walk one level of both (already-merged) sides in lock step. Flat context
/// arguments for the same reason as [`side`].
#[allow(clippy::too_many_arguments)]
fn walk(
    l: &KeyNode,
    r: &KeyNode,
    rows: &mut Vec<SbsRow>,
    counts: &mut Counts,
    stack: &mut Vec<Anc>,
    depth: usize,
    reg: Region,
    loc: &Locale,
) {
    let items = merge_level(l, r);
    let n = items.len();
    // per-side "still open after this item" uses the side's own level size
    // (keys + values it actually holds at this level)
    let l_total = l.children.len() + l.values.len();
    let r_total = r.children.len() + r.values.len();
    for (idx, item) in items.into_iter().enumerate() {
        let last = idx + 1 == n;
        let conn = if last { '\\' } else { '+' };
        match item {
            Item::Key { name, l: kl, r: kr } => match (kl, kr) {
                (Some(a), Some(b)) => {
                    rows.push(SbsRow {
                        left: Some(side(stack, reg, depth, conn, false, name.clone(), None, loc)),
                        marker: Marker::KeyPair,
                        right: Some(side(stack, reg, depth, conn, true, name.clone(), None, loc)),
                    });
                    stack.push(Anc {
                        matched: true,
                        conn,
                        l_open: idx + 1 < l_total.max(1),
                        r_open: idx + 1 < r_total.max(1),
                    });
                    walk(&a, &b, rows, counts, stack, depth + 1, reg, loc);
                    stack.pop();
                }
                (Some(a), None) => {
                    rows.push(SbsRow {
                        left: Some(side(stack, reg, depth, conn, false, name.clone(), None, loc)),
                        marker: Marker::Orphan,
                        right: cont_bars(stack, true).map(|b| Side {
                            name: b,
                            type_: None,
                            data: None,
                        }),
                    });
                    stack.push(Anc {
                        matched: false,
                        conn,
                        l_open: true,
                        r_open: false,
                    });
                    let inner = Region { in_left_orphan: true, in_right_orphan: false };
                    walk(&a, &empty_node(), rows, counts, stack, depth + 1, inner, loc);
                    stack.pop();
                }
                (None, Some(b)) => {
                    rows.push(SbsRow {
                        left: cont_bars(stack, false).map(|b| Side {
                            name: b,
                            type_: None,
                            data: None,
                        }),
                        marker: Marker::Orphan,
                        right: Some(side(stack, reg, depth, conn, true, name.clone(), None, loc)),
                    });
                    stack.push(Anc {
                        matched: false,
                        conn,
                        l_open: false,
                        r_open: true,
                    });
                    let inner = Region { in_left_orphan: false, in_right_orphan: true };
                    walk(&empty_node(), &b, rows, counts, stack, depth + 1, inner, loc);
                    stack.pop();
                }
                (None, None) => unreachable!("merged item always has one side"),
            },
            Item::Val { name, l: vl, r: vr } => match (vl, vr) {
                (Some(a), Some(b)) => {
                    let same = a.value.compare_identity() == b.value.compare_identity();
                    let marker = if same {
                        counts.same += 1;
                        Marker::Same
                    } else {
                        counts.diff += 1;
                        Marker::Diff
                    };
                    rows.push(SbsRow {
                        left: Some(side(stack, reg, depth, conn, false, name.clone(), Some(&a.value), loc)),
                        marker,
                        right: Some(side(stack, reg, depth, conn, true, name.clone(), Some(&b.value), loc)),
                    });
                }
                (Some(a), None) => {
                    counts.left_orphan += 1;
                    rows.push(SbsRow {
                        left: Some(side(stack, reg, depth, conn, false, name.clone(), Some(&a.value), loc)),
                        marker: Marker::LeftOnly,
                        right: cont_bars(stack, true).map(|b| Side {
                            name: b,
                            type_: None,
                            data: None,
                        }),
                    });
                }
                (None, Some(b)) => {
                    counts.right_orphan += 1;
                    rows.push(SbsRow {
                        left: cont_bars(stack, false).map(|b| Side {
                            name: b,
                            type_: None,
                            data: None,
                        }),
                        marker: Marker::RightOnly,
                        right: Some(side(stack, reg, depth, conn, true, name.clone(), Some(&b.value), loc)),
                    });
                }
                (None, None) => unreachable!(),
            },
        }
    }
}

// ---------------------------------------------------------------- geometry

#[derive(Debug, Clone, Copy)]
pub struct Geometry {
    pub lt: usize,
    pub ld: usize,
    pub mcol: usize,
    pub mlen: usize,
    pub rn: usize,
    pub rt: usize,
    pub rd: usize,
    pub rule: usize,
}

fn clen(s: &str) -> usize {
    s.chars().count()
}

/// Measured column formulas (docs/17 §geometry). Every floor is the
/// HEADER LABEL width of the locale (Chinese 名称/类型/数据 = 2 each,
/// English Name/Type/Data = 4 each -- verified on both installs: the EN
/// reference corpus floors `ln/tw/dw` at 4 while the ZH corpus floors them
/// at 2; content widths dominate whenever larger):
///   lt = max(fl_n, maxLn) + 1; ld = lt + max(fl_t, maxTw) + 1;
///   mcol = ld + max(fl_d, maxLd) + 1; mlen = 0 header-only / 1 '=' / 2 any
///   of <> +- -+; rn = mcol + mlen + 1; rt = rn + max(fl_n, maxRn) + 1;
///   rd = rt + max(fl_t, maxTw) + 1; rule = rd + max(fl_d, maxRd).
pub fn compute_geometry(rows: &[SbsRow], loc: &Locale) -> Geometry {
    let fl_n = clen(loc.name);
    let fl_t = clen(loc.type_);
    let fl_d = clen(loc.data);
    let mut ln = fl_n;
    let mut rnm = fl_n;
    let mut tw = fl_t;
    let mut dwl = fl_d;
    let mut dwr = fl_d;
    let mut mlen = 0;
    for r in rows {
        for (s, is_left) in [(&r.left, true), (&r.right, false)] {
            if let Some(s) = s {
                if is_left {
                    ln = ln.max(clen(&s.name));
                    if let Some(d) = &s.data {
                        dwl = dwl.max(clen(d));
                    }
                } else {
                    rnm = rnm.max(clen(&s.name));
                    if let Some(d) = &s.data {
                        dwr = dwr.max(clen(d));
                    }
                }
                if let Some(t) = &s.type_ {
                    tw = tw.max(clen(t));
                }
            }
        }
        mlen = mlen.max(match r.marker {
            Marker::KeyPair | Marker::Orphan => 0,
            Marker::Same => 1,
            _ => 2,
        });
    }
    let lt = ln + 1;
    let ld = lt + tw + 1;
    let mcol = ld + dwl + 1;
    let rn = mcol + mlen + 1;
    let rt = rn + rnm + 1;
    let rd = rt + tw + 1;
    let rule = rd + dwr;
    Geometry { lt, ld, mcol, mlen, rn, rt, rd, rule }
}

fn push_at(s: &mut String, col: usize, text: &str) {
    while clen(s) < col {
        s.push(' ');
    }
    s.push_str(text);
}

pub fn render_header(g: &Geometry, loc: &Locale) -> String {
    let mut s = String::new();
    push_at(&mut s, 0, loc.name);
    push_at(&mut s, g.lt, loc.type_);
    push_at(&mut s, g.ld, loc.data);
    push_at(&mut s, g.rn, loc.name);
    push_at(&mut s, g.rt, loc.type_);
    push_at(&mut s, g.rd, loc.data);
    s
}

pub fn render_rule(g: &Geometry) -> String {
    "-".repeat(g.rule)
}

/// Assemble one row line; the result is rstripped (left-only rows drop
/// trailing blanks; a right continuation bar stays at rn).
pub fn render_line(r: &SbsRow, g: &Geometry) -> String {
    let mut s = String::new();
    if let Some(l) = &r.left {
        push_at(&mut s, 0, &l.name);
        if let Some(t) = &l.type_ {
            push_at(&mut s, g.lt, t);
        }
        if let Some(d) = &l.data {
            push_at(&mut s, g.ld, d);
        }
    }
    if let Some(m) = match r.marker {
        Marker::Same => Some("="),
        Marker::Diff => Some("<>"),
        Marker::LeftOnly => Some("+-"),
        Marker::RightOnly => Some("-+"),
        Marker::KeyPair | Marker::Orphan => None,
    } {
        push_at(&mut s, g.mcol, m);
    }
    if let Some(rt) = &r.right {
        push_at(&mut s, g.rn, &rt.name);
        if let Some(t) = &rt.type_ {
            push_at(&mut s, g.rt, t);
        }
        if let Some(d) = &rt.data {
            push_at(&mut s, g.rd, d);
        }
    }
    // binary data text keeps its measured per-byte trailing space (column
    // width); the line's trailing blanks are trimmed, and a trailing NUL
    // that lands at line END is also stripped (measured: S1 ms7/F13 ms/J3
    // right rows lose the MULTI_SZ trailing \0; the same \0 survives when
    // column padding follows it, e.g. left rows) -- the Oracle rstrips the
    // line of whitespace AND the end-of-line NUL.
    s.trim_end_matches([' ', '\u{0}']).to_string()
}

/// Render the full sbs table body INCLUDING header/rule lines.
pub fn render_table(rows: &[SbsRow], loc: &Locale) -> Vec<String> {
    let g = compute_geometry(rows, loc);
    let mut out = Vec::with_capacity(rows.len() + 3);
    out.push(render_header(&g, loc));
    out.push(render_rule(&g));
    for r in rows {
        out.push(render_line(r, &g));
    }
    out.push(render_rule(&g));
    out
}

/// Compare two sides and render only the table BODY lines (no header/rule):
/// the shape the archived reports carry between the rules.
pub fn render_body_lines(left: &RegFile, right: &RegFile, loc: &Locale) -> Vec<String> {
    let res = compare_sbs(left, right, loc);
    let g = compute_geometry(&res.rows, loc);
    res.rows.iter().map(|r| render_line(r, &g)).collect()
}

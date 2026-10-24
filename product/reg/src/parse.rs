//! The .reg text model: encoding sniff, logical-line grammar, per-side
//! notes/errors, and the measured basekey rule.
//!
//! Every rule here maps to a measured cell in `product/verify/runs/m101*`
//! (docs/17); nothing is inferred from documentation alone.

use super::collation;
use super::values::Value;

/// A file-level condition rendered as a frame note line.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParseNote {
    /// `删除/重复跳过` / "Deletes/Duplicates Skipped" (m101b C8, m101e I6,
    /// m101f F7, m101g S1, m101n N8: value `=-`, `[-key]` lines, and
    /// folded-duplicate key/value lines each set this note, once per side).
    DeletesDuplicatesSkipped,
}

/// A per-side failure. The frame renders these as `Left/Right error: …`
/// lines (docs/17 §2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RegError {
    /// `解析错误 (行： 列)` / "Parsing Error (line: col)", 1-based. Column:
    /// the first non-space column when the line cannot START a statement
    /// (m101b C10 `(4:1)`, m101e I5 `(5:1)`, m101b C6 `(5:3)`); the column
    /// just past the raw line end when the statement starts well but is
    /// malformed inside (m101e T2 `(5:8)` for `  "bbb"`). A bad line STOPS
    /// parsing; items parsed before it SURVIVE (C10 vs I5).
    Parsing { line: usize, col: usize },
    /// `不被支持的类型` / "Unsupported Type": no recognized header (m101n
    /// N4/N9), or a recognized header with no surviving key (m101n N10).
    /// The file line then prints NO basekey suffix (G3/N4/N10).
    UnsupportedType,
    /// `文件编码错误 (第 1 行)` / "File Encoding Error (Line 1)": the raw
    /// bytes are not a text encoding at all. Measured on the PNG pair
    /// (m101 R19, m101i I7): the sniff rule is a UTF-16/UTF-8 BOM, else a
    /// raw NUL byte anywhere in the file (binary payload); a file with
    /// neither is decoded as text (UTF-8, else ANSI) even if its content is
    /// garbage (N4/N9 -> Unsupported Type, NOT Encoding).
    Encoding { line: usize },
}

/// One value under a key. The default value (`@`) uses the name `"@"`
/// internally; the display name `(默认)`/`(Default)` lives in the renderer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValueItem {
    pub name: String,
    pub value: Value,
}

/// One key node in the relative tree (below the hive component).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KeyNode {
    /// the segment as spelled when first seen (case is display truth)
    pub name: String,
    pub values: Vec<ValueItem>,
    pub children: Vec<KeyNode>,
}

impl KeyNode {
    fn new(name: &str) -> Self {
        KeyNode { name: name.to_string(), values: Vec::new(), children: Vec::new() }
    }

    fn child_mut(&mut self, seg: &str) -> &mut KeyNode {
        match self.children.iter().position(|c| collation::same_name(&c.name, seg)) {
            Some(i) => &mut self.children[i],
            None => {
                self.children.push(KeyNode::new(seg));
                self.children.last_mut().unwrap()
            }
        }
    }

    fn find(&self, path: &[String]) -> Option<&KeyNode> {
        match path.split_first() {
            None => Some(self),
            Some((head, rest)) => self
                .children
                .iter()
                .find(|c| collation::same_name(&c.name, head))
                .and_then(|c| c.find(rest)),
        }
    }

    fn child_mut_walk(&mut self, path: &[String]) -> &mut KeyNode {
        match path.split_first() {
            None => self,
            Some((head, rest)) => self.child_mut(head).child_mut_walk(rest),
        }
    }
}

/// A parsed side.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RegFile {
    /// the hive component of the first key line (e.g. `HKEY_CURRENT_USER`)
    pub hive: Option<String>,
    /// absolute base path joined with `\` INCLUDING the hive component
    /// (measured rule at [`RegFile::compute_basekey`]); `None` when the side
    /// errored before any key survived.
    pub basekey: Option<String>,
    /// relative depth-1 key nodes, in first-seen order
    pub roots: Vec<KeyNode>,
    /// values attached directly to the basekey itself
    pub base_values: Vec<ValueItem>,
    pub error: Option<RegError>,
    pub note: Option<ParseNote>,
    /// absolute (hive+relative) path of every key that has ≥1 value,
    /// first-seen spelling
    pub valued: Vec<Vec<String>>,
    /// same for every EXPLICITLY listed key line (implicit intermediates of
    /// a deeper key line are NOT listed -- m101m M1: basekey = the full
    /// listed path even through unlisted `P`)
    pub all_keys: Vec<Vec<String>>,
    /// relative path of the key value lines currently attach to
    pub current: Vec<String>,
}

impl RegFile {
    fn empty() -> Self {
        RegFile {
            hive: None,
            basekey: None,
            roots: Vec::new(),
            base_values: Vec::new(),
            error: None,
            note: None,
            valued: Vec::new(),
            all_keys: Vec::new(),
            current: Vec::new(),
        }
    }

    fn abs(&self, rel: &[String]) -> Vec<String> {
        // a listed key line always starts with a hive root; a DIFFERENT hive
        // from the first line stays a full relative path (multi-root file,
        // unobserved beyond F15 where each side had one root)
        match &self.hive {
            Some(h) if rel.first().map(|s| s.to_uppercase()) == Some(h.to_uppercase()) => {
                let mut v = vec![h.clone()];
                v.extend_from_slice(&rel[1..]);
                v
            }
            _ => rel.to_vec(),
        }
    }

    fn note_skip(&mut self) {
        self.note = Some(ParseNote::DeletesDuplicatesSkipped);
    }

    fn insert_key_line(&mut self, full_rel: &[String]) {
        if self.hive.is_none() {
            self.hive = Some(full_rel[0].clone());
        }
        let abs = self.abs(full_rel);
        if self.all_keys.iter().any(|k| same_path(k, &abs)) {
            self.note_skip();
            self.current = full_rel.to_vec();
            return;
        }
        self.all_keys.push(abs);
        // tree path BELOW the hive (multi-hive lines keep their own hive
        // segment as an ordinary root child -- F15)
        let tree_path: Vec<String> = if self.hive_matches(&full_rel[0]) {
            full_rel[1..].to_vec()
        } else {
            full_rel.to_vec()
        };
        if !tree_path.is_empty() {
            let (head, rest) = tree_path.split_first().unwrap();
            let node = self.roots.entry_by(head).child_mut_walk(rest);
            let _ = node;
        }
        // `current` is ALWAYS the hive-inclusive listed path (the same form
        // `abs`/valued use); tree lookups strip the hive on demand.
        self.current = full_rel.to_vec();
    }

    fn hive_matches(&self, seg: &str) -> bool {
        self.hive
            .as_deref()
            .map(|h| h.to_uppercase() == seg.to_uppercase())
            .unwrap_or(false)
    }

    fn insert_value_line(&mut self, name: String, value: Value, line: usize) -> Result<(), RegError> {
        if self.hive.is_none() {
            // a value before any key line: statement starts well, fails
            // inside -- end-of-line column (mirrors the T2 rule; unobserved)
            return Err(RegError::Parsing { line, col: 1 });
        }
        let abs = self.abs(&self.current.clone());
        let rel = self.tree_current();
        let dup = if rel.is_empty() {
            self.base_values.iter().any(|v| collation::same_name(&v.name, &name))
        } else {
            self.node(&rel)
                .map(|n| n.values.iter().any(|v| collation::same_name(&v.name, &name)))
                .unwrap_or(false)
        };
        if dup {
            self.note_skip();
            return Ok(());
        }
        let item = ValueItem { name, value };
        if rel.is_empty() {
            self.base_values.push(item);
        } else {
            let (head, rest) = rel.split_first().unwrap();
            self.roots.entry_by(head).child_mut_walk(rest).values.push(item);
        }
        if !self.valued.iter().any(|k| same_path(k, &abs)) {
            self.valued.push(abs);
        }
        Ok(())
    }

    /// the current listed path with the hive component stripped (tree
    /// coordinates); multi-hive lines keep their hive segment.
    fn tree_current(&self) -> Vec<String> {
        if self.current.is_empty() {
            return Vec::new();
        }
        if self.hive_matches(&self.current[0]) {
            self.current[1..].to_vec()
        } else {
            self.current.clone()
        }
    }

    /// Look up a node by TREE coordinates (paths below the hive; the first
    /// element names a `roots` child).
    pub fn node(&self, rel: &[String]) -> Option<&KeyNode> {
        let (head, rest) = rel.split_first()?;
        self.roots
            .iter()
            .find(|c| collation::same_name(&c.name, head))
            .and_then(|c| c.find(rest))
    }

    /// Measured rule (pinned across G2/J1/F12/M1–M5/M7/T9/F16/KI and
    /// m101n N7): pool = every key path with at least one value; when NO
    /// key has any value, pool = every explicitly listed key path. The
    /// basekey = case-folded common prefix of the pool, spelled with the
    /// FIRST pool entry's segments.
    fn compute_basekey(&mut self) {
        let pool: Vec<Vec<String>> = if self.valued.is_empty() {
            self.all_keys.clone()
        } else {
            self.valued.clone()
        };
        self.basekey = common_prefix(&pool).map(|p| p.join("\\"));
    }
}

/// trait-free helper: find-or-create a depth-1 root by folded name.
trait RootsEntry {
    fn entry_by(&mut self, seg: &str) -> &mut KeyNode;
}
impl RootsEntry for Vec<KeyNode> {
    fn entry_by(&mut self, seg: &str) -> &mut KeyNode {
        match self.iter().position(|c| collation::same_name(&c.name, seg)) {
            Some(i) => &mut self[i],
            None => {
                self.push(KeyNode::new(seg));
                self.last_mut().unwrap()
            }
        }
    }
}

fn same_path(a: &[String], b: &[String]) -> bool {
    a.len() == b.len()
        && a.iter().zip(b).all(|(x, y)| collation::same_name(x, y))
}

/// Decode bytes as the Oracle's text model does (m101b C11): UTF-16LE/BE
/// with BOM, UTF-8 with/without BOM, or ANSI (Latin-1 passthrough so every
/// byte round-trips for byte-faithful display).
fn decode_text(bytes: &[u8]) -> Option<String> {
    if bytes.starts_with(&[0xFF, 0xFE]) {
        let u16s: Vec<u16> = bytes[2..]
            .chunks(2)
            .filter_map(|c| c.get(..2))
            .map(|c| u16::from_le_bytes([c[0], c[1]]))
            .collect();
        return String::from_utf16(&u16s).ok();
    }
    if bytes.starts_with(&[0xFE, 0xFF]) {
        let u16s: Vec<u16> = bytes[2..]
            .chunks(2)
            .filter_map(|c| c.get(..2))
            .map(|c| u16::from_be_bytes([c[0], c[1]]))
            .collect();
        return String::from_utf16(&u16s).ok();
    }
    let body = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]).unwrap_or(bytes);
    match std::str::from_utf8(body) {
        Ok(s) => Some(s.to_string()),
        Err(_) => Some(body.iter().map(|&b| b as char).collect()),
    }
}

/// Parse one side from raw bytes. The ENCODING sniff runs first (R19/I7):
/// a UTF-16/UTF-8 BOM marks text; with no BOM, a raw NUL byte anywhere
/// means the payload is binary (the PNG signature line itself is full of
/// them) and the side reports `File Encoding Error (Line 1)`. Everything
/// else decodes as text and goes through the header grammar (N4/N9's
/// garbage-but-text is Unsupported Type, NOT Encoding).
pub fn parse_reg(bytes: &[u8]) -> RegFile {
    let bom = bytes.starts_with(&[0xFF, 0xFE])
        || bytes.starts_with(&[0xFE, 0xFF])
        || bytes.starts_with(&[0xEF, 0xBB, 0xBF]);
    if !bom && bytes.contains(&0) {
        let mut f = RegFile::empty();
        f.error = Some(RegError::Encoding { line: 1 });
        return f;
    }
    match decode_text(bytes) {
        Some(t) => parse_reg_text(&t),
        None => {
            let mut f = RegFile::empty();
            f.error = Some(RegError::UnsupportedType);
            f
        }
    }
}

/// Line splitting: CRLF/LF are breaks; a lone CR is NOT a break (it stays in
/// the logical line, which `parse_value` maps to U+0000 -- m101n N6).
fn split_lines(text: &str) -> Vec<(usize, String)> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut line = 1usize;
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '\n' => {
                out.push((line, std::mem::take(&mut cur)));
                line += 1;
            }
            '\r' if chars.peek() == Some(&'\n') => {}
            c => cur.push(c),
        }
    }
    if !cur.is_empty() {
        out.push((line, cur));
    }
    out
}

fn first_nonspace_col(raw: &str) -> usize {
    raw.chars().take_while(|c| c.is_whitespace()).count() + 1
}

/// Comma-continuation is NOT joined (measured): the Oracle stops at an
/// indented data line exactly like any other fresh statement. T1's left file
/// (`hex:68,65,6c,6c,6f,` + `  2c,20,...`) -> the value survives with the
/// FIRST line's 5 bytes and the side reports `解析错误 (5： 3)`; C6 is the
/// same without the trailing comma (archived m101g T1-comma-sbs).
///
/// Parse one side from text.
pub fn parse_reg_text(text: &str) -> RegFile {
    let mut file = RegFile::empty();
    let lines = split_lines(text);

    let mut idx = 0;
    while idx < lines.len() && lines[idx].1.trim().is_empty() {
        idx += 1;
    }
    let header_ok = idx < lines.len()
        && matches!(
            lines[idx].1.trim_end(),
            "Windows Registry Editor Version 5.00" | "REGEDIT4"
        );
    if idx >= lines.len() || !header_ok {
        file.error = Some(RegError::UnsupportedType);
        return file;
    }
    idx += 1;

    while idx < lines.len() {
        let (lnum, raw) = lines[idx].clone();
        let trimmed = raw.trim().to_string();
        idx += 1;
        if trimmed.is_empty() {
            continue;
        }
        match apply_statement(&raw, lnum, &mut file) {
            Ok(()) => {}
            Err(e) => {
                file.error = Some(e);
                break;
            }
        }
    }

    if file.error.is_none() && file.roots.is_empty() && file.base_values.is_empty()
        && file.all_keys.is_empty()
    {
        // header but no surviving key line -> UnsupportedType, no suffix
        // (m101n N10)
        file.error = Some(RegError::UnsupportedType);
        return file;
    }
    // The suffix survives a parse error whenever a key line did too: G3
    // (m101c) kept `:\\ReaProbe` on the Parsing-error side, while the side
    // where NO key survived lost the suffix (pool empty -> basekey None).
    file.compute_basekey();
    file
}

/// Apply one complete logical statement line.
fn apply_statement(logical: &str, line: usize, file: &mut RegFile) -> Result<(), RegError> {
    let trimmed = logical.trim();
    let end_col = || logical.chars().count() + 1;
    let start_col = || first_nonspace_col(logical);
    if trimmed.starts_with('[') {
        if !trimmed.ends_with(']') {
            return Err(RegError::Parsing { line, col: end_col() });
        }
        let body = &trimmed[1..trimmed.len() - 1];
        if body.starts_with('-') {
            // deletion line: skipped (m101b C8, m101f F7 header)
            file.note_skip();
            return Ok(());
        }
        let path: Vec<String> = body.split('\\').map(|s| s.to_string()).collect();
        if path.len() < 2 || path.iter().any(|s| s.is_empty()) {
            return Err(RegError::Parsing { line, col: start_col() });
        }
        file.insert_key_line(&path);
        return Ok(());
    }
    if trimmed.starts_with('"') || trimmed.starts_with('@') {
        let (name, payload) = split_value_line(trimmed, line, end_col)?;
        if payload == "-" {
            // value deletion "name"=-: skip (m101g S1)
            file.note_skip();
            return Ok(());
        }
        let value = parse_value(&payload, line, end_col)?;
        return file.insert_value_line(name, value, line);
    }
    Err(RegError::Parsing { line, col: start_col() })
}

fn split_value_line(
    trimmed: &str,
    line: usize,
    end_col: impl Fn() -> usize,
) -> Result<(String, String), RegError> {
    if let Some(rest) = trimmed.strip_prefix('@') {
        let rest = rest.trim_start();
        if !rest.starts_with('=') {
            return Err(RegError::Parsing { line, col: end_col() });
        }
        return Ok(("@".to_string(), rest[1..].trim().to_string()));
    }
    let chars: Vec<char> = trimmed.chars().collect();
    debug_assert_eq!(chars[0], '"');
    let mut name = String::new();
    let mut i = 1;
    let mut closed = false;
    while i < chars.len() {
        match chars[i] {
            '\\' if i + 1 < chars.len() && chars[i + 1] == '"' => {
                name.push('"');
                i += 2;
            }
            '"' => {
                closed = true;
                i += 1;
                break;
            }
            c => {
                name.push(c);
                i += 1;
            }
        }
    }
    if !closed {
        return Err(RegError::Parsing { line, col: end_col() });
    }
    let after: String = chars[i..].iter().collect();
    let after = after.trim_start();
    if !after.starts_with('=') {
        return Err(RegError::Parsing { line, col: end_col() });
    }
    Ok((name, after[1..].trim().to_string()))
}

fn parse_value(payload: &str, line: usize, end_col: impl Fn() -> usize) -> Result<Value, RegError> {
    if payload.starts_with('"') {
        let chars: Vec<char> = payload.chars().collect();
        let mut s = String::new();
        let mut i = 1;
        let mut closed = false;
        while i < chars.len() {
            match chars[i] {
                '\\' if i + 1 < chars.len() && chars[i + 1] == '"' => {
                    s.push('"');
                    i += 2;
                }
                '\\' if i + 1 < chars.len() && chars[i + 1] == '\\' => {
                    s.push('\\');
                    i += 2;
                }
                '"' => {
                    closed = true;
                    break;
                }
                // lone CR inside data -> U+0000 (m101n N6 ords)
                '\r' => {
                    s.push('\u{0}');
                    i += 1;
                }
                c => {
                    s.push(c);
                    i += 1;
                }
            }
        }
        if !closed {
            return Err(RegError::Parsing { line, col: end_col() });
        }
        return Ok(Value::Str(s));
    }
    if let Some(hex) = payload.strip_prefix("dword:") {
        let v = u32::from_str_radix(hex, 16)
            .map_err(|_| RegError::Parsing { line, col: end_col() })?;
        return Ok(Value::Dword(v));
    }
    if let Some(rest) = payload.strip_prefix("hex(") {
        let close = rest
            .find(')')
            .ok_or_else(|| RegError::Parsing { line, col: end_col() })?;
        // The code digits are parsed as HEX: m101d S1 `hex(11)` displayed
        // the literal type `0x11` (decimal 17 rendered), not 0x0B.
        let code: u32 = u32::from_str_radix(&rest[..close], 16)
            .map_err(|_| RegError::Parsing { line, col: end_col() })?;
        let after = rest[close + 1..]
            .trim_start()
            .strip_prefix(':')
            .ok_or_else(|| RegError::Parsing { line, col: end_col() })?;
        return Ok(Value::Typed { code, bytes: parse_hex_bytes(after) });
    }
    if let Some(rest) = payload.strip_prefix("hex:") {
        return Ok(Value::Binary(parse_hex_bytes(rest)));
    }
    Err(RegError::Parsing { line, col: end_col() })
}

fn parse_hex_bytes(rest: &str) -> Vec<u8> {
    rest.split(',')
        .map(|t| t.trim())
        .filter(|t| !t.is_empty())
        .filter_map(|t| u8::from_str_radix(t, 16).ok())
        .collect()
}

fn common_prefix(paths: &[Vec<String>]) -> Option<Vec<String>> {
    if paths.is_empty() {
        return None;
    }
    let mut common = paths[0].clone();
    for p in &paths[1..] {
        let mut n = 0;
        while n < common.len()
            && n < p.len()
            && common[n].to_uppercase() == p[n].to_uppercase()
        {
            n += 1;
        }
        common.truncate(n);
    }
    Some(common)
}

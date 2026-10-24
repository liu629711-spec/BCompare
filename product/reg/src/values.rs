//! Value types and the measured display strings (docs/17 §values).

/// One registry value as parsed from a `.reg` payload.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Value {
    /// quoted `"..."` string (REG_SZ)
    Str(String),
    /// `dword:XXXXXXXX`
    Dword(u32),
    /// `hex:...` (REG_BINARY)
    Binary(Vec<u8>),
    /// `hex(N):...` typed blob (m101n N3: code 3 displays as REG_BINARY,
    /// unknown codes display as the literal `0xNN` type)
    Typed { code: u32, bytes: Vec<u8> },
}

impl Value {
    /// The type-column text, measured in m101d S1 / m101n N3:
    /// 0→REG_NONE, 1→REG_SZ, 2→REG_EXPAND_SZ, 3→REG_BINARY (NOT the 3-type
    /// name), 7→REG_MULTI_SZ, dword→REG_DWORD, bare hex→REG_BINARY,
    /// anything else→`0x{code:02X}` uppercase.
    pub fn type_name(&self) -> String {
        match self {
            Value::Str(_) => "REG_SZ".into(),
            Value::Dword(_) => "REG_DWORD".into(),
            Value::Binary(_) => "REG_BINARY".into(),
            Value::Typed { code, .. } => match code {
                0 => "REG_NONE".into(),
                1 => "REG_SZ".into(),
                2 => "REG_EXPAND_SZ".into(),
                3 => "REG_BINARY".into(),
                // m101n N3: hex(4) displays REG_DWORD with the decoded value
                4 => "REG_DWORD".into(),
                7 => "REG_MULTI_SZ".into() ,
                other => format!("0x{:02X}", other),
            },
        }
    }

    /// The data-column bytes as Unicode text. The placeholder for empty
    /// binary (measured m101e I8: zh `(零长度二进制值)` / en
    /// `(zero-length binary value)`) is locale text supplied by the report
    /// layer; here empty data returns the sentinel `None`.
    ///
    /// Display rules (all measured):
    /// * REG_SZ / hex(1): the single string, NULs dropped;
    /// * hex(2) REG_EXPAND_SZ / hex(7) REG_MULTI_SZ: UTF-16LE decode split
    ///   at NUL; MULTI_SZ displays the strings CONCATENATED with one trailing
    ///   NUL kept (m101j J3 ords `abc\0`; the line-end copy loses it to
    ///   rstrip -- that is the renderer's problem);
    /// * REG_DWORD: `0x{v:08X} ({v})` with UNSIGNED decimal (m101j J7:
    ///   ffffffff → 4294967295);
    /// * binary and unknown types: uppercase hex bytes space-separated
    ///   (m101n N3: `01 00 00 00 02`, `AB CD`).
    ///
    /// EMPTY binary-ish data returns `None`: the frame renders a localized
    /// placeholder `(零长度二进制值)`/`(zero-length binary value)` there
    /// (m101e I8, m101f F13, N3 hex(0)), and the text is the renderer's
    /// locale vocabulary, not data.
    pub fn display_text(&self) -> Option<String> {
        match self {
            Value::Str(s) => Some(s.clone()),
            Value::Dword(v) => Some(format!("0x{v:08X} ({v})")),
            Value::Binary(b) if b.is_empty() => None,
            Value::Binary(b) => Some(hex_data(b)),
            Value::Typed { code, bytes } => {
                if bytes.is_empty() {
                    return None;
                }
                match code {
                    1 | 2 => Some(utf16le_joined(bytes, false)),
                    7 => {
                        // strings concatenated + trailing NUL (m101j J3)
                        let mut s = utf16le_joined(bytes, true);
                        s.push('\u{0}');
                        Some(s)
                    }
                    // m101n N3: hex(4):0a,00,00,00 displays the little-endian
                    // dword `0x0000000A (10)`
                    4 => {
                        let mut b = [0u8; 4];
                        b[..bytes.len().min(4)].copy_from_slice(&bytes[..bytes.len().min(4)]);
                        let v = u32::from_le_bytes(b);
                        Some(format!("0x{v:08X} ({v})"))
                    }
                    _ => Some(hex_data(bytes)),
                }
            }
        }
    }

    /// Identity for value comparison: what the engine treats as equal data.
    /// REG_SZ "ab" (quoted) vs hex(1):61,00,62,00,00,00 both display `ab`
    /// (m101d S1 ms1 vs str rows) -- display text is the measured equality
    /// surface, so compare that.
    pub fn compare_identity(&self) -> String {
        format!("{}|{}", self.type_name(), self.display_text().unwrap_or_default())
    }
}

fn hex_data(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|b| format!("{b:02X}"))
        .collect::<Vec<_>>()
        .join(" ")
}

/// Decode UTF-16LE code units; split runs at U+0000. `keep_all` concatenates
/// every string (MULTI_SZ display), otherwise only the first (SZ/EXPAND_SZ).
fn utf16le_joined(bytes: &[u8], keep_all: bool) -> String {
    let units: Vec<u16> = bytes
        .chunks(2)
        .filter_map(|c| c.get(..2))
        .map(|c| u16::from_le_bytes([c[0], c[1]]))
        .collect();
    let mut out = String::new();
    let mut cur: Vec<u16> = Vec::new();
    for &u in &units {
        if u == 0 {
            if !keep_all && !out.is_empty() {
                return out;
            }
            if !cur.is_empty() {
                out.push_str(&String::from_utf16_lossy(&cur));
                cur.clear();
            }
        } else {
            cur.push(u);
        }
    }
    if !cur.is_empty() {
        out.push_str(&String::from_utf16_lossy(&cur));
    }
    out
}

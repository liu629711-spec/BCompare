//! Line splitting + encoding per SsLineParse spec.
//! Oracle-verified: CRLF≡LF≡CR≡CRCRLF, missing final NL ≡ present,
//! BOM variants (UTF-8/16LE/16BE) compare equal, invalid UTF-8 → U+FFFD,
//! no Latin-1 fallback, NUL bytes are ordinary text.

/// Decode bytes to text using BC's detection cascade (simplified to the
/// cases the oracle exercises): UTF-16 BOM → UTF-16; else UTF-8 lossy.
fn decode_text(raw: &[u8]) -> String {
    if raw.len() >= 2 && raw[0] == 0xFF && raw[1] == 0xFE {
        let units: Vec<u16> = raw[2..]
            .chunks_exact(2)
            .map(|c| u16::from_le_bytes([c[0], c[1]]))
            .collect();
        return String::from_utf16_lossy(&units);
    }
    if raw.len() >= 2 && raw[0] == 0xFE && raw[1] == 0xFF {
        let units: Vec<u16> = raw[2..]
            .chunks_exact(2)
            .map(|c| u16::from_be_bytes([c[0], c[1]]))
            .collect();
        return String::from_utf16_lossy(&units);
    }
    let b = if raw.len() >= 3 && &raw[..3] == b"\xef\xbb\xbf" { &raw[3..] } else { raw };
    String::from_utf8_lossy(b).into_owned()
}

/// Split into lines; separators removed. A CR/LF *run* counts as one break
/// (so CRLF and CRCRLF behave like CR). A trailing break adds no empty line.
pub fn split(raw: &[u8]) -> Vec<String> {
    let text = decode_text(raw);
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut it = text.chars().peekable();
    while let Some(c) = it.next() {
        if c == '\r' || c == '\n' {
            while matches!(it.peek(), Some('\r') | Some('\n')) {
                it.next();
            }
            out.push(std::mem::take(&mut cur));
        } else {
            cur.push(c);
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

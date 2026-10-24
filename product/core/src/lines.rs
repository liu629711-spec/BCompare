//! M1.2 — byte decoding (codepage cascade) and line splitting.
//!
//! Migrated from `clone/src/lines.rs` (read-only reference) and extended with
//! the behaviours the anchor corpus exercises. Every rule below is **O**
//! (observed) in `D:\Rea\verify\golden`:
//!
//! | Rule | Evidence |
//! |---|---|
//! | CRLF ≡ LF ≡ CR ≡ CRCRLF | `le-crlf-vs-lf`, `le-crlf-vs-cr`, `le-crcrlf`, `le-mixed` |
//! | missing final newline ≡ present | `le-no-final-nl` |
//! | UTF-8 BOM stripped | `enc-utf8-bom` |
//! | UTF-16LE / UTF-16BE BOM decoded, BOM removed | `enc-utf16le`, `enc-utf16be` |
//! | invalid UTF-8 → U+FFFD, no Latin-1 fallback | `enc-latin1` (`caf\xE9` → `caf\u{FFFD}`) |
//! | Ctrl-Z (0x1A) is an ordinary character, not EOF | `enc-ctrlz-eof` (`abc\x1adef` ≠ `abc`) |
//! | NUL bytes are ordinary text | `enc-nul-binary` (`a\x00b` vs `a\x00c` → different) |
//!
//! # Why a single CR/LF *run* is one break
//!
//! `le-crcrlf` compares `a\r\r\nb\r\r\n` against `a\r\nb\r\n` and BC reports two
//! `same` lines. If the separator were consumed one code unit at a time the left
//! file would yield `["a", "", "b", "", ""]` and the report could not be
//! all-`same` (it would contain an empty line that has no counterpart). Treating
//! a run of CR/LF as one terminator is the only reading consistent with the
//! observed statuses.

/// How the bytes were interpreted. Recorded so a report can state which codepage
/// was used rather than guessing.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Encoding {
    /// No BOM; decoded as UTF-8 with U+FFFD replacement for invalid sequences.
    Utf8,
    /// UTF-8 BOM (`EF BB BF`) present and stripped.
    Utf8Bom,
    /// UTF-16LE BOM (`FF FE`) present and stripped.
    Utf16Le,
    /// UTF-16BE BOM (`FE FF`) present and stripped.
    Utf16Be,
    /// A code page named by the file's own XML declaration (`<?xml … encoding=
    /// "GBK"?>`). Measured in `probes/U8-FINDINGS.md` §3; there is deliberately
    /// no auto-detection of legacy encodings, because the Oracle was measured
    /// *not* to do that.
    CodePage(u32),
}

impl Encoding {
    /// Short stable name used in diagnostics.
    pub fn name(self) -> &'static str {
        match self {
            Encoding::Utf8 => "utf-8",
            Encoding::Utf8Bom => "utf-8-bom",
            Encoding::Utf16Le => "utf-16le-bom",
            Encoding::Utf16Be => "utf-16be-bom",
            Encoding::CodePage(_) => "declared-code-page",
        }
    }

    /// The code page this decode used, when one applies.
    pub fn code_page(self) -> Option<u32> {
        match self {
            Encoding::CodePage(cp) => Some(cp),
            _ => None,
        }
    }
}

/// A decoded file: the text plus how it was decoded.
#[derive(Debug, Clone)]
pub struct Decoded {
    pub text: String,
    pub encoding: Encoding,
    /// True when at least one byte sequence was not valid for the chosen
    /// encoding and was replaced with U+FFFD. BC emits
    /// `<error1>File Encoding Error (Line N)</error1>` in this case (observed in
    /// `enc-latin1`); we record the fact so the XML writer can do the same.
    pub had_invalid_bytes: bool,
}

/// Decode raw bytes using BC's observed cascade
/// (`probes/U8-FINDINGS.md` §1, seven serial Oracle rounds):
///
/// ```text
/// 1. UTF-16LE BOM (FF FE)      -> UTF-16LE
/// 2. UTF-16BE BOM (FE FF)      -> UTF-16BE
/// 3. UTF-8 BOM (EF BB BF)      -> UTF-8      (a BOM suppresses step 4)
/// 4. bytes start with "<?xml"  -> the declaration's code page
/// 5. UTF-16 NUL-parity heuristic
/// 6. UTF-8 lossy
/// ```
///
/// Measured precedence: a UTF-16 BOM beats a declaration, a UTF-8 BOM suppresses
/// it, a declaration not at byte 0 is ignored, and a declaration wins over a body
/// that would have been valid UTF-8.
///
/// There is deliberately **no** Latin-1 fallback and **no** legacy-encoding
/// auto-detection: `enc-latin1` shows `caf\xE9` decoded as UTF-8 lossy to
/// `caf` + U+FFFD (not `café`), and five GBK cases measured the Oracle as
/// decoding BOM-less legacy bytes as UTF-8 lossy too. A legacy code page is used
/// only when the file declares one.
pub fn decode(raw: &[u8]) -> Decoded {
    if raw.len() >= 2 && raw[0] == 0xFF && raw[1] == 0xFE {
        return decode_utf16(&raw[2..], true);
    }
    if raw.len() >= 2 && raw[0] == 0xFE && raw[1] == 0xFF {
        return decode_utf16(&raw[2..], false);
    }
    if raw.len() >= 3 && &raw[..3] == b"\xef\xbb\xbf" {
        return decode_utf8(&raw[3..], Encoding::Utf8Bom);
    }
    // Step 4: a declaration at byte 0 selects a code page. Only reachable when
    // no BOM matched, which is the measured precedence.
    if let Some((cp, _name)) = crate::codepage::declared_code_page(raw) {
        if cp == crate::codepage::CP_UTF8 {
            return decode_utf8_declared(raw).0;
        }
        if crate::codepage::LEGACY_PAGES_SUPPORTED {
            return crate::codepage::decode_declared(cp, raw).0;
        }
        // Off Windows there is no table to decode with. Falling through to
        // UTF-8 lossy is the same path an unresolvable name takes, so the gap
        // is explicit rather than a wrong decode.
    }
    // Step 5: the BOM-less UTF-16 NUL-parity heuristic.
    if let Some(little_endian) = crate::codepage::nul_parity_utf16(raw) {
        return decode_utf16(raw, little_endian);
    }
    decode_utf8(raw, Encoding::Utf8)
}

fn decode_utf8(bytes: &[u8], encoding: Encoding) -> Decoded {
    match std::str::from_utf8(bytes) {
        Ok(s) => Decoded { text: s.to_string(), encoding, had_invalid_bytes: false },
        Err(_) => Decoded {
            text: String::from_utf8_lossy(bytes).into_owned(),
            encoding,
            had_invalid_bytes: true,
        },
    }
}

/// A file that declared `encoding="UTF-8"`: the fallback decode, but recorded as
/// the declared page it named.
///
/// Measured (`U8-FINDINGS.md` §3.1): `utf-8` / `UTF-8` / `utf8` / `CP65001` all
/// resolve, and the result is indistinguishable from the no-declaration case
/// except that no error is reported for a clean file. The error line therefore
/// comes from the UTF-8 validity scan, not from a legacy page scanner.
pub(crate) fn decode_utf8_declared(raw: &[u8]) -> (Decoded, Option<usize>) {
    let d = decode_utf8(raw, Encoding::CodePage(crate::codepage::CP_UTF8));
    let err = if d.had_invalid_bytes { first_invalid_utf8_line(raw) } else { None };
    (d, err)
}

fn decode_utf16(bytes: &[u8], little_endian: bool) -> Decoded {
    // An odd trailing byte cannot form a code unit; it is dropped by
    // `chunks_exact`. That is the same shape as a lossy decode (the trailing
    // fragment carries no character) and is recorded as invalid input.
    let mut units: Vec<u16> = Vec::with_capacity(bytes.len() / 2);
    for c in bytes.chunks_exact(2) {
        units.push(if little_endian {
            u16::from_le_bytes([c[0], c[1]])
        } else {
            u16::from_be_bytes([c[0], c[1]])
        });
    }
    let had_odd_tail = bytes.len() % 2 != 0;
    // `from_utf16` reports lone surrogates; those become U+FFFD in the lossy form.
    let had_bad_units = std::char::decode_utf16(units.iter().copied())
        .any(|r| r.is_err());
    Decoded {
        text: String::from_utf16_lossy(&units),
        encoding: if little_endian { Encoding::Utf16Le } else { Encoding::Utf16Be },
        had_invalid_bytes: had_odd_tail || had_bad_units,
    }
}

/// Split decoded text into logical lines.
///
/// A separator is a run of CR characters optionally followed by ONE LF
/// (`\r+` `\n?`). That single rule covers every observed case:
///
/// | Input | Separators | Why |
/// |---|---|---|
/// | `a\r\nb` | 1 | CR then LF |
/// | `a\nb` | 1 | bare LF |
/// | `a\rb` | 1 | bare CR |
/// | `a\r\r\nb` | 1 | CR CR LF — the whole run is one break (`le-crcrlf`) |
/// | `a\n\nb` | 2 | two bare LFs, i.e. one blank line (`verify/cases/leading-empty`) |
///
/// Consuming *all* consecutive CR/LF as one break would be wrong for `\n\n`: it
/// would silently delete a blank line, and the blank line is real — BC reports
/// `\nfoo\n` as two lines with `ltid="1"` empty against `ltid="2" rtid="1" foo`.
///
/// A trailing separator adds no extra empty final line, so `a\nb` and `a\nb\n`
/// both give two lines (`le-no-final-nl`). A file consisting only of separators
/// yields exactly one empty line per separator.
pub fn split_text(text: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let mut cur = String::new();
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if c == '\r' {
            // Absorb the whole CR run plus at most one LF.
            while matches!(chars.peek(), Some('\r')) {
                chars.next();
            }
            if matches!(chars.peek(), Some('\n')) {
                chars.next();
            }
            out.push(std::mem::take(&mut cur));
        } else if c == '\n' {
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

/// Decode and split in one step.
pub fn split(raw: &[u8]) -> (Vec<String>, Encoding) {
    let d = decode(raw);
    (split_text(&d.text), d.encoding)
}

/// The 1-based number of the first line whose bytes are not valid UTF-8.
///
/// # Why this is computed rather than assumed
///
/// `verify/golden/enc-latin1.xml` shows BC emitting
/// `<error1>File Encoding Error (Line 1)</error1>` for a left file of
/// `caf\xE9\n`, i.e. it names the offending line. Reporting a guessed line
/// number (always 1, or the last line) would be indistinguishable from a
/// hardcoded answer, so the number is derived from the bytes.
///
/// # Rules
///
/// Line boundaries are found at the byte level using the same separator rule as
/// [`split_text`]. That is sound because every separator is ASCII (CR = 0x0D,
/// LF = 0x0A), and ASCII bytes cannot occur inside a multi-byte UTF-8 sequence.
/// A line "has invalid bytes" when its byte slice fails UTF-8 validation.
///
/// Returns `None` for an empty input and for input with no invalid line. Only
/// meaningful for a UTF-8-decoded file: a UTF-16 file has no invalid UTF-8 line
/// by this definition, so the caller must not use the result there (see
/// [`Decoded::encoding`]).
pub fn first_invalid_utf8_line(raw: &[u8]) -> Option<usize> {
    // A UTF-16 BOM means the bytes are not UTF-8 at all: no line of this file
    // can be an "invalid UTF-8 line" (the caller reads the encoding from
    // `Decoded` instead), so the answer is `None` by definition.
    if raw.len() >= 2 && (raw[..2] == *b"\xff\xfe" || raw[..2] == *b"\xfe\xff") {
        return None;
    }
    // Note: a *declared legacy page* must not be scanned here — its bytes are
    // validated against that page, which `codepage::decode_declared` does. The
    // only callers that reach this function with a declaration are the ones for
    // which the declaration resolved to UTF-8, where scanning is exactly right.
    // A BOM is metadata, not content, and must not shift line numbering.
    let body = if raw.len() >= 3 && &raw[..3] == b"\xef\xbb\xbf" { &raw[3..] } else { raw };
    if body.is_empty() {
        return None;
    }
    let mut line_no = 1usize;
    let mut start = 0usize;
    let mut i = 0usize;
    while i < body.len() {
        let b = body[i];
        if b == b'\r' {
            if let Some(n) = check_line(&body[start..i], line_no) {
                return Some(n);
            }
            // Absorb the CR run plus at most one LF, mirroring `split_text`.
            while i < body.len() && body[i] == b'\r' {
                i += 1;
            }
            if i < body.len() && body[i] == b'\n' {
                i += 1;
            }
            line_no += 1;
            start = i;
        } else if b == b'\n' {
            if let Some(n) = check_line(&body[start..i], line_no) {
                return Some(n);
            }
            i += 1;
            line_no += 1;
            start = i;
        } else {
            i += 1;
        }
    }
    // The final segment only counts when the file did not end on a separator;
    // a trailing separator adds no line (matching `split_text`).
    if start < body.len() {
        if let Some(n) = check_line(&body[start..], line_no) {
            return Some(n);
        }
    }
    None
}

/// `Some(line_no)` when the slice is not valid UTF-8.
fn check_line(bytes: &[u8], line_no: usize) -> Option<usize> {
    if std::str::from_utf8(bytes).is_err() {
        Some(line_no)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn lines(raw: &[u8]) -> Vec<String> {
        split(raw).0
    }

    #[test]
    fn crlf_lf_cr_and_crcrlf_are_equivalent() {
        assert_eq!(lines(b"a\r\nb\r\n"), vec!["a", "b"]);
        assert_eq!(lines(b"a\nb\n"), vec!["a", "b"]);
        assert_eq!(lines(b"a\rb\r"), vec!["a", "b"]);
        assert_eq!(lines(b"a\r\r\nb\r\r\n"), vec!["a", "b"]);
        assert_eq!(lines(b"a\r\r\nb\r\r\n"), lines(b"a\r\nb\r\n"));
    }

    #[test]
    fn mixed_separators_in_one_file() {
        // verify/golden le-mixed: a\r\nb\nc\rd == a\nb\nc\nd
        assert_eq!(lines(b"a\r\nb\nc\rd"), lines(b"a\nb\nc\nd"));
        assert_eq!(lines(b"a\r\nb\nc\rd"), vec!["a", "b", "c", "d"]);
    }

    #[test]
    fn missing_final_newline_is_equivalent() {
        assert_eq!(lines(b"a\nb"), lines(b"a\nb\n"));
        assert_eq!(lines(b"a\nb"), vec!["a", "b"]);
    }

    #[test]
    fn no_trailing_empty_line_is_produced() {
        assert_eq!(lines(b"a\n\n"), vec!["a", ""]);
        assert_eq!(lines(b"\n"), vec![""]);
        assert_eq!(lines(b""), Vec::<String>::new());
        assert_eq!(lines(b"\r\n\r\n"), vec!["", ""]);
    }

    #[test]
    fn utf8_bom_is_stripped() {
        assert_eq!(lines(b"\xef\xbb\xbfa\nb\n"), vec!["a", "b"]);
        assert_eq!(split(b"\xef\xbb\xbfa\n").1, Encoding::Utf8Bom);
        assert_eq!(lines(b"\xef\xbb\xbfa\n"), lines(b"a\n"));
    }

    #[test]
    fn utf16le_bom_is_decoded_and_stripped() {
        // verify/golden enc-utf16le-L = FF FE 61 00 0A 00 62 00 0A 00
        assert_eq!(lines(b"\xff\xfea\x00\n\x00b\x00\n\x00"), vec!["a", "b"]);
        assert_eq!(split(b"\xff\xfea\x00").1, Encoding::Utf16Le);
        // ... and is equivalent to the plain UTF-8 file
        assert_eq!(lines(b"\xff\xfea\x00\n\x00"), lines(b"a\n"));
    }

    #[test]
    fn utf16be_bom_is_decoded_and_stripped() {
        // verify/golden enc-utf16be-L = FE FF 00 61 00 0A 00 62 00 0A
        assert_eq!(lines(b"\xfe\xff\x00a\x00\n\x00b\x00\n"), vec!["a", "b"]);
        assert_eq!(split(b"\xfe\xff\x00a").1, Encoding::Utf16Be);
    }

    #[test]
    fn utf16_surrogate_pairs_survive() {
        // U+1F600 as a surrogate pair in UTF-16LE.
        let raw = b"\xff\xfe\x3d\xd8\x00\xde";
        assert_eq!(lines(raw), vec!["\u{1F600}"]);
        assert!(!decode(raw).had_invalid_bytes);
    }

    #[test]
    fn invalid_utf8_becomes_replacement_char_with_no_latin1_fallback() {
        // verify/golden enc-latin1-L = "caf\xE9" (Latin-1 é).
        let d = decode(b"caf\xe9\n");
        assert!(d.had_invalid_bytes);
        assert_eq!(d.text, "caf\u{FFFD}\n");
        // Crucial: NOT "café" (that would be a Latin-1 fallback).
        assert_ne!(d.text, "caf\u{e9}\n");
        // The UTF-8 counterpart decodes cleanly and therefore differs.
        assert_eq!(decode(b"caf\xc3\xa9\n").text, "caf\u{e9}\n");
        assert!(!decode(b"caf\xc3\xa9\n").had_invalid_bytes);
    }

    #[test]
    fn ctrl_z_is_an_ordinary_character_not_eof() {
        // verify/golden enc-ctrlz-eof: "abc\x1adef" != "abc"
        let d = decode(b"abc\x1adef\n");
        assert_eq!(d.text, "abc\u{1a}def\n");
        assert_eq!(lines(b"abc\x1adef\n"), vec!["abc\u{1a}def"]);
        assert_ne!(lines(b"abc\x1adef\n"), lines(b"abc\n"));
    }

    #[test]
    fn nul_bytes_are_ordinary_text() {
        // verify/golden enc-nul-binary: "a\0b" vs "a\0c" must stay distinct.
        assert_eq!(lines(b"a\x00b\nc\n"), vec!["a\u{0}b", "c"]);
        assert_ne!(lines(b"a\x00b\n"), lines(b"a\x00c\n"));
        assert_eq!(lines(b"a\x00b\n"), vec!["a\u{0}b"]);
    }

    #[test]
    fn tabs_are_preserved_verbatim() {
        assert_eq!(lines(b"col1\tcol2\n"), vec!["col1\tcol2"]);
    }

    #[test]
    fn a_lone_cr_at_end_of_file_adds_no_empty_line() {
        assert_eq!(lines(b"a\r"), vec!["a"]);
        assert_eq!(lines(b"a\r\r"), vec!["a"]);
    }

    #[test]
    fn encoding_name_is_stable() {
        assert_eq!(Encoding::Utf8.name(), "utf-8");
        assert_eq!(Encoding::Utf16Be.name(), "utf-16be-bom");
    }

    // ---------------------------------------------------------------
    // Encoding-error line reporting (drives <error1>)
    // ---------------------------------------------------------------

    #[test]
    fn first_invalid_line_is_derived_from_the_bytes() {
        // The golden case: caf\xE9 on line 1.
        assert_eq!(first_invalid_utf8_line(b"caf\xe9\n"), Some(1));
        // A valid file reports nothing.
        assert_eq!(first_invalid_utf8_line(b"caf\xc3\xa9\n"), None);
        assert_eq!(first_invalid_utf8_line(b"a\nb\nc\n"), None);
        assert_eq!(first_invalid_utf8_line(b""), None);
        // The offending line is located, not assumed to be 1.
        assert_eq!(first_invalid_utf8_line(b"a\nb\ncaf\xe9\n"), Some(3));
        assert_eq!(first_invalid_utf8_line(b"a\r\nb\r\ncaf\xe9"), Some(3));
        assert_eq!(first_invalid_utf8_line(b"a\rb\rcaf\xe9\r"), Some(3));
    }

    #[test]
    fn invalid_line_uses_the_same_separator_rules_as_splitting() {
        // CRCRLF is one break, so the bad byte is on line 2, not line 4.
        assert_eq!(first_invalid_utf8_line(b"a\r\r\ncaf\xe9\r\r\n"), Some(2));
        // A blank line counts as a line.
        assert_eq!(first_invalid_utf8_line(b"a\n\ncaf\xe9\n"), Some(3));
        // A UTF-8 BOM must not shift the numbering.
        assert_eq!(first_invalid_utf8_line(b"\xef\xbb\xbfa\ncaf\xe9\n"), Some(2));
    }

    #[test]
    fn first_invalid_line_ignores_later_invalid_lines() {
        assert_eq!(first_invalid_utf8_line(b"caf\xe9\nx\xff\n"), Some(1));
    }

    #[test]
    fn first_invalid_line_is_none_for_utf16_input() {
        // Documented limitation: the helper validates UTF-8 segments, so a
        // UTF-16 file has no "invalid UTF-8 line". The caller must consult the
        // detected encoding, which is why `Decoded` carries it.
        assert_eq!(first_invalid_utf8_line(b"\xff\xfea\x00\n\x00"), None);
        assert_eq!(decode(b"\xff\xfea\x00").encoding, Encoding::Utf16Le);
    }
}

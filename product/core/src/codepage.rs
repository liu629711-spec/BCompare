//! U8 — code pages: the measured detection cascade.
//!
//! Every rule here is **O** (observed) in `product/verify/probes/U8-FINDINGS.md`,
//! from seven serial Oracle rounds (u8, u8b…u8g) against BC 5.0.3.30240 on this
//! host. The recorded probes are the evidence; this module is their transcription.
//!
//! # What is *not* implemented, and why that is correct
//!
//! There is **no automatic legacy-encoding detection**. Measured: BOM-less GBK
//! bytes are decoded as UTF-8 lossy by BC, and this crate already agreed with BC
//! byte-for-byte on five such cases before this module existed. "GBK guessing"
//! was the original plan for this milestone and the probe **refuted** it — adding
//! it would have invented behaviour BC does not have. A legacy code page is used
//! only when a file *declares* one.
//!
//! # The cascade
//!
//! ```text
//! 1. UTF-16LE BOM (FF FE)      -> UTF-16LE, skip 2
//! 2. UTF-16BE BOM (FE FF)      -> UTF-16BE, skip 2
//! 3. UTF-8 BOM (EF BB BF)      -> UTF-8, skip 3   (a BOM suppresses step 4)
//! 4. bytes start with "<?xml"  -> the declaration's code page
//! 5. UTF-16 NUL-parity heuristic
//! 6. UTF-8 lossy
//! ```
//!
//! Measured precedence: a UTF-16 BOM beats a declaration (`bom-beats-decl`), a
//! UTF-8 BOM suppresses it (`decl-after-bom`), a declaration not at byte 0 is
//! ignored (`decl-line2`), and a declaration wins over content that would have
//! been valid UTF-8 (`decl-gbk-valid-utf8` — the declared page is authoritative,
//! there is no "check UTF-8 first" fallback).
//!
//! # Decoding is *loose*, error reporting is *separate*
//!
//! Measured (`u8g`): under a declared GBK page, `0xFF` decodes to `U+F8F5` **and**
//! BC writes `<error1>`. So the text and the error element come from two different
//! judgements and must not be conflated: this module decodes loosely for the text
//! and probes strictly for validity.
//!
//! # Fidelity of the tables
//!
//! `u8g` measured BC's decode as **byte-identical to `MultiByteToWideChar` on all
//! 23 pages it resolves**. Rather than transcribe ~140 KB of generated tables
//! (measured by `tools/u8_sizes.py`) that could drift from that function, the
//! legacy pages call the same OS API. That is not a third-party dependency — it
//! is the platform — and it is what makes the replication exact rather than
//! approximate.

use crate::lines::{split_text, Decoded, Encoding};

/// UTF-8's code page. A declaration of it restates the fallback rather than
/// selecting a legacy table, so it must not take the byte-level page scanner:
/// that scanner treats one byte as one unit, which is right for DBCS/SBCS pages
/// and wrong for UTF-8 (measured — `encoding="UTF-8"` was a no-op for BC, and
/// running it through the scanner reported spurious errors on valid text).
pub const CP_UTF8: u32 = 65001;

// ==========================================================================
// The declared-name table (u8f: measured by fingerprint, not assumed)
// ==========================================================================
//
// Each entry was produced by giving BC a discriminating body under a candidate
// name and comparing the decode against every candidate page's OS table. The
// measurements contain results that contradict the obvious guess, and both are
// reproduced rather than "corrected":
//
//   * `cp936` / `936` / `windows-936` / `ms936` do **not** resolve, while
//     `GBK` / `gb2312` / `GB_2312-80` / `csgb2312` / `chinese` do.
//   * `US-ASCII` / `ascii` / `ISO8859-1` / `latin1` resolve to **cp1252**
//     (the whole ASCII family shares one target), not to a 7-bit page.
//
// `ISO-8859-15` resolving to **28591** (not 28605) is likewise measured.
//
// Lookup is ASCII case-insensitive: `GbK` was measured to resolve, which no
// both-case table explains, so the comparison itself folds case.

/// `(lowercase name, code page)`. Sorted by name for a binary search.
const DECLARED_NAMES: &[(&str, u32)] = &[
    ("ansi_x3.4-1968", 1252),
    ("ascii", 1252),
    ("big-5", 950),
    ("big5", 950),
    ("chinese", 936),
    ("cn-big5", 950),
    ("cp1250", 1250),
    ("cp1251", 1251),
    ("cp1252", 1252),
    ("cp1253", 1253),
    ("cp1254", 1254),
    ("cp1255", 1255),
    ("cp1256", 1256),
    ("cp1257", 1257),
    ("cp1258", 1258),
    ("cp437", 437),
    ("cp65001", 65001),
    ("cp850", 850),
    ("cp866", 866),
    ("cp932", 932),
    ("cp949", 949),
    ("cp950", 950),
    ("csbig5", 950),
    ("csgb2312", 936),
    ("euc-kr", 949),
    ("gb18030", 54936),
    ("gb2312", 936),
    ("gb_2312-80", 936),
    ("gbk", 936),
    ("ibm437", 437),
    ("ibm850", 850),
    ("iso-8859-1", 1252),
    ("iso-8859-15", 28591),
    ("iso-8859-2", 28592),
    ("iso-8859-5", 28595),
    ("iso-8859-7", 28597),
    ("iso-ir-6", 1252),
    ("iso8859-1", 1252),
    ("johab", 1361),
    ("ks_c_5601-1987", 949),
    ("ksc5601", 949),
    ("l1", 28591),
    ("latin1", 1252),
    ("ms_kanji", 932),
    ("shift_jis", 932),
    ("sjis", 932),
    ("us-ascii", 1252),
    ("utf-8", 65001),
    ("utf8", 65001),
    ("windows-1250", 1250),
    ("windows-1251", 1251),
    ("windows-1252", 1252),
    ("windows-1253", 1253),
    ("windows-1254", 1254),
    ("windows-1255", 1255),
    ("windows-1256", 1256),
    ("windows-1257", 1257),
    ("windows-1258", 1258),
    ("windows-874", 874),
    ("x-sjis", 932),
];

/// Resolve a declared encoding name to a code page, or `None` when BC would not
/// resolve it either.
///
/// Unicode-family names (`utf-16`, `ucs-2`, `utf-32`) are absent deliberately:
/// measured, they are **rejected** and the file falls through to UTF-8 lossy.
/// So are the numeric spellings (`936`, `cp936`) — see the note above.
pub fn lookup_declared_name(name: &str) -> Option<u32> {
    let lower = name.to_ascii_lowercase();
    DECLARED_NAMES
        .binary_search_by(|(n, _)| (*n).cmp(lower.as_str()))
        .ok()
        .map(|i| DECLARED_NAMES[i].1)
}

/// Parse a code page out of an XML declaration at byte 0.
///
/// The accepted syntax is narrower than XML's, and the narrowness is measured
/// (u8c/u8e):
///
/// | Form | Result |
/// |---|---|
/// | `<?xml version="1.0" encoding="GBK"?>` | accepted |
/// | `<?xml encoding="GBK"?>` (no version) | accepted |
/// | `<?xml version="1.0" encoding='GBK'?>` | accepted |
/// | `<?xml version="1.0" encoding="GBK" standalone="yes"?>` | accepted |
/// | `<?xml version="1.0" ENCODING="GBK"?>` | **rejected** (attribute name must be lower case) |
/// | `<?xml version="1.0"   encoding = "GBK"  ?>` | **rejected** (no spaces around `=`) |
/// | `<?xml version="1.0" encoding=GBK?>` | **rejected** (value must be quoted) |
/// | `<?xml version="1.0" encoding="GBK"` | **rejected** (no `?>`) |
///
/// Returns the code page and the name as written. `None` covers every rejected
/// and unresolvable case: the caller then continues down the cascade, which is
/// what BC does (an unresolvable name is not an error, it is simply no answer).
pub fn declared_code_page(raw: &[u8]) -> Option<(u32, String)> {
    if !raw.starts_with(b"<?xml") {
        return None;
    }
    // The declaration must be terminated; measured, an unterminated one is
    // rejected rather than read to end-of-file.
    let end = raw.iter().position(|&b| b == b'>')?;
    let decl = &raw[..=end];

    // Find `encoding=` with the measured spelling rule: lower-case name, no
    // surrounding spaces. A search for that exact byte sequence *is* the rule,
    // so it is written as one rather than as a loose attribute scan.
    let needle = b"encoding=";
    let at = decl.windows(needle.len()).position(|w| w == needle)?;
    let rest = &decl[at + needle.len()..];

    let quote = *rest.first()?;
    if quote != b'"' && quote != b'\'' {
        return None;
    }
    let close = rest[1..].iter().position(|&b| b == quote)? + 1;
    let name_bytes = &rest[1..close];
    // A name is ASCII in every measured case; a non-ASCII byte cannot match the
    // table and is treated as unresolved rather than lossily converted.
    let name = std::str::from_utf8(name_bytes).ok()?;
    let cp = lookup_declared_name(name)?;
    Some((cp, name.to_string()))
}

// ==========================================================================
// The BOM-less UTF-16 NUL-parity heuristic
// ==========================================================================

/// The NUL-parity heuristic, transcribed from `SsCodePage.md` and confirmed
/// against the Oracle (`u8`/`u8b`).
///
/// `SsCodePage.md` records the thresholds as `odd > 0.6 && even < 0.02` for
/// UTF-16LE and the mirror for BE, gated on an even length. The doc says
/// "even and >3"; the Oracle measured `61 00 0A 00` (length 4) as UTF-16LE
/// while `00 61` (length 2) was **not** detected, so the gate is
/// `len >= 4 && len % 2 == 0`.
///
/// The ratios are `count * 2 / len`, i.e. the fraction of positions of that
/// parity holding NUL. Returns `Some(true)` for little-endian, `Some(false)` for
/// big-endian, `None` when neither branch fires (BC then stays on UTF-8).
pub fn nul_parity_utf16(raw: &[u8]) -> Option<bool> {
    if raw.len() < 4 || raw.len() % 2 != 0 {
        return None;
    }
    let mut even = 0usize;
    let mut odd = 0usize;
    for (i, &b) in raw.iter().enumerate() {
        if b == 0 {
            if i % 2 == 0 {
                even += 1;
            } else {
                odd += 1;
            }
        }
    }
    let total = raw.len() as f64;
    let odd_ratio = odd as f64 * 2.0 / total;
    let even_ratio = even as f64 * 2.0 / total;
    if odd_ratio > 0.6 && even_ratio < 0.02 {
        Some(true)
    } else if even_ratio > 0.6 && odd_ratio < 0.02 {
        Some(false)
    } else {
        None
    }
}

// ==========================================================================
// The platform conversion
// ==========================================================================

#[cfg(windows)]
mod os {
    #[link(name = "kernel32")]
    extern "system" {
        fn MultiByteToWideChar(
            code_page: u32,
            flags: u32,
            multi_byte_str: *const u8,
            cb_multi_byte: i32,
            wide_char_str: *mut u16,
            cch_wide_char: i32,
        ) -> i32;

        fn GetCPInfo(code_page: u32, lp_cp_info: *mut CpInfo) -> i32;
    }

    const MB_ERR_INVALID_CHARS: u32 = 0x0000_0008;

    /// `CPINFO` as `winnls.h` declares it. `lead_byte` holds up to six
    /// `{first, last}` pairs, terminated by a zero entry.
    #[repr(C)]
    #[derive(Clone, Copy)]
    pub struct CpInfo {
        pub max_char_size: u32,
        pub default_char: [u8; 2],
        pub lead_byte: [u8; 12],
    }

    /// Loose conversion — the mode BC's text comes from.
    pub fn to_wide(code_page: u32, bytes: &[u8]) -> String {
        if bytes.is_empty() {
            return String::new();
        }
        let need = unsafe {
            MultiByteToWideChar(code_page, 0, bytes.as_ptr(),
                                bytes.len() as i32, std::ptr::null_mut(), 0)
        };
        if need <= 0 {
            return String::new();
        }
        let mut buf: Vec<u16> = vec![0; need as usize];
        let got = unsafe {
            MultiByteToWideChar(code_page, 0, bytes.as_ptr(),
                                bytes.len() as i32, buf.as_mut_ptr(), need)
        };
        if got <= 0 {
            return String::new();
        }
        buf.truncate(got as usize);
        String::from_utf16_lossy(&buf)
    }

    /// Strict probe: `false` when any byte sequence is invalid for the page.
    pub fn is_valid(code_page: u32, bytes: &[u8]) -> bool {
        if bytes.is_empty() {
            return true;
        }
        let n = unsafe {
            MultiByteToWideChar(code_page, MB_ERR_INVALID_CHARS, bytes.as_ptr(),
                                bytes.len() as i32, std::ptr::null_mut(), 0)
        };
        n > 0
    }

    pub fn cp_info(code_page: u32) -> Option<CpInfo> {
        let mut info = CpInfo { max_char_size: 0, default_char: [0; 2],
                                lead_byte: [0; 12] };
        let ok = unsafe { GetCPInfo(code_page, &mut info) };
        if ok == 0 {
            None
        } else {
            Some(info)
        }
    }
}

#[cfg(not(windows))]
mod os {
    #[derive(Clone, Copy)]
    pub struct CpInfo {
        pub max_char_size: u32,
        pub default_char: [u8; 2],
        pub lead_byte: [u8; 12],
    }
    // No legacy code page tables off Windows. The cascade never reaches these
    // helpers there because `LEGACY_PAGES_SUPPORTED` is false and callers treat
    // a declared page as unresolvable, but they return the explicitly-empty
    // answer rather than pretending to decode.
    pub fn to_wide(_cp: u32, _b: &[u8]) -> String {
        String::new()
    }
    pub fn is_valid(_cp: u32, _b: &[u8]) -> bool {
        false
    }
    pub fn cp_info(_cp: u32) -> Option<CpInfo> {
        None
    }
}

/// Whether legacy code pages can be decoded at all on this platform.
///
/// `false` off Windows. The cascade then treats a declared legacy page as
/// *unresolvable* and falls through to UTF-8 lossy — the same path BC takes for
/// a name it does not know, so the gap is visible and typed rather than a silent
/// mis-decode.
pub const LEGACY_PAGES_SUPPORTED: bool = cfg!(windows);

/// The lead bytes of a code page, expanded from `GetCPInfo`'s range pairs.
fn lead_bytes(code_page: u32) -> Vec<u8> {
    let Some(info) = os::cp_info(code_page) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    let mut i = 0;
    while i + 1 < info.lead_byte.len() {
        let lo = info.lead_byte[i];
        let hi = info.lead_byte[i + 1];
        if lo == 0 {
            break;
        }
        out.extend(lo..=hi);
        i += 2;
    }
    out
}

/// One pass over a declared-page file: the decoded text, the lines, and the
/// first invalid line.
///
/// # Why the scan is at byte level
///
/// `SsLineParse.md` describes the reader skipping a DBCS lead byte together with
/// its follower, and that is visible in the report: measured (`err-dangling-eol`),
/// `ok\n\x81\nnext\n` decodes to two lines, `ok` and `?next` — the `\x81`
/// *consumed the newline*, so no break happened there. Decoding the whole buffer
/// first and splitting afterwards cannot reproduce that, because the separator is
/// already gone from the text by then.
///
/// The mirror case is `err-dangling`: a lone lead byte at end-of-file is dropped
/// with **no** line and **no** error, matching the reader's carry buffer never
/// being flushed.
///
/// Separators are kept in the returned text so a caller can re-split with
/// [`split_text`] and inherit the CRCRLF rule from one place.
pub struct PageDecode {
    /// Decoded text, separators preserved.
    pub text: String,
    /// 1-based line number of the first invalid sequence, counting the
    /// declaration line as line 1 (measured `err-line-1` / `err-line-3`).
    pub first_invalid_line: Option<usize>,
    /// True when at least one sequence was invalid.
    pub had_invalid_bytes: bool,
}

pub fn decode_page_text(code_page: u32, raw: &[u8]) -> PageDecode {
    let leads = lead_bytes(code_page);
    let max_char = os::cp_info(code_page).map(|i| i.max_char_size).unwrap_or(1);

    let mut text = String::new();
    let mut first_invalid: Option<usize> = None;
    let mut line_no = 1usize;
    let mut i = 0usize;

    while i < raw.len() {
        let b = raw[i];

        if leads.contains(&b) {
            // A lead byte takes its follower whatever it is — including a
            // separator. At EOF the pair is incomplete and is dropped.
            if i + 1 >= raw.len() {
                break;
            }
            // GB18030's four-byte form is distinguishable by a digit-shaped
            // second byte; try the longest form first so a valid four-byte
            // sequence is not mistaken for a two-byte one.
            if max_char > 2 && i + 4 <= raw.len()
                && (0x30..=0x39).contains(&raw[i + 1])
                && os::is_valid(code_page, &raw[i..i + 4])
            {
                text.push_str(&os::to_wide(code_page, &raw[i..i + 4]));
                i += 4;
                continue;
            }
            let pair = &raw[i..i + 2];
            if !os::is_valid(code_page, pair) {
                if first_invalid.is_none() {
                    first_invalid = Some(line_no);
                }
            }
            text.push_str(&os::to_wide(code_page, pair));
            i += 2;
            continue;
        }

        if b == b'\r' {
            text.push('\r');
            i += 1;
            // Mirror `split_text`: a CR run plus at most one LF is one break.
            while i < raw.len() && raw[i] == b'\r' {
                text.push('\r');
                i += 1;
            }
            if i < raw.len() && raw[i] == b'\n' {
                text.push('\n');
                i += 1;
            }
            line_no += 1;
            continue;
        }
        if b == b'\n' {
            text.push('\n');
            i += 1;
            line_no += 1;
            continue;
        }

        // A single-byte unit. On a DBCS page a stray high byte is invalid, and
        // the loose conversion still yields a character (measured: 0xFF -> U+F8F5).
        if !os::is_valid(code_page, &raw[i..i + 1]) && first_invalid.is_none() {
            first_invalid = Some(line_no);
        }
        text.push_str(&os::to_wide(code_page, &raw[i..i + 1]));
        i += 1;
    }

    PageDecode {
        text,
        first_invalid_line: first_invalid,
        had_invalid_bytes: first_invalid.is_some(),
    }
}

/// Decode a declared-page file into the cascade's [`Decoded`] shape.
///
/// A declaration of UTF-8 restates the fallback rather than selecting a legacy
/// table, so it is decoded by the UTF-8 path: the byte-level page scanner treats
/// one byte as one unit, which is correct for DBCS/SBCS pages and wrong for
/// UTF-8 (measured — routing `encoding="UTF-8"` through the scanner reported six
/// spurious errors on the six bytes of `测试`).
pub fn decode_declared(code_page: u32, raw: &[u8]) -> (Decoded, Option<usize>) {
    if code_page == CP_UTF8 {
        return crate::lines::decode_utf8_declared(raw);
    }
    let page = decode_page_text(code_page, raw);
    (
        Decoded {
            text: page.text,
            encoding: Encoding::CodePage(code_page),
            had_invalid_bytes: page.had_invalid_bytes,
        },
        page.first_invalid_line,
    )
}

/// Split a declared-page file, reusing [`split_text`] so line-break semantics
/// live in one place.
pub fn split_declared(code_page: u32, raw: &[u8]) -> (Vec<String>, Option<usize>) {
    let (d, err) = decode_declared(code_page, raw);
    (split_text(&d.text), err)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn declared_names_match_the_measured_table() {
        // Resolved, per u8f.
        assert_eq!(lookup_declared_name("GBK"), Some(936));
        assert_eq!(lookup_declared_name("gbk"), Some(936));
        assert_eq!(lookup_declared_name("GbK"), Some(936)); // case-insensitive
        assert_eq!(lookup_declared_name("gb2312"), Some(936));
        assert_eq!(lookup_declared_name("GB_2312-80"), Some(936));
        assert_eq!(lookup_declared_name("csgb2312"), Some(936));
        assert_eq!(lookup_declared_name("chinese"), Some(936));
        assert_eq!(lookup_declared_name("GB18030"), Some(54936));
        assert_eq!(lookup_declared_name("Shift_JIS"), Some(932));
        assert_eq!(lookup_declared_name("Big5"), Some(950));
        assert_eq!(lookup_declared_name("utf-8"), Some(65001));

        // The ASCII family lands on cp1252, not a 7-bit page (u8f).
        for n in ["US-ASCII", "ascii", "ASCII", "ANSI_X3.4-1968", "iso-ir-6",
                  "ISO-8859-1", "ISO8859-1", "latin1", "cp1252"] {
            assert_eq!(lookup_declared_name(n), Some(1252), "{n}");
        }
        // ISO-8859-15 -> 28591 is measured (not 28605).
        assert_eq!(lookup_declared_name("ISO-8859-15"), Some(28591));
    }

    #[test]
    fn numeric_and_unknown_names_do_not_resolve() {
        // Measured refusals. These must NOT resolve: BC falls through to UTF-8.
        for n in ["cp936", "CP936", "936", "windows-936", "ms936", "x-gbk",
                  "gbk-2312", "gb_2312", "gb231280", "932", "windows-31j",
                  "949", "950", "1252", "latin-1", "646",
                  "utf-16", "UTF-16", "utf-16le", "utf-16be", "ucs-2", "UCS-2",
                  "utf-32", "x-nonexistent-page", "", " "] {
            assert_eq!(lookup_declared_name(n), None, "{n} must not resolve");
        }
    }

    #[test]
    fn declaration_parser_accepts_the_measured_forms() {
        let gbk = b"<?xml version=\"1.0\" encoding=\"GBK\"?>\n";
        assert_eq!(declared_code_page(gbk).map(|p| p.0), Some(936));
        // No version attribute.
        assert_eq!(
            declared_code_page(b"<?xml encoding=\"GBK\"?>").map(|p| p.0),
            Some(936));
        // Single quotes.
        assert_eq!(
            declared_code_page(b"<?xml version=\"1.0\" encoding='GBK'?>")
                .map(|p| p.0),
            Some(936));
        // A further attribute after encoding.
        assert_eq!(
            declared_code_page(
                b"<?xml version=\"1.0\" encoding=\"GBK\" standalone=\"yes\"?>")
                .map(|p| p.0),
            Some(936));
        // The name is returned as written.
        assert_eq!(declared_code_page(gbk).map(|p| p.1),
                   Some("GBK".to_string()));
    }

    #[test]
    fn declaration_parser_rejects_the_measured_forms() {
        // Upper-case attribute name.
        assert_eq!(
            declared_code_page(b"<?xml version=\"1.0\" ENCODING=\"GBK\"?>"), None);
        // Spaces around `=`.
        assert_eq!(
            declared_code_page(b"<?xml version=\"1.0\"   encoding = \"GBK\"  ?>"),
            None);
        // Unquoted value.
        assert_eq!(
            declared_code_page(b"<?xml version=\"1.0\" encoding=GBK?>"), None);
        // Unterminated declaration.
        assert_eq!(
            declared_code_page(b"<?xml version=\"1.0\" encoding=\"GBK\""), None);
        // No encoding attribute at all.
        assert_eq!(declared_code_page(b"<?xml version=\"1.0\"?>"), None);
        // Not at byte 0.
        assert_eq!(declared_code_page(b"junk\n<?xml encoding=\"GBK\"?>"), None);
        // No `<?xml` prefix.
        assert_eq!(declared_code_page(b"encoding=\"GBK\"\n"), None);
        // A Unicode-family name is refused even though it is a real page name.
        assert_eq!(declared_code_page(b"<?xml encoding=\"utf-16\"?>"), None);
    }

    #[test]
    fn nul_parity_detects_utf16_without_a_bom() {
        // Measured (u8/u8b): 61 00 62 00 0A 00 -> "ab" as UTF-16LE.
        assert_eq!(nul_parity_utf16(b"a\x00b\x00\n\x00"), Some(true));
        assert_eq!(nul_parity_utf16(b"a\x00b\x00c\x00\n\x00"), Some(true));
        // Length 4 also fires: 61 00 0A 00 -> "a".
        assert_eq!(nul_parity_utf16(b"a\x00\n\x00"), Some(true));
        // Mirrored: UTF-16BE.
        assert_eq!(nul_parity_utf16(b"\x00a\x00b\x00\n"), Some(false));
        // Length 2 does not (00 61 was measured as NOT detected = "&#0;a").
        assert_eq!(nul_parity_utf16(b"\x00a"), None);
    }

    #[test]
    fn nul_parity_declines_when_the_density_does_not_fit() {
        // Measured "ab\x00cd\x00\n\x00": odd-NUL ratio 0.5, below 0.6.
        assert_eq!(nul_parity_utf16(b"ab\x00cd\x00\n\x00"), None);
        // CJK UTF-16LE has almost no NULs.
        assert_eq!(nul_parity_utf16("\u{4e2d}\u{6587}\n".as_bytes()), None);
        assert_eq!(nul_parity_utf16("中文测试\n".as_bytes()), None);
        // NULs on both parities: neither branch may fire.
        assert_eq!(nul_parity_utf16(b"a\x00\x00\x00b\x00\x00\x00"), None);
        // The existing goldens must not be caught by the heuristic.
        assert_eq!(nul_parity_utf16(b"a\x00b\nc\n"), None);
        assert_eq!(nul_parity_utf16(b"caf\xe9\n"), None);
        assert_eq!(nul_parity_utf16(b""), None);
    }

    #[cfg(windows)]
    #[test]
    fn declared_page_decodes_like_the_measured_oracle() {
        // u8g measured these as byte-identical to MultiByteToWideChar.
        // 测试 in GBK is B2 E2 CA D4.
        let (d, err) = decode_declared(936, &[0xB2, 0xE2, 0xCA, 0xD4, b'\n']);
        assert_eq!(d.text, "\u{6d4b}\u{8bd5}\n");
        assert!(!d.had_invalid_bytes);
        assert_eq!(d.encoding, Encoding::CodePage(936));
        assert_eq!(err, None);

        // The invalid byte decodes loosely to the measured private-use value
        // while still being reported invalid (u8g: 0xFF -> U+F8F5 + <error1>).
        let (bad, err) = decode_declared(936, &[0xFF, b'\n']);
        assert_eq!(bad.text, "\u{f8f5}\n");
        assert!(bad.had_invalid_bytes, "0xFF is invalid in GBK");
        assert_eq!(err, Some(1));

        // cp1252: 0xE9 is defined, so no error.
        let (latin, err) = decode_declared(1252, b"caf\xe9\n");
        assert_eq!(latin.text, "caf\u{e9}\n");
        assert!(!latin.had_invalid_bytes);
        assert_eq!(err, None);
    }

    #[cfg(windows)]
    #[test]
    fn splitting_honours_the_lead_byte_rule() {
        // Measured err-dangling-eol: the lead byte consumes the newline, so the
        // two logical lines are `ok` and `?next`.
        let (lines, err) = split_declared(936, b"ok\n\x81\nnext\n");
        assert_eq!(lines, vec!["ok".to_string(), "?next".to_string()]);
        assert_eq!(err, Some(2));

        // Measured err-dangling: a lone lead byte at EOF yields no line at all.
        let (lines, err) = split_declared(936, b"ok\n\x81");
        assert_eq!(lines, vec!["ok".to_string()]);
        assert_eq!(err, None);

        // A clean file splits normally.
        let (lines, err) = split_declared(936, &[0xB2, 0xE2, 0xCA, 0xD4, b'\n',
                                                 b'o', b'k', b'\n']);
        assert_eq!(lines, vec!["\u{6d4b}\u{8bd5}".to_string(), "ok".to_string()]);
        assert_eq!(err, None);
    }

    #[cfg(windows)]
    #[test]
    fn invalid_line_numbers_follow_the_measured_rule() {
        // A declaration occupies line 1, so an invalid byte on the next line is
        // reported as line 2 (measured err-line-1). The declaration bytes are
        // passed in, because that is what the caller decodes.
        let decl = b"<?xml version=\"1.0\" encoding=\"GBK\"?>\n";
        let mut file = decl.to_vec();
        file.extend_from_slice(b"\xff\nok\nok\n");
        let (_, err) = decode_declared(936, &file);
        assert_eq!(err, Some(2));

        // measured err-line-3: invalid on the fourth line.
        let mut file = decl.to_vec();
        file.extend_from_slice(b"a\nb\n\xff\nc\n");
        let (_, err) = decode_declared(936, &file);
        assert_eq!(err, Some(4));

        // measured err-two-bad: only the first invalid line is reported.
        let mut file = decl.to_vec();
        file.extend_from_slice(b"\xff\nok\n\xfe\n");
        let (_, err) = decode_declared(936, &file);
        assert_eq!(err, Some(2));
    }
}

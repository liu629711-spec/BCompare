//! Parser tests: every case maps to a measured Oracle cell (docs/17,
//! runs/m101*). The Oracle verdicts are reproduced from the archived report
//! lines; here we assert the parse-level facts they pin.
//!
//! Tree coordinates: `roots` are the children of the HIVE component (the
//! first segment of a key line), so the probe base
//! `HKEY_CURRENT_USER\Software\ReaProbe` lives at
//! `node(["Software", "ReaProbe"])`; `base_values` holds only values on the
//! hive itself (never observed in the corpus).
//!
//! `basekey` is a hive-INCLUSIVE absolute path (the frame prints it).

use reacmp_reg::parse::{parse_reg, parse_reg_text, KeyNode, ParseNote, RegError};
use reacmp_reg::values::Value;

const C: &str = "\r\n";
fn head() -> String {
    format!("Windows Registry Editor Version 5.00{C}{C}")
}
fn reg(lines: &[&str]) -> String {
    let mut s = head();
    s.push_str(&lines.join(C));
    s.push_str(C);
    s
}

const BRACKET: &str = r"[HKEY_CURRENT_USER\Software\ReaProbe]";
const BASE_ABS: &str = r"HKEY_CURRENT_USER\Software\ReaProbe";

/// The probe-base node (below the hive).
fn probe(f: &reacmp_reg::parse::RegFile) -> Option<&KeyNode> {
    f.node(&["Software".into(), "ReaProbe".into()])
}

#[test]
fn header_is_unsupported_type_when_absent() {
    // m101n N4 (no header) / N9 (0 bytes) / m101b R19 (PNG pair -> the
    // first line is binary junk, no header)
    let f = parse_reg_text("badline alone");
    assert_eq!(f.error, Some(RegError::UnsupportedType));
    assert_eq!(f.basekey, None);
    let f = parse_reg_text("");
    assert_eq!(f.error, Some(RegError::UnsupportedType));
}

#[test]
fn binary_payload_is_encoding_error_not_unsupported() {
    // m101 R19 / m101i I7 (both installs): the PNG pair reports
    // `File Encoding Error (Line 1)` / `文件编码错误 (第 1 行)` and the file
    // lines show NO basekey suffix. The sniff rule: no BOM + a NUL byte
    // anywhere = binary. A NUL-free garbage text file stays on the
    // Unsupported Type branch (N4/N9 above).
    let mut png = vec![0x89, b'P', b'N', b'G', 0x0d, 0x1a, 0x0a, 0x0a];
    png.extend(vec![0u8; 40]);
    let f = parse_reg(&png);
    assert_eq!(f.error, Some(RegError::Encoding { line: 1 }));
    assert_eq!(f.basekey, None);
    // NUL-free binary junk (the ANSI fallback) is still "text" -> the
    // header check runs and fails as Unsupported Type.
    let f = parse_reg(b"\x89PNG\r\n\x1a\n");
    assert_eq!(f.error, Some(RegError::UnsupportedType));
}

#[test]
fn header_only_no_keys_is_unsupported_without_suffix() {
    // m101n N10: header present but no key line -> Unsupported Type; the
    // file line shows NO `:\\basekey` suffix (basekey None)
    let f = parse_reg_text(&head());
    assert_eq!(f.error, Some(RegError::UnsupportedType));
    assert_eq!(f.basekey, None);
}

#[test]
fn regedit4_header_accepted() {
    // m101b C9: REGEDIT4 parses like the v5 shape
    let text = "REGEDIT4\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"v\"=\"1\"\r\n";
    let f = parse_reg_text(text);
    assert_eq!(f.error, None);
    assert_eq!(f.basekey.as_deref(), Some("HKEY_CURRENT_USER\\S"));
    assert_eq!(f.all_keys.len(), 1);
    assert_eq!(f.node(&["S".to_string()]).map(|n| n.values.len()), Some(1));
}

#[test]
fn parse_error_stops_parse_and_keeps_earlier_items() {
    // m101e I5: `garbage line` AFTER a good value -> Parsing (5:1); the
    // value survives (report showed 1 same item on the other side) and the
    // suffix stays (G3: a listed key survived)
    let mut text = reg(&[BRACKET, r#""v"="1""#]);
    text.push_str(&format!("garbage line{C}"));
    let f = parse_reg_text(&text);
    assert_eq!(f.error, Some(RegError::Parsing { line: 5, col: 1 }));
    assert_eq!(f.basekey.as_deref(), Some(BASE_ABS));
    assert_eq!(probe(&f).map(|n| n.values.len()), Some(1));
}

#[test]
fn parse_error_before_value_keeps_key_suffix() {
    // m101b C10: garbage right after the key line -> the key was LISTED but
    // never valued (the Oracle's other side produced `2 个重要的右边独有项`
    // from its intact pair; here we pin the parse-level facts)
    let mut text = head();
    text.push_str(&format!("{BRACKET}{C}garbage here{C}"));
    let f = parse_reg_text(&text);
    assert_eq!(f.error, Some(RegError::Parsing { line: 4, col: 1 }));
    assert_eq!(f.valued.len(), 0);
    assert_eq!(f.all_keys.len(), 1);
    // G3: the suffix survives from the pre-error key
    assert_eq!(f.basekey.as_deref(), Some(BASE_ABS));
}

#[test]
fn parse_error_with_no_surviving_key_has_no_suffix() {
    // m101c G3's orphan side: header + garbage only -> NO key survived, the
    // suffix disappeared entirely (error is Parsing, not UnsupportedType,
    // because the header itself read fine)
    let f = parse_reg_text(&format!("{}not a key line{C}", head()));
    assert_eq!(f.error, Some(RegError::Parsing { line: 3, col: 1 }));
    assert_eq!(f.basekey, None);
}

#[test]
fn value_line_missing_equals_is_end_of_line_column() {
    // m101e T2: `  "bbb"` (quoted start, no '='): the statement starts well
    // and fails inside -> Parsing (5:8) = line char count + 1. Contrast with
    // C6/C10 where a NON-starter line reports first-nonspace.
    let text = reg(&[BRACKET, r#""s"="aaa""#, r#"  "bbb""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, Some(RegError::Parsing { line: 5, col: 8 }));
    assert_eq!(probe(&f).map(|n| n.values.len()), Some(1)); // aaa survived
}

#[test]
fn comma_continuation_is_never_joined() {
    // m101g T1 (archived fixture, superseding the earlier join hypothesis):
    // `hex:68,65,6c,6c,6f,` + indented `  2c,20,77` -> NO join: the value
    // keeps the first line's five bytes, the second line cannot start a
    // statement -> Parsing (5:3), exactly like C6. The archived report's
    // left data is `68 65 6C 6C 6F` and its error line proves the rest.
    let text = reg(&[BRACKET, r#""Blob"=hex:68,65,6c,6c,6f,"#, r"  2c,20,77"]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, Some(RegError::Parsing { line: 5, col: 3 }));
    match &probe(&f).unwrap().values[0].value {
        Value::Binary(b) => assert_eq!(b, &b"hello"[..]),
        v => panic!("expected binary, got {v:?}"),
    }
}

#[test]
fn unclosed_continuation_is_next_line_first_nonspace() {
    // m101b C6: hex WITHOUT trailing ',' then an indented digit line: the
    // next line cannot START a statement -> Parsing (5:3); Blob survives
    let text = reg(&[BRACKET, r#""Blob"=hex:68,65,6c,6c,6f"#, r"  2c,20,77"]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, Some(RegError::Parsing { line: 5, col: 3 }));
    assert_eq!(probe(&f).map(|n| n.values.len()), Some(1));
}

#[test]
fn delete_value_sets_note_and_skips() {
    // m101g S1: "none"=- -> note, the value never appears
    let text = reg(&[BRACKET, r#""v"="1""#, r#""none"=-"#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.note, Some(ParseNote::DeletesDuplicatesSkipped));
    let n = probe(&f).unwrap();
    assert_eq!(n.values.len(), 1);
    assert_eq!(n.values[0].name, "v");
}

#[test]
fn delete_key_line_sets_note_and_skips() {
    // m101b C8: [-...\Gone] before the real key -> note; the deletion line
    // is not a listed key
    let text = reg(&[
        r"[-HKEY_CURRENT_USER\Software\ReaProbe\Gone]",
        BRACKET,
        r#""Name"="Alpha""#,
    ]);
    let f = parse_reg_text(&text);
    assert_eq!(f.note, Some(ParseNote::DeletesDuplicatesSkipped));
    assert_eq!(f.all_keys.len(), 1);
    assert_eq!(probe(&f).map(|n| n.values.len()), Some(1));
}

#[test]
fn duplicate_value_name_skips_with_note() {
    // m101n N8: two "v" lines -> 1 item + the note
    let text = reg(&[BRACKET, r#""v"="1""#, r#""v"="2""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.note, Some(ParseNote::DeletesDuplicatesSkipped));
    let n = probe(&f).unwrap();
    assert_eq!(n.values.len(), 1);
    assert_eq!(n.values[0].name, "v");
    assert_eq!(n.values[0].value, Value::Str("1".into())); // FIRST wins
}

#[test]
fn duplicate_key_casefold_notes() {
    // m101f F7: `\AA` then `\aa` -- folded-equal keys merge into ONE row
    // group with the note. The frame showed one item pair (the value name
    // repeats, so its second line is dup-skipped either way).
    let text = reg(&[
        r"[HKEY_CURRENT_USER\Software\ReaProbe\AA]", r#""v"="1""#,
        r"[HKEY_CURRENT_USER\Software\ReaProbe\aa]", r#""v"="1""#,
    ]);
    let f = parse_reg_text(&text);
    assert_eq!(f.note, Some(ParseNote::DeletesDuplicatesSkipped));
    let p = probe(&f).unwrap();
    assert_eq!(p.children.len(), 1);
    assert_eq!(p.children[0].name, "AA"); // first spelling wins
    assert_eq!(p.children[0].values.len(), 1);
}

#[test]
fn same_name_key_and_value_coexist() {
    // m101b G5: base holds subkey `a` AND value `a` -> both parse, no note
    // (frame: 2 same items)
    let text = reg(&[
        r"[HKEY_CURRENT_USER\Software\ReaProbe\a]", r#""v"="1""#,
        BRACKET, r#""a"="2""#,
    ]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    assert_eq!(f.note, None);
    let p = probe(&f).unwrap();
    assert_eq!(p.children.len(), 1);
    assert_eq!(p.children[0].name, "a");
    assert_eq!(p.values.len(), 1);
    assert_eq!(p.values[0].name, "a");
}

#[test]
fn default_value_uses_at_name() {
    // m101d S3/G10: @="dd" counts as a value (display name (默认) is the
    // renderer's)
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\ReaProbe\Sub]", r#"@="dd""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    let node = f
        .node(&["Software".into(), "ReaProbe".into(), "Sub".into()])
        .unwrap();
    assert_eq!(node.values[0].name, "@");
}

#[test]
fn typed_values_display_name_mapping() {
    // m101n N3 / m101d S1: hex(3) -> REG_BINARY, hex(0) -> REG_NONE with the
    // empty-data sentinel, hex(11) -> literal `0x11` (S1 pinned the code is
    // parsed as HEX), dword ffffffff -> unsigned decimal
    let text = reg(&[
        BRACKET, r#""a"=hex(3):01,00"#, r#""b"=hex(0):"#, r#""c"=hex(11):ab,cd"#,
        r#""d"=dword:ffffffff"#,
    ]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    let n = probe(&f).unwrap();
    let v: Vec<String> = n.values.iter().map(|i| i.value.type_name()).collect();
    assert_eq!(v, vec!["REG_BINARY", "REG_NONE", "0x11", "REG_DWORD"]);
    assert_eq!(
        n.values[3].value.display_text().as_deref(),
        Some("0xFFFFFFFF (4294967295)")
    );
    // empty data -> None; the localized placeholder is render-side
    // (m101e I8 / m101f F13)
    assert_eq!(n.values[1].value.display_text(), None);
}

#[test]
fn multi_sz_keeps_trailing_nul_single_sz_drops_it() {
    // m101d S1: hex(1):61,00,62,00,00,00 displays `ab` (NULs dropped);
    // m101j J3: hex(7) `ab` displays with ONE trailing NUL kept (ords)
    let sz = Value::Typed { code: 1, bytes: vec![0x61, 0, 0x62, 0, 0, 0] };
    assert_eq!(sz.type_name(), "REG_SZ");
    assert_eq!(sz.display_text().as_deref(), Some("ab"));
    let ms = Value::Typed { code: 7, bytes: vec![0x61, 0, 0x62, 0, 0, 0] };
    assert_eq!(ms.type_name(), "REG_MULTI_SZ");
    assert_eq!(ms.display_text().as_deref(), Some("ab\0"));
    // m101j J5: hex(2) expand "%PATH%" (UTF-16LE)
    let exp = Value::Typed {
        code: 2,
        bytes: "%PATH%".encode_utf16().flat_map(|u| u.to_le_bytes()).collect(),
    };
    assert_eq!(exp.type_name(), "REG_EXPAND_SZ");
    assert_eq!(exp.display_text().as_deref(), Some("%PATH%"));
}

#[test]
fn binary_display_uppercase_hex_pairs() {
    // m101n N3 `01 00 00 00 02`; m101d S1 `AB CD`
    let b = Value::Binary(vec![0x01, 0xAB]);
    assert_eq!(b.display_text().as_deref(), Some("01 AB"));
}

#[test]
fn quoted_data_escapes() {
    // m101d S15 "he said \"hi\" ok"; m101j J6 a\\b -> literal backslash
    let text = reg(&[BRACKET, r#""q"="he said \"hi\" ok""#, r#""bs"="a\\b""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    let n = probe(&f).unwrap();
    assert_eq!(n.values[0].name, "q");
    match &n.values[0].value {
        Value::Str(s) => assert_eq!(s, "he said \"hi\" ok"),
        v => panic!("{v:?}"),
    }
    match &n.values[1].value {
        Value::Str(s) => assert_eq!(s, "a\\b"),
        v => panic!("{v:?}"),
    }
}

#[test]
fn lone_cr_becomes_nul_and_is_not_a_line_break() {
    // m101n N6: `"a<CR>b"` -- the CR stays INSIDE the statement and the
    // data keeps both chars around a U+0000
    let text = format!("{}{BRACKET}{C}\"v\"=\"a\rb\"{C}", head());
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    match &probe(&f).unwrap().values[0].value {
        Value::Str(s) => assert_eq!(s, "a\0b"),
        v => panic!("{v:?}"),
    }
}

#[test]
fn basekey_rule_valued_pool_then_all_keys_fallback() {
    // the measured rule (docs/17 §basekey, G2/J1/F12/F16/M1–M7/T9/N7):
    // pool = keys with >=1 value; none valued -> all EXPLICITLY listed keys;
    // result = case-folded common prefix, first entry's spelling.
    // G2: A and B both valued under ReaProbe -> ReaProbe
    let text = reg(&[
        r"[HKEY_CURRENT_USER\Software\ReaProbe\A]", r#""v"="1""#,
        r"[HKEY_CURRENT_USER\Software\ReaProbe\B]", r#""v"="1""#,
    ]);
    let f = parse_reg_text(&text);
    assert_eq!(f.basekey.as_deref(), Some(BASE_ABS));
    // m101m M1: only [P\C] listed+valued -> the FULL listed path (implicit
    // intermediates never join the pool)
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\ReaProbe\P\C]", r#""v"="1""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.basekey.as_deref(), Some(r"HKEY_CURRENT_USER\Software\ReaProbe\P\C"));
    assert_eq!(f.all_keys.len(), 1); // P is implicit
    // M7: listed unvalued key only -> all_keys pool, full path
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\ReaProbe\P]"]);
    let f = parse_reg_text(&text);
    assert_eq!(f.basekey.as_deref(), Some(r"HKEY_CURRENT_USER\Software\ReaProbe\P"));
    // F16: unvalued Empty + valued base -> valued pool wins -> base
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\ReaProbe\Empty]", "", BRACKET, r#""z"="1""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.basekey.as_deref(), Some(BASE_ABS));
    // G1/F15 per-side: different leaf/hive on each side -> each file's own
    // full path (the renderer compares suffixes; the parser is per-side)
    let a = parse_reg_text(&reg(&[r"[HKEY_CURRENT_USER\Software\A]", r#""v"="1""#]));
    assert_eq!(a.basekey.as_deref(), Some(r"HKEY_CURRENT_USER\Software\A"));
    let l = parse_reg_text(&reg(&[r"[HKEY_LOCAL_MACHINE\Software\ProbeA]", r#""v"="1""#]));
    assert_eq!(l.basekey.as_deref(), Some(r"HKEY_LOCAL_MACHINE\Software\ProbeA"));
}

#[test]
fn utf16le_bom_decodes() {
    // m101b C11: BOM'd UTF-16LE parses identically
    let text = reg(&[BRACKET, r#""Name"="Alpha""#]);
    let u16: Vec<u8> = text.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
    let mut bytes = vec![0xFF, 0xFE];
    bytes.extend(u16);
    let f = parse_reg(&bytes);
    assert_eq!(f.error, None);
    assert_eq!(probe(&f).map(|n| n.values.len()), Some(1));
}

#[test]
fn empty_hex_is_binary_with_placeholder_sentinel() {
    // m101f F13: `hex:` alone -> REG_BINARY with empty data (display None;
    // the frame shows the localized zero-length placeholder)
    let text = reg(&[BRACKET, r#""e2"=hex:"#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    let v = &probe(&f).unwrap().values[0].value;
    assert_eq!(v.type_name(), "REG_BINARY");
    assert_eq!(v.display_text(), None);
    // F13 `e1=hex:00` displays the single byte
    let text = reg(&[BRACKET, r#""e1"=hex:00"#]);
    let f = parse_reg_text(&text);
    assert_eq!(
        probe(&f).unwrap().values[0].value.display_text().as_deref(),
        Some("00")
    );
}

#[test]
fn key_path_spaces_are_fine() {
    // m101n N7: segment with a space parses; basekey keeps it
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\My Key]", r#""v"="1""#]);
    let f = parse_reg_text(&text);
    assert_eq!(f.error, None);
    assert_eq!(f.basekey.as_deref(), Some(r"HKEY_CURRENT_USER\Software\My Key"));
    assert!(f.node(&["Software".into(), "My Key".into()]).is_some());
}

#[test]
fn deep_key_creates_implicit_intermediates() {
    // m101m M2/M6: the tree carries implicit nodes for the renderer while
    // the listing pool stays explicit-only (see M1 above)
    let text = reg(&[r"[HKEY_CURRENT_USER\Software\ReaProbe\P\C]", r#""v"="1""#]);
    let f = parse_reg_text(&text);
    let p = f
        .node(&["Software".into(), "ReaProbe".into(), "P".into()])
        .unwrap();
    assert_eq!(p.children.len(), 1);
    assert_eq!(p.children[0].name, "C");
}

#[test]
fn comparison_identity_ties_display_equivalent_forms() {
    // m101d S1: hex(1) `ab` and "ab" are the SAME type+data -> their rows
    // compare `=`; REG_SZ vs REG_EXPAND_SZ must NOT tie; dword 1 vs "1"
    // differs (m101b C5 pins the type change as a diff)
    let a = Value::Str("ab".into());
    let b = Value::Typed { code: 1, bytes: vec![0x61, 0, 0x62, 0, 0, 0] };
    assert_eq!(a.compare_identity(), b.compare_identity());
    let c = Value::Typed { code: 2, bytes: vec![0x61, 0, 0x62, 0, 0, 0] };
    assert_ne!(a.compare_identity(), c.compare_identity());
    assert_ne!(Value::Dword(1).compare_identity(), Value::Str("1".into()).compare_identity());
}

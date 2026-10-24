//! Frame-layer tests (docs/17 §frame): the measured line order, the Mode
//! line, basekey suffixes, error texts, count order, the display filters,
//! and the zero-file shell. Paths/stamps are synthetic; every STRUCTURAL
//! fact cites a measured cell.

use reacmp_reg::engine::Locale;
use reacmp_reg::parse::parse_reg_text;
use reacmp_reg::report::{
    count_lines, error_text_zh, render_registry_report, render_registry_shell, Display, Layout,
    ReportFrame,
};

fn lines(text: &str) -> Vec<String> {
    text.split("\r\n").map(|s| s.to_string()).collect()
}

#[test]
fn sbs_frame_line_order() {
    // R1-sbs-equal + G1-sid: title / Produced / blank / Mode / files /
    // [errors] / header / rule / rows / rule; NO count lines (m101c bytes).
    // The product renders Locale::EN frames (dir/pic precedent, norm-5
    // folds the Chinese golden reports onto this text).
    let l = parse_reg_text("Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"v\"=\"1\"\r\n");
    let r = l.clone();
    let text = render_registry_report(
        &ReportFrame {
            layout: Layout::SideBySide,
            display: Display::All,
            left_path: "L.reg",
            right_path: "R.reg",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &r,
    );
    let ls = lines(&text);
    assert_eq!(ls[0], "Registry Compare"); // EN title (norm-5 folds zh)
    assert_eq!(ls[1], "Produced: 2026-10-19 1:2:3");
    assert_eq!(ls[2], "");
    assert_eq!(ls[3], "Mode:  All"); // sbs always carries Mode (92/92)
    assert_eq!(ls[4], "Left file: L.reg:\\\\HKEY_CURRENT_USER\\S"); // suffix :\\ (R1)
    assert_eq!(ls[5], "Right file: R.reg:\\\\HKEY_CURRENT_USER\\S");
    assert_eq!(ls[6].matches("Name").count(), 2); // two name columns
    assert!(ls[6].starts_with("Name"));
    assert!(ls[7].starts_with('-') && ls[7].chars().all(|c| c == '-')); // rule
    let last = ls.len() - 1;
    assert!(ls[last - 1].starts_with('-')); // trailing rule
    assert!(ls[last].is_empty()); // final CRLF terminator
}

#[test]
fn summary_frame_has_counts_and_no_mode_or_table() {
    // G1-sum/C1-sum: no Mode line, no table, count lines after the file
    // lines; order same -> left orphan -> right orphan -> diff, zero
    // categories omitted (G9-sum / F4-sum / G19-title-sum).
    // A same, B left-only, C right-only, D diff -- all four categories >0.
    let l = parse_reg_text(
        "Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"A\"=\"1\"\r\n\"B\"=\"2\"\r\n\"D\"=\"x\"\r\n",
    );
    let r = parse_reg_text(
        "Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"A\"=\"1\"\r\n\"C\"=\"3\"\r\n\"D\"=\"y\"\r\n",
    );
    let text = render_registry_report(
        &ReportFrame {
            layout: Layout::Summary,
            display: Display::All,
            left_path: "L.reg",
            right_path: "R.reg",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &r,
    );
    let ls = lines(&text);
    assert_eq!(ls[3], "Left file: L.reg:\\\\HKEY_CURRENT_USER\\S"); // no Mode line
    assert!(ls.iter().any(|x| x == "1 same item(s)")); // G9-sum order head
    let idx: Vec<usize> = ["1 same item(s)", "1 important left orphan item(s)", "1 important right orphan item(s)", "1 important difference item(s)"]
        .iter()
        .map(|want| ls.iter().position(|x| x == want).unwrap())
        .collect();
    assert!(idx.windows(2).all(|w| w[0] < w[1]), "count order {idx:?}");
    assert!(!ls.iter().any(|x| x.contains("Name"))); // no table
}

#[test]
fn error_line_order_is_left_then_right_after_files() {
    // I5-parseerr / I6-deletedup / N4-only-bad: the error lines sit between
    // the file lines and the table/counts (picture precedent m83).
    let mut text = String::from("Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"v\"=\"1\"\r\n");
    text.push_str("garbage\r\n");
    let l = parse_reg_text(&text);
    let r = parse_reg_text("bad header");
    let out = render_registry_report(
        &ReportFrame {
            layout: Layout::Summary,
            display: Display::All,
            left_path: "L.reg",
            right_path: "R.reg",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &r,
    );
    let ls = lines(&out);
    assert!(ls.iter().any(|x| x == "Left error: Parsing Error (5: 1)"), "{ls:?}");
    assert!(ls.iter().any(|x| x == "Right error: Unsupported Type"), "{ls:?}");
    // error lines precede the count line
    let err = ls.iter().position(|x| x.starts_with("Left error")).unwrap();
    let cnt = ls.iter().position(|x| x.contains("item(s)")).unwrap();
    assert!(err < cnt);
    assert_eq!(error_text_zh(&l.error.clone().unwrap()), "解析错误 (5： 1)");
}

#[test]
fn dup_note_renders_as_error_line_with_suffix_kept() {
    // I6-deletedup: `删除/重复跳过` renders in the error-line slot; the
    // basekey suffix stays (the key survived).
    let l = parse_reg_text(
        "Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"v\"=\"1\"\r\n\"v\"=\"2\"\r\n",
    );
    let out = render_registry_report(
        &ReportFrame {
            layout: Layout::Summary,
            display: Display::All,
            left_path: "L.reg",
            right_path: "R.reg",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &l,
    );
    assert!(out.contains("Left error: Deletes/Duplicates Skipped"), "{out}");
    assert!(out.contains("Left file: L.reg:\\\\HKEY_CURRENT_USER\\S"));
}

#[test]
fn encoding_side_loses_the_suffix_and_prints_line1() {
    // R19-png-pair / I7-png: file lines WITHOUT suffix, `File Encoding
    // Error (Line 1)` on both sides, exit still 0, summary counts nothing.
    let png = {
        let mut b = vec![0x89, b'P', b'N', b'G', 0x0d, 0x1a, 0x0a, 0x0a];
        b.extend(vec![0u8; 40]);
        b
    };
    let f = reacmp_reg::parse_reg(&png);
    let out = render_registry_report(
        &ReportFrame {
            layout: Layout::Summary,
            display: Display::All,
            left_path: "p1.png",
            right_path: "p2.png",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &f,
        &f,
    );
    assert!(out.contains("Left file: p1.png\r\n"), "{out}"); // no :\\ suffix
    assert!(out.contains("Left error: File Encoding Error (Line 1)"), "{out}");
    assert!(!out.contains("item(s)"), "no counts: {out}");
}

#[test]
fn title_replaces_line_one_and_mode_tracks_display() {
    // R16 (title) + I4/I12 (Mode:  Differences / Same on sbs).
    let l = parse_reg_text("Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"v\"=\"1\"\r\n");
    let out = render_registry_report(
        &ReportFrame {
            layout: Layout::SideBySide,
            display: Display::Mismatches,
            left_path: "L.reg",
            right_path: "R.reg",
            stamp: "2026-10-19 1:2:3",
            title: Some("RegTitle"),
            locale: &Locale::EN,
        },
        &l,
        &l,
    );
    assert!(out.starts_with("RegTitle\r\n"), "{out}");
    assert!(out.contains("Mode:  Differences"), "{out}");
}

#[test]
fn mismatches_and_matches_filters_have_the_measured_shape() {
    // I4-sbs-dmism-box: the +- orphan rows survive, the matched `=` row is
    // dropped; I12-sbs-dmatch: only the `=` row survives (the `Kx` header
    // and the orphan rows drop). Geometry recomputes on the kept set (I4
    // rule length 24 vs the unfiltered 28: measured, docs/17 §frame).
    let l = parse_reg_text(
        "Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S\\Kx]\r\n\"a\"=\"1\"\r\n\"b\"=\"2\"\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"z\"=\"1\"\r\n",
    );
    let r = parse_reg_text("Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\S]\r\n\"z\"=\"1\"\r\n");
    let mism = render_registry_report(
        &ReportFrame {
            layout: Layout::SideBySide,
            display: Display::Mismatches,
            left_path: "L",
            right_path: "R",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &r,
    );
    assert!(!mism.contains(" = "), "same row filtered: {mism}");
    assert!(mism.contains("+-"), "orphans kept: {mism}");
    let match_only = render_registry_report(
        &ReportFrame {
            layout: Layout::SideBySide,
            display: Display::Matches,
            left_path: "L",
            right_path: "R",
            stamp: "2026-10-19 1:2:3",
            title: None,
            locale: &Locale::EN,
        },
        &l,
        &r,
    );
    assert!(!match_only.contains("Kx"), "header dropped: {match_only}");
    assert!(!match_only.contains("+-"), "orphans dropped: {match_only}");
    assert!(match_only.contains(" = "), "same row kept: {match_only}");
}

#[test]
fn shell_is_bom_title_produced_mode_base_folder() {
    // R11-zero-files (99 bytes zh) measured head lines: title / Produced /
    // blank / Mode:  全部 / 基点文件夹： -- the EN product form mirrors it
    // with the Mode line (unlike picture's shell, registry's carries it).
    let out = render_registry_shell("2026-10-19 1:2:3", None, Display::All);
    assert!(out.starts_with('\u{feff}'), "BOM first");
    let ls: Vec<&str> = out.split("\r\n").collect();
    // ls[0] carries the BOM glued to the title (the executor writes the
    // leading U+FEFF; norm-4's BOM strip folds it for comparison).
    assert_eq!(ls[0], "\u{feff}Registry Compare");
    assert_eq!(
        &ls[1..5],
        &[
            "Produced: 2026-10-19 1:2:3",
            "",
            "Mode:  All",
            "Base folder: ",
        ]
    );
    assert_eq!(ls[5], ""); // trailing CRLF
}

#[test]
fn zero_omitted_count_order() {
    // G4-sum (0 same, no orphans -> NOTHING printed): only the >0
    // categories appear.
    let empty = Default::default();
    assert!(count_lines(&empty).is_empty());
    let c = reacmp_reg::Counts { same: 2, left_orphan: 1, right_orphan: 0, diff: 3 };
    assert_eq!(
        count_lines(&c),
        vec![
            "2 same item(s)",
            "1 important left orphan item(s)",
            "3 important difference item(s)"
        ]
    );
}

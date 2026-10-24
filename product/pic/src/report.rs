//! The Picture Compare report renderer — frame geometry measured cell by cell
//! (`docs/16` §1/§4, runs/m83* Chinese + m83k/m83l/m83m English).
//!
//! Frame lines, in order, each CRLF-terminated, no trailing blank line:
//!
//! ```text
//! [title | "Picture Compare"]
//! Produced: <stamp>
//! <empty>
//! [Ignoring Unimportant]     only with options:ignore-unimportant (both layouts)
//! [Base folder: <path>]      zero-file form ONLY — replaces the two file lines
//! [Left file: <L>]           normal form
//! [Right file: <R>]
//! [Left error: <msg>]        when the left file is not a decodable picture
//! [Right error: <msg>]       ditto (errors print before any count lines)
//! <count lines>              summary layout only; zero categories omitted;
//!                            order same → unimportant → left-only → right-only
//!                            → important (m83h/i/j)
//! ```
//!
//! Measured byte rules:
//! * the **zero-file** shell carries a UTF-8 BOM (76 bytes Chinese, 67 English);
//!   a report with files does **not** (m83 P8/P11, m83k E3);
//! * `side-by-side` prints the frame and nothing else — no count lines even
//!   with `ignore-unimportant` (m83k E1, m83m EN-sbs-ignore);
//! * an error on one side suppresses the counts that would compare that side,
//!   but the *other* side's surplus pixels are still counted, against a
//!   same-sized phantom (m83l EN-mixed-error: right error + `16 left orphan`);
//! * error kinds: `Unsupported Type` (no picture signature) vs `Invalid image`
//!   (picture signature, bad payload) — m83 P12 vs m83i V3, m83l EN-gif-invalid
//!   shows both in one frame independently.

use crate::compare::{compare_rasters, CompareOptions, PictureCounts};
use crate::decode::{decode_image, ImageError};

/// One side's decoded-or-failed result, kept so the renderer can place the
/// error line exactly where the Oracle puts it.
#[derive(Debug)]
pub enum SideImage {
    Ok(crate::Raster),
    Err(ImageError),
}

impl SideImage {
    pub fn decode(data: &[u8]) -> SideImage {
        match decode_image(data) {
            Ok(r) => SideImage::Ok(r),
            Err(e) => SideImage::Err(e),
        }
    }
}

/// Which of the two measured layouts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PictureLayout {
    SideBySide,
    Summary,
}

impl PictureLayout {
    pub const NAMES: &'static str = "side-by-side, summary";

    pub fn parse(word: &str) -> Option<PictureLayout> {
        match word.to_ascii_lowercase().as_str() {
            "side-by-side" => Some(PictureLayout::SideBySide),
            "summary" => Some(PictureLayout::Summary),
            _ => None,
        }
    }
}

/// The localized label table for one install flavour. `english` is what the
/// harness normalizes to (norm-4 folds the Chinese repack's lines onto these),
/// so the renderer always emits the English strings and the golden path only
/// ever compares normalized text — the same split `reacmp_dir::report` uses
/// for folder reports (Chinese labels stay the Oracle's job; ours are English,
/// and normalize.py folds a reference run onto them).
const COUNT_LABELS: [(&str, &str); 5] = [
    ("same", "{n} same pixel(s)"),
    ("unimportant", "{n} unimportant difference pixel(s)"),
    ("left-only", "{n} left orphan pixel(s)"),
    ("right-only", "{n} right orphan pixel(s)"),
    ("important", "{n} important difference pixel(s)"),
];

const IGNORED_LABEL: &str = "{n} ignored unimportant difference pixel(s)";

/// Render the whole report. `left`/`right` are the file paths as the script
/// named them (the frame prints them verbatim, Windows separators included).
pub fn render_picture_report(
    layout: PictureLayout,
    left: &SideImage,
    right: &SideImage,
    left_path: &str,
    right_path: &str,
    stamp: &str,
    title: Option<&str>,
    options: &CompareOptions,
) -> String {
    let mut lines: Vec<String> = Vec::new();
    lines.push(title.unwrap_or("Picture Compare").to_string());
    lines.push(format!("Produced: {stamp}"));
    lines.push(String::new());
    if options.ignore_unimportant {
        lines.push("Ignoring Unimportant".to_string());
    }
    lines.push(format!("Left file: {left_path}"));
    lines.push(format!("Right file: {right_path}"));

    let le = err_text(left);
    let re = err_text(right);
    if let Some(t) = &le {
        lines.push(format!("Left error: {t}"));
    }
    if let Some(t) = &re {
        lines.push(format!("Right error: {t}"));
    }

    if layout == PictureLayout::SideBySide {
        return join_crlf(&lines);
    }

    // Summary. An errored side has no raster, and the Oracle still counts the
    // healthy side's surplus against an equal overlap (m83l EN-mixed-error:
    // right error, 16 left-orphan of a 4x4 left against... exactly the left's
    // own pixels). So a failed side is modelled as a same-size raster that
    // matches nothing: overlap pixels land in "left/right orphan"? No —
    // measured says 16 LEFT ORPHAN, the same size as the whole healthy side:
    // the phantom contributes zero overlap pixels, every healthy pixel is a
    // surplus of its own side. (docs/16 §5 records the phantom-size question
    // as a residual unknown: we cannot distinguish a same-size phantom with no
    // matched pixels from "all pixels orphan" with the cells measured.)
    let counts = match (left, right) {
        (SideImage::Ok(l), SideImage::Ok(r)) => compare_rasters(l, r),
        (SideImage::Ok(l), SideImage::Err(_)) => PictureCounts {
            left_only: l.width * l.height,
            ..Default::default()
        },
        (SideImage::Err(_), SideImage::Ok(r)) => PictureCounts {
            right_only: r.width * r.height,
            ..Default::default()
        },
        (SideImage::Err(_), SideImage::Err(_)) => PictureCounts::default(),
    };
    for (key, count) in counts.lines(options) {
        let fmt = if key == "ignored-unimportant" {
            IGNORED_LABEL
        } else {
            COUNT_LABELS.iter().find(|(k, _)| *k == key).map(|(_, f)| *f).expect("label")
        };
        lines.push(fmt.replace("{n}", &count.to_string()));
    }
    join_crlf(&lines)
}

/// The zero-file shell measured at 76/67 bytes: base folder (empty), no file
/// lines, no errors, no counts — even for `layout:summary` with files that
/// were never supplied (`picture-report layout:summary output-to:"%3"` alone,
/// m83 P8 / m83k E3). The BOM belongs to this shell only, and is written as
/// the U+FEFF character the way [`reacmp_dir`] writes the XML shells — the
/// executor's `write_report` turns the leading character into the three bytes
/// `EF BB BF` (m83: `P8-zero-files.out` starts with them).
pub fn render_picture_shell(stamp: &str, title: Option<&str>) -> String {
    format!(
        "\u{feff}{}\r\nProduced: {stamp}\r\n\r\nBase folder: \r\n",
        title.unwrap_or("Picture Compare")
    )
}

fn err_text(side: &SideImage) -> Option<&'static str> {
    match side {
        SideImage::Ok(_) => None,
        SideImage::Err(ImageError::NotSupported) => Some("Unsupported Type"),
        SideImage::Err(ImageError::Invalid) => Some("Invalid image"),
    }
}

fn join_crlf(lines: &[String]) -> String {
    let mut s = String::new();
    for l in lines {
        s.push_str(l);
        s.push_str("\r\n");
    }
    s
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::compare::CompareOptions;

    fn solid(w: usize, h: usize, v: u8) -> SideImage {
        SideImage::Ok(crate::Raster {
            width: w,
            height: h,
            pixels: vec![v; w * h * 3],
        })
    }

    #[test]
    fn frame_has_title_produced_blank_then_files() {
        // m83k E1: 5 lines for side-by-side, no counts.
        let r = render_picture_report(
            PictureLayout::SideBySide,
            &solid(8, 8, 10),
            &solid(8, 8, 10),
            r"C:\a.png",
            r"C:\b.png",
            "TIME",
            None,
            &CompareOptions::default(),
        );
        let lines: Vec<&str> = r.trim_end().split("\r\n").collect();
        assert_eq!(
            lines,
            [
                "Picture Compare",
                "Produced: TIME",
                "",
                "Left file: C:\\a.png",
                "Right file: C:\\b.png"
            ]
        );
    }

    #[test]
    fn summary_counts_in_measured_order_with_zeroes_dropped() {
        // m83b Q1 (zero dropped) and m83h F.all4 (the 5-category order).
        let opts = CompareOptions::default();
        let r = render_picture_report(
            PictureLayout::Summary,
            &solid(6, 8, 128),
            &solid(8, 6, 128),
            "L",
            "R",
            "TIME",
            None,
            &opts,
        );
        // 36 same, 12 left-only, 12 right-only (m83j).
        assert!(r.contains("36 same pixel(s)\r\n"), "{r}");
        assert!(r.contains("12 left orphan pixel(s)\r\n12 right orphan pixel(s)"), "{r}");
    }

    #[test]
    fn ignore_flag_adds_header_line_and_renames_label() {
        // m83i V2 + m83m EN-ignore.
        let opts = CompareOptions { ignore_unimportant: true };
        let r = render_picture_report(
            PictureLayout::Summary,
            &solid(4, 4, 128),
            &solid(4, 4, 140),
            "L",
            "R",
            "TIME",
            None,
            &opts,
        );
        assert!(r.contains("\r\nIgnoring Unimportant\r\nLeft file:"), "{r}");
        assert!(r.contains("16 ignored unimportant difference pixel(s)"), "{r}");
        // and side-by-side keeps the header but prints no counts (m83m EN-sbs-ignore).
        let r2 = render_picture_report(
            PictureLayout::SideBySide,
            &solid(4, 4, 128),
            &solid(4, 4, 140),
            "L",
            "R",
            "TIME",
            None,
            &opts,
        );
        assert!(r2.contains("Ignoring Unimportant"));
        assert!(!r2.contains("pixel"), "{r2}");
    }

    #[test]
    fn error_kinds_and_surplus_counting() {
        // m83 P12 / m83i V3: two distinct strings; m83l EN-gif-invalid: both
        // sides can differ in kind. EN-mixed-error: healthy side's full pixel
        // count lands on its own side.
        let bad_type = SideImage::Err(ImageError::NotSupported);
        let invalid = SideImage::Err(ImageError::Invalid);
        let r = render_picture_report(
            PictureLayout::Summary,
            &solid(4, 4, 0),
            &bad_type,
            "L",
            "R",
            "TIME",
            None,
            &CompareOptions::default(),
        );
        assert!(r.contains("Right error: Unsupported Type\r\n16 left orphan pixel(s)"), "{r}");
        let r2 = render_picture_report(
            PictureLayout::Summary,
            &invalid,
            &bad_type,
            "L",
            "R",
            "TIME",
            None,
            &CompareOptions::default(),
        );
        assert!(r2.contains("Left error: Invalid image\r\nRight error: Unsupported Type"), "{r2}");
        assert!(r2.trim_end().ends_with("Right error: Unsupported Type"), "{r2}");
    }

    #[test]
    fn title_replaces_the_first_frame_line() {
        // m83 P11.
        let r = render_picture_report(
            PictureLayout::SideBySide,
            &solid(1, 1, 0),
            &solid(1, 1, 0),
            "L",
            "R",
            "TIME",
            Some("PicTitle"),
            &CompareOptions::default(),
        );
        assert!(r.starts_with("PicTitle\r\n"), "{r}");
    }

    #[test]
    fn zero_file_shell_is_bom_prefixed() {
        // m83 P8 (76 B) / m83k E3 (67 B): BOM only on this shape.
        let s = render_picture_shell("TIME", None);
        assert_eq!(s.as_bytes()[..3], [0xEF, 0xBB, 0xBF]);
        assert_eq!(&s[3..], "Picture Compare\r\nProduced: TIME\r\n\r\nBase folder: \r\n");
    }
}

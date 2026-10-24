//! Executor tests (M4 task B).
//!
//! # What these tests are, and are not
//!
//! Each test drives [`reacmp_cli`'s executor] through its **public** entry point
//! — `reacmp-cli` is a binary crate, so this integration test includes the
//! module tree by path (see the bottom of this file) rather than linking a
//! library.  Comparisons are against the *measured* shapes from the u5 probe
//! series: the 122/155/272-byte shells, the `<filters>` position, the `<size/>`
//! rule and the exit codes. The Oracle's absolute paths are not reproduced (a
//! temp directory is used instead), so the assertions are on structure and
//! byte counts that are path-independent, plus the parts of the body that are.
//!
//! `created="…"` is wall-clock, so every body assertion replaces it first with
//! the harness's own placeholder. That mirrors
//! `product/verify/harness/normalize.py`, which folds the attribute to `TIME`
//! before comparing — so a test that passes here is testing the same bytes the
//! harness will compare.

use std::fs;
use std::path::{Path, PathBuf};

use ast::{Command, ExpandPaths, LogMode, ReportSpec};
use exec::run_script;

// ==========================================================================
// Harness
// ==========================================================================

/// A fresh scratch directory per test.
///
/// `std::env::temp_dir()` + the test's own name keeps runs independent, and the
/// comparison never writes inside a fixture — reports go to a sibling path the
/// test passes explicitly, exactly as a script's `output-to:` does.
struct Scratch {
    root: PathBuf,
}

impl Scratch {
    fn new(name: &str) -> Scratch {
        let root = std::env::temp_dir().join(format!("reacmp-exec-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).expect("scratch dir");
        Scratch { root }
    }

    fn path(&self, rel: &str) -> PathBuf {
        self.root.join(rel)
    }

    fn str(&self, rel: &str) -> String {
        self.path(rel).to_string_lossy().into_owned()
    }

    fn dir(&self, rel: &str) -> String {
        let p = self.path(rel);
        fs::create_dir_all(&p).expect("mkdir");
        p.to_string_lossy().into_owned()
    }

    fn file(&self, rel: &str, bytes: &[u8]) -> String {
        let p = self.path(rel);
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent).expect("mkdir -p");
        }
        fs::write(&p, bytes).expect("write fixture");
        p.to_string_lossy().into_owned()
    }

    fn read(&self, rel: &str) -> String {
        let bytes = fs::read(self.path(rel)).expect("read report");
        String::from_utf8_lossy(&bytes).into_owned()
    }

    fn bytes(&self, rel: &str) -> Vec<u8> {
        fs::read(self.path(rel)).expect("read report")
    }

    /// Copy picture fixtures from `tests/picfix/` into the scratch and return
    /// their paths, in order. The fixtures are the ones the picture engine is
    /// built for (`reacmp-pic/tests/pic-*`), so a CLI test exercises the same
    /// bytes the Oracle was probed with (docs/16), not a re-implementation.
    fn pix(&self, names: &[&str]) -> Vec<String> {
        names
            .iter()
            .map(|n| {
                let src = Path::new(env!("CARGO_MANIFEST_DIR"))
                    .join("tests/picfix")
                    .join(format!("pic-{n}"));
                self.file(n, &fs::read(&src).unwrap_or_else(|e| panic!("{n}: {e}")))
            })
            .collect()
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

/// The u5g fixture tree: `A/B/f.txt(6)`, `A/g.txt(4)`, `C/i.txt(3)`, `h.txt(5)`.
fn u5g_tree(s: &Scratch) {
    for side in ["L", "R"] {
        s.file(&format!("{side}/A/B/f.txt"), b"ffffff");
        s.file(&format!("{side}/A/g.txt"), b"gggg");
        s.file(&format!("{side}/C/i.txt"), b"iii");
        s.file(&format!("{side}/h.txt"), b"hhhhh");
    }
}

/// Replace the volatile `created="…"` values with the harness's `TIME` token,
/// exactly as `verify/harness/normalize.py` does, so a byte assertion can be
/// made against a wall-clock report.
fn fold_time(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut rest = text;
    while let Some(idx) = rest.find("created=\"") {
        let (head, tail) = rest.split_at(idx + "created=\"".len());
        out.push_str(head);
        match tail.find('"') {
            Some(end) => {
                out.push_str("TIME");
                rest = &tail[end..];
            }
            None => {
                out.push_str(tail);
                return out;
            }
        }
    }
    out.push_str(rest);
    out
}

/// Run a script, returning (exit code, normalised report bodies in order).
fn run(cmds: Vec<Command>, argv: &[&str]) -> (i32, Vec<String>) {
    let argv: Vec<String> = argv.iter().map(|s| s.to_string()).collect();
    let outcome = run_script(&cmds, &argv);
    let reports = outcome
        .reports
        .iter()
        .map(|p| fold_time(&fs::read_to_string(p).unwrap_or_default()))
        .collect();
    (outcome.exit_code, reports)
}

fn load(left: &str, right: &str, line: usize) -> Command {
    Command::Load {
        left: left.to_string(),
        right: Some(right.to_string()),
        line,
    }
}

fn expand_all(line: usize) -> Command {
    Command::Expand {
        paths: ExpandPaths::All,
        line,
    }
}

fn expand_named(paths: &[&str], line: usize) -> Command {
    Command::Expand {
        paths: ExpandPaths::Named(paths.iter().map(|s| s.to_string()).collect()),
        line,
    }
}

fn filter(masks: &str, line: usize) -> Command {
    Command::Filter {
        masks: masks.to_string(),
        line,
    }
}

fn criteria(spec: &str, line: usize) -> Command {
    Command::Criteria {
        spec: spec.to_string(),
        line,
    }
}

fn option(name: &str, line: usize) -> Command {
    Command::Option {
        name: name.to_string(),
        line,
    }
}

fn folder_report(layout: &str, output: &str, line: usize) -> Command {
    Command::FolderReport {
        spec: ReportSpec {
            layout: layout.to_string(),
            output_to: Some(output.to_string()),
            ..ReportSpec::default()
        },
        line,
    }
}

fn text_report(layout: &str, output: &str, comparison: &[&str], line: usize) -> Command {
    Command::TextReport {
        spec: ReportSpec {
            layout: layout.to_string(),
            output_to: Some(output.to_string()),
            comparison: comparison.iter().map(|s| s.to_string()).collect(),
            ..ReportSpec::default()
        },
        line,
    }
}

fn data_report(layout: &str, output: &str, comparison: &[&str], line: usize) -> Command {
    Command::TableReport {
        word: "data-report".to_string(),
        spec: ReportSpec {
            layout: layout.to_string(),
            output_to: Some(output.to_string()),
            comparison: comparison.iter().map(|s| s.to_string()).collect(),
            ..ReportSpec::default()
        },
        line,
    }
}

// ==========================================================================
// M6 data-report: the measured CLI surface (docs/13 §4.7, §5, runs/m63-*)
// ==========================================================================

#[test]
fn table_report_parses_as_the_same_variant_and_runs_identically() {
    // X1 (runs/m63-clisurface-*): BC accepts `table-report` as a spelling of
    // `data-report`.  The executor keys on the variant, not the word, so the
    // two spellings produce the same bytes.
    let s = Scratch::new("table-spellings");
    let l = s.file("L.csv", b"k,1\n");
    let r = s.file("R.csv", b"k,2\n");
    let out1 = s.str("a.out");
    let out2 = s.str("b.out");
    let cmd1 = data_report("side-by-side", &out1, &[&l, &r], 1);
    let cmd2 = Command::TableReport {
        word: "table-report".to_string(),
        spec: ReportSpec {
            layout: "side-by-side".to_string(),
            output_to: Some(out2.clone()),
            comparison: vec![l.clone(), r.clone()],
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (c1, b1) = run(vec![cmd1], &[]);
    let (c2, b2) = run(vec![cmd2], &[]);
    assert_eq!(c1, 0);
    assert_eq!(c2, 0);
    let fold = |t: &str| fold_stamp(t);
    assert_eq!(fold(&b1[0]), fold(&b2[0]), "both spellings write the same bytes");
}

#[test]
fn data_report_side_by_side_writes_the_measured_body() {
    // T1/X1 measured: frame "Table Compare / Produced / (blank) / Mode:  All
    // / Left file / Right file", body with ' = '/'<>' markers.  The stamp is
    // wall-clock, folded like normalize.py folds Produced:.
    let s = Scratch::new("table-sbs");
    let l = s.file("L.csv", b"h,1\na,2\nb,3\n");
    let r = s.file("R.csv", b"h,1\na,9\nc,4\n");
    let out = s.str("r.out");
    let (code, reports) = run(vec![data_report("side-by-side", &out, &[&l, &r], 1)], &[]);
    assert_eq!(code, 0);
    let body = fold_stamp(&reports[0]);
    assert!(body.starts_with("Table Compare\r\nProduced: TIME\r\n\r\nMode:  All\r\n"));
    assert!(body.contains("Left file: "));
    assert!(body.contains("Right file: "));
    // h =; the replaced gap [a,2 / b,3] vs [a,9 / c,4] zips to two `<>`
    // pairs (P1/P2: no closeness, positional zip).
    assert!(body.contains("h 1 =  h 1"), "got {body:?}");
    assert!(body.contains("a 2 <> a 9"), "got {body:?}");
    assert!(body.contains("b 3 <> c 4"), "got {body:?}");
    assert!(!reports[0].contains("+-"));
    assert!(!reports[0].contains("-+"));
    // no BOM (measured: table reports carry none)
    assert_eq!(s.bytes("r.out")[0], b'T');
}

fn fold_stamp(text: &str) -> String {
    // `Produced: <stamp>` is the table channel's wall-clock field; fold it to
    // TIME exactly as harness normalize.py does for text reports.
    let mut out = String::new();
    let mut rest = text;
    while let Some(idx) = rest.find("Produced: ") {
        let end = rest[idx + "Produced: ".len()..]
            .find('\r')
            .map(|e| idx + "Produced: ".len() + e)
            .unwrap_or(rest.len());
        out.push_str(&rest[..idx]);
        out.push_str("Produced: TIME");
        rest = &rest[end..];
    }
    out.push_str(rest);
    out
}

#[test]
fn data_report_options_any_value_is_105_with_no_report() {
    // P6-P9 measured: any options payload exits 105 and writes nothing.
    let s = Scratch::new("table-options");
    let l = s.file("L.csv", b"k,1\n");
    let r = s.file("R.csv", b"k,2\n");
    let out = s.str("never.out");
    let mut cmd = data_report("side-by-side", &out, &[&l, &r], 1);
    if let Command::TableReport { spec, .. } = &mut cmd {
        spec.options = vec!["display-mismatches".to_string()];
    }
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 105);
    assert!(reports.is_empty());
    assert!(!Path::new(&out).exists(), "no placeholder report may be written");
}

#[test]
fn data_report_output_options_is_106() {
    // X8 measured: `output-options:csv` on data-report exits 106 (the
    // script-command class), distinct from the 105 of `options:`.
    let s = Scratch::new("table-outopts");
    let l = s.file("L.csv", b"k,1\n");
    let r = s.file("R.csv", b"k,2\n");
    let out = s.str("never.out");
    let mut cmd = data_report("side-by-side", &out, &[&l, &r], 1);
    if let Command::TableReport { spec, .. } = &mut cmd {
        spec.output_options = vec!["csv".to_string()];
    }
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn data_report_xml_layout_is_106_with_no_report() {
    // T2 measured: the table engine has no xml layout.
    let s = Scratch::new("table-xml");
    let out = s.str("never.out");
    let (code, reports) = run(vec![data_report("xml", &out, &[], 1)], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn data_report_without_files_is_107() {
    // X5 measured: no path-only shell exists for the table channel.
    let s = Scratch::new("table-nofiles");
    let out = s.str("never.out");
    let (code, reports) = run(vec![data_report("side-by-side", &out, &[], 1)], &[]);
    assert_eq!(code, 107);
    assert!(reports.is_empty());
}

#[test]
fn data_report_missing_file_is_107() {
    // X7 measured.
    let s = Scratch::new("table-missing");
    let out = s.str("never.out");
    let missing = s.str("absent.csv");
    let present = s.file("R.csv", b"x,1\n");
    let (code, reports) = run(
        vec![data_report("summary", &out, &[&missing, &present], 1)],
        &[],
    );
    assert_eq!(code, 107);
    assert!(reports.is_empty());
}

#[test]
fn data_report_three_files_is_106() {
    // X6 measured: at most two comparison files.
    let s = Scratch::new("table-three");
    let l = s.file("L.csv", b"k,1\n");
    let r = s.file("R.csv", b"k,2\n");
    let out = s.str("never.out");
    let (code, reports) = run(vec![data_report("summary", &out, &[&l, &r, &l], 1)], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn data_report_title_replaces_the_first_frame_line() {
    // X4 measured: `title:"MyTitle"` makes the report start with MyTitle.
    let s = Scratch::new("table-title");
    let l = s.file("L.csv", b"k,1\n");
    let r = s.file("R.csv", b"k,2\n");
    let out = s.str("r.out");
    let mut cmd = data_report("summary", &out, &[&l, &r], 1);
    if let Command::TableReport { spec, .. } = &mut cmd {
        spec.title = Some("MyTitle".to_string());
    }
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 0);
    assert!(reports[0].starts_with("MyTitle\r\n"), "got {:?}", &reports[0][..40]);
    assert!(!reports[0].contains("Table Compare"));
    assert!(!reports[0].contains("Mode:")); // summary frame
    assert!(reports[0].contains("1 important difference row(s)"));
}

#[test]
fn data_report_is_a_script_command_not_an_argument() {
    // Both spellings moved from the unimplemented list to the script-command
    // list in args.rs (M6 graduation); a bare command line must point at
    // @<script>, like text-report does.
    for cmd in ["data-report", "table-report"] {
        let err = parse_script_cmdline(cmd);
        assert!(err.contains("script command"), "{cmd}: {err}");
    }
}

fn parse_script_cmdline(word: &str) -> String {
    // args.rs is compiled into the bin; the integration tree cannot include
    // it by path without duplicating its module deps, so the surface check
    // mirrors the SCRIPT_COMMANDS_NOT_ARGUMENTS contract through the binary:
    // run `reacmp <word> a b` and read stderr.
    let exe = env!("CARGO_BIN_EXE_reacmp");
    let out = std::process::Command::new(exe)
        .args([word, "a", "b"])
        .output()
        .expect("run reacmp");
    String::from_utf8_lossy(&out.stderr).into_owned()
}

/// `<size>` of the row whose name is `name`, or `None` when the row renders
/// `<size/>`.
///
/// The search is anchored on the row's ELEMENT start so a paired row's two
/// sides are distinguishable: `side` picks which of the two blocks is read.
fn size_of_side(report: &str, name: &str, side: &str) -> Option<String> {
    let needle = format!("<name>{name}</name>");
    let mut rest = report;
    loop {
        let Some(idx) = rest.find(&needle) else { return None };
        // Which side block are we inside? Look back for the nearest `<lt>` or
        // `<rt>` that has no closing tag after it.
        let before = &rest[..idx];
        let lt = before.rfind("<lt>");
        let rt = before.rfind("<rt>");
        let side_found = match (lt, rt) {
            (Some(a), Some(b)) => {
                if a > b {
                    "lt"
                } else {
                    "rt"
                }
            }
            (Some(_), None) => "lt",
            (None, Some(_)) => "rt",
            (None, None) => return None,
        };
        let tail = &rest[idx + needle.len()..];
        let block = tail
            .split(&format!("</{side_found}>"))
            .next()
            .unwrap_or(tail);
        if side_found == side {
            if block.contains("<size/>") {
                return None;
            }
            let Some(s) = block.find("<size>") else { return None };
            let rest_of = &block[s + "<size>".len()..];
            let end = rest_of.find("</size>")?;
            return Some(rest_of[..end].to_string());
        }
        // Try the next occurrence (a paired row shows the name twice).
        rest = &tail[block.len()..];
    }
}

/// `<size>` of the first `<name>` block with this name (either side).
fn size_of(report: &str, name: &str) -> Option<String> {
    size_of_side(report, name, "lt").or_else(|| size_of_side(report, name, "rt"))
}

/// The `<name>` values of every rendered **row**, in document order.
///
/// A row is a `<foldercomp>` or `<filecomp>` element and its FIRST `<name>`
/// child is the row's name: a paired row then repeats the same name inside
/// `<rt>`, and a one-sided row has only the one, so taking only the first name
/// per row is what makes this a row list rather than a side list.
fn names(report: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut rest = report;
    loop {
        // The next row start is whichever of the two element kinds comes first.
        let next_folder = rest.find("<foldercomp>");
        let next_file = rest.find("<filecomp");
        let Some(idx) = (match (next_folder, next_file) {
            (Some(a), Some(b)) => Some(a.min(b)),
            (Some(a), None) => Some(a),
            (None, Some(b)) => Some(b),
            (None, None) => None,
        }) else {
            break;
        };
        // Skip past the element's own tag up to its first `<name>`.
        let after = &rest[idx..];
        let Some(name_start) = after.find("<name>") else { break };
        let tail = &after[name_start + "<name>".len()..];
        let Some(name_end) = tail.find("</name>") else { break };
        out.push(tail[..name_end].to_string());
        rest = &tail[name_end..];
    }
    out
}

/// True when the report has a `<filters>` element.
fn filters_text(report: &str) -> Option<String> {
    let after = report.split("<filters>").nth(1)?;
    Some(after.split("</filters>").next()?.to_string())
}

// ==========================================================================
// Shell reports — the measured 122 / 155 / 272-byte shapes
// ==========================================================================

#[test]
fn folder_report_without_load_writes_the_155_byte_shell() {
    // u5 `folder-report-no-load` and u5b: exit 0, 155 bytes, `<ltpath/>` +
    // `<rtpath/>` inside an empty `<foldercomp>`.
    let s = Scratch::new("folder-shell");
    let out = s.str("shell.xml");
    let (code, reports) = run(vec![folder_report("xml", &out, 1)], &[]);
    assert_eq!(code, 0);
    assert_eq!(reports.len(), 1);
    // With `created="TIME"` the byte count is 155 - 19 + 4 = 140.
    assert_eq!(
        reports[0],
        "\u{feff}<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n\
         <bcreport created=\"TIME\">\r\n\
         \t<foldercomp>\r\n\
         \t\t<ltpath/>\r\n\
         \t\t<rtpath/>\r\n\
         \t</foldercomp>\r\n\
         </bcreport>\r\n"
    );
    // The untouched bytes are the measured 155 only for a 19-character stamp.
    // BC does NOT pad a single-digit hour -- measured directly at 01:52 on
    // 2026-10-16 by `runs/log-hour-pad-probe` (log line `2026-10-16 1:52:09`,
    // 18 characters, same shape in `created=`). Assert the clock-independent
    // folded shape instead: 155 - 19 + 4 = 140 with the stamp folded.
    assert_eq!(fold_time(&s.read("shell.xml")).len(), 140);
}

#[test]
fn load_default_also_produces_the_empty_folder_shell() {
    // u5g s10 `load <default>`: accepted, and the report is the same 155-byte
    // shape as no `load` at all.
    let s = Scratch::new("load-default");
    let out = s.str("shell.xml");
    let (code, reports) = run(
        vec![
            Command::Load {
                left: "<default>".to_string(),
                right: None,
                line: 1,
            },
            folder_report("xml", &out, 2),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(
        reports[0].contains("\t\t<ltpath/>\r\n\t\t<rtpath/>\r\n"),
        "{}",
        reports[0]
    );
    assert!(!reports[0].contains("<foldercomp>\r\n\t\t<ltpath>"));
    // Same clock-independent shape as the 155-byte folder shell: 140 folded
    // (the stamp is 18 characters before 10:00 local; see `log-hour-pad-probe`).
    assert_eq!(reports[0].len(), 140);
}

#[test]
fn text_report_without_files_writes_the_122_byte_shell() {
    // u5f `no-load-xml`: BOM, 122 bytes, `<ltpath/>` + `<rtpath/>` directly
    // under `<bcreport>` with no `<foldercomp>` and no comparison element.
    let s = Scratch::new("text-shell-empty");
    let out = s.str("shell.out");
    let (code, reports) = run(vec![text_report("xml", &out, &[], 1)], &[]);
    assert_eq!(code, 0);
    assert_eq!(
        reports[0],
        "\u{feff}<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n\
         <bcreport created=\"TIME\">\r\n\
         \t<ltpath/>\r\n\
         \t<rtpath/>\r\n\
         </bcreport>\r\n"
    );
    // Clock-independent: 122 raw bytes assume a 19-character stamp; BC does
    // not pad the hour (18 characters before 10:00 -- `log-hour-pad-probe`),
    // so fold to 122 - 19 + 4 = 107.
    assert_eq!(reports[0].len(), 107);
}

#[test]
fn text_report_after_load_folders_writes_the_272_byte_shell() {
    // u5f `load-folders-xml` / u5c `load-folders-then-text-report`: the same
    // shell but carrying the loaded folder paths. u5f's own report is 272 bytes
    // with two 67-character paths and a 19-character stamp; the invariant that
    // survives a different temp path is the shape plus the exact contribution
    // of each path and the stamp.
    let s = Scratch::new("text-shell-folders");
    let l = s.dir("L");
    let r = s.dir("R");
    let out = s.str("shell.out");
    let (code, reports) = run(
        vec![load(&l, &r, 1), expand_all(2), text_report("xml", &out, &[], 3)],
        &[],
    );
    assert_eq!(code, 0);
    assert!(reports[0].contains(&format!("\t<ltpath>{l}</ltpath>\r\n")));
    assert!(reports[0].contains(&format!("\t<rtpath>{r}</rtpath>\r\n")));
    assert!(!reports[0].contains("<foldercomp>"));
    // The byte arithmetic, which u5f's own numbers confirm: the 122-byte shell
    // with a 19-character stamp holds `<ltpath/>` (9 bytes) where this report
    // holds `<ltpath>PATH</ltpath>` (17 + len), so each side adds 8 + its path
    // length. u5f's 272-byte `load-folders-xml` is exactly
    // 122 + 8 + 67 + 8 + 67 with its two 67-character paths. The folded form
    // (stamp -> `TIME`) is clock-independent: 107 + 8 + len + 8 + len.
    assert_eq!(reports[0].len(), 107 + 8 + l.len() + 8 + r.len());
}

#[test]
fn text_report_with_two_files_has_no_bom() {
    // u5f `args-xml.out` is 573 bytes and starts with `<?xml` — no BOM, unlike
    // the two path-only shells.
    let s = Scratch::new("bom-args");
    let l = s.file("L.txt", b"alpha\nbeta\n");
    let r = s.file("R.txt", b"alpha\nGAMMA\n");
    let out = s.str("args.xml");
    let (code, reports) = run(vec![text_report("xml", &out, &[&l, &r], 1)], &[]);
    assert_eq!(code, 0);
    assert!(reports[0].starts_with("<?xml version=\"1.0\" encoding=\"utf-8\"?>"));
    assert!(!reports[0].starts_with('\u{feff}'));
    assert!(reports[0].contains("<filecomparison created=\"TIME\">"));
    assert!(reports[0].contains("\t\t<linecomp status=\"same\">"));
    assert!(reports[0].contains("\t\t<linecomp status=\"different\">"));
    assert!(reports[0].contains("<filename1>"));
    assert_eq!(s.bytes("args.xml")[0], b'<');
}

#[test]
fn a_missing_text_report_input_is_107() {
    // u5 `text-report-missing-files`: 107, and no report file at all.
    let s = Scratch::new("missing-text-input");
    let out = s.str("nope.xml");
    let missing = s.str("absent-L.txt");
    let present = s.file("R.txt", b"x\n");
    let (code, reports) = run(
        vec![text_report("xml", &out, &[&missing, &present], 1)],
        &[],
    );
    assert_eq!(code, 107);
    assert!(reports.is_empty());
    assert!(!Path::new(&out).exists(), "no placeholder report may be written");
}

#[test]
fn a_missing_load_path_is_107_and_stops_the_script() {
    // u5 `load-missing-folder`: 107, and the later report never runs.
    let s = Scratch::new("load-missing");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![
            load(&s.str("nope-L"), &s.str("nope-R"), 1),
            expand_all(2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 107);
    assert!(reports.is_empty());
    assert!(!Path::new(&out).exists());
}

#[test]
fn load_of_a_file_is_107() {
    // u5c `load-files-then-folder-report`: `load` takes folders, so a file is a
    // load failure even though the path exists.
    let s = Scratch::new("load-file");
    let f = s.file("a.txt", b"x\n");
    let other = s.dir("R");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![load(&f, &other, 1), folder_report("xml", &out, 2)],
        &[],
    );
    assert_eq!(code, 107);
    assert!(reports.is_empty());
}

#[test]
fn load_with_only_the_left_side_represents_the_right_as_empty() {
    // u5e `load-left-only`: exit 0, `<rtpath/>`, every row `ltonly`.
    let s = Scratch::new("left-only");
    u5g_tree(&s);
    let l = s.dir("L");
    let out = s.str("left.xml");
    let (code, reports) = run(
        vec![
            Command::Load {
                left: l.clone(),
                right: None,
                line: 1,
            },
            expand_all(2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(reports[0].contains(&format!("\t\t<ltpath>{l}</ltpath>")));
    assert!(reports[0].contains("\t\t<rtpath/>"));
    assert!(reports[0].contains("<filecomp status=\"ltonly\">"));
    // u5e `load-left-only`: A, then its child B, then g.txt, then C, i.txt,
    // then h.txt — directories before files at each level, depth first.
    assert_eq!(
        names(&reports[0]),
        ["A", "B", "f.txt", "g.txt", "C", "i.txt", "h.txt"]
    );
}

// ==========================================================================
// expand -> <size>
// ==========================================================================

#[test]
fn no_expand_renders_size_slash_and_no_child_rows() {
    // u5g s1: `A=<size/>`, `C=<size/>`, and no rows below either.
    let s = Scratch::new("no-expand");
    u5g_tree(&s);
    let out = s.str("s1.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("xml", &out, 2),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A"), None);
    assert_eq!(size_of(&reports[0], "C"), None);
    assert_eq!(names(&reports[0]), ["A", "C", "h.txt"]);
}

#[test]
fn expand_all_aggregates_every_directory() {
    // u5g s2: `A=10`, `B=6`, `C=3` and every file row present.
    let s = Scratch::new("expand-all");
    u5g_tree(&s);
    let out = s.str("s2.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A").as_deref(), Some("10"));
    assert_eq!(size_of(&reports[0], "B").as_deref(), Some("6"));
    assert_eq!(size_of(&reports[0], "C").as_deref(), Some("3"));
    assert_eq!(names(&reports[0]), ["A", "B", "f.txt", "g.txt", "C", "i.txt", "h.txt"]);
}

#[test]
fn expand_of_a_parent_keeps_the_parent_size_slash() {
    // u5g s3: `expand "A"` shows `A`'s children but `A` STILL has `<size/>`
    // because `B` below it is not expanded.
    let s = Scratch::new("expand-A");
    u5g_tree(&s);
    let l = s.dir("L");
    let r = s.dir("R");
    let out = s.str("s3.xml");
    let (code, reports) = run(
        vec![
            load(&l, &r, 1),
            expand_named(&["A"], 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A"), None, "A's subtree is not fully expanded");
    assert_eq!(size_of(&reports[0], "B"), None, "B is collapsed");
    assert_eq!(size_of(&reports[0], "C"), None);
    assert_eq!(names(&reports[0]), ["A", "B", "g.txt", "C", "h.txt"]);
}

#[test]
fn expand_of_a_nested_path_aggregates_its_ancestor() {
    // u5g s4: `expand "A\B"` -> `A=10` (whole subtree expanded) and `B=6`.
    let s = Scratch::new("expand-A-B");
    u5g_tree(&s);
    let out = s.str("s4.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_named(&["A\\B"], 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A").as_deref(), Some("10"));
    assert_eq!(size_of(&reports[0], "B").as_deref(), Some("6"));
    assert_eq!(size_of(&reports[0], "C"), None);
    assert_eq!(names(&reports[0]), ["A", "B", "f.txt", "g.txt", "C", "h.txt"]);
}

#[test]
fn expand_commands_accumulate() {
    // u5g s6: `expand "A"` then `expand "C"` -> `C=3` while `A` stays `<size/>`.
    let s = Scratch::new("expand-cumulative");
    u5g_tree(&s);
    let out = s.str("s6.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_named(&["A"], 2),
            expand_named(&["C"], 3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A"), None);
    assert_eq!(size_of(&reports[0], "C").as_deref(), Some("3"));
    assert_eq!(names(&reports[0]), ["A", "B", "g.txt", "C", "i.txt", "h.txt"]);
}

#[test]
fn a_path_spelling_does_not_change_the_target_folder() {
    // u5h `expand-forward-slash` (`A/B`) and `expand-trailing-sep` (`A\`) name
    // the same folder as `A\B` / `A`.
    let s = Scratch::new("expand-spelling");
    u5g_tree(&s);
    let l = s.dir("L");
    let r = s.dir("R");

    let mut bodies = Vec::new();
    for (spelling, out_name) in [("A/B", "slash.xml"), ("A\\B", "back.xml")] {
        let out = s.str(out_name);
        let (code, reports) = run(
            vec![
                load(&l, &r, 1),
                expand_named(&[spelling], 2),
                folder_report("xml", &out, 3),
            ],
            &[],
        );
        assert_eq!(code, 0, "{spelling}");
        bodies.push(reports[0].clone());
    }
    assert_eq!(bodies[0], bodies[1], "`A/B` and `A\\B` must render identically");

    // ...and `A\` (trailing separator) expands `A`, not `A\B` — u5h
    // `expand-trailing-sep` has `A=<size/>`, `B=<size/>`, `g.txt` visible.
    let out = s.str("trailing.xml");
    let (code, reports) = run(
        vec![
            load(&l, &r, 1),
            expand_named(&["A\\"], 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A"), None);
    assert_eq!(names(&reports[0]), ["A", "B", "g.txt", "C", "h.txt"]);
}

#[test]
fn expand_of_a_missing_path_is_106() {
    // u5e `expand-missing`: 106 with no report.
    let s = Scratch::new("expand-missing");
    u5g_tree(&s);
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_named(&["nope"], 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());
    assert!(!Path::new(&out).exists());
}

#[test]
fn expand_of_a_file_path_is_harmless() {
    // u5h `expand-a-file`: `expand "h.txt"` exits 0, changes nothing, and `A`
    // keeps `<size/>`.
    let s = Scratch::new("expand-file");
    u5g_tree(&s);
    let out = s.str("file.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_named(&["h.txt"], 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(names(&reports[0]), ["A", "C", "h.txt"]);
    assert_eq!(size_of(&reports[0], "A"), None);
}

#[test]
fn one_sided_directories_aggregate_like_paired_ones() {
    // u5j `B-expandall`: `onlyL` (no right counterpart) renders `<size>2</size>`
    // and its `x.txt` row.
    let s = Scratch::new("one-sided");
    s.file("L/onlyL/x.txt", b"xx");
    s.dir("R");
    let out = s.str("b.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "onlyL").as_deref(), Some("2"));
    assert_eq!(names(&reports[0]), ["onlyL", "x.txt"]);
    assert!(reports[0].contains("<filecomp status=\"ltonly\">"));
}

#[test]
fn a_directory_row_never_carries_a_status_attribute() {
    // u5j: 18 reports, every `d`/`onlyL`/`thing` row is a plain `<foldercomp>`,
    // expanded or not, even where the content differs.
    let s = Scratch::new("no-dir-status");
    s.file("L/d/in.txt", b"11111");
    s.file("R/d/in.txt", b"111111111");
    for (tag, cmds) in [
        ("noexpand", Vec::new()),
        ("expandall", vec![expand_all(2)]),
        ("expand-d", vec![expand_named(&["d"], 2)]),
    ] {
        let out = s.str(&format!("{tag}.xml"));
        let mut script = vec![load(&s.dir("L"), &s.dir("R"), 1)];
        script.extend(cmds);
        script.push(folder_report("xml", &out, 9));
        let (code, reports) = run(script, &[]);
        assert_eq!(code, 0, "{tag}");
        assert!(!reports[0].contains("<foldercomp status"), "{tag}");
        // The file row inside does carry the diff.
        if tag != "noexpand" {
            assert!(reports[0].contains("<filecomp status=\"diff\">"), "{tag}");
        }
    }
}

#[test]
fn per_side_aggregates_differ_when_the_sides_differ() {
    // u5j `A-expandall`: `d` is `<size>5</size>` on the left and `9` on the
    // right, because the aggregate is per side.
    let s = Scratch::new("per-side-size");
    s.file("L/d/in.txt", b"11111");
    s.file("R/d/in.txt", b"111111111");
    let out = s.str("per-side.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let report = &reports[0];
    let left_block = report.split("<name>d</name>").nth(1).unwrap();
    let left_block = left_block.split("</lt>").next().unwrap();
    assert!(left_block.contains("<size>5</size>"), "{left_block}");
    let right_block = report.rsplit("<name>d</name>").next().unwrap();
    let right_block = right_block.split("</rt>").next().unwrap();
    assert!(right_block.contains("<size>9</size>"), "{right_block}");
}

// ==========================================================================
// filter
// ==========================================================================

#[test]
fn a_filter_changes_the_row_set_and_writes_the_element() {
    // u5c `filter-include-txt` on the u5d tree: only `*.txt` file rows survive;
    // both folder rows stay with their unfiltered aggregates; `<filters>` is
    // present after `<rtpath>`.
    let s = Scratch::new("filter-include");
    for side in ["L", "R"] {
        s.file(&format!("{side}/a.txt"), b"aaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbbb");
        s.file(&format!("{side}/c.TXT"), b"cccccccc");
        s.file(&format!("{side}/d1.bin"), b"dd");
        s.file(&format!("{side}/other/g.log"), b"gggg");
        s.file(&format!("{side}/sub/e.txt"), b"eeee");
        s.file(&format!("{side}/sub/deep/f.txt"), b"ffff");
    }
    let out = s.str("filter.xml");
    let (code, reports) = run(
        vec![
            filter("*.txt", 1),
            load(&s.dir("L"), &s.dir("R"), 2),
            expand_all(3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(filters_text(&reports[0]).as_deref(), Some("*.txt"));
    // Measured document order (u5d `filter-upper-txt` is the same tree under a
    // file mask): `other`, `sub`, `sub/deep` + `f.txt`, `e.txt`, then the
    // top-level files.
    assert_eq!(
        names(&reports[0]),
        ["other", "sub", "deep", "f.txt", "e.txt", "a.txt", "c.TXT"]
    );
    // `sub` aggregates ALL its files (4 + 4 = 8) even though `*.txt` keeps both
    // here; the point is that the folder row is untouched by the file mask.
    assert_eq!(size_of(&reports[0], "sub").as_deref(), Some("8"));
}

#[test]
fn a_filter_that_matches_nothing_keeps_every_folder_row() {
    // u5c `filter-match-nothing` and u5g s7: no file row at all, folder rows
    // kept WITH their aggregates.
    let s = Scratch::new("filter-nomatch");
    u5g_tree(&s);
    let out = s.str("nomatch.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            filter("*.nomatch", 3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(size_of(&reports[0], "A").as_deref(), Some("10"));
    assert_eq!(size_of(&reports[0], "B").as_deref(), Some("6"));
    assert_eq!(size_of(&reports[0], "C").as_deref(), Some("3"));
    assert_eq!(names(&reports[0]), ["A", "B", "C"]);
    assert!(!reports[0].contains("<filecomp"));
}

#[test]
fn a_folder_exclude_mask_removes_the_whole_subtree() {
    // u5h `fg-exclude-A-*`: `filter "-A\\"` removes `A` and everything under it,
    // identically with and without `expand all`. The surviving `C` row is
    // expanded, so its `i.txt` is present in the expand-all form.
    let s = Scratch::new("filter-exclude-folder");
    u5g_tree(&s);
    let l = s.dir("L");
    let r = s.dir("R");
    let mut expanded_bodies = Vec::new();
    for (tag, with_expand) in [("noexp", false), ("expandall", true)] {
        let out = s.str(&format!("{tag}.xml"));
        let mut script = vec![load(&l, &r, 1), filter("-A\\\\", 2)];
        if with_expand {
            script.push(expand_all(3));
        }
        script.push(folder_report("xml", &out, 9));
        let (code, reports) = run(script, &[]);
        assert_eq!(code, 0, "{tag}");
        assert!(
            !reports[0].contains("<name>A</name>"),
            "{tag}: the excluded folder and its subtree must be gone"
        );
        assert_eq!(filters_text(&reports[0]).as_deref(), Some("-A\\\\"), "{tag}");
        if with_expand {
            assert_eq!(names(&reports[0]), ["C", "i.txt", "h.txt"], "{tag}");
            expanded_bodies.push(reports[0].clone());
        } else {
            // u5h `fg-exclude-A-noexp`: no `expand`, so only the top level shows
            // and `C` carries `<size/>`.
            assert_eq!(names(&reports[0]), ["C", "h.txt"], "{tag}");
            assert_eq!(size_of(&reports[0], "C"), None, "{tag}");
        }
    }
    // The expand-all form's remaining rows are the same ones u5h archived.
    assert_eq!(expanded_bodies.len(), 1);
}

#[test]
fn the_last_filter_command_wins() {
    // u5i `xml-filter-twice`: `filter "*.txt"` then `filter "*.log"` leaves only
    // `b.log` and echoes the SECOND mask.
    let s = Scratch::new("filter-twice");
    for side in ["L", "R"] {
        s.file(&format!("{side}/a.txt"), b"aaaaaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbb");
    }
    let out = s.str("twice.xml");
    let (code, reports) = run(
        vec![
            filter("*.txt", 1),
            filter("*.log", 2),
            load(&s.dir("L"), &s.dir("R"), 3),
            expand_all(4),
            folder_report("xml", &out, 5),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(filters_text(&reports[0]).as_deref(), Some("*.log"));
    assert_eq!(names(&reports[0]), ["b.log"]);
}

#[test]
fn a_folder_include_mask_restricts_folders_but_not_files() {
    // u5d `filter-folder-mask` / `filter-folder-only`: `filter "sub\\"` keeps
    // the folder `sub` (and its nested `deep`), removes every OTHER folder row,
    // and keeps every file row — including the ones outside `sub`, because a
    // folder mask says nothing about files. `<filters>` echoes the raw text.
    //
    // The u5d tree is used verbatim so the assertion is against that report:
    // folders `other` + `sub`/`deep`, files `a.txt`, `b.log`, `c.TXT`,
    // `d1.bin`, `sub/e.txt`, `sub/deep/f.txt`, `other/g.log`.
    let s = Scratch::new("filter-folder-mask");
    for side in ["L", "R"] {
        s.file(&format!("{side}/a.txt"), b"aaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbbb");
        s.file(&format!("{side}/c.TXT"), b"cccccccc");
        s.file(&format!("{side}/d1.bin"), b"dd");
        s.file(&format!("{side}/other/g.log"), b"gggg");
        s.file(&format!("{side}/sub/e.txt"), b"eeee");
        s.file(&format!("{side}/sub/deep/f.txt"), b"ffff");
    }
    let out = s.str("folder-mask.xml");
    let (code, reports) = run(
        vec![
            filter("sub\\\\", 1),
            load(&s.dir("L"), &s.dir("R"), 2),
            expand_all(3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(filters_text(&reports[0]).as_deref(), Some("sub\\\\"));
    // `other` is removed; `sub` and its nested `deep` stay; so do every file row
    // OUTSIDE the removed folder. This is the exact u5d `filter-folder-only` row
    // set (folders `sub`,`deep`; files `f.txt`,`e.txt`,`a.txt`,`b.log`,`c.TXT`,
    // `d1.bin`). `other/g.log` is absent only because its folder is gone — the
    // masks never touch a file's own visibility.
    assert!(
        !reports[0].contains("<name>other</name>"),
        "the non-matching folder must go: {}",
        reports[0]
    );
    assert!(reports[0].contains("<name>sub</name>"));
    assert!(reports[0].contains("<name>deep</name>"));
    assert_eq!(
        names(&reports[0]),
        ["sub", "deep", "f.txt", "e.txt", "a.txt", "b.log", "c.TXT", "d1.bin"]
    );
}

#[test]
fn filters_comes_after_ignoreunimportant() {
    // u5i `xml-filter-and-iu`: the measured order is `<ltpath>`, `<rtpath>`,
    // `<ignoreunimportant/>`, `<filters>`, rows.
    let s = Scratch::new("order");
    s.file("L/a.txt", b"aaaaaaaaaaa");
    s.file("R/a.txt", b"bbbbbbbbbbb");
    let out = s.str("order.xml");
    let (code, reports) = run(
        vec![
            filter("*.txt", 1),
            criteria("rules-based ignore-unimportant", 2),
            load(&s.dir("L"), &s.dir("R"), 3),
            expand_all(4),
            folder_report("xml", &out, 5),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let report = &reports[0];
    let lt = report.find("<ltpath>").expect("ltpath");
    let rt = report.find("<rtpath>").expect("rtpath");
    let iu = report.find("<ignoreunimportant/>").expect("ignoreunimportant");
    let fi = report.find("<filters>").expect("filters");
    assert!(lt < rt && rt < iu && iu < fi, "measured element order violated");
}

#[test]
fn a_report_after_a_late_criteria_uses_the_new_criteria() {
    // u5e `crit-after-report`: the FIRST report uses the default criteria (all
    // `same`), and a `criteria CRC` issued afterwards changes only the SECOND
    // report (`diff`, because the two files have equal size and timestamp).
    let s = Scratch::new("criteria-order");
    s.file("L/a.txt", b"aaaaaaaa");
    s.file("R/a.txt", b"bbbbbbbb");
    let first = s.str("first.xml");
    let second = s.str("second.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("xml", &first, 3),
            criteria("CRC", 4),
            folder_report("xml", &second, 5),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(reports.len(), 2);
    assert!(reports[0].contains("<filecomp status=\"same\">"), "{}", reports[0]);
    assert!(reports[1].contains("<filecomp status=\"diff\">"), "{}", reports[1]);
}

#[test]
fn a_bad_criteria_token_is_106() {
    // u5c `criteria-bogus`.
    let s = Scratch::new("criteria-bogus");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![
            criteria("bogus-token", 1),
            load(&s.dir("L"), &s.dir("R"), 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn an_invalid_option_value_is_106() {
    // u5e `option-bogus`.
    let s = Scratch::new("option-bogus");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![option("frobnicate", 1), folder_report("xml", &out, 2)],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn the_three_observed_options_are_accepted_and_change_nothing() {
    // u5e `option-stop-on-error`, `option-confirm-yes`, `option-confirm-no`: all
    // exit 0 with an identical report.
    let s = Scratch::new("options-ok");
    u5g_tree(&s);
    let l = s.dir("L");
    let r = s.dir("R");
    let mut bodies = Vec::new();
    for (i, name) in ["stop-on-error", "confirm:yes-to-all", "confirm:no-to-all"]
        .iter()
        .enumerate()
    {
        let out = s.str(&format!("opt{i}.xml"));
        let (code, reports) = run(
            vec![
                option(name, 1),
                load(&l, &r, 2),
                expand_all(3),
                folder_report("xml", &out, 4),
            ],
            &[],
        );
        assert_eq!(code, 0, "{name}");
        bodies.push(reports[0].clone());
    }
    assert_eq!(bodies[0], bodies[1]);
    assert_eq!(bodies[1], bodies[2]);
}

#[test]
fn an_unsupported_layout_name_is_106() {
    // u5 `bad-option-value`, and the A-3 gate's four folder-layout rejections.
    let s = Scratch::new("bad-layout");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("not-a-layout", &out, 2),
        ],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());

    // `layout:html` is a real BC *text* layout name in no set; and for a FOLDER
    // report the gate measured BC exiting 106 on it, which is the same code.
    let out2 = s.str("never2.xml");
    let (code2, _) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("html", &out2, 2),
        ],
        &[],
    );
    assert_eq!(code2, 106);

    // A text report accepts seven names, `interleaved` among them, while a
    // folder report does not — the two vocabularies are genuinely different.
    let out3 = s.str("third.xml");
    let (code3, reports3) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("interleaved", &out3, 2),
        ],
        &[],
    );
    assert_eq!(code3, 106);
    assert!(reports3.is_empty());
}

#[test]
fn printer_and_clipboard_outputs_are_refused_by_name() {
    // 09 §5: `output-to:printer|clipboard` is not implemented and must be
    // refused by name with no report, never silently redirected to a file.
    let s = Scratch::new("printer");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("xml", "printer", 2),
        ],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());

    let (code2, reports2) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            folder_report("xml", "clipboard", 2),
        ],
        &[],
    );
    assert_eq!(code2, 106);
    assert!(reports2.is_empty());
}

#[test]
fn a_report_without_output_to_is_106() {
    // u5 `missing-required-arg`: `text-report layout:xml` (no `output-to:`) is
    // 106 with no report.
    let s = Scratch::new("no-output-to");
    let (code, reports) = run(
        vec![Command::TextReport {
            spec: ReportSpec {
                layout: "xml".to_string(),
                ..ReportSpec::default()
            },
            line: 1,
        }],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());

    let out = s.str("never.xml");
    let (code2, reports2) = run(
        vec![Command::FolderReport {
            spec: ReportSpec {
                layout: "xml".to_string(),
                ..ReportSpec::default()
            },
            line: 1,
        }],
        &[],
    );
    assert_eq!(code2, 106);
    assert!(reports2.is_empty());
    assert!(!Path::new(&out).exists());
}

// ==========================================================================
// %1/%2/%3 substitution
// ==========================================================================

#[test]
fn parameters_substitute_in_paths_and_masks() {
    // u5: every recipe passes its inputs as `"%1" "%2"` and its output as
    // `"%3"`, so substitution has to reach load paths, expansion paths, filter
    // masks AND the report destination.
    let s = Scratch::new("substitution");
    u5g_tree(&s);
    let l = s.dir("L");
    let r = s.dir("R");
    let out = s.str("sub.xml");
    let (code, reports) = run(
        vec![
            Command::Load {
                left: "%1".to_string(),
                right: Some("%2".to_string()),
                line: 1,
            },
            expand_all(2),
            filter("*.txt", 3),
            Command::FolderReport {
                spec: ReportSpec {
                    layout: "xml".to_string(),
                    output_to: Some("%3".to_string()),
                    ..ReportSpec::default()
                },
                line: 4,
            },
        ],
        &[&l, &r, &out],
    );
    assert_eq!(code, 0);
    assert_eq!(reports.len(), 1);
    assert!(reports[0].contains(&format!("\t\t<ltpath>{l}</ltpath>")));
    assert!(Path::new(&out).exists());
}

#[test]
fn a_parameter_the_command_line_omitted_is_left_verbatim() {
    // No probe covers this, so the choice is documented: leaving `%2` in place
    // says "you forgot argument 2" instead of turning the path into an empty
    // string, which would fail as "not a folder" and hide the real problem.
    let s = Scratch::new("missing-param");
    let l = s.dir("L");
    let (code, reports) = run(
        vec![Command::Load {
            left: "%1".to_string(),
            right: Some("%2".to_string()),
            line: 1,
        }],
        &[&l],
    );
    assert_eq!(code, 107);
    assert!(reports.is_empty());
}

// ==========================================================================
// log
// ==========================================================================

#[test]
fn a_log_echoes_every_command_and_names_its_destination() {
    // u5c `log-explicit`: the log carries one timestamped line per command in
    // order, plus a completion line. Its wording is this build's own (see
    // `exec::LogSink`); the STRUCTURE is the measured one.
    let s = Scratch::new("log");
    u5g_tree(&s);
    let log = s.str("script.log");
    let out = s.str("log-report.xml");
    let (code, _) = run(
        vec![
            Command::Log {
                mode: LogMode::Verbose,
                path: Some(log.clone()),
                append: false,
                line: 1,
            },
            load(&s.dir("L"), &s.dir("R"), 2),
            expand_all(3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let body = fs::read_to_string(&log).expect("log file");
    assert!(!body.starts_with('\u{feff}'), "the Oracle writes no BOM in its log");
    let lines: Vec<&str> = body.trim_end_matches("\r\n").split("\r\n").collect();
    assert!(lines[0].contains(">> log verbose"), "{:?}", lines);
    assert!(lines.iter().any(|l| l.contains(">> load ")), "{:?}", lines);
    assert!(lines.iter().any(|l| l.contains(">> expand all")), "{:?}", lines);
    assert!(lines.iter().any(|l| l.contains(">> folder-report layout:xml")), "{:?}", lines);
    assert!(lines.last().unwrap().contains("Script completed"), "{:?}", lines);
    // Every line is timestamped in the observed shape: `YYYY/M/D H:MM:SS`
    // with unpadded month, day and hour -- BC's own log measured at 01:52 on
    // 2026-10-16 (`runs/log-hour-pad-probe/reports/bc.log`) renders the hour
    // as one digit, so the assertion must not pin fixed byte positions.
    fn timestamped(l: &str) -> bool {
        let (date, rest) = l.split_once(' ').unwrap_or_default();
        let time = rest.split(' ').next().unwrap_or_default();
        let parts: Vec<&str> = date.split('/').collect();
        parts.len() == 3
            && parts[0].len() == 4
            && parts[0].bytes().all(|b| b.is_ascii_digit())
            && parts[1].bytes().all(|b| b.is_ascii_digit())
            && parts[2].bytes().all(|b| b.is_ascii_digit())
            && time.bytes().next().is_some_and(|b| b.is_ascii_digit())
            && time.matches(':').count() == 2
    }
    for l in &lines {
        assert!(timestamped(l), "not a timestamped line: {l:?}");
    }
}

#[test]
fn log_append_extends_an_existing_file() {
    let s = Scratch::new("log-append");
    let log = s.str("append.log");
    fs::write(&log, "PRE-EXISTING\r\n").unwrap();
    let out = s.str("append-report.xml");
    let (code, _) = run(
        vec![
            Command::Log {
                mode: LogMode::Normal,
                path: Some(log.clone()),
                append: true,
                line: 1,
            },
            load(&s.dir("L"), &s.dir("R"), 2),
            folder_report("xml", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let body = fs::read_to_string(&log).unwrap();
    assert!(body.starts_with("PRE-EXISTING\r\n"), "{body}");
}

#[test]
fn log_none_turns_logging_back_off() {
    let s = Scratch::new("log-none");
    let log = s.str("none.log");
    let out = s.str("none-report.xml");
    let (code, _) = run(
        vec![
            Command::Log {
                mode: LogMode::Normal,
                path: Some(log.clone()),
                append: false,
                line: 1,
            },
            Command::Log {
                mode: LogMode::None,
                path: None,
                append: false,
                line: 2,
            },
            load(&s.dir("L"), &s.dir("R"), 3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(
        !Path::new(&log).exists(),
        "`log none` must not create a log file"
    );
}

// ==========================================================================
// The text layouts and their filter line
// ==========================================================================

#[test]
fn the_text_layout_filter_line_is_the_measured_bytes() {
    // u5i `summary-filter.out` line 4 is exactly `过滤：  *.txt`: the two CJK
    // characters, a FULLWIDTH colon (U+FF1A), two ASCII spaces, then the raw
    // mask. The harness normalizer does not translate this line, so a byte
    // difference here fails the comparison — and a byte difference is what this
    // asserts.
    let s = Scratch::new("filter-line");
    for side in ["L", "R"] {
        s.file(&format!("{side}/a.txt"), b"aaaaaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbb");
    }
    let out = s.str("summary.out");
    let (code, reports) = run(
        vec![
            filter("*.txt", 1),
            load(&s.dir("L"), &s.dir("R"), 2),
            expand_all(3),
            folder_report("summary", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let expected = "\u{8fc7}\u{6ee4}\u{ff1a}  *.txt";
    assert!(
        reports[0].contains(expected),
        "expected {expected:?} in {:?}",
        reports[0]
    );
    // And the exact bytes on disk, not just the escape: U+8FC7 U+6EE4 U+FF1A,
    // then two spaces.
    let raw = s.bytes("summary.out");
    let needle: Vec<u8> = vec![0xE8, 0xBF, 0x87, 0xE6, 0xBB, 0xA4, 0xEF, 0xBC, 0x9A, b' ', b' ', b'*'];
    assert!(
        raw.windows(needle.len()).any(|w| w == needle.as_slice()),
        "raw bytes do not carry the measured filter line"
    );
}

#[test]
fn a_text_layout_without_a_filter_has_no_filter_line() {
    let s = Scratch::new("no-filter-line");
    u5g_tree(&s);
    let out = s.str("summary.out");
    let (code, reports) = run(
        vec![
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("summary", &out, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(!reports[0].contains("\u{8fc7}\u{6ee4}"));
}

// ==========================================================================
// Whole-script shapes
// ==========================================================================

#[test]
fn a_full_script_runs_end_to_end_and_writes_every_report() {
    // The u5g/u5c recipe shape: filter, load, expand, criteria, two reports.
    let s = Scratch::new("end-to-end");
    for side in ["L", "R"] {
        s.file(&format!("{side}/sub/a.txt"), b"aaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbb");
    }
    let xml = s.str("report.xml");
    let summary = s.str("report.txt");
    let log = s.str("run.log");
    let (code, reports) = run(
        vec![
            filter("*.txt;*.log", 1),
            Command::Log {
                mode: LogMode::Normal,
                path: Some(log.clone()),
                append: false,
                line: 2,
            },
            load(&s.dir("L"), &s.dir("R"), 3),
            expand_all(4),
            criteria("size timestamp", 5),
            folder_report("xml", &xml, 6),
            folder_report("summary", &summary, 7),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(reports.len(), 2);
    assert_eq!(filters_text(&reports[0]).as_deref(), Some("*.txt;*.log"));
    assert!(reports[1].contains("Folder Compare Summary"));
    assert!(Path::new(&log).exists());
}

#[test]
fn the_diagnostics_name_the_failing_line() {
    // A script error must point at the script the user wrote, not at a report.
    let s = Scratch::new("diagnostics");
    let argv: Vec<String> = Vec::new();
    let outcome = run_script(
        &[criteria("bogus", 7), folder_report("xml", &s.str("x.xml"), 8)],
        &argv,
    );
    assert_eq!(outcome.exit_code, 106);
    assert_eq!(outcome.diagnostics.len(), 1);
    assert!(outcome.diagnostics[0].starts_with("line 7:"), "{:?}", outcome.diagnostics);
}

#[test]
fn the_reports_list_is_in_write_order() {
    let s = Scratch::new("report-order");
    u5g_tree(&s);
    let first = s.str("one.xml");
    let second = s.str("two.xml");
    let argv: Vec<String> = Vec::new();
    let outcome = run_script(
        &[
            load(&s.dir("L"), &s.dir("R"), 1),
            expand_all(2),
            folder_report("xml", &first, 3),
            folder_report("xml", &second, 4),
        ],
        &argv,
    );
    assert_eq!(outcome.exit_code, 0);
    assert_eq!(outcome.reports.len(), 2);
    assert!(outcome.reports[0].ends_with("one.xml"));
    assert!(outcome.reports[1].ends_with("two.xml"));
}

// ==========================================================================
// Module inclusion
//
// `reacmp-cli` is a binary crate: its `main.rs` is the crate root, so an
// integration test cannot `use reacmp_cli::...`.  The script module tree is
// therefore included by path, at this crate's root, so the SAME sources the
// binary ships are compiled here — a change in `exec.rs` that breaks this test
// breaks the binary too.
//
// `ast.rs`, `lex.rs` and `parse.rs` come along because `exec.rs` consumes them
// (`use super::ast::…` resolves to these root modules).  `args.rs` and
// `main.rs` are NOT included: the executor does not touch them, and task C owns
// both.
// ==========================================================================

#[allow(dead_code)]
#[path = "../src/script/ast.rs"]
mod ast;
#[allow(dead_code)]
#[path = "../src/script/lex.rs"]
mod lex;
#[allow(dead_code)]
#[path = "../src/script/parse.rs"]
mod parse;
#[allow(dead_code)]
#[path = "../src/script/exec.rs"]
mod exec;

// ==========================================================================
// 09 §5: features this build refuses BY NAME, never silently
// ==========================================================================

#[test]
fn load_create_prefix_is_refused_and_creates_nothing() {
    // u5g `s11-create-all` measured the Oracle CREATING the missing folders.
    // This build is read-only, so the form is refused by name with 106 — and,
    // critically, it must leave no directory behind.
    let s = Scratch::new("load-create");
    let missing_l = s.str("new-L");
    let missing_r = s.str("new-R");
    let out = s.str("never.xml");
    let (code, reports) = run(
        vec![
            Command::Load {
                left: format!("create:all {missing_l}"),
                right: Some(missing_r.clone()),
                line: 1,
            },
            folder_report("xml", &out, 2),
        ],
        &[],
    );
    assert_eq!(code, 106);
    assert!(reports.is_empty());
    assert!(!Path::new(&missing_l).exists(), "the refused form must not create a directory");
    assert!(!Path::new(&missing_r).exists());
}

#[test]
fn the_documented_filter_forms_this_build_does_not_implement_are_refused() {
    // 09 §5 names the non-name filter forms as out of scope. Each is refused
    // with 106 rather than accepted-and-ignored, so a script asking for a size
    // filter can never silently receive an unfiltered report.
    let s = Scratch::new("filter-forms");
    for (i, form) in [
        "cutoff:<12/31/2020",
        "size:>1MB",
        "attrib:+h",
        "unixtype:+d",
        "exclude-protected",
        "include-protected",
        "-size:>1MB",
        "*.txt;size:>1MB",
    ]
    .iter()
    .enumerate()
    {
        let out = s.str(&format!("never{i}.xml"));
        let (code, reports) = run(
            vec![
                filter(form, 1),
                load(&s.dir("L"), &s.dir("R"), 2),
                folder_report("xml", &out, 3),
            ],
            &[],
        );
        assert_eq!(code, 106, "{form} must be refused");
        assert!(reports.is_empty(), "{form} must write no report");
        assert!(!Path::new(&out).exists(), "{form} left a report behind");
    }
}

#[test]
fn a_name_mask_that_merely_resembles_a_keyword_is_still_a_name_mask() {
    // The refusal keys on the documented keyword vocabulary, not on "contains a
    // colon": a file may legitimately be called `size` or `a:size`.
    let s = Scratch::new("filter-lookalike");
    u5g_tree(&s);
    let out = s.str("lookalike.xml");
    let (code, reports) = run(
        vec![
            filter("size", 1),
            load(&s.dir("L"), &s.dir("R"), 2),
            expand_all(3),
            folder_report("xml", &out, 4),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(filters_text(&reports[0]).as_deref(), Some("size"));
}

// ==========================================================================
// M8: sync (docs/15; every expectation below is a measured cell)
// ==========================================================================

fn sync(
    visible: bool,
    create_empty: bool,
    mode: ast::SyncMode,
    direction: ast::SyncDirection,
    line: usize,
) -> Command {
    Command::Sync { visible, create_empty, mode, direction, line }
}

/// The set of relative paths under `dir`, sorted — the observable effect of a
/// sync is the resulting file tree, so this is what every sync test asserts.
fn tree_of(dir: &str) -> Vec<String> {
    let mut out = Vec::new();
    fn walk(base: &Path, rel: &Path, out: &mut Vec<String>) {
        for entry in fs::read_dir(base.join(rel)).expect("read_dir") {
            let entry = entry.expect("entry");
            let child_rel = rel.join(entry.file_name());
            let p = base.join(&child_rel);
            if p.is_dir() {
                let rel = child_rel.to_string_lossy().replace('\\', "/");
                out.push(format!("{rel}/"));
                walk(base, &child_rel, out);
            } else {
                out.push(child_rel.to_string_lossy().replace('\\', "/"));
            }
        }
    }
    walk(Path::new(dir), Path::new(""), &mut out);
    out.sort();
    out
}

#[test]
fn sync_update_copies_newer_pairs_and_source_orphans_but_never_deletes() {
    // m81 A1 / m81e E5 / m82d N1: newer pairs land, orphans land, a
    // destination-side orphan survives, and a destination-newer pair survives.
    let s = Scratch::new("sync-update");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/same.txt", b"IDENTICAL\n");
    s.file("R/same.txt", b"IDENTICAL\n");
    s.file("L/newerL.txt", b"L-NEW\n");
    s.file("R/newerL.txt", b"R-OLD\n");
    s.file("L/olderL.txt", b"L-OLD\n");
    s.file("R/olderL.txt", b"R-NEW\n");
    s.file("L/orphanL.txt", b"ONLY-L\n");
    s.file("R/orphanR.txt", b"ONLY-R\n");
    // Timestamps: newerL is newest on L; olderL is newest on R.
    let base = std::time::SystemTime::now();
    let older = |secs: u64| {
        let t = base - std::time::Duration::from_secs(secs);
        let ft = fs::FileTimes::new().set_modified(t);
        ft
    };
    for (p, secs) in [
        ("L/same.txt", 10 * 86400), ("R/same.txt", 10 * 86400),
        ("L/newerL.txt", 0), ("R/newerL.txt", 5 * 86400),
        ("L/olderL.txt", 5 * 86400), ("R/olderL.txt", 0),
        ("L/orphanL.txt", 3 * 86400), ("R/orphanR.txt", 3 * 86400),
    ] {
        fs::File::options().write(true).open(s.path(p)).unwrap().set_times(older(secs)).unwrap();
    }

    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, false, ast::SyncMode::Update, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let right = tree_of(&r);
    // newerL overwritten by the source; orphanL copied; orphanR and olderL kept.
    assert!(right.contains(&"newerL.txt".to_string()), "{right:?}");
    assert!(right.contains(&"orphanL.txt".to_string()), "{right:?}");
    assert!(right.contains(&"orphanR.txt".to_string()), "update must not delete: {right:?}");
    assert_eq!(s.read("R/newerL.txt"), "L-NEW\n");
    assert_eq!(s.read("R/olderL.txt"), "R-NEW\n", "a destination-newer pair is kept");
}

#[test]
fn sync_mirror_deletes_destination_orphans_including_non_empty_folders() {
    // m81 A2 / m81b B6 / m81c C4 / m82b X1: a destination orphan file and a
    // destination-only folder both go; the source orphan lands.
    let s = Scratch::new("sync-mirror");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/a.txt", b"A\n");
    s.file("R/a.txt", b"A\n");
    s.file("L/orphanL.txt", b"ONLY-L\n");
    s.file("R/orphanR.txt", b"ONLY-R\n");
    s.file("R/roDir/inner.txt", b"INNER\n");

    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, false, ast::SyncMode::Mirror, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    let right = tree_of(&r);
    assert!(right.contains(&"orphanL.txt".to_string()), "{right:?}");
    assert!(!right.iter().any(|p| p.starts_with("orphanR")), "mirror deletes file orphans: {right:?}");
    assert!(!right.iter().any(|p| p.starts_with("roDir")), "mirror deletes folder orphans: {right:?}");
}

#[test]
fn sync_mirror_with_empty_source_wipes_the_destination() {
    // m81c C4: the most destructive measured cell — an empty source and a
    // non-empty destination leaves the destination empty.
    let s = Scratch::new("sync-mirror-empty");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("R/d1.txt", b"D1\n");
    s.file("R/d2.txt", b"D2\n");
    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, false, ast::SyncMode::Mirror, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(tree_of(&r).is_empty(), "mirror to an empty source wipes the destination");
}

#[test]
fn sync_update_skips_a_source_folder_with_no_files_unless_create_empty() {
    // m81f F3/F3b, m81h H1c/H1d, m82b X5: an empty source-only folder needs
    // `create-empty`; a source folder that holds a file lands without it.
    let s = Scratch::new("sync-create-empty");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/a.txt", b"A\n");
    s.file("R/a.txt", b"A\n");
    let _ = s.dir("L/srcEmpty");

    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, false, ast::SyncMode::Update, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(!tree_of(&r).contains(&"srcEmpty/".to_string()), "no create-empty: skipped");

    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, true, ast::SyncMode::Update, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(tree_of(&r).contains(&"srcEmpty/".to_string()), "create-empty: created");
}

#[test]
fn sync_visible_disables_create_empty() {
    // m81h H1a/H1b, m81g G5, m82c K4: with `visible` present, `create-empty`
    // has no effect.
    let s = Scratch::new("sync-visible-ce");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/a.txt", b"A\n");
    s.file("R/a.txt", b"A\n");
    let _ = s.dir("L/onlyEmpty");
    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(true, true, ast::SyncMode::Update, ast::SyncDirection::LeftToRight, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(!tree_of(&r).contains(&"onlyEmpty/".to_string()), "visible disables create-empty");
}

#[test]
fn sync_update_all_copies_both_directions() {
    // m81e E5: `update:all` runs left->right then right->left.
    let s = Scratch::new("sync-all");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/orphanL.txt", b"ONLY-L\n");
    s.file("R/orphanR.txt", b"ONLY-R\n");
    let (code, _) = run(
        vec![
            load(&l, &r, 1),
            expand_all(2),
            sync(false, false, ast::SyncMode::Update, ast::SyncDirection::All, 3),
        ],
        &[],
    );
    assert_eq!(code, 0);
    assert!(tree_of(&r).contains(&"orphanL.txt".to_string()));
    assert!(tree_of(&l).contains(&"orphanR.txt".to_string()));
}

#[test]
fn sync_without_load_is_a_silent_no_op() {
    // m81 A7, m80 S4/S5: exit 0, nothing written. The scratch is only for
    // the isolated temp root and its Drop cleanup.
    let _s = Scratch::new("sync-noload");
    let (code, reports) = run(
        vec![sync(false, false, ast::SyncMode::Mirror, ast::SyncDirection::LeftToRight, 1)],
        &[],
    );
    assert_eq!(code, 0);
    assert!(reports.is_empty());
}

#[test]
fn sync_after_a_half_load_is_exit_100() {
    // m81g G6: `load "<L>"` alone leaves no right side; the Oracle exits 100.
    let s = Scratch::new("sync-halfload");
    let l = s.dir("L");
    s.file("L/a.txt", b"A\n");
    let (code, _) = run(
        vec![
            Command::Load { left: l, right: None, line: 1 },
            sync(false, false, ast::SyncMode::Update, ast::SyncDirection::LeftToRight, 2),
        ],
        &[],
    );
    assert_eq!(code, 100, "half-load sync must be the measured exit 100");
}

#[test]
fn sync_keeps_a_destination_newer_pair_under_both_modes() {
    // m81d D2, m81f F6: a destination-newer pair survives BOTH modes — mirror
    // does not overwrite a pair the destination won.
    let s = Scratch::new("sync-destnewer");
    let l = s.dir("L");
    let r = s.dir("R");
    s.file("L/x.txt", b"L-OLD\n");
    s.file("R/x.txt", b"R-NEW\n");
    let base = std::time::SystemTime::now();
    fs::File::options()
        .write(true)
        .open(s.path("L/x.txt"))
        .unwrap()
        .set_times(
            fs::FileTimes::new()
                .set_modified(base - std::time::Duration::from_secs(864000)),
        )
        .unwrap();
    fs::File::options()
        .write(true)
        .open(s.path("R/x.txt"))
        .unwrap()
        .set_times(fs::FileTimes::new().set_modified(base))
        .unwrap();

    for mode in [ast::SyncMode::Update, ast::SyncMode::Mirror] {
        let (code, _) = run(
            vec![
                load(&l, &r, 1),
                expand_all(2),
                sync(false, false, mode, ast::SyncDirection::LeftToRight, 3),
            ],
            &[],
        );
        assert_eq!(code, 0);
        assert_eq!(
            s.read("R/x.txt"),
            "R-NEW\n",
            "{mode:?} must keep the destination's newer copy"
        );
    }
}

// ==========================================================================
// M9: picture-report (docs/16; every expectation maps to a measured cell)
// ==========================================================================

fn sbs(layout: &str, out: &str, files: &[String], line: usize) -> Command {
        Command::PictureReport {
            spec: ReportSpec {
                layout: layout.to_string(),
                output_to: Some(out.to_string()),
                comparison: files.to_vec(),
                ..ReportSpec::default()
            },
            line,
    }
}

fn sbs_opts(layout: &str, out: &str, opts: &str, files: &[String], line: usize) -> Command {
        Command::PictureReport {
            spec: ReportSpec {
                layout: layout.to_string(),
                options: opts.split(',').map(|x| x.to_string()).collect(),
                output_to: Some(out.to_string()),
                comparison: files.to_vec(),
                ..ReportSpec::default()
            },
            line,
        }
    }

#[test]
fn picture_summary_equal_lists_only_same() {
        // m83 P1 + Q1: 64 same, every other category omitted.
        let s = Scratch::new("pic-eq");
        let files = s.pix(&["eq-L.png", "eq-R.png"]);
        let out = s.str("e.out");
        let (code, reports) = run(vec![sbs("summary", &out, &files, 1)], &[]);
        assert_eq!(code, 0);
        assert!(reports[0].contains("64 same pixel(s)"), "{}", reports[0]);
        assert!(!reports[0].contains("difference pixel"), "{}", reports[0]);
    }

#[test]
fn picture_summary_counts_in_measured_order() {
        // m83h/m83n O1 order: same -> unimportant -> important.
        // fixture mix (4x4): x0 important, x1 unimportant, x2,x3 same => 8/4/4.
        let s = Scratch::new("pic-mix");
        let files = s.pix(&["mix-L.png", "mix-R.png"]);
        let out = s.str("m.out");
        let (code, reports) = run(vec![sbs("summary", &out, &files, 1)], &[]);
        assert_eq!(code, 0);
        let body = &reports[0];
        let i_same = body.find("8 same pixel(s)").expect("same");
        let i_un = body.find("4 unimportant difference pixel(s)").expect("unimp");
        let i_imp = body.find("4 important difference pixel(s)").expect("imp");
        assert!(i_same < i_un && i_un < i_imp, "{body}");
    }

#[test]
fn picture_summary_size_surplus_on_both_sides() {
        // m83j: 6x8 vs 8x6, identical overlap colour => 36 same + 12 L + 12 R,
        // and the two orphan lines print left-before-right.
        let s = Scratch::new("pic-size");
        let files = s.pix(&["size-L.png", "size-R.png"]);
        let out = s.str("z.out");
        let (code, reports) = run(vec![sbs("summary", &out, &files, 1)], &[]);
        assert_eq!(code, 0);
        let body = &reports[0];
        assert!(body.contains("36 same pixel(s)"), "{body}");
        let il = body.find("12 left orphan pixel(s)").expect("left");
        let ir = body.find("12 right orphan pixel(s)").expect("right");
        assert!(il < ir, "{body}");
    }

#[test]
fn picture_side_by_side_is_frame_only() {
        // m83b Q4, m83k E1: side-by-side lists NO count line even on differing
        // images.
        let s = Scratch::new("pic-sbs");
        let files = s.pix(&["imp-L.png", "imp-R.png"]);
        let out = s.str("s.out");
        let (code, reports) = run(vec![sbs("side-by-side", &out, &files, 1)], &[]);
        assert_eq!(code, 0);
        assert!(reports[0].starts_with("Picture Compare\r\n"), "{}", reports[0]);
        assert!(!reports[0].contains("pixel"), "{}", reports[0]);
    }

#[test]
fn picture_display_options_are_accepted_but_inert() {
        // m83n O2/O3: display-mismatches and display-matches produce BYTE-
        // IDENTICAL output to the default; only ignore-unimportant changes it.
        let s = Scratch::new("pic-opt-inert");
        let files = s.pix(&["mix-L.png", "mix-R.png"]);
        let def = {
            let o = s.str("d.out");
            let (_, r) = run(vec![sbs("summary", &o, &files, 1)], &[]);
            r[0].clone()
        };
        for opt in ["display-mismatches", "display-matches"] {
            let o = s.str(&format!("{opt}.out"));
            let (code, r) = run(vec![sbs_opts("summary", &o, opt, &files, 1)], &[]);
            assert_eq!(code, 0, "{opt}");
            assert_eq!(r[0], def, "{opt} must not change the bytes");
        }
    }

#[test]
fn picture_ignore_unimportant_adds_line_and_renames_label() {
        // m83n O4 / m83i V2: the "Ignoring Unimportant" header line and the
        // renamed count label; the counts themselves are unchanged.
        let s = Scratch::new("pic-ignore");
        let files = s.pix(&["unimp-L.png", "unimp-R.png"]);
        let out = s.str("i.out");
        let (code, reports) = run(
            vec![sbs_opts("summary", &out, "ignore-unimportant", &files, 1)],
            &[],
        );
        assert_eq!(code, 0);
        let body = &reports[0];
        assert!(body.contains("Ignoring Unimportant"), "{body}");
        assert!(body.contains("16 ignored unimportant difference pixel(s)"), "{body}");
        assert!(!body.contains("16 unimportant difference pixel(s)"), "{body}");
    }

#[test]
fn picture_bogus_option_is_106() {
        // m83b Q3-5 and m83o C2 (a bogus token among valid ones refuses the
        // whole command).
        for opt in ["line-numbers", "display-mismatches,line-numbers"] {
            let name = format!("pic-badopt-{}", opt.replace(',', "-"));
            let s = Scratch::new(&name);
            let files = s.pix(&["eq-L.png", "eq-R.png"]);
            let out = s.str("o.out");
            let (code, reports) = run(vec![sbs_opts("summary", &out, opt, &files, 1)], &[]);
            assert_eq!(code, 106, "{opt}");
            assert!(reports.is_empty(), "{opt} must write no report");
        }
    }

#[test]
fn picture_output_options_is_106() {
        // m83 P7.
        let s = Scratch::new("pic-outopts");
        let files = s.pix(&["eq-L.png", "eq-R.png"]);
        let out = s.str("o.out");
        let cmd = Command::PictureReport {
            spec: ReportSpec {
                layout: "summary".to_string(),
                output_options: vec!["html-embed".to_string()],
                output_to: Some(out.to_string()),
                comparison: files,
                ..ReportSpec::default()
            },
            line: 1,
        };
        let (code, reports) = run(vec![cmd], &[]);
        assert_eq!(code, 106);
        assert!(reports.is_empty());
    }

#[test]
fn picture_file_counts_and_layout_refuse_like_the_channel() {
        // m83 P9/O6 one file = 106; O9 three = 106; P4 bogus layout = 106.
        {
            let s = Scratch::new("pic-one");
            let f = s.pix(&["eq-L.png"]);
            let o = s.str("o.out");
            let (code, r) = run(vec![sbs("summary", &o, &f, 1)], &[]);
            assert_eq!(code, 106, "one file");
            assert!(r.is_empty());
        }
        {
            let s = Scratch::new("pic-three");
            let f = s.pix(&["eq-L.png", "eq-R.png", "eq-L.png"]);
            let o = s.str("o.out");
            let (code, _) = run(vec![sbs("summary", &o, &f, 1)], &[]);
            assert_eq!(code, 106, "three files");
        }
        {
            let s = Scratch::new("pic-badlayout");
            let f = s.pix(&["eq-L.png", "eq-R.png"]);
            let o = s.str("o.out");
            let (code, _) = run(vec![sbs("bogus", &o, &f, 1)], &[]);
            assert_eq!(code, 106, "bogus layout (m83 P4)");
        }
    }

#[test]
fn picture_missing_file_is_107_either_side() {
        // m83 P10 + m83n O7/O8: unlike hex's missing-left=106, the picture
        // channel refuses BOTH missing sides as 107 (load class).
        for which in ["left", "right"] {
            let s = Scratch::new(&format!("pic-missing-{which}"));
            let good = s.pix(&["eq-L.png", "eq-R.png"]);
            let (l, r) = if which == "left" {
                (s.str("NOPE-L.png"), good[1].clone())
            } else {
                (good[0].clone(), s.str("NOPE-R.png"))
            };
            let o = s.str("o.out");
            let (code, reports) = run(vec![sbs("summary", &o, &[l, r], 1)], &[]);
            assert_eq!(code, 107, "{which}");
            assert!(reports.is_empty(), "{which}");
        }
    }

#[test]
fn picture_zero_files_writes_the_bom_shell() {
        // m83 P8 + m83n O5: zero files is exit 0 + the BOM shell with a
        // `Base folder:` line (no file lines), NOT the hex channel's 107.
        let s = Scratch::new("pic-shell");
        let o = s.str("sh.out");
        let (code, _reports) = run(vec![sbs("summary", &o, &[], 1)], &[]);
        assert_eq!(code, 0);
        let bytes = fs::read(&o).unwrap();
        assert_eq!(&bytes[..3], b"\xEF\xBB\xBF", "the shell carries a BOM");
        let text = String::from_utf8_lossy(&bytes);
        assert!(text.contains("Base folder: "), "{text}");
    }

#[test]
fn picture_error_line_and_surplus_counting() {
        // m83 P12 / m83l EN-mixed-error: a non-image side yields an error LINE
        // (not a command failure) and the healthy side's pixels count as its
        // own surplus.
        let s = Scratch::new("pic-halfbad");
        let mut files = s.pix(&["eq-L.png"]); // 8x8 left
        files.push(s.file("halfbad-R.bin", b"\x00\x01\x02\x03"));
        let o = s.str("h.out");
        let (code, reports) = run(vec![sbs("summary", &o, &files, 1)], &[]);
        assert_eq!(code, 0);
        let body = &reports[0];
        assert!(body.contains("Right error: Unsupported Type"), "{body}");
        assert!(body.contains("64 left orphan pixel(s)"), "{body}");
    }

#[test]
fn picture_title_replaces_the_first_line() {
        // m83 P11.
        let s = Scratch::new("pic-title");
        let files = s.pix(&["eq-L.png", "eq-R.png"]);
        let o = s.str("t.out");
        let cmd = Command::PictureReport {
            spec: ReportSpec {
                layout: "side-by-side".to_string(),
                title: Some("PicTitle".to_string()),
                output_to: Some(o.to_string()),
                comparison: files,
                ..ReportSpec::default()
            },
            line: 1,
        };
        let (code, reports) = run(vec![cmd], &[]);
        assert_eq!(code, 0);
        assert!(reports[0].starts_with("PicTitle\r\n"), "{}", reports[0]);
    }

// ==========================================================================
// M11: registry-report (docs/17; every expectation maps to a measured cell)
// ==========================================================================

/// .reg fixtures are text, so they live inline: `reg_body` turns LF literals
/// into the CRLF bytes the archive fixtures carry (the parser accepts both,
/// the Oracle's own exports are CRLF).
fn reg_body(text: &str) -> Vec<u8> {
    text.replace('\n', "\r\n").into_bytes()
}

const REG_SAME: &str = "Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\ReaProbe]\n\"v\"=hex:68,65,6c,6c,6f\n";

/// `same-L.reg`/`same-R.reg` (m101 fixtures): identical trees, one value line.
fn reg_pair(s: &Scratch) -> Vec<String> {
    vec![
        s.file("same-L.reg", &reg_body(REG_SAME)),
        s.file("same-R.reg", &reg_body(REG_SAME)),
    ]
}

fn reg_cmd(layout: &str, out: &str, files: &[String], line: usize) -> Command {
    Command::RegistryReport {
        spec: ReportSpec {
            layout: layout.to_string(),
            output_to: Some(out.to_string()),
            comparison: files.to_vec(),
            ..ReportSpec::default()
        },
        line,
    }
}

fn reg_opts(layout: &str, out: &str, opts: &str, files: &[String], line: usize) -> Command {
    Command::RegistryReport {
        spec: ReportSpec {
            layout: layout.to_string(),
            options: opts.split(',').map(|x| x.to_string()).collect(),
            output_to: Some(out.to_string()),
            comparison: files.to_vec(),
            ..ReportSpec::default()
        },
        line,
    }
}

#[test]
fn registry_summary_counts_and_has_no_mode_or_table() {
    // R1/G1-sum: no Mode line, no table, count lines after the file lines.
    // The identical pair has exactly one value line -> 1 same item(s).
    let s = Scratch::new("reg-sum");
    let files = reg_pair(&s);
    let out = s.str("e.out");
    let (code, reports) = run(vec![reg_cmd("summary", &out, &files, 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("1 same item(s)"), "{body}");
    assert!(!body.contains("Mode:"), "{body}");
    assert!(!body.contains("Name"), "{body}");
}

#[test]
fn registry_sbs_has_mode_and_table_and_no_counts() {
    // G*-sid bytes (92/92 tables): sbs always carries `Mode:  All` and the
    // header/rule/rows/rule block, and NEVER a count line.
    let s = Scratch::new("reg-sbs");
    let files = reg_pair(&s);
    let out = s.str("s.out");
    let (code, reports) = run(vec![reg_cmd("side-by-side", &out, &files, 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("Mode:  All\r\n"), "{body}");
    assert!(body.contains("Name"), "{body}");
    assert!(
        body.lines().any(|l| !l.is_empty() && l.chars().all(|c| c == '-')),
        "rule line: {body}"
    );
    assert!(!body.contains("item(s)"), "{body}");
    // R1: the basekey suffix `:\\<key>` on both file lines (double backslash
    // after the colon is measured, docs/17).
    assert!(
        body.contains(":\\\\HKEY_CURRENT_USER\\ReaProbe\r\n"),
        "suffix: {body}"
    );
}

#[test]
fn registry_summary_count_order_is_measured() {
    // G9-sum + F4-sum: same -> left orphan -> right orphan -> difference,
    // zero categories omitted, no unimportant category (I1/I2).
    let s = Scratch::new("reg-order");
    let l = s.file(
        "o-L.reg",
        &reg_body(
            "Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\S]\n\"A\"=\"1\"\n\"B\"=\"2\"\n\"D\"=\"x\"\n",
        ),
    );
    let r = s.file(
        "o-R.reg",
        &reg_body(
            "Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\S]\n\"A\"=\"1\"\n\"C\"=\"3\"\n\"D\"=\"y\"\n",
        ),
    );
    let out = s.str("c.out");
    let (code, reports) = run(vec![reg_cmd("summary", &out, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    let idx: Vec<usize> = [
        "1 same item(s)",
        "1 important left orphan item(s)",
        "1 important right orphan item(s)",
        "1 important difference item(s)",
    ]
    .iter()
    .map(|want| body.find(want).unwrap_or_else(|| panic!("missing {want}: {body}")))
    .collect();
    assert!(idx.windows(2).all(|w| w[0] < w[1]), "count order {idx:?}");
    assert!(!body.contains("unimportant"), "{body}");
}

#[test]
fn registry_layout_refusals_and_uppercase() {
    // R5 bogus layout = 106; R6 missing layout = 106 (H1 precedent);
    // R17 `SUMMARY` parses (case-insensitive like the other channels).
    {
        let s = Scratch::new("reg-badlayout");
        let f = reg_pair(&s);
        let o = s.str("o.out");
        let (code, r) = run(vec![reg_cmd("bogus", &o, &f, 1)], &[]);
        assert_eq!(code, 106, "bogus layout");
        assert!(r.is_empty());
    }
    {
        let s = Scratch::new("reg-nolayout");
        let f = reg_pair(&s);
        let o = s.str("o.out");
        let cmd = Command::RegistryReport {
            spec: ReportSpec {
                output_to: Some(o.clone()),
                comparison: f,
                ..ReportSpec::default()
            },
            line: 1,
        };
        let (code, _) = run(vec![cmd], &[]);
        assert_eq!(code, 106, "missing layout");
    }
    {
        let s = Scratch::new("reg-upperlayout");
        let f = reg_pair(&s);
        let o = s.str("o.out");
        let (code, r) = run(vec![reg_cmd("SUMMARY", &o, &f, 1)], &[]);
        assert_eq!(code, 0, "uppercase layout (R17)");
        assert!(r[0].contains("1 same item(s)"));
    }
}

#[test]
fn registry_file_counts_refuse_with_106() {
    // R12 one file = 106; R13 three files = 106.
    {
        let s = Scratch::new("reg-one");
        let f = reg_pair(&s);
        let o = s.str("o.out");
        let (code, r) = run(vec![reg_cmd("summary", &o, &f[..1], 1)], &[]);
        assert_eq!(code, 106, "one file");
        assert!(r.is_empty());
    }
    {
        let s = Scratch::new("reg-three");
        let mut f = reg_pair(&s);
        f.push(s.file("third.reg", &reg_body(REG_SAME)));
        let o = s.str("o.out");
        let (code, _) = run(vec![reg_cmd("summary", &o, &f, 1)], &[]);
        assert_eq!(code, 106, "three files");
    }
}

#[test]
fn registry_missing_file_is_107_either_side() {
    // R14/R15: like picture, a missing file is the load class on EITHER side.
    for which in ["left", "right"] {
        let s = Scratch::new(&format!("reg-missing-{which}"));
        let good = reg_pair(&s);
        let (l, r) = if which == "left" {
            (s.str("NOPE-L.reg"), good[1].clone())
        } else {
            (good[0].clone(), s.str("NOPE-R.reg"))
        };
        let o = s.str("o.out");
        let (code, reports) = run(vec![reg_cmd("summary", &o, &[l, r], 1)], &[]);
        assert_eq!(code, 107, "{which}");
        assert!(reports.is_empty(), "{which}");
    }
}

#[test]
fn registry_options_surface() {
    // N1/R9/N2: a bogus token is 106 (even among valid ones), the four
    // measured tokens are all accepted with exit 0.
    let s = Scratch::new("reg-opts");
    let files = reg_pair(&s);
    for opt in [
        "display-all",
        "display-matches",
        "display-mismatches",
        "ignore-unimportant",
    ] {
        let o = s.str(&format!("{opt}.out"));
        let (code, _) = run(vec![reg_opts("summary", &o, opt, &files, 1)], &[]);
        assert_eq!(code, 0, "{opt}");
    }
    {
        let o = s.str("bad.out");
        let (code, reports) = run(
            vec![reg_opts("summary", &o, "display-mismatches,line-numbers", &files, 1)],
            &[],
        );
        assert_eq!(code, 106, "bogus token");
        assert!(reports.is_empty());
    }
}

#[test]
fn registry_output_options_is_106() {
    // R10, like hex Y10 and picture P7.
    let s = Scratch::new("reg-outopts");
    let files = reg_pair(&s);
    let out = s.str("o.out");
    let cmd = Command::RegistryReport {
        spec: ReportSpec {
            layout: "summary".to_string(),
            output_options: vec!["html-embed".to_string()],
            output_to: Some(out.to_string()),
            comparison: files,
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn registry_zero_files_writes_the_bom_shell_with_mode() {
    // R11/G11: exit 0 + BOM shell, and the registry shell carries the
    // `Mode:` line that picture's shell lacks.
    let s = Scratch::new("reg-shell");
    let o = s.str("sh.out");
    let (code, _reports) = run(vec![reg_cmd("summary", &o, &[], 1)], &[]);
    assert_eq!(code, 0);
    let bytes = fs::read(&o).unwrap();
    assert_eq!(&bytes[..3], b"\xEF\xBB\xBF", "the shell carries a BOM");
    let text = String::from_utf8_lossy(&bytes);
    assert!(text.contains("Mode:  All"), "{text}");
    assert!(text.contains("Base folder: "), "{text}");
}

#[test]
fn registry_png_pair_is_encoding_error_lines_not_a_failure() {
    // R19-png-pair / I7-png: undecodable bytes are ERROR LINES (exit 0),
    // with NO basekey suffix on the file lines (docs/17 §encoding).
    let s = Scratch::new("reg-enc");
    let mut png = vec![0x89, b'P', b'N', b'G', 0x0d, 0x1a, 0x0a, 0x0a];
    png.extend(vec![0u8; 40]);
    let l = s.file("p1.png", &png);
    let r = s.file("p2.png", &png);
    let o = s.str("h.out");
    let (code, reports) = run(vec![reg_cmd("summary", &o, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(
        body.contains("Left error: File Encoding Error (Line 1)"),
        "{body}"
    );
    assert!(body.contains("p1.png\r\n"), "suffix must be absent: {body}");
    assert!(!body.contains("p1.png:\\"), "{body}");
    assert!(!body.contains("item(s)"), "no counts: {body}");
}

#[test]
fn registry_error_line_precedes_counts() {
    // I5-parseerr / N4-only-bad: a surviving-key parse error still yields a
    // Parsing Error line plus the basekey suffix, and Unsupported Type on the
    // bad-header side; error lines sit before the counts.
    let s = Scratch::new("reg-parseerr");
    let l = s.file(
        "e-L.reg",
        &reg_body(&(REG_SAME.trim_end_matches('\n').to_owned() + "\ngarbage\n")),
    );
    let r = s.file("e-R.reg", b"bad header");
    let o = s.str("e.out");
    let (code, reports) = run(vec![reg_cmd("summary", &o, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("Left error: Parsing Error (5: 1)"), "{body}");
    assert!(body.contains("Right error: Unsupported Type"), "{body}");
    assert!(
        body.contains("\\\\HKEY_CURRENT_USER\\ReaProbe"),
        "suffix survives the parse error (G3/C10): {body}"
    );
}

#[test]
fn registry_title_and_display_filters_render() {
    // R16 title; I4-sbs-dmism/Mismatches mode + Same-row filtering on the
    // sbs table (the CLI wires Display through the frame, report_cases.rs
    // owns the geometry of the filtered rows).
    let s = Scratch::new("reg-title");
    let l = s.file(
        "t-L.reg",
        &reg_body(
            "Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\S\\Kx]\n\"a\"=\"1\"\n\n[HKEY_CURRENT_USER\\S]\n\"z\"=\"1\"\n",
        ),
    );
    let r = s.file(
        "t-R.reg",
        &reg_body("Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\S]\n\"z\"=\"1\"\n"),
    );
    let o = s.str("t.out");
    let cmd = Command::RegistryReport {
        spec: ReportSpec {
            layout: "side-by-side".to_string(),
            options: vec!["display-mismatches".to_string()],
            title: Some("RegTitle".to_string()),
            output_to: Some(o.to_string()),
            comparison: vec![l, r],
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.starts_with("RegTitle\r\n"), "{body}");
    assert!(body.contains("Mode:  Differences"), "{body}");
    assert!(body.contains("+-"), "orphans kept: {body}");
    assert!(!body.contains(" = "), "same row filtered: {body}");
}

// ==========================================================================
// M112: version-report (docs/18; every expectation maps to a measured cell)
// ==========================================================================

/// The ver fixtures: small PEs copied from the m112 corpus (the ver crate's
/// tests/fixtures tree).  `verfix` turns a bare name into a scratch path.
fn verfix(s: &Scratch, name: &str) -> String {
    let src = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/verfix")
        .join(name);
    s.file(name, &fs::read(&src).unwrap_or_else(|e| panic!("{name}: {e}")))
}

fn ver_cmd(layout: &str, out: &str, files: &[String], line: usize) -> Command {
    Command::VersionReport {
        spec: ReportSpec {
            layout: layout.to_string(),
            output_to: Some(out.to_string()),
            comparison: files.to_vec(),
            ..ReportSpec::default()
        },
        line,
    }
}

#[test]
fn version_summary_prints_counts_and_no_mode_or_table() {
    // V2: identical PEs -> the count line only, no Mode line, no table.
    let s = Scratch::new("ver-sum");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("e.out");
    let (code, reports) = run(vec![ver_cmd("summary", &o, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("same item(s)"), "{body}");
    assert!(!body.contains("Mode:"), "{body}");
    assert!(!body.contains("Name"), "{body}");
}

#[test]
fn version_sbs_has_mode_and_table() {
    // V23: the sbs layout always carries `Mode:  All` and the table block.
    let s = Scratch::new("ver-sbs");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("s.out");
    let (code, reports) = run(vec![ver_cmd("side-by-side", &o, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("Mode:  All\r\n"), "{body}");
    assert!(body.contains("Name"), "{body}");
    assert!(body.contains("Company Name"), "{body}");
}

#[test]
fn version_refuses_bogus_and_missing_layouts() {
    // V11/V12: bogus layout = 106, no layout = 106.
    let s = Scratch::new("ver-layout");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("b.out");
    let (code, reports) = run(vec![ver_cmd("bogus", &o, &[l.clone(), r.clone()], 1)], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
    let cmd = Command::VersionReport {
        spec: ReportSpec {
            layout: String::new(),
            output_to: Some(o),
            comparison: vec![l, r],
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn version_layout_case_folds() {
    // V13: `layout:SUMMARY` renders fine.
    let s = Scratch::new("ver-case");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("c.out");
    let (code, _reports) = run(vec![ver_cmd("SUMMARY", &o, &[l, r], 1)], &[]);
    assert_eq!(code, 0);
}

#[test]
fn version_options_vocabulary() {
    // V14/V15/V16/V17: ignore-unimportant adds the header line; the two
    // display-* tokens are accepted; anything else is 106.
    let s = Scratch::new("ver-opts");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("o.out");
    let opts = |v: &str, lay: &str| Command::VersionReport {
        spec: ReportSpec {
            layout: lay.to_string(),
            options: v.split(',').map(|x| x.to_string()).collect(),
            output_to: Some(o.clone()),
            comparison: vec![l.clone(), r.clone()],
            ..ReportSpec::default()
        },
        line: 1,
    };
    // W11: ignore-unimportant FOLDS into the Mode line (no separate header
    // line, unlike the picture channel), so assert on an sbs report.
    let (code, reports) = run(vec![opts("ignore-unimportant", "side-by-side")], &[]);
    assert_eq!(code, 0);
    assert!(reports[0].contains("Mode:  All, Ignoring Unimportant"), "{}", reports[0]);
    let (code, _) = run(vec![opts("display-mismatches", "summary")], &[]);
    assert_eq!(code, 0);
    let (code, _) = run(vec![opts("display-matches", "summary")], &[]);
    assert_eq!(code, 0);
    let (code, reports) = run(vec![opts("line-numbers", "summary")], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());

}

#[test]
fn version_output_options_refused() {
    // V18: output-options: = 106.
    let s = Scratch::new("ver-outopts");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("o.out");
    let cmd = Command::VersionReport {
        spec: ReportSpec {
            layout: "side-by-side".to_string(),
            output_options: vec!["html-embed".to_string()],
            output_to: Some(o),
            comparison: vec![l, r],
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn version_file_count_refusals() {
    // V19: one file = 106; V13b: three files = 106.
    let s = Scratch::new("ver-count");
    let l = verfix(&s, "ver-same-L.com");
    let r = verfix(&s, "ver-same-R.com");
    let o = s.str("o.out");
    let (code, reports) = run(vec![ver_cmd("summary", &o, &[l.clone()], 1)], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
    let (code, reports) = run(vec![ver_cmd("summary", &o, &[l.clone(), r.clone(), l.clone()], 1)], &[]);
    assert_eq!(code, 106);
    assert!(reports.is_empty());
}

#[test]
fn version_zero_files_writes_the_bom_shell_with_mode() {
    // V21: zero files is exit 0 + the BOM shell WITH a Mode line (unlike
    // picture's P8 shell, like registry's R11).
    let s = Scratch::new("ver-shell");
    let o = s.str("sh.out");
    let (code, _reports) = run(vec![ver_cmd("side-by-side", &o, &[], 1)], &[]);
    assert_eq!(code, 0);
    let bytes = fs::read(&o).unwrap();
    assert_eq!(&bytes[..3], b"\xEF\xBB\xBF", "the shell carries a BOM");
    let text = String::from_utf8_lossy(&bytes);
    assert!(text.contains("Mode:  All"), "{text}");
    assert!(text.contains("Base folder: "), "{text}");
}

#[test]
fn version_missing_and_directory_inputs() {
    // V9/V10: a missing file on either side = 107; V25: a directory = 107.
    let s = Scratch::new("ver-missing");
    let good = vec![verfix(&s, "ver-same-L.com"), verfix(&s, "ver-same-R.com")];
    let o = s.str("o.out");
    let cmd1 = ver_cmd("side-by-side", &o, &[s.str("NOPE-L.exe"), good[1].clone()], 1);
    let (code, reports) = run(vec![cmd1], &[]);
    assert_eq!(code, 107);
    assert!(reports.is_empty());
    let cmd2 = ver_cmd("side-by-side", &o, &[good[0].clone(), s.str("NOPE-R.exe")], 1);
    let (code, reports) = run(vec![cmd2], &[]);
    assert_eq!(code, 107);
    assert!(reports.is_empty());
    // V25: a directory argument.
    let dir = s.dir("adir");
    let cmd3 = ver_cmd("side-by-side", &o, &[dir, good[1].clone()], 1);
    let (code, reports) = run(vec![cmd3], &[]);
    assert_eq!(code, 107);
    assert!(reports.is_empty());
}

#[test]
fn version_single_file_form_when_both_sides_agree() {
    // V8: the same path twice renders the single `File:` line.
    let s = Scratch::new("ver-single");
    let l = verfix(&s, "ver-same-L.com");
    let o = s.str("s.out");
    let (code, reports) = run(vec![ver_cmd("side-by-side", &o, &[l.clone(), l], 1)], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.contains("File: "), "{body}");
    assert!(!body.contains("Left file:"), "{body}");
}

#[test]
fn version_diff_pair_and_title() {
    // V22: title replaces line one; a real diff pair renders both sides'
    // fields with markers.
    let s = Scratch::new("ver-diff");
    let l = verfix(&s, "ver-diff-L.com");
    let r = verfix(&s, "ver-notepad.exe");
    let o = s.str("t.out");
    let cmd = Command::VersionReport {
        spec: ReportSpec {
            layout: "side-by-side".to_string(),
            title: Some("VerTitle".to_string()),
            output_to: Some(o),
            comparison: vec![l, r],
            ..ReportSpec::default()
        },
        line: 1,
    };
    let (code, reports) = run(vec![cmd], &[]);
    assert_eq!(code, 0);
    let body = &reports[0];
    assert!(body.starts_with("VerTitle\r\n"), "{}", body);
    assert!(body.contains("<>"), "{}", body);
    assert!(body.contains("Notepad"), "{}", body);
}

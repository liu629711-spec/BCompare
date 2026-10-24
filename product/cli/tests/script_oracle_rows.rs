//! Cross-checks of the executor's reports against the **archived Oracle
//! reports** in `product/verify/runs/u5*`.
//!
//! This is the strongest evidence available without re-running the Oracle: the
//! archived reports were produced by BC and are committed in this workspace, so
//! a comparison against them is a comparison against measured behaviour.
//!
//! # What is compared, and why not the whole file
//!
//! A report embeds the fixture's absolute paths and each file's mtime, so the
//! bytes are only equal when those are equal — and this test deliberately uses
//! a temp directory rather than `D:\Rea\product\verify\runs\u5g-…`. What IS
//! path- and time-independent is the **row tree**: for every row, its nesting
//! depth, whether it is a folder or a file row, its name, its rendered
//! `<size>` (including the `<size/>` form) and — for a file row — its status.
//! That projection is extracted from both reports and compared exactly.
//!
//! # Skips
//!
//! If `product/verify/runs` is absent (a checkout without the probe archive),
//! each case prints a SKIP line and returns, following the convention already
//! used by `dir/tests/engine.rs`.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use ast::{Command, ExpandPaths, ReportSpec};
use exec::run_script;

/// The archived probe runs this file reads.
const RUNS: &str = r"D:\Rea\product\verify\runs";

#[path = "../src/script/ast.rs"]
#[allow(dead_code)]
mod ast;
#[path = "../src/script/lex.rs"]
#[allow(dead_code)]
mod lex;
#[path = "../src/script/parse.rs"]
#[allow(dead_code)]
mod parse;
#[path = "../src/script/exec.rs"]
#[allow(dead_code)]
mod exec;

// ==========================================================================
// The row projection
// ==========================================================================

/// One rendered row, reduced to what a report says about it.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct Row {
    depth: usize,
    kind: Kind,
    name: String,
    size: String,
    status: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Kind {
    Folder,
    File,
}

/// Extract the row tree from a report's `<foldercomp>` body.
///
/// Deliberately a small hand-rolled scan rather than a real XML parser: the
/// reports are machine-generated, the elements the projection needs are
/// unambiguous, and this keeps the test dependency-free (the crate has no
/// third-party dependencies and adding one for a test would change the build).
fn rows(report: &str) -> Vec<Row> {
    let mut out = Vec::new();
    // `folder_depth` counts the `<foldercomp>` elements open at this point. The
    // OUTERMOST one is the report root, so a row element's depth is exactly the
    // `<foldercomp>` nesting level at which it opened:
    //   root foldercomp        -> level 1, not a row
    //   a top-level folder row -> level 2
    //   its nested folder row  -> level 3
    //   a file row             -> one below its parent folder's level
    let mut folder_depth = 0usize;
    let mut row_depth = 0usize;
    let mut in_row = false;
    let mut rest = report;
    while let Some(idx) = rest.find('<') {
        let after = &rest[idx..];
        let Some(gt) = after.find('>') else { break };
        let element = &after[1..gt];
        rest = &after[gt + 1..];
        if element.starts_with('/') {
            if element.contains("foldercomp") {
                folder_depth = folder_depth.saturating_sub(1);
                // Closing this row's own `<foldercomp>` ends the row.
                if in_row && folder_depth < row_depth {
                    in_row = false;
                }
            }
            continue;
        }
        if element.starts_with('?') || element.starts_with('!') {
            continue;
        }
        if element.starts_with("foldercomp") {
            folder_depth += 1;
            if folder_depth >= 2 {
                out.push(Row {
                    depth: folder_depth,
                    kind: Kind::Folder,
                    name: String::new(),
                    size: String::new(),
                    status: None,
                });
                row_depth = folder_depth;
                in_row = true;
            }
            continue;
        }
        if element.starts_with("filecomp") {
            let status = element
                .split_once("status=\"")
                .and_then(|(_, s)| s.split('"').next())
                .map(|s| s.to_string());
            out.push(Row {
                depth: folder_depth + 1,
                kind: Kind::File,
                name: String::new(),
                size: String::new(),
                status,
            });
            row_depth = folder_depth + 1;
            in_row = true;
            continue;
        }
        if !in_row {
            continue;
        }
        if element == "name" {
            let text = text_of(rest);
            if let Some(row) = out.last_mut() {
                if row.name.is_empty() {
                    row.name = text;
                }
            }
            continue;
        }
        if element == "size/" {
            if let Some(row) = out.last_mut() {
                if row.size.is_empty() {
                    row.size = "/".to_string();
                }
            }
            continue;
        }
        if element == "size" {
            let text = text_of(rest);
            if let Some(row) = out.last_mut() {
                if row.size.is_empty() {
                    row.size = text;
                }
            }
            continue;
        }
    }
    let _ = row_depth;
    // Only the first `<name>`/`<size>` of a row is kept above, which is what a
    // paired row needs (its two sides repeat them).
    out
}

/// The text up to the next `<`.
fn text_of(rest: &str) -> String {
    rest.split('<').next().unwrap_or("").to_string()
}

// ==========================================================================
// Harness
// ==========================================================================

struct Scratch {
    root: PathBuf,
}

impl Scratch {
    fn new(name: &str) -> Scratch {
        let root = std::env::temp_dir().join(format!("reacmp-oracle-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).expect("scratch");
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
        fs::write(&p, bytes).expect("write");
        p.to_string_lossy().into_owned()
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

/// The u5g/u5j fixture tree, byte for byte the probes' own:
/// `A/B/f.txt(6)`, `A/g.txt(4)`, `C/i.txt(3)`, `h.txt(5)`.
fn u5g_tree(s: &Scratch, side: &str) {
    s.file(&format!("{side}/A/B/f.txt"), b"ffffff");
    s.file(&format!("{side}/A/g.txt"), b"gggg");
    s.file(&format!("{side}/C/i.txt"), b"iii");
    s.file(&format!("{side}/h.txt"), b"hhhhh");
}

/// The u5h fixture tree: the u5g tree WITHOUT `C`. The u5h run's
/// `fixtures/Ldir` holds only `A/B/f.txt`, `A/g.txt` and `h.txt`, which is why
/// none of its reports shows a `C` row.
fn u5h_tree(s: &Scratch, side: &str) {
    s.file(&format!("{side}/A/B/f.txt"), b"ffffff");
    s.file(&format!("{side}/A/g.txt"), b"gggg");
    s.file(&format!("{side}/h.txt"), b"hhhhh");
}

/// Read an archived Oracle report, or `None` when the archive is absent.
fn archived(run: &str, report: &str) -> Option<String> {
    let path = Path::new(RUNS).join(run).join("reports").join(report);
    if !path.exists() {
        return None;
    }
    let bytes = fs::read(&path).ok()?;
    Some(String::from_utf8_lossy(&bytes).into_owned())
}

/// Run one script and return the rows of its report.
fn run_rows(s: &Scratch, script: Vec<Command>, out_rel: &str, argv: &[&str]) -> Vec<Row> {
    let out = s.str(out_rel);
    let mut script = script;
    script.push(Command::FolderReport {
        spec: ReportSpec {
            layout: "xml".to_string(),
            output_to: Some(out.clone()),
            ..ReportSpec::default()
        },
        line: 99,
    });
    let argv: Vec<String> = argv.iter().map(|s| s.to_string()).collect();
    let outcome = run_script(&script, &argv);
    assert_eq!(outcome.exit_code, 0, "script failed: {:?}", outcome.diagnostics);
    let body = fs::read_to_string(&out).expect("report written");
    rows(&body)
}

fn load(l: &str, r: &str) -> Command {
    Command::Load {
        left: l.to_string(),
        right: Some(r.to_string()),
        line: 1,
    }
}

fn expand(paths: &[&str]) -> Command {
    Command::Expand {
        paths: if paths == ["all"] {
            ExpandPaths::All
        } else {
            ExpandPaths::Named(paths.iter().map(|s| s.to_string()).collect())
        },
        line: 2,
    }
}

fn filter(masks: &str) -> Command {
    Command::Filter {
        masks: masks.to_string(),
        line: 2,
    }
}

// ==========================================================================
// u5g — the six `expand` scripts
// ==========================================================================

#[test]
fn the_u5g_scripts_reproduce_the_archived_oracle_rows() {
    let cases: &[(&str, &str, &[&str])] = &[
        ("s1-no-expand", "s1-no-expand.xml", &[]),
        ("s2-expand-all", "s2-expand-all.xml", &["all"]),
        ("s3-expand-A", "s3-expand-A.xml", &["A"]),
        ("s4-expand-A-B", "s4-expand-A-B.xml", &["A\\B"]),
        ("s5-expand-A-then-B", "s5-expand-A-then-B.xml", &["A", "A\\B"]),
        ("s6-expand-A-and-C", "s6-expand-A-and-C.xml", &["A", "C"]),
    ];
    let mut checked = 0;
    for (tag, report, expands) in cases {
        let Some(oracle) = archived("u5g-probe-20261014T031338Z", report) else {
            eprintln!("SKIP {tag}: the u5g archive is not present on this host");
            continue;
        };
        let s = Scratch::new(tag);
        u5g_tree(&s, "L");
        u5g_tree(&s, "R");
        let mut script = vec![load(&s.dir("L"), &s.dir("R"))];
        for e in *expands {
            script.push(expand(&[e]));
        }
        let mine = run_rows(&s, script, "out.xml", &[]);
        let theirs = rows(&oracle);
        assert_eq!(mine, theirs, "{tag}: row tree differs from the archived Oracle report");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5g archive available");
    } else {
        assert_eq!(checked, cases.len(), "every u5g case must have been checked");
    }
}

#[test]
fn the_u5g_filter_scripts_reproduce_the_archived_oracle_rows() {
    // u5g s7 (`expand all` then `filter`) and s8 (the reverse order): both must
    // reproduce the archived rows, and the filter line must not disturb them.
    let mut checked = 0;
    for (tag, report, filter_first) in [
        ("s7-expand-all-filter", "s7-expand-all-filter.xml", false),
        ("s8-filter-then-expand", "s8-filter-then-expand.xml", true),
    ] {
        let Some(oracle) = archived("u5g-probe-20261014T031338Z", report) else {
            eprintln!("SKIP {tag}: the u5g archive is not present on this host");
            continue;
        };
        let s = Scratch::new(tag);
        u5g_tree(&s, "L");
        u5g_tree(&s, "R");
        let mut script = vec![load(&s.dir("L"), &s.dir("R"))];
        if filter_first {
            script.push(filter("*.nomatch"));
            script.push(expand(&["all"]));
        } else {
            script.push(expand(&["all"]));
            script.push(filter("*.nomatch"));
        }
        let mine = run_rows(&s, script, "out.xml", &[]);
        let theirs = rows(&oracle);
        assert_eq!(mine, theirs, "{tag}: row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5g archive available");
    }
}

// ==========================================================================
// u5h — spelling, and the folder exclude mask
// ==========================================================================

#[test]
fn the_u5h_expand_spellings_reproduce_the_archived_oracle_rows() {
    let cases: &[(&str, &str, &[&str])] = &[
        ("expand-forward-slash", "expand-forward-slash.xml", &["A/B"]),
        ("expand-trailing-sep", "expand-trailing-sep.xml", &["A\\"]),
        ("expand-a-file", "expand-a-file.xml", &["h.txt"]),
    ];
    let mut checked = 0;
    for (tag, report, expands) in cases {
        let Some(oracle) = archived("u5h-probe-20261014T031518Z", report) else {
            eprintln!("SKIP {tag}: the u5h archive is not present on this host");
            continue;
        };
        let s = Scratch::new(tag);
        u5h_tree(&s, "L");
        u5h_tree(&s, "R");
        let mut script = vec![load(&s.dir("L"), &s.dir("R"))];
        for e in *expands {
            script.push(expand(&[e]));
        }
        let mine = run_rows(&s, script, "out.xml", &[]);
        let theirs = rows(&oracle);
        assert_eq!(mine, theirs, "{tag}: row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5h archive available");
    } else {
        assert_eq!(checked, cases.len());
    }
}

#[test]
fn the_u5h_folder_exclude_mask_reproduces_the_archived_oracle_rows() {
    let mut checked = 0;
    for (tag, report, with_expand) in [
        ("fg-exclude-A-expandall", "fg-exclude-A-expandall.xml", true),
        ("fg-exclude-A-noexp", "fg-exclude-A-noexp.xml", false),
    ] {
        let Some(oracle) = archived("u5h-probe-20261014T031518Z", report) else {
            eprintln!("SKIP {tag}: the u5h archive is not present on this host");
            continue;
        };
        let s = Scratch::new(tag);
        u5h_tree(&s, "L");
        u5h_tree(&s, "R");
        let mut script = vec![load(&s.dir("L"), &s.dir("R")), filter("-A\\\\")];
        if with_expand {
            script.push(expand(&["all"]));
        }
        let mine = run_rows(&s, script, "out.xml", &[]);
        let theirs = rows(&oracle);
        assert_eq!(mine, theirs, "{tag}: row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5h archive available");
    } else {
        assert_eq!(checked, 2);
    }
}

// ==========================================================================
// u5j — per-side aggregates and a one-sided folder
// ==========================================================================

#[test]
fn the_u5j_per_side_aggregates_reproduce_the_archived_oracle_rows() {
    // The u5j fixtures differ per tree, so this uses its own builder rather than
    // the u5g shape. `A` is `d/in.txt`, 5 bytes left and 9 right, with the
    // right's mtime an hour later so the row is `rtnewer` (u5j `D-expandall`).
    let Some(oracle) = archived("u5j-probe-20261014T032503Z", "A-expandall.xml") else {
        eprintln!("SKIP: the u5j archive is not present on this host");
        return;
    };
    let s = Scratch::new("u5j-a");
    s.file("L/d/in.txt", b"11111");
    s.file("L/top.txt", b"tttt");
    s.file("R/d/in.txt", b"111111111");
    s.file("R/top.txt", b"tttt");
    let mine = run_rows(
        &s,
        vec![load(&s.dir("L"), &s.dir("R")), expand(&["all"])],
        "out.xml",
        &[],
    );
    assert_eq!(mine, rows(&oracle), "u5j A-expandall: row tree differs");
}

#[test]
fn the_u5j_one_sided_folder_reproduces_the_archived_oracle_rows() {
    let Some(oracle) = archived("u5j-probe-20261014T032503Z", "B-expandall.xml") else {
        eprintln!("SKIP: the u5j archive is not present on this host");
        return;
    };
    let s = Scratch::new("u5j-b");
    s.file("L/onlyL/x.txt", b"xx");
    s.dir("R");
    let mine = run_rows(
        &s,
        vec![load(&s.dir("L"), &s.dir("R")), expand(&["all"])],
        "out.xml",
        &[],
    );
    assert_eq!(mine, rows(&oracle), "u5j B-expandall: row tree differs");
}

// ==========================================================================
// u5c/u5d — the filter masks on their own tree
// ==========================================================================

/// The u5d fixture tree, byte for byte.
fn u5d_tree(s: &Scratch, side: &str) {
    s.file(&format!("{side}/a.txt"), b"aaaaaaaa");
    s.file(&format!("{side}/b.log"), b"bbbbbb");
    s.file(&format!("{side}/c.TXT"), b"cccccccc");
    s.file(&format!("{side}/d1.bin"), b"dd");
    s.file(&format!("{side}/other/g.log"), b"gggg");
    s.file(&format!("{side}/sub/e.txt"), b"eeee");
    s.file(&format!("{side}/sub/deep/f.txt"), b"ffff");
}

#[test]
fn the_u5d_filter_masks_reproduce_the_archived_oracle_rows() {
    let cases: &[(&str, &str)] = &[
        ("filter-upper-txt", "*.TXT"),
        ("filter-question", "d?.bin"),
        ("filter-list-mixed", "*.txt;*.TXT;-b.log"),
        ("filter-folder-only", "sub\\\\"),
    ];
    let mut checked = 0;
    for (tag, mask) in cases {
        let Some(oracle) = archived("u5d-probe-20261014T030638Z", &format!("{tag}.xml")) else {
            eprintln!("SKIP {tag}: the u5d archive is not present on this host");
            continue;
        };
        let s = Scratch::new(tag);
        u5d_tree(&s, "L");
        u5d_tree(&s, "R");
        let mine = run_rows(
            &s,
            vec![
                load(&s.dir("L"), &s.dir("R")),
                filter(mask),
                expand(&["all"]),
            ],
            "out.xml",
            &[],
        );
        let theirs = rows(&oracle);
        assert_eq!(mine, theirs, "{tag} ({mask}): row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5d archive available");
    } else {
        assert_eq!(checked, cases.len());
    }
}

#[test]
fn the_u5d_no_expand_report_reproduces_the_archived_oracle_rows() {
    // u5d `no-expand`: the control case for the whole filter set, without a
    // filter and without `expand`.
    let Some(oracle) = archived("u5d-probe-20261014T030638Z", "no-expand.xml") else {
        eprintln!("SKIP: the u5d archive is not present on this host");
        return;
    };
    let s = Scratch::new("u5d-no-expand");
    u5d_tree(&s, "L");
    u5d_tree(&s, "R");
    let mine = run_rows(&s, vec![load(&s.dir("L"), &s.dir("R"))], "out.xml", &[]);
    assert_eq!(mine, rows(&oracle), "u5d no-expand: row tree differs");
}

#[test]
fn the_u5c_filter_reports_reproduce_the_archived_oracle_rows() {
    // u5c's own fixture tree: `a.txt(8)`, `b.log(11)`, `sub/c.txt(4)`,
    // `sub/d.log(4)`.
    let cases: &[(&str, &str)] = &[
        ("filter-include-txt", "*.txt"),
        ("filter-exclude-txt", "-*.txt"),
        ("filter-folder-mask", "sub\\\\"),
        ("filter-match-nothing", "*.nomatch"),
    ];
    let build = |s: &Scratch, side: &str| {
        s.file(&format!("{side}/a.txt"), b"aaaaaaaa");
        s.file(&format!("{side}/b.log"), b"bbbbbbbbbbb");
        s.file(&format!("{side}/sub/c.txt"), b"cccc");
        s.file(&format!("{side}/sub/d.log"), b"dddd");
    };
    let mut checked = 0;
    for (tag, mask) in cases {
        let Some(oracle) = archived("u5c-probe-20261014T030510Z", &format!("{tag}.out")) else {
            eprintln!("SKIP {tag}: the u5c archive is not present on this host");
            continue;
        };
        let s = Scratch::new(&format!("u5c-{tag}"));
        build(&s, "L");
        build(&s, "R");
        let mine = run_rows(
            &s,
            vec![
                load(&s.dir("L"), &s.dir("R")),
                filter(mask),
                expand(&["all"]),
            ],
            "out.xml",
            &[],
        );
        assert_eq!(mine, rows(&oracle), "{tag} ({mask}): row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5c archive available");
    } else {
        assert_eq!(checked, cases.len());
    }
}

// ==========================================================================
// u5i — the `<filters>` element and the text-layout filter line
// ==========================================================================

#[test]
fn the_u5i_xml_filter_reports_reproduce_the_archived_oracle_rows() {
    // u5i's fixture tree: `a.txt(11)`, `b.log(5)`.
    let cases: &[(&str, Option<&str>, bool)] = &[
        ("xml-filter-only", Some("*.txt"), false),
        ("xml-iu-only", None, true),
        ("xml-filter-and-iu", Some("*.txt"), true),
        ("xml-filter-twice", Some("*.log"), false),
    ];
    let mut checked = 0;
    for (tag, mask, ignore_unimportant) in cases {
        let Some(oracle) = archived("u5i-probe-20261014T032235Z", &format!("{tag}.out")) else {
            eprintln!("SKIP {tag}: the u5i archive is not present on this host");
            continue;
        };
        let s = Scratch::new(&format!("u5i-{tag}"));
        for side in ["L", "R"] {
            s.file(&format!("{side}/a.txt"), b"aaaaaaaaaaa");
            s.file(&format!("{side}/b.log"), b"bbbbb");
        }
        let mut script = Vec::new();
        // The archived scripts put `filter` first and `criteria` second.
        if let Some(m) = mask {
            script.push(filter(m));
        }
        if *ignore_unimportant {
            script.push(Command::Criteria {
                spec: "rules-based ignore-unimportant".to_string(),
                line: 2,
            });
        }
        script.push(load(&s.dir("L"), &s.dir("R")));
        script.push(expand(&["all"]));
        // `xml-filter-twice` sends `filter` twice; the second wins.
        if *tag == "xml-filter-twice" {
            script.push(filter("*.log"));
        }
        let mine = run_rows(&s, script, "out.xml", &[]);
        assert_eq!(mine, rows(&oracle), "{tag}: row tree differs");
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5i archive available");
    } else {
        assert_eq!(checked, cases.len());
    }
}

#[test]
fn the_u5i_text_layout_filter_lines_match_the_archived_bytes() {
    // The normalizer does NOT translate the filter line (it is not in
    // `TEXT_LABEL_PAIRS`), so the bytes must agree exactly: u5i's
    // `summary-filter.out` and `sxs-filter.out` line 4 is
    // `过滤：  *.txt` = U+8FC7 U+6EE4 U+FF1A + two ASCII spaces + the mask.
    let mut checked = 0;
    for (report, layout) in [
        ("summary-filter.out", "summary"),
        ("sxs-filter.out", "side-by-side"),
    ] {
        let Some(oracle) = archived("u5i-probe-20261014T032235Z", report) else {
            eprintln!("SKIP {report}: the u5i archive is not present on this host");
            continue;
        };
        let oracle_line = oracle
            .lines()
            .find(|l| l.starts_with('\u{8fc7}'))
            .unwrap_or_else(|| panic!("{report} has no filter line"));
        let expected = "\u{8fc7}\u{6ee4}\u{ff1a}  *.txt";
        assert_eq!(
            oracle_line.trim_end_matches('\r'),
            expected,
            "{report}: the archived line is not what this test asserts"
        );

        // ...and this implementation's own line for the same script.
        let s = Scratch::new(&format!("u5i-text-{layout}"));
        for side in ["L", "R"] {
            s.file(&format!("{side}/a.txt"), b"aaaaaaaaaaa");
            s.file(&format!("{side}/b.log"), b"bbbbb");
        }
        let out = s.str("out.txt");
        let outcome = run_script(
            &[
                filter("*.txt"),
                load(&s.dir("L"), &s.dir("R")),
                expand(&["all"]),
                Command::FolderReport {
                    spec: ReportSpec {
                        layout: layout.to_string(),
                        output_to: Some(out.clone()),
                        ..ReportSpec::default()
                    },
                    line: 9,
                },
            ],
            &[],
        );
        assert_eq!(outcome.exit_code, 0, "{:?}", outcome.diagnostics);
        let body = fs::read_to_string(&out).expect("report");
        assert!(
            body.contains(expected),
            "{layout}: the measured filter line is missing from {body:?}"
        );
        assert_eq!(
            body.lines().find(|l| l.starts_with('\u{8fc7}')).map(|l| l.trim_end_matches('\r')),
            Some(expected),
            "{layout}: the filter line differs from the archived bytes"
        );
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5i archive available");
    } else {
        assert_eq!(checked, 2);
    }
}

// ==========================================================================
// The shells (u5b / u5f)
// ==========================================================================

#[test]
fn the_empty_shells_match_the_archived_oracle_bytes() {
    // u5b `folder-report-no-load` is 155 bytes; u5f `no-load-xml` is 122. Both
    // carry a BOM and a `created` attribute, so the comparison folds the
    // attribute the way the harness does.
    let s = Scratch::new("shells");
    let mut checked = 0;

    if let Some(oracle) = archived("u5b-probe-20261014T030356Z", "folder-report-no-load.xml.out")
    {
        let folded = fold_time(&oracle);
        assert_eq!(folded.len(), 155 - 19 + 4, "the archived folder shell changed size");
        let out = s.str("folder.xml");
        let outcome = run_script(
            &[Command::FolderReport {
                spec: ReportSpec {
                    layout: "xml".to_string(),
                    output_to: Some(out.clone()),
                    ..ReportSpec::default()
                },
                line: 1,
            }],
            &[],
        );
        assert_eq!(outcome.exit_code, 0);
        assert_eq!(fold_time(&fs::read_to_string(&out).unwrap()), folded);
        checked += 1;
    } else {
        eprintln!("SKIP: the u5b archive is not present on this host");
    }

    if let Some(oracle) = archived("u5f-probe-20261014T031231Z", "no-load-xml.out") {
        let folded = fold_time(&oracle);
        assert_eq!(folded.len(), 122 - 19 + 4, "the archived text shell changed size");
        let out = s.str("text.xml");
        let outcome = run_script(
            &[Command::TextReport {
                spec: ReportSpec {
                    layout: "xml".to_string(),
                    output_to: Some(out.clone()),
                    ..ReportSpec::default()
                },
                line: 1,
            }],
            &[],
        );
        assert_eq!(outcome.exit_code, 0);
        assert_eq!(fold_time(&fs::read_to_string(&out).unwrap()), folded);
        checked += 1;
    } else {
        eprintln!("SKIP: the u5f archive is not present on this host");
    }
    let _ = checked;
}

/// Replace `created="…"` with the harness's `TIME` token
/// (`verify/harness/normalize.py`, `XML_TIME_ATTRS`).
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

/// BTreeMap is imported for the projection's deterministic ordering in future
/// extensions; keep the import honest rather than dropping it silently.
#[allow(dead_code)]
type RowIndex = BTreeMap<String, Row>;

// ==========================================================================
// Byte-level: a full report body, with only the two volatile fields folded
// ==========================================================================

#[test]
fn a_folder_report_body_matches_the_archived_oracle_byte_for_byte() {
    // The strongest check in this file: not the row projection but the actual
    // bytes of the whole `<foldercomp>` body, with only the two fields the
    // harness itself folds — `created="…"` and every `<modified>…</modified>` —
    // replaced by a token. Everything else (indentation, element order, the
    // `<size/>` forms, the `<filters>` position) must agree exactly.
    //
    // u5g's fixture paths are the archived run's own, so the paths in the report
    // are substituted into the archive rather than the other way round: the
    // archive is read, its two path elements rewritten to this run's equivalent
    // temp paths, and the two bodies then compared.
    let cases: &[(&str, &str, &[&str])] = &[
        ("s1-no-expand", "s1-no-expand.xml", &[]),
        ("s3-expand-A", "s3-expand-A.xml", &["A"]),
        ("s4-expand-A-B", "s4-expand-A-B.xml", &[r"A\B"]),
        ("s2-expand-all", "s2-expand-all.xml", &["all"]),
        // s7 carries `<filters>`, which is the element whose position and bytes
        // this milestone had to get exactly right (u5i/u5g).
        ("s7-expand-all-filter", "s7-expand-all-filter.xml", &["all", "*"]),
    ];
    let mut checked = 0;
    for (tag, report, expands) in cases {
        let Some(oracle) = archived("u5g-probe-20261014T031338Z", report) else {
            eprintln!("SKIP {tag}: the u5g archive is not present on this host");
            continue;
        };
        let s = Scratch::new(&format!("bytes-{tag}"));
        u5g_tree(&s, "L");
        u5g_tree(&s, "R");
        let l = s.dir("L");
        let r = s.dir("R");
        let mut script = vec![load(&l, &r)];
        for e in *expands {
            if *e == "*" {
                script.push(filter("*.nomatch"));
            } else {
                script.push(expand(&[e]));
            }
        }
        let out = s.str("out.xml");
        script.push(Command::FolderReport {
            spec: ReportSpec {
                layout: "xml".to_string(),
                output_to: Some(out.clone()),
                ..ReportSpec::default()
            },
            line: 9,
        });
        let outcome = run_script(&script, &[]);
        assert_eq!(outcome.exit_code, 0, "{:?}", outcome.diagnostics);
        let mine = fold_volatile(&fs::read_to_string(&out).expect("report"));

        // The archive's own paths, taken from its path elements, replaced by
        // this run's.
        let oracle_body = fold_volatile(&oracle);
        let (ol, or_) = oracle_paths(&oracle_body);
        let theirs = oracle_body.replace(&ol, &l).replace(&or_, &r);
        assert_eq!(
            mine, theirs,
            "{tag}: the report body differs from the archived Oracle report"
        );
        checked += 1;
    }
    if checked == 0 {
        eprintln!("SKIP: no u5g archive available");
    } else {
        assert_eq!(checked, cases.len());
    }
}

/// Fold the two volatile fields the harness folds.
fn fold_volatile(text: &str) -> String {
    let folded = fold_time(text);
    let mut out = String::with_capacity(folded.len());
    let mut rest = folded.as_str();
    while let Some(idx) = rest.find("<modified>") {
        let (head, tail) = rest.split_at(idx + "<modified>".len());
        out.push_str(head);
        match tail.find("</modified>") {
            Some(end) => {
                out.push_str("MOD");
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

/// The two base-folder paths a rendered report echoes.
fn oracle_paths(text: &str) -> (String, String) {
    let take = |tag: &str| -> String {
        let after = text
            .split(&format!("<{tag}>"))
            .nth(1)
            .unwrap_or_else(|| panic!("no <{tag}> element"));
        after.split(&format!("</{tag}>")).next().unwrap().to_string()
    };
    (take("ltpath"), take("rtpath"))
}

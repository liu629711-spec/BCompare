//! `reacmp-dir` — a read-only folder comparison CLI.
//!
//! This is the **task A-3 tool-facing binary** inside `product/dir/`. It exists so
//! the fixture runner can drive the real engine without depending on the product
//! CLI that a parallel task owns in `product/cli/`.
//!
//! It deliberately mirrors the shape of Beyond Compare's folder script so the
//! same fixtures can be handed to the Oracle later by the project lead:
//!
//! ```text
//! # this tool
//! reacmp-dir --criteria "CRC" --layout xml --no-created <left> <right>
//!
//! # the Oracle recipe it corresponds to (verified in this workspace)
//! load "<left>" "<right>"
//! expand all
//! folder-report layout:xml output-to:"<out>"
//! ```
//!
//! # Exit codes
//!
//! * `0` — comparison ran, output written
//! * `1` — comparison ran and the folders differ
//! * `2` — error (I/O failure, undecidable comparison)
//! * `106` — script-command error (an invalid criteria keyword, or an unknown
//!   layout); this matches the code the Oracle produced for
//!   `criteria content` / `criteria binary-content` (observed)
//! * `107` — a path was not found
//!
//! `--print-exit-code` forces `0` even when the folders differ, for a runner that
//! wants to inspect the output of every case.

use std::process::ExitCode;

use reacmp_dir::criteria::CriteriaError;
use reacmp_dir::{
    compare_folders, render, CompareOptions, Criteria, DirError, Layout, ReportOptions,
};
use reacmp_vfs::LocalFs;

const USAGE: &str = "\
reacmp-dir — read-only folder comparison (ReaCompare M3)

USAGE:
    reacmp-dir [OPTIONS] <LEFT> <RIGHT>

OPTIONS:
    --criteria <SPEC>     Folder-compare criteria, as in Beyond Compare's
                          `criteria` command. Examples:
                            (omitted)            default: size + timestamp
                            --criteria \"size\"
                            --criteria \"timestamp:2sec\"
                            --criteria \"timestamp:0sec;IgnoreDST\"
                            --criteria \"CRC\"
                            --criteria \"binary\"
                            --criteria \"rules-based\"
                          --criteria \"attrib:shr size\"
                          --criteria \"timezone:ignore size\"
                          --criteria \"follow-symlinks size timestamp\"
                          --criteria \"version size\"
                          --criteria \"rules-based ignore-unimportant\"
                          Rejected with exit 106 (as the Oracle does):
                            content, binary-content
                          Implemented with measured semantics (U4 probe series):
                            version         PE FileVersion, directional
                            owner, group, permissions
                                            accepted; inert on Windows
                                            (the Oracle behaves the same)
                            ignore-unimportant
                                            folds unimportant content
                                            differences under rules-based
    --layout <NAME>       side-by-side | summary | xml        (default: xml)
    --out <FILE>          Write to FILE instead of stdout.
    --created <STAMP>     XML `created` value, e.g. \"2026/10/13 14:17:16\".
                          Omitted by default so output is byte-reproducible.
    --title <TEXT>        Report title.
    --tz-offset <MIN>     Local UTC offset in minutes east (e.g. 480 for UTC+8)
                          used to render <modified>. Default: the OS zone.
    --utc                 Shorthand for --tz-offset 0.
    --follow-symlinks     Same as adding follow-symlinks to --criteria.
    --print-exit-code     Always exit 0 when the comparison ran.
    -h, --help            Print this help.

EXIT CODES:
    0 success, 1 folders differ, 2 error, 106 script-command error,
    107 path not found.
";

struct Args {
    left: String,
    right: String,
    criteria_spec: String,
    layout: Layout,
    out: Option<String>,
    created: Option<String>,
    title: Option<String>,
    tz_offset: Option<i32>,
    follow_symlinks: bool,
    print_exit_code: bool,
}

fn main() -> ExitCode {
    match run() {
        Ok(code) => code,
        Err(err) => {
            eprintln!("reacmp-dir: {err}");
            ExitCode::from(exit_code_of(&err) as u8)
        }
    }
}

fn exit_code_of(err: &CliError) -> i32 {
    match err {
        CliError::Criteria(e) => e.exit_code(),
        CliError::Dir(e) => e.exit_code(),
        CliError::Usage(msg) => {
            eprintln!("{USAGE}");
            let _ = msg;
            2
        }
    }
}

enum CliError {
    Criteria(CriteriaError),
    Dir(DirError),
    Usage(String),
}

impl std::fmt::Display for CliError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CliError::Criteria(e) => write!(f, "{e}"),
            CliError::Dir(e) => write!(f, "{e}"),
            CliError::Usage(m) => write!(f, "{m}"),
        }
    }
}

impl From<DirError> for CliError {
    fn from(e: DirError) -> Self {
        CliError::Dir(e)
    }
}

impl From<CriteriaError> for CliError {
    fn from(e: CriteriaError) -> Self {
        CliError::Criteria(e)
    }
}

impl From<reacmp_vfs::VfsError> for CliError {
    fn from(e: reacmp_vfs::VfsError) -> Self {
        CliError::Dir(DirError::Vfs { source: e })
    }
}

fn parse_args(argv: &[String]) -> Result<Args, CliError> {
    let mut left: Option<String> = None;
    let mut right: Option<String> = None;
    let mut criteria_spec = String::new();
    let mut layout = Layout::Xml;
    let mut out = None;
    let mut created = None;
    let mut title = None;
    let mut tz_offset = None;
    let mut follow_symlinks = false;
    let mut print_exit_code = false;

    let mut i = 0;
    while i < argv.len() {
        let arg = argv[i].as_str();
        let mut next = |name: &str| -> Result<String, CliError> {
            i += 1;
            argv.get(i)
                .cloned()
                .ok_or_else(|| CliError::Usage(format!("{name} needs a value")))
        };
        match arg {
            "-h" | "--help" => {
                print!("{USAGE}");
                std::process::exit(0);
            }
            "--criteria" => criteria_spec = next("--criteria")?,
            "--layout" => layout = Layout::parse(&next("--layout")?)?,
            "--out" => out = Some(next("--out")?),
            "--created" => created = Some(next("--created")?),
            "--title" => title = Some(next("--title")?),
            "--tz-offset" => {
                let v = next("--tz-offset")?;
                tz_offset = Some(v.parse().map_err(|_| {
                    CliError::Usage(format!("--tz-offset {v:?} is not an integer"))
                })?);
            }
            "--utc" => tz_offset = Some(0),
            "--follow-symlinks" => follow_symlinks = true,
            "--print-exit-code" => print_exit_code = true,
            other if other.starts_with('-') && other != "-" => {
                return Err(CliError::Usage(format!("unknown option {other:?}")));
            }
            _ => {
                if left.is_none() {
                    left = Some(argv[i].clone());
                } else if right.is_none() {
                    right = Some(argv[i].clone());
                } else {
                    return Err(CliError::Usage(format!(
                        "unexpected extra positional argument {:?}",
                        argv[i]
                    )));
                }
            }
        }
        i += 1;
    }

    let left = left.ok_or_else(|| CliError::Usage("missing <LEFT>".to_string()))?;
    let right = right.ok_or_else(|| CliError::Usage("missing <RIGHT>".to_string()))?;

    Ok(Args {
        left,
        right,
        criteria_spec,
        layout,
        out,
        created,
        title,
        tz_offset,
        follow_symlinks,
        print_exit_code,
    })
}

fn run() -> Result<ExitCode, CliError> {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let args = parse_args(&argv)?;

    let mut criteria = Criteria::parse(&args.criteria_spec)?;
    if args.follow_symlinks {
        criteria.follow_symlinks = true;
    }

    let left = LocalFs::open(&args.left)?;
    let right = LocalFs::open(&args.right)?;

    let options = CompareOptions::default();
    let mut comparison = compare_folders(&left, &right, &criteria, options)?;

    // An explicit override wins over the OS zone; otherwise the engine's probed
    // offset (from the filesystem) is used, and `None` stays `None` so the report
    // does not claim local accuracy it does not have.
    if let Some(minutes) = args.tz_offset {
        comparison.offset_minutes = Some(minutes);
    }

    let report_options = ReportOptions {
        created: args.created.clone(),
        title: args.title.clone(),
        ignore_unimportant: criteria.ignore_unimportant,
        // The M3 tool has no `filter` command; the M4 script path supplies the
        // mask (u5i) and is the only producer of `<filters>`.
        filters: None,
    };
    let text = render(&comparison, args.layout, &report_options)?;

    match &args.out {
        Some(path) => {
            std::fs::write(path, text.as_bytes())
                .map_err(|e| CliError::Usage(format!("writing {path}: {e}")))?;
        }
        None => print!("{text}"),
    }

    // A zero exit code is reserved for "ran and nothing differs", except when the
    // caller asked for a uniform code.
    let has_changes = comparison.entries.iter().any(|n| {
        let mut changed = false;
        n.walk(&mut |node| {
            if !matches!(node.status, reacmp_dir::Status::Same) {
                changed = true;
            }
        });
        changed
    });

    if args.print_exit_code {
        Ok(ExitCode::SUCCESS)
    } else if has_changes {
        Ok(ExitCode::from(1))
    } else {
        Ok(ExitCode::SUCCESS)
    }
}

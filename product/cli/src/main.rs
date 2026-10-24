//! `reacmp` — the ReaCompare command-line front end.
//!
//! # Contract (fixed by the verification harness)
//!
//! `product/verify/harness/candidate.py` declares the product entry as
//!
//! ```text
//! argv            ["{path}", "{left}", "{right}", "{output}"]
//! option_flag     "--opt={options}"
//! layout_flag     "--layout={layout}"
//! writes_report_file  true
//! ```
//!
//! so the invocation is exactly
//!
//! ```text
//! reacmp <left> <right> <output> [--opt=<options>] [--layout=<layout>]
//! ```
//!
//! With `--layout=<name>` the named text layout is written; without it the XML
//! report is written. The report always goes to `<output>` — the harness never
//! reads stdout for this candidate.
//!
//! # The other two modes (M4)
//!
//! ```text
//! reacmp [/silent] @<script> [<arg1> [<arg2> [<arg3>]]]   BC script mode
//! reacmp /qc[=<size|crc|binary>] <left> <right>            BC quick compare
//! ```
//!
//! Dispatch order and the reasoning behind it are in
//! `product/docs/09-m4-interfaces.md` §4; the observed exit codes each mode can
//! produce are in `product/verify/probes/U5-FINDINGS.md` §1 and are implemented
//! by `exit.rs`.
//!
//! # Unsupported features are named, never silently ignored
//!
//! `--help` lists what this tool does not do. Unknown `--opt=` values, unknown
//! `--layout=` names and unimplemented script commands are hard errors: a caller
//! asking for a mode that is not implemented must not receive a report for a
//! different mode.

mod args;
mod exit;
mod script;

use args::{parse, Parsed, Run};
use exit::Exit;
use reacmp_core::compare::CompareError;
use reacmp_core::{compare_bytes, compare_files, ReportOptions};

use std::process::ExitCode;

fn main() -> ExitCode {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    match parse(&argv) {
        Ok(Parsed::Help) => {
            print!("{}", args::help_text());
            ExitCode::SUCCESS
        }
        Ok(Parsed::Version) => {
            println!("reacmp {}", reacmp_core::VERSION);
            ExitCode::SUCCESS
        }
        Ok(Parsed::Run(Run::Compare(req))) => run(req),
        Ok(Parsed::Run(Run::Script(req))) => run_script(req),
        Ok(Parsed::Run(Run::QuickCompare(req))) => run_qc(req),
        Ok(Parsed::Run(Run::Merge3(req))) => run_merge3(req),
        Ok(Parsed::Run(Run::Hex3(req))) => run_hex3(req),
        Ok(Parsed::Run(Run::Dir3(req))) => run_dir3(req),
        Err(usage) => {
            eprintln!("reacmp: {usage}");
            eprintln!("try 'reacmp --help'");
            ExitCode::FAILURE
        }
    }
}

/// Execute one comparison. Every failure path prints an explicit reason and
/// exits non-zero; no path writes a placeholder report.
fn run(req: args::Request) -> ExitCode {
    let options = match ReportOptions::parse_list(&req.options) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    let comparison = match compare_files(&req.left, &req.right, options) {
        Ok(c) => c,
        Err(CompareError::Io { path, message }) => {
            eprintln!("reacmp: cannot read {}: {message}", path.display());
            return ExitCode::FAILURE;
        }
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    // `req.layout` already carries the default (`Layout::Xml` when no
    // --layout was supplied), so the renderer needs no second decision point.
    let report = comparison.render(req.layout);
    if let Err(e) = std::fs::write(&req.output, report.as_bytes()) {
        eprintln!("reacmp: cannot write {}: {e}", req.output.display());
        return ExitCode::FAILURE;
    }
    // A report was produced; the verdict lives in the report, not the exit code.
    ExitCode::SUCCESS
}

/// `--merge3` — the three-way merge data channel.
///
/// LiuCompare-native (see the USAGE note in `--help`): Beyond Compare has no
/// merge script verb, so this output has **no** BC report contract and must
/// never be compared byte-for-byte against an Oracle. It is a JSON document
/// for the Text Merge view, carrying the three files' lines plus the
/// classified sections. The section model and the counts mirror the measured
/// BC semantics (docs/19 §6.15): `difference_sections` =
/// "N difference section(s)", `conflict_sections` = the `# N conflict
/// section(s)` count, and every unresolved conflict's output band sources the
/// CENTER/base lines (`output_source: "center"`, measured).
///
/// JSON is hand-rolled (no serde dependency): the schema is small, fixed, and
/// consumed only by our own GUI.



/// `--dir3`: the folder comparison as flat row JSON for the Folder Compare
/// view. Rows are the engine's visible walk order (hidden rows skipped) with
/// their depth — the view renders depth 0 by default (BC's measured default:
/// directories collapsed with computed subtree sizes) and can expand levels
/// later without re-plumbing. Sizes are byte counts, timestamps unix millis
/// (the view renders the measured slash-date format itself).
fn run_dir3(req: args::DirRequest) -> ExitCode {
    let left = match reacmp_vfs::LocalFs::open(req.left.as_path()) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("reacmp: load {}: {e}", req.left.display());
            return ExitCode::FAILURE;
        }
    };
    let right = match reacmp_vfs::LocalFs::open(req.right.as_path()) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("reacmp: load {}: {e}", req.right.display());
            return ExitCode::FAILURE;
        }
    };
    let comparison = match reacmp_dir::compare_folders_filtered(
        &left,
        &right,
        &reacmp_dir::Criteria::default(),
        reacmp_dir::CompareOptions::default(),
        &reacmp_dir::Filter::default(),
    ) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };

    fn json_escape(s: &str) -> String {
        s.replace(char::from(92), "\\\\").replace('"', "\\\"")
    }
    fn opt_u64(v: Option<u64>) -> String {
        match v {
            Some(n) => n.to_string(),
            None => "null".into(),
        }
    }
    fn opt_i64(v: Option<i64>) -> String {
        match v {
            Some(n) => n.to_string(),
            None => "null".into(),
        }
    }

    let mut s = String::new();
    s.push_str("{
  \"kind\": \"reacmp-dir3/1\",
");
    s.push_str("  \"rows\": [");
    let mut first = true;
    {
        let mut emit_row = |row: &reacmp_dir::TreeNode, depth: usize| {
            if !first {
                s.push_str(", ");
            }
            first = false;
            let status = row.status.xml_token().unwrap_or("unknown");
            let lsize = row.reported_size(reacmp_dir::Side::Left);
            let rsize = row.reported_size(reacmp_dir::Side::Right);
            let ltime = row
                .metadata_for(reacmp_dir::Side::Left)
                .and_then(|m| m.modified)
                .map(|t| t.unix_millis());
            let rtime = row
                .metadata_for(reacmp_dir::Side::Right)
                .and_then(|m| m.modified)
                .map(|t| t.unix_millis());
            s.push_str(&format!(
                "{{\"name\": \"{}\", \"rel\": \"{}\", \"depth\": {}, \"dir\": {}, \"status\": \"{}\", \"lsize\": {}, \"rsize\": {}, \"ltime\": {}, \"rtime\": {}}}",
                json_escape(&row.name),
                json_escape(&row.relative_path),
                depth,
                row.is_dir(),
                status,
                opt_u64(lsize),
                opt_u64(rsize),
                opt_i64(ltime),
                opt_i64(rtime),
            ));
        };
        fn visit(
            node: &reacmp_dir::TreeNode,
            depth: usize,
            emit: &mut impl FnMut(&reacmp_dir::TreeNode, usize),
        ) {
            emit(node, depth);
            for c in &node.children {
                visit(c, depth + 1, emit);
            }
        }
        for e in &comparison.entries {
            visit(e, 0, &mut emit_row);
        }
    }
    s.push_str("]
}
");

    if let Err(e) = std::fs::write(&req.output, s.as_bytes()) {
        eprintln!("reacmp: cannot write {}: {e}", req.output.display());
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

/// `--hex3`: flat alignment slot stream as JSON for the Hex Compare view.
/// Slots are `[l, r, matched]` triples (byte values, `null` = the side has
/// no byte at that slot); the view regroups into its own 16-byte rows.
fn run_hex3(req: args::HexRequest) -> ExitCode {
    let left = match std::fs::read(&req.left) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("reacmp: cannot read {}: {e}", req.left.display());
            return ExitCode::FAILURE;
        }
    };
    let right = match std::fs::read(&req.right) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("reacmp: cannot read {}: {e}", req.right.display());
            return ExitCode::FAILURE;
        }
    };
    let slots = match reacmp_core::align_slots(&left, &right) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    let [same, left_or, right_or, diff] = reacmp_core::slot_counts(&slots);

    let mut s = String::new();
    s.push_str("{
  \"kind\": \"reacmp-hex3/1\",
");
    s.push_str(&format!(
        "  \"sizes\": {{\"left\": {}, \"right\": {}}},
",
        left.len(),
        right.len()
    ));
    s.push_str(&format!(
        "  \"counts\": {{\"same\": {}, \"left_orphan\": {}, \"right_orphan\": {}, \"difference\": {}}},
",
        same, left_or, right_or, diff
    ));
    s.push_str("  \"slots\": [");
    for (i, sl) in slots.iter().enumerate() {
        if i > 0 {
            s.push_str(", ");
        }
        match (sl.l, sl.r) {
            (Some(l), Some(r)) => s.push_str(&format!("[{l},{r},{}]", sl.matched)),
            (Some(l), None) => s.push_str(&format!("[{l},null,false]")),
            (None, Some(r)) => s.push_str(&format!("[null,{r},false]")),
            (None, None) => s.push_str("[null,null,false]"),
        }
    }
    s.push_str("]
}
");

    if let Err(e) = std::fs::write(&req.output, s.as_bytes()) {
        eprintln!("reacmp: cannot write {}: {e}", req.output.display());
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

fn run_merge3(req: args::MergeRequest) -> ExitCode {
    let left = match reacmp_core::read_lines(&req.left.to_string_lossy()) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    let right = match reacmp_core::read_lines(&req.right.to_string_lossy()) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    let center = match reacmp_core::read_lines(&req.center.to_string_lossy()) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("reacmp: {e}");
            return ExitCode::FAILURE;
        }
    };
    let m = reacmp_core::merge3(&center, &left, &right);

    let mut s = String::new();
    s.push_str("{\n  \"kind\": \"reacmp-merge3/1\",\n");
    s.push_str(&format!(
        "  \"counts\": {{\"difference_sections\": {}, \"conflict_sections\": {}}},\n",
        m.difference_sections(),
        m.conflict_sections()
    ));
    s.push_str("  \"lines\": {\"left\": [");
    push_json_array(&mut s, &left);
    s.push_str("], \"center\": [");
    push_json_array(&mut s, &center);
    s.push_str("], \"right\": [");
    push_json_array(&mut s, &right);
    s.push_str("]},\n");
    s.push_str("  \"sections\": [");
    for (i, sec) in m.sections.iter().enumerate() {
        if i > 0 {
            s.push_str(", ");
        }
        let kind = match sec.kind {
            reacmp_core::SectionKind::Equal => "equal",
            reacmp_core::SectionKind::TakeLeft => "take-left",
            reacmp_core::SectionKind::TakeRight => "take-right",
            reacmp_core::SectionKind::Conflict => "conflict",
        };
        s.push_str(&format!(
            "{{\"kind\": \"{kind}\", \"base\": [{}, {}], \"left\": [{}, {}], \"right\": [{}, {}], \"output_source\": \"{}\"}}",
            sec.base.0, sec.base.1, sec.left.0, sec.left.1, sec.right.0, sec.right.1,
            sec.output_source()
        ));
    }
    s.push_str("]\n}\n");

    if let Err(e) = std::fs::write(&req.output, s.as_bytes()) {
        eprintln!("reacmp: cannot write {}: {e}", req.output.display());
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

/// Emit `["a", "b"]`-style string elements (JSON-escaped) into the buffer.
fn push_json_array(s: &mut String, lines: &[String]) {
    for (i, l) in lines.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        s.push_str(&json_quote(l));
    }
}

/// Minimal JSON string escaping (control chars + quotes + backslash).
fn json_quote(text: &str) -> String {
    let mut out = String::with_capacity(text.len() + 2);
    out.push('"');
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Run a script. The script front end parses; the executor runs; the exit code
/// is BC's (see `exit.rs`). Diagnostics go to stderr — stdout is never used to
/// carry a report.
fn run_script(req: args::ScriptRequest) -> ExitCode {
    let text = match std::fs::read_to_string(&req.path) {
        Ok(t) => t,
        Err(e) => {
            // Measured (u5, `missing-script-file`): an unreadable @script file
            // is exit 105, distinct from the 106/107 classes.
            eprintln!("reacmp: cannot read script {}: {e}", req.path.display());
            return ExitCode::from(Exit::ScriptNotLoadable.code() as u8);
        }
    };
    let commands = match script::parse_script(&text) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("reacmp: {}: {e}", req.path.display());
            return ExitCode::from(e.exit_code as u8);
        }
    };
    let outcome = script::run_script(&commands, &req.args);
    for d in &outcome.diagnostics {
        eprintln!("reacmp: {d}");
    }
    ExitCode::from(outcome.exit_code as u8)
}

/// `/qc` — compare and report nothing but the exit code.
///
/// The mapping is measured, not guessed (`probes/u5b`, `u5k`):
///
/// | condition | code |
/// |---|---|
/// | bytes identical | 1 |
/// | the only difference is the line ending | 2 |
/// | `crc`/`binary` and the bytes differ | 11 |
/// | rules-based: only unimportant differences | 12 |
/// | rules-based: an important difference | 13 |
/// | an input cannot be read | 100 |
///
/// `size` and `crc` compare the same way `binary` does for the purpose of the
/// code: any difference is 11. That is what the Oracle does — measured in u5b,
/// where `/qc=crc` and `/qc=binary` return 11 for every non-identical pair,
/// including the ones `/qc` calls 2 and 12.
fn run_qc(req: args::QuickCompareRequest) -> ExitCode {
    let left = match std::fs::read(&req.left) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("reacmp: cannot read {}: {e}", req.left.display());
            return ExitCode::from(Exit::Unknown.code() as u8);
        }
    };
    let right = match std::fs::read(&req.right) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("reacmp: cannot read {}: {e}", req.right.display());
            return ExitCode::from(Exit::Unknown.code() as u8);
        }
    };

    let code = match req.kind.as_deref() {
        // `size`: BC's quick size test compares the sizes, and — measured in
        // u5k — two files of EQUAL size but different bytes still return 11, so
        // it is not a size-only test. Reading the bytes and reporting 11 for any
        // difference reproduces every observed cell.
        Some("size") | Some("crc") | Some("binary") => {
            if left == right {
                Exit::BinarySame
            } else {
                Exit::BinaryDiff
            }
        }
        None => classify_rules_based(&left, &right, &req.left, &req.right),
        Some(other) => unreachable!("args.rs admits only size/crc/binary, got {other:?}"),
    };
    ExitCode::from(code.code() as u8)
}

/// The rules-based `/qc` verdict.
///
/// `compare_bytes` is the M2 engine, and it produces exactly the three states
/// the codes need. The line-ending case is separated first because BC calls a
/// line-ending-only difference "rules-based same" (2) rather than "similar"
/// (12), which no importance verdict expresses on its own.
///
/// The paths are passed through so grammar selection (and therefore the
/// importance rules) matches what the report path would use for the same pair.
fn classify_rules_based(
    left: &[u8],
    right: &[u8],
    left_path: &std::path::Path,
    right_path: &std::path::Path,
) -> Exit {
    if left == right {
        return Exit::BinarySame;
    }
    if strip_cr(left) == strip_cr(right) {
        return Exit::RulesBasedSame;
    }
    let mut never = || false;
    match compare_bytes(
        left,
        right,
        &left_path.to_string_lossy(),
        &right_path.to_string_lossy(),
        ReportOptions::default(),
        &mut never,
    ) {
        Ok(c) => {
            if c.differences_are_all_unimportant() {
                // Every group is same/similar/one-sided-unimportant: the
                // difference is unimportant only, which is BC's "Similar" (12).
                // `is_all_same` would be wrong here -- a trailing-whitespace-only
                // pair is all `similar` and the Oracle calls it 12, not 13.
                Exit::Similar
            } else {
                Exit::RulesBasedDiff
            }
        }
        // An undecodable input is not a difference verdict; BC's own class for
        // "could not compare" is the unknown-error code.
        Err(_) => Exit::Unknown,
    }
}

/// Drop CR bytes so a CRLF/LF-only difference can be recognised.
///
/// This is a **byte** transformation, not a text one: BC classifies a
/// line-ending difference as "rules-based same", and that is the only observed
/// case where two different byte strings share that code (u5b `crlf-only`).
fn strip_cr(bytes: &[u8]) -> Vec<u8> {
    bytes.iter().copied().filter(|b| *b != b'\r').collect()
}

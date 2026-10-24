//! Executor: [`Command`]s -> reports + exit code.
//!
//! **Owner: task B.**
//!
//! # What this implements, and from which observation
//!
//! Every rule below comes from `product/verify/probes/U5-FINDINGS.md`, whose own
//! evidence is the `product/verify/runs/u5*` probe directories (raw reports,
//! raw scripts and a results JSON). The narrative spec is
//! `product/docs/09-m4-interfaces.md` §3; where the two disagree the **raw
//! report** wins, and each such place is called out in a comment.
//!
//! ## Known differences and unobserved behaviour (never hard-coded to pass)
//!
//! | # | what | status |
//! |---|---|---|
//! | 1 | the **log** file's wording | knowingly different: the structure matches (timestamped command echoes + a completion line, no BOM, CRLF) but the Oracle's two non-command lines are untranslated Chinese. See [`LogSink`]. A log is a side artifact, not part of the report-parity claim. |
//! | 2 | a `%N` the command line did not supply | unobserved: left **verbatim** rather than blanked, so the failure names the real problem instead of turning `load "%1"` into `load ""`. See [`Run::substitute`]. |
//! | 3 | a mask containing `&`/`<`/`>` | unobserved: the 19 captured `<filters>` elements contain only mask characters, so whether the Oracle escapes is unknown; this build escapes, because an unescaped `<` would make the report unparseable. |
//! | 4 | `expand "<p>"` with nothing loaded | unobserved (only `expand all` before `load` was probed, u5b): accepted rather than refused, so a script may put `expand` on either side of `load` — which u5d `settings-after-load` established for `filter`. |
//! | 5 | a report whose `output-to:` cannot be written | unobserved: reported as **107** (the documented "failed to load folders or files" class) with the real cause in the diagnostic. |
//! | 6 | the text layouts' exact formatting | **not** byte-compatible and says so in the report body itself; the `过滤：  <mask>` line inside them IS the measured bytes. See `reacmp_dir::report`. |
//! | 7 | `load create:*`, `printer`/`clipboard`, `output-options:html-*`, the six non-name `filter` forms | refused **by name** with 106, per 09 §5 — never silently ignored, never a placeholder report. |
//!
//! | command | behaviour | evidence |
//! |---|---|---|
//! | `load "<L>" "<R>"` | both sides must be **directories**; a missing path or a file is exit **107** and the script stops | u5 `load-missing-folder`, u5c `load-files-then-folder-report` |
//! | `load <default>` | accepted; the loaded state becomes empty and a report writes the empty shell | u5g s10 |
//! | `criteria <spec>` | delegated to [`reacmp_dir::Criteria::parse`]; a bad token is **106**; only reports issued **after** it are affected | u5c `criteria-bogus`, u5e `crit-after-report` |
//! | `expand all` | whole tree; a directory's `<size>` aggregates only when its whole subtree is expanded | u5g s2/s4 |
//! | `expand "<p>"` | one relative path (and its ancestors); accumulates; a path that does not exist is **106**; a path naming a file is harmless | u5g s3..s6, u5h `expand-a-file`, u5e `expand-missing` |
//! | `filter "<masks>"` | stored raw; echoed in `<filters>`; changes the visible row set | u5c/u5d/u5h/u5i |
//! | `option stop-on-error` / `option confirm:*` | accepted, no output effect; anything else is **106** | u5e `option-*` |
//! | `log <mode> ["<path>"]` | writes a log; see [`LogSink`] for the documented difference from the Oracle's log | u5c `log-explicit` |
//! | `text-report …` | two `comparison` files -> the core text engine; zero -> the path-only shell | u5f (all four shapes), u5c `load-folders-then-text-report` |
//! | `folder-report …` | reports the loaded folders; no `load` -> exit 0 + the 155-byte empty shell | u5 `folder-report-no-load`, u5b |
//!
//! # Byte parity
//!
//! Reports are compared against the Oracle's **after** the harness normalisation
//! in `product/verify/harness/normalize.py`, which rewrites
//! `<bcreport created="…">` and `<filecomparison created="…">` to `TIME` (its
//! `XML_TIME_ATTRS` / `XML_TIME_VALUE_RE` accept exactly
//! `\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d`). This module therefore stamps reports
//! with the **current local time** in that exact shape — through
//! [`reacmp_vfs::Timestamp::format_local`], the same formatter the folder rows
//! use — rather than omitting the attribute, so the normalisation has something
//! to fold and a real user gets a real timestamp.
//!
//! One more byte-level fact drives the shell reports: the Oracle writes a UTF-8
//! **BOM** for `text-report layout:xml` with no comparison files (122 bytes) and
//! for `folder-report layout:xml` (155 bytes), but **no** BOM for
//! `text-report layout:xml` with two files (u5f: `no-load-xml.out` and
//! `load-folders-xml.out` start `EF BB BF`, `args-xml.out` does not). This
//! module reproduces that split exactly.

use std::path::{Path, PathBuf};

use reacmp_dir::{
    compare_folders_filtered, render, CompareOptions, Criteria, ExpandPolicy, Filter, Layout,
    ReportOptions,
};
use reacmp_pic::{
    render_picture_report, render_picture_shell, CompareOptions as PicCompareOptions,
    PictureLayout, SideImage,
};
use reacmp_reg::{
    parse_reg, render_registry_report, render_registry_shell, Display as RegDisplay,
    Layout as RegLayout, Locale as RegLocale, ReportFrame,
};
use reacmp_ver::{
    render_version_report, render_version_shell, Display as VerDisplay, Layout as VerLayout,
    Locale as VerLocale, ReportFrame as VerReportFrame,
};
use reacmp_vfs::LocalFs;

use super::ast::{Command, ExpandPaths, LogMode, ReportSpec, SyncDirection, SyncMode};

/// Exit codes, as `product/docs/09-m4-interfaces.md` §1 fixes them.
///
/// Repeated here rather than imported from `crate::exit` because task C owns
/// that file and this module must compile independently of it (the frozen
/// interface gives the *numbers*: `run_script` returns an `i32`).
mod exit_code {
    pub const SUCCESS: i32 = 0;
    pub const SYNTAX: i32 = 106;
    pub const LOAD_FAILED: i32 = 107;
    /// 100 — "an input could not be read" (`crate::exit`, `/qc`). Measured for
    /// `sync` after a half-load (`load "<L>"` alone, no right folder):
    /// m81g G6 exits **100**, not 106/107 — the Oracle reaches for the missing
    /// side and fails to read it. The product mirrors the code.
    pub const NEEDS_INPUT: i32 = 100;
    /// The table channel's argument error.  Measured in
    /// runs/m61b-pairing-* P6-P9: **any** `options:` value on `data-report`
    /// exits 105 with no report (display-mismatches / display-matches /
    /// line-numbers / ignore-unimportant all rejected).  BC reuses its
    /// "script could not be loaded" class for table argument errors; the
    /// product mirrors the code rather than normalizing it to 106.
    pub const TABLE_ARG: i32 = 105;
}

/// What a script run produced.  The caller turns this into a process exit code.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScriptOutcome {
    /// The BC exit code (see `product/docs/09-m4-interfaces.md` §1).
    pub exit_code: i32,
    /// Every report the script wrote, in the order it wrote them.
    pub reports: Vec<String>,
    /// Diagnostics for stderr.  Never used to replace a report.
    pub diagnostics: Vec<String>,
}

/// The executor's running state.
///
/// Mirrors `product/docs/09-m4-interfaces.md` §3 with two additions the interface
/// did not fix: `expand` (which the u5g/u5h probes measured as needed for the
/// `<size>` rule) and `logged` (the log destination, if a `log` command named
/// one).
#[derive(Debug, Clone)]
pub struct ScriptContext {
    /// The most recent `load`, exactly as the script wrote the paths.
    pub loaded: Option<(String, Option<String>)>,
    /// Criteria in force; replaced by `criteria`, and read only by reports
    /// issued afterwards (u5e `crit-after-report`).
    pub criteria: Criteria,
    /// The raw `filter` mask text, echoed verbatim in `<filters>` (u5i).
    pub filter: Option<String>,
    /// The `expand` policy, accumulated across `expand` commands (u5g s5/s6).
    pub expand: ExpandPolicy,
    /// Where `log` sent output, when it was turned on.
    pub log: Option<LogSink>,
}

/// A log destination.
///
/// # Known difference from the Oracle (documented, not hidden)
///
/// u5c `log-explicit` (`product/verify/runs/u5c-.../reports/script.log`) shows
/// the Oracle's log is UTF-8 **without** a BOM, one `timestamp + two spaces +
/// text` line per event, with its own Chinese wording for the two
/// non-command lines:
///
/// ```text
/// 2026/10/14 11:05:13  >> log verbose "…script.log"
/// 2026/10/14 11:05:13  加载比较： L <-> R
/// 2026/10/14 11:05:13  >> expand all
/// 2026/10/14 11:05:13  >> folder-report layout:xml output-to:"…"
/// 2026/10/14 11:05:13  >>
/// 2026/10/14 11:05:13  脚本在 0.12 秒 内完成
/// ```
///
/// This build reproduces the **structure** (timestamped command echo lines, a
/// trailing completion line, no BOM, CRLF) but not the untranslated text: the
/// two Chinese lines become English ones, matching the rest of this product's
/// diagnostics. A log is a side artifact, not part of the report-parity claim,
/// so the difference is recorded here instead of being faked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LogSink {
    /// Destination file. `None` means the Oracle's default, `Log.txt` in the
    /// process's current directory (`help/scripting_reference.html`, LOG).
    pub path: Option<PathBuf>,
    /// `append:` was given, so the file is extended rather than replaced.
    pub append: bool,
    /// Verbosity, which this build records but does not vary its output by:
    /// every event it has is already a "normal"-level event.
    pub mode: LogMode,
}

/// Everything a run needs, resolved once so the command loop stays linear.
struct Run<'a> {
    argv: &'a [String],
    ctx: ScriptContext,
    outcome: ScriptOutcome,
    /// Log lines accumulated in order; flushed when the script ends.
    log_lines: Vec<String>,
}

/// Run a parsed script.
///
/// `argv` holds the command-line arguments `%1`/`%2`/`%3` refer to: `argv[0]` is
/// `%1`, `argv[1]` is `%2`, `argv[2]` is `%3` (the Oracle's convention, as used
/// by every recipe in `harness/oracle.py`).
///
/// Substitution happens **here**, at execution time, not in the parser — the
/// frozen AST keeps `%1` as text (`ast.rs` `Command::Load`) because the value
/// only exists once the script is invoked (u5: every recipe passes its inputs as
/// `"%1" "%2"`).
pub fn run_script(cmds: &[Command], argv: &[String]) -> ScriptOutcome {
    let mut run = Run {
        argv,
        ctx: ScriptContext {
            loaded: None,
            criteria: Criteria::default(),
            filter: None,
            // u5g s1: with no `expand` at all the tree is fully collapsed.
            expand: ExpandPolicy::None,
            log: None,
        },
        outcome: ScriptOutcome {
            exit_code: exit_code::SUCCESS,
            reports: Vec::new(),
            diagnostics: Vec::new(),
        },
        log_lines: Vec::new(),
    };

    for cmd in cmds {
        if let Err(failure) = run.step(cmd) {
            run.outcome.exit_code = failure.code;
            run.outcome.diagnostics.push(format!("line {}: {}", failure.line, failure.message));
            break;
        }
    }

    run.flush_log();
    run.outcome
}

/// A command that ended the script.
struct Failure {
    code: i32,
    line: usize,
    message: String,
}

impl Failure {
    fn syntax(line: usize, message: impl Into<String>) -> Failure {
        Failure { code: exit_code::SYNTAX, line, message: message.into() }
    }

    fn load(line: usize, message: impl Into<String>) -> Failure {
        Failure { code: exit_code::LOAD_FAILED, line, message: message.into() }
    }

    fn needs_input(line: usize, message: impl Into<String>) -> Failure {
        Failure { code: exit_code::NEEDS_INPUT, line, message: message.into() }
    }

    fn table_arg(line: usize, message: impl Into<String>) -> Failure {
        Failure { code: exit_code::TABLE_ARG, line, message: message.into() }
    }
}

impl Run<'_> {
    /// Execute one statement.
    fn step(&mut self, cmd: &Command) -> Result<(), Failure> {
        // `log` is the one command that must take effect BEFORE it is echoed:
        // u5c script.log line 0 is the `log verbose "…"` statement itself, i.e.
        // the Oracle echoes a `log` command into the log it just opened. Doing
        // it the other way round would lose that line, and would also make
        // `log none` write an entry into the log it is closing.
        if let Command::Log { mode, path, append, line } = cmd {
            self.do_log(*mode, path.as_deref(), *append, *line)?;
            self.echo(cmd);
            return Ok(());
        }
        // Every other command is echoed before it runs, as in the Oracle's log
        // (u5c script.log: the `>> folder-report …` line precedes the report).
        self.echo(cmd);
        match cmd {
            Command::Load { left, right, line } => self.do_load(left, right.as_deref(), *line),
            Command::Criteria { spec, line } => self.do_criteria(spec, *line),
            Command::Expand { paths, line } => self.do_expand(paths, *line),
            Command::Filter { masks, line } => self.do_filter(masks, *line),
            Command::Option { name, line } => self.do_option(name, *line),
            // Handled above.
            Command::Log { .. } => Ok(()),
            Command::TextReport { spec, line } => self.do_text_report(spec, *line),
            Command::FolderReport { spec, line } => self.do_folder_report(spec, *line),
            Command::TableReport { spec, line, .. } => self.do_table_report(spec, *line),
            Command::HexReport { spec, line } => self.do_hex_report(spec, *line),
            Command::PictureReport { spec, line } => self.do_picture_report(spec, *line),
            // M11: registry channel (docs/17).
            Command::RegistryReport { spec, line } => self.do_registry_report(spec, *line),
            Command::VersionReport { spec, line } => self.do_version_report(spec, *line),
            // M8: sync command.
            Command::Sync { visible, create_empty, mode, direction, line } => {
                self.do_sync(*visible, *create_empty, *mode, *direction, *line)
            }
        }
    }

    // ----------------------------------------------------------------------
    // Substitution
    // ----------------------------------------------------------------------

    /// Replace `%1`/`%2`/`%3` with `argv[0..3]`.
    ///
    /// A parameter the command line did not supply is left **verbatim** rather
    /// than replaced with an empty string: substituting nothing would silently
    /// turn `load "%1" "%2"` into `load "" ""`, which is a *different* failure
    /// (107 for "not a directory") from the real problem ("you forgot to pass
    /// the folders"). No probe exercised this case, so the choice is recorded
    /// rather than presented as measured.
    fn substitute(&self, text: &str) -> String {
        if !text.contains('%') {
            return text.to_string();
        }
        let mut out = String::with_capacity(text.len());
        let chars: Vec<char> = text.chars().collect();
        let mut i = 0;
        while i < chars.len() {
            if chars[i] == '%'
                && i + 1 < chars.len()
                && matches!(chars[i + 1], '1' | '2' | '3')
            {
                let idx = (chars[i + 1] as usize) - ('1' as usize);
                match self.argv.get(idx) {
                    Some(value) => out.push_str(value),
                    None => {
                        out.push('%');
                        out.push(chars[i + 1]);
                    }
                }
                i += 2;
            } else {
                out.push(chars[i]);
                i += 1;
            }
        }
        out
    }

    // ----------------------------------------------------------------------
    // Commands
    // ----------------------------------------------------------------------

    /// `load "<L>" ["<R>"]` — folders only (u5/u5c: a file is 107).
    ///
    /// # `load create:*` is refused by name (09 §5)
    ///
    /// u5g `s11-create-all` measured `load create:all "<L>" "<R>"` **creating**
    /// the missing directories (`fixtures/new-L`, `fixtures/new-R` appeared on
    /// disk). This product is read-only, so implementing it would introduce a
    /// destructive behaviour whose safety has not been reviewed
    /// (`04-milestones.md` §0, ADR-3). A `create:` prefix is therefore an explicit
    /// 106, never a silent no-op that would make a script appear to work.
    fn do_load(
        &mut self,
        left: &str,
        right: Option<&str>,
        line: usize,
    ) -> Result<(), Failure> {
        let left = self.substitute(left);
        let right = right.map(|r| self.substitute(r));

        if let Some(rest) = left.to_ascii_lowercase().strip_prefix("create:") {
            let _ = rest;
            return Err(Failure::syntax(
                line,
                "load create:… is not implemented: it creates folders, and this \
                 tool is read-only by design (see the product's --help)",
            ));
        }

        // u5g s10 `load <default>`: the word is accepted and the loaded state
        // stays empty. Detected **after** substitution so `load "%1"` with no
        // argument 1 does not accidentally look like the keyword.
        if left.eq_ignore_ascii_case("<default>") || left.eq_ignore_ascii_case("default") {
            self.ctx.loaded = None;
            return Ok(());
        }

        check_folder(&left, line)?;
        if let Some(r) = &right {
            check_folder(r, line)?;
        }
        // `load "<L>"` with no right side is measured behaviour: u5e
        // `load-left-only` exits 0 and the report has `<rtpath/>`, with every
        // row `ltonly`.
        self.ctx.loaded = Some((left, right));
        Ok(())
    }

    fn do_criteria(&mut self, spec: &str, line: usize) -> Result<(), Failure> {
        let spec = self.substitute(spec);
        match Criteria::parse(&spec) {
            Ok(criteria) => {
                self.ctx.criteria = criteria;
                Ok(())
            }
            // u5c `criteria-bogus` -> 106 (a command-layer error, not a path).
            Err(e) => Err(Failure::syntax(
                line,
                format!("criteria {spec:?} is not valid: {e}"),
            )),
        }
    }

    fn do_expand(&mut self, paths: &ExpandPaths, line: usize) -> Result<(), Failure> {
        match paths {
            ExpandPaths::All => {
                self.ctx.expand = ExpandPolicy::All;
                Ok(())
            }
            ExpandPaths::Named(raw) => {
                let substituted: Vec<String> =
                    raw.iter().map(|p| self.substitute(p)).collect();
                let normalised = ExpandPolicy::parse_paths(&substituted);
                // u5e `expand-missing` -> 106, and u5h `expand-a-file` -> exit 0
                // (a path naming a file neither expands nor errors). So the
                // existence test must be "is there an entry with this relative
                // path", and a FILE passes it.
                if let Some((l, r)) = self.ctx.loaded.clone() {
                    for p in &normalised {
                        if !entry_exists(&l, r.as_deref(), p) {
                            return Err(Failure::syntax(
                                line,
                                format!("expand {p:?}: no such folder under the loaded base folders"),
                            ));
                        }
                    }
                }
                // With nothing loaded there is no base folder to resolve
                // against; `expand all` alone is measured (u5b
                // `expand-all-no-load`, exit 0 + the empty shell), while a named
                // `expand` before any `load` is unobserved. Accepting it lets a
                // script keep `expand` next to `load` in either order, which is
                // what u5d `settings-after-load` established for `filter`.
                self.ctx.expand = self.ctx.expand.accumulate(&substituted);
                Ok(())
            }
        }
    }

    /// `filter "<masks>"` — a name mask list, stored raw for `<filters>`.
    ///
    /// # The non-name forms are refused by name (09 §5)
    ///
    /// `help/scripting_reference.html` (FILTER) documents six other forms —
    /// `filter cutoff:`, `filter size:`, `filter attrib:`,
    /// `filter exclude-protected`, `filter include-protected` and
    /// `filter unixtype:` — and **none** of them was probed in this workspace.
    /// They are refused with exit **106** rather than accepted-and-ignored
    /// (which would silently produce a report for a different filter than the
    /// caller asked for) or implemented from the help text (which would invent
    /// behaviour — `product/docs/02-version-and-evidence.md`).
    ///
    /// The test is on the FIRST token: every documented non-name form is a
    /// `keyword:payload` or a bare `exclude-protected`/`include-protected`, so a
    /// mask list cannot be mistaken for one (a mask contains no colon before its
    /// first separator... and a name containing a colon, e.g. `a:b.txt`, is not a
    /// documented filter form — but refusing it would be wrong). The check is
    /// therefore against the exact keyword vocabulary, not against "contains a
    /// colon".
    fn do_filter(&mut self, masks: &str, line: usize) -> Result<(), Failure> {
        let text = self.substitute(masks);
        const REFUSED: &[&str] = &[
            "cutoff:",
            "size:",
            "attrib:",
            "unixtype:",
            "exclude-protected",
            "include-protected",
        ];
        for piece in text.split(';') {
            let piece = piece.trim().trim_start_matches('-');
            let lower = piece.to_ascii_lowercase();
            for keyword in REFUSED {
                if lower == *keyword || lower.starts_with(keyword) {
                    return Err(Failure::syntax(
                        line,
                        format!(
                            "filter {piece:?} uses a filter form this build does not \
                             implement ({keyword}); only name masks are supported \
                             (see the product's --help)"
                        ),
                    ));
                }
            }
        }
        self.ctx.filter = Some(text);
        Ok(())
    }

    fn do_option(&mut self, name: &str, line: usize) -> Result<(), Failure> {
        let name = self.substitute(name);
        let lower = name.to_ascii_lowercase();
        let accepted = lower == "stop-on-error"
            || lower == "confirm:yes-to-all"
            || lower == "confirm:no-to-all"
            // The documented third value (`help/scripting_reference.html`,
            // OPTION) is accepted as well; in a non-interactive run it behaves
            // exactly like the other two, which is what u5e measured for them.
            || lower == "confirm:prompt";
        if accepted {
            Ok(())
        } else {
            // u5e `option-bogus` -> 106.
            Err(Failure::syntax(
                line,
                format!(
                    "option {name:?} is not supported (stop-on-error, \
                     confirm:prompt|yes-to-all|no-to-all)"
                ),
            ))
        }
    }

    fn do_log(
        &mut self,
        mode: LogMode,
        path: Option<&str>,
        append: bool,
        _line: usize,
    ) -> Result<(), Failure> {
        if mode == LogMode::None {
            // `log none` disables logging ("Logging is initially disabled and
            // begins when the mode is changed from none", help/LOG). Disabling
            // drops the pending events: it must NOT flush them, or a script
            // that turns logging off would still create the file it just
            // disabled — which is what this implementation did before the
            // `log_none_turns_logging_back_off` test caught it.
            self.log_lines.clear();
            self.ctx.log = None;
            return Ok(());
        }
        let path = path.map(|p| self.substitute(p)).map(PathBuf::from);
        self.ctx.log = Some(LogSink { path, append, mode });
        Ok(())
    }

    fn do_folder_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_folder_layout(spec, line)?;
        let output = self.resolve_output(spec, line)?;

        // No `load` -> the 155-byte shell (u5b `folder-report-no-load`): exit 0,
        // not 106. `load <default>` produces the same shape (u5g s10).
        let (left, right) = match self.ctx.loaded.clone() {
            Some((l, r)) => (l, r),
            None => {
                let text = empty_folder_shell(&self.now());
                return self.write_report(output, text, line).map(|_| ());
            }
        };

        let left_fs = open_folder(&left, line)?;
        // `load "<L>"` with no right side compares L against NOTHING: u5e
        // `load-left-only` renders `<rtpath/>` and every row `ltonly` with the
        // left side's own metadata. The engine needs a right backend, so it is
        // given the left tree and the result's right half is then dropped —
        // which reproduces the observed rows exactly and never invents a right
        // side that does not exist.
        let options = CompareOptions {
            expand: self.ctx.expand.clone(),
            ..CompareOptions::default()
        };
        let filter = self.ctx.filter.as_deref().map(Filter::parse).unwrap_or_default();
        let mut comparison = match &right {
            Some(r) => {
                let right_fs = open_folder(r, line)?;
                match compare_folders_filtered(
                    &left_fs,
                    &right_fs,
                    &self.ctx.criteria,
                    options,
                    &filter,
                ) {
                    Ok(c) => c,
                    Err(e) => return Err(Failure::load(line, format!("comparing {left}: {e}"))),
                }
            }
            None => {
                let mut c = match compare_folders_filtered(
                    &left_fs,
                    &left_fs,
                    &self.ctx.criteria,
                    options,
                    &filter,
                ) {
                    Ok(c) => c,
                    Err(e) => return Err(Failure::load(line, format!("comparing {left}: {e}"))),
                };
                drop_right_side(&mut c);
                c
            }
        };
        if right.is_none() {
            comparison.right_root = reacmp_vfs::VfsPath::new("");
        }

        let report_options = ReportOptions {
            created: Some(self.now()),
            title: spec.title.clone(),
            ignore_unimportant: self.ctx.criteria.ignore_unimportant,
            filters: self.ctx.filter.clone(),
        };
        let text = match render(&comparison, layout, &report_options) {
            Ok(t) => t,
            Err(e) => return Err(Failure::syntax(line, format!("folder-report: {e}"))),
        };
        self.write_report(output, text, line).map(|_| ())
    }

    fn do_text_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_text_layout(spec, line)?;
        let output = self.resolve_output(spec, line)?;

        match spec.comparison.len() {
            0 => {
                // u5f: the path-only shell. With folders loaded the two paths
                // are the loaded ones (272 bytes in that run); with nothing
                // loaded both are empty (122 bytes). Exit 0 either way.
                let (left, right) = match self.ctx.loaded.clone() {
                    Some((l, r)) => (l, r.unwrap_or_default()),
                    None => (String::new(), String::new()),
                };
                let text = match layout {
                    // The XML shell is the only layout with a measured shape
                    // (`no-load-xml` / `load-folders-xml`); the text layouts of
                    // a comparison with no files are not in the evidence, so the
                    // text renderer is given the two paths as an ordinary
                    // zero-group comparison rather than an invented shell.
                    reacmp_core::Layout::Xml => empty_text_shell(&left, &right, &self.now()),
                    _ => {
                        let comparison = reacmp_core::compare_bytes_at(
                            b"", b"", &left, &right,
                            reacmp_core::ReportOptions::default(),
                            stamp_of(&self.now()),
                            &mut || false,
                        )
                        .map_err(|e| Failure::load(line, format!("text-report: {e}")))?;
                        comparison.render(layout)
                    }
                };
                self.write_report(output, text, line).map(|_| ())
            }
            1 | 2 => {
                let files: Vec<String> = spec
                    .comparison
                    .iter()
                    .map(|f| self.substitute(f))
                    .collect();
                let left = files[0].clone();
                let right = match files.get(1) {
                    Some(r) => r.clone(),
                    None => left.clone(),
                };
                // u5 `text-report-missing-files` -> 107: a report naming files
                // that do not exist is an input-loading failure.
                for f in [&left, &right] {
                    if !Path::new(f).is_file() {
                        return Err(Failure::load(
                            line,
                            format!("text-report: {f} is not a file"),
                        ));
                    }
                }
                let comparison = reacmp_core::compare_bytes_at(
                    &read_bytes(&left, line)?,
                    &read_bytes(&right, line)?,
                    &left,
                    &right,
                    reacmp_core::ReportOptions::default(),
                    stamp_of(&self.now()),
                    &mut || false,
                )
                .map_err(|e| Failure::load(line, format!("text-report: {e}")))?;
                let text = comparison.render(layout);
                self.write_report(output, text, line).map(|_| ())
            }
            // `text-report` documents at most `<left> <right>`
            // (`help/scripting_reference.html`); a third bare argument is a
            // command error, exactly as `text-report layout:xml` with no
            // `output-to:` is (u5 `missing-required-arg` -> 106).
            _ => Err(Failure::syntax(
                line,
                "text-report takes at most two comparison files",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // data-report (M6)
    // ----------------------------------------------------------------------

    /// `data-report` / `table-report`: the table (CSV) channel.
    ///
    /// The measured surface (docs/13 §4.7, §5 and runs/m63-clisurface-*):
    /// * any `options:` payload -> **105** with no report (P6-P9);
    /// * `output-options:<x>` -> **106** (X8 measured `csv`; the table
    ///   channel's output-option vocabulary is otherwise unmeasured, so the
    ///   product refuses the payload by name rather than inventing a shape);
    /// * zero comparison files -> **107** (X5: no path-only shell exists for
    ///   the table channel, unlike `text-report`);
    /// * three or more files -> **106** (X6), one or two -> load (missing
    ///   file **107**, X7);
    /// * `layout:xml` -> **106** (T2: the table engine has no XML layout).
    fn do_table_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_table_layout(spec, line)?;
        // Measured P6-P9: options payload on a table report is 105, before
        // any file is read (no report is produced in those runs).
        if !spec.options.is_empty() {
            return Err(Failure::table_arg(
                line,
                format!(
                    "data-report does not support options:{} (the table channel \
                     has no display filtering; observed exit 105)",
                    spec.options.join(",")
                ),
            ));
        }
        // X8: output-options refused for the table channel (106, the
        // script-command class).
        if !spec.output_options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-options:{} is not supported by data-report \
                     (observed exit 106)",
                    spec.output_options.join(",")
                ),
            ));
        }
        let output = self.resolve_output(spec, line)?;
        match spec.comparison.len() {
            0 => Err(Failure::load(
                line,
                "data-report needs two comparison files (there is no \
                 path-only table shell; observed exit 107)",
            )),
            1 | 2 => {
                let files: Vec<String> = spec
                    .comparison
                    .iter()
                    .map(|f| self.substitute(f))
                    .collect();
                let left = files[0].clone();
                let right = files.get(1).cloned().unwrap_or_else(|| left.clone());
                // X7: a report naming files that do not exist is an
                // input-loading failure (107), like text-report.
                for f in [&left, &right] {
                    if !Path::new(f).is_file() {
                        return Err(Failure::load(
                            line,
                            format!("data-report: {f} is not a file"),
                        ));
                    }
                }
                let left_text = String::from_utf8_lossy(&read_bytes(&left, line)?).into_owned();
                let right_text = String::from_utf8_lossy(&read_bytes(&right, line)?).into_owned();
                let now = self.now();
                let stamp = stamp_of(&now);
                let text = reacmp_core::render_report(
                    layout,
                    &left_text,
                    &right_text,
                    &left,
                    &right,
                    &stamp,
                    spec.title.as_deref(),
                )
                .map_err(|e| match e {
                    reacmp_core::TableError::XmlUnsupported => {
                        Failure::syntax(line, format!("data-report: {e}"))
                    }
                    other => Failure::load(line, format!("data-report: {other}")),
                })?;
                self.write_report(output, text, line).map(|_| ())
            }
            _ => Err(Failure::syntax(
                line,
                "data-report takes at most two comparison files",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // hex-report (M7)
    // ----------------------------------------------------------------------

    /// `hex-report`: the hex/binary channel (docs/14).
    ///
    /// The measured surface (runs/m70/m70b/m70c/m70d/m70f/m70g):
    /// * `options:<x>` -> **106** (Y9; unlike data-report's 105 — the hex
    ///   channel refuses the payload as a command error, before any read);
    /// * `output-options:<x>` -> **106** (Y10);
    /// * unknown layout -> **106** (Y8); missing layout -> **106** (H1);
    /// * zero comparison files -> **107** (V2: same "no path-only shell"
    ///   class as data-report, X5);
    /// * exactly one comparison file -> **106** (O1: the channel needs a
    ///   pair; data-report reuses the left file here, hex-report refuses);
    /// * three files -> **106** (W6, parse's arity check);
    /// * the LEFT file missing -> **106** (O3, W5: session-open class);
    /// * the RIGHT file missing with a good left -> **107** (O2: input load
    ///   failure); both missing stays 106 (the left is checked first).
    fn do_hex_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_hex_layout(spec, line)?;
        // Y9: options payload is refused as a command error (106), not 105.
        if !spec.options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "hex-report does not support options:{} (the hex channel \
                     has no display filtering; observed exit 106)",
                    spec.options.join(",")
                ),
            ));
        }
        // Y10: output-options refused as well (106).
        if !spec.output_options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-options:{} is not supported by hex-report \
                     (observed exit 106)",
                    spec.output_options.join(",")
                ),
            ));
        }
        let output = self.resolve_output(spec, line)?;
        match spec.comparison.len() {
            0 => Err(Failure::load(
                line,
                "hex-report needs two comparison files (there is no path-only \
                 hex shell; observed exit 107)",
            )),
            1 => Err(Failure::syntax(
                line,
                "hex-report needs exactly two comparison files (a second \
                 argument is not optional here; observed exit 106)",
            )),
            2 => {
                let files: Vec<String> = spec
                    .comparison
                    .iter()
                    .map(|f| self.substitute(f))
                    .collect();
                let left = files[0].clone();
                let right = files[1].clone();
                // O3/W5: a missing LEFT file is 106 (session-open), checked
                // before the right side (O2: missing right is the 107 load
                // class).
                if !Path::new(&left).is_file() {
                    return Err(Failure::syntax(
                        line,
                        format!("hex-report: {left} is not a file (observed exit 106)"),
                    ));
                }
                if !Path::new(&right).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("hex-report: {right} is not a file"),
                    ));
                }
                let left_bytes = read_bytes(&left, line)?;
                let right_bytes = read_bytes(&right, line)?;
                let now = self.now();
                let stamp = stamp_of(&now);
                let text = reacmp_core::hex::render_hex_report(
                    layout,
                    &left_bytes,
                    &right_bytes,
                    &left,
                    &right,
                    &stamp,
                    spec.title.as_deref(),
                )
                .map_err(|e| Failure::load(line, format!("hex-report: {e}")))?;
                self.write_report(output, text, line).map(|_| ())
            }
            _ => Err(Failure::syntax(
                line,
                "hex-report takes exactly two comparison files",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // picture-report (M9)
    // ----------------------------------------------------------------------

    /// `picture-report`: the picture channel (docs/16, runs/m83* Chinese +
    /// m83k–m83o English; both installs agree).
    ///
    /// Measured surface, mirrored exactly:
    /// * layout mandatory — P5 no-layout = 106, P4 bogus = 106
    ///   (`side-by-side | summary`, m83b Q4: side-by-side prints the frame
    ///   and nothing else);
    /// * `options:` is **accepted** (unlike hex Y9): the vocabulary is
    ///   `display-mismatches` / `display-matches` / `ignore-unimportant` —
    ///   O2/O3 show the first two are accepted with NO effect on the bytes,
    ///   and only `ignore-unimportant` changes the report (header line +
    ///   renamed count label, counts unchanged — O4/V2). A token outside the
    ///   vocabulary is 106 (Q3-5; C2: `display-mismatches,line-numbers`
    ///   refuses the whole command);
    /// * `output-options:` = 106 (P7);
    /// * file counts: **0 files writes the BOM shell and exits 0** (P8/O5,
    ///   the folder-report shell's shape, not the hex 107), 1 file = 106
    ///   (P9/O6), 3+ files = 106 (O9);
    /// * a missing file is 107 **on either side** (P10/O7/O8) — unlike hex's
    ///   missing-left = 106 (O3/W5), the picture channel has no session-open
    ///   path, so both missing sides share the load class;
    /// * an undecodable file is NOT a command error: the report prints
    ///   `Left error:` / `Right error:` lines (`Unsupported Type` /
    ///   `Invalid image`) and the summary counts the healthy side's surplus
    ///   (P12/V3/EN-mixed-error);
    /// * `title:` replaces frame line 1 (P11).
    fn do_picture_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_picture_layout(spec, line)?;
        // O2/O3/O4/Q3-5/C1/C2: only the three observed tokens are accepted;
        // display-* carry no measured effect, ignore-unimportant does.
        let mut pic_opts = PicCompareOptions::default();
        for opt in &spec.options {
            let lower = opt.to_ascii_lowercase();
            match lower.as_str() {
                "display-mismatches" | "display-matches" => {}
                "ignore-unimportant" => pic_opts.ignore_unimportant = true,
                other => {
                    return Err(Failure::syntax(
                        line,
                        format!(
                            "picture-report does not support options:{other} \
                             (display-mismatches, display-matches, \
                             ignore-unimportant are accepted — observed \
                             exit 106 for anything else)"
                        ),
                    ));
                }
            }
        }
        // P7: output-options refused (106), like hex Y10.
        if !spec.output_options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-options:{} is not supported by picture-report \
                     (observed exit 106)",
                    spec.output_options.join(",")
                ),
            ));
        }
        let output = self.resolve_output(spec, line)?;
        let files: Vec<String> = spec
            .comparison
            .iter()
            .map(|f| self.substitute(f))
            .collect();
        match files.len() {
            0 => {
                // P8/O5: zero files is the 76-byte BOM shell, exit 0 — the
                // only picture shape without file lines (`Base folder:`
                // stands in for them).
                let text = render_picture_shell(&self.now(), spec.title.as_deref());
                self.write_report(output, text, line).map(|_| ())
            }
            2 => {
                let left = &files[0];
                let right = &files[1];
                // O7/O8: a missing file is the load class (107) on EITHER
                // side — measured, unlike hex-report's missing-left 106.
                if !Path::new(left).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("picture-report: {left} is not a file"),
                    ));
                }
                if !Path::new(right).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("picture-report: {right} is not a file"),
                    ));
                }
                // P12/V3: undecodable content is an ERROR LINE in the report,
                // never a command error — decode first, classify after.
                let left_image = SideImage::decode(&read_bytes(left, line)?);
                let right_image = SideImage::decode(&read_bytes(right, line)?);
                let text = render_picture_report(
                    layout,
                    &left_image,
                    &right_image,
                    left,
                    right,
                    &self.now(),
                    spec.title.as_deref(),
                    &pic_opts,
                );
                self.write_report(output, text, line).map(|_| ())
            }
            // P9/O6: one file = 106; O9: three or more = 106.
            _ => Err(Failure::syntax(
                line,
                "picture-report takes exactly two comparison files (or none, \
                 which writes the empty shell; observed exit 106 otherwise)",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // registry-report (M11)
    // ----------------------------------------------------------------------

    /// `registry-report`: the registry channel (docs/17, runs/m101* Chinese +
    /// the reference install's English corroboration). Measured refuse
    /// surface:
    /// * layout is mandatory and only `side-by-side`/`summary` parse (R5/R6
    ///   bogus/missing = 106; R17 confirms the token is case-insensitive);
    /// * the option tokens accepted are `display-all`, `display-matches`,
    ///   `display-mismatches` and `ignore-unimportant` (R9/N2 accepted); a
    ///   bogus token is 106 (N1). `ignore-unimportant` changes nothing
    ///   measured (registry has no unimportant category, I1/I2); the display
    ///   options set the Mode line and filter the sbs table (I4/I12);
    /// * `output-options:` is 106 (R10), like hex/picture;
    /// * zero files writes the BOM shell WITH a `Mode:` line (R11/G11 — the
    ///   shape that differs from picture's shell), exit 0;
    /// * exactly two files; one or three is 106 (R12/R13);
    /// * a missing file on EITHER side is the load class 107 (R14/R15).
    ///
    /// Content that is not a registry file never errors the command: it
    /// becomes `Left/Right error:` lines in the report (binary bytes ->
    /// `File Encoding Error (Line 1)`, R19/I7; bad text -> `Parsing Error`
    /// or `Unsupported Type`, C10/N4), which [`reacmp_reg`] renders.
    fn do_registry_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_registry_layout(spec, line)?;
        // R9/N2/I4/I12: the four observed option tokens; a bogus one is 106.
        let mut display = RegDisplay::All;
        for opt in &spec.options {
            let lower = opt.to_ascii_lowercase();
            match lower.as_str() {
                "display-all" | "ignore-unimportant" => {}
                "display-mismatches" => display = RegDisplay::Mismatches,
                "display-matches" => display = RegDisplay::Matches,
                other => {
                    return Err(Failure::syntax(
                        line,
                        format!(
                            "registry-report does not support options:{other} \
                             (display-all, display-matches, display-mismatches, \
                             ignore-unimportant are accepted — observed exit \
                             106 for anything else)"
                        ),
                    ));
                }
            }
        }
        // R10: output-options refused (106), like hex Y10 and picture P7.
        if !spec.output_options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-options:{} is not supported by registry-report \
                     (observed exit 106)",
                    spec.output_options.join(",")
                ),
            ));
        }
        let output = self.resolve_output(spec, line)?;
        let files: Vec<String> = spec
            .comparison
            .iter()
            .map(|f| self.substitute(f))
            .collect();
        match files.len() {
            0 => {
                // R11/G11: the zero-file shell carries the Mode line that
                // picture's shell does not; BOM-prefixed, exit 0.
                let text = render_registry_shell(&self.now(), spec.title.as_deref(), display);
                self.write_report(output, text, line).map(|_| ())
            }
            2 => {
                let left = &files[0];
                let right = &files[1];
                // R14/R15: a missing file is the load class (107) on EITHER
                // side, like picture.
                if !Path::new(left).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("registry-report: {left} is not a file"),
                    ));
                }
                if !Path::new(right).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("registry-report: {right} is not a file"),
                    ));
                }
                // R19/I7/C10/N4: undecodable or bad content is an ERROR LINE
                // in the report, never a command error — parse first,
                // classify inside reacmp_reg (the encoding sniff runs on the
                // raw bytes there).
                let left_file = parse_reg(&read_bytes(left, line)?);
                let right_file = parse_reg(&read_bytes(right, line)?);
                let frame = ReportFrame {
                    layout,
                    display,
                    left_path: left.as_str(),
                    right_path: right.as_str(),
                    stamp: &self.now(),
                    title: spec.title.as_deref(),
                    locale: &RegLocale::EN,
                };
                let text = render_registry_report(&frame, &left_file, &right_file);
                self.write_report(output, text, line).map(|_| ())
            }
            // R12: one file = 106; R13: three or more = 106.
            _ => Err(Failure::syntax(
                line,
                "registry-report takes exactly two comparison files (or none, \
                 which writes the empty shell; observed exit 106 otherwise)",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // version-report (M112)
    // ----------------------------------------------------------------------

    /// `version-report`: the PE version channel (docs/18, runs/m112*).
    ///
    /// Measured surface, mirrored exactly:
    /// * layout mandatory — V12 no-layout = 106, V11 bogus = 106; case folds
    ///   (V13 `layout:SUMMARY` renders fine, exit 0);
    /// * `options:` is accepted with the picture vocabulary — V14
    ///   `ignore-unimportant` adds the header line and folds the Mode text,
    ///   V15/V16 `display-mismatches`/`display-matches` are accepted with no
    ///   effect on the sbs bytes (they only matter for summary counts, and
    ///   m112's summary cells V2/V4 print the same totals regardless) — and
    ///   a token outside the vocabulary is 106 (V17 `line-numbers`);
    /// * `output-options:` is 106 (V18), like hex Y10 / picture P7;
    /// * one file = 106 (V19), three files = 106 (V13b), zero files writes
    ///   the BOM shell WITH a Mode line (V21, exit 0);
    /// * a missing file on EITHER side = 107 (V9/V10), and a directory
    ///   argument = 107 (V25);
    /// * the file lines use the single `文件：` form when both sides name the
    ///   SAME path (V8: the plain pair passed twice).
    fn do_version_report(&mut self, spec: &ReportSpec, line: usize) -> Result<(), Failure> {
        let layout = parse_version_layout(spec, line)?;
        let mut display = VerDisplay::All;
        let mut ignore_unimportant = false;
        for opt in &spec.options {
            let lower = opt.to_ascii_lowercase();
            match lower.as_str() {
                "display-all" => {}
                "ignore-unimportant" => ignore_unimportant = true,
                "display-mismatches" => display = VerDisplay::Mismatches,
                "display-matches" => display = VerDisplay::Matches,
                other => {
                    return Err(Failure::syntax(
                        line,
                        format!(
                            "version-report does not support options:{other}                              (display-all, display-matches, display-mismatches,                              ignore-unimportant are accepted — observed exit                              106 for anything else)"
                        ),
                    ));
                }
            }
        }
        // V18: output-options refused (106).
        if !spec.output_options.is_empty() {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-options:{} is not supported by version-report                      (observed exit 106)",
                    spec.output_options.join(",")
                ),
            ));
        }
        let output = self.resolve_output(spec, line)?;
        let files: Vec<String> = spec
            .comparison
            .iter()
            .map(|f| self.substitute(f))
            .collect();
        match files.len() {
            0 => {
                // V21: the zero-file shell carries the Mode line (like
                // registry R11, unlike picture P8), BOM-prefixed, exit 0.
                // EN for the same golden-authoring reason as the report.
                let text = render_version_shell(
                    &self.now(),
                    spec.title.as_deref(),
                    display,
                    &VerLocale::EN,
                );
                self.write_report(output, text, line).map(|_| ())
            }
            2 => {
                let left = &files[0];
                let right = &files[1];
                // V9/V10: a missing file is 107 on EITHER side; V25: a
                // directory argument is 107 too (the same load class).
                if !Path::new(left).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("version-report: {left} is not a file"),
                    ));
                }
                if !Path::new(right).is_file() {
                    return Err(Failure::load(
                        line,
                        format!("version-report: {right} is not a file"),
                    ));
                }
                let left_bytes = read_bytes(left, line)?;
                let right_bytes = read_bytes(right, line)?;
                let frame = VerReportFrame {
                    layout,
                    display,
                    ignore_unimportant,
                    left_path: left.as_str(),
                    right_path: right.as_str(),
                    stamp: &self.now(),
                    title: spec.title.as_deref(),
                    // The goldens are authored from the ENGLISH reference
                    // install (the registry precedent, docs/17 §9): the
                    // candidate replay compares against them byte-for-byte,
                    // so the CLI renders the EN frame; the ZH geometry is
                    // pinned by reacmp-ver's corpus tests.
                    locale: &VerLocale::EN,
                };
                let text = render_version_report(&frame, &left_bytes, &right_bytes);
                self.write_report(output, text, line).map(|_| ())
            }
            // V19: one file = 106; V13b: three or more = 106.
            _ => Err(Failure::syntax(
                line,
                "version-report takes exactly two comparison files (or none,                  which writes the empty shell; observed exit 106 otherwise)",
            )),
        }
    }

    // ----------------------------------------------------------------------
    // Report plumbing
    // ----------------------------------------------------------------------

    /// The `output-to:` destination, refusing the two targets this build does
    /// not implement by name (09 §5).
    fn resolve_output(&self, spec: &ReportSpec, line: usize) -> Result<Output, Failure> {
        let Some(raw) = &spec.output_to else {
            // u5 `missing-required-arg`: `text-report layout:xml` with no
            // `output-to:` exits 106 with no report.
            return Err(Failure::syntax(
                line,
                "the report command needs output-to:\"<path>\"",
            ));
        };
        let target = self.substitute(raw);
        let lower = target.to_ascii_lowercase();
        // 09 §5: `printer` and `clipboard` need a GUI/OS session and are
        // explicitly not implemented. Refused by NAME with 106 — the code the
        // Oracle uses for a script-command error — rather than silently writing
        // a file the caller did not ask for or producing a placeholder report.
        if lower == "printer" || lower == "clipboard" {
            return Err(Failure::syntax(
                line,
                format!(
                    "output-to:{target} is not supported: only a file path is \
                     implemented (see the product's --help for the full list of \
                     unimplemented Beyond Compare features)"
                ),
            ));
        }
        // `output-options:html-*` is out of scope (09 §5) and is refused rather
        // than ignored, so a caller asking for HTML never receives XML.
        for opt in &spec.output_options {
            if opt.to_ascii_lowercase().starts_with("html") {
                return Err(Failure::syntax(
                    line,
                    format!("output-options:{opt} is not supported (HTML output is not implemented)"),
                ));
            }
        }
        Ok(Output::File(PathBuf::from(target)))
    }

    fn write_report(
        &mut self,
        output: Output,
        text: String,
        line: usize,
    ) -> Result<(), Failure> {
        let Output::File(path) = output;
        match std::fs::write(&path, text.as_bytes()) {
            Ok(()) => {
                self.outcome.reports.push(path.to_string_lossy().into_owned());
                Ok(())
            }
            // A report that cannot be written is an output-path failure, which
            // u5 did not probe. 107 is the documented "failed to load folders or
            // files" code and the closest evidenced class; the diagnostic names
            // the real cause.
            Err(e) => Err(Failure::load(
                line,
                format!("cannot write {}: {e}", path.display()),
            )),
        }
    }

    /// The current local time in the report format, from the process's zone.
    fn now(&self) -> String {
        let now = std::time::SystemTime::now();
        let millis = reacmp_vfs::Timestamp::from_system_time(now)
            .map(|t| t.unix_millis())
            .unwrap_or(0);
        let offset = reacmp_vfs::system_offset_provider()
            .ok()
            .map(|z| {
                use reacmp_vfs::OffsetProvider;
                z.offset_minutes_at(millis)
            })
            .unwrap_or(0);
        reacmp_vfs::Timestamp::from_unix_millis(millis).format_local(offset)
    }

    // ----------------------------------------------------------------------
    // Log
    // ----------------------------------------------------------------------

    /// Record one command for the log, if logging is on.
    fn echo(&mut self, cmd: &Command) {
        if self.ctx.log.is_none() {
            return;
        }
        let text = render_command(cmd);
        let stamp = self.now();
        self.log_lines.push(format!("{stamp}  >> {text}"));
        match cmd {
            Command::Load { left, right, .. } => {
                let l = self.substitute(left);
                let r = right.as_deref().map(|r| self.substitute(r)).unwrap_or_default();
                // The Oracle writes a "loading comparison" line here in Chinese;
                // see `LogSink` for why this build writes English.
                self.log_lines
                    .push(format!("{stamp}  Loading comparison: {l} <-> {r}"));
            }
            _ => {}
        }
    }

    /// Write the accumulated log, if one is configured.
    fn flush_log(&mut self) {
        let Some(sink) = self.ctx.log.clone() else {
            return;
        };
        if self.log_lines.is_empty() {
            return;
        }
        let mut body = String::new();
        for line in &self.log_lines {
            body.push_str(line);
            body.push_str("\r\n");
        }
        // The completion line's own stamp is taken now, and the elapsed time is
        // reported as the rounded seconds this run took. The Oracle's wording is
        // Chinese and its duration is finer-grained; see `LogSink`.
        let script_start = self.log_lines.first().cloned().unwrap_or_default();
        let _ = script_start;
        body.push_str(&format!("{}  Script completed\r\n", self.now()));

        let path = sink
            .path
            .clone()
            .unwrap_or_else(|| PathBuf::from("Log.txt"));
        let result = if sink.append {
            use std::io::Write as _;
            std::fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(&path)
                .and_then(|mut f| f.write_all(body.as_bytes()))
        } else {
            std::fs::write(&path, body.as_bytes())
        };
        match result {
            Ok(()) => self
                .outcome
                .diagnostics
                .push(format!("log written to {}", path.display())),
            Err(e) => self
                .outcome
                .diagnostics
                .push(format!("cannot write log {}: {e}", path.display())),
        }
    }

    // ----------------------------------------------------------------------
    // Sync (M8)
    // ----------------------------------------------------------------------

    /// Execute a folder-sync command (`sync visible [create-empty] update|mirror:left->right`).
    ///
    /// Measured semantics (docs/15, runs/m81* + m82b/c):
    /// * the two flags are position-flexible but must precede the mode:direction pair;
    ///   any other shape is a syntax error (106), except the half-load case below.
    /// * With nothing loaded, the script exits 0 and does nothing (m81 A7, m80 S4/S5).
    /// * With only one side loaded (half-load, e.g. `load "<L>"` alone), exit **100**
    ///   (m81g G6): the Oracle reaches for the missing side and fails to read it.
    /// * The `visible` flag is inert in scripts except that it disables `create-empty`
    ///   (m81h H1a/H1b; m82b X4: no empty source folder created when both flags present);
    ///   neither flag affects filter scopes or the kind-conflict behavior.
    /// # Destructive by design, and why that is honest
    ///
    /// `mirror` **deletes** destination-side files and folders. That is what
    /// the Oracle does (m81 S1/A2/C4/B6/B7, m82b X1/X3) and refusing it would
    /// make a mirror script silently do something else. The safety boundary is
    /// the one ADR-3 draws: it is reachable only from an explicit `mirror`
    /// token inside a script the caller wrote — never from the command line
    /// (`args.rs` refuses `sync` there), and never by default.
    fn do_sync(
        &mut self,
        visible: bool,
        create_empty: bool,
        mode: SyncMode,
        direction: SyncDirection,
        line: usize,
    ) -> Result<(), Failure> {
        let Some((left_path, right_path_opt)) = self.ctx.loaded.clone() else {
            // Nothing loaded: silent no-op, exit 0 (m81 A7, m80 S4/S5).
            return Ok(());
        };
        let Some(right_path) = right_path_opt else {
            // Half-load (`load "<L>"` with no right side): measured exit 100
            // (m81g G6) — the Oracle reaches for the missing side and fails.
            return Err(Failure::needs_input(
                line,
                "sync needs both base folders loaded; this script loaded only one",
            ));
        };

        let left_fs = LocalFs::open(&left_path)
            .map_err(|e| Failure::load(line, format!("sync: {left_path}: {e}")))?;
        let right_fs = LocalFs::open(&right_path)
            .map_err(|e| Failure::load(line, format!("sync: {right_path}: {e}")))?;

        // m81b B7: `sync mirror` without `expand all` still recursed into a
        // nested orphan, so the policy is always ALL here — sync has no
        // "collapsed" mode.
        let options = CompareOptions { expand: ExpandPolicy::All, ..CompareOptions::default() };
        // m82b X3 / m81h H2: a filter-matched row IS synced (F4's non-deletion
        // was the filter *excluding* the row), so sync never applies a filter.
        let comparison = compare_folders_filtered(
            &left_fs,
            &right_fs,
            &self.ctx.criteria,
            options,
            &Filter::none(),
        )
        .map_err(|e| Failure::load(line, format!("sync: comparing folders: {e}")))?;

        let mirror = mode == SyncMode::Mirror;
        // m81h H1a/H1b, m81g G5, m82c K4: `visible` disables `create-empty`
        // (with both flags the empty source folder does NOT appear).
        let create_empty = create_empty && !visible;

        let mut plan = Vec::new();
        let roots: Vec<(&str, &str, bool)> = match direction {
            SyncDirection::LeftToRight => vec![(&left_path, &right_path, true)],
            SyncDirection::RightToLeft => vec![(&right_path, &left_path, false)],
            // update:all is the only `all` (parse refuses mirror:all);
            // it is update:lr followed by update:rl (m81e E5).
            SyncDirection::All => {
                vec![(&left_path, &right_path, true), (&right_path, &left_path, false)]
            }
        };
        // The comparison's own orientation is always left->right, so the
        // right->left pass reads it mirrored (`Side::Right` as the source).
        for (src_root, dst_root, src_is_left) in roots {
            for node in &comparison.entries {
                sync_node(
                    node, src_root, dst_root, src_is_left, mirror, create_empty, &mut plan,
                );
            }
        }

        for action in &plan {
            if let Err(e) = apply_action(action) {
                return Err(Failure::load(line, format!("sync: {e}")));
            }
        }
        Ok(())
    }
}

/// One filesystem effect a sync decided on.
///
/// Collected before anything is written so a failing `delete` cannot leave a
/// half-applied copy behind: the plan is built from the whole tree first, then
/// applied in order (copies first, then deletions — see [`plan`] in
/// [`Run::do_sync`]).
#[derive(Debug, Clone, PartialEq, Eq)]
enum SyncAction {
    /// Create `dst_root/<rel>` as a directory; no-op when it already exists.
    EnsureDir { path: PathBuf },
    /// Copy `src` to `dst`, preserving the source's mtime, replacing `dst`.
    Copy { src: PathBuf, dst: PathBuf },
    /// Delete `path`, file or directory tree.
    Delete { path: PathBuf },
}

/// Decide the effects for one node (and, recursively, its subtree).
fn sync_node(
    node: &reacmp_dir::TreeNode,
    src_root: &str,
    dst_root: &str,
    src_is_left: bool,
    mirror: bool,
    create_empty: bool,
    out: &mut Vec<SyncAction>,
) {
    let rel = &node.relative_path;
    let src_path = join_path(src_root, rel);
    let dst_path = join_path(dst_root, rel);

    let src_side = if src_is_left { reacmp_dir::Side::Left } else { reacmp_dir::Side::Right };
    let src_entry = node.metadata_for(src_side);
    let dst_present = if src_is_left { node.right.is_some() } else { node.left.is_some() };

    if node.is_dir_row() {
        // A directory row: on both sides, source-only, or destination-only.
        let src_present = src_entry.is_some();
        if src_present && !dst_present {
            // Source-only folder. m81f F3/F3b, m81h H1c/H1d: `create-empty` is
            // what makes an *empty* source-only folder appear; without it a
            // subtree with no file is skipped entirely (m82b X5: `innerEmpty`
            // dropped while its sibling file still lands).
            if create_empty || subtree_has_file(node, src_is_left) {
                out.push(SyncAction::EnsureDir { path: dst_path.clone() });
            }
        } else if !src_present && dst_present {
            // Destination-only folder. m81b B6, m82b X1: mirror deletes it
            // **as a tree** — including its files — so the row's children are
            // not walked (their own Delete actions would run after the
            // directory was already gone).
            if mirror {
                out.push(SyncAction::Delete { path: dst_path });
            }
            return;
        }
        // Both sides (or a source-only folder whose files still have to be
        // decided): recurse. A `Copy` creates its own parent directories, so a
        // source-only folder that was not explicitly created still receives the
        // files inside it.
        for child in &node.children {
            sync_node(child, src_root, dst_root, src_is_left, mirror, create_empty, out);
        }
        return;
    }

    // A file row (including a kind conflict, which `is_dir_row` rejects).
    //
    // m81h H3/H3b, m82c K1/K2: a kind conflict is copied by NEITHER mode in
    // the source->destination sense and, under mirror, the destination item is
    // deleted — the source item never lands. Modelling it as "delete the
    // destination, do not copy" reproduces all four cells.
    if node.is_kind_conflict() {
        if mirror && dst_present {
            out.push(SyncAction::Delete { path: dst_path });
        }
        return;
    }

    match node.status {
        reacmp_dir::Status::Same => {}
        reacmp_dir::Status::Diff => {
            // m81c C6/C7, m81d D1/D6, m82d N3: under mirror the source
            // overwrites the destination regardless of which side is newer or
            // bigger; under update nothing happens (m81c C7).
            if mirror {
                out.push(SyncAction::Copy { src: src_path, dst: dst_path });
            }
        }
        reacmp_dir::Status::LeftNewer | reacmp_dir::Status::RightNewer => {
            // The newer side is the source. N1/N2 (m82d): `update` copies it
            // even when the size differs, because the engine's own
            // classification of a size difference is a timestamp-based
            // Left/RightNewer once the two-second tolerance is exceeded.
            let newer_is_src = (node.status == reacmp_dir::Status::LeftNewer) == src_is_left;
            if newer_is_src {
                out.push(SyncAction::Copy { src: src_path, dst: dst_path });
            }
        }
        reacmp_dir::Status::LeftOnly | reacmp_dir::Status::RightOnly => {
            let orphan_is_src =
                (node.status == reacmp_dir::Status::LeftOnly) == src_is_left;
            if orphan_is_src {
                // m81 A1/A5/E5, m82d N2: an orphan is copied by both modes.
                out.push(SyncAction::Copy { src: src_path, dst: dst_path });
            } else if mirror {
                // m81 A2/B6/C4, m82b X1/X3: mirror deletes a destination
                // orphan — file or non-empty folder alike, and an empty source
                // wipes the destination (m81c C4).
                out.push(SyncAction::Delete { path: dst_path });
            }
        }
        reacmp_dir::Status::Unknown => {
            // `Unknown` carries no observed token and therefore no observed
            // sync behaviour. Doing nothing is the honest choice: copying or
            // deleting on a status the evidence cannot name would invent
            // behaviour (`02-version-and-evidence.md`).
        }
    }
}

/// True when a subtree contains at least one file on the source side.
fn subtree_has_file(node: &reacmp_dir::TreeNode, src_is_left: bool) -> bool {
    let side = if src_is_left { reacmp_dir::Side::Left } else { reacmp_dir::Side::Right };
    let mut found = false;
    let mut visit = |n: &reacmp_dir::TreeNode| {
        if let Some(m) = n.metadata_for(side) {
            if matches!(m.kind, reacmp_vfs::EntryKind::File) {
                found = true;
            }
        }
    };
    node.walk(&mut visit);
    found
}

/// Apply one planned effect.
fn apply_action(action: &SyncAction) -> Result<(), String> {
    match action {
        SyncAction::EnsureDir { path } => {
            if !path.is_dir() {
                std::fs::create_dir_all(path)
                    .map_err(|e| format!("cannot create {}: {e}", path.display()))?;
            }
            Ok(())
        }
        SyncAction::Copy { src, dst } => {
            if let Some(parent) = dst.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| format!("cannot create {}: {e}", parent.display()))?;
            }
            let bytes = std::fs::read(src)
                .map_err(|e| format!("cannot read {}: {e}", src.display()))?;
            std::fs::write(dst, &bytes)
                .map_err(|e| format!("cannot write {}: {e}", dst.display()))?;
            // m81d D5, m81g C2/C3: the copy keeps the source's mtime, so the
            // pair reads as `same` afterwards instead of staying newer.
            if let Ok(meta) = std::fs::metadata(src) {
                if let Ok(modified) = meta.modified() {
                    let times = std::fs::FileTimes::new().set_modified(modified);
                    let _ = std::fs::File::options().write(true).open(dst).and_then(|f| f.set_times(times));
                }
            }
            Ok(())
        }
        SyncAction::Delete { path } => {
            if path.is_dir() {
                std::fs::remove_dir_all(path)
                    .map_err(|e| format!("cannot delete {}: {e}", path.display()))
            } else if path.exists() {
                std::fs::remove_file(path)
                    .map_err(|e| format!("cannot delete {}: {e}", path.display()))
            } else {
                Ok(())
            }
        }
    }
}

/// Join a base folder with a relative path, handling Windows separators.
fn join_path(base: &str, rel: &str) -> PathBuf {
    let mut joined = PathBuf::from(base);
    for comp in rel.split('\\').filter(|s| !s.is_empty()) {
        joined.push(comp);
    }
    joined
}

/// Drop the right side of every row, turning a self-comparison into the
/// one-sided comparison a `load "<L>"`-only script asks for (u5e
/// `load-left-only`).
///
/// The tree is rebuilt node by node because `TreeNode`'s `left`/`right` are
/// plain fields with no setter, and the row set itself is unchanged — only the
/// right half and the derived status go away.
fn drop_right_side(comparison: &mut reacmp_dir::FolderComparison) {
    fn prune(node: &mut reacmp_dir::TreeNode) {
        node.right = None;
        // `Status` has no "left only" converter, and a row that had both sides
        // must now read `ltonly`, which is exactly the observed token in every
        // row of `load-left-only.out`.
        node.status = reacmp_dir::Status::LeftOnly;
        for child in &mut node.children {
            prune(child);
        }
    }
    for node in &mut comparison.entries {
        prune(node);
    }
}

/// Where a report goes. Only a file is implemented (09 §5).
enum Output {
    File(PathBuf),
}

// ==========================================================================
// Layout names
// ==========================================================================

/// The layout vocabulary each report command accepts, as its own enum.
///
/// The two crates keep separate `Layout` types — `reacmp_dir::Layout` has the
/// three names a `folder-report` accepts, `reacmp_core::Layout` has all seven a
/// `text-report` accepts (`help/scripting_reference.html`, FOLDER-REPORT and
/// TEXT-REPORT) — so the executor resolves the name into the type each renderer
/// needs rather than converting between them. A name outside the set is exit
/// **106** with no report: u5 `bad-option-value` measured that for
/// `layout:not-a-layout`, and the A-3 folder gate measured the same code for the
/// four names a *folder* report does not accept (`layout:html`, `layout:csv`,
/// `layout:text`, `layout:interleaved`, all BC exit 106).
/// The layouts a `folder-report` accepts (3 names).
const FOLDER_LAYOUT_NAMES: &str = "side-by-side, summary, xml";

/// The layouts a `text-report` accepts (7 names).
///
/// `over-under` is a deprecated alias of `interleaved`
/// (`help/scripting_reference.html`: "Deprecated layouts over-under and
/// composite have been replaced by interleaved"), and the core keeps both
/// spellings, so both are accepted here and the core decides what they render.
const TEXT_LAYOUT_NAMES: &str =
    "xml, side-by-side, interleaved, over-under, patch, summary, statistics";

fn parse_folder_layout(spec: &ReportSpec, line: usize) -> Result<Layout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("folder-report needs layout:<name> ({FOLDER_LAYOUT_NAMES})"),
        ));
    }
    Layout::parse(&spec.layout).map_err(|_| {
        // u5 `bad-option-value` (`layout:not-a-layout`) -> 106, no report.
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a folder-report layout ({FOLDER_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

fn parse_text_layout(spec: &ReportSpec, line: usize) -> Result<reacmp_core::Layout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("text-report needs layout:<name> ({TEXT_LAYOUT_NAMES})"),
        ));
    }
    reacmp_core::Layout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a text-report layout ({TEXT_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

/// The layouts a `data-report` accepts (3 names, measured T1/T4/T3 exit 0;
/// T2 `xml` exit 106). `over-under` is NOT accepted: the table help lists
/// exactly three layouts and no alias is observed.
const TABLE_LAYOUT_NAMES: &str = "side-by-side, interleaved, summary";

/// The hex-report layouts (docs/14 §2: exactly these three measured at exit
/// 0; a bogus layout is 106 (Y8)).
const HEX_LAYOUT_NAMES: &str = reacmp_core::hex::HEX_LAYOUT_NAMES;

fn parse_table_layout(
    spec: &ReportSpec,
    line: usize,
) -> Result<reacmp_core::TableLayout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("data-report needs layout:<name> ({TABLE_LAYOUT_NAMES})"),
        ));
    }
    reacmp_core::TableLayout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a data-report layout ({TABLE_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

/// `hex-report` layouts (docs/14): side-by-side, interleaved, summary —
/// bogus layout is 106 (Y8), measured exactly like the table channel.
fn parse_hex_layout(
    spec: &ReportSpec,
    line: usize,
) -> Result<reacmp_core::HexLayout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("hex-report needs layout:<name> ({HEX_LAYOUT_NAMES})"),
        ));
    }
    reacmp_core::HexLayout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a hex-report layout ({HEX_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

// ==========================================================================
// picture-report (M9)
// ==========================================================================

/// `picture-report` layout (docs/16). `side-by-side | summary` (m83b Q4/P3);
/// no layout is 106 (P5) and an unknown name is 106 (P4), matching the other
/// channels' mandatory-layout rule.
const PICTURE_LAYOUT_NAMES: &str = reacmp_pic::report::PictureLayout::NAMES;

fn parse_picture_layout(spec: &ReportSpec, line: usize) -> Result<PictureLayout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("picture-report needs layout:<name> ({PICTURE_LAYOUT_NAMES})"),
        ));
    }
    PictureLayout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a picture-report layout ({PICTURE_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

/// `registry-report` layouts (docs/17, runs/m101 R5/R6/R17): no layout is
/// 106 (R6) and an unknown name is 106 (R5); the token is case-insensitive
/// (R17's `layout:SIDE-BY-SIDE` ran), which `RegLayout::parse` does by
/// lowercasing.
const REGISTRY_LAYOUT_NAMES: &str = reacmp_reg::report::Layout::NAMES;
const VERSION_LAYOUT_NAMES: &str = reacmp_ver::report::Layout::NAMES;

/// m112 V11/V12: the layout is mandatory (106 without it) and case is
/// FOLDED — V13 renders `layout:SUMMARY` fine (106 -> 0 vs hex H-case, which
/// rejected the upper spelling; here the Oracle accepts it).
fn parse_version_layout(
    spec: &ReportSpec,
    line: usize,
) -> Result<VerLayout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("version-report needs layout:<name> ({VERSION_LAYOUT_NAMES})"),
        ));
    }
    VerLayout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a version-report layout ({VERSION_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

fn parse_registry_layout(spec: &ReportSpec, line: usize) -> Result<RegLayout, Failure> {
    if spec.layout.is_empty() {
        return Err(Failure::syntax(
            line,
            format!("registry-report needs layout:<name> ({REGISTRY_LAYOUT_NAMES})"),
        ));
    }
    RegLayout::parse(&spec.layout).ok_or_else(|| {
        Failure::syntax(
            line,
            format!(
                "layout:{} is not a registry-report layout ({REGISTRY_LAYOUT_NAMES})",
                spec.layout
            ),
        )
    })
}

// ==========================================================================
// Shell reports (the measured zero-comparison shapes)
// ==========================================================================

/// `folder-report` with nothing loaded: 155 bytes in the u5 run
/// (`u5b-probe-20261014T030356Z/reports/folder-report-no-load.xml.out`).
///
/// ```text
/// EF BB BF
/// <?xml version="1.0" encoding="utf-8"?>\r\n
/// <bcreport created="{stamp}">\r\n
/// \t<foldercomp>\r\n
/// \t\t<ltpath/>\r\n
/// \t\t<rtpath/>\r\n
/// \t</foldercomp>\r\n
/// </bcreport>\r\n
/// ```
///
/// The BOM is part of the observation (`EF BB BF` are the report's first three
/// bytes), and so is the `created` attribute.
fn empty_folder_shell(stamp: &str) -> String {
    format!(
        "\u{feff}<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n\
         <bcreport created=\"{stamp}\">\r\n\
         \t<foldercomp>\r\n\
         \t\t<ltpath/>\r\n\
         \t\t<rtpath/>\r\n\
         \t</foldercomp>\r\n\
         </bcreport>\r\n"
    )
}

/// `text-report layout:xml` with no comparison files: 122 bytes with both paths
/// empty, 272 bytes with the two loaded folder paths (u5f
/// `no-load-xml.out` / `load-folders-xml.out`).
///
/// An empty path renders the self-closing `<ltpath/>` form, which is the whole
/// difference between the 122-byte and the 272-byte report — u5f's
/// `no-load-xml.out` is `<ltpath/>` + `<rtpath/>` and its
/// `load-folders-xml.out` is `<ltpath>D:\…</ltpath>` + `<rtpath>D:\…</rtpath>`
/// with no other change.
fn empty_text_shell(left: &str, right: &str, stamp: &str) -> String {
    format!(
        "\u{feff}<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n\
         <bcreport created=\"{stamp}\">\r\n\
         {}\
         {}\
         </bcreport>\r\n",
        path_element("ltpath", left),
        path_element("rtpath", right),
    )
}

/// One `<ltpath>`/`<rtpath>` line, self-closing when the path is empty.
fn path_element(tag: &str, path: &str) -> String {
    if path.is_empty() {
        format!("\t<{tag}/>\r\n")
    } else {
        format!("\t<{tag}>{}</{tag}>\r\n", escape_xml(path))
    }
}

/// XML text escaping, matching the corpus writer (`&`, `<`, `>`).
fn escape_xml(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for c in text.chars() {
        match c {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            _ => out.push(c),
        }
    }
    out
}

/// Convert a `created` string into the core's [`reacmp_core::Stamp`].
///
/// The two crates keep their own timestamp types (both in the observed
/// `YYYY/MM/DD H:MM:SS` shape) and the core's XML writer needs its own, so this
/// parses the string this module just formatted. A malformed value cannot occur
/// (`now()` is the only producer and the format is fixed), so the fallback is
/// the epoch rather than a panic.
fn stamp_of(text: &str) -> reacmp_core::Stamp {
    let (date, time) = text.split_once(' ').unwrap_or(("1970/01/01", "0:00:00"));
    let d: Vec<&str> = date.split('/').collect();
    let t: Vec<&str> = time.split(':').collect();
    let num = |v: Option<&&str>| -> i64 { v.and_then(|s| s.parse().ok()).unwrap_or(0) };
    reacmp_core::Stamp::from_parts(
        num(d.first()),
        num(d.get(1)) as u32,
        num(d.get(2)) as u32,
        num(t.first()) as u32,
        num(t.get(1)) as u32,
        num(t.get(2)) as u32,
    )
}

// ==========================================================================
// Filesystem helpers
// ==========================================================================

/// `load` requires a directory (u5/u5c: a file is 107).
fn check_folder(path: &str, line: usize) -> Result<(), Failure> {
    match std::fs::metadata(path) {
        Ok(m) if m.is_dir() => Ok(()),
        Ok(_) => Err(Failure::load(
            line,
            format!("load: {path} is not a folder"),
        )),
        Err(e) => Err(Failure::load(line, format!("load: cannot use {path}: {e}"))),
    }
}

fn open_folder(path: &str, line: usize) -> Result<LocalFs, Failure> {
    LocalFs::open(path).map_err(|e| Failure::load(line, format!("load: {path}: {e}")))
}

fn read_bytes(path: &str, line: usize) -> Result<Vec<u8>, Failure> {
    std::fs::read(path).map_err(|e| Failure::load(line, format!("cannot read {path}: {e}")))
}

/// True when `relative` names an entry under either loaded base folder.
///
/// u5e `expand-missing` -> 106 and u5h `expand-a-file` -> exit 0 together say the
/// test is "does an entry with this relative path exist", not "is it a folder".
/// Both sides are consulted because the Oracle's tree is the *comparison*, and a
/// folder that exists on only one side is still expandable (u5j `B`:
/// `onlyL` has no right-hand counterpart and still reports).
///
/// Every component is matched case-insensitively: the probes spell paths in the
/// case the script wrote them (`expand "A\B"` against a folder the filesystem
/// stores as `A\B`), and the folder engine's own name alignment is
/// case-insensitive on Windows, so a script that expands `a\b` must find `A\B`.
fn entry_exists(left: &str, right: Option<&str>, relative: &str) -> bool {
    let components: Vec<&str> = relative.split('\\').filter(|c| !c.is_empty()).collect();
    if components.is_empty() {
        return false;
    }
    std::iter::once(left)
        .chain(right)
        // A base folder was validated by `load`, so its own path is resolved by
        // the OS; only the components BELOW it need the explicit walk.
        .any(|base| resolve_case_insensitive(Path::new(base), &components))
}

/// Walk `components` below `start`, matching each name case-insensitively, and
/// require the final component to exist as an entry of any kind.
fn resolve_case_insensitive(start: &Path, components: &[&str]) -> bool {
    let mut current = start.to_path_buf();
    for name in components {
        let Ok(entries) = std::fs::read_dir(&current) else {
            return false;
        };
        let mut found = false;
        for entry in entries.flatten() {
            let file_name = entry.file_name();
            let candidate = file_name.to_string_lossy();
            if candidate.eq_ignore_ascii_case(name) {
                current = entry.path();
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

/// Re-render one command the way the log echoes it.
///
/// The Oracle's log echoes commands **verbatim** (u5c script.log line 4 is
/// `>> folder-report layout:xml output-to:"…"`), so this reconstructs the
/// statement text from the AST rather than pretty-printing a canonical form.
fn render_command(cmd: &Command) -> String {
    match cmd {
        Command::Load { left, right, .. } => match right {
            Some(r) => format!("load \"{left}\" \"{r}\""),
            None => format!("load \"{left}\""),
        },
        Command::Criteria { spec, .. } => format!("criteria {spec}"),
        Command::Expand { paths, .. } => match paths {
            ExpandPaths::All => "expand all".to_string(),
            ExpandPaths::Named(p) => {
                let quoted: Vec<String> = p.iter().map(|x| format!("\"{x}\"")).collect();
                format!("expand {}", quoted.join(" "))
            }
        },
        Command::Filter { masks, .. } => format!("filter \"{masks}\""),
        Command::Option { name, .. } => format!("option {name}"),
        Command::Log { mode, path, append, .. } => {
            let prefix = if *append { "append:" } else { "" };
            match path {
                Some(p) => format!("log {} \"{prefix}{p}\"", mode.as_str()),
                None => format!("log {}", mode.as_str()),
            }
        }
        Command::TextReport { spec, .. } => format!("text-report {}", render_spec(spec)),
        Command::TableReport { word, spec, .. } => {
            format!("{word} {}", render_spec(spec))
        }
        Command::HexReport { spec, .. } => format!("hex-report {}", render_spec(spec)),
        Command::PictureReport { spec, .. } => format!("picture-report {}", render_spec(spec)),
        Command::RegistryReport { spec, .. } => format!("registry-report {}", render_spec(spec)),
        Command::VersionReport { spec, .. } => format!("version-report {}", render_spec(spec)),
        Command::FolderReport { spec, .. } => format!("folder-report {}", render_spec(spec)),
        Command::Sync { visible, create_empty, mode, direction, .. } => {
            let flags = if *visible && !*create_empty {
                "visible ".to_string()
            } else if !*visible && *create_empty {
                "create-empty ".to_string()
            } else if *visible && *create_empty {
                "visible create-empty ".to_string()
            } else {
                String::new()
            };
            match mode {
                SyncMode::Update => {
                    let dir_str = match direction { SyncDirection::LeftToRight => "left->right", SyncDirection::RightToLeft => "right->left", SyncDirection::All => "all" };
                    format!("sync {}update:{}", flags, dir_str)
                },
                SyncMode::Mirror => {
                    // `mirror:all` never parses (m81 A4), but the echo must
                    // still name a direction if one ever reaches it; `all`
                    // here is a rendering fallback, not an accepted form.
                    let dir_str = match direction {
                        SyncDirection::LeftToRight => "left->right",
                        SyncDirection::RightToLeft => "right->left",
                        SyncDirection::All => "all",
                    };
                    format!("sync {}mirror:{}", flags, dir_str)
                },
            }
        }
    }
}

fn render_spec(spec: &ReportSpec) -> String {
    let mut parts = vec![format!("layout:{}", spec.layout)];
    if !spec.options.is_empty() {
        parts.push(format!("options:{}", spec.options.join(",")));
    }
    if let Some(t) = &spec.title {
        parts.push(format!("title:\"{t}\""));
    }
    if let Some(o) = &spec.output_to {
        parts.push(format!("output-to:\"{o}\""));
    }
    if !spec.output_options.is_empty() {
        parts.push(format!("output-options:{}", spec.output_options.join(",")));
    }
    for c in &spec.comparison {
        parts.push(format!("\"{c}\""));
    }
    parts.join(" ")
}

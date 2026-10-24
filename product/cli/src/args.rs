//! Argument parsing for `reacmp`, kept in its own module so it can be tested.
//!
//! See `main.rs` for the contract and `product/docs/09-m4-interfaces.md` §4 for
//! the dispatch rules. The parser is deliberately strict: an argument it does
//! not understand is an error, because silently ignoring one would let a caller
//! believe a mode was applied when it was not.
//!
//! # The accepted shapes
//!
//! ```text
//! reacmp <left> <right> <output> [--opt=<options>] [--layout=<layout>]
//! reacmp [/silent] @<script> [<arg1> [<arg2> [<arg3>]]]
//! reacmp /qc[=<size|crc|binary>] <left> <right>
//! ```
//!
//! The three-path shape is **this product's own form** and the M1 harness
//! contract; it is not a Beyond Compare shape. The script and `/qc` shapes
//! follow BC's command line.
//!
//! BC's *bare* two-file / two-folder / three-file command lines are **not**
//! implemented: measured against `BComp.com` under `/silent` they open an
//! interactive view and never return (`product/verify/probes/U5-FINDINGS.md`
//! §1.3), so there is no behaviour to reproduce and `--help` says so.

use reacmp_core::Layout;

use std::fmt;
use std::path::PathBuf;

/// What the caller asked for: compare two files and write a report.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Request {
    pub left: PathBuf,
    pub right: PathBuf,
    pub output: PathBuf,
    pub options: String,
    pub layout: Layout,
}

/// Run a Beyond Compare script.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScriptRequest {
    /// The script path, with the leading `@` (and any surrounding quotes for the
    /// quoted `@"My Script.txt"` form) removed.
    pub path: PathBuf,
    /// The arguments after the script path. `args[0]` is BC's `%1`, `args[1]` is
    /// `%2`, `args[2]` is `%3`; see `harness/oracle.py`, whose recipes pass
    /// left, right and output in that order.
    pub args: Vec<String>,
}

/// `/qc` — a quick comparison whose only output is the exit code.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuickCompareRequest {
    /// `None` means rules-based (a bare `/qc`). Otherwise one of `size`, `crc`,
    /// `binary`, lower-cased.
    pub kind: Option<String>,
    pub left: PathBuf,
    pub right: PathBuf,
}

/// `--merge3` — the three-way merge data channel (Text Merge GUI feed).
///
/// This is a **LiuCompare-native verb**, not a Beyond Compare command: BC's
/// scripting reference (verified full command list) has NO merge verb, so the
/// only contract here is our own GUI consuming sections JSON. It must never
/// be presented as BC compatibility. Argument order follows BC's OWN merge
/// command line (`BCompare.exe <Left> <Right> <Center>`, verified
/// help/command_line_reference.html), so a user migrating muscle memory gets
/// the same positional order here.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MergeRequest {
    pub left: PathBuf,
    pub right: PathBuf,
    /// The CENTER file = merge base (BC's own convention).
    pub center: PathBuf,
    pub output: PathBuf,
}


/// `--hex3` — the flat byte-slot data channel (Hex Compare GUI feed).
///
/// **LiuCompare-native verb**, same status as `--merge3`: the BC scripting
/// reference has no hex-comparison data verb (the `hex-report` script verb
/// renders the M7 text report, a different contract). This emits the flat
/// alignment slot stream (byte values + matched flag) our Hex Compare view
/// renders; it must never be presented as BC compatibility.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HexRequest {
    pub left: PathBuf,
    pub right: PathBuf,
    pub output: PathBuf,
}


/// `--dir3` — the folder-comparison row data channel (Folder Compare GUI feed).
///
/// **LiuCompare-native verb**, same status as `--merge3`/`--hex3`: the BC
/// scripting reference's `folder-report` renders the M5 text report, a
/// different contract. This emits the FLAT visible row list (engine order,
/// hidden rows skipped) our Folder Compare view renders.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirRequest {
    pub left: PathBuf,
    pub right: PathBuf,
    pub output: PathBuf,
}

/// The parsed command line.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Run {
    Compare(Request),
    Script(ScriptRequest),
    QuickCompare(QuickCompareRequest),
    Merge3(MergeRequest),
    Hex3(HexRequest),
    Dir3(DirRequest),
}

/// A successful parse.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Parsed {
    Help,
    Version,
    Run(Run),
}

/// A parse failure, with the message `main` prints.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Usage(pub String);

impl fmt::Display for Usage {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for Usage {}

/// The `/qc` comparison types BC documents.
///
/// `help/command_line_reference.html`: "/qc=<type> ... can be size, crc, or
/// binary. If a type is not specified, a rules-based comparison will be
/// performed."
const QC_KINDS: &[&str] = &["size", "crc", "binary"];

/// BC script commands, which are **not** command-line arguments.
///
/// BC does not accept these on its command line either: they belong in a
/// `@script` file. Naming them turns "unknown argument" into an answer that
/// tells the caller what to do instead, and `--help` documents the same split.
/// The list is the command table from `help/scripting_reference.html`, not a
/// guess about which ones exist.
const SCRIPT_COMMANDS_NOT_ARGUMENTS: &[&str] = &[
    "attrib", "beep", "collapse", "compare", "copy", "copyto", "criteria",
    "delete", "expand", "file-report", "filter", "folder-report", "hex-report",
    "load", "log", "media-report", "move", "moveto", "option", "picture-report",
    "registry-report", "rename", "select", "snapshot", "sync", "table-report",
    "data-report", "text-report", "touch", "version-report",
];

/// Report types this build does not implement at all (not even inside a
/// script).  `table-report` and `data-report` LEFT this list in M6: the table
/// channel is implemented (docs/13) and only runs inside a @<script>, so both
/// spellings now live in [`SCRIPT_COMMANDS_NOT_ARGUMENTS`] above.
/// `hex-report` LEFT it in M7 (docs/14), `picture-report` in M9 (docs/16),
/// `registry-report` in M11 (docs/17), and `version-report` in M112 (docs/18),
/// each the same move.
///
/// Every one is a **missing feature**, named rather than reported as an unknown
/// argument, which is what `--help` also documents.
const KNOWN_UNSUPPORTED_COMMANDS: &[(&str, &str)] = &[
    ("text-merge", "three-way merge is not implemented in this build"),
    ("file-report", "per-type reports are not implemented in this build"),
    ("media-report", "media comparison is not implemented in this build"),
    // `registry-report` LEFT this list in M11 (docs/17) and `version-report`
    // in M112 (docs/18): both channels are implemented inside @<script>, so
    // they belong to SCRIPT_COMMANDS_NOT_ARGUMENTS instead.
];

/// Parse the argument list (excluding argv[0]).
pub fn parse(argv: &[String]) -> Result<Parsed, Usage> {
    if argv.is_empty() {
        return Err(Usage("missing arguments: expected <left> <right> <output>".into()));
    }

    // Help and version win over everything, including otherwise-bad arguments:
    // a user asking for help must get help.
    for a in argv {
        if a == "--help" || a == "-h" || a == "/?" {
            return Ok(Parsed::Help);
        }
        if a == "--version" || a == "-V" {
            return Ok(Parsed::Version);
        }
    }

    // Flags and switches may appear anywhere (the harness appends them after the
    // paths). `/silent` is recorded only to be *accepted*: this tool never
    // interacts, so there is nothing to silence, and a caller who passes it must
    // not be told the mode failed.
    let mut positional: Vec<&String> = Vec::new();
    let mut options = String::new();
    let mut layout = Layout::Xml;
    let mut qc: Option<Option<String>> = None;
    let mut merge3 = false;
    let mut hex3 = false;
    let mut dir3 = false;

    for a in argv {
        if let Some(payload) = a.strip_prefix("--opt=") {
            if !options.is_empty() {
                options.push(',');
            }
            options.push_str(payload);
        } else if let Some(name) = a.strip_prefix("--layout=") {
            match Layout::parse(name) {
                Some(l) => layout = l,
                None => {
                    return Err(Usage(format!(
                        "unsupported layout {name:?} (supported: {})",
                        Layout::ALL
                            .iter()
                            .map(|l| l.name())
                            .collect::<Vec<_>>()
                            .join(", ")
                    )));
                }
            }
        } else if a == "--merge3" {
            merge3 = true;
        } else if a == "--hex3" {
            hex3 = true;
        } else if a == "--dir3" {
            dir3 = true;
        } else if a.starts_with("--") {
            return Err(Usage(format!("unknown flag {a:?}")));
        } else if is_silent(a) {
            // Accepted and ignored: see above.
        } else if let Some(kind) = qc_switch(a)? {
            qc = Some(kind);
        } else if a.starts_with('/') && !looks_like_windows_path(a) {
            return Err(Usage(format!(
                "unsupported switch {a:?} (see --help for the implemented switches)"
            )));
        } else if a == "-" {
            // `help/command_line_reference.html`: "- Opens stdin in the
            // appropriate view". There is no view here.
            return Err(Usage(
                "reading from stdin is not implemented in this build".into(),
            ));
        } else if is_unsupported_invocation(a) {
            let word = a.split_whitespace().next().unwrap_or(a);
            let (name, why) = KNOWN_UNSUPPORTED_COMMANDS
                .iter()
                .find(|(n, _)| *n == word)
                .copied()
                .unwrap_or(("", ""));
            if name.is_empty() {
                return Err(Usage(format!(
                    "{word}: this is a script command, not a command-line argument \
                     (put it in a @<script> file)"
                )));
            }
            return Err(Usage(format!("{name}: {why}")));
        } else {
            positional.push(a);
        }
    }

    // ---- /qc: two paths, and nothing else --------------------------------
    if let Some(kind) = qc {
        if positional.first().is_some_and(|a| a.starts_with('@')) {
            return Err(Usage(
                "/qc compares two files and cannot be combined with @<script>".into(),
            ));
        }
        if !options.is_empty() || layout != Layout::Xml {
            return Err(Usage(
                "/qc takes no --opt or --layout: it reports only an exit code".into(),
            ));
        }
        if positional.len() != 2 {
            return Err(Usage(format!(
                "/qc expects <left> <right>, got {} argument(s): {}",
                positional.len(),
                positional.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ")
            )));
        }
        return Ok(Parsed::Run(Run::QuickCompare(QuickCompareRequest {
            kind,
            left: PathBuf::from(positional[0]),
            right: PathBuf::from(positional[1]),
        })));
    }

    // ---- @script: the script path plus its arguments ---------------------
    if let Some(first) = positional.first() {
        if let Some(rest) = first.strip_prefix('@') {
            let path = unquote(rest);
            if path.is_empty() {
                return Err(Usage(
                    "missing script path after '@' (expected @<script>)".into(),
                ));
            }
            if !options.is_empty() || layout != Layout::Xml {
                return Err(Usage(
                    "@<script> takes no --opt or --layout: the script names the \
                     layout itself".into(),
                ));
            }
            return Ok(Parsed::Run(Run::Script(ScriptRequest {
                path: PathBuf::from(path),
                args: positional[1..].iter().map(|s| (*s).clone()).collect(),
            })));
        }
    }

    // ---- --merge3: the three-way merge data channel ----------------------
    if merge3 {
        if !options.is_empty() || layout != Layout::Xml {
            return Err(Usage(
                "--merge3 takes no --opt or --layout: it emits sections JSON".into(),
            ));
        }
        if positional.first().is_some_and(|a| a.starts_with('@')) {
            return Err(Usage("--merge3 cannot be combined with @<script>".into()));
        }
        if positional.len() != 4 {
            return Err(Usage(format!(
                "--merge3 expects <left> <right> <center> <output>, got {} argument(s): {}",
                positional.len(),
                positional.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ")
            )));
        }
        return Ok(Parsed::Run(Run::Merge3(MergeRequest {
            left: PathBuf::from(positional[0]),
            right: PathBuf::from(positional[1]),
            center: PathBuf::from(positional[2]),
            output: PathBuf::from(positional[3]),
        })));
    }
    // ---- --hex3: the flat byte-slot data channel --------------------------
    if hex3 {
        if !options.is_empty() || layout != Layout::Xml {
            return Err(Usage(
                "--hex3 takes no --opt or --layout: it emits slot JSON".into(),
            ));
        }
        if positional.first().is_some_and(|a| a.starts_with('@')) {
            return Err(Usage("--hex3 cannot be combined with @<script>".into()));
        }
        if positional.len() != 3 {
            return Err(Usage(format!(
                "--hex3 expects <left> <right> <output>, got {} argument(s): {}",
                positional.len(),
                positional.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ")
            )));
        }
        return Ok(Parsed::Run(Run::Hex3(HexRequest {
            left: PathBuf::from(positional[0]),
            right: PathBuf::from(positional[1]),
            output: PathBuf::from(positional[2]),
        })));
    }
    // ---- --dir3: the folder row data channel ------------------------------
    if dir3 {
        if !options.is_empty() || layout != Layout::Xml {
            return Err(Usage(
                "--dir3 takes no --opt or --layout: it emits row JSON".into(),
            ));
        }
        if positional.first().is_some_and(|a| a.starts_with('@')) {
            return Err(Usage("--dir3 cannot be combined with @<script>".into()));
        }
        if positional.len() != 3 {
            return Err(Usage(format!(
                "--dir3 expects <left-dir> <right-dir> <output>, got {} argument(s): {}",
                positional.len(),
                positional.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ")
            )));
        }
        return Ok(Parsed::Run(Run::Dir3(DirRequest {
            left: PathBuf::from(positional[0]),
            right: PathBuf::from(positional[1]),
            output: PathBuf::from(positional[2]),
        })));
    }

    // ---- the three-path comparison form ----------------------------------
    if positional.len() < 3 {
        return Err(Usage(format!(
            "expected <left> <right> <output>, got {} argument(s): {}",
            positional.len(),
            positional.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ")
        )));
    }
    if positional.len() > 3 {
        return Err(Usage(format!(
            "too many arguments: {} (this tool compares exactly two files; to \
             compare folders or to drive a report from a script, use @<script>)",
            positional
                .iter()
                .map(|s| s.as_str())
                .collect::<Vec<_>>()
                .join(" ")
        )));
    }

    Ok(Parsed::Run(Run::Compare(Request {
        left: PathBuf::from(positional[0]),
        right: PathBuf::from(positional[1]),
        output: PathBuf::from(positional[2]),
        options,
        layout,
    })))
}

/// `/silent`, case-insensitively (Windows switch convention).
fn is_silent(a: &str) -> bool {
    a.eq_ignore_ascii_case("/silent")
}

/// Recognise `/qc` and `/qc=<type>`.
///
/// Returns `Ok(None)` for anything that is not a `/qc` switch so the caller can
/// keep dispatching. An unknown `<type>` is an error: BC accepts only `size`,
/// `crc` and `binary`, and a caller naming anything else must not silently get a
/// rules-based comparison instead.
fn qc_switch(a: &str) -> Result<Option<Option<String>>, Usage> {
    let lower = a.to_ascii_lowercase();
    if lower == "/qc" {
        return Ok(Some(None));
    }
    let Some(kind) = lower.strip_prefix("/qc=") else {
        return Ok(None);
    };
    if QC_KINDS.contains(&kind) {
        Ok(Some(Some(kind.to_string())))
    } else {
        Err(Usage(format!(
            "unsupported /qc type {kind:?} (supported: {}, or no type for a \
             rules-based comparison)",
            QC_KINDS.join(", ")
        )))
    }
}

/// Strip one pair of surrounding double quotes, if present.
///
/// BC writes the quoted form when the path may contain spaces:
/// `@"My Script.txt"`. No unescaping happens — the script language has no
/// documented escape mechanism, so a quote is only ever a grouping character.
fn unquote(s: &str) -> &str {
    let t = s.trim();
    t.strip_prefix('"')
        .and_then(|r| r.strip_suffix('"'))
        .unwrap_or(t)
}

/// A bare BC command name such as `load` or `text-merge`.
fn is_unsupported_invocation(a: &str) -> bool {
    let word = a.split_whitespace().next().unwrap_or("");
    SCRIPT_COMMANDS_NOT_ARGUMENTS.contains(&word)
        || KNOWN_UNSUPPORTED_COMMANDS.iter().any(|(n, _)| *n == word)
}

/// Distinguish `/silent` (a BC switch) from `C:/path/file` and `/tmp/file`.
///
/// A BC switch is a single `/word` with no further separators; a POSIX path has
/// at least one more `/`. Windows paths carry a drive letter or backslashes.
fn looks_like_windows_path(a: &str) -> bool {
    if a.len() >= 3 {
        let bytes: Vec<char> = a.chars().collect();
        if bytes[1] == ':' && (bytes[2] == '\\' || bytes[2] == '/') {
            return true;
        }
    }
    a.contains('\\') || a[1..].contains('/')
}

/// The `--help` text.
///
/// Section 6 of `product/docs/05-acceptance-strategy.md` requires every
/// unsupported capability to be listed here, and section 7 forbids presenting a
/// stub as an implementation. This text is the single place a user learns what
/// is missing, so it must stay accurate.
pub fn help_text() -> String {
    format!(
        "\
reacmp {version} -- ReaCompare text and folder comparison

USAGE
    reacmp <left> <right> <output> [--opt=<options>] [--layout=<layout>]
        Compare two FILES and write the report to <output>. With
        --layout=<name> the named text layout is written, otherwise XML.
        (This three-path form is this tool's own; Beyond Compare has no
        command line that compares two files without opening a view.)

    reacmp [/silent] @<script> [<arg1> [<arg2> [<arg3>]]]
        Run a Beyond Compare script. In the script, %1/%2/%3 refer to the
        arguments after the script path. /silent is accepted and ignored:
        this tool never interacts and never opens a window.

    reacmp /qc[=<size|crc|binary>] <left> <right>
        Quick-compare two files. The only output is the exit code. With no
        =<type> a rules-based comparison is used.

    reacmp --merge3 <left> <right> <center> <output>
    reacmp --hex3 <left> <right> <output>
    reacmp --dir3 <left-dir> <right-dir> <output>
        THREE-WAY MERGE data channel (LiuCompare-native; NOT a Beyond Compare
        command — BC has no merge script verb). <center> is the merge base,
        matching BC's own merge command-line positional order
        (<left> <right> <center>). Writes a JSON document describing the
        merge sections (equal / take-left / take-right / conflict, with line
        ranges per side and the measured section counts) for the Text Merge
        view. This form has no BC report contract.

TEXT LAYOUTS (--layout=<name>)
    xml             (default) Beyond-Compare-compatible XML report
    side-by-side    two columns with a marker per row
    interleaved     line numbers, non-same blocks split left-then-right
    over-under      accepted; renders identically to interleaved (BC deprecated it)
    patch           unified-diff-style report with cursor anchors
    summary         difference counts and section count
    statistics      one CSV row of counts

TEXT OPTIONS (--opt=<name>, repeatable or comma/space separated)
    display-all             every line (the default; no <mode> element)
    display-context         every line, mode 'Differences, With Context'
    display-matches         only matching lines, mode 'Same'
    display-mismatches      only differing lines, mode 'Differences'
    ignore-unimportant      collapse 'similar' to 'same'

    An unknown option name is an error; it is never ignored.

SCRIPT COMMANDS (the implemented subset)
    load \"<left>\" [\"<right>\"]      load two base FOLDERS (or the documented
                                    `load <default>`). A path that is missing,
                                    or a file where a folder is expected,
                                    fails the script (exit 107).
    criteria <spec>                 size / timestamp[:Ns[;IgnoreDST]] / CRC /
                                    binary / rules-based / timezone: / attrib: /
                                    follow-symlinks / ignore-unimportant /
                                    version / owner / group / permissions
    expand all | expand \"<path>\"... expand subfolders; paths are relative to
                                    the base folder, and expand commands
                                    accumulate
    filter \"<masks>\"                name masks: ';' separates, a leading '-'
                                    excludes, a trailing '\\' marks a folder
                                    mask. Filtering changes the rows the
                                    report contains.
    option stop-on-error | confirm:yes-to-all | confirm:no-to-all
    log [none|normal|verbose] [append:]<path>
    text-report   layout:<l> [options:<o>] [title:<t>] output-to:\"<file>\"
                  [\"<left>\" \"<right>\"]
    data-report   layout:<l> [title:<t>] output-to:\"<file>\"
                  [\"<left>\" \"<right>\"]
                  (table/CSV, docs/13; accepted spellings: data-report and
                  table-report.  Layouts: side-by-side, interleaved, summary -
                  there is no xml table layout (106).  The channel refuses
                  every options: value (105) and every output-options: value
                  (106).  `.csv` inputs use the built-in CSV format (fixed
                  comma, quoted cells).  Other extensions auto-detect the
                  delimiter jointly across both files
                  (comma > tab > semicolon > pipe; a delimiter inside a
                  quoted cell is not a candidate), falling back to whole-
                  line cells when none is found.  The space-delimiter split
                  is not modelled (a permanent recorded contradiction -
                  docs/13 §7.4, §8);
                  column-type inference, XLSX/XLS and HTML tables are not
                  implemented.)
    hex-report    layout:<l> [title:<t>] output-to:\"<file>\"
                  [\"<left>\" \"<right>\"]
                  (hex/binary, docs/14; only the hex-report spelling exists.
                  Layouts: side-by-side, interleaved, summary (106 for any
                  other).  Bytes align with the LCS byte diff; the report
                  chunks eight aligned slots per row and breaks blocks at
                  every equal/change transition.  The channel refuses every
                  options: and output-options: value (106, measured - unlike
                  data-report's 105), needs exactly two comparison files
                  (one -> 106, zero -> 107), a missing left file is 106 and
                  a missing right file 107.)
    folder-report layout:<l> [options:<o>] [title:<t>] output-to:\"<file>\"
    version-report layout:<l> [options:<o>] [title:<t>] output-to:\"<file>\"
                  [\"<left>\" \"<right>\"]
                  (PE version resource, docs/18; only the version-report
                  spelling exists.  Layouts: side-by-side, summary (106 for
                  any other; case folds - layout:SUMMARY renders).  Options:
                  display-mismatches / display-matches / ignore-unimportant
                  accepted; anything else 106.  output-options: 106.  One
                  comparison file 106, three 106, zero writes the BOM shell
                  (with a Mode line, exit 0).  A missing file on either side
                  107, a directory 107.  The 数据 size field's derivation is
                  an open residual (U-ver-1) - the report is otherwise
                  byte-exact against the archived cells.)

    A '#' at the start of a line is a comment; a trailing '&' continues the
    command on the next line. A script command that is not implemented, and
    any report type listed below, is refused by name (exit 106) - never
    silently ignored and never replaced by a placeholder report.

EXIT STATUS
    0    a script ran and wrote its report (whether or not the inputs differ)
    1    /qc: binary same (byte-identical)
    2    /qc: rules-based same (e.g. only the line ending differs)
    11   /qc: binary differences
    12   /qc: similar (only unimportant differences)
    13   /qc: rules-based differences
    100  /qc: an input could not be read
    105  the @script file could not be read; also the exit a data-report
         produces for any options: value (the table channel has no display
         filtering - measured, docs/13 §4.7)
    106  script syntax or command error
    107  a script input could not be loaded (missing path, or a file where a
         folder was expected)
    104 is Beyond Compare's trial-expired code; this build never produces it.

WHAT THIS BUILD DOES NOT IMPLEMENT
    Any GUI or interactive view. Beyond Compare's bare two-file, two-folder
    and three-file command lines open a view and never return, so there is
    nothing to reproduce and they are refused.
    Beyond Compare's own three-file merge VIEW (its GUI opens and never
    returns). A merge DATA channel does exist here — `--merge3` above — but
    it is LiuCompare-native, not a BC report contract (BC has no merge script
    verb), so it is never presented as BC-compatible output. media and
    per-type (file-report) reports remain unimplemented. (Picture reports ARE implemented inside
    a @<script> — docs/16. Registry reports ARE implemented inside a
    @<script> too — docs/17. Version reports ARE implemented inside a
    @<script> — docs/18.)
    Table space-delimiter split (its acceptance rule is a permanent
    recorded contradiction, docs/13 §7.4 + §8 - such inputs fall back to whole-line
    cells), column-type inference, XLSX/XLS (FlexCel), HTML tables and
    multi-sheet selection are not implemented (docs/13 §4.5, §4.9, §7.4).
    File operations: copy, copyto, move, moveto, delete, rename, sync, touch,
    attrib, and 'load create:all' (which would create directories).
    select, snapshot, beep, compare.
    output-to:printer and output-to:clipboard, and the html output-options.
    Session persistence, archives, and remote (FTP/SFTP/WebDAV) file systems.
    Beyond Compare's other command-line switches.
    Reading from stdin ('-').
    Of Beyond Compare's 25 file-format masks, the 4 with a full importance
    grammar are implemented; the rest fall back to a plain-text comparison.

    Every one of these is reported as an error naming the missing feature. No
    placeholder or hardcoded report is produced for any of them.

IMPORTANCE (same / similar / different)
    Implemented as a per-syntax-element engine for plain text, C/C++, Python
    and JavaScript, chosen by file extension. The rules are the ones measured
    in this workspace (product/verify/probes/U1-FINDINGS.md and
    U2-FINDINGS.md, plus product/docs/07-m2-importance.md); the known
    differences from Beyond Compare are listed in those documents, never
    hidden.
",
        version = reacmp_core::VERSION
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn s(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    fn req(argv: &[&str]) -> Request {
        match parse(&s(argv)).unwrap() {
            Parsed::Run(Run::Compare(r)) => r,
            other => panic!("expected a comparison request, got {other:?}"),
        }
    }

    fn script(argv: &[&str]) -> ScriptRequest {
        match parse(&s(argv)).unwrap() {
            Parsed::Run(Run::Script(r)) => r,
            other => panic!("expected a script request, got {other:?}"),
        }
    }

    fn qc(argv: &[&str]) -> QuickCompareRequest {
        match parse(&s(argv)).unwrap() {
            Parsed::Run(Run::QuickCompare(r)) => r,
            other => panic!("expected a /qc request, got {other:?}"),
        }
    }

    fn hex3(argv: &[&str]) -> HexRequest {
        match parse(&s(argv)).unwrap() {
            Parsed::Run(Run::Hex3(r)) => r,
            other => panic!("expected a --hex3 request, got {other:?}"),
        }
    }

    // ---------------------------------------------------------------
    // --hex3: the Hex Compare GUI data channel (LiuCompare-native verb)
    // ---------------------------------------------------------------

    #[test]
    fn hex3_parses_three_positionals() {
        let r = hex3(&["--hex3", "L.bin", "R.bin", "out.json"]);
        assert_eq!(r.left, PathBuf::from("L.bin"));
        assert_eq!(r.right, PathBuf::from("R.bin"));
        assert_eq!(r.output, PathBuf::from("out.json"));
    }

    #[test]
    fn hex3_rejects_option_flags() {
        // same family as --merge3: the data channel takes no --opt/--layout
        assert!(parse(&s(&["--hex3", "--opt=x", "L", "R", "O"])).is_err());
        assert!(parse(&s(&["--hex3", "--layout=summary", "L", "R", "O"])).is_err());
    }

    #[test]
    fn dir3_parses_three_positionals() {
        let r = match parse(&s(&["--dir3", "L", "R", "out.json"])).unwrap() {
            Parsed::Run(Run::Dir3(r)) => r,
            other => panic!("expected a --dir3 request, got {other:?}"),
        };
        assert_eq!(r.left, PathBuf::from("L"));
        assert_eq!(r.right, PathBuf::from("R"));
        assert_eq!(r.output, PathBuf::from("out.json"));
    }

    #[test]
    fn dir3_rejects_option_flags_and_wrong_arity() {
        assert!(parse(&s(&["--dir3", "--opt=x", "L", "R", "O"])).is_err());
        assert!(parse(&s(&["--dir3", "L", "R"])).is_err());
        assert!(parse(&s(&["--dir3", "L", "R", "O", "EXTRA"])).is_err());
    }

    #[test]
    fn hex3_rejects_wrong_arity_and_yields_to_script_shape() {
        // the @<script> shape takes precedence (the merge3 precedent): a
        // leading '@' positional is a script request whatever flags precede
        assert!(matches!(
            parse(&s(&["--hex3", "@script.txt"])).unwrap(),
            Parsed::Run(Run::Script(_))
        ));
        assert!(parse(&s(&["--hex3", "L"])).is_err());
        assert!(parse(&s(&["--hex3", "L", "R"])).is_err());
        assert!(parse(&s(&["--hex3", "L", "R", "O", "EXTRA"])).is_err());
    }

    // ---------------------------------------------------------------
    // The harness contract (M1) -- must not regress
    // ---------------------------------------------------------------

    #[test]
    fn harness_argv_shape_parses() {
        // candidate.py: argv ["{path}", "{left}", "{right}", "{output}"]
        let r = req(&["D:\\L.txt", "D:\\R.txt", "D:\\out.xml"]);
        assert_eq!(r.left, PathBuf::from("D:\\L.txt"));
        assert_eq!(r.right, PathBuf::from("D:\\R.txt"));
        assert_eq!(r.output, PathBuf::from("D:\\out.xml"));
        assert_eq!(r.layout, Layout::Xml, "no --layout means XML");
        assert_eq!(r.options, "");
    }

    #[test]
    fn harness_option_and_layout_flags_parse() {
        // candidate.py appends "--opt={options}" and "--layout={layout}".
        let r = req(&["L", "R", "O", "--opt=display-mismatches", "--layout=patch"]);
        assert_eq!(r.options, "display-mismatches");
        assert_eq!(r.layout, Layout::Patch);
    }

    #[test]
    fn flags_may_precede_the_paths() {
        let r = req(&["--layout=summary", "--opt=display-all", "L", "R", "O"]);
        assert_eq!(r.layout, Layout::Summary);
        assert_eq!(r.options, "display-all");
    }

    #[test]
    fn every_supported_layout_name_is_accepted() {
        for layout in Layout::ALL {
            let r = req(&["L", "R", "O", &format!("--layout={}", layout.name())]);
            assert_eq!(r.layout, layout, "{}", layout.name());
        }
    }

    #[test]
    fn repeated_option_flags_accumulate() {
        let r = req(&["L", "R", "O", "--opt=display-context", "--opt=ignore-unimportant"]);
        assert_eq!(r.options, "display-context,ignore-unimportant");
    }

    #[test]
    fn an_empty_options_payload_is_accepted() {
        // The adapter passes "--opt=" when the anchor has no options.
        let r = req(&["L", "R", "O", "--opt="]);
        assert_eq!(r.options, "");
    }

    // ---------------------------------------------------------------
    // Help and version
    // ---------------------------------------------------------------

    #[test]
    fn help_and_version_short_circuit() {
        for flag in ["--help", "-h", "/?"] {
            assert_eq!(parse(&s(&[flag])).unwrap(), Parsed::Help, "{flag}");
            // Even alongside nonsense arguments.
            assert_eq!(parse(&s(&[flag, "junk", "--nope"])).unwrap(), Parsed::Help, "{flag}");
        }
        for flag in ["--version", "-V"] {
            assert_eq!(parse(&s(&[flag])).unwrap(), Parsed::Version, "{flag}");
        }
    }

    #[test]
    fn help_lists_every_unsupported_capability() {
        let help = help_text();
        // `picture` LEFT this list in M9 (docs/16): picture reports are now
        // implemented inside @<script>, so they must NOT appear as an
        // unsupported capability. `registry` LEFT it in M11 (docs/17) the
        // same way.
        for required in [
            "GUI",
            "merge",
            "table",
            "media",
            "version",
            "file-report",
            "copy",
            "move",
            "delete",
            "rename",
            "sync",
            "touch",
            "attrib",
            "create:all",
            "select",
            "snapshot",
            "beep",
            "printer",
            "clipboard",
            "html",
            "Session persistence",
            "archives",
            "remote",
            "stdin",
            "switches",
        ] {
            assert!(
                help.to_lowercase().contains(&required.to_lowercase()),
                "--help must name the unsupported capability {required:?}"
            );
        }
    }

    #[test]
    fn help_is_honest_about_importance_coverage() {
        // M2 replaced the earlier spec-level approximation, so the old
        // "SPEC-LEVEL APPROXIMATION / NOT Beyond Compare" warning must be gone
        // and the remaining coverage limit (format fallback) must be stated.
        let help = help_text();
        assert!(!help.contains("SPEC-LEVEL"), "stale M1 warning still present");
        assert!(help.contains("fall back"), "the format fallback must be stated");
        assert!(help.contains("known\ndifferences") || help.contains("known differences")
                || help.contains("known\n    differences"),
                "the known differences must be pointed at");
        assert!(help.contains("2-FINDINGS") || help.contains("U2-FINDINGS"));
    }

    #[test]
    fn help_documents_the_new_shapes_and_their_exit_codes() {
        let help = help_text();
        for required in [
            "@<script>", "/qc", "/silent", "105", "106", "107", "100",
            "load", "criteria", "expand", "filter", "log",
            "text-report", "folder-report",
        ] {
            assert!(help.contains(required), "help omits {required}");
        }
    }

    #[test]
    fn help_documents_every_layout_and_option_the_parser_accepts() {
        let help = help_text();
        for layout in Layout::ALL {
            assert!(help.contains(layout.name()), "help omits layout {}", layout.name());
        }
        for option in [
            "display-all",
            "display-context",
            "display-matches",
            "display-mismatches",
            "ignore-unimportant",
        ] {
            assert!(help.contains(option), "help omits option {option}");
        }
    }

    // ---------------------------------------------------------------
    // Script mode
    // ---------------------------------------------------------------

    #[test]
    fn script_mode_parses_with_and_without_silent() {
        for argv in [
            ["@script.bcs", "L", "R", "O"].as_slice(),
            ["/silent", "@script.bcs", "L", "R", "O"].as_slice(),
            ["@script.bcs"].as_slice(),
        ] {
            let r = script(argv);
            assert_eq!(r.path, PathBuf::from("script.bcs"), "{argv:?}");
        }
        let r = script(&["/silent", "@script.bcs", "L", "R", "O"]);
        assert_eq!(r.args, s(&["L", "R", "O"]), "%1 %2 %3 order");
        assert!(script(&["@script.bcs"]).args.is_empty());
    }

    #[test]
    fn script_path_accepts_the_quoted_form_and_case_insensitive_silent() {
        let r = script(&["@\"My Script.txt\"", "a"]);
        assert_eq!(r.path, PathBuf::from("My Script.txt"));
        assert_eq!(r.args, s(&["a"]));
        for flag in ["/silent", "/SILENT", "/Silent"] {
            assert_eq!(script(&[flag, "@s.bcs"]).path, PathBuf::from("s.bcs"), "{flag}");
        }
    }

    #[test]
    fn a_bare_at_sign_is_refused() {
        let err = parse(&s(&["@"])).unwrap_err();
        assert!(err.0.contains("script path"), "{err}");
    }

    #[test]
    fn script_mode_refuses_the_comparison_form_flags() {
        // The script names its own layout and options; accepting --layout here
        // would let a caller believe it took effect.
        assert!(parse(&s(&["@s.bcs", "--layout=patch"])).is_err());
        assert!(parse(&s(&["@s.bcs", "--opt=display-all"])).is_err());
    }

    #[test]
    fn paths_may_contain_spaces_in_all_modes() {
        let r = req(&[r"D:\a b\L.txt", r"D:\a b\R.txt", r"D:\a b\out.txt"]);
        assert_eq!(r.left.to_string_lossy(), r"D:\a b\L.txt");
        assert_eq!(script(&["@s.bcs", r"D:\a b\L.txt"]).args[0], r"D:\a b\L.txt");
        assert_eq!(qc(&["/qc", r"D:\a b\L.txt", r"D:\a b\R.txt"]).left,
                   PathBuf::from(r"D:\a b\L.txt"));
    }

    // ---------------------------------------------------------------
    // /qc
    // ---------------------------------------------------------------

    #[test]
    fn qc_parses_with_every_documented_type_and_without_one() {
        assert_eq!(qc(&["/qc", "L", "R"]).kind, None, "no type means rules-based");
        for kind in ["size", "crc", "binary"] {
            let r = qc(&["/qc", "L", "R"].iter().map(|s| *s).collect::<Vec<_>>().as_slice());
            let _ = r;
            let got = qc(&[&format!("/qc={kind}"), "L", "R"]);
            assert_eq!(got.kind.as_deref(), Some(kind), "{kind}");
        }
        // The type is case-insensitive and normalised to lower case.
        assert_eq!(qc(&["/qc=CRC", "L", "R"]).kind.as_deref(), Some("crc"));
    }

    #[test]
    fn qc_keeps_the_two_paths() {
        let r = qc(&["/qc=crc", r"D:\L.bin", r"D:\R.bin"]);
        assert_eq!(r.left, PathBuf::from(r"D:\L.bin"));
        assert_eq!(r.right, PathBuf::from(r"D:\R.bin"));
    }

    #[test]
    fn an_unknown_qc_type_is_refused_and_lists_the_valid_ones() {
        let err = parse(&s(&["/qc=quick", "L", "R"])).unwrap_err();
        assert!(err.0.contains("unsupported /qc type"), "{err}");
        assert!(err.0.contains("size"), "{err}");
        assert!(err.0.contains("binary"), "{err}");
        assert!(err.0.contains("rules-based"), "{err}");
    }

    #[test]
    fn qc_requires_exactly_two_paths() {
        assert!(parse(&s(&["/qc", "L"])).is_err());
        assert!(parse(&s(&["/qc", "L", "R", "O"])).is_err());
        let err = parse(&s(&["/qc", "L", "R", "O"])).unwrap_err();
        assert!(err.0.contains("/qc expects"), "{err}");
    }

    #[test]
    fn qc_refuses_layout_and_options() {
        assert!(parse(&s(&["/qc", "L", "R", "--layout=patch"])).is_err());
        assert!(parse(&s(&["/qc", "L", "R", "--opt=display-all"])).is_err());
    }

    #[test]
    fn qc_cannot_be_combined_with_a_script() {
        let err = parse(&s(&["/qc", "@s.bcs", "R"])).unwrap_err();
        assert!(err.0.contains("cannot be combined"), "{err}");
    }

    // ---------------------------------------------------------------
    // Refusals
    // ---------------------------------------------------------------

    #[test]
    fn missing_arguments_are_refused() {
        assert!(parse(&s(&[])).is_err());
        assert!(parse(&s(&["L"])).is_err());
        assert!(parse(&s(&["L", "R"])).is_err());
    }

    #[test]
    fn too_many_paths_are_refused_with_a_script_hint() {
        let err = parse(&s(&["L", "R", "extra", "O"])).unwrap_err();
        assert!(err.0.contains("too many arguments"), "{err}");
        assert!(err.0.contains("@<script>"), "{err}");
    }

    #[test]
    fn unknown_layout_is_refused_and_lists_the_valid_names() {
        let err = parse(&s(&["L", "R", "O", "--layout=html"])).unwrap_err();
        assert!(err.0.contains("unsupported layout"), "{err}");
        assert!(err.0.contains("html"), "{err}");
        assert!(err.0.contains("side-by-side"), "{err}");
    }

    #[test]
    fn unknown_flags_are_refused() {
        assert!(parse(&s(&["L", "R", "O", "--verbose"])).is_err());
        assert!(parse(&s(&["L", "R", "O", "-x"])).is_err());
    }

    #[test]
    fn unimplemented_report_types_are_named_as_unimplemented() {
        // hex-report LEFT this list in M7 (docs/14) and picture-report in M9
        // (docs/16): both channels are implemented, and both verbs are now
        // script commands — see `script_commands_are_not_command_line_arguments`.
        // registry-report LEFT it in M11 (docs/17) and version-report in
        // M112 (docs/18) the same way.
        for (cmd, fragment) in [
            ("text-merge", "merge"),
            ("media-report", "media"),
            ("file-report", "per-type"),
        ] {
            let err = parse(&s(&[cmd, "a", "b"])).unwrap_err();
            assert!(
                err.0.contains(fragment) || err.0.contains("not implemented"),
                "{cmd}: {err}"
            );
            assert!(
                !err.0.contains("unknown flag"),
                "{cmd}: must be named, not unknown"
            );
        }
    }

    #[test]
    fn script_commands_are_not_command_line_arguments() {
        // BC does not accept these on its command line either; naming the
        // problem is more useful than "unknown argument". Folder comparison and
        // scripts ARE implemented -- via @<script>, which is what the message
        // must point at.
        for cmd in [
            "load", "criteria", "filter", "folder-report", "expand",
            "text-report", "table-report", "data-report", "hex-report",
            "picture-report", "registry-report", "version-report",
            "select", "snapshot", "sync", "copy",
        ] {
            let err = parse(&s(&[cmd, "a", "b"])).unwrap_err();
            assert!(err.0.contains("script command"), "{cmd}: {err}");
            assert!(err.0.contains("@<script>"), "{cmd}: {err}");
        }
    }

    #[test]
    fn bc_style_switches_are_refused_but_paths_are_not() {
        let err = parse(&s(&["L", "R", "O", "/verbose"])).unwrap_err();
        assert!(err.0.contains("switch"), "{err}");
        // /silent is the one implemented switch: accepted, and ignored.
        assert!(parse(&s(&["/silent", "@s.bcs"])).is_ok());
        // ...while these are paths, not switches.
        let r = req(&["C:/tmp/L.txt", "C:/tmp/R.txt", "/tmp/out.xml"]);
        assert_eq!(r.left, PathBuf::from("C:/tmp/L.txt"));
        assert_eq!(r.output, PathBuf::from("/tmp/out.xml"));
    }

    #[test]
    fn stdin_is_refused_by_name() {
        let err = parse(&s(&["-", "R", "O"])).unwrap_err();
        assert!(err.0.contains("stdin"), "{err}");
    }

    // ---------------------------------------------------------------
    // Path handling
    // ---------------------------------------------------------------

    #[test]
    fn paths_are_preserved_verbatim_never_canonicalised() {
        // The report echoes these strings, and the harness compares the header
        // paths byte-for-byte, so no normalisation may happen here.
        let r = req(&[
            r"D:\Rea\verify\layouts\mixed-L.txt",
            r"D:\Rea\verify\layouts\mixed-R.txt",
            r"D:\out\mixed-side-by-side.txt",
        ]);
        assert_eq!(r.left.to_string_lossy(), r"D:\Rea\verify\layouts\mixed-L.txt");
        assert_eq!(r.output.to_string_lossy(), r"D:\out\mixed-side-by-side.txt");
    }

    #[test]
    fn windows_path_detection_is_conservative() {
        assert!(looks_like_windows_path(r"D:\x"));
        assert!(looks_like_windows_path("C:/x"));
        assert!(looks_like_windows_path(r"\\server\share"));
        assert!(looks_like_windows_path("/tmp/out.xml"));
        assert!(!looks_like_windows_path("/silent"));
        assert!(!looks_like_windows_path("/qc"));
        assert!(!looks_like_windows_path("/qc=crc"));
        assert!(!looks_like_windows_path("/verbose"));
    }

    #[test]
    fn usage_messages_are_displayable() {
        let err = parse(&s(&["L"])).unwrap_err();
        assert!(err.to_string().contains("expected"));
    }
}

//! The script AST — the frozen interface between parsing (task A) and execution
//! (task B).
//!
//! Every type here is derived from an observation recorded in
//! `product/verify/probes/U5-FINDINGS.md`; the doc comment on each item names
//! the observation it encodes. Do not add speculative fields: a field nothing
//! observed is a field no test can check.

/// One script statement.
///
/// `line` is the **1-based line of the statement's first physical line** in the
/// original script, so a diagnostic can point at the script the user wrote
/// rather than at the joined logical line.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    /// `load "<left>" ["<right>"]` — the two base folders.
    ///
    /// Observed (u5f/u5h): `load` takes **folders**.  A path that does not exist
    /// or names a file makes the script fail with exit 107.
    Load {
        left: String,
        right: Option<String>,
        line: usize,
    },

    /// `criteria <spec>` — the whole argument tail, unparsed.
    ///
    /// Deliberately unparsed here: the token grammar already lives in
    /// `reacmp_dir::Criteria::parse`, and duplicating it would create a second
    /// definition of "valid criteria". An invalid spec is exit 106 (u5c).
    Criteria { spec: String, line: usize },

    /// `expand all` or `expand "<path>" ["<path>" ...]`.
    ///
    /// Observed (u5g/u5h): `A\B`, `A/B` and a trailing separator all name the
    /// same folder; repeated `expand` commands accumulate; a path that does not
    /// exist is exit 106, while a path naming a *file* is harmless.
    Expand { paths: ExpandPaths, line: usize },

    /// `filter "<mask>[;<mask>...]"` — the raw mask text.
    ///
    /// Kept raw because the report echoes it verbatim in `<filters>` (u5i), and
    /// the matcher's rules are task B's concern.
    Filter { masks: String, line: usize },

    /// `option <name>` — `stop-on-error`, `confirm:yes-to-all`, `confirm:no-to-all`.
    ///
    /// Observed (u5e): those three are accepted and change nothing in a
    /// non-interactive run; any other value is exit 106.
    Option { name: String, line: usize },

    /// `log [none|normal|verbose] [append:]<path>`
    Log {
        mode: LogMode,
        path: Option<String>,
        append: bool,
        line: usize,
    },

    /// `text-report ...`
    TextReport { spec: ReportSpec, line: usize },

    /// `folder-report ...`
    FolderReport { spec: ReportSpec, line: usize },

    /// `data-report ...` / `table-report ...` (M6).
    ///
    /// Both spellings are accepted by the Oracle (measured X1 in
    /// runs/m63-clisurface-*: `table-report layout:...` runs and reports
    /// "Table Compare"); `data-report` is the name the scripting help prints
    /// in its TABLE-REPORT Usage line, so the AST keeps one variant and the
    /// command word is carried for the log echo.
    TableReport { word: String, spec: ReportSpec, line: usize },

    /// `hex-report ...` (M7, runs/m70-*: `hex-report layout:<l> output-to:
    /// "%3" "%1" "%2"` runs; WITHOUT a layout the Oracle is 106 — H1 — so the
    /// layout is mandatory here too; no other spelling of the verb is
    /// documented or measured).
    HexReport { spec: ReportSpec, line: usize },

    /// `picture-report ...` (M9, docs/16, runs/m83*): the picture channel.
    /// Parses like the other report verbs (layout mandatory — m83 P5 no-layout
    /// is 106 — and `options:`/`title:`/`output-to:` in any order), but its
    /// refuse surface is its own: 0 files writes the BOM shell (P8/O5), 1 file
    /// or 3+ files is 106 (P9/O6/O9), and a missing file is 107 (P10/O7/O8).
    /// `output-options:` is 106 (P7, same as hex).
    PictureReport { spec: ReportSpec, line: usize },

    /// `registry-report ...` (M11, docs/17, runs/m101*): the registry
    /// channel. Parses like the other report verbs (layout mandatory —
    /// m101 R6 no-layout is 106 — and `options:`/`title:`/`output-to:`/
    /// files), with its own refuse surface: bogus/missing layout, a bogus
    /// option token, `output-options:`, 1 or 3 files = 106 (R5/R6/R10/
    /// R12/R13/N1), a missing file on EITHER side = 107 (R14/R15), and
    /// zero files writes the BOM shell WITH a Mode line (R11/G11).
    RegistryReport { spec: ReportSpec, line: usize },

    /// `version-report ...` (M112, docs/18, runs/m112*): the PE version
    /// channel. Parses like the other report verbs (layout mandatory —
    /// m112 V12 no-layout is 106, V11 bogus is 106 — and `options:`/
    /// `title:`/`output-to:`/files), with its own refuse surface: a bogus
    /// option token is 106 (V17), `output-options:` is 106 (V18), one file
    /// is 106 (V19), three files is 106 (V13b), zero files writes the BOM
    /// shell WITH a Mode line (V21), a missing file on EITHER side is 107
    /// (V9/V10), and a directory argument is 107 (V25).
    VersionReport { spec: ReportSpec, line: usize },

    /// `sync [visible] [create-empty] update|mirror:(left->right|right->left|all)`
    /// — the folder-sync command (M8, `docs/15`; runs/m81*, m82*).
    ///
    /// Unlike every report verb this one has a real filesystem effect — the
    /// Oracle copies and, for `mirror`, deletes destination-side files
    /// (m81-S1/A2). The grammar is frozen to the measured surface:
    /// * the two flags both precede the mode but accept EITHER relative order
    ///   (m81f F3, m81g G5, m81h H1a — all exit 0); a flag after the mode is
    ///   refused (`update:left->right visible`, m81f F2-1 — 106);
    /// * `visible` alongside `create-empty` disables it (m81h H1a/H1b,
    ///   m81g G5: no empty source folder lands in the destination), and it is
    ///   inert otherwise (m82b X2: `visible mirror` still deletes);
    /// * `mirror:all` is a measured 106 (m81 A4) and the direction abbrev
    ///   `lr` is a measured 106 (m81g G7), so only the three long directions
    ///   parse and `mirror` accepts only the two single directions;
    /// * everything malformed is 106 (m81b B8-1..6/8), never a silent no-op.
    ///
    /// The executor refuses a half-load (`load "<L>"` alone) with the measured
    /// exit 100 (m81g G6); with nothing loaded it is a silent no-op exit 0
    /// (m81 A7, m80 S4/S5).
    Sync {
        visible: bool,
        create_empty: bool,
        mode: SyncMode,
        /// `left->right`, `right->left` or `all` — the long form only.
        direction: SyncDirection,
        line: usize,
    },
}

/// `sync`'s mode token (Usage line, `help/scripting_reference.html`, SYNC).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SyncMode {
    /// Copy newer pairs and source-side orphans; never delete, never touch a
    /// tie or a destination-newer pair (m81 A1/A3, m81c C1, m81e E5).
    Update,
    /// Update's copies PLUS copy "different" pairs source->destination and
    /// delete destination-side orphans, recursively — including empty source
    /// folders and non-empty destination folders (m81 A2, m81b B4/B6/B7,
    /// m81c C4, m81f F3, m81h H2a).
    Mirror,
}

/// `sync`'s direction token.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SyncDirection {
    LeftToRight,
    RightToLeft,
    /// Legal for `update` only (m81 A4: `mirror:all` is 106).
    All,
}

/// Which folders `expand` names.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExpandPaths {
    /// `expand all`
    All,
    /// `expand "<p>" ...` — relative paths, in script order.
    Named(Vec<String>),
}

/// `log` verbosity.
///
/// The Oracle's log begins when the mode is changed away from `none`
/// (`help/scripting_reference.html`, LOG).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogMode {
    None,
    Normal,
    Verbose,
}

impl LogMode {
    pub fn parse(word: &str) -> Option<LogMode> {
        match word.to_ascii_lowercase().as_str() {
            "none" => Some(LogMode::None),
            "normal" => Some(LogMode::Normal),
            "verbose" => Some(LogMode::Verbose),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            LogMode::None => "none",
            LogMode::Normal => "normal",
            LogMode::Verbose => "verbose",
        }
    }
}

/// The parsed arguments of a report command.
///
/// Arguments may appear in any order (`help/scripting_reference.html` shows
/// `layout:` first, but the Oracle accepts the documented set in any position).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct ReportSpec {
    /// `layout:<name>` — the one required argument.
    ///
    /// Kept as text so the error for an unknown name can quote what the user
    /// wrote. Validation happens in the executor against the layouts each
    /// report command actually supports (text: 7 names; folder: 3 names).
    pub layout: String,
    /// `options:` payload, split on commas.
    pub options: Vec<String>,
    /// `title:<text>`
    pub title: Option<String>,
    /// `output-to:<target>` — a filename, or the words `printer`/`clipboard`
    /// which this build refuses by name (see 09 §5).
    pub output_to: Option<String>,
    /// `output-options:` payload, split on commas.
    pub output_options: Vec<String>,
    /// Bare arguments after the named ones: `"<left>" ["<right>"]`.
    ///
    /// Observed (u5f): for `text-report` these are the files to compare, and
    /// they override the loaded folders; zero of them means "use the loaded
    /// state", which produces the path-only report shape.
    pub comparison: Vec<String>,
}

/// A syntax error, with the script line that caused it.
///
/// Maps to exit 106, **except** an unterminated quote, which the Oracle treats
/// as an input-loading failure (107) — see `U5-FINDINGS.md` §1.1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScriptError {
    pub line: usize,
    pub message: String,
    /// The exit code this error must produce.  `105`/`106`/`107` only; the
    /// parser sets 107 for an unterminated quote and 106 for everything else.
    pub exit_code: i32,
}

impl ScriptError {
    pub fn syntax(line: usize, message: impl Into<String>) -> Self {
        ScriptError { line, message: message.into(), exit_code: 106 }
    }

    pub fn load(line: usize, message: impl Into<String>) -> Self {
        ScriptError { line, message: message.into(), exit_code: 107 }
    }
}

impl std::fmt::Display for ScriptError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "line {}: {}", self.line, self.message)
    }
}

impl std::error::Error for ScriptError {}

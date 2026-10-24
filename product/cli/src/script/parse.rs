//! Parser: logical lines -> [`Command`]s.
//!
//! **Owner: task A.**  Implemented for M4; the interface is frozen by
//! `product/docs/09-m4-interfaces.md` §2 and the grammar below is the one
//! `help/scripting_reference.html` documents, restricted to the commands
//! milestone M4 implements.  Every restriction is an explicit refusal, never a
//! silent acceptance — `09-m4-interfaces.md` §5: "每个都必须以命名错误的形式拒绝，
//! 不得静默忽略、不得产出占位报告".
//!
//! # Command words are case-insensitive
//!
//! `LOAD`, `load` and `Load` are the same command.
//!
//! * `help/scripting_reference.html` lists the commands in **uppercase**
//!   (`ATTRIB BEEP COLLAPSE COMPARE …`) while every sample in
//!   `help/sample_scripts.html` and every usage string in the reference itself
//!   is **lowercase** (`load "My Session"`, `text-report layout:…`); a
//!   case-sensitive reading would make the reference's own examples use a
//!   spelling its command table does not contain.
//! * `criteria CRC` is accepted by the Oracle (u5e `crit-before-load`, exit 0)
//!   although the documented spelling in that grammar is `CRC`, and the dir
//!   engine's own `Criteria::parse` is case-insensitive too.
//!
//! **Not directly probed**: the probes always wrote lowercase command words, so
//! uppercase acceptance is inferred from the documents plus the case-insensitive
//! `criteria` token.  Recorded here rather than presented as measured.
//!
//! # `lt` / `rt` are not handled here
//!
//! `help/scripting_reference.html`: "You can use `lt` in place of `left` or `rt`
//! in place of `right` in any of the commands."  Every command with a *side*
//! argument (`copy`, `select`, `snapshot`, `touch`, `delete`, …) is refused by
//! name below, so no implemented command has a side for the alias to name, and
//! there is nothing to translate.
//!
//! # Tokenizer
//!
//! Shared by every command except `criteria` (see [`parse_script`]):
//!
//! * split on runs of whitespace;
//! * a `"` groups text — the quote characters are removed and the spaces inside
//!   are preserved, so `"My Report.txt"` is **one** token `My Report.txt`;
//! * a quote may appear mid-token, and quoting may toggle: `output-to:"a b"` is
//!   one token whose text is `output-to:a b`;
//! * each token remembers whether it *started* with a quote
//!   ([`Token::starts_quoted`]).  A token that starts with a quote is literal
//!   text and is **never** read as a `name:value` argument, which is what keeps
//!   `"%1"` — a Windows path with a drive colon once the executor substitutes it
//!   — a plain value instead of a broken `name:value` pair.
//!
//! There is no escape character (see `lex.rs`: `\"` appears in the official
//! `filter "…;-CVS\"` sample and would break it), so a `"` always toggles.
//!
//! # `%1` / `%2` / `%3` are not substituted here
//!
//! They are replaced at execution time against the command line that invoked
//! the script (`help/scripting_reference.html`, "Command line parameters"; u5
//! passes its inputs as `"%1" "%2"`).  The parser stores them verbatim, so a
//! parser test can assert `%1` reaches the AST unchanged.
//!
//! # Command reference implemented here
//!
//! | command | grammar parsed |
//! |---|---|
//! | [`Command::Load`] | `load "<L>" ["<R>"]`, `load <default>`, and the refusal of `load create:*` |
//! | [`Command::Criteria`] | `criteria <spec>` — the whole tail, verbatim |
//! | [`Command::Expand`] | `expand all` \| `expand "<p>" [<p> …]` |
//! | [`Command::Filter`] | `filter "<masks>"` — one name-mask list, raw |
//! | [`Command::Option`] | `option stop-on-error`, `option confirm:yes-to-all`, `option confirm:no-to-all` |
//! | [`Command::Log`] | `log [none\|normal\|verbose] [[append:]<path>]` |
//! | [`Command::TextReport`] | `text-report layout:… output-to:… [options:…] [title:…] [output-options:…] ["<L>" "<R>"]` |
//! | [`Command::FolderReport`] | the same argument list for `folder-report` |

use super::ast::{Command, ExpandPaths, LogMode, ReportSpec, ScriptError, SyncDirection, SyncMode};
use super::lex::{logical_lines, LogicalLine};

// ==========================================================================
// Command words
// ==========================================================================

/// Beyond Compare script commands that this build refuses **by name**.
///
/// `help/scripting_reference.html` documents these; this build does not
/// implement them (`09-m4-interfaces.md` §5), so a script that uses one gets
/// exit 106 with the command's own name in the message — never a silent no-op
/// and never a placeholder report.  `args.rs`'s `--help` makes the same promise
/// in prose ("Every one of these is reported as an error naming the missing
/// feature").
///
/// Two entries are worth explaining:
///
/// * `select` and `snapshot` are in `09-m4-interfaces.md` §5's list, so they are
///   refused like the destructive commands even though neither destroys
///   anything: a report this build cannot produce from them would be a made-up
///   report.
///   `text-merge` is BC's three-way merge command.
///
/// `data-report` / `table-report` LEFT this list in M6: the table channel is
/// implemented (docs/13), so both spellings parse into
/// [`Command::TableReport`] now.  `hex-report` LEFT it in M7 (docs/14:
/// [`Command::HexReport`]).
const UNIMPLEMENTED_COMMANDS: &[&str] = &[
    "attrib",
    "beep",
    "collapse",
    "compare",
    "copy",
    "copyto",
    "delete",
    "file-report",
    "media-report",
    "move",
    "moveto",
    // `picture-report` LEFT this list in M9 (docs/16): the picture channel is
    // implemented (runs/m83*/m83k–m83o, verified against both installs).
    // `registry-report` LEFT it in M11 (docs/17): the registry channel is
    // implemented (runs/m101*, verified against both installs).
    // `version-report` LEFT it in M112 (docs/18): the version channel is
    // implemented (runs/m112*, verified against the reference install).
    "rename",
    "select",
    "snapshot",
    // `sync` LEFT this list in M8 (docs/15): the folder-sync command is
    // implemented with its measured grammar (runs/m81*, m82*).
    "text-merge",
    "touch",
];

/// The refusal for a documented command this build does not implement.
///
/// Names the command, as the spec requires; "not implemented in this build"
/// distinguishes it from a typo, which is the point of having two messages.
fn unimplemented_command(word: &str, line: usize) -> ScriptError {
    ScriptError::syntax(
        line,
        format!(
            "{word} is a Beyond Compare script command that is not implemented in \
             this build: it is refused by name rather than ignored (see the \
             product's --help for the full list of unimplemented features)"
        ),
    )
}

/// The refusal for a word that is not a BC command at all.
///
/// Exit 106, measured for an unknown command name (u5 §1.1: "未知命令名").
fn unknown_command(word: &str, line: usize) -> ScriptError {
    ScriptError::syntax(
        line,
        format!(
            "unknown command {word:?}; this build implements load, criteria, \
             expand, filter, option, log, text-report and folder-report"
        ),
    )
}

// ==========================================================================
// Tokenizer
// ==========================================================================

/// One whitespace-delimited argument, with its quotes already removed.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Token {
    /// The token with its `"` grouping characters removed.  Spaces inside a
    /// quoted run are preserved, so the text may contain whitespace.
    text: String,
    /// True when the token's **first** character in the script was `"`.
    ///
    /// Such a token is literal text: it is never treated as `name:value`, which
    /// is what makes `"%1"` and `"C:\My Report.txt"` plain values.
    starts_quoted: bool,
}

/// Split one argument tail into [`Token`]s.
///
/// See the module docs for the rules.  A quote that is opened and never closed
/// cannot reach here: `logical_lines` has already rejected an odd number of `"`
/// characters (exit 107).
fn tokenize(text: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let mut chars = text.chars().peekable();
    loop {
        while matches!(chars.peek(), Some(c) if c.is_whitespace()) {
            chars.next();
        }
        if chars.peek().is_none() {
            return tokens;
        }
        let starts_quoted = chars.peek() == Some(&'"');
        let mut piece = String::new();
        let mut in_quotes = false;
        while let Some(&c) = chars.peek() {
            match c {
                '"' => {
                    in_quotes = !in_quotes;
                    chars.next();
                }
                // Whitespace separates tokens only outside quotes.
                c if c.is_whitespace() && !in_quotes => break,
                _ => {
                    piece.push(c);
                    chars.next();
                }
            }
        }
        tokens.push(Token { text: piece, starts_quoted });
    }
}

/// Split `logical` into the command word and the raw (still quoted) tail.
///
/// The tail is what `criteria` captures verbatim; every other command
/// re-tokenizes it.  The command word is the text up to the first whitespace —
/// a script writes it unquoted (`load "L"`), and a quoted or glued command word
/// is not a command this build knows, so it falls out as an unknown command.
fn split_command_head(line: &str) -> (&str, &str) {
    let end = line.find(char::is_whitespace).unwrap_or(line.len());
    (&line[..end], line[end..].trim())
}

/// Strip `keyword` from the front of `text`, ASCII-case-insensitively.
///
/// Uses `str::get` so a non-ASCII prefix cannot panic on a byte index that is
/// not a character boundary.
fn strip_prefix_ci<'a>(text: &'a str, keyword: &str) -> Option<&'a str> {
    match text.get(..keyword.len()) {
        Some(head) if head.eq_ignore_ascii_case(keyword) => text.get(keyword.len()..),
        _ => None,
    }
}

// ==========================================================================
// Entry point
// ==========================================================================

/// Parse a whole script.
///
/// `%1`/`%2`/`%3` are **not** substituted here: the substitution happens at
/// execution time against the command line that invoked the script
/// (`help/scripting_reference.html`, "Command line parameters"; u5 uses the same
/// `"%1" "%2"` form in every recipe).
///
/// # Errors
///
/// The first bad statement stops the parse and is returned; `lex.rs`'s errors
/// (an unterminated quote, exit 107) propagate unchanged, because they are
/// produced while joining the lines this function consumes.  Every other error
/// is exit 106 with the line of the statement's first physical line.
///
/// Parsing the **whole** script before anything runs is what the frozen
/// signature asks for (a `Result` of all commands), so a syntax error on the
/// last line means no earlier command runs.  Whether the Oracle executes
/// earlier lines first is unprobed; this is the interface's meaning, not a
/// measured claim (see the task report).
pub fn parse_script(text: &str) -> Result<Vec<Command>, ScriptError> {
    let mut commands = Vec::new();
    for line in logical_lines(text)? {
        commands.push(parse_line(&line)?);
    }
    Ok(commands)
}

/// Dispatch one logical line on its command word.
fn parse_line(line: &LogicalLine) -> Result<Command, ScriptError> {
    let (word, tail) = split_command_head(&line.text);
    let number = line.line;
    let lower = word.to_ascii_lowercase();
    match lower.as_str() {
        "load" => parse_load(tail, number),
        "criteria" => parse_criteria(tail, number),
        "expand" => parse_expand(tail, number),
        "filter" => parse_filter(tail, number),
        "option" => parse_option(tail, number),
        "log" => parse_log(tail, number),
        "text-report" => parse_report("text-report", &tokenize(tail), number),
        "folder-report" => parse_report("folder-report", &tokenize(tail), number),
        // M6: the Oracle accepts BOTH spellings identically (X1 measured:
        // `table-report layout:...` runs like `data-report` and reports
        // "Table Compare"); `data-report` is the name the scripting help's
        // TABLE-REPORT Usage line prints. Both reach parse_report, which
        // builds a TableReport carrying the word for the log echo.
        "data-report" | "table-report" => parse_report(&lower, &tokenize(tail), number),
        // M7: `hex-report` parses like the other report verbs (runs/m70:
        // layout + output-to + two files; H1 without layout => 106, which
        // parse_report's mandatory-layout check already produces).
        "hex-report" => parse_report(&lower, &tokenize(tail), number),
        // M9: `picture-report` parses the same way (docs/16, runs/m83): layout
        // mandatory (P5 no-layout => 106), options/title/output-to/two files.
        "picture-report" => parse_report(&lower, &tokenize(tail), number),
        // M11: `registry-report` parses the same way (docs/17, runs/m101 R5/
        // R6: bogus/missing layout => 106; the grammar carries
        // options/title/output-to/output-options/comparison files).
        "registry-report" => parse_report(&lower, &tokenize(tail), number),
        // M112: `version-report` parses the same way (docs/18, runs/m112
        // V11/V12: bogus/missing layout => 106; the grammar carries
        // options/title/output-to/output-options/comparison files).
        "version-report" => parse_report(&lower, &tokenize(tail), number),
        // M8: `sync` LEFT the refusal list; its measured grammar lives in
        // parse_sync (docs/15, runs/m81* + m82*).
        "sync" => parse_sync(tail, number),
        _ if UNIMPLEMENTED_COMMANDS.contains(&lower.as_str()) => {
            Err(unimplemented_command(&lower, number))
        }
        _ => Err(unknown_command(word, number)),
    }
}

// ==========================================================================
// load
// ==========================================================================

/// `load "<L>" ["<R>"]`, `load <default>`, and the `load create:*` refusal.
///
/// # `load <default>`
///
/// The word `<default>` is stored **exactly as written, angle brackets
/// included**, as [`Command::Load::left`], with no right side.  The executor
/// recognises it (u5g s10: the Oracle accepts it and the report keeps the empty
/// `<ltpath/> <rtpath/>` shell, so it means "a new session with default
/// settings", not a folder called `<default>`) and turns the loaded state back
/// to empty.  The parser must not translate the sentinel into anything else: the
/// angle brackets are the whole signal, and an empty string would instead be a
/// path the executor fails to load (107).
///
/// The parser does not special-case the spelling at all — it passes the token
/// through, and `exec.rs` accepts both `<default>` and a bare `default`
/// (`left.eq_ignore_ascii_case("<default>") || left.eq_ignore_ascii_case("default")`).
///
/// # `load create:*` is refused
///
/// u5g `s11-create-all` measured `load create:all "<L>" "<R>"` **creating** the
/// missing directories on disk.  The frozen AST has no field for the modifier,
/// and silently dropping a destructive modifier would run a *different* script
/// than the user wrote, so the form is refused with a 106 whose message names
/// both the word the script used and `create:all`.  `exec.rs` refuses it too
/// (belt and braces: the executor's check also covers a `create:` produced by
/// `%1` substitution, which the parser never sees).
fn parse_load(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    if let Some(first) = tokens.first() {
        if strip_prefix_ci(&first.text, "create:").is_some() {
            return Err(ScriptError::syntax(
                line,
                format!(
                    "load {} is not implemented: the create: modifier creates \
                     missing folders (create:all is destructive), and this tool is \
                     read-only by design (see the product's --help)",
                    first.text
                ),
            ));
        }
    }
    let left = match tokens.first() {
        Some(t) => t.text.clone(),
        None => {
            return Err(ScriptError::syntax(
                line,
                "load needs one or two folders (or the documented `load <default>`)",
            ))
        }
    };
    let right = match tokens.get(1) {
        Some(t) => Some(t.text.clone()),
        None => None,
    };
    if tokens.len() > 2 {
        return Err(ScriptError::syntax(
            line,
            format!(
                "load takes one or two folders (or `load <default>`), not {} arguments",
                tokens.len()
            ),
        ));
    }
    Ok(Command::Load { left, right, line })
}

// ==========================================================================
// sync (M8)
// ==========================================================================

/// `sync [visible] [create-empty] (update|mirror):(left->right|right->left|all)`
/// — the measured grammar (docs/15, runs/m81* + m82*).
///
/// Measured accept/refuse surface, every cell reproducible:
/// * the two flags may appear **before the mode in either relative order**
///   (m81f F3 `visible mirror:…`, m81g G5 `visible create-empty update:…`,
///   m81h H1a `create-empty visible update:…` — all exit 0), but AFTER the
///   mode is refused (`sync update:left->right visible`, m81f F2-1 — 106).
/// * A flag glued to the mode with a colon is refused: `update visible:…`,
///   `visible:create-empty`, `create-empty:yes` (m81f F2-2/3/4 — 106), as is
///   the `lr` abbreviation (m81g G7) and everything malformed — bare `sync`,
///   unknown mode, mode with no direction, trailing positionals
///   (m81b B8-1..6/8).
/// * `mirror:all` is 106 (m81 A4) while `update:all` is legal (m81 A5,
///   m81e E5).
fn parse_sync(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    let mut idx = 0;
    let mut visible = false;
    let mut create_empty = false;

    // The two flags, either order, both before the mode (measurements above).
    loop {
        match tokens.get(idx).map(|t| t.text.as_str()) {
            Some(w) if w.eq_ignore_ascii_case("visible") && !visible && !create_empty => {
                visible = true;
                idx += 1;
            }
            Some(w) if w.eq_ignore_ascii_case("create-empty") && !visible && !create_empty => {
                create_empty = true;
                idx += 1;
            }
            _ => break,
        }
    }

    // `mode:direction` as ONE token — m81f F2-2/3/4 measured that splitting
    // the pair across spaces (`update visible:…`) or colon-flagging it
    // (`create-empty:yes`) is 106, so a quoted `sync visible …` still needs
    // the mode token at exactly this position.
    let mode_token = match tokens.get(idx) {
        Some(t) => t.text.clone(),
        None => {
            return Err(ScriptError::syntax(
                line,
                "sync needs a mode and direction, e.g. `sync update:left->right` \
                 (visible and create-empty precede it)",
            ))
        }
    };
    if tokens.len() > idx + 1 {
        return Err(ScriptError::syntax(
            line,
            format!(
                "sync takes flags and one `mode:direction`, not {} extra arguments",
                tokens.len() - idx - 1
            ),
        ));
    }

    let (mode_word, direction_word) = match mode_token.split_once(':') {
        Some((m, d)) if !m.is_empty() && !d.is_empty() => (m, d),
        _ => {
            return Err(ScriptError::syntax(
                line,
                format!(
                    "sync argument {mode_token} is not a mode:direction pair \
                     (update|mirror : left->right|right->left|all)"
                ),
            ))
        }
    };

    let mode = match mode_word.to_ascii_lowercase().as_str() {
        "update" => SyncMode::Update,
        "mirror" => SyncMode::Mirror,
        other => {
            return Err(ScriptError::syntax(
                line,
                format!("sync mode {other:?} is not a known mode (update, mirror)"),
            ))
        }
    };
    let direction = match direction_word.to_ascii_lowercase().as_str() {
        "left->right" => SyncDirection::LeftToRight,
        "right->left" => SyncDirection::RightToLeft,
        "all" if mode == SyncMode::Update => SyncDirection::All,
        // m81 A4: `sync mirror:all` is exit 106 — the public SYNC help states
        // `all` is invalid with mirror, and the Oracle refuses it.
        "all" => {
            return Err(ScriptError::syntax(
                line,
                "sync mirror:all is not valid: `all` works with update only",
            ))
        }
        other => {
            return Err(ScriptError::syntax(
                line,
                format!(
                    "sync direction {other:?} is not a known direction \
                     (left->right, right->left, all; abbreviations like `lr` \
                     are refused — m81g G7)"
                ),
            ))
        }
    };

    Ok(Command::Sync { visible, create_empty, mode, direction, line })
}

// ==========================================================================
// criteria
// ==========================================================================

/// `criteria <spec>` — the **entire argument tail, verbatim**.
///
/// # Why the tail is not tokenized
///
/// The criteria grammar already lives in `reacmp_dir::Criteria::parse`
/// (`09-m4-interfaces.md` §2: "不解析 `criteria` 的规格串（交给既有
/// `reacmp_dir::Criteria::parse`）").  Building a second token grammar here would
/// create a second definition of "valid criteria", and the two would drift: the
/// executor would then validate a *re-spelled* spec rather than the user's.
///
/// Nothing is lost by not tokenizing: every documented example —
/// `criteria attrib:sh timestamp:2sec;IgnoreDST rules-based timezone:left+6`
/// (`help/scripting_reference.html`), `criteria timestamp size` and
/// `criteria crc` (`help/sample_scripts.html`) — and every probed recipe
/// (`criteria CRC`, `criteria bogus-token`) writes its tokens unquoted, so the
/// raw text is what the engine's parser wants.  The raw text is handed to the
/// executor as-is; an invalid spec is exit **106**, which u5c `criteria-bogus`
/// measured.
fn parse_criteria(tail: &str, line: usize) -> Result<Command, ScriptError> {
    if tail.is_empty() {
        return Err(ScriptError::syntax(
            line,
            "criteria needs a spec, e.g. `criteria timestamp size`",
        ));
    }
    Ok(Command::Criteria { spec: tail.to_string(), line })
}

// ==========================================================================
// expand
// ==========================================================================

/// `expand all` or `expand "<p>" ["<p>" …]`.
///
/// The two forms are alternatives (`help/scripting_reference.html` EXPAND prints
/// them as separate usages), so `expand all "A"` is a 106.
///
/// An **unquoted** `all` is the keyword; a quoted `"all"` is a folder named
/// `all`.  The distinction is the tokenizer's `starts_quoted` and it is
/// deliberate: the usage's other branch names *paths*, and a folder called `all`
/// is perfectly ordinary, so the quoting is the only thing that says which
/// branch the script meant.  (The keyword test is case-insensitive — `expand ALL`
/// is accepted.  Not probed; every other keyword in this language, including the
/// `LogMode` words, is case-insensitive.)
fn parse_expand(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    if tokens.is_empty() {
        return Err(ScriptError::syntax(
            line,
            "expand needs `all` or at least one path",
        ));
    }
    let mut all = false;
    let mut named = Vec::new();
    for token in &tokens {
        if !token.starts_quoted && token.text.eq_ignore_ascii_case("all") {
            all = true;
        } else {
            named.push(token.text.clone());
        }
    }
    match (all, named.is_empty()) {
        (true, true) => Ok(Command::Expand { paths: ExpandPaths::All, line }),
        (false, _) => Ok(Command::Expand { paths: ExpandPaths::Named(named), line }),
        (true, false) => Err(ScriptError::syntax(
            line,
            "expand all cannot be combined with a named path: the usage documents \
             the two forms as alternatives (`expand all` | `expand \"<path>\" [...]`)",
        )),
    }
}

// ==========================================================================
// filter
// ==========================================================================

/// The documented `filter` forms this build does not implement.
///
/// `help/scripting_reference.html` (FILTER) documents six non-name forms.  None
/// was probed in this workspace, and treating one as a filename mask would
/// produce a report for a *different* filter with no error — which
/// `09-m4-interfaces.md` §5 forbids.  So each is refused by name with 106.
const UNIMPLEMENTED_FILTER_FORMS: &[&str] =
    &["cutoff:", "size:", "attrib:", "unixtype:", "exclude-protected", "include-protected"];

/// `filter "<masks>"` — exactly one name-mask list, stored raw.
///
/// The mask text is **not** interpreted: `;`, a leading `-` and a trailing `\`
/// are task B's matcher's business, and `<filters>` echoes the text verbatim
/// (u5i).  The quotes are removed because they are grouping, not content.
///
/// # The six documented non-name forms are refused
///
/// `filter size:>1MB` silently read as a file mask would drop every row from the
/// report and explain nothing, so each documented non-name form is refused with
/// 106 naming the form.  The test is the whole argument's keyword, which means
/// this layer is the **narrower** of the two: every form refused here is also
/// refused by `exec.rs`, and the executor additionally checks each `;`-separated
/// piece (so `"*.txt;size:>1MB"` passes this function and is caught there).  The
/// split follows the rule that `;` splitting is the matcher's job; the layers
/// cannot disagree in the unsafe direction, because a mask this function refuses
/// never reaches the executor.
///
/// A filename mask cannot plausibly collide with the refused keywords: a colon
/// is not legal in a Windows filename, and the two bare forms are only refused
/// when the script wrote them **unquoted** — a quoted `"exclude-protected"` is
/// left alone here because a file may be called that, and the executor is the
/// layer that decides on the `-`-exclude-mask reading of it.
fn parse_filter(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    if tokens.is_empty() {
        return Err(ScriptError::syntax(line, "filter needs a file mask list"));
    }
    if tokens.len() > 1 {
        return Err(ScriptError::syntax(
            line,
            format!(
                "filter takes exactly one mask list (`filter \"*.txt;-*.log\"`), not {} \
                 arguments",
                tokens.len()
            ),
        ));
    }
    let arg = &tokens[0];
    let probe = arg.text.trim().to_ascii_lowercase();
    // A leading `-` is the exclude marker in a mask list; the executor strips it
    // before its own keyword test, so this one does too.
    let probe = probe.trim_start_matches('-');
    for keyword in UNIMPLEMENTED_FILTER_FORMS {
        let matches = if *keyword == "exclude-protected" || *keyword == "include-protected" {
            !arg.starts_quoted && probe == *keyword
        } else {
            probe.starts_with(keyword)
        };
        if matches {
            return Err(ScriptError::syntax(
                line,
                format!(
                    "filter {} uses the documented `{keyword}` form, which this build \
                     does not implement: only name masks are supported, and accepting \
                     this as a name mask would silently produce a report for a \
                     different filter (see the product's --help)",
                    arg.text
                ),
            ));
        }
    }
    Ok(Command::Filter { masks: arg.text.clone(), line })
}

// ==========================================================================
// option
// ==========================================================================

/// `option stop-on-error` | `option confirm:yes-to-all` | `option confirm:no-to-all`.
///
/// Accepted case-insensitively, and **stored as the script wrote it** (the
/// executor compares case-insensitively and the log echoes the command, so
/// keeping the author's spelling is the more faithful value).
///
/// # `confirm:prompt` is refused
///
/// `help/scripting_reference.html` (OPTION) documents `confirm:prompt` as the
/// default.  This build has no interactive mode at all (`args.rs --help`:
/// "/silent is accepted and ignored: this tool never interacts and never opens a
/// window"), so a prompt policy cannot be honoured and the value is refused by
/// name with an explanation rather than accepted-and-ignored.  Uppercase is not
/// the issue; the *value* is.
///
/// (`exec.rs` would accept `confirm:prompt` as harmless in a non-interactive
/// run; the parser is the gate that refuses it, so the executor's branch is
/// unreachable from a script.  Reported, not changed — `exec.rs` is task B's.)
fn parse_option(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    let name = match tokens.first() {
        Some(t) => t.text.clone(),
        None => {
            return Err(ScriptError::syntax(
                line,
                "option needs a value (stop-on-error, confirm:yes-to-all, confirm:no-to-all)",
            ))
        }
    };
    if tokens.len() > 1 {
        return Err(ScriptError::syntax(
            line,
            format!("option takes exactly one value, not {} arguments", tokens.len()),
        ));
    }
    match name.to_ascii_lowercase().as_str() {
        "stop-on-error" | "confirm:yes-to-all" | "confirm:no-to-all" => {
            Ok(Command::Option { name, line })
        }
        "confirm:prompt" => Err(ScriptError::syntax(
            line,
            "option confirm:prompt is not implemented in this build: this tool is \
             non-interactive and never prompts, so the value would be meaningless \
             (use confirm:yes-to-all or confirm:no-to-all) -- see the product's --help",
        )),
        _ => Err(ScriptError::syntax(
            line,
            format!(
                "option {name:?} is not supported (stop-on-error, confirm:yes-to-all, \
                 confirm:no-to-all)"
            ),
        )),
    }
}

// ==========================================================================
// log
// ==========================================================================

/// `log [none|normal|verbose] [[append:]<path>]`.
///
/// # The default mode is `none`
///
/// With no mode word the mode is [`LogMode::None`].  The frozen AST gives
/// `mode` no "unchanged" spelling, so the parser must choose, and `none` is the
/// only choice that does not invent behaviour:
/// `help/scripting_reference.html` (LOG) says "Logging is initially disabled and
/// begins when the mode is changed from none", so a statement that names no mode
/// cannot turn logging *on*.  Choosing `None` therefore means a mode-less `log`
/// never fabricates a log file the Oracle would not have written.
///
/// The consequence, recorded rather than hidden: a bare `log` issued after
/// `log normal "<path>"` turns logging back off (`exec.rs` treats `None` as
/// "disable").  The alternative — picking `normal` — would make `log "x.txt"`
/// alone start writing a log, which is the behaviour the help text rules out.
///
/// # Which argument is a mode, and quoting
///
/// Only the first argument is ever read as a mode word.  The single-argument
/// form is a mode when it is one of the three words and a path otherwise; the
/// mode-word test does **not** look at quoting, because treating `log "normal"`
/// as a *path* would select the default mode (`none`, see above) and write no
/// file at all — a strictly worse reading of the same text.
///
/// The `append:` prefix, unlike the mode word, is recognised only on a token
/// that does not start with a quote: a quoted `"append:x.txt"` is literal text,
/// so the five characters stay part of the path.  `append:` with nothing after
/// it is a 106 rather than an empty path.
fn parse_log(tail: &str, line: usize) -> Result<Command, ScriptError> {
    let tokens = tokenize(tail);
    if tokens.len() > 2 {
        return Err(ScriptError::syntax(
            line,
            format!(
                "log takes at most a mode and a path (`log [none|normal|verbose] \
                 [[append:]<path>]`), not {} arguments",
                tokens.len()
            ),
        ));
    }
    let (mode, path_token) = match tokens.len() {
        0 => return Ok(Command::Log { mode: LogMode::None, path: None, append: false, line }),
        1 => match LogMode::parse(&tokens[0].text) {
            Some(mode) => {
                return Ok(Command::Log { mode, path: None, append: false, line });
            }
            None => (LogMode::None, &tokens[0]),
        },
        _ => match LogMode::parse(&tokens[0].text) {
            Some(mode) => (mode, &tokens[1]),
            None => {
                return Err(ScriptError::syntax(
                    line,
                    format!(
                        "log: {:?} is not a log mode (none, normal, verbose)",
                        tokens[0].text
                    ),
                ))
            }
        },
    };
    let (path, append) = match strip_prefix_ci(&path_token.text, "append:") {
        Some(rest) if !path_token.starts_quoted => {
            if rest.is_empty() {
                return Err(ScriptError::syntax(
                    line,
                    "log append: needs a filename after the prefix",
                ));
            }
            (rest.to_string(), true)
        }
        _ => (path_token.text.clone(), false),
    };
    Ok(Command::Log { mode, path: Some(path), append, line })
}

// ==========================================================================
// text-report / folder-report
// ==========================================================================

/// The report argument names, recognised only on a token that was not quoted.
///
/// `help/scripting_reference.html`, "Common report arguments", is the list.
const REPORT_ARGUMENTS: &[&str] =
    &["layout:", "options:", "title:", "output-to:", "output-options:"];

/// Split a comma-separated payload, dropping empty segments.
///
/// `options:column-size,column-timestamp` and `output-options:print-color,wrap-word`
/// are the documented shapes; `a,,b` and a trailing comma therefore yield
/// `[a, b]` rather than empty names.
fn comma_list(payload: &str) -> Vec<String> {
    payload.split(',').filter(|s| !s.is_empty()).map(|s| s.to_string()).collect()
}

/// Parse a report command's arguments into [`ReportSpec`].
///
/// # Layout is not validated here
///
/// `layout:<name>` is stored as text and not checked against a layout set.  The
/// executor validates it against the names each command actually supports
/// (`text-report`: 7, `folder-report`: 3 — `exec.rs`'s
/// `TEXT_LAYOUT_NAMES`/`FOLDER_LAYOUT_NAMES`).  The split is deliberate: those
/// sets live in exactly one place, next to the renderer that honours them, and
/// the error the user sees can quote what they wrote.  A bad name is exit 106
/// either way (u5 `bad-option-value`, `layout:not-a-layout`).
///
/// # `layout:` and `output-to:` are required
///
/// Both are syntax errors when absent, even though `ReportSpec::output_to` is an
/// `Option` (the AST keeps the `Option` for the executor's use; the parser
/// always fills it).
///
/// Evidence: u5 `missing-required-arg` measured `text-report layout:xml` — a
/// layout *present*, `output-to:` absent — exiting **106** with a 0-byte report
/// (`report_bytes: 0`, `report_exists: false` in
/// `runs/u5-probe-20261014T030001Z/u5-results.json`), while the same command
/// **with** `output-to:` exits 0 and writes a report.  So the 106 is
/// attributable to the missing output target, not to anything else in the line.
/// `help/scripting_reference.html` agrees in prose: the report commands "must
/// include information on where the report should be sent".
///
/// # Repeated arguments: last one wins
///
/// Not probed.  Repeating an argument is a script author's bug either way, and
/// "the last mention is the one in force" matches how the Oracle's state-machine
/// commands behave (`load`, `criteria`), so a later `layout:` overrides an
/// earlier one rather than making the parse fail.
///
/// # Bare words become the comparison
///
/// A token that is not one of [`REPORT_ARGUMENTS`] — quoted or not — is a
/// "comparison" entry: a session name or a filename (`help/scripting_reference.html`,
/// "Common report arguments": `<comparison>` "can either be a session name or a
/// pair of filenames").  They keep script order and more than two is a 106.
///
/// Note that `folder-report`'s documented usage has **no** `[<comparison>]`
/// argument while its sibling reports do; the frozen AST shares one `ReportSpec`
/// type, the spec for this task collects bare words for both commands, and the
/// executor ignores `comparison` for a folder report.  Implemented as specified;
/// recorded here as the one place a folder-report argument can be dropped
/// without a diagnostic.
fn parse_report(
    name: &str,
    tokens: &[Token],
    line: usize,
) -> Result<Command, ScriptError> {
    if tokens.is_empty() {
        return Err(ScriptError::syntax(
            line,
            format!("{name} needs layout:<name> and output-to:\"<path>\""),
        ));
    }
    let mut spec = ReportSpec::default();
    for token in tokens {
        // A quoted token is literal text and is never an argument (the tokenizer
        // contract); it falls through to the comparison list below.
        if !token.starts_quoted {
            if let Some((key, value)) = token.text.split_once(':') {
                match key.to_ascii_lowercase().as_str() {
                    "layout" => {
                        if value.is_empty() {
                            return Err(ScriptError::syntax(
                                line,
                                format!("{name} layout: needs a layout name"),
                            ));
                        }
                        spec.layout = value.to_string();
                        continue;
                    }
                    "options" => {
                        spec.options = comma_list(value);
                        continue;
                    }
                    "title" => {
                        // An empty title is legal: it is a text field, and
                        // `title:""` is the documented way to write no title.
                        spec.title = Some(value.to_string());
                        continue;
                    }
                    "output-to" => {
                        if value.is_empty() {
                            return Err(ScriptError::syntax(
                                line,
                                format!("{name} output-to: needs a target (a filename)"),
                            ));
                        }
                        // `printer` and `clipboard` parse here: the executor
                        // refuses them by name (09 §5), and that refusal is the
                        // one that can mention the product's --help list.
                        spec.output_to = Some(value.to_string());
                        continue;
                    }
                    "output-options" => {
                        spec.output_options = comma_list(value);
                        continue;
                    }
                    _ => {}
                }
                return Err(ScriptError::syntax(
                    line,
                    format!(
                        "{name}: unknown argument {:?}; the recognised arguments are \
                         {} (a value containing a colon must be quoted, e.g. \
                         output-to:\"C:\\out.txt\")",
                        token.text,
                        REPORT_ARGUMENTS.join(", ")
                    ),
                ));
            }
        }
        spec.comparison.push(token.text.clone());
    }
    if spec.comparison.len() > 2 {
        return Err(ScriptError::syntax(
            line,
            format!(
                "{name} takes at most two comparison files (or one session name), not {}",
                spec.comparison.len()
            ),
        ));
    }
    if spec.layout.is_empty() {
        return Err(ScriptError::syntax(
            line,
            format!("{name} needs layout:<name>"),
        ));
    }
    if spec.output_to.is_none() {
        return Err(ScriptError::syntax(
            line,
            format!("{name} needs output-to:\"<path>\""),
        ));
    }
    Ok(match name {
        "folder-report" => Command::FolderReport { spec, line },
        "data-report" | "table-report" => Command::TableReport {
            word: name.to_string(),
            spec,
            line,
        },
        // M7: the hex channel (docs/14). The Oracle accepts ONLY the
        // `hex-report` spelling — runs/m70 H1/H3/H4 show every alternative
        // verb (`hex-report` without layout, `file-report`, `binary-report`)
        // exit 106. No alias exists, so one variant carries no word.
        "hex-report" => Command::HexReport { spec, line },
        // M9: the picture channel (docs/16, runs/m83 P4/P5). One spelling,
        // like hex.
        "picture-report" => Command::PictureReport { spec, line },
        // M11: the registry channel (docs/17, runs/m101). One spelling.
        "registry-report" => Command::RegistryReport { spec, line },
        // M112: the PE version channel (docs/18, runs/m112). One spelling.
        "version-report" => Command::VersionReport { spec, line },
        _ => Command::TextReport { spec, line },
    })
}

// ==========================================================================
// Tests
// ==========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// Parse a script that must succeed.
    fn cmds(text: &str) -> Vec<Command> {
        parse_script(text).unwrap_or_else(|e| panic!("script must parse, got {e}"))
    }

    /// Parse a script that must produce exactly one command.
    fn one(text: &str) -> Command {
        let mut parsed = cmds(text);
        assert_eq!(parsed.len(), 1, "expected exactly one command, got {parsed:?}");
        parsed.remove(0)
    }

    /// Parse a script that must be refused.
    fn err(text: &str) -> ScriptError {
        match parse_script(text) {
            Ok(c) => panic!("script must be refused, got {c:?}"),
            Err(e) => e,
        }
    }

    /// A `load` command, for comparison.
    fn load(left: &str, right: Option<&str>, line: usize) -> Command {
        Command::Load {
            left: left.to_string(),
            right: right.map(|r| r.to_string()),
            line,
        }
    }

    /// A report spec with the two required arguments filled in.
    fn spec(layout: &str, output_to: &str) -> ReportSpec {
        ReportSpec {
            layout: layout.to_string(),
            output_to: Some(output_to.to_string()),
            ..ReportSpec::default()
        }
    }

    // ==================================================================
    // Command words
    // ==================================================================

    #[test]
    fn every_implemented_command_word_is_case_insensitive() {
        // Lower, upper and title case must produce identical commands.  Not
        // directly probed (the probes wrote lowercase); see the module docs for
        // the documentary evidence.
        let cases = [
            ("load \"L\"", "LOAD \"L\"", "Load \"L\""),
            ("criteria size", "CRITERIA size", "Criteria size"),
            ("expand all", "EXPAND all", "Expand all"),
            ("filter \"*.txt\"", "FILTER \"*.txt\"", "Filter \"*.txt\""),
            ("option stop-on-error", "OPTION stop-on-error", "Option stop-on-error"),
            ("log normal", "LOG normal", "Log normal"),
            (
                "text-report layout:xml output-to:\"o\"",
                "TEXT-REPORT layout:xml output-to:\"o\"",
                "Text-Report layout:xml output-to:\"o\"",
            ),
            (
                "folder-report layout:xml output-to:\"o\"",
                "FOLDER-REPORT layout:xml output-to:\"o\"",
                "Folder-Report layout:xml output-to:\"o\"",
            ),
        ];
        for (lower, upper, title) in cases {
            assert_eq!(one(lower), one(upper), "upper case: {upper}");
            assert_eq!(one(lower), one(title), "title case: {title}");
        }
    }

    #[test]
    fn an_unknown_command_is_106_and_names_the_word() {
        let e = err("frobnicate\n");
        assert_eq!(e.exit_code, 106);
        assert_eq!(e.line, 1);
        assert!(e.message.contains("unknown command"), "{e}");
        assert!(e.message.contains("frobnicate"), "{e}");
    }

    #[test]
    fn every_documented_but_unimplemented_command_is_refused_by_name() {
        for word in UNIMPLEMENTED_COMMANDS {
            let e = err(&format!("{word} whatever\n"));
            assert_eq!(e.exit_code, 106, "{word}");
            assert!(
                e.message.contains(word),
                "{word}: the message must name the command, got {e}"
            );
            assert!(
                e.message.contains("not implemented"),
                "{word}: the message must say it is not implemented, got {e}"
            );
            // Case-insensitive too.
            let upper = err(&format!("{}\n", word.to_ascii_uppercase()));
            assert!(upper.message.contains(word), "{word} upper: {upper}");
        }
    }

    #[test]
    fn the_destructive_commands_are_all_refused() {
        // 09 §5: each is refused by name, never silently accepted.
        for word in ["sync", "copy", "copyto", "move", "moveto", "delete", "rename", "touch", "attrib"] {
            let e = err(&format!("{word} left->right\n"));
            assert_eq!(e.exit_code, 106, "{word}");
            assert!(e.message.contains(word), "{word}: {e}");
        }
    }

    #[test]
    fn select_and_snapshot_are_refused_not_implemented() {
        // Both appear in BC's command table but are outside M4 (09 §5).
        for word in ["select", "snapshot"] {
            let e = err(&format!("{word} all\n"));
            assert_eq!(e.exit_code, 106, "{word}");
            assert!(e.message.contains(word) && e.message.contains("not implemented"), "{e}");
        }
    }

    #[test]
    fn the_literal_compare_two_files_sample_is_refused_because_it_uses_file_report() {
        // help/sample_scripts.html, "Comparing two files by name" writes
        // `file-report`; that command is not implemented, so the literal sample
        // is a 106 naming it (the text-report twin of the sample parses — see
        // `the_official_compare_two_files_sample_parses`).
        let e = err(
            "file-report layout:side-by-side &\n   options:display-mismatches &\n   \
             output-to:\"%3\" \"%1\" \"%2\"\n",
        );
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("file-report"), "{e}");
    }

    // ==================================================================
    // load
    // ==================================================================

    #[test]
    fn load_with_one_folder_has_no_right_side() {
        assert_eq!(one("load \"C:\\L\"\n"), load("C:\\L", None, 1));
    }

    #[test]
    fn load_with_two_folders_keeps_both_in_order() {
        assert_eq!(
            one("load \"C:\\L\" \"C:\\R\"\n"),
            load("C:\\L", Some("C:\\R"), 1)
        );
    }

    #[test]
    fn load_accepts_two_unquoted_arguments() {
        // The official sample writes the ftp side unquoted:
        // `load "C:\My Folder" ftp://user@website.com/folder`.
        assert_eq!(
            one("load \"C:\\My Folder\" ftp://user@website.com/folder\n"),
            load("C:\\My Folder", Some("ftp://user@website.com/folder"), 1)
        );
    }

    #[test]
    fn load_default_sentinel_is_kept_exactly() {
        // The angle brackets are the whole signal; the executor recognises this
        // exact text (exec.rs `do_load`) and means "default settings", so the
        // parser must not strip or re-spell it.
        assert_eq!(one("load <default>\n"), load("<default>", None, 1));
        assert_eq!(one("load \"<default>\"\n"), load("<default>", None, 1));
        assert_eq!(one("LOAD <DEFAULT>\n"), load("<DEFAULT>", None, 1));
    }

    #[test]
    fn load_create_all_is_refused_and_named() {
        let e = err("load create:all \"L\" \"R\"\n");
        assert_eq!(e.exit_code, 106);
        assert_eq!(e.line, 1);
        assert!(e.message.contains("create:all"), "{e}");
        assert!(e.message.contains("not implemented"), "{e}");
        assert!(e.message.contains("read-only"), "{e}");
    }

    #[test]
    fn load_create_left_and_right_are_refused_too() {
        for word in ["create:left", "create:right", "CREATE:ALL"] {
            let e = err(&format!("load {word} \"L\" \"R\"\n"));
            assert_eq!(e.exit_code, 106, "{word}");
            assert!(e.message.contains(word), "{word}: {e}");
            assert!(e.message.contains("create:all"), "{word}: {e}");
        }
    }

    #[test]
    fn load_with_no_arguments_is_106() {
        let e = err("load\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("load"), "{e}");
    }

    #[test]
    fn load_with_three_arguments_is_106() {
        let e = err("load \"L\" \"R\" \"X\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("one or two"), "{e}");
    }

    // ==================================================================
    // criteria
    // ==================================================================

    #[test]
    fn criteria_captures_the_whole_tail_verbatim() {
        // The official example, verbatim from help/scripting_reference.html.
        let spec = "attrib:sh timestamp:2sec;IgnoreDST rules-based timezone:left+6";
        assert_eq!(
            one(&format!("criteria {spec}\n")),
            Command::Criteria { spec: spec.to_string(), line: 1 }
        );
    }

    #[test]
    fn criteria_keeps_extra_whitespace_and_hash_characters() {
        // The tail is trimmed at the ends but never re-spaced or re-tokenized,
        // so what the engine's parser sees is the user's own text.
        assert_eq!(
            one("criteria   timestamp   size\n"),
            Command::Criteria { spec: "timestamp   size".to_string(), line: 1 }
        );
        assert_eq!(
            one("criteria attrib:#1\n"),
            Command::Criteria { spec: "attrib:#1".to_string(), line: 1 }
        );
    }

    #[test]
    fn criteria_case_does_not_change_the_spec() {
        // Only the command word is lowercased; `CRC` reaches the engine as
        // written, and the engine accepts it (u5e `crit-before-load`, exit 0).
        assert_eq!(
            one("CRITERIA CRC\n"),
            Command::Criteria { spec: "CRC".to_string(), line: 1 }
        );
    }

    #[test]
    fn criteria_with_no_argument_is_106() {
        let e = err("criteria\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("criteria"), "{e}");
    }

    // ==================================================================
    // expand
    // ==================================================================

    #[test]
    fn expand_all_is_the_keyword_form() {
        assert_eq!(one("expand all\n"), Command::Expand { paths: ExpandPaths::All, line: 1 });
        assert_eq!(one("expand ALL\n"), Command::Expand { paths: ExpandPaths::All, line: 1 });
    }

    #[test]
    fn expand_quoted_all_is_a_folder_name() {
        assert_eq!(
            one("expand \"all\"\n"),
            Command::Expand { paths: ExpandPaths::Named(vec!["all".into()]), line: 1 }
        );
    }

    #[test]
    fn expand_named_paths_keep_script_order() {
        assert_eq!(
            one("expand \"B\" \"A\\B\" \"C\\\"\n"),
            Command::Expand {
                paths: ExpandPaths::Named(vec!["B".into(), "A\\B".into(), "C\\".into()]),
                line: 1,
            }
        );
    }

    #[test]
    fn expand_accepts_repeated_commands_and_accumulates_nothing_here() {
        // Accumulation is the executor's job (`ExpandPolicy::accumulate`); the
        // parser just yields two commands in order.
        let parsed = cmds("expand \"A\"\nexpand \"A\\B\"\n");
        assert_eq!(parsed.len(), 2);
        assert_eq!(parsed[0], Command::Expand { paths: ExpandPaths::Named(vec!["A".into()]), line: 1 });
        assert_eq!(
            parsed[1],
            Command::Expand { paths: ExpandPaths::Named(vec!["A\\B".into()]), line: 2 }
        );
    }

    #[test]
    fn expand_all_mixed_with_a_path_is_106() {
        let e = err("expand all \"A\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("alternatives"), "{e}");
        let e = err("expand \"A\" all\n");
        assert_eq!(e.exit_code, 106, "order must not matter: {e}");
    }

    #[test]
    fn expand_with_no_argument_is_106() {
        let e = err("expand\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("expand"), "{e}");
    }

    // ==================================================================
    // filter
    // ==================================================================

    #[test]
    fn filter_keeps_the_mask_text_raw_quotes_stripped() {
        assert_eq!(
            one("filter \"*.txt;-*.log\"\n"),
            Command::Filter { masks: "*.txt;-*.log".to_string(), line: 1 }
        );
    }

    #[test]
    fn filter_keeps_a_trailing_backslash_folder_mask() {
        // u5c/u5d: `filter "sub\"` keeps only that folder; the mask text must
        // reach the executor with the backslash intact.
        assert_eq!(
            one("filter \"sub\\\"\n"),
            Command::Filter { masks: "sub\\".to_string(), line: 1 }
        );
        assert_eq!(
            one("filter \"-A\\\"\n"),
            Command::Filter { masks: "-A\\".to_string(), line: 1 }
        );
    }

    #[test]
    fn filter_accepts_an_unquoted_mask_list() {
        assert_eq!(
            one("filter *.txt;-*.log\n"),
            Command::Filter { masks: "*.txt;-*.log".to_string(), line: 1 }
        );
    }

    #[test]
    fn the_documented_non_name_filter_forms_are_refused_by_name() {
        for form in ["cutoff:<7days", "size:>1MB", "attrib:+r", "unixtype:-l"] {
            let e = err(&format!("filter {form}\n"));
            assert_eq!(e.exit_code, 106, "{form}");
            assert!(e.message.contains("not implement"), "{form}: {e}");
            let keyword = form.split(':').next().unwrap();
            assert!(e.message.contains(keyword), "{form}: must name the form, got {e}");
        }
    }

    #[test]
    fn the_two_bare_filter_forms_are_refused_unquoted() {
        for form in ["exclude-protected", "include-protected"] {
            let e = err(&format!("filter {form}\n"));
            assert_eq!(e.exit_code, 106, "{form}");
            assert!(e.message.contains(form), "{form}: {e}");
        }
    }

    #[test]
    fn a_quoted_filter_word_that_is_a_legal_filename_stays_a_mask() {
        // A file may be called `exclude-protected`; only the unquoted keyword
        // form is the documented filter form.
        assert_eq!(
            one("filter \"exclude-protected\"\n"),
            Command::Filter { masks: "exclude-protected".to_string(), line: 1 }
        );
    }

    #[test]
    fn filter_refuses_the_colon_forms_even_when_quoted() {
        // A Windows filename cannot contain `:`, so a quoted `"size:>1MB"` can
        // never be a name mask and must not be accepted as one.
        let e = err("filter \"size:>1MB\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("size:"), "{e}");
    }

    #[test]
    fn an_exclude_mask_of_a_keyword_like_name_is_still_a_name_mask() {
        // `size` (no colon) is an ordinary mask: the refusal keys on the
        // documented keyword vocabulary, not on resemblance.  The same reading is
        // enforced end-to-end by `tests/script_exec.rs`
        // `a_name_mask_that_merely_resembles_a_keyword_is_still_a_name_mask`.
        assert_eq!(
            one("filter \"size\"\n"),
            Command::Filter { masks: "size".to_string(), line: 1 }
        );
        // A QUOTED bare form is left to the executor: this layer refuses only the
        // unquoted keyword, because a file may be called `exclude-protected`.
        // (`exec.rs`'s own per-piece test strips a leading `-` and does refuse
        // this spelling, so the end-to-end outcome is a 106 with the executor's
        // message; the two layers differ only in *which* message, never in
        // whether a mask escapes validation.  `exec.rs` is task B's file, so the
        // difference is recorded here rather than patched there.)
        assert_eq!(
            one("filter \"-exclude-protected\"\n"),
            Command::Filter { masks: "-exclude-protected".to_string(), line: 1 }
        );
    }

    #[test]
    fn filter_with_zero_or_two_arguments_is_106() {
        assert_eq!(err("filter\n").exit_code, 106);
        assert_eq!(err("filter \"a\" \"b\"\n").exit_code, 106);
    }

    // ==================================================================
    // option
    // ==================================================================

    #[test]
    fn the_three_observed_options_are_accepted() {
        // u5e: stop-on-error and the two confirm: values are accepted and change
        // nothing in a non-interactive run.
        for name in ["stop-on-error", "confirm:yes-to-all", "confirm:no-to-all"] {
            assert_eq!(
                one(&format!("option {name}\n")),
                Command::Option { name: name.to_string(), line: 1 }
            );
        }
    }

    #[test]
    fn option_values_are_case_insensitive_and_kept_as_written() {
        assert_eq!(
            one("option STOP-ON-ERROR\n"),
            Command::Option { name: "STOP-ON-ERROR".to_string(), line: 1 }
        );
        assert_eq!(
            one("option Confirm:Yes-To-All\n"),
            Command::Option { name: "Confirm:Yes-To-All".to_string(), line: 1 }
        );
    }

    #[test]
    fn option_confirm_prompt_is_refused_with_the_no_prompt_reason() {
        // Documented by BC, meaningless here: this tool never prompts.
        let e = err("option confirm:prompt\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("confirm:prompt"), "{e}");
        assert!(e.message.contains("prompt"), "{e}");
        assert!(
            e.message.contains("never prompts") || e.message.contains("non-interactive"),
            "{e}"
        );
    }

    #[test]
    fn an_unknown_option_is_106() {
        // u5e `option-bogus` (`option frobnicate`) -> 106.
        let e = err("option frobnicate\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("frobnicate"), "{e}");
    }

    #[test]
    fn option_with_zero_or_two_arguments_is_106() {
        assert_eq!(err("option\n").exit_code, 106);
        assert_eq!(err("option stop-on-error confirm:yes-to-all\n").exit_code, 106);
    }

    // ==================================================================
    // log
    // ==================================================================

    #[test]
    fn a_bare_log_names_no_mode_and_no_path() {
        // Mode-less logging cannot turn logging on (help/LOG), so the mode is
        // `none` rather than a mode the script never asked for.
        assert_eq!(
            one("log\n"),
            Command::Log { mode: LogMode::None, path: None, append: false, line: 1 }
        );
    }

    #[test]
    fn log_mode_alone_has_no_path() {
        for (word, mode) in [
            ("none", LogMode::None),
            ("normal", LogMode::Normal),
            ("verbose", LogMode::Verbose),
            ("VERBOSE", LogMode::Verbose),
        ] {
            assert_eq!(
                one(&format!("log {word}\n")),
                Command::Log { mode, path: None, append: false, line: 1 }
            );
        }
    }

    #[test]
    fn log_mode_and_path() {
        // The official sample: `log normal "C:\My Log.txt"`.
        assert_eq!(
            one("log normal \"C:\\My Log.txt\"\n"),
            Command::Log {
                mode: LogMode::Normal,
                path: Some("C:\\My Log.txt".to_string()),
                append: false,
                line: 1,
            }
        );
    }

    #[test]
    fn log_accepts_the_official_append_form() {
        // `log verbose append:"C:\My Log.txt"` from help/sample_scripts.html.
        assert_eq!(
            one("log verbose append:\"C:\\My Log.txt\"\n"),
            Command::Log {
                mode: LogMode::Verbose,
                path: Some("C:\\My Log.txt".to_string()),
                append: true,
                line: 1,
            }
        );
    }

    #[test]
    fn log_with_only_a_path_uses_the_default_mode() {
        assert_eq!(
            one("log \"C:\\My Log.txt\"\n"),
            Command::Log {
                mode: LogMode::None,
                path: Some("C:\\My Log.txt".to_string()),
                append: false,
                line: 1,
            }
        );
    }

    #[test]
    fn log_append_prefix_without_a_mode_is_still_recognised() {
        assert_eq!(
            one("log append:Log.txt\n"),
            Command::Log {
                mode: LogMode::None,
                path: Some("Log.txt".to_string()),
                append: true,
                line: 1,
            }
        );
    }

    #[test]
    fn a_quoted_append_prefix_is_literal_path_text() {
        // The tokenizer contract: a token that starts with a quote is literal,
        // so the five characters stay part of the filename.
        assert_eq!(
            one("log verbose \"append:x.txt\"\n"),
            Command::Log {
                mode: LogMode::Verbose,
                path: Some("append:x.txt".to_string()),
                append: false,
                line: 1,
            }
        );
    }

    #[test]
    fn log_append_with_an_empty_value_is_106() {
        let e = err("log append:\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("append:"), "{e}");
        assert_eq!(err("log normal append:\n").exit_code, 106);
    }

    #[test]
    fn log_with_a_bad_first_argument_in_the_two_argument_form_is_106() {
        let e = err("log frobnicate \"x.txt\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("frobnicate"), "{e}");
    }

    #[test]
    fn log_with_three_arguments_is_106() {
        assert_eq!(err("log normal append:x.txt extra\n").exit_code, 106);
    }

    // ==================================================================
    // text-report / folder-report
    // ==================================================================

    #[test]
    fn the_official_compare_two_files_sample_parses() {
        // help/sample_scripts.html, "Comparing two files by name"
        // (sample_scripts.html: `file-report layout:side-by-side &
        // options:display-mismatches & output-to:"%3" "%1" "%2"`).
        //
        // The literal sample spells the command `file-report`, which this build
        // refuses by name (see
        // `the_literal_compare_two_files_sample_is_refused_because_it_uses_file_report`);
        // so the sample is parsed with its own sibling command, `text-report`,
        // which the very next section of the same help page uses for the same
        // argument list.  Everything asserted below — exactly one report
        // command, `layout:side-by-side`, two comparison files, the `%N`
        // placeholders — is the sample's structure.
        let parsed = cmds(
            "# Compare two files by name.\n\
             text-report layout:side-by-side &\n   \
             options:display-mismatches &\n   \
             output-to:\"%3\" \"%1\" \"%2\"\n",
        );
        assert_eq!(parsed.len(), 1, "the sample is one continued statement");
        match &parsed[0] {
            Command::TextReport { spec, line } => {
                assert_eq!(*line, 2, "the statement starts on physical line 2");
                assert_eq!(spec.layout, "side-by-side");
                assert_eq!(spec.options, vec!["display-mismatches"]);
                assert_eq!(spec.output_to.as_deref(), Some("%3"));
                assert_eq!(spec.comparison, vec!["%1", "%2"], "two comparison files");
                assert_eq!(spec.comparison.len(), 2);
            }
            other => panic!("expected exactly one TextReport, got {other:?}"),
        }
    }

    #[test]
    fn the_official_generating_a_report_sample_parses_completely() {
        let parsed = cmds(
            "text-report layout:side-by-side &\n   \
             options:ignore-unimportant,display-context &\n   \
             output-to:\"%3\" output-options:html-color \"%1\" \"%2\"\n",
        );
        assert_eq!(parsed.len(), 1);
        match &parsed[0] {
            Command::TextReport { spec, .. } => {
                assert_eq!(spec.layout, "side-by-side");
                assert_eq!(spec.options, vec!["ignore-unimportant", "display-context"]);
                assert_eq!(spec.output_to.as_deref(), Some("%3"));
                assert_eq!(spec.output_options, vec!["html-color"]);
                assert_eq!(spec.comparison, vec!["%1", "%2"]);
            }
            other => panic!("expected a text report, got {other:?}"),
        }
    }

    #[test]
    fn the_official_folder_report_sample_parses() {
        // help/sample_scripts.html, "Performing a rules-based comparison …":
        // `folder-report layout:summary & options:… & output-to:"My Report.txt"`.
        let parsed = cmds(
            "folder-report layout:summary &\n   \
             options:display-mismatches,column-size,column-timestamp,column-attributes &\n   \
             output-to:\"My Report.txt\"\n",
        );
        assert_eq!(parsed.len(), 1);
        match &parsed[0] {
            Command::FolderReport { spec, .. } => {
                assert_eq!(spec.layout, "summary");
                assert_eq!(
                    spec.options,
                    vec!["display-mismatches", "column-size", "column-timestamp", "column-attributes"]
                );
                assert_eq!(spec.output_to.as_deref(), Some("My Report.txt"));
                assert!(spec.comparison.is_empty());
            }
            other => panic!("expected a folder report, got {other:?}"),
        }
    }

    #[test]
    fn report_arguments_may_appear_in_any_order() {
        let forward = spec("xml", "out.xml");
        let mut expected = forward.clone();
        expected.title = Some("Report".to_string());
        expected.options = vec!["display-matches".to_string()];
        let in_order =
            one("text-report layout:xml options:display-matches title:Report output-to:out.xml\n");
        let reversed =
            one("text-report output-to:out.xml title:Report options:display-matches layout:xml\n");
        assert_eq!(in_order, Command::TextReport { spec: expected.clone(), line: 1 });
        assert_eq!(reversed, Command::TextReport { spec: expected, line: 1 });
    }

    #[test]
    fn a_missing_layout_is_106() {
        let e = err("text-report output-to:\"o\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("layout"), "{e}");
        let e = err("folder-report output-to:\"o\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("layout"), "{e}");
    }

    #[test]
    fn a_report_with_no_arguments_at_all_is_106() {
        let e = err("text-report\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("layout"), "{e}");
        assert_eq!(err("folder-report\n").exit_code, 106);
    }

    #[test]
    fn a_missing_output_to_is_106() {
        // u5 `missing-required-arg`: `text-report layout:xml` alone exited 106
        // with a 0-byte report, so the missing output target is the cause.
        let e = err("text-report layout:xml\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("output-to"), "{e}");
        let e = err("folder-report layout:xml\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("output-to"), "{e}");
    }

    #[test]
    fn an_empty_layout_is_106() {
        let e = err("text-report layout: output-to:\"o\"\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("layout"), "{e}");
    }

    #[test]
    fn an_empty_output_to_is_106() {
        let e = err("text-report layout:xml output-to:\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("output-to"), "{e}");
    }

    #[test]
    fn an_empty_title_is_allowed_and_an_empty_options_list_is_empty() {
        let mut expected = spec("xml", "o");
        expected.title = Some(String::new());
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" title:\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
        let expected = spec("xml", "o");
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" options:\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn comma_lists_drop_empty_segments() {
        let mut expected = spec("xml", "o");
        expected.options = vec!["a".to_string(), "b".to_string()];
        expected.output_options = vec!["wrap-word".to_string(), "print-color".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" options:a,,b, output-options:wrap-word,print-color\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn an_unknown_report_argument_is_106_and_names_it() {
        // The message quotes the token as the tokenizer produced it (quotes
        // removed), so the assertion is on the argument's name.
        for (bad, key) in [
            ("layoutx:xml", "layoutx"),
            ("ouput-to:\"o\"", "ouput-to"),
            ("size:10", "size"),
        ] {
            let e = err(&format!("text-report layout:xml output-to:\"o\" {bad}\n"));
            assert_eq!(e.exit_code, 106, "{bad}");
            assert!(e.message.contains("unknown argument"), "{bad}: {e}");
            assert!(e.message.contains(key), "{bad}: the message must name it, got {e}");
        }
    }

    #[test]
    fn bare_comparison_words_collect_in_order_up_to_two() {
        let mut expected = spec("xml", "o");
        assert_eq!(one("text-report layout:xml output-to:\"o\"\n"), Command::TextReport { spec: expected.clone(), line: 1 });
        expected.comparison = vec!["My Session".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" \"My Session\"\n"),
            Command::TextReport { spec: expected.clone(), line: 1 }
        );
        expected.comparison = vec!["L.txt".to_string(), "R.txt".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" L.txt R.txt\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn three_bare_comparison_words_are_106() {
        let e = err("text-report layout:xml output-to:\"o\" a b c\n");
        assert_eq!(e.exit_code, 106);
        assert!(e.message.contains("two"), "{e}");
    }

    #[test]
    fn parameters_are_left_unsubstituted() {
        let mut expected = spec("xml", "%3");
        expected.comparison = vec!["%1".to_string(), "%2".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"%3\" \"%1\" \"%2\"\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn a_quoted_value_with_a_colon_stays_a_comparison_file() {
        // The tokenizer's `starts_quoted`: a quoted Windows path is a value,
        // never a `name:value` argument.
        let mut expected = spec("xml", "o");
        expected.comparison = vec!["C:\\a\\1.txt".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" \"C:\\a\\1.txt\"\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn output_to_printer_parses_and_is_left_to_the_executor() {
        // 09 §5: `printer`/`clipboard` are refused — by the executor, which is
        // where the message can point at the --help list.  The parser must not
        // refuse them, or the two layers would disagree about the diagnosis.
        let mut expected = spec("xml", "printer");
        expected.comparison = vec!["a.txt".to_string(), "b.txt".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:printer a.txt b.txt\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn a_layout_name_is_not_validated_here() {
        // The executor validates against the layouts each command supports and
        // can quote the name; u5 `bad-option-value` measured 106 there.
        let mut expected = spec("not-a-layout", "o");
        expected.comparison = Vec::new();
        assert_eq!(
            one("folder-report layout:not-a-layout output-to:\"o\"\n"),
            Command::FolderReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn a_quoted_multi_word_value_is_one_token() {
        let mut expected = spec("xml", "My Report.txt");
        expected.title = Some("My Report".to_string());
        assert_eq!(
            one("text-report layout:xml title:\"My Report\" output-to:\"My Report.txt\"\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn a_repeated_argument_takes_the_last_value() {
        let expected = spec("summary", "second.xml");
        assert_eq!(
            one("text-report layout:xml layout:summary output-to:first.xml output-to:second.xml\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    #[test]
    fn args_aliases_are_not_needed_for_the_implemented_subset() {
        // `lt`/`rt` name a *side*, and no implemented command takes one, so a
        // bare `lt` here is just a comparison filename.
        let mut expected = spec("xml", "o");
        expected.comparison = vec!["lt".to_string(), "rt".to_string()];
        assert_eq!(
            one("text-report layout:xml output-to:\"o\" lt rt\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }

    // ==================================================================
    // Whole scripts: lines, comments, quotes, errors
    // ==================================================================

    #[test]
    fn an_empty_or_comment_only_script_is_empty() {
        assert!(cmds("").is_empty());
        assert!(cmds("# only a comment\n\n").is_empty());
    }

    #[test]
    fn line_numbers_survive_comments_blank_lines_and_continuations() {
        // Physical lines: 1 comment, 2 blank, 3 load, 4 blank, 5 expand,
        // 6 blank, 7-9 the continued report (with a comment on line 8),
        // 10 blank, 11 filter.
        let parsed = cmds(
            "# header\n\
             \n\
             load \"L\" \"R\"\n\
             \n\
             expand all\n\
             \n\
             text-report layout:xml &\n\
             # a comment inside the continuation\n\
             output-to:\"o\"\n\
             \n\
             filter \"*.txt\"\n",
        );
        assert_eq!(parsed.len(), 4);
        assert_eq!(parsed[0], load("L", Some("R"), 3));
        assert_eq!(parsed[1], Command::Expand { paths: ExpandPaths::All, line: 5 });
        match &parsed[2] {
            Command::TextReport { spec, line } => {
                assert_eq!(*line, 7, "the statement starts on line 7, not 8 or 9");
                assert_eq!(spec.output_to.as_deref(), Some("o"));
            }
            other => panic!("expected a text report, got {other:?}"),
        }
        assert_eq!(parsed[3], Command::Filter { masks: "*.txt".to_string(), line: 11 });
    }

    #[test]
    fn a_realistic_script_parses_into_the_expected_state_machine() {
        let parsed = cmds(
            "# Turn logging on.\n\
             log normal \"C:\\My Log.txt\"\n\
             # Set the comparison criteria.\n\
             criteria timestamp size\n\
             # Load the base folders.\n\
             load \"C:\\My Folder\" \"C:\\Your Folder\"\n\
             expand all\n\
             filter \"*.pas;*.dfm;-archive\\\"\n\
             option confirm:yes-to-all\n\
             folder-report layout:summary &\n   \
             options:display-mismatches &\n   \
             output-to:\"My Report.txt\"\n",
        );
        assert_eq!(parsed.len(), 7);
        assert_eq!(
            parsed[0],
            Command::Log {
                mode: LogMode::Normal,
                path: Some("C:\\My Log.txt".to_string()),
                append: false,
                line: 2,
            }
        );
        assert_eq!(parsed[1], Command::Criteria { spec: "timestamp size".to_string(), line: 4 });
        assert_eq!(parsed[2], load("C:\\My Folder", Some("C:\\Your Folder"), 6));
        assert_eq!(parsed[3], Command::Expand { paths: ExpandPaths::All, line: 7 });
        assert_eq!(parsed[4], Command::Filter { masks: "*.pas;*.dfm;-archive\\".to_string(), line: 8 });
        assert_eq!(
            parsed[5],
            Command::Option { name: "confirm:yes-to-all".to_string(), line: 9 }
        );
        match &parsed[6] {
            Command::FolderReport { spec, line } => {
                assert_eq!(*line, 10);
                assert_eq!(spec.layout, "summary");
                assert_eq!(spec.output_to.as_deref(), Some("My Report.txt"));
            }
            other => panic!("expected a folder report, got {other:?}"),
        }
    }

    #[test]
    fn an_unterminated_quote_is_107_through_parse_script() {
        // The lexer's error class must survive the parser: 107, not 106.
        let e = err("load \"L\n");
        assert_eq!(e.exit_code, 107);
        assert_eq!(e.line, 1);
        let e = err("# comment\nload \"L\" &\n\"R\n");
        assert_eq!(e.exit_code, 107);
        assert_eq!(e.line, 2, "the statement starts on line 2");
    }

    #[test]
    fn the_first_bad_statement_stops_the_parse() {
        let e = err("load \"L\"\nfrobnicate\nexpand all\n");
        assert_eq!(e.exit_code, 106);
        assert_eq!(e.line, 2);
    }

    #[test]
    fn a_statement_with_only_an_ampersand_carries_the_next_line() {
        assert_eq!(cmds("load \"L\" \"R\"\n&\nexpand all\n").len(), 2);
    }

    #[test]
    fn a_mid_token_quote_groups_the_rest_of_the_value() {
        // `output-to:"a b"` — one token, one argument.
        let expected = spec("xml", "a b");
        assert_eq!(
            one("text-report layout:xml output-to:\"a b\"\n"),
            Command::TextReport { spec: expected, line: 1 }
        );
    }
}

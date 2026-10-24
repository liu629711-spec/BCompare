//! Lexer: physical lines -> logical lines.
//!
//! **Owner: task A.**  Implemented for M4; the interface is frozen by
//! `product/docs/09-m4-interfaces.md` §2 and the behaviour below is the measured
//! Oracle behaviour recorded in `product/verify/probes/U5-FINDINGS.md` §2.1.
//!
//! # Rules, and where each one comes from
//!
//! | rule | evidence |
//! |---|---|
//! | a line ending in `&` continues on the next line | `help/sample_scripts.html`: "An ampersand (&) at the end of a line means that the command continues on the next line."  Every multi-line official sample and every recipe in `product/verify/runs/u5*` uses it. |
//! | a line whose first non-whitespace character is `#` is a comment and is dropped | `help/sample_scripts.html`: every sample script is commented with leading `#` lines. |
//! | an unclosed `"` is an **input-loading** failure, exit **107**, not 106 | u5 `unclosed-quote` (`product/verify/runs/u5-probe-20261014T030001Z/u5-results.json`): `text-report layout:xml output-to:"%3 "%1" "%2"` exits **107** with no report.  The intuitive answer, 106, is wrong. |
//! | blank lines produce no statement | a command is one physical line unless continued, so a blank line carries no command. |
//!
//! # Continuation is a *line-level* rule, even inside quotes
//!
//! The official rule is stated at line level ("An ampersand (&) at the end of a
//! line …") with **no quote caveat**, so this lexer never tracks quote state when
//! deciding whether a line continues.  A `&` inside a quoted value therefore
//! still continues the statement, and the pieces are still joined with a single
//! space:
//!
//! ```text
//! text-report layout:xml &
//!    output-to:"C:\My &
//!    Report.txt"
//! ```
//!
//! joins to `text-report layout:xml output-to:"C:\My Report.txt"` — one quoted
//! value, not three.  A quote-aware rule would break the documented multi-line
//! form for anyone whose filename contains `&`, which is legal on Windows, and
//! would make the official samples depend on the `&` never landing inside a
//! value.  What breaks is the *value* (the space the join inserts becomes part
//! of the path) if the split is in the middle of a real path — that is the
//! script author's problem, and the alternative is worse.
//!
//! # Quotes: no escape mechanism
//!
//! Nothing in `help/sample_scripts.html`, `help/scripting_reference.html` or
//! `help/scripting.html` documents a `\"` escape, and the official
//! exclude-a-folder mask proves the opposite is required: the sample
//! `filter "*.htm;*.html;*.php;*.jpg;*.gif;-CVS\"` ends with `\` immediately
//! before the closing quote, and the mask it means is `-CVS\` (trailing
//! backslash = folder mask, `help/scripting_reference.html` FILTER).  If `\`
//! escaped the quote, that sample could not be written at all.  This lexer
//! therefore has no escape handling: **every `"` toggles quoting**, and
//! unterminated-ness is decided by counting the `"` characters of the joined
//! statement (an odd count is unclosed).
//!
//! # Comment placement
//!
//! The comment test is "first non-whitespace character is `#`" on the *physical*
//! line, and it is applied before the continuation test: a comment line is
//! dropped entirely, so it never continues a statement and never terminates one
//! either — a pending continuation simply resumes on the next line.  A `#`
//! anywhere else is literal text (it is not special inside quotes).
//!
//! # Line numbers
//!
//! Each [`LogicalLine`] keeps the 1-based number of its **first** physical line,
//! so a diagnostic can point at the script the user wrote rather than at the
//! joined text.  A statement begins at the first non-comment physical line that
//! belongs to it, even if that line carries no text of its own (a line that is
//! only `&` still starts the statement it continues).

use super::ast::ScriptError;

/// Message for a statement whose `"` characters cannot be paired.
///
/// The exit code is the point: [`ScriptError::load`] makes this **107** (an
/// input-loading failure), which is what the Oracle produces for u5
/// `unclosed-quote` — not the 106 a syntax error would use.  See the module docs.
const UNTERMINATED_QUOTE: &str =
    "unterminated double quote: this statement has an odd number of '\"' characters";

/// One joined script line.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LogicalLine {
    /// The statement text, with continuation joined by a single space and the
    /// leading/trailing whitespace of the pieces trimmed.
    pub text: String,
    /// 1-based line number of the first physical line of the statement.
    pub line: usize,
}

/// Join physical lines into logical ones.
///
/// Returns `Err` only for an unterminated quote, which the Oracle reports as an
/// input-loading failure (exit 107) rather than a syntax error (u5).
///
/// # Algorithm
///
/// 1. Split on `\n`; `\r\n` needs no special case because every line has its
///    trailing whitespace trimmed (which includes the `\r`).
/// 2. Drop a physical line whose first non-whitespace character is `#`.
/// 3. Trim the line's trailing whitespace; if it now ends in `&`, drop the `&`
///    and mark the statement as continuing.
/// 4. Accumulate the trimmed pieces; a line that does **not** continue completes
///    the statement, and the pieces are joined with one space.
/// 5. An empty joined statement produces no [`LogicalLine`] — but it still
///    terminates a pending continuation, because it is a line that does not end
///    in `&`.
/// 6. A statement with an odd number of `"` characters is the 107 error above.
/// 7. A continuation still pending when the input ends simply ends there: no
///    error.  (`&` on the last line is not measured behaviour; ending the
///    statement is the reading that neither invents a command nor loses one.)
pub fn logical_lines(text: &str) -> Result<Vec<LogicalLine>, ScriptError> {
    // A UTF-8 BOM is not `char::is_whitespace`, so it would glue itself to the
    // first command word and turn `load …` into an unknown command.  Nothing in
    // the help files says a script file has a BOM, but the workspace's own
    // evidence shows the Oracle writes BOMs (`exec.rs`: the 122/155-byte shell
    // reports start `EF BB BF`), so a BOM-prefixed script is plausible and is
    // stripped.  Not probed; the alternative is a confusing
    // "unknown command \u{feff}load".
    let text = text.strip_prefix('\u{feff}').unwrap_or(text);

    let mut out = Vec::new();
    let mut pieces: Vec<String> = Vec::new();
    let mut start_line = 0usize;
    let mut in_statement = false;

    for (index, physical) in text.split('\n').enumerate() {
        let number = index + 1;
        let line = physical.trim_end();
        // Comments are dropped before the continuation test, so a comment line
        // neither continues nor terminates a pending statement.
        if line.trim_start().starts_with('#') {
            continue;
        }
        if !in_statement {
            start_line = number;
            in_statement = true;
        }
        let (piece, continues) = match line.strip_suffix('&') {
            Some(rest) => (rest, true),
            None => (line, false),
        };
        let piece = piece.trim();
        if !piece.is_empty() {
            pieces.push(piece.to_string());
        }
        if !continues {
            finish(&mut out, &mut pieces, start_line)?;
            in_statement = false;
        }
    }

    // Rule 7: an unterminated continuation just ends the statement here.
    if in_statement {
        finish(&mut out, &mut pieces, start_line)?;
    }
    Ok(out)
}

/// Complete the statement accumulated in `pieces`.
///
/// Split out so the "a line that does not continue" and "input ran out" cases
/// cannot drift apart: both must apply the same empty-statement and quote-parity
/// rules.
fn finish(
    out: &mut Vec<LogicalLine>,
    pieces: &mut Vec<String>,
    start_line: usize,
) -> Result<(), ScriptError> {
    let joined = pieces.join(" ");
    pieces.clear();
    if joined.is_empty() {
        return Ok(());
    }
    if joined.matches('"').count() % 2 == 1 {
        return Err(ScriptError::load(start_line, UNTERMINATED_QUOTE));
    }
    out.push(LogicalLine { text: joined, line: start_line });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Lex, requiring success.
    fn lex(text: &str) -> Vec<LogicalLine> {
        logical_lines(text).expect("script lexes (no unclosed quote)")
    }

    /// The statement texts only.
    fn texts(text: &str) -> Vec<String> {
        lex(text).into_iter().map(|l| l.text).collect()
    }

    // ==================================================================
    // Continuation
    // ==================================================================

    #[test]
    fn a_trailing_ampersand_joins_the_next_line() {
        assert_eq!(texts("load \"L\" &\n\"R\"\n"), vec!["load \"L\" \"R\""]);
    }

    #[test]
    fn the_official_three_line_report_sample_joins_into_one_line() {
        // help/sample_scripts.html, "Generating a report": the continuation is
        // what lets a report command span lines, and the sample's indentation
        // must not survive into the statement.
        let script = "text-report layout:side-by-side &\n   \
                      options:ignore-unimportant,display-context &\n   \
                      output-to:\"%3\" output-options:html-color \"%1\" \"%2\"\n";
        let lines = lex(script);
        assert_eq!(lines.len(), 1);
        assert_eq!(lines[0].line, 1, "the statement starts on line 1");
        assert_eq!(
            lines[0].text,
            "text-report layout:side-by-side \
             options:ignore-unimportant,display-context \
             output-to:\"%3\" output-options:html-color \"%1\" \"%2\""
        );
    }

    #[test]
    fn every_piece_is_trimmed_before_joining() {
        let lines = lex("  load   \"L\"   &\n\t\t\"R\"\t\n");
        assert_eq!(lines[0].text, "load   \"L\" \"R\"");
    }

    #[test]
    fn continuation_inside_a_quoted_value_joins_with_one_space() {
        // Module rule: the official rule is stated at line level with no quote
        // caveat, so the `&` continues even inside a quoted value and the two
        // pieces become ONE quoted value.
        assert_eq!(
            texts("load \"C:\\My &\n Folder\"\n"),
            vec!["load \"C:\\My Folder\""]
        );
    }

    #[test]
    fn an_ampersand_inside_quotes_leaves_the_quote_count_even() {
        // The consequence of the previous test: the joined statement still has
        // two `"` characters, so it is not the 107 error.
        let lines = lex("load \"A &\nB\"\n");
        assert_eq!(lines.len(), 1);
        assert_eq!(lines[0].text.matches('"').count(), 2);
    }

    #[test]
    fn many_continuations_join_in_order() {
        assert_eq!(
            texts("a &\nb &\nc &\nd\n"),
            vec!["a b c d"],
            "pieces keep their order and are separated by one space"
        );
    }

    #[test]
    fn a_continuation_pending_at_the_end_of_the_input_ends_the_statement() {
        assert_eq!(texts("load \"L\" &"), vec!["load \"L\""]);
    }

    #[test]
    fn a_blank_line_terminates_a_pending_continuation() {
        // A blank line does not end in `&`, so it completes the statement — the
        // literal reading of "when a line does NOT end with `&`, the statement is
        // complete".  The next line is then a statement of its own.
        assert_eq!(
            texts("load \"L\" &\n\n\"R\"\n"),
            vec!["load \"L\"", "\"R\""]
        );
    }

    #[test]
    fn a_statement_that_is_only_continuations_produces_nothing() {
        assert!(texts("&\n&\n").is_empty());
        assert!(texts("   &   \n").is_empty());
    }

    // ==================================================================
    // Comments
    // ==================================================================

    #[test]
    fn a_comment_line_is_dropped_even_after_leading_whitespace() {
        assert_eq!(
            texts("# a comment\n   # indented\nload \"L\"\n"),
            vec!["load \"L\""]
        );
    }

    #[test]
    fn a_comment_after_a_continuation_lets_the_statement_resume() {
        // The pending continuation skips the comment on line 3 and completes on
        // line 4; the statement still reports its own first line (2, not 4 and
        // not the leading comment's line 1).
        let lines = lex("# header\nload \"L\" &\n# why\n\"R\"\n");
        assert_eq!(lines.len(), 1);
        assert_eq!(lines[0].text, "load \"L\" \"R\"");
        assert_eq!(lines[0].line, 2);
    }

    #[test]
    fn a_comment_line_ending_in_ampersand_does_not_continue() {
        // Comments are dropped entirely, so the `&` on a comment line means
        // nothing and the next line is a fresh statement.
        assert_eq!(
            texts("# comment &\nload \"L\" \"R\"\n"),
            vec!["load \"L\" \"R\""]
        );
    }

    #[test]
    fn a_comment_line_inside_a_pending_quoted_value_is_still_dropped() {
        // Both rules are line-level: `&` continues even inside a quote, and the
        // comment test does not look at quote state either.
        assert_eq!(texts("load \"A &\n# gone\nB\"\n"), vec!["load \"A B\""]);
    }

    #[test]
    fn a_hash_that_is_not_first_is_literal_text() {
        assert_eq!(texts("criteria attrib:#1\n"), vec!["criteria attrib:#1"]);
        assert_eq!(texts("load \"L\" #x\n"), vec!["load \"L\" #x"]);
    }

    #[test]
    fn a_hash_inside_quotes_is_literal_text() {
        // The first non-whitespace character is `f` and the `#` is inside the
        // quotes; neither makes the line a comment.
        assert_eq!(texts("filter \"a#b;c#d\"\n"), vec!["filter \"a#b;c#d\""]);
    }

    #[test]
    fn a_quote_before_the_hash_keeps_the_line() {
        // The first non-whitespace character decides, and here it is `"`.  The
        // quotes survive into the logical line; dropping them is the parser's
        // tokenizer job.
        assert_eq!(texts("\"#not a comment\"\n"), vec!["\"#not a comment\""]);
    }

    #[test]
    fn a_comment_only_script_produces_nothing() {
        assert!(texts("# one\n# two\n").is_empty());
        assert!(texts("").is_empty());
    }

    // ==================================================================
    // Blank lines, whitespace and line endings
    // ==================================================================

    #[test]
    fn blank_lines_between_statements_produce_nothing() {
        assert_eq!(
            texts("load \"L\" \"R\"\n\n\nexpand all\n"),
            vec!["load \"L\" \"R\"", "expand all"]
        );
    }

    #[test]
    fn trailing_whitespace_is_trimmed() {
        let lines = lex("load \"L\"   \t\n");
        assert_eq!(lines[0].text, "load \"L\"");
    }

    #[test]
    fn crlf_line_endings_are_handled() {
        let lines = lex("load \"L\" \"R\"\r\n# comment\r\nexpand all\r\n");
        assert_eq!(lines.len(), 2);
        assert_eq!(lines[0].text, "load \"L\" \"R\"", "no stray \\r");
        assert_eq!(lines[1].text, "expand all");
        assert_eq!(lines[1].line, 3);
    }

    #[test]
    fn crlf_continuation_joins() {
        assert_eq!(
            texts("load \"L\" &\r\n\"R\"\r\n"),
            vec!["load \"L\" \"R\""]
        );
    }

    #[test]
    fn a_missing_final_newline_is_fine() {
        assert_eq!(texts("expand all"), vec!["expand all"]);
    }

    #[test]
    fn a_utf8_bom_does_not_glue_itself_to_the_first_command() {
        assert_eq!(
            logical_lines("\u{feff}load \"L\" \"R\"\n").unwrap()[0].text,
            "load \"L\" \"R\""
        );
    }

    // ==================================================================
    // Line numbers
    // ==================================================================

    #[test]
    fn line_numbers_track_the_first_physical_line() {
        let lines = lex("# header\n\nload \"L\" \"R\"\nexpand all &\n  \"A\"\n");
        assert_eq!(lines.len(), 2);
        assert_eq!((lines[0].line, lines[0].text.as_str()), (3, "load \"L\" \"R\""));
        assert_eq!((lines[1].line, lines[1].text.as_str()), (4, "expand all \"A\""));
    }

    #[test]
    fn a_statement_starting_with_a_lone_ampersand_reports_that_line() {
        // The statement textually begins on the `&` line even though the `&`
        // contributes no characters, and the `&` says the next line continues it.
        let lines = lex("load \"L\" \"R\"\n&\nexpand all\n");
        assert_eq!(lines.len(), 2);
        assert_eq!((lines[1].line, lines[1].text.as_str()), (2, "expand all"));
    }

    // ==================================================================
    // Unterminated quotes: exit 107, and the statement's first line
    // ==================================================================

    #[test]
    fn an_unterminated_quote_is_exit_107() {
        // u5 `unclosed-quote` measured 107 (input-loading failure), not 106.
        let err = logical_lines("load \"L\n").unwrap_err();
        assert_eq!(err.exit_code, 107, "the Oracle reports 107, not 106");
        assert_eq!(err.line, 1);
        assert!(err.message.contains("quote"), "message names the problem: {err}");
    }

    #[test]
    fn an_unterminated_quote_reports_the_statements_first_line() {
        let script = "# a comment\n\nload \"L\" &\n\"R\n";
        let err = logical_lines(script).unwrap_err();
        assert_eq!(err.line, 3, "the statement starts on line 3");
        assert_eq!(err.exit_code, 107);
    }

    #[test]
    fn the_u5_unclosed_quote_recipe_is_107_on_line_one() {
        // The measured script verbatim (u5 `unclosed-quote`):
        // text-report layout:xml output-to:"%3 "%1" "%2"   -- an odd number of
        // quotes, and the Oracle exits 107 rather than 106.
        let script = "text-report layout:xml output-to:\"%3 \"%1\" \"%2\"\n";
        let err = logical_lines(script).unwrap_err();
        assert_eq!(err.exit_code, 107);
        assert_eq!(err.line, 1);
    }

    #[test]
    fn a_backslash_does_not_escape_a_quote() {
        // The official exclude-a-folder sample: the mask is `-CVS\` and the
        // closing quote follows the backslash.  Two quotes, so it lexes, and the
        // backslash stays part of the value (the parser keeps it; task B's
        // matcher reads the trailing `\` as a folder mask).
        let lines = lex("filter \"*.htm;*.gif;-CVS\\\"\n");
        assert_eq!(lines.len(), 1);
        assert_eq!(lines[0].text, "filter \"*.htm;*.gif;-CVS\\\"");
    }
}

//! Report options: the CLI flag vocabulary and the display/ignore switches.
//!
//! # Option vocabulary (observed)
//!
//! The three `--opt=` values the golden corpus names in its `note` fields are
//! **O**bserved in `verify/golden`:
//!
//! | Option | Effect | Evidence |
//! |---|---|---|
//! | `display-all` | every line, no filtering (the default) | `opt-display-all` |
//! | `display-mismatches` | only `similar` and `different` lines | `opt-display-mismatches` |
//! | `display-context` | all lines, with `<mode>Differences, With Context</mode>` | `opt-display-context` |
//! | `display-matches` | only `same` lines, with `<mode>Same</mode>` | `opt-display-matches` |
//! | `ignore-unimportant` | `similar` collapses to `same`, with `<ignoreunimportant/>` | `opt-ignore-unimportant` |
//!
//! `display-mismatches` is the only filter that also emits a `<mode>` element,
//! and `display-context` / `display-matches` emit their own; ordering in the
//! document is `<filename2>`, then `<mode>`, then `<ignoreunimportant/>`, then
//! the `linecomp` sequence — which is the order observed in the four option
//! reports.
//!
//! Any value outside this vocabulary is rejected with an explicit error rather
//! than ignored, so an unsupported option can never silently produce a report
//! for a different mode than the caller asked for.

use std::fmt;

/// Which lines appear in the report.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum DisplayMode {
    /// Every line. The default, and the mode with no `<mode>` element.
    #[default]
    All,
    /// Only `similar` and `different` lines. Emits `<mode>Differences</mode>`.
    Mismatches,
    /// All lines, with surrounding context. Emits
    /// `<mode>Differences, With Context</mode>`.
    Context,
    /// Only `same` lines. Emits `<mode>Same</mode>`.
    Matches,
}

impl DisplayMode {
    /// The `<mode>` element text, or `None` when this mode emits no element.
    pub fn as_xml_mode(self) -> Option<&'static str> {
        match self {
            DisplayMode::All => None,
            DisplayMode::Mismatches => Some("Differences"),
            DisplayMode::Context => Some("Differences, With Context"),
            DisplayMode::Matches => Some("Same"),
        }
    }

    /// The name accepted on the command line, i.e. the `display-*` option name.
    pub fn option_name(self) -> &'static str {
        match self {
            DisplayMode::All => "display-all",
            DisplayMode::Mismatches => "display-mismatches",
            DisplayMode::Context => "display-context",
            DisplayMode::Matches => "display-matches",
        }
    }

    /// True when `same` lines are kept in the report body.
    pub fn keeps_same(self) -> bool {
        !matches!(self, DisplayMode::Mismatches)
    }

    /// True when non-`same` lines are kept in the report body.
    pub fn keeps_different(self) -> bool {
        !matches!(self, DisplayMode::Matches)
    }
}

impl fmt::Display for DisplayMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.option_name())
    }
}

/// A complete option set for one comparison.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct ReportOptions {
    pub display: DisplayMode,
    /// `ignore-unimportant`: collapse `similar` to `same` before reporting.
    pub ignore_unimportant: bool,
}

/// An option name that is not in the observed vocabulary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnknownOption(pub String);

impl fmt::Display for UnknownOption {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "unsupported option {:?} (supported: display-all, display-context, \
             display-matches, display-mismatches, ignore-unimportant)",
            self.0
        )
    }
}

impl std::error::Error for UnknownOption {}

impl ReportOptions {
    /// Apply one option name. Unknown names are refused, never ignored.
    pub fn apply(&mut self, name: &str) -> Result<(), UnknownOption> {
        match name.trim() {
            "" => return Ok(()),
            "display-all" => self.display = DisplayMode::All,
            "display-context" => self.display = DisplayMode::Context,
            "display-matches" => self.display = DisplayMode::Matches,
            "display-mismatches" => self.display = DisplayMode::Mismatches,
            "ignore-unimportant" => self.ignore_unimportant = true,
            other => return Err(UnknownOption(other.to_string())),
        }
        Ok(())
    }

    /// Parse a `--opt=` payload: one or more names separated by `,` or spaces.
    ///
    /// Both separators are accepted because BC's own `options:` list is
    /// comma-separated while a shell user naturally writes spaces. Names are
    /// trimmed, so `"a, b"` and `"a,b"` agree.
    pub fn parse_list(payload: &str) -> Result<Self, UnknownOption> {
        let mut opts = ReportOptions::default();
        for part in payload.split(|c: char| c == ',' || c.is_whitespace()) {
            opts.apply(part)?;
        }
        Ok(opts)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_is_display_all_with_no_ignore() {
        let o = ReportOptions::default();
        assert_eq!(o.display, DisplayMode::All);
        assert!(!o.ignore_unimportant);
        assert_eq!(o.display.as_xml_mode(), None);
    }

    #[test]
    fn every_display_name_round_trips() {
        for mode in [
            DisplayMode::All,
            DisplayMode::Mismatches,
            DisplayMode::Context,
            DisplayMode::Matches,
        ] {
            let mut o = ReportOptions::default();
            o.apply(mode.option_name()).unwrap();
            assert_eq!(o.display, mode, "round trip failed for {}", mode.option_name());
        }
    }

    #[test]
    fn mode_elements_match_the_golden_reports() {
        assert_eq!(DisplayMode::All.as_xml_mode(), None);
        assert_eq!(DisplayMode::Mismatches.as_xml_mode(), Some("Differences"));
        assert_eq!(
            DisplayMode::Context.as_xml_mode(),
            Some("Differences, With Context")
        );
        assert_eq!(DisplayMode::Matches.as_xml_mode(), Some("Same"));
    }

    #[test]
    fn filter_predicates_match_the_golden_status_sequences() {
        // opt-display-matches keeps only the three `same` lines.
        assert!(DisplayMode::Matches.keeps_same());
        assert!(!DisplayMode::Matches.keeps_different());
        // opt-display-mismatches keeps only similar/similar/different.
        assert!(!DisplayMode::Mismatches.keeps_same());
        assert!(DisplayMode::Mismatches.keeps_different());
        // display-all and display-context keep everything.
        for m in [DisplayMode::All, DisplayMode::Context] {
            assert!(m.keeps_same() && m.keeps_different());
        }
    }

    #[test]
    fn comma_and_space_separated_lists_agree() {
        let a = ReportOptions::parse_list("display-mismatches, ignore-unimportant").unwrap();
        let b = ReportOptions::parse_list("display-mismatches ignore-unimportant").unwrap();
        assert_eq!(a, b);
        assert_eq!(a.display, DisplayMode::Mismatches);
        assert!(a.ignore_unimportant);
    }

    #[test]
    fn empty_payload_is_the_default() {
        assert_eq!(ReportOptions::parse_list("").unwrap(), ReportOptions::default());
        assert_eq!(ReportOptions::parse_list("  ").unwrap(), ReportOptions::default());
    }

    #[test]
    fn unknown_options_are_refused_not_ignored() {
        let err = ReportOptions::parse_list("display-everything").unwrap_err();
        assert_eq!(err.0, "display-everything");
        assert!(err.to_string().contains("unsupported option"));
        assert!(ReportOptions::parse_list("ignore-whitespace").is_err());
        assert!(ReportOptions::parse_list("display-all,ignore-case").is_err());
    }

    #[test]
    fn last_display_option_wins() {
        let o = ReportOptions::parse_list("display-matches,display-all").unwrap();
        assert_eq!(o.display, DisplayMode::All);
    }
}

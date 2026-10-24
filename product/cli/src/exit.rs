//! Exit codes, as one table both the CLI and the tests read.
//!
//! Every code here is either **observed** in this workspace (`probes/u5*`, see
//! `verify/probes/U5-FINDINGS.md`) or quoted from the Oracle's own
//! `help/command_line_reference.html` "Return codes" table. The distinction
//! matters: a code taken from the help file is documented, not measured, and
//! the tests exercise only the observed ones.

/// The BC exit code vocabulary.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Exit {
    /// 0 — the script ran and its report was written, whether or not the inputs
    /// differ (O: every anchor and every u5 script run).
    Success,
    /// 1 — `/qc`: byte-identical (O: u5b/u5k).
    BinarySame,
    /// 2 — `/qc` rules-based: only a line-ending difference (O: u5b crlf-only).
    RulesBasedSame,
    /// 11 — `/qc crc|binary`: bytes differ (O: u5b/u5k).
    BinaryDiff,
    /// 12 — `/qc` rules-based: only unimportant differences (O: u5b ws/case,
    /// u5k indentation/trailing whitespace).
    Similar,
    /// 13 — `/qc` rules-based: an important difference (O: u5b comment-only,
    /// u5k content control).
    RulesBasedDiff,
    /// 100 — `/qc` could not read an input (O: u5b missing files).
    Unknown,
    /// 104 — trial expired.  Documentation only; this build never produces it.
    TrialExpired,
    /// 105 — the `@` script file could not be read (O: u5 missing-script-file).
    ScriptNotLoadable,
    /// 106 — script syntax/command error (O: u5 unknown command, missing
    /// argument, bad enum value; u5c `criteria bogus`; u5e `option bogus`,
    /// `expand <missing path>`).
    ScriptSyntax,
    /// 107 — an input could not be loaded: `load` of a missing path or of a
    /// file, a report naming missing files, an unterminated quote
    /// (O: u5, u5c, u5f).
    LoadFailed,
}

impl Exit {
    pub fn code(self) -> i32 {
        match self {
            Exit::Success => 0,
            Exit::BinarySame => 1,
            Exit::RulesBasedSame => 2,
            Exit::BinaryDiff => 11,
            Exit::Similar => 12,
            Exit::RulesBasedDiff => 13,
            Exit::Unknown => 100,
            Exit::TrialExpired => 104,
            Exit::ScriptNotLoadable => 105,
            Exit::ScriptSyntax => 106,
            Exit::LoadFailed => 107,
        }
    }

    /// True when this code came from an observation in this workspace rather
    /// than from the help file.  Tests assert against these; the rest are
    /// documented for completeness.
    pub fn is_observed(self) -> bool {
        !matches!(self, Exit::TrialExpired)
    }

    pub fn meaning(self) -> &'static str {
        match self {
            Exit::Success => "success",
            Exit::BinarySame => "binary same",
            Exit::RulesBasedSame => "rules-based same",
            Exit::BinaryDiff => "binary differences",
            Exit::Similar => "similar",
            Exit::RulesBasedDiff => "rules-based differences",
            Exit::Unknown => "unknown error",
            Exit::TrialExpired => "trial period expired (documentation only)",
            Exit::ScriptNotLoadable => "error loading script file",
            Exit::ScriptSyntax => "script syntax error",
            Exit::LoadFailed => "script failed to load folders or files",
        }
    }
}

impl From<Exit> for i32 {
    fn from(e: Exit) -> i32 {
        e.code()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn codes_match_the_observed_table() {
        // Each pair is (code, the observation that produced it) from
        // probes/u5*; see verify/probes/U5-FINDINGS.md section 1.
        assert_eq!(Exit::Success.code(), 0);
        assert_eq!(Exit::BinarySame.code(), 1);
        assert_eq!(Exit::RulesBasedSame.code(), 2);
        assert_eq!(Exit::BinaryDiff.code(), 11);
        assert_eq!(Exit::Similar.code(), 12);
        assert_eq!(Exit::RulesBasedDiff.code(), 13);
        assert_eq!(Exit::Unknown.code(), 100);
        assert_eq!(Exit::ScriptNotLoadable.code(), 105);
        assert_eq!(Exit::ScriptSyntax.code(), 106);
        assert_eq!(Exit::LoadFailed.code(), 107);
    }

    #[test]
    fn only_the_trial_code_is_unobserved() {
        let all = [
            Exit::Success, Exit::BinarySame, Exit::RulesBasedSame, Exit::BinaryDiff,
            Exit::Similar, Exit::RulesBasedDiff, Exit::Unknown, Exit::TrialExpired,
            Exit::ScriptNotLoadable, Exit::ScriptSyntax, Exit::LoadFailed,
        ];
        let unobserved: Vec<&str> = all.iter()
            .filter(|e| !e.is_observed())
            .map(|e| e.meaning())
            .collect();
        assert_eq!(unobserved.len(), 1, "{unobserved:?}");
        assert!(unobserved[0].contains("documentation only"));
    }

    #[test]
    fn every_code_is_distinct() {
        let all = [
            Exit::Success, Exit::BinarySame, Exit::RulesBasedSame, Exit::BinaryDiff,
            Exit::Similar, Exit::RulesBasedDiff, Exit::Unknown, Exit::TrialExpired,
            Exit::ScriptNotLoadable, Exit::ScriptSyntax, Exit::LoadFailed,
        ];
        let mut codes: Vec<i32> = all.iter().map(|e| e.code()).collect();
        codes.sort_unstable();
        codes.dedup();
        assert_eq!(codes.len(), all.len());
    }
}

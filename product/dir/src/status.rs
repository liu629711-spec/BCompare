//! The comparison status of one aligned entry.
//!
//! # Evidence for the token vocabulary
//!
//! Two independent sources, both O level:
//!
//! 1. **Observed output.** Actual Oracle reports contain exactly three of these
//!    tokens. Counted across every stored run
//!    (`product/verify/runs/*/raw/*.xml`):
//!
//!    ```text
//!    filecomp status="same"     80
//!    filecomp status="ltonly"   20
//!    filecomp status="rtonly"   20
//!    ```
//!
//! 2. **The report writer's own string table and code.** The function that
//!    generates `<filecomp status="…">` is `FUN_140fd1e90` in
//!    `DlgDirReport.pas` (`specs/dir/README.md` section 3.7,
//!    `extracted/string-function-index.tsv` lines 11893-11896). Its string
//!    literals are `ltnewer`, `rtnewer`, `ltonly`, `rtonly`, `same`, `diff`, and
//!    the decompiled body
//!    (`extracted/pseudocode/140fd1e90.c`, `body_size: 673`) switches on a status
//!    byte:
//!
//!    ```text
//!    bVar1 == 0  -> "same"      bVar1 == 6 -> "ltnewer"
//!    bVar1 == 2  -> "ltonly"    bVar1 == 7 -> "rtnewer"
//!    bVar1 == 3  -> "rtonly"    bVar1 == 9 -> "diff"
//!    ```
//!
//! So the report-visible vocabulary is **six** tokens. Those six are modelled
//! here, and [`Status::xml_token`] restricts output to exactly them.
//!
//! # What is deliberately *not* modelled
//!
//! `product/verify/harness/normalize.py` also lists `leftolder`, `rightolder`,
//! `orphan` and `conflict` in `KNOWN_FILECOMP_STATUS`. **Those four have never
//! been observed in output and do not appear in the writer's string table**, so
//! this crate does not emit them. They are treated as unproven supersets of the
//! vocabulary, not as evidence. (`orphan` exists in the binary but belongs to a
//! different function, `FUN_1417d1d20` — see `string-function-index.tsv` line
//! 18039 — not to the folder-report writer.)
//!
//! Likewise `DirHollow` and `DirFiltered` are real `DlgDirReport` status names
//! (O: string table, `extracted/pseudocode/140fccbf0.c`), but "hollow" is a
//! *scan-state* ("Folders may appear hollow when you first start the comparison.
//! This happens when the background scanning process has not yet completed those
//! folders" — `help/dir_understanding_the_display.html`), not a comparison
//! result, and a fully computed report has no scanning in progress. Both are out
//! of scope for a read-only batch comparison and are recorded as such in
//! `docs/EVIDENCE.md`.

use std::fmt;

/// The comparison result of one aligned pair (or one-sided entry).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum Status {
    /// Both sides exist and every applicable criterion matches.
    Same,
    /// Both sides exist and a criterion other than the timestamp differs.
    Diff,
    /// Only the left side has the entry.
    LeftOnly,
    /// Only the right side has the entry.
    RightOnly,
    /// Both sides exist, all content criteria match, and the left timestamp is
    /// newer.
    LeftNewer,
    /// Both sides exist, all content criteria match, and the right timestamp is
    /// newer.
    RightNewer,
    /// The comparison could not be decided.
    ///
    /// Carried as an explicit variant so an undecidable case can never be
    /// silently reported as `Same`. [`Status::xml_token`] returns `None` for it,
    /// and the XML writer refuses to write a status it cannot name.
    Unknown,
}

impl Status {
    /// The exact token the observed report writer emits, or `None` when this
    /// status has no observed token.
    pub fn xml_token(self) -> Option<&'static str> {
        match self {
            Status::Same => Some("same"),
            Status::Diff => Some("diff"),
            Status::LeftOnly => Some("ltonly"),
            Status::RightOnly => Some("rtonly"),
            Status::LeftNewer => Some("ltnewer"),
            Status::RightNewer => Some("rtnewer"),
            Status::Unknown => None,
        }
    }

    /// All tokens with observed evidence, for tests and for the report legend.
    pub fn observed_tokens() -> [&'static str; 6] {
        ["same", "diff", "ltonly", "rtonly", "ltnewer", "rtnewer"]
    }

    pub fn is_orphan(self) -> bool {
        matches!(self, Status::LeftOnly | Status::RightOnly)
    }

    pub fn is_match(self) -> bool {
        matches!(self, Status::Same)
    }

    /// A one-word English label for the text layouts.
    pub fn label(self) -> &'static str {
        match self {
            Status::Same => "same",
            Status::Diff => "different",
            Status::LeftOnly => "left only",
            Status::RightOnly => "right only",
            Status::LeftNewer => "left newer",
            Status::RightNewer => "right newer",
            Status::Unknown => "unknown",
        }
    }
}

impl fmt::Display for Status {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.xml_token() {
            Some(t) => f.write_str(t),
            None => f.write_str(self.label()),
        }
    }
}

/// A note attached to a comparison result, for behaviour that is deliberately
/// not implemented.
///
/// Exists so a partial implementation is *visible in the output* rather than
/// silently indistinguishable from the real thing
/// (`product/docs/05-acceptance-strategy.md` section 6, checks 2 and 3).
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ComparisonNote {
    /// `criteria rules-based` was requested. The criterion is evaluated as byte
    /// equality; the per-format importance rules that can turn a difference into
    /// `similar` are M2 work (`04-milestones.md` M2.2/M2.3) and are not
    /// implemented here. Recorded so no caller reads the verdict as full BC
    /// semantics.
    RulesBasedTextRulesNotImplemented,
    /// `follow-symlinks` was requested and an entry is a symlink whose target
    /// could not be resolved.
    UnresolvedSymlink { name: String },
    /// A path could not be read; the entry is reported as an explicit failure
    /// rather than as absent.
    ReadFailed { name: String, detail: String },
    /// A criterion does not apply to this entry's kind.
    ///
    /// Only used for a non-regular-file entry, e.g. the size criterion on a
    /// symlink that is not being followed: a link is not a file with a size, so
    /// the criterion is *not applicable* rather than "equal". Recorded so the
    /// distinction is visible instead of being an implicit pass.
    CriterionNotApplicable { name: String, criterion: &'static str },
}

impl fmt::Display for ComparisonNote {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ComparisonNote::RulesBasedTextRulesNotImplemented => write!(
                f,
                "criteria rules-based: evaluated as byte equality; the text-format \
                 importance rules (M2) are not implemented"
            ),
            ComparisonNote::UnresolvedSymlink { name } => {
                write!(f, "unresolved symlink: {name}")
            }
            ComparisonNote::ReadFailed { name, detail } => {
                write!(f, "read failed for {name}: {detail}")
            }
            ComparisonNote::CriterionNotApplicable { name, criterion } => write!(
                f,
                "criterion {criterion} does not apply to {name} (not a regular file)"
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn xml_tokens_are_exactly_the_six_the_writer_emits() {
        let mut tokens: Vec<&str> = [
            Status::Same,
            Status::Diff,
            Status::LeftOnly,
            Status::RightOnly,
            Status::LeftNewer,
            Status::RightNewer,
        ]
        .iter()
        .filter_map(|s| s.xml_token())
        .collect();
        tokens.sort_unstable();
        let mut expected = Status::observed_tokens().to_vec();
        expected.sort_unstable();
        assert_eq!(tokens, expected);
    }

    #[test]
    fn unobserved_tokens_are_not_emitted() {
        // The harness's larger vocabulary must not leak into output.
        let emitted: Vec<&str> = Status::observed_tokens().to_vec();
        for unobserved in ["leftolder", "rightolder", "orphan", "conflict"] {
            assert!(
                !emitted.contains(&unobserved),
                "{unobserved} has no observed evidence and must not be emitted"
            );
        }
    }

    #[test]
    fn unknown_status_has_no_token_and_is_not_same() {
        assert_eq!(Status::Unknown.xml_token(), None);
        assert!(!Status::Unknown.is_match());
        assert_ne!(Status::Unknown, Status::Same);
    }

    #[test]
    fn orphan_predicate_covers_both_sides_only() {
        assert!(Status::LeftOnly.is_orphan());
        assert!(Status::RightOnly.is_orphan());
        assert!(!Status::Same.is_orphan());
        assert!(!Status::Diff.is_orphan());
    }
}

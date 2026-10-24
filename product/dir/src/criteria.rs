//! The comparison criteria model.
//!
//! # The observed model (O level)
//!
//! `product/docs/00-current-state.md` section 6 records the measurement
//! (`tools/_audit/probe-dir-criteria.py`, run against BCompare 5.2.1.32035). The
//! fixture's `diff.txt` is `aaaa` vs `bbbb` — same size, same timestamp — and the
//! report verdict per criteria command was:
//!
//! | criteria | `diff.txt` | `samesize.bin` |
//! |---|---|---|
//! | default (no criteria) | **same** | same |
//! | `criteria size` | same | same |
//! | `criteria timestamp` | same | same |
//! | `criteria CRC` | **diff** | diff |
//! | `criteria binary` | **diff** | diff |
//! | `criteria rules-based` | **diff** | diff |
//! | `criteria content` / `binary-content` | exit 106 (invalid command) | — |
//!
//! > **结论：BC 文件夹比较默认是「时间戳 + 大小」，不是内容比较。**
//!
//! So:
//!
//! * **default = size + timestamp**, *not* content. This is the single most
//!   important semantic in the folder engine and it is O-level evidence.
//! * `size`, `timestamp`, `CRC`, `binary`, `rules-based` are the five valid
//!   content/quick criteria.
//! * `content` and `binary-content` are **invalid**: BC exits 106 with no report.
//!   Modelled as [`CriteriaError::InvalidCriteria`], never silently accepted.
//!
//! # Documented parameter surface (O level, official help)
//!
//! `help/scripting_reference.html`, CRITERIA:
//!
//! ```text
//! criteria [attrib:<attribute set>] [version] [timestamp[:[<number of seconds>sec][;IgnoreDST]]]
//!          [size|CRC|binary|rules-based] [timezone:(ignore|(left|right)(+|-)<0..12>)]
//!          [follow-symlinks] [ignore-unimportant] [owner] [group] [permissions]
//! ```
//!
//! * "`timestamp` enables timestamp comparisons" and "`<number of seconds>sec`
//!   considers differences within a tolerance of seconds as matches".
//! * "`IgnoreDST` considers differences of exactly 1 hour as matches."
//! * "`size`, `CRC`, `binary` and `rules-based` are the possible ways to compare
//!   contents."
//!
//! # What is implemented, and what is explicitly refused
//!
//! Implemented and testable: the five observed criteria, the default, timestamp
//! tolerance, IgnoreDST, `attrib:`, `timezone:`, `follow-symlinks`.
//!
//! **Refused with an explicit error** (never silently ignored): `version`,
//! `owner`, `group`, `permissions`, `ignore-unimportant`. Each names a real BC
//! feature whose behaviour has not been probed in this workspace, and
//! `product/docs/04-milestones.md` section 5 says to implement only probed
//! models and list the rest. See [`Criteria::apply_token`].

use std::fmt;

/// Which side of the comparison a rule or error applies to.
///
/// Re-used from the VFS layer rather than redefined, so there is exactly one
/// `Side` type in the system and no conversion is needed at the boundary.
pub use reacmp_vfs::Side;
use reacmp_vfs::AttributeSet;

/// The content/quick comparison mode. Exactly the five observed commands.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ContentCriteria {
    /// Compare file size only (a quick test).
    Size,
    /// Compare modification time (a quick test).
    Timestamp,
    /// Compare CRC of the contents (requires reading the files).
    Crc,
    /// Compare contents byte-for-byte (requires reading the files).
    Binary,
    /// Compare contents with the file-format rules (requires reading the files).
    RulesBased,
    /// Compare embedded PE version resources (requires reading the files).
    ///
    /// Semantics measured in `probes/U4-FINDINGS.md` section 1: this compares
    /// the **FileVersion** field of the VS_FIXEDFILEINFO resource — a
    /// ProductVersion-only difference reports `same` (u4c
    /// `ver-product-only-field`) — and the result is *directional*: the higher
    /// version is reported `ltnewer`/`rtnewer` (u4c `ver-left-higher`,
    /// `ver-both-higher-right`). A side without a version resource is treated
    /// as older than a side with one (u4f `f-version-pe-left` /
    /// `f-version-pe-right`). The criterion REPLACES the default size+timestamp
    /// pair like every other content keyword, and a later size/timestamp token
    /// re-activates those (u4f `f-version-plus-size`).
    Version,
    /// Compare POSIX-style owner information.
    ///
    /// On Windows the observable behaviour is **inert**: the live Oracle
    /// accepts the token and ignores it, including for files whose NTFS owner
    /// actually differs (u4 `owner-equal-files`, u4b `owner-systemdir`,
    /// u4e `owner-size-differs` — the size difference vanished but the owner
    /// never produced a difference). The token still REPLACES the default
    /// size+timestamp pair, which is what u4e actually measured.
    Owner,
    /// Compare POSIX-style group information. Windows-inert, as [`Self::Owner`].
    Group,
    /// Compare POSIX-style access permissions. Windows-inert, as
    /// [`Self::Owner`]; an NTFS deny-ACE difference on one side did not change
    /// the row (u4 `permissions-acl-differs`, u4b `perm-dir-acl`).
    Permissions,
}

impl ContentCriteria {
    pub fn as_str(self) -> &'static str {
        match self {
            ContentCriteria::Size => "size",
            ContentCriteria::Timestamp => "timestamp",
            ContentCriteria::Crc => "CRC",
            ContentCriteria::Binary => "binary",
            ContentCriteria::RulesBased => "rules-based",
            ContentCriteria::Version => "version",
            ContentCriteria::Owner => "owner",
            ContentCriteria::Group => "group",
            ContentCriteria::Permissions => "permissions",
        }
    }

    /// True when evaluating this criterion needs the file bytes.
    ///
    /// Mirrors the help page's "Quick tests" vs "Requires opening files"
    /// distinction: names, sizes and timestamps are cheap; CRC and content need
    /// a read. Used by the engine to avoid reading bytes under the default.
    pub fn requires_content_read(self) -> bool {
        matches!(
            self,
            ContentCriteria::Crc
                | ContentCriteria::Binary
                | ContentCriteria::RulesBased
                | ContentCriteria::Version
        )
    }

    /// True for the three POSIX-metadata criteria that are inert on Windows.
    ///
    /// A separate predicate because the engine must not treat them as
    /// "no criterion at all": they still replace the default pair.
    pub fn is_posix_metadata(self) -> bool {
        matches!(
            self,
            ContentCriteria::Owner | ContentCriteria::Group | ContentCriteria::Permissions
        )
    }

    /// Parse one criteria keyword. Case-insensitive, as BC's scripting is.
    pub fn parse(token: &str) -> Option<Self> {
        match token.to_ascii_lowercase().as_str() {
            "size" => Some(ContentCriteria::Size),
            "timestamp" => Some(ContentCriteria::Timestamp),
            "crc" => Some(ContentCriteria::Crc),
            "binary" => Some(ContentCriteria::Binary),
            "rules-based" => Some(ContentCriteria::RulesBased),
            "version" => Some(ContentCriteria::Version),
            "owner" => Some(ContentCriteria::Owner),
            "group" => Some(ContentCriteria::Group),
            "permissions" => Some(ContentCriteria::Permissions),
            _ => None,
        }
    }
}

impl fmt::Display for ContentCriteria {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Timestamp comparison settings.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct TimestampRule {
    /// Differences up to this many seconds count as a match. `0` means exact.
    ///
    /// `criteria timestamp:2sec` -> `2`. O: documented in the help text quoted
    /// in the module doc. Not yet Oracle-probed for the *boundary* case
    /// (exactly `N` seconds apart) — see `docs/EVIDENCE.md` U-M3-2.
    pub tolerance_seconds: u32,
    /// Ignore a difference of exactly one hour (the documented `IgnoreDST`).
    pub ignore_dst: bool,
}

impl TimestampRule {
    /// Whether two instants count as matching under this rule.
    ///
    /// Order of evaluation matters and is *derived* from the documentation:
    /// `IgnoreDST` is described as "differences of **exactly** 1 hour", so it is
    /// tested as an exact value and does not combine with a numeric tolerance
    /// (a tolerance of 7200 s would otherwise subsume it and change the meaning
    /// of "exactly").
    pub fn matches(&self, left: reacmp_vfs::Timestamp, right: reacmp_vfs::Timestamp) -> bool {
        let diff = left.seconds_between(right);
        if self.ignore_dst && diff == 3600 {
            return true;
        }
        diff <= self.tolerance_seconds as i64
    }
}

/// `timezone:` handling — the script grammar the live Oracle accepts.
///
/// The help text documents `timezone:(ignore|(left|right)(+|-)<0..12>)` (O),
/// but the A-3 folder gate measured the Oracle **rejecting every shifted
/// form with exit 106** (`A3-folder-gate-serial-01` FINDINGS F3), so the
/// only script-level rule is `ignore`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum TimezoneRule {
    /// No `timezone:` was given; timestamps are compared as reported.
    #[default]
    UseLocalZone,
    /// `timezone:ignore` — treat a timestamp difference that is a whole number of
    /// hours (0..14) as a zone artefact rather than a real difference.
    ///
    /// Which hour values count is **not** fully probed; the A-3 gate confirmed
    /// the whole-hour convention against the live Oracle (`tz-ignore`:
    /// 1 h and 2 h differences both compare `same`). An unrecognised rule is
    /// never silently ignored: `Ignore` never matches a *partial* hour
    /// difference.
    Ignore,
}

impl TimezoneRule {
    /// The offset in seconds to apply to each side, if any.
    ///
    /// Always `(0, 0)`: the live Oracle rejects shifted timezone rules
    /// (FINDINGS F3), so no rule shifts a side any more.
    pub fn offsets_seconds(self) -> (i64, i64) {
        let _ = self;
        (0, 0)
    }

    /// True when a whole-hour difference should be treated as a zone artefact
    /// rather than a real timestamp difference (`timezone:ignore`).
    pub fn suppresses_whole_hour_differences(self) -> bool {
        matches!(self, TimezoneRule::Ignore)
    }
}

/// A full criteria specification, matching the documented `criteria` grammar.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Criteria {
    /// Criteria actually compared, in the order the command set them.
    ///
    /// `criteria size` **sets** the content criterion (help text: "Sets all
    /// comparison criteria settings"), so the last content keyword wins and the
    /// default pair is replaced, not appended to.
    pub content: Vec<ContentCriteria>,
    pub timestamp: TimestampRule,
    pub timezone: TimezoneRule,
    pub attributes: AttributeSet,
    pub follow_symlinks: bool,
    /// `ignore-unimportant`: fold unimportant content differences to matches.
    ///
    /// Observed scope (u4e `rb-comment-only-iu`, u4f `f-iu-rb-ws` /
    /// `f-iu-rb-real` / `f-iu-alone-size`): the token only affects a
    /// **rules-based content** comparison — a comment-only `.c` difference
    /// becomes `same` while an identifier difference stays `diff` — and has
    /// no effect on size/timestamp-only rows (u4f `f-iu-alone-size` reports
    /// `same`, which the default criteria produce anyway because sizes are
    /// equal there; the u4d `iu-*` folder probes show one-sided entries and
    /// structural rows are untouched).
    pub ignore_unimportant: bool,
}

impl Default for Criteria {
    /// The observed default: **size + timestamp**, no content comparison.
    fn default() -> Self {
        Criteria {
            content: vec![ContentCriteria::Size, ContentCriteria::Timestamp],
            timestamp: TimestampRule::default(),
            timezone: TimezoneRule::default(),
            attributes: AttributeSet::EMPTY,
            follow_symlinks: false,
            ignore_unimportant: false,
        }
    }
}

impl Criteria {
    /// The default, spelled out (`O`).
    pub fn observed_default() -> Self {
        Criteria::default()
    }

    /// Build from a single content keyword, mirroring `criteria <keyword>`.
    ///
    /// This is the shape the observed probe used: `criteria CRC` alone, with no
    /// `size`/`timestamp`, and it produced `diff` — so the keyword replaces the
    /// default pair rather than adding to it.
    pub fn from_content(kind: ContentCriteria) -> Self {
        let mut c = Criteria::default();
        c.content = vec![kind];
        c
    }

    /// Parse a `criteria` argument string (everything after the command word).
    ///
    /// Accepts the documented grammar. Returns an explicit error for anything
    /// unrecognised, including the two invalid content keywords — never a
    /// silent fallback to the default.
    ///
    /// # The set semantics (measured)
    ///
    /// The default **size+timestamp** pair applies ONLY when no token is given
    /// at all. Naming ANY token clears the set first, and only the tokens that
    /// name a comparison get compared. U4i measured this for every
    /// modifier-shaped token — `timezone:ignore`, `follow-symlinks`,
    /// `attrib:z` and `ignore-unimportant` each reported `same` for a pair
    /// whose size differed by 2048 bytes AND whose timestamp differed by two
    /// hours — and u4d/u4h confirmed it for `ignore-unimportant` on content
    /// that genuinely differs. `criteria size` and `criteria timestamp` each
    /// compare exactly their own test, which is the same rule seen from the
    /// other side.
    pub fn parse(args: &str) -> Result<Self, CriteriaError> {
        let mut c = Criteria::default();
        // An empty criteria string keeps the observed default pair; a non-empty
        // one clears it (see the doc comment).
        let mut content_seen = !args.split_whitespace().next().is_some();
        if !content_seen {
            c.content.clear();
            content_seen = true;
        }
        for token in args.split_whitespace() {
            c.apply_token(token, &mut content_seen)?;
        }
        Ok(c)
    }

    fn apply_token(&mut self, token: &str, content_seen: &mut bool) -> Result<(), CriteriaError> {
        let lower = token.to_ascii_lowercase();

        // `ignore-unimportant` is a modifier: it folds unimportant content
        // differences under a rules-based comparison (u4e/u4f). On its own it
        // names no comparison, so a set consisting of only this token compares
        // nothing (u4i `ignore-unimportant-alone` -> `same` despite differing
        // size and timestamp).
        if lower == "ignore-unimportant" {
            self.ignore_unimportant = true;
            return Ok(());
        }

        // --- the two keywords the Oracle rejects with exit 106 (O) ---
        if lower == "content" || lower == "binary-content" {
            return Err(CriteriaError::InvalidCriteria {
                token: token.to_string(),
                detail: "Beyond Compare rejects this folder-compare criteria \
                         keyword on the command line with exit code 106; \
                         use size, CRC, binary or rules-based"
                    .to_string(),
            });
        }

        if lower == "follow-symlinks" {
            self.follow_symlinks = true;
            return Ok(());
        }

        if let Some(rest) = lower.strip_prefix("attrib:") {
            let set = AttributeSet::parse(rest)
                .map_err(|detail| CriteriaError::InvalidCriteria {
                    token: token.to_string(),
                    detail,
                })?;
            self.attributes = set;
            // Naming an attribute set REPLACES the default size+timestamp pair
            // (`criteria size` semantics): the gate observed the live Oracle
            // judging a timestamp-newer file `same` under `criteria attrib:z`
            // alone, so the quick pair cannot still be in force. A later
            // size/timestamp/CRC token appends on top, as before.
            if !*content_seen {
                self.content.clear();
                *content_seen = true;
            }
            return Ok(());
        }

        if let Some(rest) = lower.strip_prefix("timezone:") {
            self.timezone = parse_timezone(rest, token)?;
            return Ok(());
        }

        if lower == "timestamp" {
            if !*content_seen {
                self.content.clear();
                *content_seen = true;
            }
            self.content.push(ContentCriteria::Timestamp);
            return Ok(());
        }

        if let Some(rest) = lower.strip_prefix("timestamp:") {
            self.timestamp = parse_timestamp_rule(rest, token)?;
            if !*content_seen {
                self.content.clear();
                *content_seen = true;
            }
            if !self.content.contains(&ContentCriteria::Timestamp) {
                self.content.push(ContentCriteria::Timestamp);
            }
            return Ok(());
        }

        if let Some(kind) = ContentCriteria::parse(&lower) {
            if !*content_seen {
                self.content.clear();
                *content_seen = true;
            }
            if !self.content.contains(&kind) {
                self.content.push(kind);
            }
            return Ok(());
        }

        Err(CriteriaError::InvalidCriteria {
            token: token.to_string(),
            detail: "not a criteria keyword Beyond Compare documents".to_string(),
        })
    }

    /// True when evaluating these criteria requires reading file bytes.
    pub fn requires_content_read(&self) -> bool {
        self.content.iter().any(|c| c.requires_content_read())
    }

    /// Round-trip back to a `criteria …` argument string.
    ///
    /// Used by the fixture manifest and by the report's provenance header, so a
    /// run records exactly which criteria produced it.
    ///
    /// An EMPTY criterion list round-trips to the empty string, which is what
    /// selects the default pair on the way back (see [`Criteria::parse`]).
    pub fn to_argument_string(&self) -> String {
        let mut parts: Vec<String> = Vec::new();
        if !self.attributes.is_empty() {
            parts.push(format!("attrib:{}", self.attributes.as_str()));
        }
        for c in &self.content {
            match c {
                ContentCriteria::Timestamp => {
                    if self.timestamp.tolerance_seconds > 0 || self.timestamp.ignore_dst {
                        let mut t = format!("timestamp:{}sec", self.timestamp.tolerance_seconds);
                        if self.timestamp.ignore_dst {
                            t.push_str(";IgnoreDST");
                        }
                        parts.push(t);
                    } else {
                        parts.push("timestamp".to_string());
                    }
                }
                other => parts.push(other.as_str().to_string()),
            }
        }
        match self.timezone {
            TimezoneRule::UseLocalZone => {}
            TimezoneRule::Ignore => parts.push("timezone:ignore".to_string()),
        }
        if self.follow_symlinks {
            parts.push("follow-symlinks".to_string());
        }
        if self.ignore_unimportant {
            parts.push("ignore-unimportant".to_string());
        }
        parts.join(" ")
    }

    /// Which attributes to compare, as a display set.
    pub fn attribute_set(&self) -> AttributeSet {
        self.attributes
    }
}

fn parse_timezone(rest: &str, token: &str) -> Result<TimezoneRule, CriteriaError> {
    if rest == "ignore" {
        return Ok(TimezoneRule::Ignore);
    }
    // The A-3 folder gate observed the live Oracle rejecting every shifted
    // form with exit 106 (`criteria timestamp timezone:left+1` → 106;
    // `A3-folder-gate-serial-01` FINDINGS F3), while `timezone:ignore` is
    // accepted. The help text documents the shift syntax, but the script
    // command does not take it — the Oracle is the authority, so any
    // `left`/`right` form is refused here exactly as the Oracle refuses it.
    for prefix in ["left", "right"] {
        if rest.starts_with(prefix) {
            return Err(CriteriaError::InvalidCriteria {
                token: token.to_string(),
                detail: "the live Oracle rejects timezone:left/right offsets \
                         with exit 106 (only timezone:ignore is accepted)"
                    .to_string(),
            });
        }
    }
    Err(CriteriaError::InvalidCriteria {
        token: token.to_string(),
        detail: "expected `ignore` (the Oracle rejects left/right offsets)".to_string(),
    })
}

/// Parse `[<seconds>sec][;IgnoreDST]` (the part after `timestamp:`).
fn parse_timestamp_rule(rest: &str, token: &str) -> Result<TimestampRule, CriteriaError> {
    let mut rule = TimestampRule::default();
    let mut parts = rest.split(';');
    let first = parts.next().unwrap_or("");
    if !first.is_empty() {
        // Only the documented `Nsec` suffix is accepted. A bare number would be
        // ambiguous in seconds vs minutes, so it is refused rather than guessed.
        let digits = first.strip_suffix("sec").ok_or_else(|| CriteriaError::InvalidCriteria {
            token: token.to_string(),
            detail: "expected `<number>sec` (the `sec` suffix is required)".to_string(),
        })?;
        rule.tolerance_seconds =
            digits
                .parse()
                .map_err(|_| CriteriaError::InvalidCriteria {
                    token: token.to_string(),
                    detail: format!("{digits:?} is not a whole number of seconds"),
                })?;
    }
    for opt in parts {
        if opt.eq_ignore_ascii_case("ignoredst") {
            rule.ignore_dst = true;
        } else if !opt.is_empty() {
            return Err(CriteriaError::InvalidCriteria {
                token: token.to_string(),
                detail: format!("unknown timestamp option {opt:?} (expected IgnoreDST)"),
            });
        }
    }
    Ok(rule)
}

/// Why a criteria specification could not be used.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CriteriaError {
    /// The token is not valid for a folder comparison in BC (observed: exit 106).
    InvalidCriteria { token: String, detail: String },
    /// A real BC feature whose behaviour has not been probed in this workspace.
    ///
    /// Refused rather than approximated, per `04-milestones.md` section 5:
    /// "只实现已对拍的模式，报告中列出未支持项".
    NotProbed { token: String },
}

impl CriteriaError {
    /// The process exit code the Oracle produced for this class of error.
    ///
    /// Observed for the invalid-keyword case: `criteria content` and
    /// `criteria binary-content` both exit **106** (`00-current-state.md`
    /// section 6). `product/verify/README.md` section 3 defines 106 as
    /// "script command error". Reproducing that code keeps the CLI's exit
    /// semantics aligned with the observed Oracle.
    pub fn exit_code(&self) -> i32 {
        match self {
            CriteriaError::InvalidCriteria { .. } => 106,
            // Not observed for this specific case; 106 is the documented
            // "script command error" class that an unrecognised command falls
            // into, and is used here as the closest evidenced value.
            CriteriaError::NotProbed { .. } => 106,
        }
    }
}

impl fmt::Display for CriteriaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CriteriaError::InvalidCriteria { token, detail } => {
                write!(f, "invalid folder-compare criteria {token:?}: {detail}")
            }
            CriteriaError::NotProbed { token } => write!(
                f,
                "criteria {token:?} is documented by Beyond Compare but has not been \
                 probed in this workspace, so it is not implemented"
            ),
        }
    }
}

impl std::error::Error for CriteriaError {}

#[cfg(test)]
mod tests {
    use super::*;
    use reacmp_vfs::Attributes;

    #[test]
    fn default_is_size_plus_timestamp_not_content() {
        // The single most important observed semantic: the default report calls a
        // same-size, same-timestamp, different-content pair `same`.
        let c = Criteria::observed_default();
        assert_eq!(
            c.content,
            vec![ContentCriteria::Size, ContentCriteria::Timestamp]
        );
        assert!(!c.requires_content_read());
        assert_eq!(c.to_argument_string(), "size timestamp");
    }

    #[test]
    fn the_five_observed_keywords_parse() {
        for (text, expected) in [
            ("size", ContentCriteria::Size),
            ("timestamp", ContentCriteria::Timestamp),
            ("CRC", ContentCriteria::Crc),
            ("binary", ContentCriteria::Binary),
            ("rules-based", ContentCriteria::RulesBased),
            ("crc", ContentCriteria::Crc),
            ("RULES-BASED", ContentCriteria::RulesBased),
        ] {
            let c = Criteria::parse(text).unwrap_or_else(|e| panic!("{text}: {e}"));
            assert_eq!(c.content, vec![expected], "{text}");
        }
    }

    #[test]
    fn a_content_keyword_replaces_the_default_pair() {
        // `criteria CRC` alone produced `diff` in the probe, so it must not be
        // evaluated together with the default size+timestamp pair.
        let c = Criteria::parse("CRC").unwrap();
        assert_eq!(c.content, vec![ContentCriteria::Crc]);
        assert!(!c.content.contains(&ContentCriteria::Size));
        assert!(!c.content.contains(&ContentCriteria::Timestamp));
    }

    #[test]
    fn content_and_binary_content_are_invalid_with_exit_106() {
        for bad in ["content", "binary-content", "CONTENT"] {
            let err = Criteria::parse(bad).expect_err(bad);
            assert!(
                matches!(err, CriteriaError::InvalidCriteria { .. }),
                "{bad}: {err:?}"
            );
            assert_eq!(err.exit_code(), 106, "{bad}");
        }
    }

    #[test]
    fn invalid_keywords_are_never_silently_accepted() {
        // A typo must fail, not fall back to the default.
        assert!(Criteria::parse("sizee").is_err());
        assert!(Criteria::parse("--size").is_err());
        assert!(Criteria::parse("timestamp:5min").is_err());
        assert!(Criteria::parse("timezone:left6").is_err());
        assert!(Criteria::parse("timezone:left+13").is_err());
        // `attrib:z` is ACCEPTED, not refused: the live Oracle exits 0 on it
        // (FINDINGS F5); unknown letters are inert, not an error. Only
        // non-letters are still malformed.
        assert!(Criteria::parse("attrib:z").is_ok());
        assert!(Criteria::parse("attrib:1").is_err());
        assert!(Criteria::parse("attrib:").is_ok(), "empty set is the documented default");
    }

    #[test]
    fn the_five_unlocked_criteria_are_accepted_with_measured_semantics() {
        // Previously refused as not-probed; the U4 series measured all five
        // (`probes/U4-FINDINGS.md`). The four content keywords name their own
        // comparison; `ignore-unimportant` is a pure modifier.
        for token in ["version", "owner", "group", "permissions"] {
            let c = Criteria::parse(token).expect(token);
            assert_eq!(c.content.len(), 1, "{token} is the only comparison named");
            assert_eq!(
                c.content[0].as_str().to_ascii_lowercase(),
                token,
                "{token} must be the sole content criterion"
            );
        }
        // `ignore-unimportant` alone names NO comparison, so the set is empty
        // and nothing is compared (u4i `ignore-unimportant-alone` -> `same`
        // despite a 2048-byte size difference and a 2-hour timestamp
        // difference).
        let c = Criteria::parse("ignore-unimportant").unwrap();
        assert!(c.ignore_unimportant);
        assert!(c.content.is_empty(), "a modifier names no comparison");
        // Later size/timestamp tokens add on top (u4f `f-version-plus-size`
        // reports `diff`, `f-owner-plus-size` too).
        let c = Criteria::parse("version size").unwrap();
        assert!(c.content.contains(&ContentCriteria::Version));
        assert!(c.content.contains(&ContentCriteria::Size));
    }

    #[test]
    fn naming_any_token_replaces_the_default_pair() {
        // u4i: every modifier-shaped token clears the default pair.
        for spec in ["timezone:ignore", "follow-symlinks", "attrib:z", "ignore-unimportant"] {
            let c = Criteria::parse(spec).unwrap();
            assert!(
                c.content.is_empty(),
                "{spec} names no comparison, so the default pair must not survive"
            );
        }
        // A content keyword compares exactly itself.
        let c = Criteria::parse("size").unwrap();
        assert_eq!(c.content, vec![ContentCriteria::Size]);
        let c = Criteria::parse("timestamp").unwrap();
        assert_eq!(c.content, vec![ContentCriteria::Timestamp]);
        // No criteria at all is the only way to get the default pair.
        let c = Criteria::parse("").unwrap();
        assert_eq!(c.content, vec![ContentCriteria::Size, ContentCriteria::Timestamp]);
    }

    #[test]
    fn posix_metadata_criteria_are_flagged_inert_on_windows() {
        for token in ["owner", "group", "permissions"] {
            let c = Criteria::parse(token).unwrap();
            assert!(c.content[0].is_posix_metadata(), "{token}");
        }
        assert!(!ContentCriteria::Version.is_posix_metadata());
        assert!(ContentCriteria::Version.requires_content_read());
    }

    #[test]
    fn argument_round_trip_includes_the_new_criteria() {
        for spec in [
            "version",
            "version size",
            "owner",
            "group",
            "permissions",
            "ignore-unimportant",
            "rules-based ignore-unimportant",
        ] {
            let c = Criteria::parse(spec).unwrap();
            let back = Criteria::parse(&c.to_argument_string()).unwrap();
            assert_eq!(back, c, "{spec} did not round-trip through {:?}", c.to_argument_string());
        }
    }

    #[test]
    fn timestamp_tolerance_parses_and_matches() {
        let c = Criteria::parse("timestamp:2sec").unwrap();
        assert_eq!(c.timestamp.tolerance_seconds, 2);
        assert!(c.content.contains(&ContentCriteria::Timestamp));

        let base = reacmp_vfs::Timestamp::from_unix_seconds(1_000_000);
        assert!(c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(1_000_002)));
        assert!(!c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(1_000_003)));

        // The boundary value itself is inside the tolerance.
        assert!(c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(999_998)));
    }

    #[test]
    fn ignore_dst_matches_exactly_one_hour_only() {
        let c = Criteria::parse("timestamp:0sec;IgnoreDST").unwrap();
        assert!(c.timestamp.ignore_dst);
        let base = reacmp_vfs::Timestamp::from_unix_seconds(1_000_000);
        assert!(c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(1_003_600)));
        assert!(c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(996_400)));
        // Exactly two hours is not "exactly 1 hour".
        assert!(!c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(1_007_200)));
        // And neither is 1 hour + 1 second.
        assert!(!c.timestamp.matches(base, reacmp_vfs::Timestamp::from_unix_seconds(1_003_601)));
    }

    #[test]
    fn timestamp_rule_round_trips_through_the_argument_string() {
        let c = Criteria::parse("attrib:shr timestamp:2sec;IgnoreDST timezone:ignore follow-symlinks").unwrap();
        assert_eq!(c.attributes.as_str(), "shr");
        assert_eq!(c.timestamp.tolerance_seconds, 2);
        assert!(c.timestamp.ignore_dst);
        assert!(c.follow_symlinks);
        assert_eq!(c.timezone, TimezoneRule::Ignore);
        let text = c.to_argument_string();
        let again = Criteria::parse(&text).unwrap();
        assert_eq!(again, c, "round trip via {text:?}");
    }

    #[test]
    fn timezone_shift_forms_are_rejected_like_the_live_oracle_rejects_them() {
        // The A-3 folder gate measured the live Oracle exiting 106 for every
        // shifted timezone form (FINDINGS F3), while `timezone:ignore` is
        // accepted (`tz-ignore` case).
        for bad in ["left+1", "left-1", "right+2", "right-2", "left6", "left-13"] {
            let err = Criteria::parse(&format!("timestamp timezone:{bad}")).unwrap_err();
            assert!(matches!(err, CriteriaError::InvalidCriteria { .. }), "{bad}: {err:?}");
        }
        let c = Criteria::parse("timestamp timezone:ignore").unwrap();
        assert_eq!(c.timezone, TimezoneRule::Ignore);
        assert_eq!(c.timezone.offsets_seconds(), (0, 0));
    }

    #[test]
    fn criteria_round_trip_reparses_identically() {
        for text in [
            "",
            "size",
            "timestamp",
            "CRC",
            "binary",
            "rules-based",
            "size timestamp",
            "CRC follow-symlinks",
            "attrib:sh size",
            "timestamp:10sec",
            "timestamp:1sec;IgnoreDST",
            "timezone:ignore CRC",
        ] {
            let c = Criteria::parse(text).unwrap_or_else(|e| panic!("{text:?}: {e}"));
            let rendered = c.to_argument_string();
            let again = Criteria::parse(&rendered).unwrap_or_else(|e| panic!("{rendered:?}: {e}"));
            assert_eq!(again, c, "text={text:?} rendered={rendered:?}");
        }
    }

    #[test]
    fn requires_content_read_matches_the_documented_split() {
        assert!(!Criteria::from_content(ContentCriteria::Size).requires_content_read());
        assert!(!Criteria::from_content(ContentCriteria::Timestamp).requires_content_read());
        assert!(Criteria::from_content(ContentCriteria::Crc).requires_content_read());
        assert!(Criteria::from_content(ContentCriteria::Binary).requires_content_read());
        assert!(Criteria::from_content(ContentCriteria::RulesBased).requires_content_read());
    }

    #[test]
    fn attribute_criteria_parses_the_documented_letters() {
        let c = Criteria::parse("attrib:shr").unwrap();
        assert_eq!(c.attributes.as_str(), "shr");
        // `shr` names three of the four letters; `as hr` alone is not ALL.
        assert_eq!(
            c.attribute_set(),
            AttributeSet(AttributeSet::SYSTEM | AttributeSet::HIDDEN | AttributeSet::READ_ONLY)
        );
        assert_eq!(Criteria::parse("attrib:ashr").unwrap().attributes, AttributeSet::ALL);
        // `attributes` defaults to "compare nothing about attributes".
        assert!(Criteria::observed_default().attributes.is_empty());
    }

    #[test]
    fn attributes_unknown_does_not_match_a_named_set() {
        // A backend with no DOS attributes must not report "attributes equal".
        let set = AttributeSet::parse("r").unwrap();
        assert_eq!(Attributes::unknown().contains_all(set), None);
    }
}

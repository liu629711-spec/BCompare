//! The `filter` mask engine behind `<filters>` (M4 task B).
//!
//! # What the Oracle does (O)
//!
//! `product/verify/probes/U5-FINDINGS.md` §3, from the u5c/u5d/u5g/u5h/u5i
//! probe runs. The evidence used below is the *raw report XML*, because the
//! findings table and this implementation disagree about one mask shape (see
//! "The `sub\` reading" below).
//!
//! | script | observable result | evidence |
//! |---|---|---|
//! | `filter "*.txt"` | only `*.txt` **file** rows; every folder row kept, aggregates unchanged | u5c `filter-include-txt` |
//! | `filter "-*.txt"` | every file row except `*.txt`; folder rows kept | u5c `filter-exclude-txt` |
//! | `filter "d?.bin"` | `d1.bin` kept; `?` is a single-character wildcard | u5d `filter-question` |
//! | `filter "*.txt;*.TXT;-b.log"` | include list + exclude list together | u5d `filter-list-mixed` |
//! | `filter "*.nomatch"` | **no** file row survives, every folder row survives *with its aggregate size* | u5c `filter-match-nothing`, u5g s7 |
//! | `filter "-A\\"` | the folder `A` **and its whole subtree** disappear, with and without `expand all` | u5h `fg-exclude-A-expandall` / `-noexp` |
//! | `filter "sub\\"` | the folder `other` disappears; **every file row survives**, including the top-level ones | u5d `filter-folder-only` (folders `sub`, `deep`; files `f.txt`, `e.txt`, `a.txt`, `b.log`, `c.TXT`, `d1.bin`) |
//! | `filter "*.TXT"` | matches `a.txt` and `c.TXT` — case-insensitive | u5d `filter-upper-txt` |
//! | mask matching a nested file | `*.TXT` matches `sub/e.txt` and `sub/deep/f.txt` — a bare name mask applies at **any depth** | u5d `filter-upper-txt` |
//! | `filter` twice | the **last** `filter` wins (`<filters>*.log</filters>`, only `b.log` left) | u5i `xml-filter-twice` |
//! | `filter` + `expand` order | irrelevant (`u5g` s7 == s8) | u5g s7/s8 |
//! | folder aggregate vs filter | a folder keeps the aggregate of **all** its files, visible or not | u5c `filter-include-txt` (`sub` = 8 with only its 4-byte `c.txt` visible), u5g s7 (`A=10` with no file rows) |
//! | file mask vs folders | `*.TXT` leaves the `other` folder row and removes only its file | u5d `filter-upper-txt` (`other` present, `g.log` absent) |
//!
//! # The model these facts imply
//!
//! BC keeps **two independent mask lists** — file masks and folder masks — and
//! the trailing backslash is what marks a folder mask
//! (`help/scripting_reference.html`, FILTER: "To indicate that a mask affects
//! folders use a trailing backslash"). Each list has its own effect:
//!
//! * **Files** — if any file include mask exists, a file must match one; a file
//!   exclude mask always wins (the help text: "Include a minus sign (-) in front
//!   of files to be excluded"). A file mask never removes a folder row, which is
//!   why `*.TXT` leaves `other` in place but removes `other/g.log`.
//! * **Folders** — a folder exclude mask removes the folder *and prunes its whole
//!   subtree* (u5h `-A\`). If any folder **include** mask exists, a folder
//!   survives only when it matches one, is inside one, or is an ancestor that the
//!   path leads through; that is what removes `other` for `sub\` while keeping
//!   `sub` and its nested `deep`.
//!
//! # The `sub\` reading (a correction to `U5-FINDINGS.md` §3)
//!
//! `U5-FINDINGS.md` §3 states that `filter "sub\"` "只保留该文件夹及其内容"
//! (keeps only that folder and its contents). The raw report is narrower than
//! that: u5d `filter-folder-only` keeps `sub` and `sub/deep` — and ALSO every
//! file OUTSIDE `sub` (`a.txt`, `b.log`, `c.TXT`, `d1.bin`). So a folder include
//! mask restricts **folder rows only**; it does not hide files the way a file
//! include mask does. That is the reading implemented here, and it is the only
//! one the artifacts support.
//!
//! # What is deliberately not implemented
//!
//! Non-name filter forms (`filter cutoff:`, `filter size:`, `filter attrib:`,
//! `filter exclude-protected`, `filter include-protected`, `filter unixtype:`)
//! are **refused by name** in the executor (exit 106) rather than ignored —
//! `product/docs/09-m4-interfaces.md` §5.
//!
//! # One inference, marked
//!
//! `raw()` is the text the report echoes, and the **caller** (the executor)
//! writes it through the report writer's XML escaping. No mask in the whole u5
//! corpus contains a character that needs escaping — every one of the 19
//! captured `<filters>` elements holds only letters, digits, `.`, `*`, `?`, `;`,
//! `-` and `\` — so whether the Oracle escapes a mask is **unobserved**. The
//! writer escapes `&`, `<` and `>` because an unescaped `<` would make the report
//! unparseable and the harness parses it with `ElementTree`; that is an
//! engineering necessity, not a measurement, and it is recorded here rather than
//! presented as parity.
//!
//! The masks that DO carry a backslash matter for a different reason: the
//! script spells a folder mask as `"sub\\"`, and the Oracle echoes the doubled
//! form into `<filters>sub\\</filters>`. What this module must therefore NOT do
//! is normalise the raw text — matching normalises a copy, `raw()` stays
//! verbatim. The one contract this depends on is the frozen AST's, which keeps
//! `Command::Filter::masks` raw for exactly this reason (`ast.rs`: "Kept raw
//! because the report echoes it verbatim in `<filters>`"). Matching tolerates
//! either spelling (`-A\` and `-A\\` both name folder `A`), so only the echo
//! follows the AST.

/// One side of a parsed mask set.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Filter {
    /// The mask text exactly as the script wrote it (for `<filters>`).
    raw: Option<String>,
    file_include: Vec<String>,
    file_exclude: Vec<String>,
    /// Parsed but currently inert — see the module comment.
    folder_include: Vec<String>,
    folder_exclude: Vec<String>,
}

impl Filter {
    /// The "no filter" value: every row is visible and no `<filters>` element
    /// is written.
    pub fn none() -> Filter {
        Filter::default()
    }

    /// Parse a mask string. Never fails: an unrecognised mask is still a mask
    /// (`*` and `?` are the whole grammar), so there is nothing to reject.
    pub fn parse(raw: &str) -> Filter {
        let mut f = Filter {
            raw: Some(raw.to_string()),
            ..Filter::default()
        };
        for piece in raw.split(';') {
            let piece = piece.trim();
            if piece.is_empty() {
                continue;
            }
            let (exclude, body) = match piece.strip_prefix('-') {
                Some(rest) => (true, rest),
                None => (false, piece),
            };
            if body.is_empty() {
                continue;
            }
            let is_folder = body.ends_with('\\') || body.ends_with('/');
            // The Observed masks spell a folder mask with a doubled
            // backslash inside the script (`filter "-A\\"`), which the XML
            // echoes verbatim as `-A\\`, so the trailing separator handling
            // must strip ALL of them: the mask the Oracle acts on for `-A\\`
            // is the folder `A` (u5h).
            let pattern = crate::expand::normalise(body);
            if pattern.is_empty() {
                continue;
            }
            match (is_folder, exclude) {
                (true, true) => f.folder_exclude.push(pattern),
                (true, false) => f.folder_include.push(pattern),
                (false, true) => f.file_exclude.push(pattern),
                (false, false) => f.file_include.push(pattern),
            }
        }
        f
    }

    /// True when at least one mask was given, i.e. when the report writes
    /// `<filters>` (u5i).
    pub fn is_set(&self) -> bool {
        !(self.file_include.is_empty()
            && self.file_exclude.is_empty()
            && self.folder_include.is_empty()
            && self.folder_exclude.is_empty())
    }

    /// The raw mask text, exactly as written (an empty mask list has no text).
    pub fn raw(&self) -> Option<&str> {
        if self.is_set() {
            self.raw.as_deref()
        } else {
            None
        }
    }

    /// True when a **file** row survives the masks.
    pub fn file_visible(&self, name: &str, relative: &str) -> bool {
        if self.matches(&self.file_exclude, name, relative) {
            return false;
        }
        if self.file_include.is_empty() {
            return true;
        }
        self.matches(&self.file_include, name, relative)
    }

    /// True when a **directory** row survives the masks.
    ///
    /// Three cases, from u5d `filter-folder-only` / u5h `fg-exclude-A-*`:
    ///
    /// * a folder exclude mask that matches removes it (and its subtree);
    /// * when a folder include mask exists, a folder survives if it matches one,
    ///   lies **inside** one (matching a prefix of its relative path — that is
    ///   what keeps `sub/deep` for `sub\`), or is an **ancestor** of one (which
    ///   is what keeps the path to a named folder visible);
    /// * with no folder include mask, nothing removes a folder but the exclude
    ///   list.
    pub fn folder_visible(&self, name: &str, relative: &str) -> bool {
        if self.folder_removed(name, relative) {
            return false;
        }
        if self.folder_include.is_empty() {
            return true;
        }
        let rel = crate::expand::normalise(relative);
        self.folder_include.iter().any(|p| {
            // The folder itself.
            glob_match(p, &rel)
                || glob_match(p, name)
                // A folder INSIDE a named folder: `sub\` keeps `sub\deep`.
                || is_under(&rel, p)
                // The path TO a named folder: `sub\deep\` keeps `sub`.
                || is_under(p, &rel)
        })
    }

    /// True when a **directory** row was removed by a folder mask, in which case
    /// its whole subtree also goes (u5h `-A\`).
    pub fn folder_removed(&self, name: &str, relative: &str) -> bool {
        self.matches(&self.folder_exclude, name, relative)
    }

    /// Folder include masks, as parsed (`sub` for the script's `sub\`).
    pub fn folder_includes(&self) -> &[String] {
        &self.folder_include
    }

    /// True when any mask matches this item.
    ///
    /// A mask that contains a separator is matched against the item's relative
    /// path; a bare mask is matched against its **name at any depth**, which is
    /// what u5d `filter-upper-txt` shows (`*.TXT` matches `sub/deep/f.txt`).
    /// Both sides are normalised and compared case-insensitively.
    fn matches(&self, patterns: &[String], name: &str, relative: &str) -> bool {
        if patterns.is_empty() {
            return false;
        }
        let rel = crate::expand::normalise(relative);
        for p in patterns {
            if p.contains('\\') {
                if glob_match(p, &rel) {
                    return true;
                }
            } else if glob_match(p, name) {
                return true;
            }
        }
        false
    }
}

/// Case-insensitive `*`/`?` glob matching (the whole mask grammar the probes
/// exercised: `*`, `?`, and literals).
///
/// `*` spans any characters, including a separator. No probe in this workspace
/// uses a wildcard across a path separator, so the choice is recorded here as
/// **unobserved** rather than presented as a measurement.
fn glob_match(pattern: &str, text: &str) -> bool {
    let p: Vec<char> = pattern.to_lowercase().chars().collect();
    let t: Vec<char> = text.to_lowercase().chars().collect();
    let (mut pi, mut ti) = (0usize, 0usize);
    // Backtracking state for the most recent `*`.
    let (mut star_p, mut star_t): (Option<usize>, usize) = (None, 0);
    while ti < t.len() {
        if pi < p.len() && (p[pi] == '?' || p[pi] == t[ti]) {
            pi += 1;
            ti += 1;
        } else if pi < p.len() && p[pi] == '*' {
            star_p = Some(pi);
            star_t = ti;
            pi += 1;
        } else if let Some(sp) = star_p {
            // Let the last `*` consume one more character.
            pi = sp + 1;
            star_t += 1;
            ti = star_t;
        } else {
            return false;
        }
    }
    while pi < p.len() && p[pi] == '*' {
        pi += 1;
    }
    pi == p.len()
}

/// True when `inner` is a proper descendant path of `outer` (`A\B` is under
/// `A`; `AB` is not).
fn is_under(inner: &str, outer: &str) -> bool {
    let outer = outer.to_lowercase();
    let inner = inner.to_lowercase();
    inner
        .strip_prefix(&outer)
        .map(|rest| rest.starts_with('\\'))
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn no_masks_means_no_filter_element_and_everything_visible() {
        for raw in ["", "  ", ";;"] {
            let f = Filter::parse(raw);
            assert!(!f.is_set(), "{raw:?}");
            assert_eq!(f.raw(), None);
            assert!(f.file_visible("a.txt", "sub\\a.txt"));
            assert!(f.folder_visible("sub", "sub"));
        }
        assert!(!Filter::none().is_set());
    }

    #[test]
    fn include_file_mask_keeps_only_matching_files_at_any_depth() {
        // u5c filter-include-txt and u5d filter-upper-txt.
        let f = Filter::parse("*.txt");
        assert!(f.is_set());
        assert_eq!(f.raw(), Some("*.txt"));
        assert!(f.file_visible("a.txt", "a.txt"));
        assert!(f.file_visible("e.txt", "sub\\e.txt"));
        assert!(f.file_visible("f.txt", "sub\\deep\\f.txt"));
        assert!(!f.file_visible("b.log", "b.log"));
        assert!(!f.file_visible("d.log", "sub\\d.log"));
        // A file mask never removes a folder (u5c keeps both `sub` rows, and
        // u5d keeps `other` while dropping its `g.log`).
        assert!(f.folder_visible("sub", "sub"));
        assert!(f.folder_visible("other", "other"));
    }

    #[test]
    fn include_mask_is_case_insensitive() {
        // u5d filter-upper-txt: `*.TXT` matches `a.txt` and `c.TXT`.
        let f = Filter::parse("*.TXT");
        assert!(f.file_visible("a.txt", "a.txt"));
        assert!(f.file_visible("c.TXT", "c.TXT"));
        assert!(!f.file_visible("b.log", "b.log"));
    }

    #[test]
    fn question_mark_is_a_single_character_wildcard() {
        // u5d filter-question: `d?.bin` matches `d1.bin`.
        let f = Filter::parse("d?.bin");
        assert!(f.file_visible("d1.bin", "d1.bin"));
        assert!(!f.file_visible("d12.bin", "d12.bin"));
        assert!(!f.file_visible("d.bin", "d.bin"));
    }

    #[test]
    fn exclude_file_mask_wins_and_needs_no_include_list() {
        // u5c filter-exclude-txt.
        let f = Filter::parse("-*.txt");
        assert!(!f.file_visible("a.txt", "a.txt"));
        assert!(!f.file_visible("c.txt", "sub\\c.txt"));
        assert!(f.file_visible("b.log", "b.log"));
        assert!(f.file_visible("d1.bin", "d1.bin"));
        assert!(f.folder_visible("sub", "sub"));
        assert!(f.folder_visible("other", "other"));
    }

    #[test]
    fn a_mixed_list_applies_includes_then_excludes() {
        // u5d filter-list-mixed: `*.txt;*.TXT;-b.log`.
        let f = Filter::parse("*.txt;*.TXT;-b.log");
        assert!(f.file_visible("a.txt", "a.txt"));
        assert!(f.file_visible("c.TXT", "c.TXT"));
        assert!(f.file_visible("e.txt", "sub\\e.txt"));
        assert!(!f.file_visible("b.log", "b.log"));
        assert!(!f.file_visible("d1.bin", "d1.bin"));
        assert!(!f.file_visible("g.log", "other\\g.log"));
    }

    #[test]
    fn exclude_folder_mask_removes_the_whole_subtree() {
        // u5h `-A\\` (the script doubles the separator; the mask acts on `A`).
        for raw in ["-A\\", "-A\\\\", "-A/"] {
            let f = Filter::parse(raw);
            assert!(f.is_set(), "{raw}");
            assert_eq!(f.raw(), Some(raw), "the raw text is echoed verbatim");
            assert!(f.folder_removed("A", "A"), "{raw}");
            // The subtree is pruned by the caller, which never descends into a
            // removed folder; the mask itself only answers for the folder row.
            assert!(!f.folder_removed("B", "A\\B"), "{raw}");
            // A folder mask says nothing about FILE rows: u5h
            // `fg-exclude-A-noexp` keeps `h.txt`.
            assert!(f.file_visible("h.txt", "h.txt"), "{raw} must not hide files");
        }
    }

    #[test]
    fn a_folder_include_mask_restricts_folder_rows_only() {
        // u5d `filter-folder-only` (`sub\\`) against the u5d tree: folders `sub`
        // and `sub/deep` survive, `other` is gone, and EVERY file row survives
        // — including the ones outside `sub` (a.txt, b.log, c.TXT, d1.bin).
        let f = Filter::parse("sub\\\\");
        assert!(f.is_set());
        assert_eq!(f.folder_includes(), ["sub"]);

        assert!(f.folder_visible("sub", "sub"));
        assert!(f.folder_visible("deep", "sub\\deep"));
        assert!(!f.folder_visible("other", "other"), "other is not under sub");

        for (name, rel) in [
            ("a.txt", "a.txt"),
            ("b.log", "b.log"),
            ("c.TXT", "c.TXT"),
            ("d1.bin", "d1.bin"),
            ("e.txt", "sub\\e.txt"),
            ("f.txt", "sub\\deep\\f.txt"),
            ("g.log", "other\\g.log"),
        ] {
            assert!(f.file_visible(name, rel), "{rel} survives a folder mask");
        }
    }

    #[test]
    fn a_folder_include_mask_keeps_the_path_to_the_named_folder() {
        // The path THROUGH a folder tree must stay visible, or a nested folder
        // mask would be unusable: `sub\deep\` keeps `sub` so `deep` can be
        // reached.
        let f = Filter::parse("sub\\deep\\\\");
        assert!(f.folder_visible("sub", "sub"));
        assert!(f.folder_visible("deep", "sub\\deep"));
        assert!(!f.folder_visible("other", "other"));
        assert!(!f.folder_visible("deeper", "sub\\deeper"));
    }

    #[test]
    fn a_file_mask_never_removes_a_folder_row() {
        // u5d `filter-upper-txt`: `*.TXT` leaves the `other` folder row and
        // removes only its file.
        let f = Filter::parse("*.TXT");
        assert!(f.folder_visible("other", "other"));
        assert!(f.folder_visible("sub", "sub"));
        assert!(f.folder_visible("deep", "sub\\deep"));
        assert!(!f.file_visible("g.log", "other\\g.log"));
        assert!(f.file_visible("a.txt", "a.txt"));
        assert!(f.file_visible("c.TXT", "c.TXT"));
        assert!(f.file_visible("e.txt", "sub\\e.txt"));
        assert!(f.file_visible("f.txt", "sub\\deep\\f.txt"));
    }

    #[test]
    fn a_mask_with_separators_matches_the_relative_path() {
        let f = Filter::parse("sub\\deep\\f.txt");
        assert!(f.file_visible("f.txt", "sub\\deep\\f.txt"));
        assert!(!f.file_visible("f.txt", "sub\\f.txt"));
        // The same mask spelled with forward slashes names the same file: the
        // separator normalisation is the one `expand` uses (u5h).
        let g = Filter::parse("sub/deep/f.txt");
        assert!(g.file_visible("f.txt", "sub\\deep\\f.txt"));
    }

    #[test]
    fn glob_backtracking_handles_multiple_stars() {
        assert!(glob_match("*a*b*", "xxaxxbxx"));
        assert!(glob_match("*", "anything"));
        assert!(glob_match("", ""));
        assert!(!glob_match("", "x"));
        assert!(glob_match("a*", "a"));
        assert!(!glob_match("a*b", "a"));
        assert!(glob_match("**", ""));
    }
}

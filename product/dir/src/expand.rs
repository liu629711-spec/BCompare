//! The `expand` policy: which directories a report descends into, and which
//! therefore show an **aggregate** `<size>` (M4 task B).
//!
//! # The measured rule (O)
//!
//! `product/verify/probes/U5-FINDINGS.md` §4, from the u5g/u5h/u5j probe series
//! (`product/verify/runs/u5g-probe-*`, `u5h-probe-*`, `u5j-probe-*`):
//!
//! | directory row | `<size>` |
//! |---|---|
//! | its whole subtree is expanded | the sum of the file bytes in that subtree, per side |
//! | anything below it is still collapsed | `<size/>` (self-closing) |
//!
//! The fixture tree of u5g is `A/B/f.txt(6)`, `A/g.txt(4)`, `C/i.txt(3)`,
//! `h.txt(5)`, and the measured rows are:
//!
//! | script | `A` | `B` | `C` |
//! |---|---|---|---|
//! | no `expand` | `<size/>` | *(no row)* | `<size/>` |
//! | `expand all` | `10` | `6` | `3` |
//! | `expand "A"` | `<size/>` | `<size/>` | `<size/>` |
//! | `expand "A\B"` | `10` | `6` | `<size/>` |
//! | `expand "A"` then `expand "C"` | `<size/>` | `<size/>` | `3` |
//!
//! Three facts from those rows drive this module:
//!
//! 1. **A named path expands that directory one level, and expands every
//!    ancestor on the way to it.**  `expand "A\B"` renders `A`'s children
//!    (`B` and `g.txt`) *and* `B`'s child (`f.txt`), while `expand "A"` renders
//!    only `A`'s children — so `A` is expanded in both cases, and `B` in the
//!    second only.
//! 2. **Expansion is cumulative**: `expand "A"` then `expand "A\B"` expands
//!    both (`u5g` s5); `expand "A"` then `expand "C"` expands both (s6).
//! 3. **The aggregate is a property of the whole subtree, not of the policy**:
//!    `expand "A"` leaves `A` at `<size/>` *because `A` contains the
//!    subdirectory `B`, which is not expanded*, while `expand "C"` gives `C`
//!    the aggregate `3` *because `C` contains only files* (u5g s3 vs s6), and
//!    u5j `A-expand-d` gives `d` the aggregate `5/9` for the same reason.
//!
//! Fact 3 has a consequence the frozen interface in
//! `product/docs/09-m4-interfaces.md` §3.3 does not spell out: **no function of
//! the policy and a relative path alone can answer "is this subtree fully
//! expanded"**, because two directories with identical policies and identical
//! relative paths have different answers depending on their contents.  The
//! engine therefore computes the answer while walking the tree
//! (`tree.rs`: [`crate::tree::DirState::fully_expanded`]) and this module
//! exposes:
//!
//! * [`ExpandPolicy::is_expanded`] — the recursion control ("does this
//!   directory's child rows appear at all"), which *is* a function of the
//!   policy and the path;
//! * [`ExpandPolicy::fully_expanded_given`] — the bottom-up rule the engine
//!   applies for each directory once its child directories are known;
//! * [`ExpandPolicy::fully_expanded`] — the policy-only projection, which is
//!   the correct answer for a directory that has **no subdirectories** (the
//!   `expand "C"` and u5j `expand "d"` shapes) and for the `All`/`None`
//!   policies.  It is what a caller with no tree to offer can honestly ask.

/// Which folders a report descends into.
///
/// The default is [`ExpandPolicy::All`], which is the M3 behaviour (the folder
/// engine always recursed) and keeps the existing folder gate byte-identical
/// (`04-milestones.md` M4 regression clause).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub enum ExpandPolicy {
    /// Nothing expanded: every directory row is `<size/>` and carries no child
    /// rows at all (u5g s1/u5j `*-noexpand`).  The root's own level is always
    /// listed — an unexpanded report is not an empty one.
    None,
    /// Everything expanded (the M3 behaviour, and `expand all`).
    #[default]
    All,
    /// Only the listed relative paths, plus every ancestor of each of them, are
    /// expanded (u5g s3..s6, u5h `expand-forward-slash` / `-trailing-sep`).
    Only(Vec<String>),
}

impl ExpandPolicy {
    /// Normalise the paths a script's `expand "<p>"` names.
    ///
    /// Observed (u5h): `A\B`, `A/B` and a trailing separator (`expand "A\"`)
    /// all name the same folder, so the separator is normalised to the
    /// comparison's own (`\`), a trailing separator is dropped, and a repeated
    /// separator is collapsed.  Leading separators are dropped for the same
    /// reason (a relative path has no leading separator; `expand "\A"` is
    /// unobserved and this is the reading that keeps it meaningful).
    ///
    /// Paths are compared case-insensitively on Windows, like every other name
    /// in this product (the filter probes measure case-insensitivity for
    /// masks: U5-FINDINGS §3).
    pub fn parse_paths(paths: &[String]) -> Vec<String> {
        let mut out: Vec<String> = Vec::with_capacity(paths.len());
        for raw in paths {
            let normalised = normalise(raw);
            if normalised.is_empty() {
                // `expand ""` (or `expand "\"`) names the base folder, which is
                // always expanded; keeping it would only add a no-op entry.
                continue;
            }
            if !out
                .iter()
                .any(|p: &String| p.eq_ignore_ascii_case(&normalised))
            {
                out.push(normalised);
            }
        }
        out
    }

    /// True when this directory's **child rows** are present.
    ///
    /// The base folder (`""`) is always expanded: the no-`expand` probes still
    /// list the top level (u5g s1 shows `A`, `C` and `h.txt`).
    pub fn is_expanded(&self, relative: &str) -> bool {
        let path = normalise(relative);
        match self {
            ExpandPolicy::All => true,
            ExpandPolicy::None => path.is_empty(),
            ExpandPolicy::Only(paths) => {
                if path.is_empty() {
                    return true;
                }
                paths.iter().any(|named| {
                    named.eq_ignore_ascii_case(&path) || is_strict_ancestor(&path, named)
                })
            }
        }
    }

    /// The answer for a directory whose subtree contains **no further
    /// directories** — see the module comment for why the general question
    /// needs the tree.
    ///
    /// * `All` — `true`: everything below is expanded by definition.
    /// * `None` — `false`: nothing is expanded, so no subtree is complete.
    /// * `Only(paths)` — `is_expanded(relative)`, which is correct exactly when
    ///   there is nothing below to leave collapsed (u5g s6 `C=3`,
    ///   u5j `A-expand-d` `d=5/9`).
    pub fn fully_expanded(&self, relative: &str) -> bool {
        match self {
            ExpandPolicy::All => true,
            ExpandPolicy::None => false,
            ExpandPolicy::Only(_) => self.is_expanded(relative),
        }
    }

    /// The bottom-up rule the engine applies for one directory, given whether
    /// **every child directory below it is itself fully expanded**.
    ///
    /// `expand "A\B"` → `fully_expanded_given("A", true) == true` (u5g s4:
    /// `A=10`), `expand "A"` → `fully_expanded_given("A", false) == false`
    /// (u5g s3: `A=<size/>`), and any directory that is not expanded at all is
    /// never fully expanded (it has rows nobody can see).
    pub fn fully_expanded_given(
        &self,
        relative: &str,
        all_child_dirs_fully_expanded: bool,
    ) -> bool {
        self.is_expanded(relative) && all_child_dirs_fully_expanded
    }

    /// Add the paths of another `expand` command (measured: repeated `expand`
    /// accumulates, u5g s5/s6).  `All` absorbs everything.
    pub fn accumulate(&self, paths: &[String]) -> ExpandPolicy {
        match self {
            ExpandPolicy::All => ExpandPolicy::All,
            ExpandPolicy::None => ExpandPolicy::Only(ExpandPolicy::parse_paths(paths)),
            ExpandPolicy::Only(existing) => {
                let mut union = existing.clone();
                for p in ExpandPolicy::parse_paths(paths) {
                    if !union.iter().any(|q| q.eq_ignore_ascii_case(&p)) {
                        union.push(p);
                    }
                }
                ExpandPolicy::Only(union)
            }
        }
    }

    /// The named paths, for diagnostics and for `<filters>`-style provenance.
    /// Empty for `None`; `None` (the `Option`) for `All`, whose path set is
    /// unbounded.
    pub fn named_paths(&self) -> Option<&[String]> {
        match self {
            ExpandPolicy::All => None,
            ExpandPolicy::None => Some(&[]),
            ExpandPolicy::Only(paths) => Some(paths),
        }
    }
}

/// Normalise one path: `\`-separated, no leading/trailing/duplicate
/// separators.  Public because the executor normalises a script path before it
/// asks whether that path exists in the loaded tree.
pub fn normalise(path: &str) -> String {
    let unified = path.trim().replace('/', "\\");
    let mut out = String::with_capacity(unified.len());
    for component in unified.split('\\') {
        let component = component.trim_end_matches(['\\']);
        if component.is_empty() {
            continue;
        }
        if !out.is_empty() {
            out.push('\\');
        }
        out.push_str(component);
    }
    out
}

/// True when `path` is a proper ancestor of `named` (`A` is an ancestor of
/// `A\B`, and not of `AB`).
fn is_strict_ancestor(path: &str, named: &str) -> bool {
    let named = named.to_lowercase();
    let path = path.to_lowercase();
    named
        .strip_prefix(&path)
        .map(|rest| rest.starts_with('\\'))
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn only(paths: &[&str]) -> ExpandPolicy {
        ExpandPolicy::Only(ExpandPolicy::parse_paths(
            &paths.iter().map(|s| s.to_string()).collect::<Vec<_>>(),
        ))
    }

    #[test]
    fn default_is_all_which_is_the_m3_behaviour() {
        assert_eq!(ExpandPolicy::default(), ExpandPolicy::All);
        assert!(ExpandPolicy::default().is_expanded("anything"));
        assert!(ExpandPolicy::default().fully_expanded("anything"));
    }

    #[test]
    fn parse_paths_normalises_separators_and_trailing_separators() {
        let got = ExpandPolicy::parse_paths(&[
            "A\\B".to_string(),
            "A/B".to_string(),
            "A\\".to_string(),
            "C".to_string(),
            "A\\\\B".to_string(),
            "  D  ".to_string(),
        ]);
        // `A\B`, `A/B` and `A\\B` are one path; the duplicate is dropped in
        // first-seen order; trailing/leading whitespace is trimmed.
        assert_eq!(got, vec!["A\\B", "A", "C", "D"]);
    }

    #[test]
    fn parse_paths_drops_the_base_folder_and_keeps_order() {
        assert!(ExpandPolicy::parse_paths(&["".to_string(), "\\".to_string()]).is_empty());
        let got = ExpandPolicy::parse_paths(&["b".to_string(), "A".to_string()]);
        assert_eq!(got, vec!["b", "A"]);
        // Deduplication ignores case, matching the platform's name rules.
        let got = ExpandPolicy::parse_paths(&["A".to_string(), "a".to_string()]);
        assert_eq!(got, vec!["A"]);
    }

    #[test]
    fn none_expands_only_the_top_level() {
        let p = ExpandPolicy::None;
        assert!(p.is_expanded(""), "the base folder always lists its children");
        assert!(!p.is_expanded("A"));
        assert!(!p.fully_expanded("A"));
        // u5g s1: A=<size/>, C=<size/>, no child rows.
        assert!(p.named_paths().unwrap().is_empty());
    }

    #[test]
    fn a_named_path_expands_itself_and_its_ancestors() {
        let p = only(&["A\\B"]);
        // u5g s4: A's children are rendered, so A is expanded too.
        assert!(p.is_expanded("A"));
        assert!(p.is_expanded("A\\B"));
        assert!(!p.is_expanded("C"));
        assert!(!p.is_expanded("A\\B\\C"), "nothing below a named path is implied");
        // Path spelling does not matter (u5h).
        assert!(p.is_expanded("A/B"));
        assert!(p.is_expanded("a\\b"));
    }

    #[test]
    fn a_named_path_never_denotes_a_child_directory() {
        // `AB` is not `A\B`: the ancestor test is component-wise.
        let p = only(&["A\\B"]);
        assert!(!p.is_expanded("A\\BC"));
        // A child of the named directory is not itself named, and the Oracle
        // does not expand it either: u5g s4 renders `A\B`'s children but no
        // grandchildren.
        assert!(!p.is_expanded("A\\B\\C"));
        assert!(p.is_expanded("A\\B"));
    }

    #[test]
    fn cumulative_expand_is_a_union() {
        // u5g s5 (`expand "A"` then `expand "A\B"`) and s6 (`A` then `C`).
        let p = only(&["A"]).accumulate(&["A\\B".to_string()]);
        assert_eq!(p, only(&["A", "A\\B"]));
        let p = only(&["A"]).accumulate(&["C".to_string()]);
        assert_eq!(p, only(&["A", "C"]));
        // `All` absorbs.
        assert_eq!(ExpandPolicy::All.accumulate(&["A".to_string()]), ExpandPolicy::All);
        assert_eq!(
            ExpandPolicy::None.accumulate(&["A".to_string()]),
            only(&["A"])
        );
    }

    #[test]
    fn fully_expanded_is_the_leaf_answer_for_the_u5g_shapes() {
        // u5g s6: `expand "A"` + `expand "C"` -> `C=3` (C holds only i.txt).
        let p = only(&["A", "C"]);
        assert!(p.fully_expanded("C"));
        // The same policy must NOT answer for A: A holds the unexpanded B, so
        // the tree-aware form is the one that decides (u5g s3: A=<size/>).
        assert!(p.is_expanded("A"));
        assert!(!p.fully_expanded_given("A", false));
        // u5g s4: `expand "A\B"` -> A=10 because B (the only child dir) is
        // expanded; B=6 because it has no child directories at all, so
        // `fully_expanded` is the whole answer for it.
        let p = only(&["A\\B"]);
        assert!(p.fully_expanded_given("A", true));
        assert!(p.fully_expanded("A\\B"));
        assert!(!p.fully_expanded("C"));
        // u5j A-expand-d: `expand "d"`, d holds in.txt only -> d aggregates.
        let p = only(&["d"]);
        assert!(p.fully_expanded("d"));
        // ...while the same directory under `expand "d"` with a child folder
        // still collapsed is NOT fully expanded (u5j D, `expand "d"`).
        assert!(p.is_expanded("d"));
        assert!(!p.fully_expanded_given("d", false));
    }
}

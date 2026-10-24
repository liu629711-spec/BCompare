//! Text Merge channel (docs/20 §6 step 4, D4): three-way merge core.
//!
//! # Evidence discipline
//!
//! BC exposes **no merge script command** (verified against the full
//! SCRIPTING command list, docs/19 §6.15), so there is no byte-level golden
//! for this module. The behavioral rules below are traced to two sources and
//! are marked accordingly:
//!
//! * **measured** — the live probes `extracted/live/textmerge-en` and
//!   `extracted/live/textmerge-conf-en` (2026-10-23): clean merge of
//!   independent edits (`2 difference section(s)`, no conflict), conflict
//!   sections flagged `# N conflict section(s)`, the unresolved output band
//!   keeps the CENTER/base content, and independent edits are auto-taken
//!   into the output;
//! * **official documentation** — `help/3-way_merge_concepts.html`: a merge
//!   session combines separate sets of changes against an older copy of the
//!   data (the center file); a line changed on BOTH sides to DIFFERENT
//!   content is flagged as a conflict requiring manual review; an item added
//!   on one side and absent on the other is resolvable against the base.
//!
//! The section model (equal / take-left / take-right / conflict) and the
//! "unresolved conflict keeps base content until Take" rule are therefore a
//! direct implementation of the measured+documented BC semantics; the
//! alignment itself reuses [`crate::myers`] (observed BC core, see
//! report-algorithm.md).

use crate::lines::{decode, split_text};
use crate::myers::{diff_matches, map_ids};

/// One three-way section between consecutive common anchors.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SectionKind {
    /// Base, left and right all agree on this run.
    Equal,
    /// Only the left side changed relative to base: auto-take-left
    /// (measured: output shows the left band, status counts it as a
    /// difference section, no conflict).
    TakeLeft,
    /// Only the right side changed relative to base.
    TakeRight,
    /// Both sides changed the same base run to DIFFERENT content (measured:
    /// red output band (255,227,227) + `# N conflict section(s)`; output
    /// keeps base content until a Take resolves it).
    Conflict,
}

/// A section of the merge grid. `base`/`left`/`right` are half-open line
/// ranges into the respective input line lists.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MergeSection {
    pub kind: SectionKind,
    pub base: (usize, usize),
    pub left: (usize, usize),
    pub right: (usize, usize),
}

impl MergeSection {
    /// Content the OUTPUT pane shows for this section in its unresolved
    /// state (measured: conflict keeps base, equal/takes keep the side that
    /// changed).
    pub fn output_source(&self) -> &'static str {
        match self.kind {
            SectionKind::Equal | SectionKind::Conflict => "center",
            SectionKind::TakeLeft => "left",
            SectionKind::TakeRight => "right",
        }
    }
}

/// Full merge result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MergeResult {
    pub sections: Vec<MergeSection>,
}

impl MergeResult {
    /// `N difference section(s)`-style count for the status bar (measured
    /// BC: a clean 2-edit merge reported `2 difference section(s)`; equal
    /// runs are not sections).
    pub fn difference_sections(&self) -> usize {
        self.sections
            .iter()
            .filter(|s| s.kind != SectionKind::Equal)
            .count()
    }

    /// `# N conflict section(s)` count.
    pub fn conflict_sections(&self) -> usize {
        self.sections
            .iter()
            .filter(|s| s.kind == SectionKind::Conflict)
            .count()
    }

    /// Materialize the output pane content: for every section, the resolved
    /// side (equal = base, take = that side, unresolved conflict = base per
    /// the measured rule). `overrides` lets a Take button re-resolve a
    /// conflict section before re-rendering.
    pub fn output_lines(
        &self,
        base: &[String],
        left: &[String],
        right: &[String],
        overrides: &std::collections::HashMap<usize, SectionKind>,
    ) -> Vec<String> {
        let mut out = Vec::new();
        for (i, s) in self.sections.iter().enumerate() {
            let kind = overrides.get(&i).copied().unwrap_or(s.kind);
            let src: &[String] = match kind {
                SectionKind::Equal => base,
                SectionKind::TakeLeft => left,
                SectionKind::TakeRight => right,
                // measured: an unresolved conflict holds the center content
                SectionKind::Conflict => base,
            };
            let run = match kind {
                SectionKind::Equal | SectionKind::Conflict => s.base,
                SectionKind::TakeLeft => s.left,
                SectionKind::TakeRight => s.right,
            };
            // a Take of a section whose side is empty means "take nothing"
            // (delete side taken) — the run is already empty and adds nothing.
            out.extend(src[run.0..run.1].iter().cloned());
        }
        out
    }

    /// The COMPACT output document for the merge view (docs/19 §6.17,
    /// measured by the textmerge-edit probe): the resolved lines of every
    /// section in order, flattened to ONE output row per source line — the
    /// GUI output pane is a normal document, NOT band-aligned with the
    /// source panes. Q1 measured: this is what the output pane shows on open
    /// (the save-target file's own disk content never appears).
    pub fn output_document(&self, base: &[String], left: &[String], right: &[String]) -> Vec<String> {
        self.output_lines(base, left, right, &std::collections::HashMap::new())
    }
}

/// Compute the three-way merge of `base` against `left` and `right`
/// (BC's pane order: left / center=base / right; the CLI argument order
/// follows BC's own command line, `L R C` — callers pass the logical roles).
pub fn merge3(base: &[String], left: &[String], right: &[String]) -> MergeResult {
    // Two independent alignments against base (observed BC engine core,
    // report-algorithm.md: Myers shortest-edit + prefix/suffix trim).
    let (bid_l, lid_l) = map_ids(base, left);
    let ml = diff_matches(&bid_l, &lid_l).expect("diff_matches base-left"); // (base_i, left_i)
    let (bid_r, rid_r) = map_ids(base, right);
    let mr = diff_matches(&bid_r, &rid_r).expect("diff_matches base-right"); // (base_i, right_i)

    // Three-way anchors: base rows matched in BOTH alignments. map_ids gives
    // equal ids to equal content and diff_matches pairs equal ids, so each
    // anchor row is literally common to all three files. Both match lists
    // are strictly increasing, so the (b, l, r) triples are monotone.
    let mut la: std::collections::HashMap<usize, usize> = Default::default();
    for (b, l) in &ml {
        la.insert(*b, *l);
    }
    let mut ra: std::collections::HashMap<usize, usize> = Default::default();
    for (b, r) in &mr {
        ra.insert(*b, *r);
    }
    let mut anchors: Vec<(usize, usize, usize)> = Vec::new();
    for b in 0..base.len() {
        if let (Some(l), Some(r)) = (la.get(&b).copied(), ra.get(&b).copied()) {
            anchors.push((b, l, r));
        }
    }

    let mut sections: Vec<MergeSection> = Vec::new();

    // gap section between (pb,pl,pr) and the next anchor/start boundary
    let mut push_gap = |pb: usize, pl: usize, pr: usize, b1: usize, l1: usize, r1: usize,
                        sections: &mut Vec<MergeSection>| {
        if b1 == pb && l1 == pl && r1 == pr {
            return;
        }
        let bs = (pb, b1);
        let ls = (pl, l1);
        let rs = (pr, r1);
        let l_changed = run_changed(base, left, bs, ls);
        let r_changed = run_changed(base, right, bs, rs);
        let kind = match (l_changed, r_changed) {
            (false, false) => SectionKind::Equal,
            (true, false) => SectionKind::TakeLeft,
            (false, true) => SectionKind::TakeRight,
            (true, true) => {
                // Both sides rewrote the same base region. Documented rule:
                // only DIFFERENT independent changes conflict — an identical
                // rewrite on both sides merges (take either side).
                if left[ls.0..ls.1] == right[rs.0..rs.1] {
                    SectionKind::TakeLeft
                } else {
                    SectionKind::Conflict
                }
            }
        };
        sections.push(MergeSection {
            kind,
            base: bs,
            left: ls,
            right: rs,
        });
    };

    // Coalesce maximal chains of consecutive anchors ((b,l,r) all stepping
    // by exactly one) into single Equal runs; anything between chains is a
    // gap section classified above.
    let (mut pb, mut pl, mut pr) = (0usize, 0usize, 0usize);
    let mut i = 0usize;
    while i < anchors.len() {
        let mut j = i;
        while j + 1 < anchors.len()
            && anchors[j + 1].0 == anchors[j].0 + 1
            && anchors[j + 1].1 == anchors[j].1 + 1
            && anchors[j + 1].2 == anchors[j].2 + 1
        {
            j += 1;
        }
        let (ab, al, ar) = anchors[i];
        let (eb, el, er) = anchors[j];
        push_gap(pb, pl, pr, ab, al, ar, &mut sections);
        sections.push(MergeSection {
            kind: SectionKind::Equal,
            base: (ab, eb + 1),
            left: (al, el + 1),
            right: (ar, er + 1),
        });
        pb = eb + 1;
        pl = el + 1;
        pr = er + 1;
        i = j + 1;
    }
    push_gap(pb, pl, pr, base.len(), left.len(), right.len(), &mut sections);
    MergeResult { sections }
}

/// True when the side's line run differs from the base run (length or any
/// row content).
fn run_changed(base: &[String], side: &[String], b: (usize, usize), s: (usize, usize)) -> bool {
    let (bl, sl) = (b.1 - b.0, s.1 - s.0);
    if bl != sl {
        return true;
    }
    (0..bl).any(|i| base[b.0 + i] != side[s.0 + i])
}

/// Read + decode + split one merge input, reusing the observed line-splitting
/// rules (clone/lines anchors: CRLF≡LF etc.).
pub fn read_lines(path: &str) -> Result<Vec<String>, String> {
    let bytes = std::fs::read(path).map_err(|e| format!("cannot read {path}: {e}"))?;
    let dec = decode(&bytes);
    Ok(split_text(&dec.text))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ls(v: &[&str]) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn m_independent_edits_no_conflict() {
        // measured probe textmerge-en fixture: L edits line2, R edits line5.
        let base = ls(&["one", "two", "three", "four", "five", "six", "seven", "eight"]);
        let left = ls(&["one", "two-L", "three", "four", "five", "six", "seven", "eight"]);
        let right = ls(&["one", "two", "three", "four", "five-R", "six", "seven", "eight"]);
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 0);
        // two difference sections (BC status bar reported exactly 2)
        assert_eq!(m.difference_sections(), 2);
        let tl = m
            .sections
            .iter()
            .find(|s| s.kind == SectionKind::TakeLeft)
            .unwrap();
        assert_eq!(&left[tl.left.0..tl.left.1], &["two-L".to_string()][..]);
        assert_eq!(tl.output_source(), "left");
        // output materialization holds BOTH edits
        let out = m.output_lines(&base, &left, &right, &Default::default());
        assert!(out.contains(&"two-L".to_string()), "{out:?}");
        assert!(out.contains(&"five-R".to_string()), "{out:?}");
    }

    #[test]
    fn m_conflict_same_line_both_sides() {
        // measured probe textmerge-conf-en fixture: line2 edited BOTH ways.
        let base = ls(&["one", "two", "three", "four", "five", "six", "seven", "eight"]);
        let left = ls(&["one", "two-L", "three", "four", "five", "six", "seven", "eight"]);
        let right = ls(&["one", "two-R", "three", "four", "five", "six", "seven", "eight"]);
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 1);
        let c = m
            .sections
            .iter()
            .find(|s| s.kind == SectionKind::Conflict)
            .unwrap();
        // unresolved output keeps CENTER/base content
        assert_eq!(c.output_source(), "center");
        assert_eq!(&base[c.base.0..c.base.1], &["two".to_string()][..]);
        let out = m.output_lines(&base, &left, &right, &Default::default());
        assert!(out.contains(&"two".to_string()) && !out.contains(&"two-L".to_string()), "{out:?}");
        // Take Left on the conflict index resolves it
        let idx = m.sections.iter().position(|s| s.kind == SectionKind::Conflict).unwrap();
        let mut ov = std::collections::HashMap::new();
        ov.insert(idx, SectionKind::TakeLeft);
        let out2 = m.output_lines(&base, &left, &right, &ov);
        assert!(out2.contains(&"two-L".to_string()) && !out2.contains(&"two".to_string()), "{out2:?}");
    }

    #[test]
    fn m_identical_independent_edits_merge_without_conflict() {
        // documented: only DIFFERENT changes on the same line conflict.
        let base = ls(&["a", "b", "c"]);
        let left = ls(&["a", "B", "c"]);
        let right = ls(&["a", "B", "c"]);
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 0);
        assert_eq!(m.difference_sections(), 1);
    }

    #[test]
    fn m_insert_one_side_only() {
        // 3-way concept page: item added on one side is resolvable against
        // base (not a conflict).
        let base = ls(&["a", "c"]);
        let left = ls(&["a", "b", "c"]);
        let right = ls(&["a", "c"]);
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 0);
        assert_eq!(m.difference_sections(), 1);
        let tl = m
            .sections
            .iter()
            .find(|s| s.kind == SectionKind::TakeLeft)
            .unwrap();
        assert_eq!(&left[tl.left.0..tl.left.1], &["b".to_string()][..]);
    }

    #[test]
    fn m_delete_vs_edit_is_conflict() {
        let base = ls(&["a", "b", "c"]);
        let left = ls(&["a", "c"]); // delete b
        let right = ls(&["a", "B", "c"]); // edit b
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 1);
    }

    #[test]
    fn m_all_identical() {
        let a = ls(&["x", "y"]);
        let m = merge3(&a, &a, &a);
        assert!(m.sections.iter().all(|s| s.kind == SectionKind::Equal));
        assert_eq!(m.difference_sections(), 0);
        assert_eq!(m.conflict_sections(), 0);
        let out = m.output_lines(&a, &a, &a, &Default::default());
        assert_eq!(out, a);
    }

    #[test]
    fn m_no_common_rows_all_conflict() {
        // extreme: L/R both replace everything differently — one conflict.
        let base = ls(&["1", "2", "3"]);
        let left = ls(&["L1", "L2"]);
        let right = ls(&["R1"]);
        let m = merge3(&base, &left, &right);
        assert_eq!(m.conflict_sections(), 1);
        let c = m.sections.iter().find(|s| s.kind == SectionKind::Conflict).unwrap();
        assert_eq!(c.base, (0, 3));
        assert_eq!(c.left, (0, 2));
        assert_eq!(c.right, (0, 1));
    }

    #[test]
    fn m_output_document_crossvalidates_edit_probe() {
        // Cross-validation against the LIVE textmerge-edit probe bytes
        // (docs/19 §6.17 / merge-edit-findings.json Q1+Q2). The probe saved
        // (after Ctrl+S, no Take): the 8 base lines verbatim + the typed
        // marker appended AFTER 'line eight' — i.e. BC's initial output
        // document for the conflict fixture == the engine's compact
        // materialization. Fixture names/contents mirror _scratch_merge/{lc,
        // rc,base}.txt exactly.
        let base = ls(&[
            "line one", "line two", "line three", "line four", "line five",
            "line six", "line seven", "line eight",
        ]);
        let left = ls(&[
            "line one", "line two LEFTWASHERE", "line three", "line four", "line five",
            "line six", "line seven", "line eight",
        ]);
        let right = ls(&[
            "line one", "line two RIGHTWASHERE", "line three", "line four", "line five",
            "line six", "line seven", "line eight",
        ]);
        let m = merge3(&base, &left, &right);
        // probe OUT_after_ctrl_s (minus the user-typed marker line):
        // 'line one\nline two\nline three\nline four\nline five\nline six\n
        //  line seven\nline eight\nZZEDITMARKER7'
        let doc = m.output_document(&base, &left, &right);
        assert_eq!(doc.len(), 8, "{doc:?}");
        assert_eq!(doc[1], "line two", "unresolved conflict must hold CENTER");
        assert_eq!(doc[0], "line one");
        assert_eq!(doc[7], "line eight");
        // the independent-edit fixture cross-check (textmerge-en): output =
        // BOTH auto-takes merged, nothing lost.
        let bl = ls(&[
            "line one", "line two edited by left", "line three", "line four", "line five",
            "line six", "line seven", "line eight",
        ]);
        let br = ls(&[
            "line one", "line two", "line three", "line four", "line five changed by right",
            "line six", "line seven", "line eight",
        ]);
        let bc = ls(&[
            "line one", "line two", "line three", "line four", "line five",
            "line six", "line seven", "line eight",
        ]);
        let mi = merge3(&bc, &bl, &br);
        let doci = mi.output_document(&bc, &bl, &br);
        assert!(doci.iter().any(|l| l.contains("edited by left")), "{doci:?}");
        assert!(doci.iter().any(|l| l.contains("changed by right")), "{doci:?}");
        assert_eq!(doci.len(), 8);
    }
}

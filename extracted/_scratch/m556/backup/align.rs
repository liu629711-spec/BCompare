//! M1.3 (block layer) — turn a shortest edit script into the report's group
//! sequence.
//!
//! [`crate::myers`] returns matched index pairs only. This module derives the
//! difference runs, pairs them up, and assigns the final status of every group.
//! The rules below are all **O**bserved in `verify/golden`:
//!
//! | Rule | Evidence |
//! |---|---|
//! | Orphan blocks pair `min(left, right)` as `different`; the remainder are orphans | `al-replace-block` (3 vs 3 → three `different`), `verify/disambig/unequal-replace` (2 vs 3 → `different`, `different`, `rightorphan`) |
//! | A purely one-sided block produces orphans only | `al-insert`, `al-delete`, `al-empty-left` |
//! | Adjacent difference groups form ONE difference section, merged as in `140dc6a00` / `140dc6b20` | the layout corpus counts sections; `mixed` is 1 section over 5 non-`same` groups, `orphans` is 2 |
//! | No move detection | `al-move-down`, `al-swap-blocks` |
//! | Repeated lines resolve forward-first | `al-duplicates` (enforced in `myers`) |
//!
//! # What "merging adjacent difference runs" means here
//!
//! The observed emit functions extend the *current* run instead of starting a
//! new one when the line is adjacent to it, and start a new record when it is
//! not. The consequence for the report is that a maximal run of consecutive
//! unmatched lines becomes one contiguous block rather than one group per line.
//! This module reproduces exactly that: [`Block`] is a maximal run, and
//! [`Group`] is the emitted unit.

use crate::importance::{Plan, Verdict};
use crate::importance::Grammar;

impl Verdict {
    fn into_status(self) -> Status {
        match self {
            Verdict::Same => Status::Same,
            Verdict::Similar => Status::Similar,
            Verdict::Different => Status::Different,
        }
    }
}

/// `linecomp/@status` for one emitted group.
///
/// The seven values here are the complete paired/orphan vocabulary a text
/// compare report uses. `leftsimilar`/`rightsimilar` are M2 additions,
/// observed in `u2-probe-*`/`u2b-probe-*`: a ONE-SIDED line whose content is
/// entirely unimportant (a comment, blank or whitespace-only line) is
/// reported `leftsimilar`/`rightsimilar` instead of an orphan, and folds to
/// `same` under `ignore-unimportant`. The normalizer in `product/verify` also
/// knows `leftnewer`/`rightolder`/`leftorphanimportant` etc. for other
/// engines and other modes; none of those occur in a text compare report, so
/// they are not produced here.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Status {
    Same,
    Similar,
    Different,
    LeftOrphan,
    RightOrphan,
    LeftSimilar,
    RightSimilar,
}

impl Status {
    /// The exact `status=` attribute text used by the XML report.
    pub fn as_xml(self) -> &'static str {
        match self {
            Status::Same => "same",
            Status::Similar => "similar",
            Status::Different => "different",
            Status::LeftOrphan => "leftorphan",
            Status::RightOrphan => "rightorphan",
            Status::LeftSimilar => "leftsimilar",
            Status::RightSimilar => "rightsimilar",
        }
    }

    /// True for the four one-sided statuses.
    pub fn is_orphan(self) -> bool {
        matches!(
            self,
            Status::LeftOrphan | Status::RightOrphan | Status::LeftSimilar | Status::RightSimilar
        )
    }

    /// True when `ignore-unimportant` folds this status to `same` (observed:
    /// u2b folds `leftsimilar`/`rightsimilar` alongside `similar`).
    pub fn folds_to_same(self) -> bool {
        matches!(
            self,
            Status::Similar | Status::LeftSimilar | Status::RightSimilar
        )
    }
}

/// Marks a group that `ignore-unimportant` folded from a one-sided
/// unimportant line (`leftsimilar`/`rightsimilar`) into a `same` row.
///
/// The row's OWN line id stays in `left`/`right`; the id shown for the other
/// side is BORROWED from the nearest preceding paired row at render time (BC
/// reuses that id; none means `0` — u2b `orphan-comment-lead+iu` shows
/// `rtid="0"`). A folded [`FoldOrigin::RightSimilar`] row renders an empty
/// `<text/>`: the observed report carries both ids but not the right line's
/// content.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FoldOrigin {
    LeftSimilar,
    RightSimilar,
}

/// A maximal run of consecutive unmatched lines on one or both sides.
///
/// `left` and `right` are half-open ranges of line indices. One of them may be
/// empty; both cannot (an empty run is not emitted as a block).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Block {
    pub left_start: usize,
    pub left_end: usize,
    pub right_start: usize,
    pub right_end: usize,
}

impl Block {
    pub fn left_len(&self) -> usize {
        self.left_end - self.left_start
    }
    pub fn right_len(&self) -> usize {
        self.right_end - self.right_start
    }
}

/// One emitted report unit.
///
/// `left` / `right` are `None` for an orphan side. A paired group always has
/// both sides set. `folded` is `None` for every group the aligner produces;
/// it is set only by `ignore-unimportant` folding (see [`FoldOrigin`]).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Group {
    pub left: Option<usize>,
    pub right: Option<usize>,
    pub status: Status,
    pub folded: Option<FoldOrigin>,
}

impl Group {
    pub fn paired(left: usize, right: usize, status: Status) -> Group {
        Group { left: Some(left), right: Some(right), status, folded: None }
    }

    pub fn left_only(i: usize, status: Status) -> Group {
        Group { left: Some(i), right: None, status, folded: None }
    }

    pub fn right_only(i: usize, status: Status) -> Group {
        Group { left: None, right: Some(i), status, folded: None }
    }

    pub fn left_index(&self) -> Option<usize> {
        self.left
    }
    pub fn right_index(&self) -> Option<usize> {
        self.right
    }
}

/// Derive the unmatched blocks from the matched pairs.
///
/// Both inputs are ordered index lists over the same id arrays. The result is
/// the list of maximal blocks, in document order, including a trailing block
/// when the last pairs do not reach the end of either file.
pub fn blocks_from_matches(
    a_len: usize,
    b_len: usize,
    pairs: &[(usize, usize)],
) -> Vec<Block> {
    let mut out = Vec::new();
    let (mut ai, mut bi) = (0usize, 0usize);
    for &(pi, pj) in pairs {
        if pi > ai || pj > bi {
            out.push(Block { left_start: ai, left_end: pi, right_start: bi, right_end: pj });
        }
        ai = pi + 1;
        bi = pj + 1;
    }
    if ai < a_len || bi < b_len {
        out.push(Block { left_start: ai, left_end: a_len, right_start: bi, right_end: b_len });
    }
    out
}

/// The anchor key one line contributes to the exact-match layer.
///
/// A line WITH important content anchors on that content: two lines whose
/// important text is equal may be matched by Myers. A line with NO important
/// content (a comment, a blank, a whitespace-only line) must **never** anchor —
/// BC places such lines by similarity, not by identity, so giving them all one
/// shared key (which would let Myers match comment-to-comment ahead of a better
/// overall script) is wrong. The `side`/`index` fields make each such key
/// unique, which removes it from the match set without affecting any other
/// line.
///
/// Evidence: the m2-* anchors (`orphan-comment-lead`, `align-comments-forward`,
/// `three-comments-one`) all show comments placed by the pairing layer rather
/// than anchored ahead of content, and the closeness model with this key rule
/// reproduces every recorded BC pairing in the corpus (see
/// `product/verify/tools/m26_model_grade.py`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum AnchorKey<'a> {
    Important(&'a str),
    Unimportant { side: u8, index: usize },
}

/// Pair up the two sides of a block.
///
/// Inside an unmatched block BC pairs the remaining lines by **closeness**:
/// its alignment help documents "Use closeness matching ... attempt[s] to
/// align the remaining mismatched lines based on their similarity", and the
/// emitter (`FUN_140dc6c40` case 2) turns a 1x1 no-match cell into a *paired*
/// row — so a `different` row is a pair the aligner chose, not an accident.
///
/// The rule implemented here is the one that reproduces every recorded BC
/// pairing: a monotone matching maximizing (total similarity, pair count),
/// where similarity is the longest common subsequence of the closeness texts
/// (verbatim lines for plain text — case-sensitive; important text for syntax
/// formats, see [`Plan::closeness_text`]). Ties minimize the total length of
/// the paired **left** lines, then resolve to the earliest pairs. With
/// all-zero similarity this degenerates to the identity zip unless a shorter
/// left line can pair instead (`al-replace-block` records three `different`
/// rows for a 3x3 block), and with a genuinely similar line present it picks
/// that line even across a positional offset (`similar-preference`, the m26
/// `all-kinds` cases).
///
/// The tie rules are measured, not guessed (`runs/m51b-probe-20261014T163003Z`
/// and `runs/m51c-probe-manual`): a 3-score pair beats a 0-score zip
/// (`score-vs-count`); among equal (score, count) matchings BC pairs the
/// *shorter left* lines — `[abcdefgh, ab] vs [X]` pairs `ab`, not the earlier
/// `abcdefgh` (`tie-len-2v1`), and `[bbbb, o1] vs [X]` pairs `o1`
/// (`tie-2v1`) — while equal-length or fixed-left ties fall back to earliest
/// (`tie-dup`, `tie-3v1`, `tie-len-1v2`, `tie-len-eq`). The key is
/// left-only because monotone count-max matchings always spend the first k
/// right lines: which right lines pair is never a choice, which left lines
/// pair is.
///
/// Resource bound: the similarity pass is skipped when the block or a line
/// pair exceeds [`CLOSENESS_MAX_CELLS`] / [`CLOSENESS_MAX_TEXT_PRODUCT`], in
/// which case the block falls back to the identity zip. That keeps the
/// linear-space guarantee of `myers` intact for very large files; the bound is
/// a resource policy, not an observed rule.
pub fn pair_block(block: &Block, plan: &Plan, out: &mut Vec<Group>) {
    let ls: Vec<usize> = (block.left_start..block.left_end).collect();
    let rs: Vec<usize> = (block.right_start..block.right_end).collect();
    let pairs = closeness_pairs(&ls, &rs, plan)
        .unwrap_or_else(|| identity_pairs(&ls, &rs));
    emit_block(&ls, &rs, &pairs, plan, out);
}

/// Maximum `left_len * right_len` a block may have for the closeness pass to
/// run; above it the block uses the identity zip. 250k cells is ~2 MB of
/// scratch and covers every block the recorded corpus contains.
const CLOSENESS_MAX_CELLS: usize = 250_000;

/// Total character work (`cells * max_left_len * max_right_len`) a single
/// block may spend on similarity, guarding the `O(cells * len^2)` pass so the
/// linear-space guarantee of `myers` is never broken by a large block of long
/// lines. A block that would exceed it falls back to the identity zip.
const CLOSENESS_WORK_BUDGET: usize = 32_000_000;

/// Top-first identity pairing: k pairs with k, the longer side's leftovers
/// become one-sided rows.
fn identity_pairs(ls: &[usize], rs: &[usize]) -> Vec<(usize, usize)> {
    (0..ls.len().min(rs.len())).map(|k| (ls[k], rs[k])).collect()
}

/// The closeness pass: a monotone matching of `ls` against `rs` maximizing
/// (total similarity, pair count), then minimizing the total paired left
/// length, earliest pairs on the remaining ties.
///
/// Returns `None` when the block exceeds [`CLOSENESS_MAX_CELLS`], so the caller
/// can fall back to the identity zip without paying for the table.
fn closeness_pairs(ls: &[usize], rs: &[usize], plan: &Plan) -> Option<Vec<(usize, usize)>> {
    let n = ls.len();
    let m = rs.len();
    if n == 0 || m == 0 {
        return Some(Vec::new());
    }
    if n.saturating_mul(m) > CLOSENESS_MAX_CELLS {
        return None;
    }
    let lt: Vec<&str> = ls.iter().map(|&i| plan.score_text(true, i)).collect();
    let rt: Vec<&str> = rs.iter().map(|&j| plan.score_text(false, j)).collect();
    let max_l = lt.iter().map(|s| s.len()).max().unwrap_or(0);
    let max_r = rt.iter().map(|s| s.len()).max().unwrap_or(0);
    if n.saturating_mul(m).saturating_mul(max_l.max(1)).saturating_mul(max_r.max(1))
        > CLOSENESS_WORK_BUDGET
    {
        return None;
    }
    // Pair scores come from the decoded `FUN_140e726b0` (see
    // [`pair_similarity`]). Its "equal hash ids" branch is keyed on the same
    // anchor keys the alignment layer uses, and requires both lines to carry
    // important content: for `Unimportant` (blank/comment-only) lines the
    // fetched text is not empty and BC scores them through the
    // character-intersection branch, not as "same line, changed".
    use crate::importance::AlignKey;
    let lkey: Vec<&AlignKey> = ls.iter().map(|&i| plan.left_key(i)).collect();
    let rkey: Vec<&AlignKey> = rs.iter().map(|&j| plan.right_key(j)).collect();
    let lw: Vec<usize> = ls.iter().map(|&i| plan.important_text(true, i).len()).collect();
    let rw: Vec<usize> = rs.iter().map(|&j| plan.important_text(false, j).len()).collect();
    let mut score = vec![0i64; n * m];
    for a in 0..n {
        for b in 0..m {
            let same_key = !matches!(lkey[a], AlignKey::Unimportant) && lkey[a] == rkey[b];
            score[a * m + b] = pair_similarity(lt[a], rt[b], same_key, lw[a], rw[b]);
        }
    }
    // The decoded pairing engine is a Needleman-Wunsch fill over the block
    // (`FUN_140e74660`): each unpaired line costs a fixed gap penalty
    // (`GAP_PENALTY`, 20), a pair adds its signed `pair_similarity`. The fill
    // runs in REVERSED coordinates with the tie order diagonal > skip-left >
    // skip-right and traces back from the (n, m) corner — the preference is
    // anchored at the END of the block, which is what the recorded case-swap
    // shapes pin (docs/11 §15: `[a, B] vs [b, A]` pairs B/b, not a/A).
    //
    // This replaces the M5.1b triple DP — (score, count, min-left-len) over a
    // free-skip lattice. The two are not interchangeable: with signed scores
    // the free skip silently rejects every negative pair, which the recorded
    // corpus does not do (docs/11 §15, configs C/D vs F). The old tie keys
    // survive inside the decoded objective: a skipped line is the -20 "gap",
    // and the reversed fill prefers earlier-pairing solutions on equal score.
    //
    // Indices: `lt`/`lkey`/`lw` are indexed by POSITION in `ls`/`rs` (0..n),
    // while the elements of `ls`/`rs` are document line numbers. The fill
    // walks positions `a`/`b` in reverse, so the position that pairs at
    // (c, r) is `a = n - c`, `b = m - r`.
    let mut f = vec![0i64; (m + 1) * (n + 1)];
    let mut d = vec![0u8; (m + 1) * (n + 1)]; // 1 = skip-left, 2 = skip-right, 3 = pair
    let idx = |r: usize, c: usize| r * (n + 1) + c;
    for c in 1..=n {
        f[idx(0, c)] = f[idx(0, c - 1)] - GAP_PENALTY;
        d[idx(0, c)] = 1;
    }
    for r in 1..=m {
        f[idx(r, 0)] = f[idx(r - 1, 0)] - GAP_PENALTY;
        d[idx(r, 0)] = 2;
        for c in 1..=n {
            let a = n - c;
            let b = m - r;
            let same_key = !matches!(lkey[a], AlignKey::Unimportant) && lkey[a] == rkey[b];
            let mut best = f[idx(r - 1, c - 1)]
                + pair_similarity(lt[a], rt[b], same_key, lw[a], rw[b]);
            let mut dir = 3u8;
            if best < f[idx(r, c - 1)] - GAP_PENALTY {
                best = f[idx(r, c - 1)] - GAP_PENALTY;
                dir = 1;
            }
            if best < f[idx(r - 1, c)] - GAP_PENALTY {
                best = f[idx(r - 1, c)] - GAP_PENALTY;
                dir = 2;
            }
            f[idx(r, c)] = best;
            d[idx(r, c)] = dir;
        }
    }
    // The reversed fill traces back from the (m, n) corner, so the pairs
    // come out in ascending document order already.
    let mut pairs = Vec::new();
    let (mut r, mut c) = (m, n);
    while r != 0 || c != 0 {
        match d[idx(r, c)] {
            3 => {
                pairs.push((ls[n - c], rs[m - r]));
                r -= 1;
                c -= 1;
            }
            2 => r -= 1,
            _ => c -= 1,
        }
    }
    Some(pairs)
}

/// `FUN_140e74660`'s gap cost: every line skipped on either side.
const GAP_PENALTY: i64 = 20;

/// `FUN_140e726b0` — BC's line-pair score, all three decoded branches.
///
/// Decoded 2026-10-15 (docs/11 §9, §15). Every branch is a *relative* score
/// used to rank candidate pairs inside one unmatched block; only their
/// ordering matters, so the negative walls below are reproduced but their
/// exact offsets are not load-bearing beyond comparisons.
///
/// * equal hash ids (the lines carry the same anchor key — passed in as
///   `same_key`): `-10` when either text is empty, else `(wL + wR) * 2`
///   with `w` the important-text length, minus one when the two text lengths
///   differ. This is the branch the corpus hits constantly: two lines with
///   the same key are "the same line, changed", and BC scores by bulk.
/// * differing keys, one text empty: `v = -4 * (lL + lR) - 1`, raised to
///   `-11` when above `-12`, floored at `-40` (`+0xac == 0` additionally
///   hard-walls to `-18`/`-5000` — those flags are runtime state this model
///   does not reproduce; see §15.2's residual unknowns).
/// * differing keys, both non-empty: the order-free character intersection
///   (`FUN_140e725f0`): `raw = 3 * common - lL - lR`; `raw < 1` clamps to
///   `max(raw * 4 - 1, -40)`, else scales `(raw * 25) / min(lL, lR)`.
#[allow(clippy::too_many_arguments)]
fn pair_similarity(a: &str, b: &str, same_key: bool, wl: usize, wr: usize) -> i64 {
    if same_key {
        if a.is_empty() || b.is_empty() {
            return -10;
        }
        let mut s = ((wl + wr) * 2) as i64;
        if a.len() != b.len() {
            s -= 1;
        }
        return s;
    }
    if a.is_empty() || b.is_empty() {
        let mut v = -4 * ((a.len() + b.len()) as i64) - 1;
        if v > -12 {
            v = -11;
        }
        if v < -39 {
            v = -40;
        }
        return v;
    }
    let common = char_intersection(a, b);
    let raw = 3 * common - (a.len() + b.len()) as isize;
    if raw < 1 {
        (raw as i64 * 4 - 1).max(-40)
    } else {
        (raw * 25 / a.len().min(b.len()) as isize) as i64
    }
}

/// `FUN_140e725f0`: `common = Σ_c min(freq_a[c], freq_b[c])` over a 256-bucket
/// histogram — order-free, NOT the longest common subsequence.
fn char_intersection(a: &str, b: &str) -> isize {
    let mut count = [0i32; 256];
    for &c in a.as_bytes() {
        count[c as usize] += 1;
    }
    let mut common = 0isize;
    for &c in b.as_bytes() {
        let e = &mut count[c as usize];
        *e -= 1;
        if *e >= 0 {
            common += 1;
        }
    }
    common
}

/// Emit the groups of one block from its pairing, orphans at their own
/// document positions (BC emits one-sided runs as the subdivision finds them,
/// so an orphan sits between the pairs that bound it — `al-insert` reports
/// `same, rightorphan, same`).
fn emit_block(
    ls: &[usize],
    rs: &[usize],
    pairs: &[(usize, usize)],
    plan: &Plan,
    out: &mut Vec<Group>,
) {
    let (mut a, mut b) = (0usize, 0usize);
    for &(li, rj) in pairs {
        // One-sided lines that precede this pair on either side, in document
        // order: left orphans first, then right orphans (the order the
        // subdivision's left-recursion-then-right-recursion produces).
        while a < ls.len() && ls[a] < li {
            push_left(ls[a], plan, out);
            a += 1;
        }
        while b < rs.len() && rs[b] < rj {
            push_right(rs[b], plan, out);
            b += 1;
        }
        out.push(Group::paired(li, rj, plan.verdict(li, rj).into_status()));
        if a < ls.len() && ls[a] == li {
            a += 1;
        }
        if b < rs.len() && rs[b] == rj {
            b += 1;
        }
    }
    while a < ls.len() {
        push_left(ls[a], plan, out);
        a += 1;
    }
    while b < rs.len() {
        push_right(rs[b], plan, out);
        b += 1;
    }
}

fn push_left(i: usize, plan: &Plan, out: &mut Vec<Group>) {
    let status = if plan.line_is_unimportant(true, i) {
        Status::LeftSimilar
    } else {
        Status::LeftOrphan
    };
    out.push(Group::left_only(i, status));
}

fn push_right(j: usize, plan: &Plan, out: &mut Vec<Group>) {
    let status = if plan.line_is_unimportant(false, j) {
        Status::RightSimilar
    } else {
        Status::RightOrphan
    };
    out.push(Group::right_only(j, status));
}

/// Build the full group sequence for two line lists.
///
/// `grammar` selects the importance rules (see [`crate::importance`]).
/// Cancellation and size failures propagate: they are never turned into an
/// empty or partial group list.
pub fn align(
    left: &[String],
    right: &[String],
    grammar: Grammar,
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Vec<Group>, crate::myers::DiffError> {
    align_plan(&Plan::build(left, right, grammar), cancel)
}

/// Align from a prebuilt [`Plan`] (single tokenization pass, cross-line
/// state threaded per side).
pub fn align_plan(
    plan: &Plan,
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Vec<Group>, crate::myers::DiffError> {
    // Alignment compares *anchor keys*, not raw text: a line with important
    // content anchors on that content (so a `similar` pair is actually
    // aligned), while a line with no important content takes a key unique to
    // itself and therefore never anchors — such lines are placed by the
    // closeness pass in `pair_block`. See [`AnchorKey`].
    let lk: Vec<AnchorKey<'_>> = (0..plan.left_len())
        .map(|i| match plan.line_is_unimportant(true, i) {
            true => AnchorKey::Unimportant { side: 0, index: i },
            false => AnchorKey::Important(plan.important_text(true, i)),
        })
        .collect();
    let rk: Vec<AnchorKey<'_>> = (0..plan.right_len())
        .map(|j| match plan.line_is_unimportant(false, j) {
            true => AnchorKey::Unimportant { side: 1, index: j },
            false => AnchorKey::Important(plan.important_text(false, j)),
        })
        .collect();
    let (li, ri) = crate::myers::map_ids(&lk, &rk);
    let pairs = crate::myers::diff_matches_cancellable(&li, &ri, cancel)?;
    Ok(groups_from_pairs(plan, &pairs))
}

/// Assemble groups from a matched-pair list. Split out so tests can drive the
/// block/pairing layer without running an alignment.
///
/// `blocks_from_matches` returns the unmatched blocks in document order, with
/// each block ending exactly where the next matched pair begins. So a single
/// forward walk suffices: before emitting pair *k*, emit the block that lies
/// entirely before it; after the last pair, emit any trailing block.
pub fn groups_from_pairs(plan: &Plan, pairs: &[(usize, usize)]) -> Vec<Group> {
    let blocks = blocks_from_matches(plan.left_len(), plan.right_len(), pairs);
    let mut out: Vec<Group> = Vec::with_capacity(pairs.len() + blocks.len());
    let mut bi = 0usize;
    for &(pi, pj) in pairs {
        if let Some(b) = blocks.get(bi) {
            if b.left_end <= pi && b.right_end <= pj {
                pair_block(b, plan, &mut out);
                bi += 1;
            }
        }
        out.push(Group::paired(pi, pj, plan.verdict(pi, pj).into_status()));
    }
    while let Some(b) = blocks.get(bi) {
        pair_block(b, plan, &mut out);
        bi += 1;
    }
    out
}

/// Count the number of difference sections: maximal runs of consecutive
/// non-`same` groups.
///
/// Observed via the summary layout, which prints `N difference section(s)`:
/// `mixed` has 5 non-`same` groups in one run and reports 1; `orphans` has three
/// separated runs and reports 2. Reproduced here because both the report and the
/// tests need one definition.
pub fn difference_sections(groups: &[Group]) -> usize {
    let mut sections = 0usize;
    let mut prev_same = true;
    for g in groups {
        let same = g.status == Status::Same;
        if !same && prev_same {
            sections += 1;
        }
        prev_same = same;
    }
    sections
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::myers::DiffError;

    fn s(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    fn statuses(groups: &[Group]) -> Vec<&'static str> {
        groups.iter().map(|g| g.status.as_xml()).collect()
    }

    fn no_cancel() -> impl FnMut() -> bool {
        || false
    }

    // ---------------------------------------------------------------
    // Block derivation
    // ---------------------------------------------------------------

    #[test]
    fn no_pairs_yields_one_block_covering_everything() {
        let blocks = blocks_from_matches(3, 2, &[]);
        assert_eq!(blocks.len(), 1);
        assert_eq!(blocks[0].left_len(), 3);
        assert_eq!(blocks[0].right_len(), 2);
    }

    #[test]
    fn full_match_yields_no_blocks() {
        assert_eq!(blocks_from_matches(2, 2, &[(0, 0), (1, 1)]), vec![]);
    }

    #[test]
    fn leading_and_trailing_blocks_are_found() {
        // L = a,b,c,d  R = b,c   (a is a left orphan, d is a left orphan)
        let blocks = blocks_from_matches(4, 2, &[(1, 0), (2, 1)]);
        assert_eq!(blocks.len(), 2);
        assert_eq!((blocks[0].left_start, blocks[0].left_end), (0, 1));
        assert_eq!((blocks[0].right_start, blocks[0].right_end), (0, 0));
        assert_eq!((blocks[1].left_start, blocks[1].left_end), (3, 4));
        assert_eq!((blocks[1].right_start, blocks[1].right_end), (2, 2));
    }

    #[test]
    fn adjacent_unmatched_lines_merge_into_one_block() {
        // A 3-line replacement must be one block, not three.
        // L = h1,x,y,z,h2  R = h1,p,q,r,h2 ; pairs = (0,0),(4,4)
        let blocks = blocks_from_matches(5, 5, &[(0, 0), (4, 4)]);
        assert_eq!(blocks.len(), 1);
        assert_eq!(blocks[0].left_len(), 3);
        assert_eq!(blocks[0].right_len(), 3);
    }

    // ---------------------------------------------------------------
    // Block pairing
    // ---------------------------------------------------------------

    #[test]
    fn unequal_replace_pairs_min_and_orphans_the_rest() {
        // verify/disambig/unequal-replace: x,y vs p,q,r
        let plan = Plan::build(&s(&["x", "y"]), &s(&["p", "q", "r"]), crate::importance::Grammar::PlainText);
        let b = Block { left_start: 0, left_end: 2, right_start: 0, right_end: 3 };
        let mut g = Vec::new();
        pair_block(&b, &plan, &mut g);
        assert_eq!(statuses(&g), vec!["different", "different", "rightorphan"]);
        assert_eq!(g[0].left, Some(0));
        assert_eq!(g[0].right, Some(0));
        assert_eq!(g[2].left, None);
        assert_eq!(g[2].right, Some(2));
    }

    #[test]
    fn left_heavy_block_orphans_on_the_left() {
        let plan = Plan::build(&s(&["x", "y", "z"]), &s(&["p"]), crate::importance::Grammar::PlainText);
        let b = Block { left_start: 0, left_end: 3, right_start: 0, right_end: 1 };
        let mut g = Vec::new();
        pair_block(&b, &plan, &mut g);
        assert_eq!(statuses(&g), vec!["different", "leftorphan", "leftorphan"]);
    }

    // ---------------------------------------------------------------
    // Closeness pairing (M2.6)
    //
    // Every case below is a recorded BC report: the golden/disambig anchors and
    // the m26 probe's Oracle output. They pin the rule that replaced the old
    // positional/anchored pair: a monotone matching maximizing (similarity,
    // pair count), and an anchor layer in which a line with no important
    // content never anchors.
    // ---------------------------------------------------------------

    #[test]
    fn closeness_picks_the_similar_line_across_a_positional_offset() {
        // disambig/case-swap-align: a,B vs b,A. BC pairs B with b (similar) and
        // orphans `a`, rather than zipping positionally (a/b different, B/A
        // different-plus-orphans). Only the similarity pass can produce this.
        let g = align(&s(&["a", "B"]), &s(&["b", "A"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(g[0].status, Status::LeftOrphan);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(0)));
        assert_eq!(g[1].status, Status::Similar);
        assert_eq!(g[2].status, Status::RightOrphan);
    }

    #[test]
    fn closeness_prefers_the_exact_line_over_an_earlier_partial_match() {
        // disambig/similar-preference: alpha,beta,gamma vs beta,alpha,gamma.
        // Both `beta` and `alpha` are exact matches; the earliest optimal
        // pairing uses beta and orphans the other alpha.
        let g = align(&s(&["alpha", "beta", "gamma"]), &s(&["beta", "alpha", "gamma"]),
                      Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(statuses(&g), vec!["leftorphan", "same", "rightorphan", "same"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(0)));
    }

    #[test]
    fn closeness_spreads_a_replaced_block_instead_of_collapsing_it() {
        // al-replace-block / unequal-replace: with no similarity anywhere the
        // matching must pair as many lines as it can (the identity zip), which
        // is what BC reports — three `different` rows, not two `same` rows plus
        // an orphan block.
        let g = align(&s(&["h1", "x", "y", "z", "h2"]), &s(&["h1", "p", "q", "r", "h2"]),
                      Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(statuses(&g),
                   vec!["same", "different", "different", "different", "same"]);
        let g = align(&s(&["h1", "x", "y", "h2"]), &s(&["h1", "p", "q", "r", "h2"]),
                      Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(statuses(&g),
                   vec!["same", "different", "different", "rightorphan", "same"]);
    }

    #[test]
    fn m26_all_kinds_c_matches_the_recorded_oracle() {
        // m26 probe `all-kinds-c`: BC reports leftsimilar,different,similar,
        // different,rightsimilar — the comments pair with the comments and the
        // code with the code, one row shifted. The old pair_block produced
        // rightorphan,similar,different,similar,leftorphan instead.
        let g = align(
            &s(&["// a", "int p;", "// q", "int r;"]),
            &s(&["int x;", "// b", "int y;", "// s"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["leftsimilar", "different", "similar", "different", "rightsimilar"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(0)));
        assert_eq!((g[2].left, g[2].right), (Some(2), Some(1)));
        assert_eq!((g[3].left, g[3].right), (Some(3), Some(2)));
    }

    #[test]
    fn m26_all_kinds_txt_matches_the_recorded_oracle() {
        // Same text as `all-kinds-c` under the plain-text grammar, where the
        // comment syntax is not recognized: BC orphans the first and last lines
        // and pairs the three middle ones positionally.
        let g = align(
            &s(&["// a", "int p;", "// q", "int r;"]),
            &s(&["int x;", "// b", "int y;", "// s"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["leftorphan", "different", "different", "different", "rightorphan"]);
    }

    #[test]
    fn m26_comment_lead_and_middle_match_the_recorded_oracle() {
        // m26 `comment-lead-c`: one comment at the top of a 3x2 replace. BC
        // reports the comment as leftsimilar and pairs the two code lines.
        let g = align(
            &s(&["// a", "int p;", "int r;"]),
            &s(&["int x;", "int y;", "// s"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["leftsimilar", "different", "different", "rightsimilar"]);
        // m26 `comment-middle-c`: the comment sits inside the block and is
        // reported as a one-sided leftsimilar row between the two pairs.
        let g = align(
            &s(&["int p;", "// a", "int r;"]),
            &s(&["int x;", "int y;", "// s"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["different", "leftsimilar", "different", "rightsimilar"]);
        // m26 `comment-tail-c` (control, already agreed): both sides end in a
        // comment, so the trailing pair is similar.
        let g = align(
            &s(&["int p;", "int r;", "// a"]),
            &s(&["int x;", "int y;", "// s"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["different", "different", "similar"]);
    }

    #[test]
    fn m26_tail_tiebreak_matches_the_recorded_oracle() {
        // m26 `tail-1v2-txt` (the U8h failure shape): the left `?next` is closer
        // to the right `next` than to `x`, so BC orphans `x` and pairs the
        // replacement — the opposite of the old positional choice.
        let g = align(
            &s(&["alpha", "beta", "?next"]),
            &s(&["gamma", "alpha", "beta", "x", "next"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["rightorphan", "same", "same", "rightorphan", "different"]);
        assert_eq!((g[4].left, g[4].right), (Some(2), Some(4)));
    }

    #[test]
    fn an_unimportant_line_never_anchors_ahead_of_content() {
        // m2-align-comments-forward: `// a, // b, int x;` vs `// c, int x;`.
        // BC pairs the FIRST comment with the only comment and orphans the
        // second; if both comment lines shared one anchor key, Myers would match
        // the second (forward-first) and the first would become the orphan.
        let g = align(
            &s(&["// a", "// b", "int x;"]),
            &s(&["// c", "int x;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["similar", "leftsimilar", "same"]);
        assert_eq!((g[0].left, g[0].right), (Some(0), Some(0)));
        assert_eq!(g[1].left, Some(1));
        assert_eq!(g[1].right, None);
    }

    #[test]
    fn a_shared_comment_is_divided_between_the_comments_in_order() {
        // m2-three-comments-one: `// a, // b, // c` vs `// z` — BC pairs the
        // first and leaves the rest one-sided, again because the unmatched
        // side is placed by position, not by an all-comments-are-equal anchor.
        let g = align(
            &s(&["// a", "// b", "// c"]),
            &s(&["// z"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["similar", "leftsimilar", "leftsimilar"]);
        assert_eq!((g[0].left, g[0].right), (Some(0), Some(0)));

    }

    // ---------------------------------------------------------------
    // Closeness tie rules (M5.1b) — measured live in
    // runs/m51b-probe-20261014T163003Z and runs/m51c-probe-manual.
    // ---------------------------------------------------------------

    #[test]
    fn closeness_score_beats_pair_count() {
        // m51b `score-vs-count`: the abc/abcX pair scores 3; the identity zip
        // scores 0 with two pairs. BC takes the pair, so similarity ranks
        // above count.
        let g = align(
            &s(&["a", "zz", "abc", "c"]),
            &s(&["a", "abcX", "qq", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["same", "leftorphan", "different", "rightorphan", "same"]);
        assert_eq!((g[2].left, g[2].right), (Some(2), Some(1)));
    }

    #[test]
    fn closeness_ties_pair_the_shorter_left_lines() {
        // m51c `tie-len-2v1`: equal (score, count); BC pairs `ab` (2 chars),
        // not the earlier `abcdefgh` (8). m51b `tie-2v1` is the same rule:
        // [bbbb, o1] vs [X] pairs `o1` (2 < 4 left chars).
        let g = align(
            &s(&["a", "abcdefgh", "ab", "c"]),
            &s(&["a", "X", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "leftorphan", "different", "same"]);
        assert_eq!((g[2].left, g[2].right), (Some(2), Some(1)));
        let g = align(
            &s(&["a", "bbbb", "o1", "c"]),
            &s(&["a", "X", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "leftorphan", "different", "same"]);
        assert_eq!((g[2].left, g[2].right), (Some(2), Some(1)));
    }

    #[test]
    fn closeness_rheavy_prefers_the_higher_scoring_right_line() {
        // m51c `tie-len-1v2`: [abcdefgh] vs [ab, X] pairs `ab` — it scores 2
        // (`ab` is a subsequence of `abcdefgh`) against X's 0, so similarity
        // decides on the right side too; the shorter but scoreless `X` loses.
        let g = align(
            &s(&["a", "abcdefgh", "c"]),
            &s(&["a", "ab", "X", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "different", "rightorphan", "same"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(1)));
    }

    #[test]
    fn closeness_equal_length_ties_fall_back_to_earliest() {
        // m51c `tie-len-eq` and m51b `tie-3v1`: every optimal matching covers
        // the same length, so the top-first zip wins.
        let g = align(
            &s(&["a", "abcdefgh", "c"]),
            &s(&["a", "XY", "ZW", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "different", "rightorphan", "same"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(1)));
        let g = align(
            &s(&["a", "p", "q", "r", "c"]),
            &s(&["a", "X", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g),
                   vec!["same", "different", "leftorphan", "leftorphan", "same"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(1)));
    }

    #[test]
    fn closeness_scores_are_case_sensitive_for_plain_text() {
        // m51b `cs-check`: BC zips [bbbb, xx] vs [X, Y] into two zero-score
        // pairs. Lower-cased closeness text would score xx/X = 1 and orphan
        // both ends instead — the anchor layer stays case-insensitive, this
        // layer must not.
        let g = align(
            &s(&["a", "bbbb", "xx", "c"]),
            &s(&["a", "X", "Y", "c"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "different", "different", "same"]);
        assert_eq!((g[1].left, g[1].right), (Some(1), Some(1)));
        assert_eq!((g[2].left, g[2].right), (Some(2), Some(2)));
    }

    #[test]
    fn one_sided_blocks_produce_only_orphans() {
        let plan = Plan::build(&s(&["x", "y"]), &s(&[]), crate::importance::Grammar::PlainText);
        let mut g = Vec::new();
        pair_block(&Block { left_start: 0, left_end: 2, right_start: 0, right_end: 0 }, &plan, &mut g);
        assert_eq!(statuses(&g), vec!["leftorphan", "leftorphan"]);
        let plan = Plan::build(&s(&[]), &s(&["p"]), crate::importance::Grammar::PlainText);
        let mut g = Vec::new();
        pair_block(&Block { left_start: 0, left_end: 0, right_start: 0, right_end: 1 }, &plan, &mut g);
        assert_eq!(statuses(&g), vec!["rightorphan"]);
    }

    #[test]
    fn leftover_unimportant_lines_are_leftsimilar_not_leftorphan() {
        use crate::importance::Grammar;
        // u2b orphan-comment-trailing: `int b;` is leftorphan, `// c` is
        // leftsimilar in the same leftover run.
        let g = align(
            &s(&["int a;", "int b;", "// c"]),
            &s(&["int x;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["different", "leftorphan", "leftsimilar"]);
        // u2b orphan-mixed-trailing-comment: a line whose important part is
        // non-empty is never leftsimilar.
        let g = align(
            &s(&["int a;", "x = 1; // c"]),
            &s(&["int a;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "leftorphan"]);
        // u2b orphan-empty-line / orphan-ws-line: blanks are leftsimilar too.
        let g = align(
            &s(&["int x;", ""]),
            &s(&["int x;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "leftsimilar"]);
        let g = align(
            &s(&["   ", "int x;"]),
            &s(&["int x;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["leftsimilar", "same"]);
    }

    // ---------------------------------------------------------------
    // End-to-end alignment, one test per golden anchor that pins the
    // status sequence.
    // ---------------------------------------------------------------

    #[test]
    fn anchor_al_identical() {
        let g = align(&s(&["x", "y"]), &s(&["x", "y"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(statuses(&g), vec!["same", "same"]);
    }

    #[test]
    fn anchor_al_insert_and_delete() {
        let g = align(&s(&["a", "c"]), &s(&["a", "b", "c"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(statuses(&g), vec!["same", "rightorphan", "same"]);
        let g = align(&s(&["a", "b", "c"]), &s(&["a", "c"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(statuses(&g), vec!["same", "leftorphan", "same"]);
    }

    #[test]
    fn anchor_al_replace_block() {
        let g = align(
            &s(&["h1", "x", "y", "z", "h2"]),
            &s(&["h1", "p", "q", "r", "h2"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(
            statuses(&g),
            vec!["same", "different", "different", "different", "same"]
        );
    }

    #[test]
    fn anchor_al_move_down() {
        let g = align(
            &s(&["a", "b", "c", "d"]),
            &s(&["a", "c", "d", "b"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(
            statuses(&g),
            vec!["same", "leftorphan", "same", "same", "rightorphan"]
        );
    }

    #[test]
    fn anchor_al_swap_blocks() {
        let g = align(
            &s(&["a", "b", "c", "d"]),
            &s(&["c", "d", "a", "b"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(
            statuses(&g),
            vec!["leftorphan", "leftorphan", "same", "same", "rightorphan", "rightorphan"]
        );
        assert_eq!(g[2].left, Some(2));
        assert_eq!(g[2].right, Some(0));
    }

    #[test]
    fn anchor_al_duplicates_resolves_forward_first() {
        // THE milestone's flagged regression risk. L = x,x,x  R = x,x must give
        // same, same, leftorphan — with the orphan LAST.
        let g = align(&s(&["x", "x", "x"]), &s(&["x", "x"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(statuses(&g), vec!["same", "same", "leftorphan"]);
        assert_eq!(g[0].left, Some(0));
        assert_eq!(g[0].right, Some(0));
        assert_eq!(g[1].left, Some(1));
        assert_eq!(g[1].right, Some(1));
        assert_eq!(g[2].left, Some(2));
        assert_eq!(g[2].right, None);
    }

    #[test]
    fn anchor_al_empty_left_and_both() {
        let g = align(&s(&[]), &s(&["only"]), Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(statuses(&g), vec!["rightorphan"]);
        let g = align(&s(&[]), &s(&[]), Grammar::PlainText, &mut no_cancel()).unwrap();
        assert!(g.is_empty());
    }

    #[test]
    fn anchor_al_similar_then_diff() {
        let g = align(
            &s(&["same", "beta", "diff1"]),
            &s(&["same", "BETA", "diff2"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["same", "similar", "different"]);
    }

    #[test]
    fn anchor_opt_pair_sequence() {
        // The opt-* anchors all use this pair; with display-all the baseline is
        // same, same, similar, similar, different, same.
        let l = s(&["same line", "case diff", "Case Diff", "ws diff ", "real diff 1", "real diff 2"]);
        let r = s(&["same line", "case diff", "CASE DIFF", "ws diff", "real diff 9", "real diff 2"]);
        let g = align(&l, &r, Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(
            statuses(&g),
            vec!["same", "same", "similar", "similar", "different", "same"]
        );
        assert_eq!(g[2].left, Some(2));
        assert_eq!(g[2].right, Some(2));
        assert_eq!(g[4].left, Some(4));
        assert_eq!(g[4].right, Some(4));
    }

    #[test]
    fn anchor_comment_c_aligns_comments_with_comments() {
        use crate::importance::Grammar;
        let g = align(
            &s(&["// old note", "x;"]),
            &s(&["// new note", "x;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(statuses(&g), vec!["similar", "same"]);
        assert_eq!(g[0].left, Some(0));
        assert_eq!(g[0].right, Some(0));
    }

    #[test]
    fn anchor_ws_and_case_anchors_classify_correctly() {
        use crate::importance::Grammar;
        let cases: [(&[&str], &[&str], Grammar, &str); 5] = [
            (&["a ", "b"], &["a", "b"], Grammar::PlainText, "similar"),
            (&["  a", "b"], &["a", "b"], Grammar::PlainText, "similar"),
            (&["a\tb"], &["a b"], Grammar::PlainText, "similar"),
            (&["void main( )"], &["void main()"], Grammar::PlainText, "similar"),
            (&["alpha"], &["ALPHA"], Grammar::PlainText, "similar"),
        ];
        for (l, r, gram, want) in cases {
            let g = align(&s(l), &s(r), gram, &mut no_cancel()).unwrap();
            assert_eq!(g[0].status.as_xml(), want, "{l:?} vs {r:?}");
        }
        let g = align(
            &s(&["int Abc = 1;"]),
            &s(&["int abc = 1;"]),
            Grammar::Cpp,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(g[0].status.as_xml(), "different");
    }

    // ---------------------------------------------------------------
    // Sections
    // ---------------------------------------------------------------

    #[test]
    fn difference_sections_match_the_layout_corpus() {
        // mixed: same / {different block of 5} / same  -> 1 section
        let l = s(&["same line", "case diff", "Case Diff", "ws diff ", "real diff 1", "real diff 2"]);
        let r = s(&["same line", "case diff", "CASE DIFF", "ws diff", "real diff 9", "real diff 2"]);
        let g = align(&l, &r, Grammar::PlainText, &mut no_cancel()).unwrap();
        assert_eq!(difference_sections(&g), 1);

        // orphans: {left} / same / {right} -> 2 sections
        let g = align(
            &s(&["only-left", "shared"]),
            &s(&["shared", "only-right"]),
            Grammar::PlainText,
            &mut no_cancel(),
        )
        .unwrap();
        assert_eq!(difference_sections(&g), 2);

        // identical: no sections at all
        let g = align(&s(&["x", "y"]), &s(&["x", "y"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(difference_sections(&g), 0);
    }

    #[test]
    fn more_than_one_pair_of_same_lines_is_one_section() {
        // similar: {similar} / same -> 1 section
        let g = align(&s(&["alpha", "beta"]), &s(&["ALPHA", "beta"]), Grammar::PlainText, &mut no_cancel())
            .unwrap();
        assert_eq!(difference_sections(&g), 1);
    }

    // ---------------------------------------------------------------
    // Error propagation
    // ---------------------------------------------------------------

    #[test]
    fn cancellation_propagates_out_of_align() {
        let l = s(&["a", "b", "c"]);
        let r = s(&["c", "b", "a"]);
        let err = align(&l, &r, Grammar::PlainText, &mut || true).unwrap_err();
        assert_eq!(err, DiffError::Cancelled);
    }

    #[test]
    fn groups_are_in_document_order_and_cover_every_line_once() {
        let l = s(&["a", "b", "c", "d", "e"]);
        let r = s(&["a", "x", "c", "y", "y", "e"]);
        let g = align(&l, &r, Grammar::PlainText, &mut no_cancel()).unwrap();
        let mut seen_l = Vec::new();
        let mut seen_r = Vec::new();
        for group in &g {
            if let Some(i) = group.left {
                seen_l.push(i);
            }
            if let Some(j) = group.right {
                seen_r.push(j);
            }
        }
        assert_eq!(seen_l, (0..l.len()).collect::<Vec<_>>(), "left indices must be complete and ordered");
        assert_eq!(seen_r, (0..r.len()).collect::<Vec<_>>(), "right indices must be complete and ordered");
    }

    #[test]
    fn status_xml_names_are_the_observed_vocabulary() {
        assert_eq!(Status::Same.as_xml(), "same");
        assert_eq!(Status::Similar.as_xml(), "similar");
        assert_eq!(Status::Different.as_xml(), "different");
        assert_eq!(Status::LeftOrphan.as_xml(), "leftorphan");
        assert_eq!(Status::RightOrphan.as_xml(), "rightorphan");
        assert_eq!(Status::LeftSimilar.as_xml(), "leftsimilar");
        assert_eq!(Status::RightSimilar.as_xml(), "rightsimilar");
        assert!(Status::LeftOrphan.is_orphan());
        assert!(Status::LeftSimilar.is_orphan());
        assert!(!Status::Same.is_orphan());
        assert!(Status::RightSimilar.folds_to_same());
        assert!(!Status::LeftOrphan.folds_to_same());
    }
}

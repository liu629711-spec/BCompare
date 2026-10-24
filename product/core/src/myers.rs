//! M1.3 — Myers linear-space (divide-and-conquer) matching core.
//!
//! # Why this module exists
//!
//! `clone/src/align.rs` used an LCS DP over an `n x m` matrix: `O(n*m)` time and
//! memory, unusable on large files. Beyond Compare uses the linear-space variant
//! of Myers' algorithm. The structural evidence is **O**bserved:
//!
//! * `report-algorithm.md` §2 and `extracted/pseudocode/140dc5d80.c` — two
//!   arrays of `(2*D_max+1)*4` bytes, base-shifted so that negative diagonal
//!   indices are addressable;
//! * `extracted/pseudocode/140dc60b0.c` — diagonal traversal with step 2 in both
//!   the forward and the reverse loop; a `delta & 1` parity branch selecting in
//!   which direction the overlap between the two searches is tested; and an
//!   immediate split into two halves on overlap (the space-saving bisection);
//! * `extracted/pseudocode/140dc5d80.c` — common prefix and suffix trimming
//!   before the search, plus an "identical, return early" branch;
//! * `extracted/pseudocode/140dc6d80.c` — one callback per `D` iteration, i.e.
//!   the cancellation seam;
//! * `extracted/pseudocode/140dc6a00.c` / `140dc6b20.c` — adjacent difference
//!   runs are *merged* rather than emitted one at a time. That belongs to the
//!   block layer and therefore lives in [`crate::align`]; this module returns
//!   matched pairs only and the caller derives maximal difference runs.
//!
//! # What this module computes
//!
//! A shortest edit script, expressed as the ordered list of matched index pairs
//! (strictly increasing in both coordinates). Unmatched elements form the
//! difference runs. Minimality — that the pairs form a *longest* common
//! subsequence — is asserted against a brute-force DP reference over thousands
//! of generated inputs in the tests.
//!
//! # Determinism and the duplicate-line rule
//!
//! There is no hashing order, no randomness and no timing input: the output is a
//! pure function of the two id sequences. Which of several equally short scripts
//! is returned is decided by the "furthest reaching" preference in the forward
//! loop (the insertion branch is taken only when it is *strictly* further along,
//! so the deletion branch wins ties). That preference is what makes repeated
//! lines resolve forward-first: anchor `al-duplicates` (`x,x,x` vs `x,x`) must be
//! `same, same, leftorphan`, not `leftorphan, same, same`.
//!
//! # Deliberately not replicated from the observed binary
//!
//! The decompiled loops also run `k` past `D` up to an array-edge bound and read
//! sentinel V entries at `V[n]` / `V[delta]`. Those are allocation/locality
//! micro-optimisations: they change which intermediate cells are written, never
//! which minimal script is produced. They are **not** reproduced here because
//! they cannot be validated without executing the binary, which this milestone
//! must not do. This is recorded in `README.md` as an unresolved micro-detail —
//! it is not presented as equivalent to the original.

use std::collections::HashMap;
use std::hash::Hash;

/// Failure modes. All are explicit; none yields a placeholder result.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiffError {
    /// The caller's progress callback asked to stop.
    Cancelled,
    /// The search ran out of `D` iterations without finding an overlap. Myers'
    /// theorem makes this unreachable; it exists so a hypothetical defect
    /// surfaces loudly rather than returning a wrong script.
    SearchExhausted,
    /// A sub-problem could not be reduced even though it still contains a common
    /// element. Unreachable by construction; kept explicit so that an
    /// algorithmic regression can never manifest as an infinite loop or a
    /// silently truncated script.
    NoProgress,
    /// The inputs exceed the diagonal-index limit (see [`MAX_DIAGONAL`]).
    TooLarge { needed: usize, limit: usize },
}

impl std::fmt::Display for DiffError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DiffError::Cancelled => write!(f, "comparison cancelled"),
            DiffError::SearchExhausted => {
                write!(f, "alignment search exhausted its D budget without meeting")
            }
            DiffError::NoProgress => write!(
                f,
                "alignment could not split a sub-problem that still has common elements"
            ),
            DiffError::TooLarge { needed, limit } => write!(
                f,
                "inputs too large: {needed} combined elements exceed the {limit}-element \
                 alignment diagonal limit"
            ),
        }
    }
}

impl std::error::Error for DiffError {}

/// Upper bound on `n + m`, i.e. the largest diagonal index the V buffers must
/// address. The same `0xffffff` clamp is observed in `140dc5d80.c`.
pub const MAX_DIAGONAL: usize = 0x00FF_FFFF;

/// Reduce two sequences to dense integer ids.
///
/// Sharing one integer alphabet makes the Myers core independent of the payload
/// type (lines, records, byte blocks), which is the sequence→hash reduction step
/// of `03-architecture-options.md` §1 and lets every engine reuse this one
/// implementation. Ids are assigned in first-seen order over `a` then `b`, so
/// the mapping is a deterministic function of the inputs.
pub fn map_ids<T: Hash + Eq>(a: &[T], b: &[T]) -> (Vec<usize>, Vec<usize>) {
    let mut ids: HashMap<&T, usize> = HashMap::new();
    let mut left = Vec::with_capacity(a.len());
    for x in a {
        let next = ids.len();
        left.push(*ids.entry(x).or_insert(next));
    }
    let mut right = Vec::with_capacity(b.len());
    for x in b {
        let next = ids.len();
        right.push(*ids.entry(x).or_insert(next));
    }
    (left, right)
}

/// Reusable `O(n + m)` scratch: the two V arrays, allocated once for the root
/// problem.
///
/// `vf` is indexed by the **absolute** diagonal `k = x - y` and holds the
/// furthest-reaching `x`. `ur` is indexed by the **reverse-space** diagonal
/// `j = u - v` (where `u = n - x`) and holds the furthest-reaching `u`; the
/// matching absolute diagonal is `delta - j`. Using reverse space for the
/// reverse search makes its recurrence a literal mirror of the forward one,
/// which is what the observed binary's second loop does.
struct Scratch {
    vf: Vec<i32>,
    ur: Vec<i32>,
    /// Diagonal index that maps to array slot 0.
    offset: i32,
}

impl Scratch {
    fn new(n: usize, m: usize) -> Result<Self, DiffError> {
        let d_max = n + m;
        if d_max > MAX_DIAGONAL {
            return Err(DiffError::TooLarge { needed: d_max, limit: MAX_DIAGONAL });
        }
        // 2*D_max+1 entries, base-shifted so index -(D_max) lands at slot 0 —
        // the same allocation shape as the observed FUN_140dc5d80.
        let len = 2 * d_max + 1;
        Ok(Scratch { vf: vec![0; len], ur: vec![0; len], offset: d_max as i32 })
    }
}

/// Array slot for a signed diagonal index.
///
/// A free function rather than a method: as a method it would hold an immutable
/// borrow of `Scratch` while the call site needs a mutable one, and the borrow
/// checker is right to reject that. `offset` is the only state it needs.
#[inline]
fn slot(offset: i32, k: i32) -> usize {
    (offset + k) as usize
}

/// Find the middle snake of `a[a_lo..a_hi]` vs `b[b_lo..b_hi]`.
///
/// Returns the run in absolute coordinates: pairs `(a_start..a_end)` matched with
/// `(b_start..b_end)`. `cancel` is invoked once per `D` iteration — the same seam
/// as `FUN_140dc6d80`.
///
/// The two V buffers are caller-owned scratch, so a single pair serves every
/// sub-problem (each call finishes before its children start).
#[allow(clippy::too_many_arguments)]
fn middle_snake(
    a: &[usize],
    b: &[usize],
    a_lo: usize,
    a_hi: usize,
    b_lo: usize,
    b_hi: usize,
    scratch: &mut Scratch,
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Run, DiffError> {
    let n = (a_hi - a_lo) as i32;
    let m = (b_hi - b_lo) as i32;
    debug_assert!(n > 0 && m > 0, "middle_snake requires a non-empty rectangle");
    let delta = n - m;
    let odd = (delta & 1) != 0;
    // Myers' theorem: an overlap is guaranteed by D = ceil((n + m) / 2).
    let d_bound = (n + m + 1) / 2;

    // Forward seed: V[1] = 0 makes the D = 0 read at k = 0 well defined.
    scratch.vf[slot(scratch.offset, 1)] = 0;
    // Reverse seed: same, in reverse space.
    scratch.ur[slot(scratch.offset, 1)] = 0;

    for d in 0..=d_bound {
        // ---- forward pass: absolute diagonals k = -d, -d+2, ..., d ----
        let mut k = -d;
        while k <= d {
            // "Furthest reaching": take V[k+1] (insertion) only when it is
            // strictly further along, so the deletion branch wins ties. This is
            // the observed `V[k-1] < V[k+1]` test, and it is what makes repeated
            // lines resolve forward-first.
            let mut x = if k == -d
                || (k != d && scratch.vf[slot(scratch.offset, k - 1)] < scratch.vf[slot(scratch.offset, k + 1)])
            {
                scratch.vf[slot(scratch.offset, k + 1)]
            } else {
                scratch.vf[slot(scratch.offset, k - 1)] + 1
            };
            let mut y = x - k;
            while x < n && y < m && a[a_lo + x as usize] == b[b_lo + y as usize] {
                x += 1;
                y += 1;
            }
            scratch.vf[slot(scratch.offset, k)] = x;

            // A forward D-path can only meet a reverse (D-1)-path when delta is
            // odd — the observed `delta & 1` branch. Reverse-space diagonals
            // computed so far span j in [-(d-1), d-1], i.e. absolute diagonals
            // k = delta - j in [delta-(d-1), delta+(d-1)].
            if odd && k >= delta - (d - 1) && k <= delta + (d - 1) {
                let j = delta - k;
                // Reverse space reaches u; the absolute point is n - u. They
                // overlap when the reverse reach is at or before the forward one.
                if n - scratch.ur[slot(scratch.offset, j)] <= x {
                    // The snake is the matching run ENDING at the forward point
                    // (x, y): `x` and `y` are local, so translate to absolute.
                    return Ok(snake_around(
                        a,
                        b,
                        a_lo,
                        a_hi,
                        b_lo,
                        b_hi,
                        a_lo + x as usize,
                        b_lo + y as usize,
                    ));
                }
            }
            k += 2;
        }

        // ---- reverse pass: reverse diagonals j = -d, -d+2, ..., d ----
        let mut j = -d;
        while j <= d {
            let mut u = if j == -d
                || (j != d && scratch.ur[slot(scratch.offset, j - 1)] < scratch.ur[slot(scratch.offset, j + 1)])
            {
                scratch.ur[slot(scratch.offset, j + 1)]
            } else {
                scratch.ur[slot(scratch.offset, j - 1)] + 1
            };
            let mut v = u - j;
            while u < n && v < m && a[a_hi - 1 - u as usize] == b[b_hi - 1 - v as usize] {
                u += 1;
                v += 1;
            }
            scratch.ur[slot(scratch.offset, j)] = u;

            // A reverse D-path meets a forward D-path when delta is even. The
            // absolute diagonal of this reverse-space diagonal is delta - j.
            if !odd {
                let k = delta - j;
                if k >= -d && k <= d && n - u <= scratch.vf[slot(scratch.offset, k)] {
                    // The snake is the matching run STARTING at the reverse
                    // path's frontier, which in absolute coordinates is
                    // (a_lo + n - u, b_lo + m - v): `n - u` is local.
                    return Ok(snake_around(
                        a,
                        b,
                        a_lo,
                        a_hi,
                        b_lo,
                        b_hi,
                        a_lo + (n - u) as usize,
                        b_lo + (m - v) as usize,
                    ));
                }
            }
            j += 2;
        }

        // Cancellation is polled once per D iteration, after both passes — the
        // placement of the observed FUN_140dc6d80 call at the top of the loop.
        if cancel() {
            return Err(DiffError::Cancelled);
        }
    }
    Err(DiffError::SearchExhausted)
}

/// A maximal matching run in absolute coordinates.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Run {
    a_start: usize,
    a_end: usize,
    b_start: usize,
    b_end: usize,
}

impl Run {
    fn is_empty(&self) -> bool {
        self.a_start == self.a_end
    }
    fn len(&self) -> usize {
        self.a_end - self.a_start
    }
}

/// Extend a split point into the maximal matching run that contains it.
///
/// The split point is guaranteed to be a *matching* pair (`a[x] == b[y]`) or a
/// boundary; walking outward from it yields the middle snake of the paper.
#[allow(clippy::too_many_arguments)]
fn snake_around(
    a: &[usize],
    b: &[usize],
    a_lo: usize,
    a_hi: usize,
    b_lo: usize,
    b_hi: usize,
    mut x: usize,
    mut y: usize,
) -> Run {
    let (mut ex, mut ey) = (x, y);
    if x < a_hi && y < b_hi && a[x] == b[y] {
        while ex < a_hi && ey < b_hi && a[ex] == b[ey] {
            ex += 1;
            ey += 1;
        }
    }
    while x > a_lo && y > b_lo && a[x - 1] == b[y - 1] {
        x -= 1;
        y -= 1;
    }
    Run { a_start: x, a_end: ex, b_start: y, b_end: ey }
}

/// True when no value of the smaller side occurs in the larger side, i.e. the
/// longest common subsequence of the rectangle is empty.
///
/// Only called on small rectangles and on the degenerate-split path, so its
/// `O(min(n, m))` cost is never on the hot path.
fn lcs_is_empty(a: &[usize], b: &[usize], a_lo: usize, a_hi: usize, b_lo: usize, b_hi: usize) -> bool {
    let (small, large) = if a_hi - a_lo <= b_hi - b_lo {
        (&a[a_lo..a_hi], &b[b_lo..b_hi])
    } else {
        (&b[b_lo..b_hi], &a[a_lo..a_hi])
    };
    let set: std::collections::HashSet<usize> = small.iter().copied().collect();
    !large.iter().any(|v| set.contains(v))
}

/// One unit of work for the explicit recursion stack.
///
/// The divide-and-conquer is iterative on purpose: deep splits on large inputs
/// would otherwise risk a native stack overflow, and an explicit stack keeps peak
/// memory proportional to the problem rather than to the recursion depth.
enum Job {
    Range { a_lo: usize, a_hi: usize, b_lo: usize, b_hi: usize },
    EmitRun { a_start: usize, b_start: usize, len: usize },
}

/// Directly resolve a rectangle that contains no match at all: every element is
/// unmatched. Correct because an empty LCS makes the shortest edit script
/// "delete everything, insert everything", whose cost `n + m` is minimal.
///
/// Takes the trimmed suffix as a parameter so the two call sites read
/// identically and cannot diverge.
fn emit_unmatched_then_suffix(
    out: &mut Vec<(usize, usize)>,
    a_hi: usize,
    b_hi: usize,
    suf: usize,
) {
    if suf > 0 {
        out.reserve(suf);
        for i in 0..suf {
            out.push((a_hi - suf + i, b_hi - suf + i));
        }
    }
}

/// Build the matched-pair list, polling for cancellation once per `D` iteration.
///
/// `a` and `b` must already be reduced to comparable ids (see [`map_ids`]).
/// The returned pairs are strictly increasing in both coordinates.
pub fn diff_matches_cancellable(
    a: &[usize],
    b: &[usize],
    cancel: &mut dyn FnMut() -> bool,
) -> Result<Vec<(usize, usize)>, DiffError> {
    let mut out: Vec<(usize, usize)> = Vec::new();
    if a.is_empty() || b.is_empty() {
        return Ok(out);
    }
    let mut scratch = Scratch::new(a.len(), b.len())?;
    let mut stack: Vec<Job> = Vec::new();
    stack.push(Job::Range { a_lo: 0, a_hi: a.len(), b_lo: 0, b_hi: b.len() });

    while let Some(job) = stack.pop() {
        let (mut a_lo, a_hi, mut b_lo, b_hi) = match job {
            Job::EmitRun { a_start, b_start, len } => {
                out.reserve(len);
                for i in 0..len {
                    out.push((a_start + i, b_start + i));
                }
                continue;
            }
            Job::Range { a_lo, a_hi, b_lo, b_hi } => (a_lo, a_hi, b_lo, b_hi),
        };

        // ---- common prefix trim (observed in FUN_140dc5d80) ----
        let mut pre = 0usize;
        while a_lo + pre < a_hi && b_lo + pre < b_hi && a[a_lo + pre] == b[b_lo + pre] {
            pre += 1;
        }
        if pre > 0 {
            out.reserve(pre);
            for i in 0..pre {
                out.push((a_lo + i, b_lo + i));
            }
            a_lo += pre;
            b_lo += pre;
        }
        if a_lo == a_hi || b_lo == b_hi {
            // One side is exhausted: every remaining element is unmatched.
            continue;
        }

        // ---- common suffix trim (observed in FUN_140dc5d80) ----
        let mut suf = 0usize;
        while a_hi - suf > a_lo && b_hi - suf > b_lo && a[a_hi - 1 - suf] == b[b_hi - 1 - suf] {
            suf += 1;
        }
        let (a_hi_in, b_hi_in) = (a_hi - suf, b_hi - suf);
        if a_lo == a_hi_in || b_lo == b_hi_in {
            // No middle to solve; the trimmed suffix still matches.
            if suf > 0 {
                out.reserve(suf);
                for i in 0..suf {
                    out.push((a_hi - suf + i, b_hi - suf + i));
                }
            }
            continue;
        }

        // ---- small-rectangle base cases ----
        //
        // A one-element rectangle has a trivially computable minimum: match the
        // element with its FIRST occurrence on the other side (which is both
        // minimal and the forward-first choice), or nothing if it is absent.
        // Handling it here keeps the middle-snake search away from the corner
        // degeneracies a 1xN rectangle produces.
        if a_hi_in - a_lo == 1 || b_hi_in - b_lo == 1 {
            emit_single_match(&mut out, a, b, a_lo, a_hi_in, b_lo, b_hi_in);
            emit_unmatched_then_suffix(&mut out, a_hi, b_hi, suf);
            continue;
        }
        // An empty LCS is a legitimate "no common element" rectangle: nothing to
        // match. Checked only for small rectangles so the hot path stays free of
        // the extra pass; the degenerate-split path below covers the rest.
        if (a_hi_in - a_lo).min(b_hi_in - b_lo) <= 32
            && lcs_is_empty(a, b, a_lo, a_hi_in, b_lo, b_hi_in)
        {
            emit_unmatched_then_suffix(&mut out, a_hi, b_hi, suf);
            continue;
        }

        // ---- middle snake of the remaining rectangle ----
        let run = middle_snake(a, b, a_lo, a_hi_in, b_lo, b_hi_in, &mut scratch, cancel)?;

        // A split at a corner would re-enter this same rectangle and never
        // shrink it. That is only legitimate when the rectangle genuinely has no
        // common element; anything else is an algorithmic defect and must fail
        // loudly rather than loop or truncate.
        let at_start = run.a_start == a_lo && run.b_start == b_lo;
        let at_end = run.a_end == a_hi_in && run.b_end == b_hi_in;
        if run.is_empty() && (at_start || at_end) {
            if lcs_is_empty(a, b, a_lo, a_hi_in, b_lo, b_hi_in) {
                emit_unmatched_then_suffix(&mut out, a_hi, b_hi, suf);
                continue;
            }
            return Err(DiffError::NoProgress);
        }

        // Document order for this rectangle is: prefix (emitted above), left
        // sub-problem, this run, right sub-problem, suffix. Push in reverse so
        // the LIFO pops reproduce that order without ever sorting `out`.
        if suf > 0 {
            stack.push(Job::EmitRun { a_start: a_hi - suf, b_start: b_hi - suf, len: suf });
        }
        stack.push(Job::Range { a_lo: run.a_end, a_hi: a_hi_in, b_lo: run.b_end, b_hi: b_hi_in });
        if run.len() > 0 {
            stack.push(Job::EmitRun {
                a_start: run.a_start,
                b_start: run.b_start,
                len: run.len(),
            });
        }
        stack.push(Job::Range { a_lo, a_hi: run.a_start, b_lo, b_hi: run.b_start });
    }

    debug_assert!(
        out.windows(2).all(|w| w[0].0 < w[1].0 && w[0].1 < w[1].1),
        "matched pairs must be strictly increasing in both coordinates"
    );
    Ok(out)
}

/// Resolve a rectangle where one side has exactly one element.
fn emit_single_match(
    out: &mut Vec<(usize, usize)>,
    a: &[usize],
    b: &[usize],
    a_lo: usize,
    a_hi: usize,
    b_lo: usize,
    b_hi: usize,
) {
    if a_hi - a_lo == 1 {
        let value = a[a_lo];
        if let Some(off) = b[b_lo..b_hi].iter().position(|v| *v == value) {
            out.push((a_lo, b_lo + off));
        }
    } else {
        debug_assert!(b_hi - b_lo == 1);
        let value = b[b_lo];
        if let Some(off) = a[a_lo..a_hi].iter().position(|v| *v == value) {
            out.push((a_lo + off, b_lo));
        }
    }
}

/// Convenience wrapper: diff without cancellation.
pub fn diff_matches(a: &[usize], b: &[usize]) -> Result<Vec<(usize, usize)>, DiffError> {
    diff_matches_cancellable(a, b, &mut || false)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ------------------------------------------------------------------
    // Brute-force reference: LCS length by O(n*m) DP. Test-only oracle for
    // minimality; deliberately the very algorithm production must not use.
    // ------------------------------------------------------------------
    fn lcs_len(a: &[usize], b: &[usize]) -> usize {
        let m = b.len();
        let mut prev = vec![0usize; m + 1];
        let mut cur = vec![0usize; m + 1];
        for i in (0..a.len()).rev() {
            for j in (0..m).rev() {
                cur[j] = if a[i] == b[j] { prev[j + 1] + 1 } else { prev[j].max(cur[j + 1]) };
            }
            std::mem::swap(&mut prev, &mut cur);
        }
        prev[0]
    }

    /// Deterministic xorshift, so the property tests are reproducible without a
    /// dependency and without a random seed.
    struct Rng(u64);
    impl Rng {
        fn next(&mut self) -> u64 {
            let mut x = self.0;
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            self.0 = x;
            x
        }
        fn below(&mut self, n: u64) -> u64 {
            self.next() % n
        }
    }

    fn check_minimal(a: &[usize], b: &[usize], pairs: &[(usize, usize)]) {
        let mut prev: Option<(usize, usize)> = None;
        for &(i, j) in pairs {
            assert!(i < a.len() && j < b.len(), "index out of range in {pairs:?}");
            if let Some((pi, pj)) = prev {
                assert!(i > pi && j > pj, "pairs not increasing: {prev:?} then ({i},{j})");
            }
            assert_eq!(a[i], b[j], "pair ({i},{j}) is not a match");
            prev = Some((i, j));
        }
        assert_eq!(
            pairs.len(),
            lcs_len(a, b),
            "not a longest common subsequence: a={a:?} b={b:?} got={pairs:?}"
        );
    }

    #[test]
    fn identical_sequences_match_everything() {
        let a = [1usize, 2, 3];
        assert_eq!(diff_matches(&a, &a).unwrap(), vec![(0, 0), (1, 1), (2, 2)]);
    }

    #[test]
    fn empty_sequences() {
        assert_eq!(diff_matches(&[], &[]).unwrap(), vec![]);
        assert_eq!(diff_matches(&[1], &[]).unwrap(), vec![]);
        assert_eq!(diff_matches(&[], &[1]).unwrap(), vec![]);
    }

    #[test]
    fn pure_insertion_and_deletion() {
        assert_eq!(diff_matches(&[1, 3], &[1, 2, 3]).unwrap(), vec![(0, 0), (1, 2)]);
        assert_eq!(diff_matches(&[1, 2, 3], &[1, 3]).unwrap(), vec![(0, 0), (2, 1)]);
    }

    #[test]
    fn adjacent_difference_runs_are_contiguous() {
        // Anchor al-replace-block: h1 x y z h2 vs h1 p q r h2. The three middle
        // pairs must be one contiguous unmatched run on each side.
        let a = [1usize, 2, 3, 4, 5];
        let b = [1usize, 6, 7, 8, 5];
        let pairs = diff_matches(&a, &b).unwrap();
        assert_eq!(pairs, vec![(0, 0), (4, 4)]);
    }

    #[test]
    fn duplicates_resolve_forward_first() {
        // Anchor al-duplicates: L = x,x,x  R = x,x  -> same, same, leftorphan.
        // Forward-first means the LAST left line is the orphan, i.e. pairs
        // (0,0) and (1,1) — not (0,0),(2,1) and not (1,0),(2,1).
        let a = [7usize, 7, 7];
        let b = [7usize, 7];
        assert_eq!(diff_matches(&a, &b).unwrap(), vec![(0, 0), (1, 1)]);
        // Mirror direction: an extra right line is the trailing orphan.
        assert_eq!(diff_matches(&b, &a).unwrap(), vec![(0, 0), (1, 1)]);
    }

    #[test]
    fn block_swap_has_no_move_detection() {
        // Anchor al-swap-blocks: a,b,c,d vs c,d,a,b — the script is
        // "delete a,b then insert a,b"; the LCS is exactly one block (length 2),
        // never a move.
        let a = [1usize, 2, 3, 4];
        let b = [3usize, 4, 1, 2];
        let pairs = diff_matches(&a, &b).unwrap();
        assert_eq!(pairs.len(), 2, "no move detection: LCS length must be 2");
        assert_eq!(pairs, vec![(2, 0), (3, 1)]);
    }

    #[test]
    fn move_down_pairs_the_shifted_line_as_orphan() {
        // Anchor al-move-down: a,b,c,d vs a,c,d,b.
        let a = [1usize, 2, 3, 4];
        let b = [1usize, 3, 4, 2];
        assert_eq!(diff_matches(&a, &b).unwrap(), vec![(0, 0), (2, 1), (3, 2)]);
    }

    #[test]
    fn unequal_replace_keeps_the_shared_ends() {
        // verify/disambig/unequal-replace: h1 x y h2 vs h1 p q r h2.
        let a = [1usize, 2, 3, 4];
        let b = [1usize, 5, 6, 7, 4];
        assert_eq!(diff_matches(&a, &b).unwrap(), vec![(0, 0), (3, 4)]);
    }

    #[test]
    fn no_common_element_yields_no_pairs() {
        assert_eq!(diff_matches(&[1, 2, 3], &[4, 5, 6]).unwrap(), vec![]);
        assert_eq!(diff_matches(&[1], &[2]).unwrap(), vec![]);
        assert_eq!(diff_matches(&[1, 2], &[3, 4, 5]).unwrap(), vec![]);
        assert_eq!(diff_matches(&[3, 4, 5], &[1, 2]).unwrap(), vec![]);
    }

    #[test]
    fn single_element_matches_its_first_occurrence() {
        // Forward-first for a one-element side.
        assert_eq!(diff_matches(&[7], &[7, 7, 7]).unwrap(), vec![(0, 0)]);
        assert_eq!(diff_matches(&[8, 7], &[7]).unwrap(), vec![(1, 0)]);
    }

    #[test]
    fn random_inputs_are_always_minimal() {
        let mut rng = Rng(0x1234_5678_9abc_def0);
        for _ in 0..4000 {
            let n = rng.below(10) as usize;
            let m = rng.below(10) as usize;
            let alphabet = 1 + rng.below(3) as usize; // tiny alphabet => duplicates
            let a: Vec<usize> = (0..n).map(|_| rng.below(alphabet as u64) as usize).collect();
            let b: Vec<usize> = (0..m).map(|_| rng.below(alphabet as u64) as usize).collect();
            let pairs = diff_matches(&a, &b).expect("search must terminate");
            check_minimal(&a, &b, &pairs);
        }
    }

    #[test]
    fn random_binary_inputs_are_always_minimal() {
        let mut rng = Rng(0xdead_beef_cafe_0001);
        for _ in 0..800 {
            let n = rng.below(40) as usize;
            let m = rng.below(40) as usize;
            let a: Vec<usize> = (0..n).map(|_| rng.below(2) as usize).collect();
            let b: Vec<usize> = (0..m).map(|_| rng.below(2) as usize).collect();
            let pairs = diff_matches(&a, &b).expect("search must terminate");
            check_minimal(&a, &b, &pairs);
        }
    }

    #[test]
    fn random_wide_alphabet_inputs_are_always_minimal() {
        let mut rng = Rng(0x0f0f_0f0f_1234_5678);
        for _ in 0..400 {
            let n = rng.below(30) as usize;
            let m = rng.below(30) as usize;
            let a: Vec<usize> = (0..n).map(|_| rng.below(97) as usize).collect();
            let b: Vec<usize> = (0..m).map(|_| rng.below(97) as usize).collect();
            let pairs = diff_matches(&a, &b).expect("search must terminate");
            check_minimal(&a, &b, &pairs);
        }
    }

    #[test]
    fn alternating_patterns_are_minimal() {
        // Adversarial shapes that hit the parity branches hardest.
        let cases: [(&[usize], &[usize]); 6] = [
            (&[1, 2, 1, 2, 1, 2], &[2, 1, 2, 1, 2, 1]),
            (&[1, 1, 2, 2, 3, 3], &[1, 2, 3, 1, 2, 3]),
            (&[1, 2, 3, 1, 2, 3], &[3, 2, 1, 3, 2, 1]),
            (&[1, 1, 1, 1], &[1, 1]),
            (&[5, 5, 5], &[5, 5, 5, 5, 5]),
            (&[1, 2, 3, 4, 5, 6, 7], &[2, 4, 6, 1, 3, 5, 7]),
        ];
        for (a, b) in cases {
            let pairs = diff_matches(a, b).expect("search must terminate");
            check_minimal(a, b, &pairs);
        }
    }

    #[test]
    fn long_common_prefix_and_suffix_are_fully_matched() {
        let mut a: Vec<usize> = (0..500).collect();
        let mut b: Vec<usize> = (0..500).collect();
        a.push(9999);
        b.push(9998);
        let pairs = diff_matches(&a, &b).unwrap();
        assert_eq!(pairs, (0..500).map(|i| (i, i)).collect::<Vec<_>>());
    }

    #[test]
    fn cancellation_is_polled_and_reported() {
        // Two 500-element sides with no common element force many D rounds.
        let a: Vec<usize> = (0..500).map(|i| i * 2).collect();
        let b: Vec<usize> = (0..500).map(|i| i * 2 + 1).collect();
        let mut calls = 0usize;
        let err = diff_matches_cancellable(&a, &b, &mut || {
            calls += 1;
            true
        })
        .unwrap_err();
        assert_eq!(err, DiffError::Cancelled);
        assert_eq!(calls, 1, "the callback fires once per D iteration");
    }

    #[test]
    fn cancellation_never_returns_an_empty_success() {
        let a: Vec<usize> = (0..200).map(|i| i % 3).collect();
        let b: Vec<usize> = (0..200).map(|i| (i + 1) % 3).collect();
        let result = diff_matches_cancellable(&a, &b, &mut || true);
        assert!(result.is_err(), "a cancelled search must not report success");
    }

    #[test]
    fn no_cancellation_when_the_callback_says_no() {
        assert_eq!(
            diff_matches_cancellable(&[1, 2, 3], &[1, 3], &mut || false).unwrap(),
            vec![(0, 0), (2, 1)]
        );
    }

    #[test]
    fn map_ids_is_deterministic_and_preserves_equality() {
        let (ia, ib) = map_ids(&["x", "y", "x"], &["y", "z"]);
        assert_eq!(ia, vec![0, 1, 0]);
        assert_eq!(ib, vec![1, 2]);
        assert_eq!(ia, map_ids(&["x", "y", "x"], &["y", "z"]).0);
    }

    #[test]
    fn oversized_inputs_fail_explicitly() {
        // The guard is on the diagonal budget, so it is checked without
        // allocating the buffers: construct ids long enough to trip it.
        let err = match Scratch::new(MAX_DIAGONAL + 1, 1) {
            Ok(_) => panic!("a 0xffffff+1 diagonal budget must be refused"),
            Err(e) => e,
        };
        assert!(matches!(err, DiffError::TooLarge { .. }));
        assert!(err.to_string().contains("too large"));
    }

    #[test]
    fn error_display_is_informative() {
        assert!(DiffError::Cancelled.to_string().contains("cancel"));
        assert!(DiffError::NoProgress.to_string().contains("split"));
        assert!(DiffError::SearchExhausted.to_string().contains("budget"));
    }
}

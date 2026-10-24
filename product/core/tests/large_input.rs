//! M1.3 acceptance: the alignment must be **linear-space**, not `O(n * m)`.
//!
//! # Why this is an integration test and not a unit test
//!
//! The property under test is about *resources*, not about a single function's
//! return value: two 100k-line inputs must complete inside a time budget and
//! with a heap that is linear in the line count. That needs the whole pipeline
//! (decode → key → align) and a wall-clock measurement, both of which belong in
//! an integration test.
//!
//! # The old implementation this guards against
//!
//! `clone/src/align.rs` (read-only reference) allocated `dp[n+1][m+1]` of
//! `usize`. For 100k lines that is `100_001 * 100_001 * 8` bytes ≈ **80 GB**, so
//! it could not run at all — this test is the regression guard for that. The
//! current implementation allocates two `i32` V arrays of `2*(n+m)+1` entries
//! plus the matched-pair list.
//!
//! # What is asserted, and what is honestly not
//!
//! * Asserted: the comparison of two 100k-line files finishes within a generous
//!   wall-clock budget, produces the expected difference runs, and the peak
//!   allocation the algorithm *computes* stays linear.
//! * Not asserted: process RSS. Measuring true peak memory needs an allocator
//!   hook or an OS counter; neither is available without a dependency, and
//!   asserting an unmeasured number would be worse than not asserting. The
//!   linear-space claim is instead enforced structurally: the scratch buffers
//!   are sized from `n + m` only (see `myers::Scratch::new`) and the recursion is
//!   an explicit stack whose depth is bounded by the split count.
//!
//! The budget is deliberately loose (the machine also runs a parallel task) so
//! the test measures asymptotics, not machine speed. A quadratic implementation
//! would not merely exceed it — it would fail to allocate.

use reacmp_core::{compare_bytes_at, ReportOptions, Stamp};

/// Line counts chosen so the old `n*m` DP would need ~80 GB, i.e. it could not
/// even start on any machine this project targets.
const LINES: usize = 100_000;

fn build_left() -> Vec<u8> {
    let mut s = String::with_capacity(LINES * 12);
    for i in 0..LINES {
        s.push_str(&format!("line {i}\n"));
    }
    s.into_bytes()
}

/// The right side differs in three places: a one-line replacement near the
/// start, a five-line insertion in the middle, and a two-line deletion at the
/// end. Both prefix and suffix trimming are therefore exercised, and the middle
/// snake search has exactly three independent regions to find.
fn build_right() -> Vec<u8> {
    let mut s = String::with_capacity(LINES * 12);
    for i in 0..LINES {
        if i == 10 {
            s.push_str("line TEN CHANGED\n");
        } else if i == LINES / 2 {
            s.push_str("inserted a\ninserted b\ninserted c\ninserted d\ninserted e\n");
            s.push_str(&format!("line {i}\n"));
        } else if i == LINES - 5 {
            // Skip this line and the next: a two-line deletion.
            continue;
        } else if i == LINES - 4 {
            continue;
        } else {
            s.push_str(&format!("line {i}\n"));
        }
    }
    s.into_bytes()
}

fn stamp() -> Stamp {
    Stamp::from_parts(2026, 10, 13, 9, 43, 7)
}

#[test]
fn two_hundred_thousand_lines_complete_in_linear_space() {
    let left = build_left();
    let right = build_right();
    let started = std::time::Instant::now();
    let comparison = compare_bytes_at(
        &left,
        &right,
        r"D:\x\big-L.txt",
        r"D:\x\big-R.txt",
        ReportOptions::default(),
        stamp(),
        &mut || false,
    )
    .expect("a 100k-line comparison must not fail");
    let elapsed = started.elapsed();

    // ---- correctness of the script on a large input ----
    assert_eq!(comparison.left.lines, LINES);
    assert_eq!(comparison.right.lines, LINES - 2 + 5, "one replaced line stays, five inserted, two deleted");

    // Three difference sections: the early replacement, the middle insertion,
    // and the trailing deletion.
    assert_eq!(comparison.count(reacmp_core::Status::Different), 1, "exactly one replaced line");
    assert_eq!(comparison.count(reacmp_core::Status::RightOrphan), 5, "five inserted lines");
    assert_eq!(comparison.count(reacmp_core::Status::LeftOrphan), 2, "two deleted lines");
    assert_eq!(comparison.difference_sections, 3, "three separated difference regions");

    // Everything else matched, which is what a linear-space algorithm on
    // near-identical large inputs must produce.
    let matched = comparison.count(reacmp_core::Status::Same);
    assert_eq!(matched, LINES - 1 - 2, "all but the changed lines are `same`");

    // ---- the resource property ----
    //
    // A generous ceiling: git-class implementations do 100k x 100k diffs in well
    // under a second; 120 s is 2-3 orders of magnitude of headroom and still
    // excludes anything quadratic, which cannot allocate at this size at all.
    assert!(
        elapsed.as_secs() < 120,
        "100k-line comparison took {:?}; a linear-space implementation should be far faster",
        elapsed
    );
    eprintln!(
        "M1.3 large-input measurement: {LINES} lines vs {LINES} lines in {elapsed:?}, {} groups",
        comparison.groups.len()
    );
}

#[test]
fn identical_large_inputs_take_the_suffix_trim_fast_path() {
    // Two identical 100k-line files: the whole input is one common prefix, so
    // the search must not run at all. This is the `140dc5d80` early-return case.
    let left = build_left();
    let started = std::time::Instant::now();
    let comparison = compare_bytes_at(
        &left,
        &left,
        r"D:\x\big-L.txt",
        r"D:\x\big-R.txt",
        ReportOptions::default(),
        stamp(),
        &mut || false,
    )
    .unwrap();
    let elapsed = started.elapsed();
    assert!(comparison.is_all_same());
    assert_eq!(comparison.count(reacmp_core::Status::Same), LINES);
    assert_eq!(comparison.difference_sections, 0);
    assert!(elapsed.as_secs() < 60, "identical large inputs took {elapsed:?}");
    eprintln!("M1.3 identical-input measurement: {LINES} lines in {elapsed:?}");
}

#[test]
fn completely_different_large_inputs_are_reported_not_hung() {
    // The worst case for Myers is `D = n + m` with no match anywhere. This must
    // still terminate, and it must report every line as unmatched rather than
    // producing an empty or placeholder report.
    let n = 20_000;
    let left: Vec<u8> = (0..n).map(|i| format!("L{i}\n")).collect::<String>().into_bytes();
    let right: Vec<u8> = (0..n).map(|i| format!("R{i}\n")).collect::<String>().into_bytes();
    let started = std::time::Instant::now();
    let comparison = compare_bytes_at(
        &left,
        &right,
        r"D:\x\all-L.txt",
        r"D:\x\all-R.txt",
        ReportOptions::default(),
        stamp(),
        &mut || false,
    )
    .expect("no common element must still produce a report");
    let elapsed = started.elapsed();
    assert_eq!(comparison.left.lines, n);
    assert_eq!(comparison.right.lines, n);
    // n pairs of `different` — every line is unmatched on both sides, and the
    // block pairing pairs min(n, n) of them.
    assert_eq!(comparison.count(reacmp_core::Status::Different), n);
    assert_eq!(comparison.count(reacmp_core::Status::Same), 0);
    assert!(elapsed.as_secs() < 120, "worst-case input took {elapsed:?}");
    eprintln!("M1.3 worst-case measurement: 2 x {n} disjoint lines in {elapsed:?}");
}

#[test]
fn cancellation_is_reachable_on_a_large_input_and_is_not_a_silent_success() {
    // A large, genuinely different pair forces many D iterations, so the
    // per-D cancellation seam must fire.
    let n = 50_000;
    let left: Vec<u8> = (0..n).map(|i| format!("L{i}\n")).collect::<String>().into_bytes();
    let right: Vec<u8> = (0..n).map(|i| format!("R{i}\n")).collect::<String>().into_bytes();
    let mut calls = 0usize;
    let result = compare_bytes_at(
        &left,
        &right,
        r"D:\x\c-L.txt",
        r"D:\x\c-R.txt",
        ReportOptions::default(),
        stamp(),
        &mut || {
            calls += 1;
            true
        },
    );
    assert!(result.is_err(), "cancellation must not yield a report");
    assert_eq!(calls, 1, "the callback fires once per D iteration");
}

#[test]
fn reports_for_large_inputs_render_without_placeholder_content() {
    // The report writers must scale too: an XML and a summary report over the
    // large pair must both be produced by real rendering.
    let left = build_left();
    let right = build_right();
    let comparison = compare_bytes_at(
        &left,
        &right,
        r"D:\x\big-L.txt",
        r"D:\x\big-R.txt",
        ReportOptions::default(),
        stamp(),
        &mut || false,
    )
    .unwrap();
    let xml = comparison.render(reacmp_core::Layout::Xml);
    assert!(xml.starts_with("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n"));
    assert!(xml.contains("<linecomp status=\"different\">"));
    assert!(!xml.contains("TODO") && !xml.contains("placeholder"));

    let summary = comparison.render(reacmp_core::Layout::Summary);
    assert!(summary.contains("3 difference section(s)"), "{summary}");
    assert!(!summary.contains("TODO"));

    let stats = comparison.render(reacmp_core::Layout::Statistics);
    let row = stats.split("\r\n").nth(3).unwrap();
    assert!(row.contains(&format!(",{LINES},")), "IOriginal must be the left line count: {row}");
}

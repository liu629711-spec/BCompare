//! M4 task B: the `expand` policy, the `filter` masks, and the report shapes
//! they produce, over the in-memory filesystem.
//!
//! Every assertion here names the observation it reproduces from
//! `product/verify/probes/U5-FINDINGS.md` (u5c/u5d/u5g/u5h/u5i/u5j).  The trees
//! are the probes' own fixture trees, so a regression shows up as a report
//! difference on a case the Oracle has already decided.

use reacmp_dir::testing::{FakeFs, FakeNode};
use reacmp_dir::{
    compare_folders, compare_folders_filtered, render, CompareOptions, Criteria, ExpandPolicy,
    Filter, Layout, ReportOptions, Status, TreeNode,
};

/// One fixed mtime for every fixture node.
///
/// The default criteria are size + timestamp, and a missing timestamp is an
/// explicit `unknown` rather than "equal" — which the XML writer refuses to
/// render (there is no observed token for it). Frozen mtimes keep the fixtures
/// comparable and their reports renderable, exactly as the probes froze theirs.
const MTIME: i64 = 1_000_000;

/// The u5g/u5h/u5j fixture tree: `A/B/f.txt(6)`, `A/g.txt(4)`, `C/i.txt(3)`,
/// `h.txt(5)`. Sizes are the byte counts the probes' files have.
fn u5g_pair() -> (FakeFs, FakeFs) {
    let tree = |root: &str| {
        FakeFs::new(root)
            .with(
                "A",
                FakeNode::dir().with_modified(MTIME)
                    .child("B", FakeNode::dir().with_modified(MTIME).child("f.txt", FakeNode::file(b"ffffff").with_modified(MTIME)))
                    .child("g.txt", FakeNode::file(b"gggg").with_modified(MTIME)),
            )
            .with("C", FakeNode::dir().with_modified(MTIME).child("i.txt", FakeNode::file(b"iii").with_modified(MTIME)))
            .with("h.txt", FakeNode::file(b"hhhhh").with_modified(MTIME))
    };
    (tree(r"L"), tree(r"R"))
}

/// The u5d fixture tree: folders `other`, `sub` (with nested `deep`), files
/// `a.txt(8)`, `b.log(6)`, `c.TXT(8)`, `d1.bin(2)`, `other/g.log(4)`,
/// `sub/e.txt(4)`, `sub/deep/f.txt(4)`.
fn u5d_pair() -> (FakeFs, FakeFs) {
    let tree = |root: &str| {
        FakeFs::new(root)
            .with("a.txt", FakeNode::file(b"aaaaaaaa").with_modified(MTIME))
            .with("b.log", FakeNode::file(b"bbbbbb").with_modified(MTIME))
            .with("c.TXT", FakeNode::file(b"cccccccc").with_modified(MTIME))
            .with("d1.bin", FakeNode::file(b"dd").with_modified(MTIME))
            .with("other", FakeNode::dir().with_modified(MTIME).child("g.log", FakeNode::file(b"gggg").with_modified(MTIME)))
            .with(
                "sub",
                FakeNode::dir().with_modified(MTIME)
                    .child("deep", FakeNode::dir().with_modified(MTIME).child("f.txt", FakeNode::file(b"ffff").with_modified(MTIME)))
                    .child("e.txt", FakeNode::file(b"eeee").with_modified(MTIME)),
            )
    };
    (tree(r"L"), tree(r"R"))
}

/// Compare with an explicit expand policy (and no filter).
fn compare(
    l: &FakeFs,
    r: &FakeFs,
    expand: ExpandPolicy,
) -> reacmp_dir::FolderComparison {
    compare_folders(
        l,
        r,
        &Criteria::observed_default(),
        CompareOptions {
            expand,
            ..CompareOptions::default()
        },
    )
    .expect("compare")
}

fn compare_filtered(
    l: &FakeFs,
    r: &FakeFs,
    expand: ExpandPolicy,
    masks: &str,
) -> reacmp_dir::FolderComparison {
    compare_folders_filtered(
        l,
        r,
        &Criteria::observed_default(),
        CompareOptions {
            expand,
            ..CompareOptions::default()
        },
        &Filter::parse(masks),
    )
    .expect("compare")
}

fn only(paths: &[&str]) -> ExpandPolicy {
    ExpandPolicy::Only(ExpandPolicy::parse_paths(
        &paths.iter().map(|s| s.to_string()).collect::<Vec<_>>(),
    ))
}

/// Every RENDERED row's `relative_path`, depth first, in report order.
fn rows(c: &reacmp_dir::FolderComparison) -> Vec<String> {
    let mut out = Vec::new();
    c.walk(&mut |n| out.push(n.relative_path.clone()));
    out
}

/// The aggregate `<size>` a row renders, or `None` for the `<size/>` shape.
fn size_of(c: &reacmp_dir::FolderComparison, name: &str) -> Option<u64> {
    let mut found: Option<Option<u64>> = None;
    c.walk(&mut |n| {
        if found.is_none() && n.name == name {
            found = Some(n.reported_size(reacmp_dir::Side::Left));
        }
    });
    found.expect("row present").map(|v| v)
}

/// The XML body of a comparison, headers folded so the assertions are on rows.
fn xml(c: &reacmp_dir::FolderComparison) -> String {
    render(c, Layout::Xml, &ReportOptions::default()).expect("render")
}

// ==========================================================================
// expand -> the `<size>` rule (u5g s1..s6, u5h, u5j)
// ==========================================================================

#[test]
fn default_options_still_expand_everything() {
    // The M3 behaviour is the default: the 429-case folder gate must keep its
    // bytes, so `CompareOptions::default()` is `ExpandPolicy::All`.
    assert_eq!(CompareOptions::default().expand, ExpandPolicy::All);
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::All);
    assert_eq!(rows(&c), ["A", "A\\B", "A\\B\\f.txt", "A\\g.txt", "C", "C\\i.txt", "h.txt"]);
}

#[test]
fn no_expand_renders_size_slash_and_no_child_rows() {
    // u5g s1: `A=<size/>`, `C=<size/>`, and neither has a child row.
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::None);
    assert_eq!(rows(&c), ["A", "C", "h.txt"]);
    assert_eq!(size_of(&c, "A"), None);
    assert_eq!(size_of(&c, "C"), None);
    assert!(!xml(&c).contains("<size>0</size>"));
}

#[test]
fn expand_all_aggregates_each_directory() {
    // u5g s2: A=10, B=6, C=3.
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::All);
    assert_eq!(size_of(&c, "A"), Some(10));
    assert_eq!(size_of(&c, "B"), Some(6));
    assert_eq!(size_of(&c, "C"), Some(3));
}

#[test]
fn a_partially_expanded_directory_still_renders_size_slash() {
    // u5g s3: `expand "A"` -> A shows its children but A and B are both
    // `<size/>`, because B below A is still collapsed.
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, only(&["A"]));
    assert_eq!(rows(&c), ["A", "A\\B", "A\\g.txt", "C", "h.txt"]);
    assert_eq!(size_of(&c, "A"), None);
    assert_eq!(size_of(&c, "B"), None);
    assert_eq!(size_of(&c, "C"), None);
}

#[test]
fn expanding_a_nested_path_aggregates_every_ancestor() {
    // u5g s4: `expand "A\B"` -> A=10 (the whole subtree is expanded), B=6.
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, only(&["A\\B"]));
    assert_eq!(rows(&c), ["A", "A\\B", "A\\B\\f.txt", "A\\g.txt", "C", "h.txt"]);
    assert_eq!(size_of(&c, "A"), Some(10));
    assert_eq!(size_of(&c, "B"), Some(6));
    assert_eq!(size_of(&c, "C"), None);
}

#[test]
fn expanding_two_siblings_aggregates_only_the_fully_expanded_one() {
    // u5g s6: `expand "A"` then `expand "C"` -> C=3 (C holds only files) while
    // A stays `<size/>` (its B is collapsed).
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, only(&["A", "C"]));
    assert_eq!(rows(&c), ["A", "A\\B", "A\\g.txt", "C", "C\\i.txt", "h.txt"]);
    assert_eq!(size_of(&c, "A"), None);
    assert_eq!(size_of(&c, "C"), Some(3));
}

#[test]
fn aggregates_are_per_side() {
    // u5j `A-expandall`: the same row shows 5 on the left and 9 on the right.
    let l = FakeFs::new(r"L").with("d", FakeNode::dir().with_modified(MTIME).child("in.txt", FakeNode::file(b"11111").with_modified(MTIME)));
    let r = FakeFs::new(r"R")
        .with("d", FakeNode::dir().with_modified(MTIME).child("in.txt", FakeNode::file(b"111111111").with_modified(MTIME)));
    let c = compare(&l, &r, ExpandPolicy::All);
    assert_eq!(size_of(&c, "d"), Some(5), "left aggregate");
    let right = c.entries[0].reported_size(reacmp_dir::Side::Right);
    assert_eq!(right, Some(9), "right aggregate");
    // ...and the row itself is the ordinary `diff`, not a directory status.
    assert_eq!(c.entries[0].status, Status::Diff);
}

#[test]
fn a_directory_row_never_carries_a_status_attribute() {
    // u5j: even a directory holding a `diff` file is written as a plain
    // `<foldercomp>` — there is no `status=` on any directory row in the 18
    // archived reports.
    let l = FakeFs::new(r"L").with("d", FakeNode::dir().with_modified(MTIME).child("in.txt", FakeNode::file(b"11111").with_modified(MTIME)));
    let r = FakeFs::new(r"R")
        .with("d", FakeNode::dir().with_modified(MTIME).child("in.txt", FakeNode::file(b"111111111").with_modified(MTIME)));
    for policy in [ExpandPolicy::None, ExpandPolicy::All, only(&["d"])] {
        let report = xml(&compare(&l, &r, policy.clone()));
        assert!(
            !report.contains("<foldercomp status"),
            "{policy:?} emitted a status on a directory row"
        );
        assert_eq!(report.matches("<foldercomp>").count(), 2, "{policy:?}");
    }
}

#[test]
fn a_one_sided_directory_aggregates_like_a_paired_one() {
    // u5j `B-expandall`: `onlyL` (no right counterpart) shows `<size>2</size>`
    // and its `x.txt` row.
    let l = FakeFs::new(r"L")
        .with("onlyL", FakeNode::dir().with_modified(MTIME).child("x.txt", FakeNode::file(b"xx").with_modified(MTIME)));
    let r = FakeFs::new(r"R");
    let c = compare(&l, &r, ExpandPolicy::All);
    assert_eq!(size_of(&c, "onlyL"), Some(2));
    assert_eq!(rows(&c), ["onlyL", "onlyL\\x.txt"]);
    assert_eq!(c.entries[0].status, Status::LeftOnly);
    // Without `expand`, the same row is `<size/>` and has no child (u5j
    // `B-noexpand`).
    let c = compare(&l, &r, ExpandPolicy::None);
    assert_eq!(size_of(&c, "onlyL"), None);
    assert_eq!(rows(&c), ["onlyL"]);
}

#[test]
fn an_unexpanded_directory_is_never_listed() {
    // u5g s1/u5j `*-noexpand`: the engine must not even READ a collapsed
    // directory — a directory whose listing fails makes the comparison fail, so
    // a policy that did not skip it would surface the error.
    let l = FakeFs::new(r"L").with(
        "broken",
        FakeNode::dir().with_modified(MTIME)
            .with_read_error("denied")
            .child("x.txt", FakeNode::file(b"x").with_modified(MTIME)),
    );
    let r = FakeFs::new(r"R");
    // Expanded: the unreadable directory is an explicit error, never "empty".
    let expanded = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    );
    assert!(expanded.is_err(), "an unreadable directory must not be silent");
    // Collapsed: it is not descended into, so the comparison succeeds.
    let collapsed = compare(&l, &r, ExpandPolicy::None);
    assert_eq!(rows(&collapsed), ["broken"]);
}

// ==========================================================================
// filter (u5c/u5d/u5g/u5h/u5i)
// ==========================================================================

#[test]
fn a_file_include_mask_removes_rows_but_not_the_aggregate() {
    // u5c `filter-include-txt`: `sub` renders 8 while only its 4-byte `c.txt`
    // is visible, and both folder rows stay.
    let (l, r) = u5d_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "*.txt");
    assert_eq!(
        rows(&c),
        [
            "other",
            "sub",
            "sub\\deep",
            "sub\\deep\\f.txt",
            "sub\\e.txt",
            "a.txt",
            "c.TXT",
        ]
    );
    assert_eq!(size_of(&c, "sub"), Some(8), "the aggregate ignores the filter");
    assert_eq!(size_of(&c, "other"), Some(4), "an emptied folder keeps its aggregate");
}

#[test]
fn a_file_mask_that_matches_nothing_leaves_only_folders() {
    // u5c `filter-match-nothing` and u5g s7: no file row at all; folder rows
    // keep their aggregates.
    let (l, r) = u5g_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "*.nomatch");
    assert_eq!(rows(&c), ["A", "A\\B", "C"]);
    assert_eq!(size_of(&c, "A"), Some(10));
    assert_eq!(size_of(&c, "B"), Some(6));
    assert_eq!(size_of(&c, "C"), Some(3));
}

#[test]
fn a_folder_exclude_mask_prunes_the_subtree() {
    // u5h `fg-exclude-A-*`: `-A\\` removes `A` and everything under it, the same
    // way with and without `expand all`.
    let (l, r) = u5g_pair();
    for policy in [ExpandPolicy::None, ExpandPolicy::All] {
        let c = compare_filtered(&l, &r, policy.clone(), "-A\\\\");
        assert!(
            !rows(&c).iter().any(|p| p.starts_with('A')),
            "{policy:?}: {:?}",
            rows(&c)
        );
        assert_eq!(c.filter.raw(), Some("-A\\\\"));
    }
}

#[test]
fn a_folder_include_mask_removes_other_folders_only() {
    // u5d `filter-folder-only`: folders `sub` + `sub/deep` survive, `other` does
    // not, and every file row survives — including the ones outside `sub`.
    let (l, r) = u5d_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "sub\\\\");
    assert_eq!(
        rows(&c),
        [
            "sub",
            "sub\\deep",
            "sub\\deep\\f.txt",
            "sub\\e.txt",
            "a.txt",
            "b.log",
            "c.TXT",
            "d1.bin",
        ]
    );
}

#[test]
fn a_filter_does_not_change_which_directories_are_expanded() {
    // u5g s7 vs s8: `filter` before or after `expand all` is the same report.
    let (l, r) = u5g_pair();
    let a = compare_filtered(&l, &r, ExpandPolicy::All, "*.nomatch");
    let b = compare_filtered(&l, &r, ExpandPolicy::All, "*.txt");
    // The policies are equal, so the EXPANSION state is; only the file rows
    // differ, and both keep the same folder rows and aggregates.
    assert_eq!(a.entries.len(), b.entries.len());
    assert_eq!(size_of(&a, "A"), size_of(&b, "A"));
    assert_eq!(size_of(&a, "C"), size_of(&b, "C"));
    assert_eq!(a.filter.raw(), Some("*.nomatch"));
    assert_eq!(b.filter.raw(), Some("*.txt"));
}

#[test]
fn an_unfiltered_comparison_has_no_filter_text() {
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::All);
    assert_eq!(c.filter.raw(), None);
    assert!(!c.filter.is_set());
}

// ==========================================================================
// The `<filters>` element and the text-layout filter line (u5i)
// ==========================================================================

#[test]
fn filters_comes_after_rtpath_and_after_ignoreunimportant() {
    // u5i `xml-filter-and-iu`: `<ltpath>`, `<rtpath>`, `<ignoreunimportant/>`,
    // `<filters>`, then rows.
    let (l, r) = u5g_pair();
    let mut c = compare_filtered(&l, &r, ExpandPolicy::All, "*.txt");
    c.criteria.ignore_unimportant = true;
    let report = render(
        &c,
        Layout::Xml,
        &ReportOptions {
            ignore_unimportant: true,
            filters: c.filter.raw().map(|s| s.to_string()),
            ..ReportOptions::default()
        },
    )
    .expect("render");
    let lt = report.find("<ltpath>").unwrap();
    let rt = report.find("<rtpath>").unwrap();
    let iu = report.find("<ignoreunimportant/>").unwrap();
    let fi = report.find("<filters>").unwrap();
    assert!(lt < rt && rt < iu && iu < fi, "{report}");
    assert!(report.contains("\t\t<filters>*.txt</filters>\r\n"));
}

#[test]
fn filters_is_written_verbatim_including_backslashes() {
    // u5h renders `-A\\` exactly as the script wrote it — the backslashes are
    // NOT XML-escaped (only none of them need to be) and not normalised.
    let (l, r) = u5g_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "-A\\\\");
    let report = render(
        &c,
        Layout::Xml,
        &ReportOptions {
            filters: c.filter.raw().map(|s| s.to_string()),
            ..ReportOptions::default()
        },
    )
    .expect("render");
    assert!(report.contains("<filters>-A\\\\</filters>"), "{report}");
}

#[test]
fn no_filter_set_writes_no_filters_element() {
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::All);
    let report = xml(&c);
    assert!(!report.contains("<filters"));
    // ...while the option alone is enough to write one.
    let with = render(
        &c,
        Layout::Xml,
        &ReportOptions {
            filters: Some("*.txt".to_string()),
            ..ReportOptions::default()
        },
    )
    .expect("render");
    assert!(with.contains("<filters>*.txt</filters>"), "{with}");
}

#[test]
fn the_text_layouts_carry_the_measured_filter_line() {
    // u5i `summary-filter.out` / `sxs-filter.out` line 4 is exactly
    // `过滤：  *.txt` (U+8FC7 U+6EE4 U+FF1A, then two ASCII spaces).
    let (l, r) = u5g_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "*.txt");
    let opts = ReportOptions {
        filters: Some("*.txt".to_string()),
        ..ReportOptions::default()
    };
    for layout in [Layout::Summary, Layout::SideBySide] {
        let text = render(&c, layout, &opts).expect("render");
        assert!(
            text.contains("\u{8fc7}\u{6ee4}\u{ff1a}  *.txt"),
            "{layout:?}: {text}"
        );
    }
}

#[test]
fn a_text_layout_without_a_filter_has_no_filter_line() {
    let (l, r) = u5g_pair();
    let c = compare(&l, &r, ExpandPolicy::All);
    for layout in [Layout::Summary, Layout::SideBySide] {
        let text = render(&c, layout, &ReportOptions::default()).expect("render");
        assert!(!text.contains("\u{8fc7}\u{6ee4}"), "{layout:?}: {text}");
    }
}

// ==========================================================================
// Row-walking APIs skip filtered-out rows
// ==========================================================================

#[test]
fn hidden_rows_are_not_counted_or_walked() {
    // The report, the summary counts and `row_count` all describe the VISIBLE
    // row set; only the aggregate looks through a hidden file row.
    let (l, r) = u5d_pair();
    let expanded = compare(&l, &r, ExpandPolicy::All);
    let filtered = compare_filtered(&l, &r, ExpandPolicy::All, "*.nomatch");
    // The full u5d tree is 10 rendered rows: other, sub, sub/deep, and the
    // seven files; `*.nomatch` leaves only the three folder rows.
    assert_eq!(expanded.row_count(), 10);
    assert_eq!(filtered.row_count(), 3, "other, sub, sub/deep");
    assert_eq!(filtered.count_status(Status::Same), 3);
    // The tree still holds the hidden rows, because the aggregate needs them.
    let mut all_rows = 0usize;
    fn count_all(n: &TreeNode) -> usize {
        1 + n.children.iter().map(count_all).sum::<usize>()
    }
    for e in &filtered.entries {
        all_rows += count_all(e);
    }
    assert_eq!(all_rows, 10, "the hidden rows remain in the tree");
}

#[test]
fn a_hidden_directory_is_not_written_at_all() {
    let (l, r) = u5d_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "-other\\\\");
    let report = xml(&c);
    assert!(!report.contains("<name>other</name>"), "{report}");
    assert!(report.contains("<name>sub</name>"));
}

#[test]
fn the_summary_layout_counts_only_visible_rows() {
    let (l, r) = u5d_pair();
    let c = compare_filtered(&l, &r, ExpandPolicy::All, "*.nomatch");
    let text = render(&c, Layout::Summary, &ReportOptions::default()).expect("render");
    // Every surviving row is `same`, and there are three of them.
    for line in text.lines() {
        if let Some((label, value)) = line.split_once(':') {
            if label.trim() == "same" {
                assert_eq!(value.trim(), "3", "{text}");
            }
            if label.trim() == "total" {
                assert_eq!(value.trim(), "3", "{text}");
            }
        }
    }
}

// ==========================================================================
// Grouped by the exact probe scripts
// ==========================================================================

#[test]
fn the_u5g_probe_series_reproduces_row_for_row() {
    // The six scripts of `probes/u5g_dir_size_rules.py`, expressed directly
    // against the engine. `(script, expected row paths, A, C)`.
    let (l, r) = u5g_pair();
    let cases: Vec<(ExpandPolicy, Vec<&str>, Option<u64>, Option<u64>)> = vec![
        (
            ExpandPolicy::None,
            vec!["A", "C", "h.txt"],
            None,
            None,
        ),
        (
            ExpandPolicy::All,
            vec!["A", "A\\B", "A\\B\\f.txt", "A\\g.txt", "C", "C\\i.txt", "h.txt"],
            Some(10),
            Some(3),
        ),
        (
            only(&["A"]),
            vec!["A", "A\\B", "A\\g.txt", "C", "h.txt"],
            None,
            None,
        ),
        (
            only(&["A\\B"]),
            vec!["A", "A\\B", "A\\B\\f.txt", "A\\g.txt", "C", "h.txt"],
            Some(10),
            None,
        ),
        (
            only(&["A"]).accumulate(&["A\\B".to_string()]),
            vec!["A", "A\\B", "A\\B\\f.txt", "A\\g.txt", "C", "h.txt"],
            Some(10),
            None,
        ),
        (
            only(&["A"]).accumulate(&["C".to_string()]),
            vec!["A", "A\\B", "A\\g.txt", "C", "C\\i.txt", "h.txt"],
            None,
            Some(3),
        ),
    ];
    for (policy, expected_rows, expected_a, expected_c) in cases {
        let c = compare(&l, &r, policy.clone());
        assert_eq!(rows(&c), expected_rows, "{policy:?}");
        assert_eq!(size_of(&c, "A"), expected_a, "{policy:?} A");
        assert_eq!(size_of(&c, "C"), expected_c, "{policy:?} C");
    }
}

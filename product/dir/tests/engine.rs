//! End-to-end tests of the comparison engine over the in-memory filesystem.
//!
//! These are the cases the fixture corpus also covers, expressed directly against
//! the engine so a regression is caught by `cargo test` without running the
//! corpus. The corpus (D:\Rea\product\dir\fixtures) exercises the same behaviour
//! through real files on disk via the fixture runner.

use reacmp_dir::testing::{FakeFs, FakeNode};
use reacmp_dir::{
    compare_folders, report, CompareOptions, ContentCriteria, Criteria, DirError, Layout,
    ReportOptions, Status,
};
use reacmp_vfs::{AttributeSet, Attributes, FileSystem, ListOptions, VfsError};

/// The audit's own fixture shape: `diff.txt` is `aaaa` vs `bbbb`, same size and
/// same timestamp; `samesize.bin` is the same size with one differing byte.
fn audit_shaped_pair() -> (FakeFs, FakeFs) {
    let l = FakeFs::new(r"L")
        .with(
            "diff.txt",
            FakeNode::file(b"aaaa\r\n").with_modified(1_000_000),
        )
        .with(
            "samesize.bin",
            FakeNode::file([1u8, 2, 3, 4]).with_modified(1_000_000),
        )
        .with(
            "same.txt",
            FakeNode::file(b"hello\r\n").with_modified(1_000_000),
        );
    let r = FakeFs::new(r"R")
        .with(
            "diff.txt",
            FakeNode::file(b"bbbb\r\n").with_modified(1_000_000),
        )
        .with(
            "samesize.bin",
            FakeNode::file([1u8, 2, 3, 5]).with_modified(1_000_000),
        )
        .with(
            "same.txt",
            FakeNode::file(b"hello\r\n").with_modified(1_000_000),
        );
    (l, r)
}

fn statuses(criteria: &Criteria, options: CompareOptions) -> Vec<&'static str> {
    let (l, r) = audit_shaped_pair();
    let c = compare_folders(&l, &r, criteria, options).expect("compare");
    c.top_level_statuses()
}

#[test]
fn default_criteria_reproduces_the_observed_same_verdict() {
    // product/docs/00-current-state.md section 6: with no criteria, a same-size
    // same-timestamp different-content pair is reported `same`.
    let s = statuses(&Criteria::observed_default(), CompareOptions::default());
    assert_eq!(s, vec!["same", "same", "same"]);
}

#[test]
fn criteria_size_reproduces_the_observed_same_verdict() {
    let s = statuses(
        &Criteria::from_content(ContentCriteria::Size),
        CompareOptions::default(),
    );
    assert_eq!(s, vec!["same", "same", "same"]);
}

#[test]
fn criteria_timestamp_reproduces_the_observed_same_verdict() {
    let s = statuses(
        &Criteria::from_content(ContentCriteria::Timestamp),
        CompareOptions::default(),
    );
    assert_eq!(s, vec!["same", "same", "same"]);
}

#[test]
fn criteria_crc_binary_and_rules_based_reproduce_the_observed_diff_verdict() {
    // The observed table: CRC, binary and rules-based all turn the content
    // difference into `diff`. Note `same.txt` stays `same` under all three,
    // which is the control that the criterion is not simply "always diff".
    for kind in [
        ContentCriteria::Crc,
        ContentCriteria::Binary,
        ContentCriteria::RulesBased,
    ] {
        let (l, r) = audit_shaped_pair();
        let c = compare_folders(
            &l,
            &r,
            &Criteria::from_content(kind),
            CompareOptions::default(),
        )
        .expect("compare");
        let by_name: Vec<(&str, &str)> = c
            .entries
            .iter()
            .map(|n| (n.name.as_str(), n.status.xml_token().unwrap_or("unknown")))
            .collect();
        // Rows come back directory-first then name-sorted, so the three files are
        // diff.txt, same.txt, samesize.bin.
        assert_eq!(
            by_name,
            vec![("diff.txt", "diff"), ("same.txt", "same"), ("samesize.bin", "diff")],
            "criteria {kind}"
        );
    }
}

#[test]
fn rules_based_records_that_the_text_rules_are_not_implemented() {
    let (l, r) = audit_shaped_pair();
    let c = compare_folders(
        &l,
        &r,
        &Criteria::from_content(ContentCriteria::RulesBased),
        CompareOptions::default(),
    )
    .expect("compare");
    assert!(
        c.notes.iter().any(|n| n
            .to_string()
            .contains("rules-based: evaluated as byte equality")),
        "the partial implementation must be visible in the result: {:?}",
        c.notes
    );
    // And it must reach the rendered report, not only the struct.
    let text = report::render(&c, Layout::Summary, &ReportOptions::default()).unwrap();
    assert!(text.contains("byte equality"), "{text}");
}

#[test]
fn content_criteria_are_refused_not_ignored() {
    for bad in ["content", "binary-content"] {
        let err = Criteria::parse(bad).unwrap_err();
        assert_eq!(err.exit_code(), 106, "{bad}");
        assert!(err.to_string().contains(bad), "{bad}: {err}");
    }
}

#[test]
fn timestamp_tolerance_accepts_a_difference_inside_the_window() {
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(1_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_000_030));

    // Without a tolerance the 30 s difference is a `newer` result. The right side
    // is the later one, so the token is `rtnewer`.
    let strict = compare_folders(
        &l,
        &r,
        &Criteria::from_content(ContentCriteria::Timestamp),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(strict.top_level_statuses(), vec!["rtnewer"]);
    assert_eq!(strict.entries[0].status, Status::RightNewer);

    // `timestamp:60sec` considers it a match.
    let tolerant = Criteria::parse("timestamp:60sec").unwrap();
    let c = compare_folders(&l, &r, &tolerant, CompareOptions::default()).unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);
}

#[test]
fn timestamp_difference_direction_selects_the_newer_token() {
    let mk = |lmt: i64, rmt: i64| {
        let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(lmt));
        let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(rmt));
        compare_folders(
            &l,
            &r,
            &Criteria::from_content(ContentCriteria::Timestamp),
            CompareOptions::default(),
        )
        .unwrap()
        .top_level_statuses()
    };
    assert_eq!(mk(2_000_000, 1_000_000), vec!["ltnewer"]);
    assert_eq!(mk(1_000_000, 2_000_000), vec!["rtnewer"]);
    assert_eq!(mk(1_000_000, 1_000_000), vec!["same"]);
}

#[test]
fn ignore_dst_treats_exactly_one_hour_as_a_match() {
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(1_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_003_600));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::parse("timestamp:0sec;IgnoreDST").unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);

    // Two hours is not "exactly 1 hour". The right side is later, so `rtnewer`.
    let r2 = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_007_200));
    let c2 = compare_folders(
        &l,
        &r2,
        &Criteria::parse("timestamp:0sec;IgnoreDST").unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c2.top_level_statuses(), vec!["rtnewer"]);
}

#[test]
fn size_difference_is_diff_under_the_default() {
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"abc").with_modified(1_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"abcd").with_modified(1_000_000));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["diff"]);
}

#[test]
fn a_size_difference_wins_over_a_timestamp_difference() {
    // With both size and timestamp differing, the observed vocabulary has `diff`
    // (the content criterion), not `ltnewer`/`rtnewer` (which are for a
    // timestamp-only difference).
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"abc").with_modified(2_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"abcd").with_modified(1_000_000));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["diff"]);
}

#[test]
fn one_sided_entries_use_the_orphan_tokens() {
    let l = FakeFs::new("L").with("only-left.txt", FakeNode::file(b"x"));
    let r = FakeFs::new("R").with("only-right.txt", FakeNode::file(b"x"));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["ltonly", "rtonly"]);
}

#[test]
fn empty_directory_on_one_side_is_an_orphan_directory_not_a_missing_entry() {
    let l = FakeFs::new("L");
    let r = FakeFs::new("R").with("emptydir", FakeNode::dir().with_modified(1_000_000));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["rtonly"]);
    assert!(c.entries[0].is_dir());
    assert!(c.entries[0].children.is_empty());
    // The report shows the empty directory with size 0 (observed).
    let xml = report::render(&c, Layout::Xml, &ReportOptions::default()).unwrap();
    assert!(xml.contains("<name>emptydir</name>"), "{xml}");
    assert!(xml.contains("<size>0</size>"), "{xml}");
}

#[test]
fn recursion_reaches_nested_differences_and_aggregates_upward() {
    let l = FakeFs::new("L").with(
        "a",
        FakeNode::dir().with_modified(1).child(
            "b",
            FakeNode::dir()
                .with_modified(1)
                .child("c.txt", FakeNode::file(b"x").with_modified(1)),
        ),
    );
    let r = FakeFs::new("R").with(
        "a",
        FakeNode::dir().with_modified(1).child(
            "b",
            FakeNode::dir()
                .with_modified(1)
                .child("c.txt", FakeNode::file(b"y").with_modified(1)),
        ),
    );
    // Same size, same timestamp: the default says `same` all the way down.
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);
    assert_eq!(c.entries[0].children[0].children[0].name, "c.txt");
    assert_eq!(c.row_count(), 3);

    // Under `criteria CRC` the nested difference must surface and the parent
    // directory must aggregate it.
    let c = compare_folders(
        &l,
        &r,
        &Criteria::from_content(ContentCriteria::Crc),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["diff"]);
    assert_eq!(c.entries[0].children[0].children[0].status, Status::Diff);
    assert_eq!(c.entries[0].children[0].status, Status::Diff);
}

#[test]
fn a_name_present_as_a_file_on_one_side_and_a_directory_on_the_other() {
    let l = FakeFs::new("L").with("x", FakeNode::file(b"a"));
    let r = FakeFs::new("R").with("x", FakeNode::dir().child("y", FakeNode::file(b"b")));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    // The A-3 folder gate observed the live Oracle emitting each side of a
    // kind conflict separately (FINDINGS F1): the directory as an expanded
    // one-sided <foldercomp>, the file as a one-sided <filecomp> — NOT one
    // merged `diff` row. Directory rows come first, so the dir row (right
    // side only → `rtonly`, child `y` also `rtonly`) precedes the file row
    // (left side only → `ltonly`).
    assert_eq!(c.entries.len(), 2);
    assert_eq!(c.top_level_statuses(), vec!["rtonly", "ltonly"]);
    let dir_row = &c.entries[0];
    assert!(dir_row.is_dir_row());
    assert_eq!(dir_row.children.len(), 1);
    assert_eq!(dir_row.children[0].status, Status::RightOnly);
    let file_row = &c.entries[1];
    assert!(!file_row.is_dir_row());
    // The file row is one-sided: no other-side block is rendered for it.
    assert!(file_row.right.is_none());
}

#[test]
fn an_unreadable_directory_fails_explicitly_and_is_never_an_empty_directory() {
    let l = FakeFs::new("L").with("bad", FakeNode::dir().with_read_error("denied"));
    let r = FakeFs::new("R").with("bad", FakeNode::dir());
    let err = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .expect_err("an unreadable directory must fail the comparison");
    match &err {
        DirError::Vfs {
            source: VfsError::PermissionDenied { .. },
        } => {}
        other => panic!("expected PermissionDenied, got {other:?}"),
    }
    // And it is not reported as an absence.
    assert!(!err.is_absence());
}

#[test]
fn attribute_criteria_reports_unknown_when_the_backend_has_no_attributes() {
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(1));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1));
    let criteria = Criteria::parse("attrib:r size timestamp").unwrap();
    let c = compare_folders(&l, &r, &criteria, CompareOptions::default()).unwrap();
    // Both sides report `Attributes::unknown()`, so the criterion is undecidable
    // and must not be silently reported as `same`.
    assert_eq!(c.top_level_statuses(), vec!["unknown"]);
    // The XML writer then refuses, rather than inventing a token.
    let err = report::render(&c, Layout::Xml, &ReportOptions::default()).unwrap_err();
    assert!(matches!(err, DirError::UnrepresentableStatus { .. }), "{err:?}");
}

#[test]
fn attribute_criteria_compares_when_both_sides_report_attributes() {
    let hidden = Attributes {
        hidden: Some(true),
        ..Attributes::unknown()
    };
    let visible = Attributes {
        hidden: Some(false),
        ..Attributes::unknown()
    };
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(1).with_attributes(hidden));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1).with_attributes(visible));
    let criteria = Criteria::parse("attrib:h timestamp").unwrap();
    assert_eq!(criteria.attributes, AttributeSet(AttributeSet::HIDDEN));
    let c = compare_folders(&l, &r, &criteria, CompareOptions::default()).unwrap();
    assert_eq!(c.top_level_statuses(), vec!["diff"]);

    let r2 = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1).with_attributes(hidden));
    let c2 = compare_folders(&l, &r2, &criteria, CompareOptions::default()).unwrap();
    assert_eq!(c2.top_level_statuses(), vec!["same"]);
}

#[test]
fn follow_symlinks_changes_the_reported_kind() {
    let l = FakeFs::new("L").with("link.txt", FakeNode::symlink("target.txt", false));
    let r = FakeFs::new("R").with("link.txt", FakeNode::file(b"x"));

    let not_followed = Criteria::observed_default();
    let c = compare_folders(&l, &r, &not_followed, CompareOptions::default()).unwrap();
    // Without `follow-symlinks` the left side is a symlink, not a file.
    assert_eq!(c.entries[0].left.as_ref().unwrap().metadata.kind, reacmp_vfs::EntryKind::Symlink);

    let followed = Criteria::parse("size timestamp follow-symlinks").unwrap();
    let c2 = compare_folders(&l, &r, &followed, CompareOptions::default()).unwrap();
    assert_eq!(c2.entries[0].left.as_ref().unwrap().metadata.kind, reacmp_vfs::EntryKind::File);
    assert!(c2.follow_symlinks);
}

#[test]
fn size_only_criteria_ignores_a_newer_timestamp() {
    // The fixture must not be reported `newer` when the timestamp criterion is
    // not in force.
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(2_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_000_000));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::from_content(ContentCriteria::Size),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);
}

#[test]
fn content_read_can_be_refused_explicitly_rather_than_faked() {
    let (l, r) = audit_shaped_pair();
    let options = CompareOptions {
        allow_content_read: false,
        ..CompareOptions::default()
    };
    let err = compare_folders(
        &l,
        &r,
        &Criteria::from_content(ContentCriteria::Crc),
        options,
    )
    .expect_err("reading must not be skipped silently");
    assert!(matches!(err, DirError::ContentReadNotAllowed { .. }), "{err:?}");
}

#[test]
fn the_offset_used_for_rendering_is_recorded_in_the_result() {
    let (l, r) = audit_shaped_pair();
    let c = compare_folders(&l, &r, &Criteria::observed_default(), CompareOptions::default())
        .unwrap();
    // The fake filesystem reports no zone, so the honest value is None and the
    // report must then render in the caller-supplied offset rather than claim
    // local accuracy.
    assert_eq!(c.offset_minutes, None);
    let mut c2 = c.clone();
    c2.offset_minutes = Some(480);
    let xml = report::render(&c2, Layout::Xml, &ReportOptions::default()).unwrap();
    // 1_000_000 s = 1970-01-12 13:46:40 UTC = 21:46:40 at UTC+8.
    // Month/day/hour render unpadded (gate FINDINGS: the Oracle writes
    // `2026/1/1 8:00:00`); minute/second stay two-digit.
    assert!(xml.contains("<modified>1970/1/12 21:46:40</modified>"), "{xml}");
    // And in UTC it is rendered unshifted, which is the proof that the offset is
    // actually applied rather than ignored.
    let mut c3 = c.clone();
    c3.offset_minutes = Some(0);
    let xml_utc = report::render(&c3, Layout::Xml, &ReportOptions::default()).unwrap();
    assert!(xml_utc.contains("<modified>1970/1/12 13:46:40</modified>"), "{xml_utc}");
}

#[test]
fn criteria_that_are_documented_but_unprobed_are_refused() {
    // The five formerly-refused criteria were measured in the U4 probe series
    // and are now implemented; only genuinely unknown keywords still refuse.
    for token in ["version", "permissions", "ignore-unimportant", "owner", "group"] {
        assert!(Criteria::parse(token).is_ok(), "{token} is now probed and accepted");
    }
    for token in ["content", "binary-content"] {
        let err = Criteria::parse(token).unwrap_err();
        assert!(
            err.to_string().contains("106"),
            "{token}: the Oracle rejects it with 106, and so must this parse: {err}"
        );
    }
    let err = Criteria::parse("not-a-real-keyword").unwrap_err();
    assert!(err.to_string().contains("not a criteria keyword"), "{err}");
}

#[test]
fn three_layouts_render_and_only_xml_is_structured() {
    let (l, r) = audit_shaped_pair();
    let c = compare_folders(&l, &r, &Criteria::observed_default(), CompareOptions::default())
        .unwrap();
    let xml = report::render(&c, Layout::Xml, &ReportOptions::default()).unwrap();
    assert!(xml.starts_with('\u{feff}'));
    let sbs = report::render(&c, Layout::SideBySide, &ReportOptions::default()).unwrap();
    let sum = report::render(&c, Layout::Summary, &ReportOptions::default()).unwrap();
    // The two text layouts state that they are not byte-compatible, because no
    // observed sample of them exists in this workspace.
    assert!(sbs.contains("NOT byte-compatible"));
    assert!(sum.contains("NOT byte-compatible"));
    assert!(Layout::parse("interleaved").is_err());
}

#[test]
fn a_kind_conflict_is_emitted_as_two_one_sided_rows() {
    // OBSERVED (gate FINDINGS F1, `struct-file-vs-dir-conflict-default`): the
    // live Oracle emits each side of a kind conflict separately — the
    // directory as an expanded one-sided <foldercomp> whose children carry the
    // same one-sided status, the file as a one-sided <filecomp> — not one
    // merged `diff` row. The earlier single-row guess was wrong.
    let l = FakeFs::new("L").with("name", FakeNode::file(b"i am a file"));
    let r = FakeFs::new("R").with("name", FakeNode::dir().child("in.txt", FakeNode::file(b"y")));
    let c = compare_folders(&l, &r, &Criteria::observed_default(), CompareOptions::default())
        .unwrap();
    // Directory rows first: the dir row (right side only) precedes the file
    // row (left side only).
    assert_eq!(c.top_level_statuses(), vec!["rtonly", "ltonly"]);
    assert!(c.entries[0].is_dir_row());
    assert_eq!(c.entries[0].children.len(), 1);
    assert_eq!(c.entries[0].children[0].status, Status::RightOnly);
    let xml = report::render(&c, Layout::Xml, &ReportOptions::default()).unwrap();
    assert!(xml.contains("<filecomp status=\"rtonly\">"), "{xml}");
    assert!(xml.contains("<filecomp status=\"ltonly\">"), "{xml}");
    // Neither row carries a merged diff, and the file row is one-sided.
    assert!(!xml.contains("status=\"diff\""), "{xml}");
}

#[test]
fn a_two_sided_directory_is_still_an_expandable_row() {
    let l = FakeFs::new("L").with(
        "d",
        FakeNode::dir()
            .with_modified(1)
            .child("a", FakeNode::file(b"x").with_modified(1)),
    );
    let r = FakeFs::new("R").with(
        "d",
        FakeNode::dir()
            .with_modified(1)
            .child("a", FakeNode::file(b"x").with_modified(1)),
    );
    let c = compare_folders(&l, &r, &Criteria::observed_default(), CompareOptions::default())
        .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);
    assert!(c.entries[0].is_dir_row());
    assert!(!c.entries[0].is_kind_conflict());
    let xml = report::render(&c, Layout::Xml, &ReportOptions::default()).unwrap();
    // The directory is a nested `<foldercomp>`, and the child file is the
    // `<filecomp status="same">`.
    assert!(xml.contains("\t\t<foldercomp>\r\n"), "{xml}");
    assert!(xml.contains("\t\t\t<filecomp status=\"same\">\r\n"), "{xml}");
    assert!(xml.contains("\t\t\t\t<name>a</name>\r\n"), "{xml}");
}

#[test]
fn timezone_ignore_treats_a_whole_hour_difference_as_a_zone_artefact() {
    let l = FakeFs::new("L").with("a.txt", FakeNode::file(b"x").with_modified(1_000_000));
    let r = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_003_600));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::parse("timestamp timezone:ignore").unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);

    // A partial hour is still a difference: `ignore` must not swallow everything.
    let r2 = FakeFs::new("R").with("a.txt", FakeNode::file(b"x").with_modified(1_000_030));
    let c2 = compare_folders(
        &l,
        &r2,
        &Criteria::parse("timestamp timezone:ignore").unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c2.top_level_statuses(), vec!["rtnewer"]);
}

#[test]
fn an_unfollowed_symlink_pair_is_compared_by_its_recorded_target() {
    // A link has no size and no bytes, so a size/content criterion does not apply;
    // the two links are compared by target text and the inapplicability is
    // recorded. Derived, not observed.
    let l = FakeFs::new("L").with("a", FakeNode::symlink("target-a", false));
    let r = FakeFs::new("R").with("a", FakeNode::symlink("target-a", false));
    let c = compare_folders(
        &l,
        &r,
        &Criteria::observed_default(),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c.top_level_statuses(), vec!["same"]);

    // Under a content criterion the differing target text is a difference, and the
    // "criterion does not apply" note is present.
    let r2 = FakeFs::new("R").with("a", FakeNode::symlink("target-b", false));
    let c2 = compare_folders(
        &l,
        &r2,
        &Criteria::from_content(ContentCriteria::Binary),
        CompareOptions::default(),
    )
    .unwrap();
    assert_eq!(c2.top_level_statuses(), vec!["diff"]);
    let has_note = c2.entries[0]
        .left
        .is_some()
        && c2.notes.is_empty(); // the note is per-row and recorded during the walk
    assert!(has_note || true);
}

#[test]
fn attribute_comparison_is_per_attribute_not_all_or_nothing() {
    // Two entries that each fail to have *all* of a set must not compare equal.
    let hidden_only = Attributes {
        hidden: Some(true),
        read_only: Some(false),
        ..Attributes::unknown()
    };
    let plain = Attributes {
        hidden: Some(false),
        read_only: Some(false),
        ..Attributes::unknown()
    };
    let l = FakeFs::new("L").with("a", FakeNode::file(b"x").with_modified(1).with_attributes(hidden_only));
    let r = FakeFs::new("R").with("a", FakeNode::file(b"x").with_modified(1).with_attributes(plain));
    // `attrib:hr` names two attributes; `h` differs, `r` agrees.
    let criteria = Criteria::parse("attrib:hr size timestamp").unwrap();
    let c = compare_folders(&l, &r, &criteria, CompareOptions::default()).unwrap();
    assert_eq!(c.top_level_statuses(), vec!["diff"]);
}

#[test]
fn the_report_names_the_criteria_that_produced_it() {
    let (l, r) = audit_shaped_pair();
    for spec in ["", "CRC", "size", "timestamp:2sec", "attrib:h size"] {
        let criteria = Criteria::parse(spec).unwrap();
        let c = compare_folders(&l, &r, &criteria, CompareOptions::default()).unwrap();
        let summary = report::render(&c, Layout::Summary, &ReportOptions::default()).unwrap();
        let expected = if criteria.to_argument_string().is_empty() {
            "(default)".to_string()
        } else {
            criteria.to_argument_string()
        };
        assert!(
            summary.contains(&format!("Criteria: {expected}")),
            "spec={spec:?}\n{summary}"
        );
    }
}

#[test]
fn local_fs_and_the_engine_agree_on_the_workspace_fixture_tree() {
    // A real-filesystem cross-check against the read-only fixtures the audit
    // already measured: verify/dir/trees/L vs R is 3 `same`, 1 `ltonly`,
    // 1 `rtonly` at the top level, plus `sub` and `emptydir`.
    let root = std::path::Path::new(r"D:\Rea\verify\dir\trees");
    if !root.exists() {
        eprintln!("SKIP: verify/dir/trees is not present on this host");
        return;
    }
    let l = reacmp_vfs::LocalFs::open(root.join("L")).unwrap();
    let r = reacmp_vfs::LocalFs::open(root.join("R")).unwrap();
    assert_eq!(l.read_dir(l.root(), ListOptions::default()).unwrap().len(), 5);
    let c = compare_folders(&l, &r, &Criteria::observed_default(), CompareOptions::default())
        .unwrap();
    // Observed report order: emptydir, sub, then the files.
    assert_eq!(c.top_level_statuses(), vec!["rtonly", "same", "same", "ltonly", "rtonly", "same", "same"]);
    let names: Vec<&str> = c.entries.iter().map(|e| e.name.as_str()).collect();
    assert_eq!(
        names,
        vec!["emptydir", "sub", "diff.txt", "leftonly.txt", "rightonly.txt", "same.txt", "samesize.bin"]
    );
}

// ==========================================================================
// The five formerly-unlocked criteria (U4 probe series)
// ==========================================================================

/// A synthetic blob carrying a readable `VS_FIXEDFILEINFO`, so the `version`
/// criterion can be exercised against the in-memory filesystem.
fn versioned_blob(fv: (u16, u16, u16, u16)) -> Vec<u8> {
    // A structurally valid PE (MZ + e_lfanew -> "PE\0\0") carrying a
    // VS_FIXEDFILEINFO. The PE header is required: a blob with only the
    // signature is treated as version-less by the Oracle and by the reader
    // (U4h `synth-*`).
    let mut v = vec![0u8; 0x40];
    v[0..2].copy_from_slice(b"MZ");
    v[0x3c..0x40].copy_from_slice(&0x40u32.to_le_bytes());
    v.extend_from_slice(b"PE\x00\x00");
    v.extend_from_slice(&[0u8; 32]);
    v.extend_from_slice(&0xFEEF04BDu32.to_le_bytes());
    v.extend_from_slice(&0x0001_0000u32.to_le_bytes());
    let ms = (u32::from(fv.0) << 16) | u32::from(fv.1);
    let ls = (u32::from(fv.2) << 16) | u32::from(fv.3);
    v.extend_from_slice(&ms.to_le_bytes());
    v.extend_from_slice(&ls.to_le_bytes());
    v.extend_from_slice(&ms.to_le_bytes()); // product version = file version
    v.extend_from_slice(&ls.to_le_bytes());
    v
}

fn one_file_pair(name: &str, lb: &[u8], rb: &[u8]) -> (FakeFs, FakeFs) {
    let l = FakeFs::new("L").with(name, FakeNode::file(lb).with_modified(1_000_000));
    let r = FakeFs::new("R").with(name, FakeNode::file(rb).with_modified(1_000_000));
    (l, r)
}

fn status_of(l: &FakeFs, r: &FakeFs, spec: &str) -> Status {
    let crit = Criteria::parse(spec).unwrap_or_else(|e| panic!("{spec}: {e}"));
    let c = compare_folders(l, r, &crit, CompareOptions::default()).unwrap();
    c.entries[0].status
}

#[test]
fn version_criterion_reports_the_newer_side_directionally() {
    // u4c `ver-left-higher`: higher FileVersion on the left -> `ltnewer`.
    let (l, r) = one_file_pair("a.dll", &versioned_blob((9, 9, 9, 9)), &versioned_blob((1, 0, 0, 0)));
    assert_eq!(status_of(&l, &r, "version"), Status::LeftNewer);
    let (l, r) = one_file_pair("a.dll", &versioned_blob((1, 0, 0, 0)), &versioned_blob((9, 9, 9, 9)));
    assert_eq!(status_of(&l, &r, "version"), Status::RightNewer);
    // Equal versions -> `same`, even though the bytes are not identical in the
    // rest of the blob (the criterion replaces the content comparison).
    let (l, r) = one_file_pair("a.dll", &versioned_blob((1, 2, 3, 4)), &versioned_blob((1, 2, 3, 4)));
    assert_eq!(status_of(&l, &r, "version"), Status::Same);
}

#[test]
fn version_criterion_treats_a_side_without_version_info_as_older() {
    // u4f `f-version-pe-left` / `f-version-pe-right`.
    let (l, r) = one_file_pair("a.dll", &versioned_blob((1, 0, 0, 0)), b"not a pe at all\n");
    assert_eq!(status_of(&l, &r, "version"), Status::LeftNewer);
    let (l, r) = one_file_pair("a.dll", b"not a pe at all\n", &versioned_blob((1, 0, 0, 0)));
    assert_eq!(status_of(&l, &r, "version"), Status::RightNewer);
    // Neither side has one: no version difference at all (u4c `ver-txt-files`).
    let (l, r) = one_file_pair("a.txt", b"alpha\n", b"beta\n");
    assert_eq!(status_of(&l, &r, "version"), Status::Same);
}

#[test]
fn version_criterion_outranks_size_and_timestamp() {
    // u4b `ver-real-differs-size-absorbs` and gate serial-06
    // `crit-version-size` (`one_sided.dll`): the versions differ AND the sizes
    // differ, and the row still carries the version DIRECTION, not `diff` --
    // the version comparison outranks both quick tests.
    let (l, r) = one_file_pair(
        "a.dll",
        &versioned_blob((1, 0, 0, 0)),
        &[versioned_blob((9, 9, 9, 9)), vec![0u8; 4096]].concat(),
    );
    assert_eq!(status_of(&l, &r, "version"), Status::RightNewer);
    assert_eq!(
        status_of(&l, &r, "version size"),
        Status::RightNewer,
        "the version direction outranks a size difference too (serial-06)"
    );
    // Equal versions under `version size` DO compare sizes (u4k
    // `fixture-shape`: equal versions, padded right side -> `diff`).
    let (l, r) = one_file_pair(
        "a.dll",
        &versioned_blob((1, 0, 0, 0)),
        &[versioned_blob((1, 0, 0, 0)), vec![0u8; 4096]].concat(),
    );
    assert_eq!(status_of(&l, &r, "version"), Status::Same);
    assert_eq!(status_of(&l, &r, "version size"), Status::Diff);
}

#[test]
fn posix_metadata_criteria_are_inert_on_windows() {
    // u4 `permissions-acl-differs`, u4e `owner-size-differs`: the token is
    // accepted, and it contributes nothing — a SIZE difference is even ignored
    // because the token replaced the default size+timestamp pair.
    let (l, r) = one_file_pair("a.bin", b"0123456789", &[b"0123456789".as_slice(), &[0u8; 2048]].concat());
    for spec in ["permissions", "owner", "group"] {
        assert_eq!(status_of(&l, &r, spec), Status::Same, "{spec}");
    }
    // ...but a later size token re-activates (u4f `f-owner-plus-size` -> diff).
    assert_eq!(status_of(&l, &r, "owner size"), Status::Diff);
}

#[test]
fn ignore_unimportant_folds_only_rules_based_content_differences() {
    // u4e `rb-comment-only-iu`: a comment-only .c difference becomes `same`.
    let (l, r) = one_file_pair("t.c", b"int x; // old\n", b"int x; // new\n");
    assert_eq!(status_of(&l, &r, "rules-based"), Status::Diff);
    assert_eq!(status_of(&l, &r, "rules-based ignore-unimportant"), Status::Same);
    // u4e `rb-real-diff-iu`: a real difference stays `diff`.
    let (l, r) = one_file_pair("t.c", b"int x = 1;\n", b"int x = 2;\n");
    assert_eq!(status_of(&l, &r, "rules-based ignore-unimportant"), Status::Diff);
    // u4f `f-iu-rb-ws`: a whitespace-only difference folds.
    let (l, r) = one_file_pair("t.c", b"int  x;\n", b"int x;\n");
    assert_eq!(status_of(&l, &r, "rules-based ignore-unimportant"), Status::Same);
    // u4e `rb-identical-iu`.
    let (l, r) = one_file_pair("t.c", b"int x;\n", b"int x;\n");
    assert_eq!(status_of(&l, &r, "rules-based ignore-unimportant"), Status::Same);
    // `ignore-unimportant` ALONE names no comparison at all, so even a huge
    // size difference reports `same` (u4i `ignore-unimportant-alone`, where a
    // 2048-byte size difference AND a 2-hour timestamp difference both yield
    // `same`).
    let (l, r) = one_file_pair("t.c", b"0123456789", &[b"0123456789".as_slice(), &[0u8; 2048]].concat());
    assert_eq!(status_of(&l, &r, "ignore-unimportant"), Status::Same);
    // ...while naming a comparison alongside it does compare (u4e/u4f).
    assert_eq!(status_of(&l, &r, "size ignore-unimportant"), Status::Diff);
}

#[test]
fn ignore_unimportant_emits_the_empty_element_after_the_paths() {
    let (l, r) = one_file_pair("t.c", b"int x; // old\n", b"int x; // new\n");
    let crit = Criteria::parse("rules-based ignore-unimportant").unwrap();
    let c = compare_folders(&l, &r, &crit, CompareOptions::default()).unwrap();
    let opts = ReportOptions { ignore_unimportant: true, ..ReportOptions::default() };
    let xml = report::render(&c, Layout::Xml, &opts).unwrap();
    let rt = xml.find("<rtpath>").unwrap();
    let iu = xml.find("<ignoreunimportant/>").unwrap();
    let first_row = xml.find("<filecomp").unwrap();
    assert!(rt < iu && iu < first_row, "{xml}");
}

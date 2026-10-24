//! The directory tree model: recursion, left/right alignment, status computation.
//!
//! # Alignment (O + D)
//!
//! `help/dir_how_to_compare.html`:
//!
//! > The display aligns files and subfolders of the same name, left and right.
//!
//! and
//!
//! > A folder is classified as "newer" if it contains newer files. Folders are
//! > compared by aggregating the comparisons of files within them.
//!
//! So alignment is **by name within the same relative directory**, and a
//! directory's result is an aggregate of its children — not a comparison of the
//! directories' own timestamps.
//!
//! # Ordering of entries (D, derived from the observed report)
//!
//! In `tools/_audit/dir-load-expand-report.xml` (O) the top-level entries appear
//! as:
//!
//! ```text
//! emptydir (rt only)   sub (both)   diff.txt   leftonly.txt   rightonly.txt
//! same.txt   samesize.bin
//! ```
//!
//! `diff.txt` sorts before `emptydir` ordinally, so directories are **not**
//! interleaved with files: the report lists directories first, then files, each
//! group name-sorted. [`TreeNode::children`] preserves that order.
//!
//! Whether the sort is ordinal or a natural/case-insensitive collation is not
//! determined by that single sample — see `docs/EVIDENCE.md` U-M3-6. This
//! implementation sorts ordinally and exposes the question.
//!
//! # Expansion and filtering (M4, added by task B)
//!
//! The M3 engine always recursed and always rendered an aggregate `<size>`.
//! The M4 script probes measured that this is only true when the folder is
//! **expanded** (`U5-FINDINGS.md` §4, u5g/u5h/u5j):
//!
//! * an *unexpanded* directory has **no child rows** and renders `<size/>`;
//! * an *expanded* directory whose whole subtree is expanded renders the
//!   aggregate of the file bytes in that subtree, per side;
//! * an *expanded* directory with something still collapsed below it renders
//!   `<size/>` as well — so "has children" and "shows an aggregate" are
//!   different questions (`expand "A"` vs `expand "A\B"`, u5g s3/s4).
//!
//! [`ExpandPolicy`] answers the first question; the second is answered
//! bottom-up while the tree is built, which is why [`TreeNode`] carries an
//! `expanded` flag and [`TreeNode::fully_expanded`] is a method rather than a
//! policy lookup (see `expand.rs` for why a path alone cannot decide it).
//!
//! A `filter` changes the **visible row set** and nothing else: a directory
//! removed by a folder exclude mask takes its subtree with it (u5h `-A\`),
//! while a file that no mask matches is dropped from the report but still
//! counted in its parent's aggregate — u5c `filter-include-txt` shows `sub` as
//! `8` while only its 4-byte `c.txt` is visible, and u5g s7 shows `A=10` with
//! no file rows at all. Rows that are filtered out are therefore kept in the
//! tree with `hidden = true` so the aggregate stays right, and every
//! row-walking API here skips them.
//!
//! # Status computation
//!
//! Per the criteria module, the content criteria are evaluated independently and
//! the outcome maps to the six observed report tokens:
//!
//! | condition | status |
//! |---|---|
//! | one side only | `ltonly` / `rtonly` |
//! | every criterion matches | `same` |
//! | only the timestamp criterion differs | `ltnewer` / `rtnewer` |
//! | anything else differs | `diff` |
//!
//! The `ltnewer`/`rtnewer` row is a **derivation**, not a measurement. It follows
//! from three pieces of *observed* evidence: the writer emits exactly those two
//! tokens for the "newer" cases
//! (`extracted/pseudocode/140fd1e90.c`); the display help says a file's colour is
//! "newer **or** different" and that a content comparison "can override the file
//! colors ... would change to all black if the content comparison determines the
//! files match"; and the criteria probe shows the default really does compare
//! timestamp and size. What is *not* measured is the exact trigger boundary — see
//! `docs/EVIDENCE.md` U-M3-1. Fixture cases that exercise it are labelled
//! `predicted` in the manifest.

use reacmp_vfs::{
    AttributeSet, Entry, EntryKind, FileSystem, ListOptions, Metadata, SymlinkPolicy, Timestamp,
    VfsPath, VfsResult,
};

use crate::criteria::{ContentCriteria, Criteria, Side, TimezoneRule};
use crate::error::DirError;
use crate::expand::ExpandPolicy;
use crate::filter::Filter;
use crate::status::{ComparisonNote, Status};

/// One aligned row of the comparison.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TreeNode {
    /// The entry's name. For an aligned pair both sides agree, by construction.
    pub name: String,
    /// Path relative to the comparison root, using the backend separator.
    /// Empty for the root itself.
    pub relative_path: String,
    /// Left-hand entry, absent when the entry is right-only.
    pub left: Option<Entry>,
    /// Right-hand entry, absent when the entry is left-only.
    pub right: Option<Entry>,
    /// The comparison result for this row.
    pub status: Status,
    /// Child rows, in report order. Empty for a file.
    pub children: Vec<TreeNode>,
    /// Whether this row is **rendered** at all.
    ///
    /// Set for a file row that no `filter` mask matched (u5c
    /// `filter-include-txt`: `b.log` is gone from the report while `a.txt`
    /// stays).  A filtered-out row is still in the tree because a directory's
    /// `<size>` aggregates the subtree **including** the files no mask matched
    /// — u5c shows `sub` as `8` while only its 4-byte `c.txt` is visible, and
    /// u5g s7 shows `A=10` with no file rows at all — so the row cannot simply
    /// be dropped.  Every row-walking API here skips it, and so does the
    /// report writer.
    pub hidden: bool,
    /// Whether this row's **child rows are present**.
    ///
    /// Measured (u5g s1: no `expand`; s3: `expand "A"`): a directory that is
    /// not expanded renders no children at all.  Note that the inverse is not
    /// "an aggregate `<size>`": an expanded directory whose subtree still has a
    /// collapsed directory below it renders `<size/>` too (u5g s3 `A`), which
    /// is what [`TreeNode::subtree_fully_expanded`] decides.  Always `true` for
    /// a file row, which has no children by definition.
    pub expanded: bool,
    /// Explicit notes about behaviour that is deliberately not implemented.
    pub notes: Vec<ComparisonNote>,
}


impl TreeNode {
    pub fn is_dir(&self) -> bool {
        self.left
            .as_ref()
            .or(self.right.as_ref())
            .map(|e| matches!(e.metadata.kind, EntryKind::Directory))
            .unwrap_or(false)
    }

    /// True when this row should be reported as an expandable directory row
    /// (`<foldercomp>`), rather than a file row (`<filecomp>`).
    ///
    /// Distinct from [`TreeNode::is_dir`] for a *kind conflict* — a name that is a
    /// file on one side and a directory on the other. Such a row cannot be
    /// expanded as a directory (there is a file on one side), so it is reported as
    /// a `filecomp`, which is the only structural choice the observed XML offers.
    /// **Derived, not observed**: no Oracle report containing a kind conflict
    /// exists in this workspace, so the representation is this project's choice —
    /// see `docs/EVIDENCE.md` U-M3-8.
    pub fn is_dir_row(&self) -> bool {
        match (&self.left, &self.right) {
            (Some(l), Some(r)) => {
                matches!(l.metadata.kind, EntryKind::Directory)
                    && matches!(r.metadata.kind, EntryKind::Directory)
            }
            (Some(l), None) => matches!(l.metadata.kind, EntryKind::Directory),
            (None, Some(r)) => matches!(r.metadata.kind, EntryKind::Directory),
            (None, None) => false,
        }
    }

    /// True when the two sides exist but are not the same kind.
    pub fn is_kind_conflict(&self) -> bool {
        match (&self.left, &self.right) {
            (Some(l), Some(r)) => l.metadata.kind != r.metadata.kind,
            _ => false,
        }
    }

    /// The size the report shows for this entry.
    ///
    /// Observed: an unexpanded directory renders `<size/>` and a fully expanded
    /// one renders the aggregate of its files —
    /// `dir-load-then-report.xml` has `<name>sub</name><size/>` while
    /// `dir-load-expand-report.xml` (same tree, after `expand all`) has
    /// `<name>sub</name><size>3</size>` and `<name>emptydir</name><size>0</size>`
    /// (O). So the reported size is the entry's own size for a file, and the sum
    /// of file sizes in the subtree for a directory.
    ///
    /// **M4 refinement (O)**: the aggregate appears only when the whole subtree
    /// is expanded.  u5g measured `A=<size/>` for `expand "A"` (its `B` was
    /// still collapsed) against `A=10` for `expand "A\B"`, so this returns
    /// `None` — the `<size/>` shape — for any directory that is not expanded or
    /// has a collapsed directory below it.  [`TreeNode::subtree_fully_expanded`]
    /// is the predicate, and it is computed while the tree is built.
    ///
    /// Whether the aggregate is the whole subtree or only immediate children is
    /// not separable from the M3 sample (`sub` has one file and no nested
    /// directory) — see `docs/EVIDENCE.md` U-M3-7. This implementation sums the
    /// whole subtree, which the A-3 gate's `deep-nesting` case confirmed
    /// (`A3-folder-gate-serial-03`).
    ///
    /// Files hidden by a `filter` still count: U5-FINDINGS §3 ("文件夹行的
    /// `<size>` 聚合**忽略 filter**"), reproduced here by summing over every
    /// child regardless of its `hidden` flag.
    pub fn reported_size(&self, side: Side) -> Option<u64> {
        if self.is_dir() {
            if !self.subtree_fully_expanded() {
                // `<size/>`: the measured shape for a directory the report did
                // not fully descend into (u5g s1/s3, u5h expand-a-file).
                return None;
            }
            // OBSERVED (A3-folder-gate-serial-03, deep-nesting): the Oracle
            // aggregates the file bytes of the WHOLE subtree, per side — the
            // gate caught the right side of a differing 12-level chain showing
            // 9 (its own leaf) while this engine rendered the left side's 4.
            // The audit trees could not expose this because their two sides
            // are byte-identical.
            let mut total: u64 = 0;
            for child in &self.children {
                if let Some(s) = child.reported_size(side) {
                    total = total.saturating_add(s);
                }
            }
            Some(total)
        } else {
            let e = if side == Side::Left {
                self.left.as_ref()
            } else {
                self.right.as_ref()
            };
            e.and_then(|e| e.metadata.size)
        }
    }

    /// True when this row's whole subtree is present in the report, which is
    /// exactly when the row renders an aggregate `<size>` (u5g s4 `A=10`,
    /// s6 `C=3`, s3 `A=<size/>`).
    ///
    /// The value is computed during the tree build (`CompareCtx::
    /// remember_expansion`) because it is a subtree predicate: a directory with
    /// children on disk and no expanded child directory is fully expanded the
    /// moment it is expanded itself, while the same directory with one
    /// collapsed child directory is not.  A file row is always fully expanded
    /// in this sense, which is what lets a file's own size flow into a parent's
    /// aggregate.
    pub fn subtree_fully_expanded(&self) -> bool {
        self.expanded && self.children.iter().all(TreeNode::subtree_fully_expanded)
    }

    /// True when a `filter` removed this row from the report.
    pub fn is_hidden(&self) -> bool {
        self.hidden
    }

    /// The rows that are actually rendered, in report order.
    pub fn visible_children(&self) -> impl Iterator<Item = &TreeNode> {
        self.children.iter().filter(|c| !c.hidden)
    }

    /// The modified time the report shows. A directory reports its **own**
    /// timestamp, not an aggregate (O: `emptydir` and `sub` both show
    /// `2026/10/13 10:06:12`, which is each directory's own mtime).
    pub fn reported_modified(&self) -> Option<Timestamp> {
        self.left
            .as_ref()
            .or(self.right.as_ref())
            .and_then(|e| e.metadata.modified)
    }

    /// The metadata the report shows for one side.
    pub fn metadata_for(&self, side: Side) -> Option<&Metadata> {
        match side {
            Side::Left => self.left.as_ref(),
            Side::Right => self.right.as_ref(),
        }
        .map(|e| &e.metadata)
    }

    /// Depth-first walk of every **rendered** row, parents before children.
    ///
    /// A row removed by a `filter` is skipped, together with its subtree (a
    /// hidden row is either a file, which has none, or a folder removed by a
    /// folder-exclude mask, whose subtree the Oracle also removes — u5h
    /// `-A\`).
    pub fn walk(&self, visit: &mut impl FnMut(&TreeNode)) {
        if self.hidden {
            return;
        }
        visit(self);
        for child in &self.children {
            child.walk(visit);
        }
    }

    /// Total **rendered** row count including this node.
    pub fn row_count(&self) -> usize {
        if self.hidden {
            return 0;
        }
        1 + self.children.iter().map(TreeNode::row_count).sum::<usize>()
    }

    /// Count rendered rows by status.
    pub fn count_status(&self, status: Status) -> usize {
        if self.hidden {
            return 0;
        }
        let mut n = if self.status == status { 1 } else { 0 };
        for child in &self.children {
            n += child.count_status(status);
        }
        n
    }
}

/// The result of comparing two folders.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FolderComparison {
    pub left_root: VfsPath,
    pub right_root: VfsPath,
    pub criteria: Criteria,
    /// Rows at the top level of the comparison, in report order.
    pub entries: Vec<TreeNode>,
    /// Notes attached to the comparison as a whole.
    pub notes: Vec<ComparisonNote>,
    /// Whether symlinks were followed (mirrors `criteria.follow_symlinks`).
    pub follow_symlinks: bool,
    /// The local UTC offset, in minutes east, used to render timestamps.
    ///
    /// Recorded explicitly because the observed report renders local wall-clock
    /// time (see `reacmp_vfs::time`), so the same tree rendered in two zones
    /// legitimately differs. `None` means the offset was unknown and the report
    /// says so.
    pub offset_minutes: Option<i32>,
    /// The `expand` policy the tree was built under, so a renderer or a caller
    /// can see why some directories show `<size/>` (u5g).
    pub expand: ExpandPolicy,
    /// The `filter` in force, when one was set, so the report can echo
    /// `<filters>` and a caller can see which rows were removed.
    pub filter: Filter,
}

impl FolderComparison {
    /// Walk every **rendered** row (see [`TreeNode::walk`]).
    pub fn walk(&self, visit: &mut impl FnMut(&TreeNode)) {
        for e in &self.entries {
            e.walk(visit);
        }
    }

    pub fn count_status(&self, status: Status) -> usize {
        self.entries.iter().map(|e| e.count_status(status)).sum()
    }

    pub fn row_count(&self) -> usize {
        self.entries.iter().map(TreeNode::row_count).sum()
    }

    /// The statuses of the top-level rows, in report order. The fixture runner
    /// asserts against this projection, which is the folder analogue of the
    /// text corpus's `statuses` array.
    pub fn top_level_statuses(&self) -> Vec<&'static str> {
        self.entries
            .iter()
            .map(|n| n.status.xml_token().unwrap_or("unknown"))
            .collect()
    }
}

/// Comparison options that are not part of the criteria grammar.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompareOptions {
    /// Whether entry names are compared case-insensitively.
    ///
    /// `specs/dir/DirTree.md` section 4 line 566 records a name comparison
    /// function taking a `tree+0xe8` carrying "大小写/编码选项" (case/encoding
    /// options), i.e. case handling is an option rather than a constant. Its
    /// default has not been probed in this workspace
    /// (`docs/EVIDENCE.md` U-M3-5), and a Windows directory cannot hold two names
    /// differing only in case, so this only affects cross-filesystem comparison.
    /// Default `false` = ordinal, which is what an exact-name alignment means.
    pub case_insensitive_names: bool,
    /// Whether to read file bytes to evaluate a content criterion.
    ///
    /// Default `true`: CRC/binary/rules-based are meaningless without it, and
    /// silently skipping a read would make them fake. Set to `false` only in a
    /// test that asserts the refusal.
    pub allow_content_read: bool,
    /// Which directories the report descends into (`expand`), and therefore
    /// which directory rows show an aggregate `<size>`.
    ///
    /// The default is [`ExpandPolicy::All`] — the M3 behaviour, where the
    /// engine always recursed and always aggregated — so every existing folder
    /// fixture and the 429-case M3 gate keep their bytes. A script that sends
    /// no `expand` uses [`ExpandPolicy::None`] (u5g s1: `A=<size/>`, no child
    /// rows), and `expand "<p>"` maps to [`ExpandPolicy::Only`].
    pub expand: ExpandPolicy,
}

impl Default for CompareOptions {
    fn default() -> Self {
        CompareOptions {
            case_insensitive_names: false,
            allow_content_read: true,
            expand: ExpandPolicy::All,
        }
    }
}

/// Compare two folder trees.
///
/// # Errors
///
/// Every I/O failure is an explicit error. A listing that cannot be read fails
/// the comparison; it is never treated as an empty directory, because an empty
/// directory and an unreadable one are different observations and the report
/// distinguishes them.
pub fn compare_folders(
    left: &dyn FileSystem,
    right: &dyn FileSystem,
    criteria: &Criteria,
    options: CompareOptions,
) -> Result<FolderComparison, DirError> {
    compare_folders_filtered(left, right, criteria, options, &Filter::none())
}

/// Compare two folder trees under a `filter`.
///
/// The filter is applied while the tree is built rather than as a post-pass,
/// because the two halves behave differently and only the build knows which is
/// which: a file no mask matched stays in the tree marked `hidden` (so its bytes
/// still count toward its parent's aggregate, per U5-FINDINGS §3), while a
/// folder removed by a folder-exclude mask takes its whole subtree with it
/// (u5h `-A\`).  Split out of [`compare_folders`] so the 429-case M3 gate and
/// every existing caller keep the unfiltered entry point unchanged.
pub fn compare_folders_filtered(
    left: &dyn FileSystem,
    right: &dyn FileSystem,
    criteria: &Criteria,
    options: CompareOptions,
    filter: &Filter,
) -> Result<FolderComparison, DirError> {
    let list_options = ListOptions {
        symlinks: if criteria.follow_symlinks {
            SymlinkPolicy::Follow
        } else {
            SymlinkPolicy::DoNotFollow
        },
    };

    let mut notes: Vec<ComparisonNote> = Vec::new();
    if criteria.content.contains(&ContentCriteria::RulesBased) {
        // Declared once for the whole comparison rather than per file, and
        // carried into the report so the verdict cannot be mistaken for full BC
        // rules-based semantics (M2 is not implemented yet).
        notes.push(ComparisonNote::RulesBasedTextRulesNotImplemented);
    }

    // The offset used to render timestamps: the left backend's local zone, or the
    // right's when the left has none (e.g. an archive). `None` when neither
    // knows, in which case the report says the offset was not known.
    let probe_instant = left
        .metadata_opt(left.root(), list_options)
        .ok()
        .flatten()
        .and_then(|m| m.modified)
        .map(|t| t.unix_millis())
        .unwrap_or(0);
    let offset_minutes = left
        .local_offset_minutes(probe_instant)
        .or_else(|| right.local_offset_minutes(probe_instant));

    let expand = options.expand.clone();
    let mut ctx = CompareCtx {
        left,
        right,
        criteria,
        options,
        list_options,
        filter,
    };
    let entries = ctx.compare_dir(left.root(), right.root(), "", &mut notes)?;

    Ok(FolderComparison {
        left_root: left.root().clone(),
        right_root: right.root().clone(),
        criteria: criteria.clone(),
        entries,
        notes,
        follow_symlinks: criteria.follow_symlinks,
        offset_minutes,
        expand,
        filter: filter.clone(),
    })
}

struct CompareCtx<'a> {
    left: &'a dyn FileSystem,
    right: &'a dyn FileSystem,
    criteria: &'a Criteria,
    options: CompareOptions,
    list_options: ListOptions,
    filter: &'a Filter,
}

impl CompareCtx<'_> {
    /// List one directory's aligned rows.
    ///
    /// `relative` is the directory's own path relative to the comparison root
    /// (`""` for the root), which is what the `expand` policy is keyed on and
    /// what a filter mask with separators is matched against.
    fn compare_dir(
        &mut self,
        left_path: &VfsPath,
        right_path: &VfsPath,
        relative: &str,
        notes: &mut Vec<ComparisonNote>,
    ) -> Result<Vec<TreeNode>, DirError> {
        // A root that is absent is not an "empty directory": refuse explicitly.
        let left_entries = self.list_or_absent(self.left, left_path, Side::Left)?;
        let right_entries = self.list_or_absent(self.right, right_path, Side::Right)?;

        let aligned = align_entries(left_entries, right_entries, self.options.case_insensitive_names);

        // Report order is directories first, then files, each by the Oracle's
        // name collation. A kind conflict contributes to BOTH groups: the
        // directory side is an expanded one-sided <foldercomp>, the file side
        // a one-sided <filecomp> (gate FINDINGS F1).
        let mut dirs_out: Vec<TreeNode> = Vec::with_capacity(aligned.len());
        let mut files_out: Vec<TreeNode> = Vec::with_capacity(aligned.len());
        for (name, l, r) in aligned {
            let child_rel = if relative.is_empty() {
                name.clone()
            } else {
                format!("{relative}{}{}", self.left.separator(), name)
            };

            let left_kind = l.as_ref().map(|e| e.metadata.kind);
            let right_kind = r.as_ref().map(|e| e.metadata.kind);
            let left_is_dir = left_kind == Some(EntryKind::Directory);
            let right_is_dir = right_kind == Some(EntryKind::Directory);

            // Two entries that exist on both sides but are not the same kind
            // are not merged into one row. The A-3 folder gate observed the
            // live Oracle emitting each side separately — the directory as an
            // expanded one-sided <foldercomp> whose children carry the same
            // one-sided status, and the file as a one-sided <filecomp>
            // (FINDINGS F1, `struct-file-vs-dir-conflict-default`). The
            // earlier single-`diff`-row guess was wrong.
            let kind_conflict = match (left_kind, right_kind) {
                (Some(a), Some(b)) => a != b,
                _ => false,
            };

            if kind_conflict {
                // FINDINGS F1: emit each side separately. The directory side is
                // an expanded one-sided <foldercomp> (its children carry the
                // same one-sided status); the non-directory side is a one-sided
                // <filecomp>. The link-vs-file combination is unobserved in the
                // gate corpus, so treating it like the observed file-vs-dir
                // case is a derived generalisation (EVIDENCE.md U-M3-8 note).
                for (side_left, entry) in [(true, l.as_ref()), (false, r.as_ref())] {
                    let entry = match entry {
                        Some(e) => e,
                        None => continue,
                    };
                    if matches!(entry.metadata.kind, EntryKind::Directory) {
                        // u5h `-A\` removes the folder AND its subtree, so a
                        // removed directory side of a conflict contributes no
                        // row at all. The help text says the same: "expand all
                        // will not expand subfolders that have been excluded
                        // from the comparison by File Filter settings".
                        if !self.filter.folder_visible(&name, &child_rel) {
                            continue;
                        }
                        let expanded = self.options.expand.is_expanded(&child_rel);
                        let children = if expanded {
                            self.expand_one_sided_dir(&entry.path, &child_rel, side_left, notes)?
                        } else {
                            Vec::new()
                        };
                        let status = if side_left {
                            Status::LeftOnly
                        } else {
                            Status::RightOnly
                        };
                        dirs_out.push(TreeNode {
                            name: name.clone(),
                            relative_path: child_rel.clone(),
                            left: if side_left { l.clone() } else { None },
                            right: if side_left { None } else { r.clone() },
                            status,
                            children,
                            hidden: false,
                            expanded,
                            notes: Vec::new(),
                        });
                    } else {
                        // One-sided row: the other side holds a DIFFERENT kind
                        // under the same name, so it must not be rendered into
                        // this <filecomp> — the writer omits a None side
                        // entirely (the observed one-sided row shape).
                        let status = if side_left {
                            Status::LeftOnly
                        } else {
                            Status::RightOnly
                        };
                        let hidden = !self.filter.file_visible(&name, &child_rel);
                        files_out.push(TreeNode {
                            name: name.clone(),
                            relative_path: child_rel.clone(),
                            left: if side_left { l.clone() } else { None },
                            right: if side_left { None } else { r.clone() },
                            status,
                            children: Vec::new(),
                            hidden,
                            expanded: true,
                            notes: Vec::new(),
                        });
                    }
                }
                continue;
            }

            if left_is_dir || right_is_dir {
                // A folder mask that excludes this folder removes it and its
                // whole subtree (u5h `fg-exclude-A-*`).
                if !self.filter.folder_visible(&name, &child_rel) {
                    continue;
                }
                // An unexpanded directory is not listed AT ALL (u5g s1: `A` has
                // no child rows whatsoever), and the policy is checked before
                // the recursion so a collapsed directory's contents are never
                // even read.
                let expanded = self.options.expand.is_expanded(&child_rel);
                let l_path = l
                    .as_ref()
                    .map(|e| e.path.clone())
                    .unwrap_or_else(|| self.join_relative(left_path, &name));
                let r_path = r
                    .as_ref()
                    .map(|e| e.path.clone())
                    .unwrap_or_else(|| self.join_relative(right_path, &name));
                // A one-sided directory has no other side to recurse into; its
                // children are taken from the side that exists so the report shows
                // the real structure rather than an empty folder.
                let children = if !expanded {
                    Vec::new()
                } else {
                    match (&l, &r) {
                        (Some(_), Some(_)) => {
                            self.compare_dir(&l_path, &r_path, &child_rel, notes)?
                        }
                        (Some(_), None) => {
                            let absent = self.join_relative(right_path, &name);
                            self.compare_dir(&l_path, &absent, &child_rel, notes)?
                        }
                        (None, Some(_)) => {
                            let absent = self.join_relative(left_path, &name);
                            self.compare_dir(&absent, &r_path, &child_rel, notes)?
                        }
                        (None, None) => Vec::new(),
                    }
                };
                let status = directory_status(&l, &r, &children);
                dirs_out.push(TreeNode {
                    name,
                    relative_path: child_rel,
                    left: l,
                    right: r,
                    status,
                    children,
                    hidden: false,
                    expanded,
                    notes: Vec::new(),
                });
            } else {
                let status = self.file_status(&name, &l, &r, notes)?;
                // A file row that no mask matches is dropped from the report
                // but kept in the tree: its bytes still count in the parent's
                // aggregate (u5c `filter-include-txt` shows `sub` as 8 with
                // only its 4-byte `c.txt` visible; u5g s7 shows `A=10` with no
                // file rows at all).
                let hidden = !self.filter.file_visible(&name, &child_rel);
                files_out.push(TreeNode {
                    name,
                    relative_path: child_rel,
                    left: l,
                    right: r,
                    status,
                    children: Vec::new(),
                    hidden,
                    expanded: true,
                    notes: Vec::new(),
                });
            }
        }

        dirs_out.sort_by(|a, b| name_order::compare(&a.name, &b.name));
        files_out.sort_by(|a, b| name_order::compare(&a.name, &b.name));
        dirs_out.extend(files_out);
        Ok(dirs_out)
    }

    /// Append one name to a parent path using this side's separator.
    fn join_relative(&self, parent: &VfsPath, name: &str) -> VfsPath {
        self.left.join(parent, name)
    }

    /// Expand a directory that exists on only ONE side — a one-sided directory
    /// or the directory side of a kind conflict. Every row carries only that
    /// side; nested directories recurse the same way. This deliberately does
    /// not reuse `compare_dir` with a joined "absent" path: in a kind conflict
    /// the other side's path exists as a DIFFERENT kind, and listing it would
    /// either fail (`NotADirectory`) or silently compare the wrong thing.
    fn expand_one_sided_dir(
        &mut self,
        path: &VfsPath,
        relative: &str,
        side_left: bool,
        notes: &mut Vec<ComparisonNote>,
    ) -> Result<Vec<TreeNode>, DirError> {
        let (fs, side) = if side_left {
            (self.left, Side::Left)
        } else {
            (self.right, Side::Right)
        };
        let mut entries = self.list_or_absent(fs, path, side)?;
        sort_entries(&mut entries);
        let mut out = Vec::with_capacity(entries.len());
        for entry in entries {
            let child_rel = if relative.is_empty() {
                entry.name.clone()
            } else {
                format!("{relative}{}{}", self.left.separator(), entry.name)
            };
            let is_dir = matches!(entry.metadata.kind, EntryKind::Directory);
            if is_dir && !self.filter.folder_visible(&entry.name, &child_rel) {
                // `-A\` prunes the whole subtree (u5h), including one-sided
                // rows: `expand all` never expands a folder a file filter
                // excluded (help, EXPAND).
                continue;
            }
            let expanded = if is_dir {
                self.options.expand.is_expanded(&child_rel)
            } else {
                true
            };
            let children = if is_dir && expanded {
                self.expand_one_sided_dir(&entry.path, &child_rel, side_left, notes)?
            } else {
                Vec::new()
            };
            let status = if side_left {
                Status::LeftOnly
            } else {
                Status::RightOnly
            };
            out.push(TreeNode {
                name: entry.name.clone(),
                relative_path: child_rel,
                left: if side_left { Some(entry.clone()) } else { None },
                right: if side_left { None } else { Some(entry) },
                status,
                children,
                hidden: false,
                expanded,
                notes: Vec::new(),
            });
        }
        Ok(out)
    }

    fn list_or_absent(
        &self,
        fs: &dyn FileSystem,
        path: &VfsPath,
        _side: Side,
    ) -> Result<Vec<Entry>, DirError> {
        match fs.read_dir(path, self.list_options) {
            Ok(mut v) => {
                sort_entries(&mut v);
                Ok(v)
            }
            Err(e) if e.is_absence() => Ok(Vec::new()),
            Err(e) => Err(DirError::Vfs { source: e }),
        }
    }

    fn file_status(
        &self,
        name: &str,
        left: &Option<Entry>,
        right: &Option<Entry>,
        notes: &mut Vec<ComparisonNote>,
    ) -> Result<Status, DirError> {
        match (left, right) {
            (Some(_), None) => Ok(Status::LeftOnly),
            (None, Some(_)) => Ok(Status::RightOnly),
            (None, None) => Ok(Status::Unknown),
            (Some(l), Some(r)) => {
                let mut timestamp_differs: Option<bool> = None;
                let mut non_timestamp_differs = false;
                // Set by a `version` criterion difference (u4c/u4f): the result
                // is directional, reported as `ltnewer`/`rtnewer`.
                let mut version_newer: Option<Side> = None;

                // A symlink that is not followed has no size and no contents, so
                // size or content criteria do not *apply* to it. The A-3 gate
                // observed the live Oracle judging an unfollowed junction pair
                // by its targets even under the default size+timestamp
                // criteria (FINDINGS F7: `links-not-followed-default` →
                // `diff`), so the target comparison is not gated on a content
                // criterion; the inapplicability of content criteria is
                // recorded either way.
                let both_unfollowed_links = matches!(l.metadata.kind, EntryKind::Symlink)
                    && matches!(r.metadata.kind, EntryKind::Symlink);
                if both_unfollowed_links {
                    let same_target = l.metadata.symlink_target == r.metadata.symlink_target;
                    for criterion in &self.criteria.content {
                        if criterion.requires_content_read() {
                            notes.push(ComparisonNote::CriterionNotApplicable {
                                name: name.to_string(),
                                criterion: criterion.as_str(),
                            });
                        }
                    }
                    if !same_target {
                        return Ok(Status::Diff);
                    }
                    // The timestamp criterion still applies: a link does have an
                    // mtime.
                    if self.criteria.content.contains(&ContentCriteria::Timestamp) {
                        match (l.metadata.modified, r.metadata.modified) {
                            (Some(a), Some(b)) => {
                                timestamp_differs = Some(!self.criteria.timestamp.matches(a, b));
                            }
                            _ => timestamp_differs = None,
                        }
                    }
                    if non_timestamp_differs {
                        return Ok(Status::Diff);
                    }
                    return Ok(match timestamp_differs {
                        Some(true) => {
                            let (a, b) = (l.metadata.modified, r.metadata.modified);
                            match (a, b) {
                                (Some(a), Some(b)) if a > b => Status::LeftNewer,
                                (Some(_), Some(_)) => Status::RightNewer,
                                _ => Status::Unknown,
                            }
                        }
                        _ => Status::Same,
                    });
                }

                for criterion in &self.criteria.content {
                    match criterion {
                        ContentCriteria::Timestamp => {
                            let (lo, ro) = self.criteria.timezone.offsets_seconds();
                            match (l.metadata.modified, r.metadata.modified) {
                                (Some(a), Some(b)) => {
                                    let a = shift(a, lo);
                                    let b = shift(b, ro);
                                    let raw_diff = a.seconds_between(b);
                                    let differs = if self
                                        .criteria
                                        .timezone
                                        .suppresses_whole_hour_differences()
                                        && raw_diff % 3600 == 0
                                    {
                                        // `timezone:ignore`: a whole-hour offset is
                                        // a zone artefact, not a real difference.
                                        false
                                    } else {
                                        !self.criteria.timestamp.matches(a, b)
                                    };
                                    timestamp_differs = Some(differs);
                                }
                                // A timestamp the backend cannot report is an
                                // explicit unknown, never "equal".
                                _ => {
                                    notes.push(ComparisonNote::ReadFailed {
                                        name: name.to_string(),
                                        detail: "modified time unavailable on at least one side"
                                            .to_string(),
                                    });
                                    return Ok(Status::Unknown);
                                }
                            }
                        }
                        ContentCriteria::Size => {
                            match (l.metadata.size, r.metadata.size) {
                                (Some(a), Some(b)) if a == b => {}
                                (Some(_), Some(_)) => non_timestamp_differs = true,
                                _ => {
                                    notes.push(ComparisonNote::ReadFailed {
                                        name: name.to_string(),
                                        detail: "size unavailable on at least one side".to_string(),
                                    });
                                    return Ok(Status::Unknown);
                                }
                            }
                        }
                        ContentCriteria::Version => {
                            // Directional, not equal/not-equal: a higher FileVersion
                            // is reported `ltnewer`/`rtnewer`, and a side with no
                            // version resource is older than one with a resource
                            // (u4c/u4f). Only regular files carry a version.
                            match self.version_order(l, r)? {
                                VersionOrder::Equal => {}
                                VersionOrder::LeftNewer => {
                                    version_newer = Some(Side::Left);
                                }
                                VersionOrder::RightNewer => {
                                    version_newer = Some(Side::Right);
                                }
                            }
                        }
                        ContentCriteria::Owner
                        | ContentCriteria::Group
                        | ContentCriteria::Permissions => {
                            // Measured inert on Windows (u4 `owner-equal-files`,
                            // `permissions-acl-differs`; u4b `perm-dir-acl`): the
                            // token is accepted and the comparison contributes
                            // nothing on this platform. The criterion still
                            // replaces the default pair, which the `content` list
                            // models, so there is no branch body.
                        }
                        ContentCriteria::Crc
                        | ContentCriteria::Binary
                        | ContentCriteria::RulesBased => {
                            if self.content_differs(l, r)? {
                                // `rules-based ignore-unimportant`: an
                                // unimportant-only difference (comment or
                                // whitespace, per the M2 engine) is a match
                                // (u4e `rb-comment-only-iu` -> `same`; u4f
                                // `f-iu-rb-ws` -> `same`, `f-iu-rb-real` ->
                                // `diff`). Only the rules-based comparison sees
                                // the difference at that granularity.
                                //
                                // `ignore-unimportant` ALONE is a pure
                                // modifier: it enables no content comparison,
                                // so the row falls back to the quick tests
                                // (u4h `iu-alone-real-diff` reports `same` for
                                // byte-different contents, `iu-alone-size-diff`
                                // and `iu-alone-timestamp` likewise report
                                // `same` under the DEFAULT pair).
                                let folded = *criterion == ContentCriteria::RulesBased
                                    && self.criteria.ignore_unimportant
                                    && self.rules_based_only_unimportant(l, r)?;
                                if !folded {
                                    non_timestamp_differs = true;
                                }
                            }
                        }
                    }
                }

                // Attribute criteria, when the command named a letter set.
                // Compared per attribute (see `Attributes::compare_selected`).
                // The A-3 gate observed the live Oracle IGNORING the attribute
                // comparison when a content criterion is present (FINDINGS F6:
                // `criteria attrib:h CRC` judged a hidden-bit difference
                // `same`), so content replaces the attribute check. Whether
                // size/timestamp also yield to a content criterion is
                // unobserved (EVIDENCE.md U-M3-13) and stays combined here.
                let content_read = self
                    .criteria
                    .content
                    .iter()
                    .any(|c| c.requires_content_read());
                if !self.criteria.attributes.is_empty() && !content_read {
                    match l
                        .metadata
                        .attributes
                        .compare_selected(&r.metadata.attributes, self.criteria.attributes)
                    {
                        Some(true) => {}
                        Some(false) => non_timestamp_differs = true,
                        // Unknown on at least one side: explicit unknown, so a
                        // platform without DOS attributes cannot silently pass.
                        None => return Ok(Status::Unknown),
                    }
                }

                // A version difference outranks EVERY other criterion: the
                // live Oracle reports `ltnewer`/`rtnewer` for a versioned file
                // paired with a truncated one even under `version size`, where
                // the sizes also differ (gate serial-06 `crit-version-size`,
                // `one_sided.dll`), and it outranks the timestamp too (u4j
                // `v-differs` with frozen mtimes). So this check precedes the
                // `diff` return.
                if let Some(side) = version_newer {
                    return Ok(match side {
                        Side::Left => Status::LeftNewer,
                        Side::Right => Status::RightNewer,
                    });
                }
                if non_timestamp_differs {
                    return Ok(Status::Diff);
                }
                match timestamp_differs {
                    None => Ok(Status::Same),
                    Some(false) => Ok(Status::Same),
                    Some(true) => {
                        // Only the timestamp differs: the observed vocabulary has
                        // dedicated tokens for this.
                        let (a, b) = (l.metadata.modified, r.metadata.modified);
                        match (a, b) {
                            (Some(a), Some(b)) => {
                                let (lo, ro) = self.criteria.timezone.offsets_seconds();
                                if shift(a, lo) > shift(b, ro) {
                                    Ok(Status::LeftNewer)
                                } else {
                                    Ok(Status::RightNewer)
                                }
                            }
                            _ => Ok(Status::Unknown),
                        }
                    }
                }
            }
        }
    }

    fn content_differs(&self, left: &Entry, right: &Entry) -> Result<bool, DirError> {
        if !self.options.allow_content_read {
            return Err(DirError::ContentReadNotAllowed {
                name: left.name.clone(),
            });
        }
        if let (Some(a), Some(b)) = (left.metadata.size, right.metadata.size) {
            if a != b {
                // A size difference settles it without reading anything, and the
                // report would say `diff` either way.
                return Ok(true);
            }
        }
        let a = self.left.read_file(&left.path).map_err(|e| DirError::Vfs { source: e })?;
        let b = self.right.read_file(&right.path).map_err(|e| DirError::Vfs { source: e })?;
        Ok(a != b)
    }

    /// Order two entries by their PE FileVersion (the `version` criterion).
    ///
    /// Only regular files carry a version resource. The observed rule
    /// (u4c/u4f): a side with no readable version is OLDER than a side with
    /// one; two sides with no version are equal; two versions compare as four
    /// 16-bit words. The size shortcut is deliberately NOT taken: a version
    /// difference outweighs a size difference (u4b
    /// `ver-real-differs-size-absorbs` still reports the version direction).
    ///
    /// The name gate comes first: measured in U9 (`probes/U9-FINDINGS.md`), BC
    /// reads the version resource **only** for a specific set of extensions, and
    /// returns `same` for everything else *even when the file is a real PE*.
    /// A `.cpl` (a genuine PE) and a `.txt` carrying real PE bytes are both
    /// ignored, while the obsolete `.vxd`/`.386` driver formats are compared —
    /// so this is a specific name list, not a content sniff and not "every PE
    /// type". The gate is a name test and the PE resource is only the *value*
    /// source; a compared name whose content is not a PE still reads `ltnewer`
    /// when the other side has a version (u9c `textonly.exe`).
    fn version_order(&self, left: &Entry, right: &Entry) -> Result<VersionOrder, DirError> {
        if left.metadata.kind != reacmp_vfs::EntryKind::File
            || right.metadata.kind != reacmp_vfs::EntryKind::File
        {
            // Directories (and other non-files) have no version resource on
            // either side, so they compare equal (u4c reports no directory
            // difference for `criteria version`).
            return Ok(VersionOrder::Equal);
        }
        if !reacmp_vfs::pe::version_applies_to(&left.name)
            || !reacmp_vfs::pe::version_applies_to(&right.name)
        {
            // Out of the mask: BC contributes no version difference at all, so
            // the rows fall through as equal (u9 `notes.txt`, `setup.msi`, `noext`).
            return Ok(VersionOrder::Equal);
        }
        if !self.options.allow_content_read {
            return Err(DirError::ContentReadNotAllowed {
                name: left.name.clone(),
            });
        }
        let a = self.left.read_file(&left.path).map_err(|e| DirError::Vfs { source: e })?;
        let b = self.right.read_file(&right.path).map_err(|e| DirError::Vfs { source: e })?;
        let va = reacmp_vfs::pe::file_version(&a);
        let vb = reacmp_vfs::pe::file_version(&b);
        Ok(match (va, vb) {
            (None, None) => VersionOrder::Equal,
            (Some(_), None) => VersionOrder::LeftNewer,
            (None, Some(_)) => VersionOrder::RightNewer,
            (Some(x), Some(y)) if x == y => VersionOrder::Equal,
            (Some(x), Some(y)) if x > y => VersionOrder::LeftNewer,
            (Some(_), Some(_)) => VersionOrder::RightNewer,
        })
    }

    /// True when the two files' `rules-based` comparison differs ONLY in
    /// unimportant ways (the condition `ignore-unimportant` folds).
    ///
    /// Delegates to the M2 importance engine (`reacmp_core::importance`), which
    /// is the same per-element rule the text comparison uses, so the folder and
    /// text paths can never disagree about what "unimportant" means. A pair
    /// whose formats are unknown to the engine compares as plain text, which is
    /// what the M2 probes measured for unknown extensions (u2 `foo-*`).
    fn rules_based_only_unimportant(&self, left: &Entry, right: &Entry) -> Result<bool, DirError> {
        if !self.options.allow_content_read {
            return Err(DirError::ContentReadNotAllowed {
                name: left.name.clone(),
            });
        }
        let a = self.left.read_file(&left.path).map_err(|e| DirError::Vfs { source: e })?;
        let b = self.right.read_file(&right.path).map_err(|e| DirError::Vfs { source: e })?;
        Ok(reacmp_core::folder_rules_based_ignoring_unimportant(&a, &b, &left.name))
    }
}

/// Which side carries the higher version, per [`Compare::version_order`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum VersionOrder {
    Equal,
    LeftNewer,
    RightNewer,
}

/// Apply a timezone offset to a timestamp.
fn shift(t: Timestamp, seconds: i64) -> Timestamp {
    Timestamp::from_unix_millis(t.unix_millis().saturating_add(seconds.saturating_mul(1000)))
}

/// A directory's status is an aggregate of its children (O: help text), never a
/// comparison of the directories' own timestamps.
///
/// `ltonly`/`rtonly` win when one side is missing, because the directory itself
/// is then an orphan regardless of what the existing side contains.
fn directory_status(
    left: &Option<Entry>,
    right: &Option<Entry>,
    children: &[TreeNode],
) -> Status {
    match (left.is_some(), right.is_some()) {
        (true, false) => return Status::LeftOnly,
        (false, true) => return Status::RightOnly,
        (false, false) => return Status::Unknown,
        (true, true) => {}
    }
    let mut any_unknown = false;
    for child in children {
        match child.status {
            Status::Unknown => any_unknown = true,
            Status::Diff
            | Status::LeftOnly
            | Status::RightOnly
            | Status::LeftNewer
            | Status::RightNewer => return Status::Diff,
            Status::Same => {}
        }
    }
    if any_unknown {
        // A directory containing an undecidable child must not be reported as
        // `same`; `unknown` is the honest aggregate.
        Status::Unknown
    } else {
        Status::Same
    }
}

/// Order the entries the way the report does: directories first, then files,
/// each group name-sorted ordinally.
/// Report-row name order, as the Oracle renders it.
///
/// Three gate observations pin this comparator (`A3-folder-gate-serial-01/02`):
///
/// 1. `tol-60sec` orders `d0, d30, d60, d3600, d7200` — digit runs compare
///    numerically;
/// 2. `struct-names-xml-escaping` orders `ünïcødé_中文.txt` before
///    `UPPER.TXT` — a linguistic, case-insensitive collation (ordinal
///    lowercasing would put `U` (0x55) before `ü` (0xFC), and measured
///    `CompareStringW(NORM_IGNORECASE)` agrees with the Oracle here);
/// 3. digit ordering is NOT produced by `CompareStringW` at all — measured
///    via ctypes, passing `SORT_DIGITSASNUMBERS` (0x10) to `CompareStringW`
///    makes it return 0 (error): the flag belongs to `CompareStringEx`.
///
/// The comparator is therefore a hybrid: while both strings are positioned at
/// ASCII digit runs, the runs compare as numbers; at the first character
/// position that is not a shared character, the REMAINders compare through
/// `CompareStringW(NORM_IGNORECASE)`. Every observed order follows; a pure
/// `StrCmpLogicalW` or a pure `CompareStringW` satisfies only part of them.
#[cfg(windows)]
mod name_order {
    use std::cmp::Ordering;
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    const LOCALE_USER_DEFAULT: u32 = 0x0400;
    const NORM_IGNORECASE: u32 = 0x0000_0001;
    const CSTR_LESS_THAN: i32 = 1;
    const CSTR_GREATER_THAN: i32 = 3;

    #[link(name = "kernel32")]
    extern "system" {
        fn CompareStringW(
            locale: u32,
            flags: u32,
            s1: *const u16,
            c1: i32,
            s2: *const u16,
            c2: i32,
        ) -> i32;
    }

    /// Linguistic, case-insensitive comparison of two UTF-16 slices, exactly
    /// what `AnsiCompareText` (the Delphi runtime's comparer) wraps. Falls
    /// back to ordinal comparison of the code units if the API errors.
    fn win_compare(a: &[u16], b: &[u16]) -> Ordering {
        let r = unsafe {
            CompareStringW(
                LOCALE_USER_DEFAULT,
                NORM_IGNORECASE,
                a.as_ptr(),
                a.len() as i32,
                b.as_ptr(),
                b.len() as i32,
            )
        };
        match r {
            CSTR_LESS_THAN => Ordering::Less,
            CSTR_GREATER_THAN => Ordering::Greater,
            _ if r == 0 => a.cmp(b),
            _ => Ordering::Equal,
        }
    }

    /// ASCII `0..=9` for a UTF-16 code unit (`u16` has no `is_ascii_digit`).
    fn is_digit(c: u16) -> bool {
        (0x30..=0x39).contains(&c)
    }

    /// Parse the ASCII digit run starting at `i`; returns (value, end index).
    fn digit_run(s: &[u16], i: usize) -> (u64, usize) {
        let mut v: u64 = 0;
        let mut j = i;
        while j < s.len() && is_digit(s[j]) {
            v = v
                .saturating_mul(10)
                .saturating_add(u64::from(s[j] - u16::from(b'0')));
            j += 1;
        }
        (v, j)
    }

    pub fn compare(a: &str, b: &str) -> Ordering {
        let ab: Vec<u16> = OsStr::new(a).encode_wide().collect();
        let bb: Vec<u16> = OsStr::new(b).encode_wide().collect();
        let (mut i, mut j) = (0usize, 0usize);
        while i < ab.len() && j < bb.len() {
            let da = is_digit(ab[i]);
            let db = is_digit(bb[j]);
            if da && db {
                // Both positioned at a digit: the runs compare as numbers
                // (`d60` < `d3600` — the order a linguistic comparison gets
                // wrong). Numerically equal runs (`01` vs `1`) are unobserved
                // in the corpus; continue after the runs rather than guessing
                // which padding orders first.
                let (va, na) = digit_run(&ab, i);
                let (vb, nb) = digit_run(&bb, j);
                if va != vb {
                    return va.cmp(&vb);
                }
                i = na;
                j = nb;
            } else if da || db {
                // A digit against a non-digit at the same position: linguistic.
                return win_compare(&ab[i..], &bb[j..]);
            } else if ab[i] == bb[j] {
                // Shared non-digit: the linguistic comparison would tie on it
                // anyway; advancing keeps reaching the first real difference.
                i += 1;
                j += 1;
            } else {
                return win_compare(&ab[i..], &bb[j..]);
            }
        }
        // One side is a prefix of the other: the shorter orders first.
        (ab.len() - i).cmp(&(bb.len() - j))
    }
}

/// Non-Windows fallback: case-insensitive ordinal with numeric digit runs.
/// The measured order is the Windows collation above; this fallback is a
/// best-effort approximation for portability, not a parity claim.
#[cfg(not(windows))]
mod name_order {
    use std::cmp::Ordering;

    pub fn compare(a: &str, b: &str) -> Ordering {
        let mut ai = a.chars().peekable();
        let mut bi = b.chars().peekable();
        loop {
            match (ai.peek().copied(), bi.peek().copied()) {
                (None, None) => return Ordering::Equal,
                (None, Some(_)) => return Ordering::Less,
                (Some(_), None) => return Ordering::Greater,
                (Some(ca), Some(cb)) => {
                    if ca.is_ascii_digit() && cb.is_ascii_digit() {
                        let na = digits(&mut ai);
                        let nb = digits(&mut bi);
                        if na != nb {
                            return na.cmp(&nb);
                        }
                    } else {
                        let la = ca.to_lowercase().next().unwrap_or(ca);
                        let lb = cb.to_lowercase().next().unwrap_or(cb);
                        if la != lb {
                            return la.cmp(&lb);
                        }
                        ai.next();
                        bi.next();
                    }
                }
            }
        }
    }

    fn digits(it: &mut std::iter::Peekable<std::str::Chars<'_>>) -> u64 {
        let mut v: u64 = 0;
        while let Some(c) = it.peek().copied() {
            if !c.is_ascii_digit() {
                break;
            }
            v = v.saturating_mul(10).saturating_add((c as u64) - '0' as u64);
            it.next();
        }
        v
    }
}

#[cfg(all(test, windows))]
mod name_order_tests {
    use super::name_order::compare as cmp;
    use std::cmp::Ordering::*;

    #[test]
    fn matches_the_gate_observed_orders() {
        // Digit runs compare numerically (gate tol-* trees).
        assert_eq!(cmp("d0.txt", "d30.txt"), Less);
        assert_eq!(cmp("d60.txt", "d3600.txt"), Less);
        assert_eq!(cmp("d3600.txt", "d7200.txt"), Less);
        // Linguistic, case-insensitive; diacritics are secondary weights that
        // only break ties at the same position (gate names tree).
        assert_eq!(cmp("ünïcødé_中文.txt", "UPPER.TXT"), Less);
        assert_eq!(cmp("amp&name&2.txt", "amp&name.txt"), Less);
        assert_eq!(cmp("  leading_spaces.txt", "amp&name.txt"), Less);
        assert_eq!(cmp("trailing.dot", "ünïcødé_中文.txt"), Less);
        assert_eq!(cmp("no_extension", "plus+semi;eq=.txt"), Less);
        // Prefix orders first.
        assert_eq!(cmp("abc", "abcd"), Less);
    }
}

fn sort_entries(entries: &mut [Entry]) {
    entries.sort_by(|a, b| {
        let a_dir = matches!(a.metadata.kind, EntryKind::Directory);
        let b_dir = matches!(b.metadata.kind, EntryKind::Directory);
        b_dir.cmp(&a_dir)
            .then_with(|| name_order::compare(&a.name, &b.name))
    });
}

/// Align two listings by name.
///
/// Returns rows in report order: the union of both sides' names, ordered by the
/// same rule as a single listing (directories first, then files, each sorted).
/// An entry present on only one side yields `(name, Some, None)` or the mirror.
pub fn align_entries(
    mut left: Vec<Entry>,
    mut right: Vec<Entry>,
    case_insensitive: bool,
) -> Vec<(String, Option<Entry>, Option<Entry>)> {
    sort_entries(&mut left);
    sort_entries(&mut right);

    let key = |s: &str| {
        if case_insensitive {
            s.to_lowercase()
        } else {
            s.to_string()
        }
    };

    // Build the union of keys, preserving "directories first" ordering from the
    // sorted inputs. A name present on both sides uses the left spelling, which is
    // what a paired report row shows on the left.
    let mut order: Vec<String> = Vec::new();
    let mut seen: std::collections::HashSet<String> = std::collections::HashSet::new();
    let mut dir_flags: std::collections::HashMap<String, bool> =
        std::collections::HashMap::new();

    for e in left.iter().chain(right.iter()) {
        let k = key(&e.name);
        let is_dir = matches!(e.metadata.kind, EntryKind::Directory);
        let flag = dir_flags.entry(k.clone()).or_insert(is_dir);
        *flag = *flag || is_dir;
        if seen.insert(k.clone()) {
            order.push(k);
        }
    }

    order.sort_by(|a, b| {
        let ad = dir_flags.get(a).copied().unwrap_or(false);
        let bd = dir_flags.get(b).copied().unwrap_or(false);
        bd.cmp(&ad).then_with(|| a.cmp(b))
    });

    let mut left_by_key: std::collections::HashMap<String, Entry> =
        left.into_iter().map(|e| (key(&e.name), e)).collect();
    let mut right_by_key: std::collections::HashMap<String, Entry> =
        right.into_iter().map(|e| (key(&e.name), e)).collect();

    let mut rows = Vec::with_capacity(order.len());
    for k in order {
        let l = left_by_key.remove(&k);
        let r = right_by_key.remove(&k);
        let name = l
            .as_ref()
            .or(r.as_ref())
            .map(|e| e.name.clone())
            .unwrap_or_else(|| k.clone());
        rows.push((name, l, r));
    }
    rows
}

/// Select the `attrib:` letter set for a criteria, if any.
pub fn criteria_attribute_set(criteria: &Criteria) -> AttributeSet {
    criteria.attributes
}

/// The timezone rule for a criteria, for reporting.
pub fn criteria_timezone(criteria: &Criteria) -> TimezoneRule {
    criteria.timezone
}

/// Re-export for callers that need the per-side metadata of a node.
pub fn node_metadata<'a>(node: &'a TreeNode, side: Side) -> Option<&'a Metadata> {
    node.metadata_for(side)
}

/// The raw bytes of a file on one side, used by the fixture runner to prove that
/// a `same` verdict really was a quick test and not a content read.
pub fn read_side_bytes(
    fs: &dyn FileSystem,
    path: &VfsPath,
) -> VfsResult<Vec<u8>> {
    fs.read_file(path)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn file_entry(name: &str, parent: &str, size: u64, mtime: i64) -> Entry {
        Entry::new(
            name,
            VfsPath::new(format!("{parent}{name}")),
            Metadata::file(size).with_modified(Timestamp::from_unix_seconds(mtime)),
        )
    }

    fn dir_entry(name: &str, parent: &str, mtime: i64) -> Entry {
        Entry::new(
            name,
            VfsPath::new(format!("{parent}{name}")),
            Metadata::directory().with_modified(Timestamp::from_unix_seconds(mtime)),
        )
    }

    #[test]
    fn alignment_pairs_by_name_and_orders_dirs_first() {
        let left = vec![
            file_entry("b.txt", "L\\", 1, 100),
            dir_entry("sub", "L\\", 100),
            file_entry("a.txt", "L\\", 1, 100),
        ];
        let right = vec![
            file_entry("a.txt", "R\\", 1, 100),
            file_entry("only-right.txt", "R\\", 1, 100),
        ];
        let rows = align_entries(left, right, false);
        let names: Vec<&str> = rows.iter().map(|(n, _, _)| n.as_str()).collect();
        assert_eq!(names, vec!["sub", "a.txt", "b.txt", "only-right.txt"]);

        assert!(rows[0].1.is_some() && rows[0].2.is_none(), "sub is left-only");
        assert!(rows[1].1.is_some() && rows[1].2.is_some(), "a.txt pairs");
        assert!(rows[2].1.is_some() && rows[2].2.is_none(), "b.txt is left-only");
        assert!(rows[3].1.is_none() && rows[3].2.is_some(), "only-right is right-only");
    }

    #[test]
    fn alignment_uses_left_spelling_for_a_paired_row() {
        let left = vec![file_entry("Name.TXT", "L\\", 1, 100)];
        let right = vec![file_entry("name.txt", "R\\", 1, 100)];
        let rows = align_entries(left, right, true);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].0, "Name.TXT");
    }

    #[test]
    fn directory_status_aggregates_children_not_own_timestamp() {
        // Two directories with identical child content must be `same` even
        // though their own timestamps differ (O: help text, and the observed
        // report shows a directory's own mtime separately).
        let children = vec![TreeNode {
            name: "inner.txt".to_string(),
            relative_path: "sub/inner.txt".to_string(),
            left: None,
            right: None,
            status: Status::Same,
            children: vec![],
            hidden: false,
            expanded: true,
            notes: vec![],
        }];
        let l = Some(dir_entry("sub", "L\\", 10));
        let r = Some(dir_entry("sub", "R\\", 99999));
        assert_eq!(directory_status(&l, &r, &children), Status::Same);
    }

    #[test]
    fn directory_status_is_orphan_when_one_side_missing() {
        let l = Some(dir_entry("sub", "L\\", 10));
        assert_eq!(directory_status(&l, &None, &[]), Status::LeftOnly);
        let r = Some(dir_entry("sub", "R\\", 10));
        assert_eq!(directory_status(&None, &r, &[]), Status::RightOnly);
    }

    #[test]
    fn directory_status_propagates_diff_and_unknown() {
        let mk = |status| {
            vec![TreeNode {
                name: "x".to_string(),
                relative_path: "x".to_string(),
                left: None,
                right: None,
                status,
                children: vec![],
                hidden: false,
                expanded: true,
                notes: vec![],
            }]
        };
        let both = (Some(dir_entry("d", "L\\", 1)), Some(dir_entry("d", "R\\", 1)));
        assert_eq!(directory_status(&both.0, &both.1, &mk(Status::Diff)), Status::Diff);
        assert_eq!(
            directory_status(&both.0, &both.1, &mk(Status::LeftNewer)),
            Status::Diff
        );
        assert_eq!(
            directory_status(&both.0, &both.1, &mk(Status::Unknown)),
            Status::Unknown
        );
        // An empty directory pairs as `same`.
        assert_eq!(directory_status(&both.0, &both.1, &[]), Status::Same);
    }

    #[test]
    fn reported_size_of_a_directory_sums_its_subtree_files() {
        let leaf = TreeNode {
            name: "a".to_string(),
            relative_path: "d/a".to_string(),
            left: Some(file_entry("a", "L\\", 7, 1)),
            right: Some(file_entry("a", "R\\", 7, 1)),
            status: Status::Same,
            children: vec![],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        let nested = TreeNode {
            name: "n".to_string(),
            relative_path: "d/n".to_string(),
            left: Some(dir_entry("n", "L\\", 1)),
            right: Some(dir_entry("n", "R\\", 1)),
            status: Status::Same,
            children: vec![TreeNode {
                name: "b".to_string(),
                relative_path: "d/n/b".to_string(),
                left: Some(file_entry("b", "L\\", 5, 1)),
                right: Some(file_entry("b", "R\\", 5, 1)),
                status: Status::Same,
                children: vec![],
                hidden: false,
                expanded: true,
                notes: vec![],
            }],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        let dir = TreeNode {
            name: "d".to_string(),
            relative_path: "d".to_string(),
            left: Some(dir_entry("d", "L\\", 1)),
            right: Some(dir_entry("d", "R\\", 1)),
            status: Status::Same,
            children: vec![leaf, nested],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        assert_eq!(dir.reported_size(Side::Left), Some(12));
        // An empty directory reports zero, matching the observed
        // `<name>emptydir</name><size>0</size>`.
        let empty = TreeNode {
            children: vec![],
            left: Some(dir_entry("emptydir", "R\\", 1)),
            right: None,
            status: Status::RightOnly,
            name: "emptydir".to_string(),
            relative_path: "emptydir".to_string(),
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        assert_eq!(empty.reported_size(Side::Left), Some(0));
    }

    #[test]
    fn reported_size_of_a_file_is_its_own_size() {
        let f = TreeNode {
            name: "a.txt".to_string(),
            relative_path: "a.txt".to_string(),
            left: Some(file_entry("a.txt", "L\\", 6, 1)),
            right: Some(file_entry("a.txt", "R\\", 6, 1)),
            status: Status::Same,
            children: vec![],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        assert_eq!(f.reported_size(Side::Left), Some(6));
    }
}

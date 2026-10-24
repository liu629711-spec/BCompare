//! `reacmp-dir` — read-only folder comparison.
//!
//! Implements M3.2 – M3.5 of `product/docs/04-milestones.md` on top of the
//! `reacmp-vfs` read-only `FileSystem` seam:
//!
//! | Module | Milestone | Contents |
//! |---|---|---|
//! | [`criteria`] | M3.3 | the observed criteria model |
//! | [`tree`] | M3.2 | recursion, alignment, status computation |
//! | [`status`] | M3.2 | the six observed report status tokens |
//! | [`report`] | M3.5 | side-by-side, summary and xml layouts |
//! | [`expand`] | M4.2 | the `expand` policy and its `<size>` rule |
//! | [`filter`] | M4.2 | the `filter` mask matcher behind `<filters>` |
//! | [`testing`] | — | an in-memory `FileSystem` for hermetic tests |
//!
//! # How to compare two folders
//!
//! ```no_run
//! use reacmp_dir::{compare_folders, report, Criteria, CompareOptions, Layout, ReportOptions};
//! use reacmp_vfs::LocalFs;
//!
//! # fn main() -> Result<(), Box<dyn std::error::Error>> {
//! let left = LocalFs::open(r"D:\Rea\verify\dir\trees\L")?;
//! let right = LocalFs::open(r"D:\Rea\verify\dir\trees\R")?;
//! let criteria = Criteria::observed_default();
//! let comparison = compare_folders(&left, &right, &criteria, CompareOptions::default())?;
//! let xml = report::render(&comparison, Layout::Xml, &ReportOptions::default())?;
//! println!("{xml}");
//! # Ok(())
//! # }
//! ```
//!
//! # Scope, stated up front
//!
//! Read-only. No copy, move, sync, delete or attribute change exists in this
//! crate, and the engine accepts only [`reacmp_vfs::FileSystem`], so it cannot
//! reach a writable backend even by accident (ADR-3).
//!
//! `criteria rules-based` is evaluated as byte equality; the per-format
//! importance rules it implies are M2 work and are **not** implemented. Every
//! such comparison carries
//! [`status::ComparisonNote::RulesBasedTextRulesNotImplemented`] so the
//! limitation travels with the output instead of living only in a document.
//!
//! `criteria content` and `criteria binary-content` are rejected with
//! [`criteria::CriteriaError::InvalidCriteria`] and exit code 106, matching the
//! observed Oracle behaviour — they are not accepted and ignored.
//!
//! `criteria version|owner|group|permissions|ignore-unimportant` are refused with
//! [`criteria::CriteriaError::NotProbed`]: each is a real BC feature that this
//! workspace has not probed, and guessing would violate the evidence discipline
//! in `product/docs/02-version-and-evidence.md`.

#![warn(missing_debug_implementations)]

pub mod criteria;
pub mod error;
pub mod expand;
pub mod filter;
pub mod report;
pub mod status;
pub mod tree;

#[cfg(any(test, feature = "testing"))]
pub mod testing;
pub use criteria::{ContentCriteria, Criteria, CriteriaError, Side, TimestampRule, TimezoneRule};
pub use error::DirError;
pub use expand::ExpandPolicy;
pub use filter::Filter;
pub use report::{render, Layout, ReportOptions};
pub use status::{ComparisonNote, Status};
pub use tree::{
    align_entries, compare_folders, compare_folders_filtered, CompareOptions, FolderComparison,
    TreeNode,
};

/// Crate version, recorded in reports so a run can name the engine that made it.
pub const DIR_VERSION: &str = env!("CARGO_PKG_VERSION");

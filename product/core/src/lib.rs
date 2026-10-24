//! ReaCompare text-comparison core (milestone M1).
//!
//! Layering (see `product/docs/03-architecture-options.md` §1 / §6 and §8):
//!
//! ```text
//! CLI (product/cli)  ->  compare.rs  (load + compare + render)
//!                          |
//!   lines.rs (M1.2)  -----+----- align.rs (M1.3)
//!   encoding / line split       Myers linear-space matching + block pairing
//!                          |
//!   importance.rs  -------+  xml.rs (M1.5) / layouts.rs (M1.4)
//!   SPEC-LEVEL approx.        reports
//! ```
//!
//! # Evidence discipline
//!
//! Every behavioural rule implemented here is traced to an observation in the
//! read-only corpora (`verify/golden`, `verify/layouts`, `verify/probe-patch`,
//! `verify/oracle`) or to the structural reverse-engineering evidence in
//! `report-algorithm.md` / `extracted/pseudocode/`. Rules that are *not*
//! observed are marked in the code as unverified and are never presented as
//! Beyond Compare behaviour. See `README.md` in this crate for the full ledger.

pub mod align;
pub mod codepage;
pub mod compare;
pub mod hex;
pub mod importance;
pub mod layouts;
pub mod lines;
pub mod merge;
pub mod myers;
pub mod options;
pub mod stamp;
pub mod table;
pub mod xml;

pub use align::{Block, Group, Status};
pub use codepage::{declared_code_page, lookup_declared_name, nul_parity_utf16};
pub use compare::{
    classify_pair, compare_bytes, compare_bytes_at, compare_files, CompareError, Comparison,
    FileInfo,
};
pub use importance::{folder_rules_based_ignoring_unimportant, Grammar, Verdict};
pub use lines::{decode, split_text, Decoded, Encoding};
pub use merge::{merge3, read_lines, MergeResult, MergeSection, SectionKind};
pub use myers::{diff_matches, diff_matches_cancellable, map_ids, DiffError, MAX_DIAGONAL};
pub use options::{DisplayMode, ReportOptions, UnknownOption};
pub use hex::{
    align_bytes, align_slots, render_hex_report, slot_counts, hex_counts, ByteSlot, HexError,
    HexLayout, HexRow, HEX_LAYOUT_NAMES,
};
pub use stamp::Stamp;
pub use table::{align_rows, render_report, split_records, RowStatus, TableError, TableGroup, TableLayout};
pub use xml::{escape_text, Layout, XmlReport};

/// Crate version, reported by `reacmp --version`.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

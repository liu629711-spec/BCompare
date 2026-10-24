//! `reacmp-reg` — Registry Compare (.reg) parsing and report model.
//!
//! Implements the measured Registry Compare channel (M10/M11, docs/17).
//! Hermetic like its siblings: zero third-party dependencies, `cargo test`
//! works offline.
//!
//! | Module | Contents |
//! |---|---|
//! | [`parse`]  | .reg text model: encoding, line grammar, errors, basekey rule |
//! | [`values`] | value types, hex/dword decoding, display strings (measured vocabulary) |
//!
//! The measured model (`docs/17`) drives everything. Headline facts, each
//! pinned to a probe cell in `product/verify/runs/m101*`:
//! * a valid file needs the v5/REGEDIT4 header AND at least one key, else the
//!   side reports `Unsupported Type` with NO base-key suffix (G3/N4/N9/N10);
//! * a bad line STOPS parsing; items before it survive (C10 vs I5);
//! * delete lines `[-…]` and duplicate keys/values and `"name"=-` are SKIPPED
//!   with the file-level note `Deletes/Duplicates Skipped` (C8/G13/F7/N8/S1);
//! * continuation is NEVER joined (archived m101g T1 supersedes the earlier
//!   hypothesis): an indented data line cannot start a statement -> parse
//!   error at its first non-space column, the value keeps the first line's
//!   bytes (C6 and T1 share this rule);
//! * the basekey suffix = common path prefix of the keys that HAVE at least
//!   one value; no valued keys -> common prefix of all keys (rule pinned
//!   across G2/J1/F12/M1–M5/T9/F16; see [`parse::RegFile::basekey`]).

#![warn(missing_debug_implementations)]

pub mod collation;
pub mod engine;
pub mod parse;
pub mod report;
pub mod values;

pub use engine::{compare_sbs, Counts, Locale, SbsResult, SbsRow};
pub use parse::{parse_reg, KeyNode, ParseNote, RegError, RegFile, ValueItem};
pub use report::{
    count_lines, error_text_zh, mode_text, render_registry_report, render_registry_shell,
    Display, Layout, ReportFrame, SideError,
};
pub use values::Value;

//! ReaCompare version comparison (function 8, the `version-report` half).
//!
//! Zero dependencies, offline-testable -- the same hermetic rule as its
//! siblings. Decodes the PE version resource (or reports why a file has none),
//! builds the measured two-column field table, and renders the two layouts.
//!
//! Everything here is measured, never assumed (docs/18):
//! * the refuse surface: m112 V9/V10/V11/V12/V17/V18/V19/V13b, V25;
//! * the frame and the field model: m112 V1..V8, m112b W1..W12;
//! * the geometry: the same locale-parameterized floors the registry channel
//!   measured (docs/17 §6) -- the column floors are the header LABEL widths.

pub mod collation;
pub mod engine;
pub mod parse;
pub mod report;
pub mod values;

pub use engine::Locale;
pub use parse::{read_version, VerError, VersionInfo};
pub use report::{render_version_report, render_version_shell, Display, Layout, ReportFrame};

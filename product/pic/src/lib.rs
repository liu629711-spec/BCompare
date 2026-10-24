//! `reacmp-pic` — picture comparison for ReaCompare.
//!
//! Implements the measured Picture Compare report channel (M9, `docs/16`).
//! Like its siblings this crate is hermetic: zero third-party dependencies, so
//! `cargo test` works offline. That is why PNG/BMP decoding is implemented here
//! rather than pulled from a crate (a registry dependency would make the offline
//! gate depend on a cache existing).
//!
//! | Module | Contents |
//! |---|---|
//! | [`deflate`] | minimal DEFLATE inflate (RFC 1951), verified against CPython zlib fixtures |
//! | [`png`]     | 8-bit non-interlaced PNG decode (gray/RGB/RGBA), all five scanline filters |
//! | [`bmp`]     | 24-bit uncompressed BMP decode |
//! | [`decode`]  | format sniffing: PNG or BMP, otherwise "not supported" |
//! | [`compare`] | the pixel categories (same / important / unimportant / left-only / right-only) with the measured 26-boundary rule |
//!
//! The measured model (`docs/16`) drives everything: a differing pixel is
//! *important* when some RGB channel differs by **26 or more** (≤25 unimportant —
//! the boundary is measured between 25 and 26 and the constant is recorded; its
//! derivation is a residual unknown); the alpha channel is ignored; size surplus
//! pixels become the larger side's "own"; an un-decodable file yields an error
//! line, not a refusal.

#![warn(missing_debug_implementations)]

pub mod bmp;
pub mod compare;
pub mod decode;
pub mod deflate;
pub mod png;
pub mod report;

pub use compare::{compare_rasters, CompareOptions, PictureCounts};
pub use decode::{decode_image, ImageError};
pub use png::Raster;
pub use report::{render_picture_report, render_picture_shell, PictureLayout, SideImage};

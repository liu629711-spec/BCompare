//! `reacmp-vfs` — the read-only filesystem seam for ReaCompare folder comparison.
//!
//! Implements M3.1 of `product/docs/04-milestones.md`: a read-only `FileSystem`
//! trait plus a `LocalFs` implementation, shaped per
//! `product/docs/03-architecture-options.md` section 2 and ADR-2/3/4.
//!
//! ```no_run
//! use reacmp_vfs::{FileSystem, ListOptions, LocalFs, VfsPath};
//!
//! # fn main() -> Result<(), reacmp_vfs::VfsError> {
//! let fs = LocalFs::open(r"D:\Rea\verify\dir\trees\L")?;
//! for entry in fs.read_dir(fs.root(), ListOptions::default())? {
//!     println!("{} {:?}", entry.name, entry.metadata.size);
//! }
//! # Ok(())
//! # }
//! ```
//!
//! # The seam, in one paragraph
//!
//! The comparison engine sees a [`FileSystem`], never `std::fs`. That is ADR-2:
//! an archive backend (zip/7z/tar) or a remote backend can be added later without
//! touching the comparison engine, because the engine only asks for a listing,
//! metadata, and bytes. Nothing it can call writes anything (ADR-3), and every
//! path it handles is an opaque string (ADR-4) so a `ftp://host/dir` or a
//! `C:\a.zip\sub` is representable.
//!
//! # What is deliberately absent
//!
//! * **No archive backend.** Archive VFS is `product/docs/02` U7 and
//!   `04-milestones.md` P7; the trait is shaped for it, but implementing it
//!   without an Oracle-probed spec would be guessing.
//! * **No remote backend.** ADR-9 excludes remote resources from the first year.
//! * **No writable implementation.** [`WritableFileSystem`] is declared so the
//!   boundary is in the type system; nothing implements it, and no read-only
//!   entry point can reach it.

#![forbid(unsafe_op_in_unsafe_fn)]
#![warn(missing_debug_implementations)]

pub mod error;
pub mod local;
pub mod path;
pub mod pe;
pub mod time;
pub mod traits;

pub use error::{Side, VfsError, VfsResult};
pub use local::LocalFs;
pub use path::{from_local_path, VfsPath};
pub use time::{
    system_offset_provider, FixedOffset, OffsetProvider, SystemZone, TimeZoneInfo, Timestamp,
    TransitionRule, UtcOffset,
};
pub use traits::{
    AttributeSet, Attributes, Entry, EntryKind, FileSystem, ListOptions, Metadata, SymlinkPolicy,
    WritableFileSystem,
};

/// Crate version, so a report can record which VFS seam produced it.
pub const VFS_VERSION: &str = env!("CARGO_PKG_VERSION");

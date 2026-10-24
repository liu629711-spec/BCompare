//! The read-only filesystem seam.
//!
//! # Why these traits are shaped this way
//!
//! `product/docs/03-architecture-options.md` section 2 (方案 2A, recommended) and
//! section 7 (ADR-2 / ADR-3 / ADR-4) bind the design:
//!
//! * **ADR-2** — folder comparison is built on a `FileSystem` trait, not on
//!   `std::fs`, so an archive backend (zip/7z/tar) or a remote backend can be
//!   added without touching the comparison engine.
//! * **ADR-3** — read-only and writable operations are **separate traits**. The
//!   comparison engine must not be able to write. This is a safety property:
//!   only copy/move/sync need mutation, and those carry the project's highest
//!   risk (`product/docs/01` section 5, `04` M4 "唯一破坏性模块").
//! * **ADR-4** — paths are **opaque strings**, never `std::path::Path`.
//!
//! # Two deliberate departures from the sketch in 03 section 2
//!
//! The audit's sketch used an associated type (`type Entry`) and returned
//! `Box<dyn Read>`. This implementation:
//!
//! 1. returns **owned** entry values ([`Entry`]) rather than an associated type,
//!    so the tree model and the comparison engine can outlive a borrow of the
//!    backend and so two backends can be compared without a unified type
//!    parameter. An associated type would force the engine to be generic over
//!    both sides' backends simultaneously, which makes "compare a local folder
//!    against an archive" awkward — the exact case ADR-2 exists to enable.
//! 2. returns a **byte vector** from [`FileSystem::read_file`] rather than a
//!    `Box<dyn Read>` for the whole-file read used by content criteria
//!    (CRC/binary), and provides [`FileSystem::open_read`] for streaming. The
//!    criteria engine hashes whole files; a streaming API is offered separately
//!    so a future large-file path can avoid buffering, but the comparison never
//!    depends on it.
//!
//! `Metadata`, `EntryKind` and `Attributes` are provider-neutral: they carry
//! exactly what the observed report needs (`<name>`, `<size>`, `<modified>`) plus
//! what the criteria model needs (attributes, symlink targets), and nothing that
//! only a local filesystem could supply.

use crate::error::VfsResult;
use crate::path::VfsPath;
use crate::time::Timestamp;

/// What an entry is. Deliberately small: only kinds the folder comparison can act
/// on distinctly.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum EntryKind {
    File,
    Directory,
    /// A symbolic link or NTFS junction, **not** followed.
    Symlink,
    /// The backend knows the entry exists but cannot classify it.
    ///
    /// Carried explicitly so the comparison can report an explicit unknown
    /// rather than silently treating it as a file or skipping it.
    Unknown,
}

impl EntryKind {
    pub fn as_str(self) -> &'static str {
        match self {
            EntryKind::File => "file",
            EntryKind::Directory => "directory",
            EntryKind::Symlink => "symlink",
            EntryKind::Unknown => "unknown",
        }
    }

    pub fn is_dir(self) -> bool {
        matches!(self, EntryKind::Directory)
    }
}

impl std::fmt::Display for EntryKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// DOS-style attribute set, as named by the `attrib:` criteria
/// (`help/scripting_reference.html`, CRITERIA: "`a` for archive, `s` for system,
/// `h` for hidden and `r` for read-only" — O-level, official documentation).
///
/// Non-Windows backends have no DOS attributes and report all four as `None`
/// (unknown), which is distinguishable from `false` (present-and-clear).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Hash)]
pub struct Attributes {
    pub archive: Option<bool>,
    pub system: Option<bool>,
    pub hidden: Option<bool>,
    pub read_only: Option<bool>,
}

impl Attributes {
    /// All four attributes unknown — the honest value for a backend that has no
    /// DOS attribute concept.
    pub fn unknown() -> Self {
        Attributes::default()
    }

    pub fn is_fully_unknown(&self) -> bool {
        self.archive.is_none()
            && self.system.is_none()
            && self.hidden.is_none()
            && self.read_only.is_none()
    }

    /// Render the subset of `a`,`s`,`h`,`r` (in that order) that is known.
    ///
    /// Order follows `help/scripting_reference.html` CRITERIA
    /// ("[a][s][h][r]") and ATTRIB ("`attrib +sh -a`"). Unknown attributes are
    /// omitted rather than guessed.
    pub fn known_letters(&self) -> String {
        let mut s = String::new();
        if self.read_only == Some(true) {
            s.push('r');
        }
        if self.hidden == Some(true) {
            s.push('h');
        }
        if self.archive == Some(true) {
            s.push('a');
        }
        if self.system == Some(true) {
            s.push('s');
        }
        s
    }

    /// True when every attribute named in `set` is known *and* set.
    ///
    /// Returns `None` when a named attribute is unknown, so the criteria engine
    /// can report an explicit unknown instead of a false "no difference".
    pub fn contains_all(&self, set: AttributeSet) -> Option<bool> {
        let mut result = true;
        for (flag, value) in [
            (AttributeSet::ARCHIVE, self.archive),
            (AttributeSet::SYSTEM, self.system),
            (AttributeSet::HIDDEN, self.hidden),
            (AttributeSet::READ_ONLY, self.read_only),
        ] {
            if set.0 & flag == 0 {
                continue;
            }
            match value {
                Some(true) => {}
                Some(false) => result = false,
                None => return None,
            }
        }
        Some(result)
    }

    /// The value of one named attribute, or `None` when it is unknown.
    pub fn get(&self, flag: u8) -> Option<bool> {
        if flag & AttributeSet::ARCHIVE != 0 {
            self.archive
        } else if flag & AttributeSet::SYSTEM != 0 {
            self.system
        } else if flag & AttributeSet::HIDDEN != 0 {
            self.hidden
        } else if flag & AttributeSet::READ_ONLY != 0 {
            self.read_only
        } else {
            None
        }
    }

    /// Compare **each** attribute named in `set` between two entries.
    ///
    /// Returns `Some(true)` when every named attribute is known on both sides and
    /// equal, `Some(false)` when at least one named attribute is known on both
    /// sides and differs, and `None` when any named attribute is unknown on
    /// either side.
    ///
    /// Comparing `contains_all(set)` on each side instead would be wrong: two
    /// entries that each *fail* to have all of `ashr` — one because it is hidden
    /// and the other because it is not — would compare equal. The documented
    /// criterion is per-attribute ("enables comparisons of the specified DOS file
    /// attributes"), so it is evaluated per attribute.
    pub fn compare_selected(&self, other: &Attributes, set: AttributeSet) -> Option<bool> {
        let mut equal = true;
        for flag in [
            AttributeSet::ARCHIVE,
            AttributeSet::SYSTEM,
            AttributeSet::HIDDEN,
            AttributeSet::READ_ONLY,
        ] {
            if set.0 & flag == 0 {
                continue;
            }
            match (self.get(flag), other.get(flag)) {
                (Some(a), Some(b)) => {
                    if a != b {
                        equal = false;
                    }
                }
                _ => return None,
            }
        }
        Some(equal)
    }
}

/// A set of attribute letters, parsed from an `attrib:` criteria value.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Hash)]
pub struct AttributeSet(pub u8);

impl AttributeSet {
    pub const ARCHIVE: u8 = 1 << 0;
    pub const SYSTEM: u8 = 1 << 1;
    pub const HIDDEN: u8 = 1 << 2;
    pub const READ_ONLY: u8 = 1 << 3;

    pub const EMPTY: AttributeSet = AttributeSet(0);
    pub const ALL: AttributeSet =
        AttributeSet(Self::ARCHIVE | Self::SYSTEM | Self::HIDDEN | Self::READ_ONLY);

    pub fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// Parse a letter set such as `shr` or `+sh-r`.
    ///
    /// `+`/`-` prefixes are accepted and ignored: `criteria attrib:sh` (the
    /// documented "enables comparisons of the specified DOS file attributes"
    /// form) names exactly the letters to compare, so a sign does not change the
    /// set.
    ///
    /// Letters outside the four DOS attributes are ACCEPTED but inert: the
    /// A-3 folder gate observed the live Oracle accepting `criteria attrib:z`
    /// with exit 0 and a full report (`A3-folder-gate-serial-01` FINDINGS F5),
    /// so refusing them would diverge from the Oracle. Only the known letters
    /// reach the comparison; unknown ones are dropped silently because they
    /// name nothing this platform compares.
    pub fn parse(text: &str) -> Result<Self, String> {
        let mut bits = 0u8;
        for ch in text.chars() {
            match ch {
                '+' | '-' => {}
                'a' | 'A' => bits |= Self::ARCHIVE,
                's' | 'S' => bits |= Self::SYSTEM,
                'h' | 'H' => bits |= Self::HIDDEN,
                'r' | 'R' => bits |= Self::READ_ONLY,
                other if other.is_ascii_alphabetic() => {}
                other => {
                    return Err(format!(
                        "unknown attribute letter {other:?} (expected attribute letters)"
                    ))
                }
            }
        }
        Ok(AttributeSet(bits))
    }

    /// Render as the canonical letter order `as hr` -> `ashr`.
    pub fn as_str(self) -> String {
        let mut s = String::new();
        if self.0 & Self::ARCHIVE != 0 {
            s.push('a');
        }
        if self.0 & Self::SYSTEM != 0 {
            s.push('s');
        }
        if self.0 & Self::HIDDEN != 0 {
            s.push('h');
        }
        if self.0 & Self::READ_ONLY != 0 {
            s.push('r');
        }
        s
    }
}

/// Provider-neutral metadata for one entry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Metadata {
    /// Backend-defined kind of the entry.
    pub kind: EntryKind,
    /// Size in bytes for a regular file.
    ///
    /// `None` when the backend cannot report a size (e.g. an unresolved symlink
    /// in a backend without link metadata). The observed report writes an empty
    /// `<size/>` element for a directory (`tools/_audit/dir-load-then-report.xml`,
    /// O-level: `<name>emptydir</name><size/>`), so "no size" is a value the
    /// report format itself expresses.
    pub size: Option<u64>,
    /// Last-modified time.
    pub modified: Option<Timestamp>,
    /// DOS-style attributes when the backend has them.
    pub attributes: Attributes,
    /// Target of a symlink/junction, verbatim, when this entry is one and the
    /// backend can read it.
    pub symlink_target: Option<VfsPath>,
}

impl Metadata {
    pub fn file(size: u64) -> Self {
        Metadata {
            kind: EntryKind::File,
            size: Some(size),
            modified: None,
            attributes: Attributes::unknown(),
            symlink_target: None,
        }
    }

    pub fn directory() -> Self {
        Metadata {
            kind: EntryKind::Directory,
            size: None,
            modified: None,
            attributes: Attributes::unknown(),
            symlink_target: None,
        }
    }

    pub fn with_modified(mut self, t: Timestamp) -> Self {
        self.modified = Some(t);
        self
    }

    pub fn with_attributes(mut self, a: Attributes) -> Self {
        self.attributes = a;
        self
    }
}

/// One directory entry: a name plus its metadata.
///
/// The name is carried separately from the full path so the comparison aligns on
/// the recorded `<name>` element and does not have to re-split an opaque path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Entry {
    pub name: String,
    pub path: VfsPath,
    pub metadata: Metadata,
}

impl Entry {
    pub fn new(name: impl Into<String>, path: VfsPath, metadata: Metadata) -> Self {
        Entry {
            name: name.into(),
            path,
            metadata,
        }
    }

    pub fn is_dir(&self) -> bool {
        self.metadata.kind.is_dir()
    }

    pub fn is_file(&self) -> bool {
        matches!(self.metadata.kind, EntryKind::File)
    }
}

/// Controls symlink handling, mirroring the documented `follow-symlinks`
/// criterion (`help/scripting_reference.html`: "treats symbolic links and NTFS
/// junctions as the target file or folder, rather than the link itself").
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SymlinkPolicy {
    /// Report the link itself: kind `Symlink`, target recorded, not traversed.
    #[default]
    DoNotFollow,
    /// Resolve to the target's kind and metadata.
    Follow,
}

/// Options a backend may honour per listing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct ListOptions {
    pub symlinks: SymlinkPolicy,
}

/// The read-only filesystem seam.
///
/// A backend implements listing, metadata, whole-file reads, streaming reads and
/// path joining. Nothing here mutates anything, so a read-only backend (an
/// archive, a snapshot, a remote service opened read-only) is a complete
/// implementation — which is the point of ADR-3.
pub trait FileSystem {
    /// A short, stable identity for the backend, used in reports and errors.
    fn kind(&self) -> &'static str;

    /// The separator this backend uses when joining path components.
    fn separator(&self) -> char;

    /// The root path this backend was opened at, echoed into `<ltpath>`/`<rtpath>`.
    fn root(&self) -> &VfsPath;

    /// List one directory's immediate children.
    ///
    /// Implementations must return an explicit error for a path that is not a
    /// directory ([`VfsError::NotADirectory`]) or does not exist
    /// ([`VfsError::NotFound`]). They must **not** return an empty vector to
    /// signal failure: an empty directory and an unreadable directory are
    /// different observations, and the report shows them differently
    /// (`<size>0</size>` for the empty directory in
    /// `tools/_audit/dir-load-expand-report.xml`, O-level).
    fn read_dir(&self, path: &VfsPath, options: ListOptions) -> VfsResult<Vec<Entry>>;

    /// Metadata for one path.
    ///
    /// Unlike [`FileSystem::read_dir`], a missing path is a normal answer here:
    /// the comparison asks about a name on both sides and one side may simply not
    /// have it. The error is still explicit ([`VfsError::NotFound`]), and callers
    /// convert it to "absent" using [`VfsError::is_absence`].
    fn metadata(&self, path: &VfsPath, options: ListOptions) -> VfsResult<Metadata>;

    /// Read a whole file.
    fn read_file(&self, path: &VfsPath) -> VfsResult<Vec<u8>>;

    /// Stream a file's bytes.
    ///
    /// Provided for future large-file handling. The default implementation
    /// delegates to [`FileSystem::read_file`], so a backend that cannot stream is
    /// still complete; a backend that can should override it.
    fn open_read(&self, path: &VfsPath) -> VfsResult<Box<dyn std::io::Read + '_>> {
        let bytes = self.read_file(path)?;
        Ok(Box::new(std::io::Cursor::new(bytes)))
    }

    /// Join a child name onto a parent path using this backend's separator.
    fn join(&self, parent: &VfsPath, name: &str) -> VfsPath {
        parent.join_with(name, self.separator())
    }

    /// True when the path exists in this filesystem.
    ///
    /// Default implementation: `metadata` succeeded, or failed with something
    /// other than absence. A backend that can answer more cheaply should
    /// override, but the default is never a guess about content.
    fn exists(&self, path: &VfsPath, options: ListOptions) -> bool {
        match self.metadata(path, options) {
            Ok(_) => true,
            Err(e) => !e.is_absence(),
        }
    }

    /// Convenience: metadata, mapping absence to `Ok(None)`.
    ///
    /// This is the form the comparison uses for a name that may be on only one
    /// side. Any error other than absence propagates, so an unreadable path is
    /// never silently reported as "missing".
    fn metadata_opt(&self, path: &VfsPath, options: ListOptions) -> VfsResult<Option<Metadata>> {
        match self.metadata(path, options) {
            Ok(m) => Ok(Some(m)),
            Err(e) if e.is_absence() => Ok(None),
            Err(e) => Err(e),
        }
    }

    /// The backend's local UTC offset for a UTC instant, when it knows one.
    ///
    /// Only a local filesystem has a meaningful answer. Returning `None` is not
    /// an error: a report must then render in the offset the reporter was given,
    /// which is the honest behaviour for an archive whose stored timestamp has no
    /// zone.
    fn local_offset_minutes(&self, _utc_millis: i64) -> Option<i32> {
        None
    }
}

/// The writable half of the seam (ADR-3).
///
/// Declared so the boundary is visible in the type system, and **intentionally
/// not implemented by any type in this crate**: folder comparison is read-only
/// and the destructive copy/move/sync operations are out of scope
/// (`product/docs/04-milestones.md` section 0 "MVP 明确不做", and section 4 P9
/// requires an independent safety review first).
///
/// Nothing in the comparison engine or report writer accepts a
/// `WritableFileSystem`, so a read-only feature cannot accidentally gain write
/// access.
pub trait WritableFileSystem: FileSystem {
    fn open_write(&self, path: &VfsPath) -> VfsResult<Box<dyn std::io::Write + '_>>;

    fn create_dir(&self, path: &VfsPath) -> VfsResult<()>;

    fn remove(&self, path: &VfsPath) -> VfsResult<()>;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn attribute_set_parses_documented_letters() {
        assert_eq!(AttributeSet::parse("shr").unwrap().as_str(), "shr");
        assert_eq!(AttributeSet::parse("+sh-r").unwrap().as_str(), "shr");
        assert_eq!(AttributeSet::parse("SHR").unwrap().as_str(), "shr");
        // Unknown letters are inert but ACCEPTED: the live Oracle exits 0 on
        // `criteria attrib:z` (gate FINDINGS F5).
        assert_eq!(AttributeSet::parse("x").unwrap().as_str(), "");
        assert_eq!(AttributeSet::parse("hx").unwrap().as_str(), "h");
        assert!(AttributeSet::parse("1").is_err(), "non-letters stay malformed");
        assert!(AttributeSet::EMPTY.is_empty());
        assert_eq!(AttributeSet::ALL.as_str(), "ashr");
    }

    #[test]
    fn attribute_letters_render_only_known_true_flags() {
        let a = Attributes {
            archive: Some(true),
            system: Some(false),
            hidden: Some(true),
            read_only: None,
        };
        // Order follows the documented [a][s][h][r] and letters that are not set
        // are omitted.
        assert_eq!(a.known_letters(), "ha");
        assert!(!a.is_fully_unknown());
        assert!(Attributes::unknown().is_fully_unknown());
        assert_eq!(Attributes::unknown().known_letters(), "");
    }

    #[test]
    fn contains_all_reports_unknown_rather_than_false() {
        let all_set = Attributes {
            archive: Some(true),
            system: Some(true),
            hidden: Some(true),
            read_only: Some(true),
        };
        assert_eq!(contains(all_set, "shr"), Some(true));
        assert_eq!(contains(all_set, "ashr"), Some(true));

        // `hidden` is present-and-clear: "all of shr are set" is therefore false,
        // and that is a *known* false, not an unknown.
        let hidden_clear = Attributes {
            hidden: Some(false),
            ..all_set
        };
        assert_eq!(contains(hidden_clear, "shr"), Some(false));
        // ...while a set that does not name `hidden` is unaffected by it.
        assert_eq!(contains(hidden_clear, "sr"), Some(true));

        // Unknown must never be reported as "no difference".
        assert_eq!(contains(Attributes::unknown(), "r"), None);
    }

    fn contains(a: Attributes, set: &str) -> Option<bool> {
        a.contains_all(AttributeSet::parse(set).unwrap())
    }

    #[test]
    fn entry_kind_is_not_conflated_with_directory() {
        assert!(EntryKind::Directory.is_dir());
        assert!(!EntryKind::Symlink.is_dir());
        // Unknown must not be silently a directory or a file.
        assert!(!EntryKind::Unknown.is_dir());
        assert_eq!(EntryKind::Unknown.as_str(), "unknown");
    }
}

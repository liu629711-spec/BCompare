//! Typed VFS errors.
//!
//! Design rule (product/docs/05-acceptance-strategy.md section 6, "no fake
//! features"): an operation that cannot be carried out must return an explicit,
//! typed error. It must never return an empty listing or a placeholder value.

use std::fmt;

use crate::path::VfsPath;

/// Which side of a comparison an error came from. Carried so the comparison
/// engine can attribute an I/O failure without re-parsing a message string.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    Left,
    Right,
}

impl Side {
    pub fn as_str(self) -> &'static str {
        match self {
            Side::Left => "left",
            Side::Right => "right",
        }
    }
}

/// The reason a VFS operation failed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VfsError {
    /// The path does not exist in this filesystem.
    NotFound { path: VfsPath },
    /// The path exists but has the wrong entry kind (e.g. `read_dir` on a file).
    NotADirectory { path: VfsPath },
    /// The path exists but is not a regular file (e.g. `open_read` on a dir).
    NotAFile { path: VfsPath },
    /// The operating system or backend refused access.
    PermissionDenied { path: VfsPath, detail: String },
    /// The path string is not valid for this filesystem.
    ///
    /// Opaque path strings are validated by each backend (ADR-4); a path that a
    /// backend cannot represent is an explicit error, not a silent skip.
    InvalidPath { path: VfsPath, detail: String },
    /// The backend does not implement this operation for this path.
    ///
    /// Used instead of a silent empty result, e.g. reading the bytes of a
    /// directory, or a backend that is declared but not implemented.
    Unsupported { path: VfsPath, operation: &'static str },
    /// The operation is not available on this platform / build.
    PlatformUnsupported { operation: &'static str, detail: String },
    /// The entry is present but its kind cannot be determined.
    UnknownKind { path: VfsPath, detail: String },
    /// Anything else the backend could not classify, with the raw description.
    Other { path: VfsPath, detail: String },
}

impl VfsError {
    /// The path the error refers to, when the variant carries one.
    pub fn path(&self) -> Option<&VfsPath> {
        match self {
            VfsError::NotFound { path }
            | VfsError::NotADirectory { path }
            | VfsError::NotAFile { path }
            | VfsError::PermissionDenied { path, .. }
            | VfsError::InvalidPath { path, .. }
            | VfsError::Unsupported { path, .. }
            | VfsError::UnknownKind { path, .. }
            | VfsError::Other { path, .. } => Some(path),
            VfsError::PlatformUnsupported { .. } => None,
        }
    }

    /// True when the error means "the entry is simply not there", which a
    /// comparison may treat as absence rather than as a hard failure.
    pub fn is_absence(&self) -> bool {
        matches!(self, VfsError::NotFound { .. })
    }

    pub(crate) fn from_io(err: std::io::Error, path: VfsPath) -> Self {
        match err.kind() {
            std::io::ErrorKind::NotFound => VfsError::NotFound { path },
            std::io::ErrorKind::PermissionDenied => VfsError::PermissionDenied {
                path,
                detail: err.to_string(),
            },
            _ => VfsError::Other {
                path,
                detail: err.to_string(),
            },
        }
    }
}

impl fmt::Display for VfsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            VfsError::NotFound { path } => write!(f, "not found: {path}"),
            VfsError::NotADirectory { path } => write!(f, "not a directory: {path}"),
            VfsError::NotAFile { path } => write!(f, "not a file: {path}"),
            VfsError::PermissionDenied { path, detail } => {
                write!(f, "permission denied: {path}: {detail}")
            }
            VfsError::InvalidPath { path, detail } => {
                write!(f, "invalid path {path}: {detail}")
            }
            VfsError::Unsupported { path, operation } => {
                write!(f, "unsupported operation {operation} on {path}")
            }
            VfsError::PlatformUnsupported { operation, detail } => {
                write!(f, "platform does not support {operation}: {detail}")
            }
            VfsError::UnknownKind { path, detail } => {
                write!(f, "unknown entry kind for {path}: {detail}")
            }
            VfsError::Other { path, detail } => write!(f, "{path}: {detail}"),
        }
    }
}

impl std::error::Error for VfsError {}

/// Result alias used throughout the crate.
pub type VfsResult<T> = Result<T, VfsError>;

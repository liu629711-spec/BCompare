//! Errors raised by the folder comparison engine.
//!
//! Every variant is explicit. In particular there is **no** variant that means
//! "we could not tell, so we treated it as equal"
//! (`product/docs/05-acceptance-strategy.md` section 6).

use std::fmt;

use reacmp_vfs::VfsError;

/// A folder-comparison failure.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DirError {
    /// The filesystem layer failed.
    Vfs { source: VfsError },
    /// A content criterion needs the file bytes, but reading was not permitted.
    ///
    /// Returned instead of silently downgrading the criterion, which would make
    /// `criteria CRC` a fake feature.
    ContentReadNotAllowed { name: String },
    /// A report layout name that is not one of the three documented layouts.
    UnknownLayout { layout: String },
    /// The XML report cannot represent a status that has no observed token.
    UnrepresentableStatus { status: String },
    /// A fixture manifest is malformed.
    Manifest { detail: String },
}

impl DirError {
    /// True when the underlying cause is "the path is not there".
    pub fn is_absence(&self) -> bool {
        match self {
            DirError::Vfs { source } => source.is_absence(),
            _ => false,
        }
    }

    /// The process exit code that goes with this class of failure.
    ///
    /// `0` success, `1` "different" and `2` "error" are the conventional
    /// comparison-tool codes; the Oracle's script-error codes observed in this
    /// workspace are 104 (licensing, fatal), 105 (script error), 106 (script
    /// command error) and 107 (file not found / argument error) —
    /// `product/verify/README.md` section 3. Only 106 and 107 have a direct
    /// analogue here and are mapped; the rest use the generic error code rather
    /// than inventing a specific one.
    pub fn exit_code(&self) -> i32 {
        match self {
            DirError::Vfs { source } if source.is_absence() => 107,
            DirError::Manifest { .. } => 106,
            DirError::UnknownLayout { .. } => 106,
            DirError::UnrepresentableStatus { .. } => 106,
            DirError::ContentReadNotAllowed { .. } => 2,
            DirError::Vfs { .. } => 2,
        }
    }
}

impl fmt::Display for DirError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DirError::Vfs { source } => write!(f, "{source}"),
            DirError::ContentReadNotAllowed { name } => write!(
                f,
                "content criterion requested for {name} but reading file bytes is disabled"
            ),
            DirError::UnknownLayout { layout } => write!(
                f,
                "unknown report layout {layout:?}; the documented folder-report layouts are \
                 side-by-side, summary and xml"
            ),
            DirError::UnrepresentableStatus { status } => write!(
                f,
                "status {status:?} has no observed <filecomp status=\"…\"> token, so it cannot \
                 be written to an XML report"
            ),
            DirError::Manifest { detail } => write!(f, "manifest error: {detail}"),
        }
    }
}

impl std::error::Error for DirError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            DirError::Vfs { source } => Some(source),
            _ => None,
        }
    }
}

impl From<VfsError> for DirError {
    fn from(source: VfsError) -> Self {
        DirError::Vfs { source }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use reacmp_vfs::VfsPath;

    #[test]
    fn absence_maps_to_the_observed_not_found_exit_code() {
        let e = DirError::Vfs {
            source: VfsError::NotFound {
                path: VfsPath::new("x"),
            },
        };
        assert!(e.is_absence());
        assert_eq!(e.exit_code(), 107);
    }

    #[test]
    fn other_failures_do_not_claim_a_specific_oracle_code() {
        let e = DirError::Vfs {
            source: VfsError::PermissionDenied {
                path: VfsPath::new("x"),
                detail: "nope".to_string(),
            },
        };
        assert!(!e.is_absence());
        assert_eq!(e.exit_code(), 2);
    }

    #[test]
    fn content_read_refusal_is_its_own_error() {
        let e = DirError::ContentReadNotAllowed {
            name: "a.txt".to_string(),
        };
        assert!(e.to_string().contains("a.txt"));
        assert!(!e.is_absence());
    }
}

//! Opaque path strings — ADR-4.
//!
//! `product/docs/03-architecture-options.md` section 7:
//!
//! > ADR-4 | 路径用不透明字符串而非 `std::path::Path` | **建议** | 报告 XML 的
//! > `ltpath` 是字符串（O）
//!
//! The observed folder report carries `<ltpath>D:\Rea\verify\dir\trees\L</ltpath>`
//! (`tools/_audit/dir-load-expand-report.xml`, O-level) — a string, echoed
//! verbatim. A remote path (`ftp://host/dir`) or an archive member path
//! (`C:\a.zip\inner/file.txt`) has no faithful `std::path::Path` representation
//! on Windows, so the comparison engine must never require one.
//!
//! Consequences of the design that are visible in this module:
//!
//! * The separator is a *backend* property, not a property of the value, so
//!   [`VfsPath::name`] accepts either `\` or `/` and [`crate::traits::FileSystem::join`]
//!   is what supplies the separator.
//! * Nothing here normalises, canonicalises, or resolves `.` / `..`: those are
//!   backend concerns and a silent rewrite would corrupt an opaque string that
//!   is echoed into a report.

use std::fmt;

/// An opaque, backend-defined path.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct VfsPath(String);

impl VfsPath {
    pub fn new(value: impl Into<String>) -> Self {
        VfsPath(value.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    /// The last path component, for *any* backend separator.
    ///
    /// Returns the whole string when it contains no separator (so a bare name
    /// round-trips) and an empty string for a root such as `C:\` — callers that
    /// need a name for display must handle that case, which is why this returns
    /// `&str` rather than `Option<&str>`: "no name" is a legitimate observation.
    pub fn name(&self) -> &str {
        match self.0.rfind(['\\', '/']) {
            Some(i) => &self.0[i + 1..],
            None => &self.0,
        }
    }

    /// The parent path, or `None` for a value with no separator.
    ///
    /// Preserves the original separator; does not normalise.
    pub fn parent(&self) -> Option<VfsPath> {
        let i = self.0.rfind(['\\', '/'])?;
        Some(VfsPath(self.0[..i].to_string()))
    }

    /// Append one component with an explicit separator (supplied by the backend).
    pub fn join_with(&self, name: &str, sep: char) -> VfsPath {
        if self.0.is_empty() {
            return VfsPath(name.to_string());
        }
        if self.0.ends_with(['\\', '/']) {
            VfsPath(format!("{}{}", self.0, name))
        } else {
            VfsPath(format!("{}{}{}", self.0, sep, name))
        }
    }

    /// True when this path ends with the given suffix, comparing separators
    /// loosely. Used by tests and by report sanity checks, never by comparison.
    pub fn ends_with_component(&self, component: &str) -> bool {
        self.name() == component
    }
}

impl From<&str> for VfsPath {
    fn from(value: &str) -> Self {
        VfsPath::new(value)
    }
}

impl From<String> for VfsPath {
    fn from(value: String) -> Self {
        VfsPath::new(value)
    }
}

impl fmt::Display for VfsPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

/// Convenience for tests and for the CLI layer: build a `VfsPath` from a
/// `std::path::Path` at the *boundary only*. The comparison engine never calls
/// this; it exists so a local backend can be pointed at a user-supplied path.
pub fn from_local_path(path: &std::path::Path) -> VfsPath {
    VfsPath::new(path.to_string_lossy().into_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn name_splits_on_both_separators() {
        assert_eq!(VfsPath::new(r"C:\a\b\c.txt").name(), "c.txt");
        assert_eq!(VfsPath::new("ftp://host/dir/x.txt").name(), "x.txt");
        assert_eq!(VfsPath::new("bare.txt").name(), "bare.txt");
        assert_eq!(VfsPath::new(r"C:\").name(), "");
    }

    #[test]
    fn parent_preserves_original_separator() {
        assert_eq!(
            VfsPath::new(r"C:\a\b").parent().unwrap().as_str(),
            r"C:\a"
        );
        assert_eq!(VfsPath::new("a/b/c").parent().unwrap().as_str(), "a/b");
        assert!(VfsPath::new("bare").parent().is_none());
    }

    #[test]
    fn join_does_not_double_the_separator() {
        assert_eq!(VfsPath::new(r"C:\a").join_with("b", '\\').as_str(), r"C:\a\b");
        assert_eq!(VfsPath::new("a/").join_with("b", '/').as_str(), "a/b");
        assert_eq!(VfsPath::new("").join_with("b", '/').as_str(), "b");
    }

    #[test]
    fn path_is_not_normalised() {
        // A silent rewrite would corrupt an opaque string echoed into a report.
        let p = VfsPath::new(r"C:\a\.\..\b");
        assert_eq!(p.as_str(), r"C:\a\.\..\b");
    }
}

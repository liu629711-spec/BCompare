//! An in-memory [`FileSystem`] so the engine's tests are hermetic.
//!
//! Exists so a test can construct a precise tree — including cases the real
//! filesystem cannot express on this host, such as an unreadable directory or a
//! name collision between a file and a directory — without touching disk and
//! without depending on host privileges.
//!
//! It is a test double, not a feature: the crate-level comparison engine accepts
//! any [`FileSystem`], and this is simply one more implementation.

use std::collections::BTreeMap;

use reacmp_vfs::{
    AttributeSet, Attributes, Entry, EntryKind, FileSystem, ListOptions, Metadata, Timestamp,
    VfsError, VfsPath, VfsResult,
};

/// One node in the in-memory tree.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FakeNode {
    pub kind: EntryKind,
    pub size: u64,
    pub modified: Option<Timestamp>,
    pub attributes: Attributes,
    /// Content, for a file. Empty for a directory.
    pub content: Vec<u8>,
    /// `Some(message)` makes this directory/list operation fail with an explicit
    /// error, which is how the "unreadable directory is not an empty directory"
    /// behaviour is tested.
    pub read_error: Option<String>,
    /// Children, keyed by name.
    pub children: BTreeMap<String, FakeNode>,
    pub symlink_target: Option<VfsPath>,
}

impl FakeNode {
    pub fn file(content: impl Into<Vec<u8>>) -> Self {
        let content = content.into();
        FakeNode {
            kind: EntryKind::File,
            size: content.len() as u64,
            modified: None,
            attributes: Attributes::unknown(),
            content,
            read_error: None,
            children: BTreeMap::new(),
            symlink_target: None,
        }
    }

    pub fn dir() -> Self {
        FakeNode {
            kind: EntryKind::Directory,
            size: 0,
            modified: None,
            attributes: Attributes::unknown(),
            content: Vec::new(),
            read_error: None,
            children: BTreeMap::new(),
            symlink_target: None,
        }
    }

    /// A symlink node, reported as a link (target recorded) unless followed.
    pub fn symlink(target: &str, resolved_kind_is_dir: bool) -> Self {
        FakeNode {
            kind: EntryKind::Symlink,
            size: 0,
            modified: None,
            attributes: Attributes::unknown(),
            content: Vec::new(),
            read_error: None,
            children: if resolved_kind_is_dir {
                BTreeMap::new()
            } else {
                BTreeMap::new()
            },
            symlink_target: Some(VfsPath::new(target)),
        }
    }

    pub fn with_modified(mut self, seconds: i64) -> Self {
        self.modified = Some(Timestamp::from_unix_seconds(seconds));
        self
    }

    pub fn with_attributes(mut self, attributes: Attributes) -> Self {
        self.attributes = attributes;
        self
    }

    pub fn with_read_error(mut self, message: &str) -> Self {
        self.read_error = Some(message.to_string());
        self
    }

    /// Explicit byte size, for tests that need a size that does not match the
    /// stored content (a "same size, different content" pair, or a metadata
    /// inconsistency).
    pub fn with_size(mut self, size: u64) -> Self {
        self.size = size;
        self
    }

    pub fn child(mut self, name: &str, node: FakeNode) -> Self {
        self.children.insert(name.to_string(), node);
        self
    }
}

/// An in-memory filesystem with a fixed root path.
#[derive(Debug, Clone)]
pub struct FakeFs {
    root: VfsPath,
    root_node: FakeNode,
}

impl FakeFs {
    pub fn new(root: &str) -> Self {
        FakeFs {
            root: VfsPath::new(root),
            root_node: FakeNode::dir(),
        }
    }

    pub fn with(mut self, name: &str, node: FakeNode) -> Self {
        self.root_node.children.insert(name.to_string(), node);
        self
    }

    fn resolve(&self, path: &VfsPath) -> VfsResult<&FakeNode> {
        let rel = relative(path, &self.root)?;
        let mut node = &self.root_node;
        for part in rel.split(['\\', '/']) {
            if part.is_empty() {
                continue;
            }
            node = node.children.get(part).ok_or_else(|| VfsError::NotFound {
                path: path.clone(),
            })?;
        }
        Ok(node)
    }
}

fn relative(path: &VfsPath, root: &VfsPath) -> VfsResult<String> {
    let p = path.as_str();
    let r = root.as_str();
    if p == r {
        return Ok(String::new());
    }
    p.strip_prefix(r)
        .map(|s| s.trim_start_matches(['\\', '/']).to_string())
        .ok_or_else(|| VfsError::InvalidPath {
            path: path.clone(),
            detail: format!("not under the fake root {r}"),
        })
}

impl FileSystem for FakeFs {
    fn kind(&self) -> &'static str {
        "fake"
    }

    fn separator(&self) -> char {
        // Fixed so the tests' expected relative paths are platform-independent.
        '\\'
    }

    fn root(&self) -> &VfsPath {
        &self.root
    }

    fn read_dir(&self, path: &VfsPath, options: ListOptions) -> VfsResult<Vec<Entry>> {
        let node = self.resolve(path)?;
        if node.kind != EntryKind::Directory {
            return Err(VfsError::NotADirectory { path: path.clone() });
        }
        if let Some(message) = &node.read_error {
            return Err(VfsError::PermissionDenied {
                path: path.clone(),
                detail: message.clone(),
            });
        }
        let mut out = Vec::with_capacity(node.children.len());
        for (name, child) in &node.children {
            let child_path = path.join_with(name, self.separator());
            let kind = self.effective_kind(child, options);
            out.push(Entry::new(
                name.clone(),
                child_path,
                Metadata {
                    kind,
                    size: if kind == EntryKind::File {
                        Some(child.size)
                    } else {
                        None
                    },
                    modified: child.modified,
                    attributes: child.attributes,
                    symlink_target: child.symlink_target.clone(),
                },
            ));
        }
        Ok(out)
    }

    fn metadata(&self, path: &VfsPath, options: ListOptions) -> VfsResult<Metadata> {
        let node = self.resolve(path)?;
        let kind = self.effective_kind(node, options);
        Ok(Metadata {
            kind,
            size: if kind == EntryKind::File {
                Some(node.size)
            } else {
                None
            },
            modified: node.modified,
            attributes: node.attributes,
            symlink_target: node.symlink_target.clone(),
        })
    }

    fn read_file(&self, path: &VfsPath) -> VfsResult<Vec<u8>> {
        let node = self.resolve(path)?;
        match node.kind {
            EntryKind::File => Ok(node.content.clone()),
            EntryKind::Directory => Err(VfsError::NotAFile { path: path.clone() }),
            other => Err(VfsError::Unsupported {
                path: path.clone(),
                operation: match other {
                    EntryKind::Symlink => "read_file on an unfollowed symlink",
                    _ => "read_file on an unclassified entry",
                },
            }),
        }
    }

    fn local_offset_minutes(&self, _utc_millis: i64) -> Option<i32> {
        // The fake filesystem has no zone; tests set the offset through the
        // criteria or leave it unknown, so behaviour is explicit either way.
        None
    }
}

impl FakeFs {
    fn effective_kind(&self, node: &FakeNode, options: ListOptions) -> EntryKind {
        if node.kind == EntryKind::Symlink
            && options.symlinks == reacmp_vfs::SymlinkPolicy::Follow
        {
            // Followed: report the target kind. The fake target is a file unless
            // the target path was declared as a directory by convention.
            if node
                .symlink_target
                .as_ref()
                .map(|t| t.as_str().ends_with('/'))
                .unwrap_or(false)
            {
                return EntryKind::Directory;
            }
            return EntryKind::File;
        }
        node.kind
    }
}

/// Convenience: the standard `Attributes` for a hidden file on Windows, used by
/// the attribute fixtures.
pub fn hidden() -> Attributes {
    Attributes {
        hidden: Some(true),
        ..Attributes::unknown()
    }
}

pub fn read_only() -> Attributes {
    Attributes {
        read_only: Some(true),
        ..Attributes::unknown()
    }
}

/// Parse a letter set into an [`AttributeSet`], for test brevity.
pub fn attr_set(text: &str) -> AttributeSet {
    AttributeSet::parse(text).expect("valid attribute set")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fake_fs_lists_and_reads() {
        let fs = FakeFs::new(r"L")
            .with("a.txt", FakeNode::file(b"1234").with_modified(100))
            .with("sub", FakeNode::dir().child("inner", FakeNode::file(b"x")));

        let entries = fs.read_dir(fs.root(), ListOptions::default()).unwrap();
        assert_eq!(entries.len(), 2);

        let a = entries.iter().find(|e| e.name == "a.txt").unwrap();
        assert_eq!(a.metadata.size, Some(4));
        assert_eq!(fs.read_file(&a.path).unwrap(), b"1234");

        let sub = entries.iter().find(|e| e.name == "sub").unwrap();
        assert_eq!(sub.metadata.kind, EntryKind::Directory);
        assert_eq!(sub.metadata.size, None);
    }

    #[test]
    fn fake_fs_reports_absence_and_unreadable_directories_differently() {
        let fs = FakeFs::new("L").with("bad", FakeNode::dir().with_read_error("denied"));
        let missing = VfsPath::new(r"L\nope");
        assert!(fs.metadata(&missing, ListOptions::default()).unwrap_err().is_absence());

        let bad = VfsPath::new(r"L\bad");
        let err = fs.read_dir(&bad, ListOptions::default()).unwrap_err();
        assert!(!err.is_absence(), "an unreadable directory is not an absence");
        assert!(matches!(err, VfsError::PermissionDenied { .. }));
    }

    #[test]
    fn fake_fs_symlink_is_reported_as_a_link_unless_followed() {
        let fs = FakeFs::new("L").with("link.txt", FakeNode::symlink("target.txt", false));
        let p = VfsPath::new(r"L\link.txt");
        let unfollowed = fs.metadata(&p, ListOptions::default()).unwrap();
        assert_eq!(unfollowed.kind, EntryKind::Symlink);
        let followed = fs
            .metadata(
                &p,
                ListOptions {
                    symlinks: reacmp_vfs::SymlinkPolicy::Follow,
                },
            )
            .unwrap();
        assert_eq!(followed.kind, EntryKind::File);
        // Reading a link without following is explicitly unsupported, not empty.
        assert!(matches!(
            fs.read_file(&p),
            Err(VfsError::Unsupported { .. })
        ));
    }
}

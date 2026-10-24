//! The measured ordering for the `变化` (StringFileInfo) group.
//!
//! Measured on every cell: the group is sorted by the **English key name**,
//! not by the resource's own order and not by the translated label:
//!
//! * m112b W1: resource order is CompanyName, FileDescription, FileVersion,
//!   LegalCopyright, LegalTrademarks, OriginalFilename, ProductName,
//!   ProductVersion, Comments -- the report prints 语言, 注释(Comments),
//!   公司名称(CompanyName), 文件描述, 文件版本, 合法版权, 合法商标,
//!   原始文件名, 产品名称, 产品版本. Comments sorts SECOND, which is neither
//!   resource order nor Chinese-label order.
//! * m112 V6 (notepad vs cmd) puts 内部名称(InternalName) between
//!   文件版本(FileVersion) and 合法版权(LegalCopyright) -- English
//!   alphabetical, not code-point.
//!
//! So the sort key is the ASCII key name, case-insensitive, ordinal (the keys
//! are a fixed ASCII vocabulary, so no locale collation is needed -- and
//! using one would not match the measured result either).
//!
//! Transcribed rather than shared with `reacmp-reg`: this crate must stay
//! standalone and hermetic (the `reacmp-pic`/`reacmp-reg` precedent).

use std::cmp::Ordering;

/// Order two StringFileInfo keys by their English name (case-insensitive).
pub fn compare_key(a: &str, b: &str) -> Ordering {
    let la = a.to_ascii_lowercase();
    let lb = b.to_ascii_lowercase();
    match la.cmp(&lb) {
        Ordering::Equal => a.cmp(b),
        other => other,
    }
}

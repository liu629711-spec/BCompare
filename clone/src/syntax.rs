//! Syntax-element importance per BcSyntaxElements / BcFileFormat specs.
//!
//! Element order (bcfileformats-spec.json): 0 Keyword, 1 Identifier,
//! 2 Number, 3-5 String, 6 Directive, 7-8 Comment, 9 Operator.
//! Importance (oracle-verified): identifiers/strings/numbers/operators/
//! directives are important in .c; comments are NOT; whitespace never is.

/// Extension → syntax-aware? (BC picks a grammar by file extension.)
pub fn is_syntax_aware(path: &str) -> bool {
    let lower = path.to_lowercase();
    !(lower.ends_with(".txt") || lower.ends_with(".text"))
}

/// Does a line look like a pure comment (leading // or /* or * continuation)?
pub fn is_comment_line(s: &str) -> bool {
    let t = s.trim_start();
    t.starts_with("//") || t.starts_with("/*") || t.starts_with('*') || t.starts_with("<!--")
}

/// Compare two lines under a syntax grammar.
/// Returns Some(status_kind) where 0=same, 1=similar, 2=different.
pub fn compare_aware(a: &str, b: &str, syntax_aware: bool) -> u8 {
    if a == b {
        return 0;
    }
    if syntax_aware && is_comment_line(a) && is_comment_line(b) {
        // Comments are unimportant: differing comment text = similar.
        return 1;
    }
    // Whitespace-only difference (any position) is unimportant.
    let strip = |s: &str| s.chars().filter(|c| !c.is_whitespace()).collect::<String>();
    if strip(a) == strip(b) {
        return 1;
    }
    // Case-only difference: important when syntax-aware, unimportant in text.
    if !syntax_aware && strip(a).to_lowercase() == strip(b).to_lowercase() {
        return 1;
    }
    if syntax_aware && strip(a).to_lowercase() == strip(b).to_lowercase() {
        // Syntax-aware: case is important → different.
        return 2;
    }
    2
}

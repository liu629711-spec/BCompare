//! LCS/Myers-style alignment with importance-normalized matching.
//!
//! Oracle-verified semantics (verify/golden/disambig):
//!  - lines match for ALIGNMENT when equal after normalization (case+whitespace)
//!  - status is "same" when raw bytes equal, "similar" when only unimportant
//!    differences remain, "different" when important ones remain
//!  - no move detection (shortest edit script)
//!  - duplicates align front-first

#[derive(Debug, Clone, PartialEq)]
pub enum Status {
    Same,
    Similar,
    Different,
    LeftOrphan,
    RightOrphan,
}

pub struct Group {
    pub left: Option<usize>,
    pub right: Option<usize>,
    pub status: Status,
}

/// Normalize for matching. Oracle-verified: ALL whitespace is removed
/// (including punctuation-adjacent: `f( a )` ≡ `f(a)`), and case is folded
/// for plain text. Syntax-aware case sensitivity comes later (BcSyntaxElements).
fn norm(s: &str) -> String {
    s.chars().filter(|c| !c.is_whitespace()).collect::<String>().to_lowercase()
}

fn equal_after_norm(a: &str, b: &str) -> bool {
    norm(a) == norm(b)
}

/// Matching key: in syntax-aware files comment lines match other comment
/// lines (BC aligns comments with comments regardless of text).
fn match_key(s: &str, syntax_aware: bool) -> String {
    if syntax_aware && crate::syntax::is_comment_line(s) {
        "COMMENT-LINE-KEY".to_string()
    } else {
        norm(s)
    }
}

fn equal_key(a: &str, b: &str, syntax_aware: bool) -> bool {
    match_key(a, syntax_aware) == match_key(b, syntax_aware)
}

/// Classic LCS DP over normalized lines, with tie-breaking that prefers
/// matching earlier lines on both sides (front-first, per oracle).
fn lcs_pairs(l: &[String], r: &[String], syntax_aware: bool) -> Vec<(usize, usize)> {
    let n = l.len();
    let m = r.len();
    // dp[i][j] = LCS length of l[i..], r[j..]
    let mut dp = vec![vec![0usize; m + 1]; n + 1];
    for i in (0..n).rev() {
        for j in (0..m).rev() {
            dp[i][j] = if equal_key(&l[i], &r[j], syntax_aware) {
                dp[i + 1][j + 1] + 1
            } else {
                dp[i + 1][j].max(dp[i][j + 1])
            };
        }
    }
    let (mut i, mut j) = (0, 0);
    let mut pairs = Vec::new();
    while i < n && j < m {
        if equal_key(&l[i], &r[j], syntax_aware) && dp[i][j] == dp[i + 1][j + 1] + 1 {
            pairs.push((i, j));
            i += 1;
            j += 1;
        } else if dp[i + 1][j] >= dp[i][j + 1] {
            i += 1;
        } else {
            j += 1;
        }
    }
    pairs
}

pub fn align(l: &[String], r: &[String], syntax_aware: bool) -> Vec<Group> {
    let pairs = lcs_pairs(l, r, syntax_aware);
    let mut out = Vec::new();
    let (mut li, mut ri) = (0usize, 0usize);
    for (pi, pj) in pairs {
        // Unmatched runs become orphan/different blocks.
        emit_block(l, r, li, pi, ri, pj, &mut out);
        let status = match crate::syntax::compare_aware(&l[pi], &r[pj], syntax_aware) {
            0 => Status::Same,
            1 => Status::Similar,
            _ => Status::Different,
        };
        out.push(Group { left: Some(pi), right: Some(pj), status });
        li = pi + 1;
        ri = pj + 1;
    }
    emit_block(l, r, li, l.len(), ri, r.len(), &mut out);
    out
}

/// Unmatched region: pair up min(a,b) as "different", rest as orphans.
/// (Oracle: unequal replace -> differing pairs then a right orphan.)
fn emit_block(
    l: &[String], r: &[String],
    ls: usize, le: usize, rs: usize, re: usize,
    out: &mut Vec<Group>,
) {
    let lc = le - ls;
    let rc = re - rs;
    let paired = lc.min(rc);
    for k in 0..paired {
        out.push(Group { left: Some(ls + k), right: Some(rs + k), status: Status::Different });
    }
    for k in paired..lc {
        out.push(Group { left: Some(ls + k), right: None, status: Status::LeftOrphan });
    }
    for k in paired..rc {
        out.push(Group { left: None, right: Some(rs + k), status: Status::RightOrphan });
    }
}

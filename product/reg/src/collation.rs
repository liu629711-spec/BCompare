//! The measured name-order comparator for registry sibling keys/values.
//!
//! Registry siblings order by the SAME linguistic comparator the folder
//! report uses: pinned by the reference install in `runs/m101f` (F8 symbol
//! zoo `!x %x &x *x ;x ?x ^x `x {x |x }x +x <x >x`; F9 `a!b ab a-b ac`;
//! F10 `0 a Z 中`; F11 `0a a0 aa ab` — none of which is code-point order).
//! This module is a verbatim transcription of `reacmp-dir`'s `name_order`
//! (itself validated against the Oracle in `A3-folder-gate-serial-01/02`),
//! copied rather than shared because `reacmp-reg` must stay a standalone
//! hermetic crate (the `reacmp-pic` zero-dependency precedent).
//!
//! * Windows: ASCII digit runs compare numerically; the first differing
//!   position falls through to `CompareStringW(LOCALE_USER_DEFAULT,
//!   NORM_IGNORECASE)`.
//! * Non-Windows: case-insensitive ordinal with numeric digit runs (an
//!   approximation, not a parity claim -- the Oracle is Windows-only).

use std::cmp::Ordering;

/// Sibling / value-name order.
pub fn compare(a: &str, b: &str) -> Ordering {
    #[cfg(windows)]
    {
        windows_compare(a, b)
    }
    #[cfg(not(windows))]
    {
        fallback_compare(a, b)
    }
}

#[cfg(windows)]
mod win {
    use std::cmp::Ordering;
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    const LOCALE_USER_DEFAULT: u32 = 0x0400;
    const NORM_IGNORECASE: u32 = 0x0000_0001;
    const CSTR_LESS_THAN: i32 = 1;
    const CSTR_GREATER_THAN: i32 = 3;

    #[link(name = "kernel32")]
    extern "system" {
        fn CompareStringW(
            locale: u32,
            flags: u32,
            s1: *const u16,
            c1: i32,
            s2: *const u16,
            c2: i32,
        ) -> i32;
    }

    fn win_compare(a: &[u16], b: &[u16]) -> Ordering {
        let r = unsafe {
            CompareStringW(
                LOCALE_USER_DEFAULT,
                NORM_IGNORECASE,
                a.as_ptr(),
                a.len() as i32,
                b.as_ptr(),
                b.len() as i32,
            )
        };
        match r {
            CSTR_LESS_THAN => Ordering::Less,
            CSTR_GREATER_THAN => Ordering::Greater,
            0 => a.cmp(b),
            _ => Ordering::Equal,
        }
    }

    fn is_digit(c: u16) -> bool {
        (0x30..=0x39).contains(&c)
    }

    fn digit_run(s: &[u16], i: usize) -> (u64, usize) {
        let mut v: u64 = 0;
        let mut j = i;
        while j < s.len() && is_digit(s[j]) {
            v = v.saturating_mul(10).saturating_add(u64::from(s[j] - u16::from(b'0')));
            j += 1;
        }
        (v, j)
    }

    pub fn compare(a: &str, b: &str) -> Ordering {
        let ab: Vec<u16> = OsStr::new(a).encode_wide().collect();
        let bb: Vec<u16> = OsStr::new(b).encode_wide().collect();
        let (mut i, mut j) = (0usize, 0usize);
        while i < ab.len() && j < bb.len() {
            let da = is_digit(ab[i]);
            let db = is_digit(bb[j]);
            if da && db {
                let (va, na) = digit_run(&ab, i);
                let (vb, nb) = digit_run(&bb, j);
                if va != vb {
                    return va.cmp(&vb);
                }
                i = na;
                j = nb;
            } else if da || db {
                return win_compare(&ab[i..], &bb[j..]);
            } else if ab[i] == bb[j] {
                i += 1;
                j += 1;
            } else {
                return win_compare(&ab[i..], &bb[j..]);
            }
        }
        (ab.len() - i).cmp(&(bb.len() - j))
    }
}

#[cfg(windows)]
fn windows_compare(a: &str, b: &str) -> Ordering {
    win::compare(a, b)
}

#[cfg(not(windows))]
fn fallback_compare(a: &str, b: &str) -> Ordering {
    let mut ai = a.chars().peekable();
    let mut bi = b.chars().peekable();
    loop {
        match (ai.peek().copied(), bi.peek().copied()) {
            (None, None) => return Ordering::Equal,
            (None, Some(_)) => return Ordering::Less,
            (Some(_), None) => return Ordering::Greater,
            (Some(ca), Some(cb)) => {
                if ca.is_ascii_digit() && cb.is_ascii_digit() {
                    let na = digits(&mut ai);
                    let nb = digits(&mut bi);
                    if na != nb {
                        return na.cmp(&nb);
                    }
                } else {
                    let la = ca.to_lowercase().next().unwrap_or(ca);
                    let lb = cb.to_lowercase().next().unwrap_or(cb);
                    if la != lb {
                        return la.cmp(&lb);
                    }
                    ai.next();
                    bi.next();
                }
            }
        }
    }
}

#[cfg(not(windows))]
fn digits(it: &mut std::iter::Peekable<std::str::Chars>) -> u64 {
    let mut v: u64 = 0;
    while let Some(c) = it.peek() {
        if c.is_ascii_digit() {
            v = v.saturating_mul(10).saturating_add(u64::from(*c as u8 - b'0'));
            it.next();
        } else {
            break;
        }
    }
    v
}

/// Case-folded equality used for merge identity (a duplicate key/value whose
/// names `compare` Equal merges as `删除/重复跳过`; `AA`/`aa` tie but their
/// digit-free fold is `Aa`).
pub fn same_name(a: &str, b: &str) -> bool {
    compare(a, b) == Ordering::Equal
}

//! Report timestamps and header path formatting.
//!
//! # Timestamp format (observed)
//!
//! Every timed golden report carries `yyyy/mm/dd h:nn:ss` with the hour
//! **unpadded**:
//!
//! ```text
//! Produced: 2026/10/13 9:43:07              verify/layouts/mixed-side-by-side.txt
//! <bcreport created="2026/10/13 9:24:26">   verify/golden/al-duplicates.xml
//! ```
//!
//! The normalizer in `product/verify/harness/normalize.py` encodes the same shape
//! as `\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d` (the `{1,2}` hour is the observed
//! unpadded form), so a report must match it exactly to be comparable.
//!
//! # Why the timestamp is injectable
//!
//! A report that embeds wall-clock time cannot be reproduced byte-for-byte, and
//! the harness handles that by normalizing `Produced:` / `created=` to `TIME`.
//! Emitting the real clock is still the right default for a user, so the
//! timestamp enters through [`Stamp`] and tests supply a fixed one. No hidden
//! global clock read happens anywhere else in the crate.
//!
//! # Formatting the clock without a dependency
//!
//! The core has no third-party dependencies, so the civil-date conversion is
//! done here with Howard Hinnant's `civil_from_days` algorithm. It is exact for
//! the whole proleptic Gregorian calendar; only UTC is produced.

use std::time::{SystemTime, UNIX_EPOCH};

/// A report timestamp in BC's observed format.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Stamp {
    text: String,
}

impl Stamp {
    /// Build a timestamp from its components. The hour is unpadded, as observed.
    pub fn from_parts(year: i64, month: u32, day: u32, hour: u32, minute: u32, second: u32) -> Stamp {
        Stamp {
            text: format!("{year:04}/{month:02}/{day:02} {hour}:{minute:02}:{second:02}"),
        }
    }

    /// The current UTC time.
    pub fn now_utc() -> Stamp {
        let secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            // A clock before the Unix epoch cannot be represented in this format
            // without inventing a value, so fall back to the epoch itself and let
            // the caller see a deterministic, obviously-synthetic date rather
            // than a crash.
            .unwrap_or(0);
        Stamp::from_unix_seconds(secs)
    }

    /// Convert Unix seconds to the civil representation.
    ///
    /// `civil_from_days` (Hinnant): shift the epoch to 0000-03-01 so leap days
    /// land at the end of the year, then use the 400-year cycle's exact
    /// arithmetic.
    pub fn from_unix_seconds(secs: i64) -> Stamp {
        let days = secs.div_euclid(86_400);
        let rem = secs.rem_euclid(86_400);
        let (hour, minute, second) = ((rem / 3600) as u32, ((rem % 3600) / 60) as u32, (rem % 60) as u32);

        let z = days + 719_468;
        let era = z.div_euclid(146_097);
        let doe = z.rem_euclid(146_097); // [0, 146096]
        let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365; // [0, 399]
        let y = yoe + era * 400;
        let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
        let mp = (5 * doy + 2) / 153; // [0, 11]
        let d = (doy - (153 * mp + 2) / 5 + 1) as u32; // [1, 31]
        let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32; // [1, 12]
        let year = if m <= 2 { y + 1 } else { y };

        Stamp::from_parts(year, m, d, hour, minute, second)
    }

    /// The rendered timestamp.
    pub fn as_str(&self) -> &str {
        &self.text
    }
}

impl std::fmt::Display for Stamp {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.text)
    }
}

/// The padding between the two paths in a text report header.
///
/// Observed as exactly five spaces in every captured header:
/// `Left file: <L>     Right file: <R>` (see `verify/layouts/*-side-by-side.txt`
/// and `verify/oracle/report-*.txt`, measured at 5 spaces in all of them).
///
/// This is the *short-path* form. BC wraps the header onto two lines when the
/// combined path text is long (`02-version-and-evidence.md` §3.5); that wrap
/// depends only on path length, and `product/verify/harness/normalize.py`
/// deliberately re-joins it. Because the corpus reports are generated with the
/// pinned `D:\Rea\verify\layouts\...` paths, this crate emits the single-line
/// form and records the wrap as a **known difference** for long paths rather
/// than guessing a width rule that was never measured.
pub const HEADER_GAP: &str = "     ";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn observed_timestamp_shape() {
        // The exact strings from the corpus.
        assert_eq!(
            Stamp::from_parts(2026, 10, 13, 9, 43, 7).as_str(),
            "2026/10/13 9:43:07"
        );
        assert_eq!(
            Stamp::from_parts(2026, 10, 13, 9, 24, 26).as_str(),
            "2026/10/13 9:24:26"
        );
        // The hour is unpadded but the other fields are not.
        assert_eq!(Stamp::from_parts(2026, 1, 2, 0, 5, 9).as_str(), "2026/01/02 0:05:09");
        assert_eq!(Stamp::from_parts(2026, 12, 31, 23, 59, 59).as_str(), "2026/12/31 23:59:59");
    }

    #[test]
    fn epoch_conversion_is_exact() {
        assert_eq!(Stamp::from_unix_seconds(0).as_str(), "1970/01/01 0:00:00");
        // 2026-10-13 09:43:07 UTC == 1791884587
        assert_eq!(Stamp::from_unix_seconds(1_791_884_587).as_str(), "2026/10/13 9:43:07");
        // A known leap day.
        assert_eq!(Stamp::from_unix_seconds(1_582_934_400).as_str(), "2020/02/29 0:00:00");
        // The 2000 leap-year rule (divisible by 400) must be honoured.
        assert_eq!(Stamp::from_unix_seconds(951_782_400).as_str(), "2000/02/29 0:00:00");
        // ...and 1900 was not a leap year.
        assert_eq!(Stamp::from_unix_seconds(-2_203_891_200).as_str(), "1900/03/01 0:00:00");
    }

    #[test]
    fn round_trip_over_many_days() {
        // Every 997th day from 1970 to 2100 renders without panicking and stays
        // inside the expected field ranges.
        let mut secs = 0i64;
        while secs < 4_102_444_800 {
            let s = Stamp::from_unix_seconds(secs);
            let t = s.as_str();
            assert_eq!(t.len(), 18, "unexpected shape: {t}");
            let parts: Vec<&str> = t.split(['/', ' ', ':']).collect();
            assert_eq!(parts.len(), 6, "{t}");
            let year: i64 = parts[0].parse().unwrap();
            let month: u32 = parts[1].parse().unwrap();
            let day: u32 = parts[2].parse().unwrap();
            assert!((1970..=2100).contains(&year), "{t}");
            assert!((1..=12).contains(&month), "{t}");
            assert!((1..=31).contains(&day), "{t}");
            secs += 997 * 86_400;
        }
    }

    #[test]
    fn matches_the_normalizer_timestamp_pattern() {
        // product/verify/harness/normalize.py accepts \d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d
        let t = Stamp::from_parts(2026, 10, 13, 9, 43, 7);
        let s = t.as_str();
        let (date, time) = s.split_once(' ').unwrap();
        let d: Vec<&str> = date.split('/').collect();
        assert_eq!(d.len(), 3);
        assert_eq!(d[0].len(), 4);
        assert_eq!(d[1].len(), 2);
        assert_eq!(d[2].len(), 2);
        let tm: Vec<&str> = time.split(':').collect();
        assert_eq!(tm.len(), 3);
        assert!(tm[0].len() <= 2, "hour must be 1 or 2 digits");
        assert_eq!(tm[1].len(), 2);
        assert_eq!(tm[2].len(), 2);
    }

    #[test]
    fn display_matches_as_str() {
        let t = Stamp::from_parts(2026, 10, 13, 9, 43, 7);
        assert_eq!(format!("{t}"), t.as_str());
    }

    #[test]
    fn header_gap_is_five_spaces() {
        assert_eq!(HEADER_GAP.len(), 5);
        assert!(HEADER_GAP.chars().all(|c| c == ' '));
    }
}

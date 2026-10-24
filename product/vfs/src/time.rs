//! Timestamps and local-time rendering.
//!
//! # Observed evidence
//!
//! The folder report renders a modified time as `2026/10/13 10:06:12`
//! (`tools/_audit/dir-load-expand-report.xml`, O-level: read directly from the
//! Oracle output).
//!
//! **Derived (O -> D):** cross-checking that observed line against the actual
//! fixture metadata shows the value is the file's **local** wall clock, not UTC:
//!
//! ```text
//! fixture            os.stat st_mtime -> local        -> UTC           report says
//! trees/L/diff.txt   2026/10/13 10:06:12                 2026/10/13 02:06:12   2026/10/13 10:06:12
//! ```
//!
//! (This machine is UTC+08:00.) Method: `python -c
//! "import os,datetime;st=os.stat(p);
//!  print(datetime.datetime.fromtimestamp(st.st_mtime))"` on the read-only
//! fixture, compared to the report line. So rendering must apply the local UTC
//! offset.
//!
//! # Unknown
//!
//! Whether a single-digit hour is rendered as `9:06:12` or `09:06:12` is **not
//! determined**: every observed sample has a two-digit hour. See
//! `docs/EVIDENCE.md` "U-M3-3".

use std::fmt;

/// Milliseconds since the Unix epoch (UTC).
///
/// Sub-second precision is retained because a timestamp tolerance expressed in
/// seconds must be evaluated on the real value; the report only *renders*
/// whole seconds (observed).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Timestamp {
    unix_millis: i64,
}

impl Timestamp {
    pub fn from_unix_millis(unix_millis: i64) -> Self {
        Timestamp { unix_millis }
    }

    pub fn from_unix_seconds(unix_seconds: i64) -> Self {
        Timestamp {
            unix_millis: unix_seconds.saturating_mul(1000),
        }
    }

    pub fn from_system_time(t: std::time::SystemTime) -> Option<Self> {
        match t.duration_since(std::time::UNIX_EPOCH) {
            Ok(d) => Some(Timestamp {
                unix_millis: d.as_millis() as i64,
            }),
            Err(e) => {
                // A pre-epoch timestamp is representable but unusual; keep it
                // rather than dropping it, so the comparison still sees a value.
                let d = e.duration();
                let ms = d.as_millis() as i64;
                Some(Timestamp {
                    unix_millis: -ms,
                })
            }
        }
    }

    pub fn unix_millis(self) -> i64 {
        self.unix_millis
    }

    pub fn unix_seconds(self) -> i64 {
        self.unix_millis.div_euclid(1000)
    }

    /// Absolute difference in seconds, truncated toward zero.
    pub fn seconds_between(self, other: Timestamp) -> i64 {
        (self.unix_millis - other.unix_millis).abs() / 1000
    }

    /// Render as the report does, in local wall-clock time.
    ///
    /// `offset_minutes` is minutes **east** of UTC (UTC+08:00 -> `480`).
    pub fn format_local(self, offset_minutes: i32) -> String {
        let shifted = self.unix_millis + (offset_minutes as i64) * 60_000;
        let secs = shifted.div_euclid(1000);
        let (y, mo, d, h, mi, s) = civil_from_unix_seconds(secs);
        // Observed unpadded month/day/hour with padded minute/second: the
        // A-3 folder gate (product/verify/runs/A3-folder-gate-serial-01/
        // REPORT.md) showed the Oracle rendering `<modified>2026/1/1
        // 8:00:00</modified>` (day 1, hour 8 unpadded; minute/second `00`
        // padded) while this engine padded everything; the stored audit
        // report's `10:06:12` confirms minute/second stay two-digit.
        format!("{y:04}/{mo}/{d} {h}:{mi:02}:{s:02}")
    }
}

impl fmt::Display for Timestamp {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}ms", self.unix_millis)
    }
}

/// Convert Unix seconds to a civil date-time (proleptic Gregorian, UTC basis).
///
/// Howard Hinnant's `civil_from_days` algorithm, which is exact for the whole
/// `i64` range and needs no tables or leap-year special cases.
fn civil_from_unix_seconds(secs: i64) -> (i64, u32, u32, u32, u32, u32) {
    let days = secs.div_euclid(86_400);
    let secs_of_day = secs.rem_euclid(86_400);
    let h = (secs_of_day / 3600) as u32;
    let mi = ((secs_of_day % 3600) / 60) as u32;
    let s = (secs_of_day % 60) as u32;

    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097; // [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365; // [0, 399]
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
    let mp = (5 * doy + 2) / 153; // [0, 11]
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32; // [1, 31]
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32; // [1, 12]
    (if m <= 2 { y + 1 } else { y }, m, d, h, mi, s)
}

/// A `SYSTEMTIME`-shaped rule describing when a DST regime starts or ends.
///
/// Mirrors the Win32 `SYSTEMTIME` fields that participate in a time-zone
/// transition rule: month, week (1..5, where 5 means "last"), weekday
/// (0 = Sunday), hour, minute, second.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct TransitionRule {
    pub month: u16,
    pub week: u16,
    pub day_of_week: u16,
    pub hour: u16,
    pub minute: u16,
    pub second: u16,
}

impl TransitionRule {
    pub fn is_absent(&self) -> bool {
        self.month == 0
    }

    /// The local wall-clock instant of this rule in the given year, as Unix
    /// seconds expressed on a *UTC basis* (i.e. the fields are taken verbatim).
    pub fn local_seconds_in_year(&self, year: i64) -> Option<i64> {
        if self.is_absent() {
            return None;
        }
        let day = nth_weekday_of_month(year, self.month as i64, self.week as i64, self.day_of_week as i64)?;
        let days = days_from_civil(year, self.month as i64, day);
        Some(days * 86_400 + self.hour as i64 * 3600 + self.minute as i64 * 60 + self.second as i64)
    }
}

/// `days_from_civil`, the inverse of the date part of [`civil_from_unix_seconds`].
fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = y - era * 400;
    let mp = if m > 2 { m - 3 } else { m + 9 };
    let doy = (153 * mp + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

/// Day-of-week with 0 = Sunday, for a civil date.
fn weekday_of_civil(y: i64, m: i64, d: i64) -> i64 {
    (days_from_civil(y, m, d) + 4).rem_euclid(7)
}

/// Day of month for "the `week`-th `weekday` of `month` in `year`",
/// where `week == 5` means the last such weekday.
fn nth_weekday_of_month(year: i64, month: i64, week: i64, weekday: i64) -> Option<i64> {
    if !(1..=12).contains(&month) || !(1..=5).contains(&week) || !(0..=6).contains(&weekday) {
        return None;
    }
    let first_weekday = weekday_of_civil(year, month, 1);
    let offset = (weekday - first_weekday).rem_euclid(7);
    let first = 1 + offset;
    let mut day = first + (week - 1) * 7;
    let last = days_in_month(year, month);
    if week == 5 {
        while day > last {
            day -= 7;
        }
    }
    if day > last {
        return None;
    }
    Some(day)
}

fn days_in_month(year: i64, month: i64) -> i64 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if (year % 4 == 0 && year % 100 != 0) || year % 400 == 0 {
                29
            } else {
                28
            }
        }
        _ => 30,
    }
}

/// The Win32 `TIME_ZONE_INFORMATION` fields that affect an offset computation.
///
/// Held as plain data (not as the FFI struct) so the offset logic is testable
/// with synthetic rules — including rules for a time zone this machine is not in.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TimeZoneInfo {
    /// Minutes to add to local time to get UTC (`UTC = local + bias`), so a
    /// UTC+08:00 zone has `bias = -480`. Sign convention as documented by Win32.
    pub bias_minutes: i32,
    pub standard_bias_minutes: i32,
    pub daylight_bias_minutes: i32,
    pub standard_date: TransitionRule,
    pub daylight_date: TransitionRule,
}

impl TimeZoneInfo {
    /// A zone with a fixed offset east of UTC and no DST.
    pub fn fixed(east_minutes: i32) -> Self {
        TimeZoneInfo {
            bias_minutes: -east_minutes,
            standard_bias_minutes: 0,
            daylight_bias_minutes: 0,
            standard_date: TransitionRule::default(),
            daylight_date: TransitionRule::default(),
        }
    }

    pub fn has_daylight(&self) -> bool {
        !self.daylight_date.is_absent()
    }

    /// Minutes east of UTC for a given UTC instant.
    pub fn offset_minutes_at(&self, utc_millis: i64) -> i32 {
        let standard_east = -(self.bias_minutes + self.standard_bias_minutes);
        if !self.has_daylight() {
            return standard_east;
        }
        let daylight_east = -(self.bias_minutes + self.daylight_bias_minutes);
        let secs = utc_millis.div_euclid(1000);
        let (year, _, _, _, _, _) = civil_from_unix_seconds(secs);

        // Evaluate the rule for this year and its neighbours, because a
        // southern-hemisphere regime starts in one year and ends in the next.
        let mut is_daylight = false;
        for y in [year - 1, year, year + 1] {
            let Some(start_local_standard) = self.daylight_date.local_seconds_in_year(y) else {
                continue;
            };
            let Some(end_local_daylight) = self.standard_date.local_seconds_in_year(y) else {
                continue;
            };
            // The start rule is stated in local *standard* time; the end rule in
            // local *daylight* time. Convert both to UTC before comparing.
            let start_utc = start_local_standard - standard_east as i64 * 60;
            let end_utc = end_local_daylight - daylight_east as i64 * 60;
            let contained = if start_utc < end_utc {
                // Northern hemisphere: one interval ends inside the same year.
                secs >= start_utc && secs < end_utc
            } else {
                // Southern hemisphere: the interval opened in year `y` runs to
                // the end rule of the *following* year. Testing `secs >= start`
                // against this year's own (earlier) end rule would mark the
                // whole year as daylight, so the next year's end is used.
                match self.standard_date.local_seconds_in_year(y + 1) {
                    Some(next_end_local) => {
                        let next_end_utc = next_end_local - daylight_east as i64 * 60;
                        secs >= start_utc && secs < next_end_utc
                    }
                    None => false,
                }
            };
            if contained {
                is_daylight = true;
            }
        }
        if is_daylight {
            daylight_east
        } else {
            standard_east
        }
    }
}

/// Supplies the local UTC offset for a UTC instant.
///
/// Injected rather than assumed so unit tests are deterministic and so a future
/// CLI can supply a different source.
pub trait OffsetProvider {
    fn offset_minutes_at(&self, utc_millis: i64) -> i32;
}

/// A fixed offset; used by tests and by `--tz-offset` CLI overrides.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FixedOffset {
    pub east_minutes: i32,
}

impl FixedOffset {
    pub fn new(east_minutes: i32) -> Self {
        FixedOffset { east_minutes }
    }
}

impl OffsetProvider for FixedOffset {
    fn offset_minutes_at(&self, _utc_millis: i64) -> i32 {
        self.east_minutes
    }
}

/// Always UTC. Deterministic, and honest: it never claims local accuracy.
#[derive(Debug, Clone, Copy, Default)]
pub struct UtcOffset;

impl OffsetProvider for UtcOffset {
    fn offset_minutes_at(&self, _utc_millis: i64) -> i32 {
        0
    }
}

/// The operating system's local time zone.
///
/// On Windows this reads `TIME_ZONE_INFORMATION` and self-checks the result
/// against `GetLocalTime()` vs `GetSystemTime()` for the current instant, so a
/// wrong struct interpretation surfaces as an explicit error instead of a
/// silently wrong offset. On other platforms construction fails explicitly —
/// callers must inject an [`OffsetProvider`].
pub struct SystemZone {
    info: TimeZoneInfo,
}

impl std::fmt::Debug for SystemZone {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SystemZone")
            .field("info", &self.info)
            .finish()
    }
}

impl SystemZone {
    pub fn info(&self) -> &TimeZoneInfo {
        &self.info
    }
}

impl OffsetProvider for SystemZone {
    fn offset_minutes_at(&self, utc_millis: i64) -> i32 {
        self.info.offset_minutes_at(utc_millis)
    }
}

#[cfg(windows)]
mod win {
    use super::*;
    use crate::error::{VfsError, VfsResult};

    #[repr(C)]
    #[derive(Clone, Copy, Default)]
    struct SystemTime {
        year: u16,
        month: u16,
        day_of_week: u16,
        day: u16,
        hour: u16,
        minute: u16,
        second: u16,
        milliseconds: u16,
    }

    extern "system" {
        fn GetTimeZoneInformation(lp_time_zone_information: *mut u8) -> u32;
        fn GetLocalTime(lp_system_time: *mut SystemTime);
        fn GetSystemTime(lp_system_time: *mut SystemTime);
    }

    /// Byte offsets inside `TIME_ZONE_INFORMATION` (x64, natural alignment):
    /// `BIAS(4) + StandardName(64) + StandardDate(16) + StandardBias(4) +
    /// DaylightName(64) + DaylightDate(16) + DaylightBias(4)`.
    ///
    /// The buffer is byte-addressed on purpose: declaring the full struct in
    /// Rust would make a layout mistake invisible, whereas reading at documented
    /// offsets lets [`super::SystemZone::new`] validate the result.
    const OFF_BIAS: usize = 0;
    const OFF_STANDARD_DATE: usize = 68;
    const OFF_STANDARD_BIAS: usize = 84;
    const OFF_DAYLIGHT_DATE: usize = 152;
    const OFF_DAYLIGHT_BIAS: usize = 168;
    const BUF_LEN: usize = 176;

    fn read_i32(buf: &[u8], off: usize) -> i32 {
        i32::from_le_bytes([buf[off], buf[off + 1], buf[off + 2], buf[off + 3]])
    }

    fn read_u16(buf: &[u8], off: usize) -> u16 {
        u16::from_le_bytes([buf[off], buf[off + 1]])
    }

    /// Read a `SYSTEMTIME` transition rule. `wYear` is deliberately skipped: it
    /// is always 0 for a DST rule ("every year").
    fn read_rule(buf: &[u8], off: usize) -> TransitionRule {
        TransitionRule {
            month: read_u16(buf, off + 2),
            day_of_week: read_u16(buf, off + 4),
            week: read_u16(buf, off + 6),
            hour: read_u16(buf, off + 8),
            minute: read_u16(buf, off + 10),
            second: read_u16(buf, off + 12),
        }
    }

    pub fn system_zone() -> VfsResult<SystemZone> {
        let mut buf = [0u8; BUF_LEN];
        let rc = unsafe { GetTimeZoneInformation(buf.as_mut_ptr()) };

        let bias = read_i32(&buf, OFF_BIAS);
        if !(-1440..=1440).contains(&bias) {
            return Err(VfsError::PlatformUnsupported {
                operation: "GetTimeZoneInformation",
                detail: format!("implausible bias {bias}; struct layout mismatch?"),
            });
        }

        let std_rule = read_rule(&buf, OFF_STANDARD_DATE);
        let dst_rule = read_rule(&buf, OFF_DAYLIGHT_DATE);
        let info = TimeZoneInfo {
            bias_minutes: bias,
            standard_bias_minutes: read_i32(&buf, OFF_STANDARD_BIAS),
            daylight_bias_minutes: read_i32(&buf, OFF_DAYLIGHT_BIAS),
            standard_date: std_rule,
            daylight_date: dst_rule,
        };

        let zone = SystemZone { info };

        // Self-check: the offset for "now" must agree with the difference
        // between the OS's local and UTC clocks.
        let mut local = SystemTime::default();
        let mut utc = SystemTime::default();
        unsafe {
            GetLocalTime(&mut local);
            GetSystemTime(&mut utc);
        }
        let local_secs = civil_seconds_from_systemtime(&local);
        let utc_secs = civil_seconds_from_systemtime(&utc);
        let observed_offset = ((local_secs - utc_secs) / 60) as i32;
        let computed = zone.offset_minutes_at(utc_secs * 1000);
        // Allow a one-minute disagreement caused by the two clock reads
        // straddling a minute boundary.
        if (computed - observed_offset).abs() > 1 {
            return Err(VfsError::PlatformUnsupported {
                operation: "GetTimeZoneInformation",
                detail: format!(
                    "computed offset {computed} disagrees with clocks ({observed_offset}); \
                     struct layout mismatch?"
                ),
            });
        }

        // Keep the fields actually read, so an unused-field warning cannot
        // silently hide a mistake.
        debug_assert!(info.standard_date.week <= 5 && info.daylight_date.week <= 5);
        let _ = rc;
        Ok(zone)
    }

    fn civil_seconds_from_systemtime(st: &SystemTime) -> i64 {
        let days = days_from_civil(st.year as i64, st.month as i64, st.day as i64);
        days * 86_400
            + st.hour as i64 * 3600
            + st.minute as i64 * 60
            + st.second as i64
    }
}

#[cfg(windows)]
pub use win::system_zone;

/// Build the system offset provider, or an explicit error when impossible.
#[cfg(windows)]
pub fn system_offset_provider() -> crate::error::VfsResult<SystemZone> {
    win::system_zone()
}

#[cfg(not(windows))]
pub fn system_offset_provider() -> crate::error::VfsResult<SystemZone> {
    Err(crate::error::VfsError::PlatformUnsupported {
        operation: "system_offset_provider",
        detail: "implemented for Windows only; inject an OffsetProvider instead".to_string(),
    })
}

/// Unsupported-zone placeholder for non-Windows targets.
#[cfg(not(windows))]
#[derive(Debug)]
pub struct SystemZone {
    info: TimeZoneInfo,
}

#[cfg(not(windows))]
impl OffsetProvider for SystemZone {
    fn offset_minutes_at(&self, utc_millis: i64) -> i32 {
        self.info.offset_minutes_at(utc_millis)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn civil_conversion_matches_known_instants() {
        // 2026-10-13 10:06:12 UTC+8 == 2026-10-13 02:06:12 UTC.
        // The instant is the one the observed report rendered, converted from the
        // fixture's own st_mtime (see the module doc).
        let t = Timestamp::from_unix_seconds(1_791_857_172);
        assert_eq!(t.format_local(0), "2026/10/13 2:06:12");
        assert_eq!(t.format_local(480), "2026/10/13 10:06:12");
        // Single-digit month/day/hour render UNPADDED while minute/second stay
        // two-digit — observed on the live Oracle (gate FINDINGS:
        // `<modified>2026/1/1 8:00:00</modified>`).
        // 1_767_225_600 s = 2026-01-01 00:00:00 UTC = 08:00:00 at UTC+8,
        // which is exactly the mtime the gate's tolerance fixtures carry.
        assert_eq!(
            Timestamp::from_unix_seconds(1_767_225_600).format_local(480),
            "2026/1/1 8:00:00"
        );
    }

    #[test]
    fn civil_conversion_handles_epoch_and_leap_day() {
        assert_eq!(Timestamp::from_unix_seconds(0).format_local(0), "1970/1/1 0:00:00");
        // 2024-02-29T12:00:00Z
        assert_eq!(
            Timestamp::from_unix_seconds(1_709_208_000).format_local(0),
            "2024/2/29 12:00:00"
        );
        // 2000-02-29 (400-year leap rule)
        assert_eq!(
            Timestamp::from_unix_seconds(951_782_400).format_local(0),
            "2000/2/29 0:00:00"
        );
    }

    #[test]
    fn seconds_between_uses_absolute_value() {
        let a = Timestamp::from_unix_seconds(100);
        let b = Timestamp::from_unix_seconds(103);
        assert_eq!(a.seconds_between(b), 3);
        assert_eq!(b.seconds_between(a), 3);
        // Sub-second differences truncate to zero seconds.
        assert_eq!(
            Timestamp::from_unix_millis(1_000).seconds_between(Timestamp::from_unix_millis(1_900)),
            0
        );
    }

    #[test]
    fn fixed_zone_has_no_daylight() {
        let z = TimeZoneInfo::fixed(480);
        assert_eq!(z.bias_minutes, -480);
        assert!(!z.has_daylight());
        assert_eq!(z.offset_minutes_at(1_792_200_372_000), 480);
    }

    #[test]
    fn synthetic_us_rules_select_daylight_correctly() {
        // US Eastern: bias 300 (UTC-5), daylight bias -60 (UTC-4);
        // DST starts 2nd Sunday of March 02:00 local standard,
        // ends 1st Sunday of November 02:00 local daylight.
        let z = TimeZoneInfo {
            bias_minutes: 300,
            standard_bias_minutes: 0,
            daylight_bias_minutes: -60,
            standard_date: TransitionRule {
                month: 11,
                week: 1,
                day_of_week: 0,
                hour: 2,
                minute: 0,
                second: 0,
            },
            daylight_date: TransitionRule {
                month: 3,
                week: 2,
                day_of_week: 0,
                hour: 2,
                minute: 0,
                second: 0,
            },
        };
        // Known calendar facts for 2026: 2nd Sunday of March is the 8th,
        // 1st Sunday of November is the 1st.
        assert_eq!(nth_weekday_of_month(2026, 3, 2, 0), Some(8));
        assert_eq!(nth_weekday_of_month(2026, 11, 1, 0), Some(1));

        // 2026-01-15T12:00:00Z -> standard, UTC-5
        assert_eq!(z.offset_minutes_at(1_768_478_400_000), -300);
        // 2026-07-01T12:00:00Z -> daylight, UTC-4
        assert_eq!(z.offset_minutes_at(1_782_907_200_000), -240);
        // One hour before the March transition: still standard.
        // 2026-03-08T07:00:00Z is 02:00 EST = the transition instant (start).
        assert_eq!(z.offset_minutes_at(1_772_953_200_000 - 3_600_000), -300);
        assert_eq!(z.offset_minutes_at(1_772_953_200_000), -240);
        // One hour after the November transition: standard again.
        // 2026-11-01T06:00:00Z is 02:00 EDT = the transition instant (end).
        assert_eq!(z.offset_minutes_at(1_793_512_800_000 - 3_600_000), -240);
        assert_eq!(z.offset_minutes_at(1_793_512_800_000), -300);
    }

    #[test]
    fn southern_hemisphere_rules_wrap_the_new_year() {
        // Australia/Sydney shaped: UTC+10 standard, UTC+11 daylight.
        // Win32 `DaylightBias` is signed the same way as `Bias` (add-to-local to
        // get UTC), so a +1h shift eastward is `-60`.
        let z = TimeZoneInfo {
            bias_minutes: -600,
            standard_bias_minutes: 0,
            daylight_bias_minutes: -60,
            standard_date: TransitionRule {
                month: 4,
                week: 1,
                day_of_week: 0,
                hour: 3,
                minute: 0,
                second: 0,
            },
            daylight_date: TransitionRule {
                month: 10,
                week: 1,
                day_of_week: 0,
                hour: 2,
                minute: 0,
                second: 0,
            },
        };
        // January is daylight in the southern hemisphere.
        assert_eq!(z.offset_minutes_at(1_768_478_400_000), 660);
        // July is standard.
        assert_eq!(z.offset_minutes_at(1_782_907_200_000), 600);
    }
}

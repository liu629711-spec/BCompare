//! The measured value renderings for every field (docs/18 §3).
//!
//! Each function here exists because a probe cell pinned the exact spelling:
//! `字节` for the file size, `0x%08X` for the checksum and image base, the
//! comma-joined `标志`/`DLL 旗帜` flag lists, the `Windows NT <maj>.<min>`
//! OS strings, and the version-number dotted forms.

use crate::parse::{PeHeader, VersionInfo};

/// The `代码/数据` field: the file size (m112: "124,048 字节" / EN " bytes").
///
/// The measured separator is a comma grouping the thousands, and the unit is a
/// separate token with one leading ASCII space.
pub fn size_text(size: u64, locale: &crate::engine::Locale) -> String {
    let n = size.to_string();
    let grouped = group_thousands(&n);
    format!("{grouped} {}", locale.bytes_unit)
}

fn group_thousands(n: &str) -> String {
    let mut out = String::with_capacity(n.len() + n.len() / 3);
    for (i, c) in n.chars().enumerate() {
        let from_end = n.len() - i;
        #[allow(clippy::manual_is_multiple_of)] // the 3-digit grouping mirrors the archive
        if i > 0 && from_end % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    out
}

/// The `PE 头信息/操作系统` field: "Windows NT 6.0" (m112), from the optional
/// header's MajorOperatingSystemVersion/MinorOperatingSystemVersion.
pub fn os_text(v: (u16, u16)) -> String {
    format!("Windows NT {}.{}", v.0, v.1)
}

/// The `固定/操作系统` field: "Windows NT, Windows 32-bit" (m112) -- a FIXED
/// string on every measured cell, not derived from the file.
pub const FIXED_OS_TEXT_EN: &str = "Windows NT, Windows 32-bit";
pub const FIXED_OS_TEXT_ZH: &str = "Windows NT, Windows 32-bit";

/// The `PE 头信息/用户界面` field: "<subsystem name> <maj>.<min>"
/// (m112: "Windows GUI 6.0", "Windows console 5.0", "Windows console 10.0").
pub fn subsystem_text(subsystem: u16, version: (u16, u16)) -> String {
    let name = match subsystem {
        1 => "本机",
        2 => "Windows GUI",
        3 => "Windows console",
        5 => "OS/2 console",
        7 => "Posix console",
        9 => "Windows CE GUI",
        14 => "EFI 应用程序",
        16 => "Windows 启动应用程序",
        other => return format!("{other}"),
    };
    format!("{name} {}.{}", version.0, version.1)
}

/// The `PE 头信息/处理器` field (m112: "AMD64", "I386").
pub fn machine_text(machine: u16) -> String {
    match machine {
        0x014c => "I386".to_string(),
        0x8664 => "AMD64".to_string(),
        0x01c0 => "ARM".to_string(),
        0xaa64 => "ARM64".to_string(),
        0x01c4 => "ARMNT".to_string(),
        0x0200 => "IA64".to_string(),
        0x0EBC => "RISC-V 32位".to_string(),
        other => format!("{other:#06x}"),
    }
}

/// The `PE 头信息/链接器版本` field (m112: "2.25", "8.0", "14.38").
pub fn linker_text(v: (u8, u8)) -> String {
    format!("{}.{}", v.0, v.1)
}

/// The `PE 头信息/图像库` field: "0x0000000000400000" (PE32+) /
/// "0x00400000" (PE32) -- the measured width follows the magic, not the value.
pub fn image_base_text(base: u64, pe32_plus: bool, locale: &crate::engine::Locale) -> String {
    if locale.is_zh {
        // Measured on the current install: PE32+ prints 16 hex digits, PE32
        // prints 8 -- the same rule the English install uses, only the label
        // text differs.
    }
    if pe32_plus {
        format!("{base:#018X}")
    } else {
        format!("{base:#010X}")
    }
}

/// The `PE 头信息/校验` field: "0x0305D366" (m112) -- always 8 hex digits.
pub fn checksum_text(sum: u32) -> String {
    format!("{sum:#010X}")
}

/// The `PE 头信息/创建日期` field: the COFF timestamp rendered in the LOCAL
/// zone as "2026/3/21 2:52:34" (m112: slash separators, NO zero padding).
///
/// The measured zone is the machine's: the donor's stamp is 2026-03-20
/// 18:52:34 UTC and the report shows 2026/3/21 2:52:34 (UTC+8). `offset_secs`
/// is passed in by the caller so the crate stays hermetic (no OS time API).
pub fn timestamp_text(stamp: u32, offset_secs: i64) -> String {
    let mut days = (stamp as i64 + offset_secs) / 86_400;
    let secs = ((stamp as i64 + offset_secs) % 86_400) as u32;
    let hour = secs / 3600;
    let minute = (secs % 3600) / 60;
    let second = secs % 60;
    // Shift from 1970-01-01 to the proleptic Gregorian 0000-03-01 epoch.
    days += 719_468;
    let era = if days >= 0 { days } else { days - 146_096 } / 146_097;
    let doe = (days - era * 146_097) as u64; // [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365; // [0, 399]
    let y = (yoe as i64) + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
    let mp = (5 * doy + 2) / 153; // [0, 11]
    let d = doy - (153 * mp + 2) / 5 + 1; // [1, 31]
    let m = if mp < 10 { mp + 3 } else { mp - 9 }; // [1, 12]
    let year = if m <= 2 { y + 1 } else { y };
    // The measured rendering pads minutes and seconds to two digits but
    // leaves the hour and the date unpadded (m112: "8:06:14", "2:52:34").
    format!("{year}/{m}/{d} {hour}:{minute:02}:{second:02}")
}

/// The `PE 头信息/标志` field: the COFF characteristics as a comma-joined
/// Chinese list (m112: "可执行文件, 地址空间>2GB, 已移除调试信息").
///
/// `machine` matters: every I386 file in the corpus renders BOTH `小端序` and
/// `大端序` regardless of the characteristic bits (m112b W8: 0x818e has
/// neither 0x0080 nor a big-endian bit, yet the archive prints both), while
/// AMD64 files print neither.  Measured, not derived -- docs/18 §4.
pub fn characteristics_text(c: u16, machine: u16, locale: &crate::engine::Locale) -> String {
    // Build in the measured order; the endianness pair is keyed on the
    // MACHINE, not on bits (docs/18 §4): I386 renders `小端序` before
    // `32位字长` and `大端序` right after it; AMD64 renders neither.
    let le = if locale.is_zh { "小端序" } else { "Little endian" };
    let be = if locale.is_zh { "大端序" } else { "Big endian" };
    let order: &[(u16, &str)] = &[
        (0x0002, if locale.is_zh { "可执行文件" } else { "Executable" }),
        (0x0004, if locale.is_zh { "行号被剥离" } else { "Line numbers stripped" }),
        (0x0008, if locale.is_zh { "本地符号被剥离" } else { "Local symbols stripped" }),
        (0x0000, le), // machine-keyed, always passes the bit test below
        (0x0100, if locale.is_zh { "32位字长" } else { "32-bit words" }),
        (0x0000, be),
        (0x0020, if locale.is_zh { "地址空间>2GB" } else { "Addresses larger than 2 GB" }),
        (0x0001, if locale.is_zh { "已重定位" } else { "relocations stripped" }),
        (0x0010, if locale.is_zh { "强制最小" } else { "force minimum" }),
        (0x0200, if locale.is_zh { "已移除调试信息" } else { "Debug info stripped" }),
        (0x1000, if locale.is_zh { "系统文件" } else { "system file" }),
        (0x2000, "DLL"),
    ];
    let i386 = machine == 0x014c;
    let mut out = Vec::new();
    for (bit, name) in order {
        let hit = if *bit == 0 { i386 } else { c & bit != 0 };
        if hit {
            out.push(*name);
        }
    }
    out.join(", ")
}

/// The `PE 头信息/DLL 旗帜` field (m112: "高熵值64位地址, 动态基址, 兼容NX保护,
/// 终端服务器感知").
pub fn dll_flags_text(c: u16, locale: &crate::engine::Locale) -> String {
    let flags: &[(u16, &str)] = if locale.is_zh {
        &[
            (0x0020, "高熵值64位地址"),
            (0x0040, "动态基址"),
            (0x0100, "兼容NX保护"),
            (0x4000, "控制流防护"),
            (0x8000, "终端服务器感知"),
        ]
    } else {
        &[
            (0x0020, "High entropy 64-bit addresses"),
            (0x0040, "Dynamic base"),
            (0x0100, "NX compatible"),
            (0x4000, "Control flow guard"),
            (0x8000, "Terminal server aware"),
        ]
    };
    let mut out = Vec::new();
    for (bit, name) in flags {
        if c & bit != 0 {
            out.push(*name);
        }
    }
    out.join(", ")
}

/// The `固定/文件版本` / `固定/产品版本` field: "5.2.1.32035" (m112).
pub fn version_text(v: (u16, u16, u16, u16)) -> String {
    format!("{}.{}.{}.{}", v.0, v.1, v.2, v.3)
}

/// The `固定/文件类型` field (m112: "应用程序", "DLL").
pub fn file_type_text(t: u32, locale: &crate::engine::Locale) -> String {
    let s = match t {
        1 => if locale.is_zh { "应用程序" } else { "Application" },
        2 => "DLL",
        3 => if locale.is_zh { "驱动程序" } else { "Driver" },
        4 => if locale.is_zh { "字体" } else { "Font" },
        5 => if locale.is_zh { "虚拟设备" } else { "Virtual device" },
        7 => if locale.is_zh { "静态库" } else { "Static library" },
        _ => if locale.is_zh { "未知" } else { "Unknown" },
    };
    s.to_string()
}

/// True when the optional header is PE32+ (`magic == 0x20b`).
pub fn is_pe32_plus(_info: &VersionInfo, pe: &PeHeader) -> bool {
    // PE32+ is identified by the 64-bit image-base form; AMD64/ARM64 machines
    // are always PE32+ in the measured corpus (m112 W9).
    matches!(pe.machine, 0x8664 | 0xaa64)
}

/// PE32+ detection used by [`image_base_text`]: AMD64/ARM64 are always PE32+
/// in the measured corpus (m112 W9). Exposed as a free function so the engine
/// can call it without a full `VersionInfo`.
pub fn is_pe32_plus_dummy(p: &PeHeader) -> bool {
    matches!(p.machine, 0x8664 | 0xaa64)
}

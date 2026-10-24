//! Minimal PE version-resource decoding (docs/18 §3).
//!
//! Zero dependencies: the resource tree is walked straight off the file bytes.
//! Only what the measured model needs is decoded:
//!
//! * the RT_VERSION (type 16) resource, first name entry, first language;
//! * the `VS_VERSION_INFO` blob -- the fixed block (file/product version) and
//!   the `StringFileInfo` children;
//! * the `VarFileInfo` translation list (lang, codepage).
//!
//! ## What the Oracle's field list is made of (m112/m112b measurements)
//!
//! The report is a two-column table of aligned FIELD pairs. The left column
//! order, measured on every cell, is:
//!
//! ```text
//! 代码                      group
//!   数据                    value  = "<n> 字节"    -- the FILE SIZE
//! PE 头信息                  group
//!   操作系统 / 处理器 / 创建日期 / 标志 /
//!   链接器版本 / 图像库 / [图像版本] / 校验 /
//!   用户界面 / DLL 旗帜      values from the COFF/optional header
//! 固定                      group  (the VS_FIXEDFILEINFO block)
//!   文件版本 / 产品版本 / 操作系统 / 文件类型
//! 翻译                      group
//!   语言                    from VarFileInfo
//! 变化                      group  (the StringFileInfo entries)
//!   语言 / 公司名称 / 文件描述 / 文件版本 / 合法版权 /
//!   合法商标 / 原始文件名 / 产品名称 / 产品版本 / 注释
//! ```
//!
//! `[图像版本]` is present only when the optional header carries a non-zero
//! MajorImageVersion/MinorImageVersion (observed on the Windows system
//! binaries, absent on both BCompare engines -- W9/V6).
//!
//! Not decoded here because the measured corpus never showed them: `InternalName`
//! and `PrivateBuild`/`SpecialBuild` (the donor PE has no such entries, so
//! whether BC prints them is UNMEASURED -- see docs/18 §7 residual U-ver-2).

/// One decoded version resource.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct VersionInfo {
    /// File size in bytes -- the `代码/数据` field (m112: "124,048 字节").
    pub file_size: u64,
    /// The `PE 头信息` fields, in the measured order.
    pub pe: Option<PeHeader>,
    /// The `固定` block: file version, product version, OS, file type.
    pub fixed: Option<FixedInfo>,
    /// The `翻译` language string, e.g. "英语(美国), 01252  (ANSI - 拉丁语 I)".
    pub translation: Option<String>,
    /// The `变化` (StringFileInfo) entries, in the resource's own order.
    pub strings: Vec<(String, String)>,
}

/// The `PE 头信息` group (m112: 操作系统/处理器/创建日期/标志/链接器版本/
/// 图像库/[图像版本]/校验/用户界面/DLL 旗帜).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct PeHeader {
    pub machine: u16,
    /// COFF timestamp as a seconds-since-epoch count (the report renders it in
    /// the local zone; this crate stores the raw value).
    pub time_date_stamp: u32,
    pub characteristics: u16,
    pub subsystem: u16,
    pub dll_characteristics: u16,
    pub image_base: u64,
    pub check_sum: u32,
    pub linker_version: (u8, u8),
    pub os_version: (u16, u16),
    pub image_version: Option<(u16, u16)>,
    pub subsystem_version: (u16, u16),
}

/// The `固定` (VS_FIXEDFILEINFO) block.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct FixedInfo {
    pub file_version: (u16, u16, u16, u16),
    pub product_version: (u16, u16, u16, u16),
    pub file_os: u32,
    pub file_type: u32,
}

/// Why a file has no version info at all.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VerError {
    /// Not a PE: no `MZ` signature (m112 V7/V8: a plain .txt -- the report then
    /// shows an EMPTY field list on that side).
    NotPE,
    /// A PE with no RT_VERSION resource (still prints the PE 头信息 group).
    NoResource,
}

/// Locate and decode the version resource of a PE image.
///
/// Returns `Err(VerError::NotPE)` for a non-PE (the measured "empty side"
/// case) and `Err(VerError::NoResource)` when the image is a PE but carries no
/// version resource (the PE 头信息 group still renders in the report, so the
/// caller must distinguish the two -- m112 V8).
pub fn read_version(bytes: &[u8]) -> Result<VersionInfo, VerError> {
    if bytes.len() < 0x40 || &bytes[..2] != b"MZ" {
        return Err(VerError::NotPE);
    }
    let pe_off = match slice4(bytes, 0x3c) {
        Some(v) => u32::from_le_bytes(v) as usize,
        None => return Err(VerError::NotPE),
    };
    if pe_off + 24 > bytes.len() || &bytes[pe_off..pe_off + 4] != b"PE\0\0" {
        return Err(VerError::NotPE);
    }
    let coff = &bytes[pe_off + 4..];
    let machine = match (coff.first(), coff.get(1)) {
        (Some(a), Some(b)) => u16::from_le_bytes([*a, *b]),
        _ => return Err(VerError::NotPE),
    };
    let time_date_stamp = u32::from_le_bytes(u32_of(coff, 4).ok_or(VerError::NotPE)?);
    let opt_size = match (coff.get(16), coff.get(17)) {
        (Some(a), Some(b)) => u16::from_le_bytes([*a, *b]) as usize,
        _ => return Err(VerError::NotPE),
    };
    let characteristics = match (coff.get(18), coff.get(19)) {
        (Some(a), Some(b)) => u16::from_le_bytes([*a, *b]),
        _ => return Err(VerError::NotPE),
    };
    let opt = &bytes[pe_off + 24..];
    if opt.len() < opt_size.max(96) {
        return Err(VerError::NotPE);
    }
    let magic = u16::from_le_bytes([opt[0], opt[1]]);
    let pe32_plus = magic == 0x20b;
    // Optional header layout after the magic word:
    //   PE32:   0x60.. SizeOfImage? no: 0x38 NumberOfRvaAndSizes, 0x3c dirs
    //   PE32+:  0x70 NumberOfRvaAndSizes? -- offsets below are measured from
    //   the published layouts and validated against both engines and the
    //   Windows system binaries in the m112 corpus.  The version fields at
    //   0x28/0x2c/0x30 and the DllCharacteristics pair at 0x44..0x47 sit at
    //   the SAME offsets in PE32 and PE32+ (m112: both magic values render
    //   identically), so those reads take no branch.
    let nrva = if pe32_plus {
        u32::from_le_bytes(u32_of(opt, 0x6c).ok_or(VerError::NotPE)?)
    } else {
        u32::from_le_bytes(u32_of(opt, 0x5c).ok_or(VerError::NotPE)?)
    };
    let dir_base = if pe32_plus { 0x70 } else { 0x60 };
    let linker_version = (opt[2], opt[3]);
    let os_version = u16x2_of(opt, 0x28).ok_or(VerError::NotPE)?;
    let image_version = match u16x2_of(opt, 0x2c).ok_or(VerError::NotPE)? {
        (0, 0) => None,
        v => Some(v),
    };
    let subsystem_version = u16x2_of(opt, 0x30).ok_or(VerError::NotPE)?;
    let image_base = if pe32_plus {
        u64::from_le_bytes(u64_of(opt, 0x18).ok_or(VerError::NotPE)?)
    } else {
        u32::from_le_bytes(u32_of(opt, 0x1c).ok_or(VerError::NotPE)?) as u64
    };
    // CheckSum sits at optional-header offset 0x40 in BOTH PE32 and
    // PE32+ (m112b W8: a PE32 BComp copy shows 0x0002D28D there; the earlier
    // PE32 0x3c guess read the Reserved/segment-count field, 0x400).
    let check_sum = u32::from_le_bytes(u32_of(opt, 0x40).ok_or(VerError::NotPE)?);
    let subsystem = u16::from_le_bytes([
        *opt.get(0x44).unwrap_or(&0),
        *opt.get(0x45).unwrap_or(&0),
    ]);
    let dll_characteristics = u16::from_le_bytes([
        *opt.get(0x46).unwrap_or(&0),
        *opt.get(0x47).unwrap_or(&0),
    ]);

    let pe = PeHeader {
        machine,
        time_date_stamp,
        characteristics,
        subsystem,
        dll_characteristics,
        image_base,
        check_sum,
        linker_version,
        os_version,
        image_version,
        subsystem_version,
    };

    // --- sections, then the resource directory ------------------------------
    let sec_off = pe_off + 24 + opt_size;
    let sec_count = u16::from_le_bytes([coff[2], coff[3]]) as usize;
    let sections = read_sections(bytes, sec_off, sec_count).unwrap_or_default();

    // The version INFO is optional ON TOP of the PE header: a truncated file
    // whose resource directory is unreachable still renders every PE-header
    // group (m112b W8's truncated left side shows PE 头信息 only), so a
    // resource failure returns the header-only VersionInfo instead of an
    // error.
    let resource = locate_version_resource(bytes, &sections, nrva, dir_base, opt);
    let (rsrc_off, data_rva, data_size) = match resource {
        Some(v) => v,
        None => {
            return Ok(VersionInfo {
                file_size: bytes.len() as u64,
                pe: Some(pe),
                ..Default::default()
            });
        }
    };
    let data_off = rva_to_off(&sections, data_rva, data_size)
        .unwrap_or(rsrc_off + (data_size as usize));
    let blob = &bytes[data_off..(data_off + data_size as usize).min(bytes.len())];

    let mut info = VersionInfo {
        file_size: bytes.len() as u64,
        pe: Some(pe),
        ..Default::default()
    };
    let (fixed, translation, strings) = decode_vs_version_info(blob);
    info.fixed = fixed;
    info.translation = translation;
    info.strings = strings;
    Ok(info)
}

/// Walk the resource directory (type 16 = RT_VERSION -> first name -> first
/// language) and return `(dir_offset, data_rva, data_size)`; `None` when any
/// step is unreachable (a truncated file, m112b W8).
fn locate_version_resource(
    bytes: &[u8],
    sections: &[(u32, u32, u32, u32)],
    nrva: u32,
    dir_base: usize,
    opt: &[u8],
) -> Option<(usize, u32, u32)> {
    if nrva <= 2 {
        return None;
    }
    let rsrc_rva = u32::from_le_bytes(u32_of(opt, dir_base + 2 * 8)?);
    if rsrc_rva == 0 {
        return None;
    }
    let rsrc_size = u32::from_le_bytes(u32_of(opt, dir_base + 2 * 8 + 4)?);
    let rsrc_off = rva_to_off(sections, rsrc_rva, rsrc_size)?;
    let type_entry = find_dir_entry(bytes, rsrc_off, 16)?;
    let name_dir = rsrc_off + (type_entry & 0x7fff_ffff) as usize;
    let name_entry = first_named_or_id(bytes, name_dir)?;
    let lang_dir = rsrc_off + (name_entry & 0x7fff_ffff) as usize;
    let lang_entry = first_named_or_id(bytes, lang_dir)?;
    let leaf = rsrc_off + (lang_entry & 0x7fff_ffff) as usize;
    let data_rva = u32::from_le_bytes(u32_of(bytes, leaf)?);
    let data_size = u32::from_le_bytes(u32_of(bytes, leaf + 4)?);
    Some((rsrc_off, data_rva, data_size))
}

/// The sections table, as (virtual_address, virtual_size, file_offset, raw_size).
fn read_sections(bytes: &[u8], off: usize, count: usize) -> Option<Vec<(u32, u32, u32, u32)>> {
    let mut out = Vec::with_capacity(count);
    for i in 0..count {
        let b = off + i * 40;
        if b + 40 > bytes.len() {
            break;
        }
        let vsize = u32::from_le_bytes(slice4(bytes, b + 8)?);
        let vaddr = u32::from_le_bytes(slice4(bytes, b + 12)?);
        let rawsize = u32::from_le_bytes(slice4(bytes, b + 16)?);
        let rawoff = u32::from_le_bytes(slice4(bytes, b + 20)?);
        out.push((vaddr, vsize, rawoff, rawsize));
    }
    Some(out)
}

fn rva_to_off(sections: &[(u32, u32, u32, u32)], rva: u32, _size: u32) -> Option<usize> {
    for &(vaddr, vsize, rawoff, rawsize) in sections {
        if rva >= vaddr && rva < vaddr + vsize.max(rawsize) {
            let delta = rva - vaddr;
            if delta < rawsize {
                return Some((rawoff + delta) as usize);
            }
        }
    }
    None
}

/// The resource directory entry whose id is `id` (a leaf-ish search of the
/// first level only).
fn find_dir_entry(bytes: &[u8], dir: usize, id: u32) -> Option<u32> {
    let named = u16::from_le_bytes([*bytes.get(dir + 12)?, *bytes.get(dir + 13)?]) as usize;
    let idcount = u16::from_le_bytes([*bytes.get(dir + 14)?, *bytes.get(dir + 15)?]) as usize;
    for i in 0..(named + idcount) {
        let e = dir + 16 + i * 8;
        let name = u32::from_le_bytes(slice4(bytes, e)?);
        let off = u32::from_le_bytes(slice4(bytes, e + 4)?);
        if i >= named && name == id {
            return Some(off);
        }
    }
    None
}

/// The first entry of a directory (name or id), used for the name and language
/// levels where the measured corpus always has exactly one.
fn first_named_or_id(bytes: &[u8], dir: usize) -> Option<u32> {
    let named = u16::from_le_bytes([*bytes.get(dir + 12)?, *bytes.get(dir + 13)?]) as usize;
    let idcount = u16::from_le_bytes([*bytes.get(dir + 14)?, *bytes.get(dir + 15)?]) as usize;
    if named + idcount == 0 {
        return None;
    }
    Some(u32::from_le_bytes(u32_of(bytes, dir + 16 + 4)?))
}

/// Decode `VS_VERSION_INFO`: the fixed block, the translation list and the
/// `StringFileInfo` entries.
fn decode_vs_version_info(blob: &[u8]) -> (Option<FixedInfo>, Option<String>, Vec<(String, String)>) {
    let mut fixed = None;
    let mut translation = None;
    let mut strings = Vec::new();
    if blob.len() < 6 {
        return (fixed, translation, strings);
    }
    // The 6-byte header is wLength/wValueLength/wType; the key follows, then
    // either the fixed block (when wValueLength != 0) or the children.
    let value_len = u16::from_le_bytes([blob[2], blob[3]]) as usize;
    let mut p = 6;
    // Skip the "VS_VERSION_INFO" key (UTF-16LE, NUL-terminated), then align to 4.
    p = skip_key(blob, p);
    if value_len >= 52 && p + 52 <= blob.len() {
        let b = &blob[p..p + 52];
        let _sig = u32::from_le_bytes([b[0], b[1], b[2], b[3]]);
        // dwFileVersionMS holds (minor, major) as two u16 -- the measured
        // display is major.minor.hi.lo (m112: bytes 02 00 05 00 23 7d 01 00
        // render "5.2.1.32035").
        let ms = |o: usize| (
            u16::from_le_bytes([b[o + 2], b[o + 3]]),   // major
            u16::from_le_bytes([b[o], b[o + 1]]),       // minor
        );
        let ls = |o: usize| (
            u16::from_le_bytes([b[o + 2], b[o + 3]]),   // hi
            u16::from_le_bytes([b[o], b[o + 1]]),       // lo
        );
        let (fmaj, fmin) = ms(8);
        let (fhi, flo) = ls(12);
        let (pmaj, pmin) = ms(16);
        let (phi, plo) = ls(20);
        let fv = (fmaj, fmin, fhi, flo);
        let pv = (pmaj, pmin, phi, plo);
        let file_os = u32::from_le_bytes([b[32], b[33], b[34], b[35]]);
        let file_type = u32::from_le_bytes([b[36], b[37], b[38], b[39]]);
        if _sig == 0xfeef04bd {
            fixed = Some(FixedInfo { file_version: fv, product_version: pv, file_os, file_type });
        }
        p += 52;
    }
    // Children: StringFileInfo and VarFileInfo, each a 6-byte header + key.
    while p + 6 <= blob.len() {
        let len = u16::from_le_bytes([blob[p], blob[p + 1]]) as usize;
        if len < 6 || p + len > blob.len() {
            break;
        }
        let child = &blob[p..p + len];
        let q = skip_key(child, 6);
        let key = key_at(child, 6).unwrap_or_default();
        match key.as_str() {
            "StringFileInfo" => {
                let mut r = q;
                while r + 6 <= child.len() {
                    let sub_len = u16::from_le_bytes([child[r], child[r + 1]]) as usize;
                    if sub_len < 6 || r + sub_len > child.len() {
                        break;
                    }
                    let sub = &child[r..r + sub_len];
                    let mut s = skip_key(sub, 6);
                    while s + 6 <= sub.len() {
                        let e_len = u16::from_le_bytes([sub[s], sub[s + 1]]) as usize;
                        let v_len = u16::from_le_bytes([sub[s + 2], sub[s + 3]]) as usize;
                        if e_len < 6 || s + e_len > sub.len() {
                            break;
                        }
                        let entry = &sub[s..s + e_len];
                        let kp = skip_key(entry, 6);
                        if let Some(k) = key_at(entry, 6) {
                            // wValueLength counts UTF-16 CODE UNITS, not bytes
                            // (m112b W1: CompanyName "Scooter Software" is
                            // v_len=16 and the text is 16 chars / 32 bytes).
                            let wbytes = v_len.saturating_mul(2);
                            let vbytes = &entry[kp..(kp + wbytes).min(entry.len())];
                            let v = utf16_trim_nul(vbytes);
                            strings.push((k, v));
                        }
                        s += e_len;
                        #[allow(clippy::manual_is_multiple_of)] // the 4-byte alignment walk is the measured PE rule
                        while s % 4 != 0 && s < sub.len() {
                            s += 1;
                        }
                    }
                    r += sub_len;
                    #[allow(clippy::manual_is_multiple_of)] // the 4-byte alignment walk is the measured PE rule
                    while r % 4 != 0 && r < child.len() {
                        r += 1;
                    }
                }
            }
            "VarFileInfo" => {
                let mut r = q;
                while r + 6 <= child.len() {
                    let sub_len = u16::from_le_bytes([child[r], child[r + 1]]) as usize;
                    if sub_len < 6 || r + sub_len > child.len() {
                        break;
                    }
                    let sub = &child[r..r + sub_len];
                    let s = skip_key(sub, 6);
                    if key_at(sub, 6).as_deref() == Some("Translation") && s + 4 <= sub.len() {
                        let lang = u16::from_le_bytes([sub[s], sub[s + 1]]);
                        let cp = u16::from_le_bytes([sub[s + 2], sub[s + 3]]);
                        translation = Some(format_lang_cp(lang, cp));
                        break;
                    }
                    r += sub_len;
                    #[allow(clippy::manual_is_multiple_of)] // the 4-byte alignment walk is the measured PE rule
                    while r % 4 != 0 && r < child.len() {
                        r += 1;
                    }
                }
            }
            _ => {}
        }
        p += len;
        while p % 4 != 0 && p < blob.len() {
            p += 1;
        }
    }
    (fixed, translation, strings)
}

fn skip_key(b: &[u8], mut p: usize) -> usize {
    while p + 1 < b.len() && !(b[p] == 0 && b[p + 1] == 0) {
        p += 2;
    }
    p += 2;
    #[allow(clippy::manual_is_multiple_of)] // the 4-byte alignment walk is the measured PE rule
    while p % 4 != 0 && p < b.len() {
        p += 1;
    }
    p
}

fn key_at(b: &[u8], p: usize) -> Option<String> {
    let mut end = p;
    while end + 1 < b.len() && !(b[end] == 0 && b[end + 1] == 0) {
        end += 2;
    }
    if end <= p {
        return None;
    }
    Some(utf16_trim_nul(&b[p..end]))
}

fn utf16_trim_nul(b: &[u8]) -> String {
    let mut v: Vec<u16> = b
        .chunks_exact(2)
        .map(|c| u16::from_le_bytes([c[0], c[1]]))
        .collect();
    while v.last() == Some(&0) {
        v.pop();
    }
    String::from_utf16_lossy(&v)
}

/// The measured `翻译/语言` spelling: "英语(美国), 01252  (ANSI - 拉丁语 I)"
/// (m112) or "英语(美国), UTF-16LE" (m112 V6, the UTF-16LE codepage 1200).
///
/// Only the two codepages the corpus measured are named; anything else
/// degrades to the raw numeric form rather than guessing (docs/18 §7).
pub fn format_lang_cp(lang: u16, cp: u16) -> String {
    let name = match lang {
        0x0409 => "英语(美国)",
        0x0419 => "俄语",
        0x0407 => "德语(德国)",
        _ => return format!("{:#06x}, {:#06x}", lang, cp),
    };
    match cp {
        // 0x04b0 == 1200 decimal, so this arm IS the UTF-16LE case (the
        // Windows system binaries, m112 V6); 0x04e4 == 1252 is the ANSI-Latin
        // case (both BCompare engines, m112 V1). Both spellings are measured.
        0x04b0 => format!("{name}, UTF-16LE"),
        0x04e4 => format!("{name}, 01252  (ANSI - 拉丁语 I)"), // 1252
        1251 => format!("{name}, 01251  (ANSI - 西里尔语)"),
        _ => format!("{name}, {cp:05}"),
    }
}

fn slice4(b: &[u8], i: usize) -> Option<[u8; 4]> {
    Some([*b.get(i)?, *b.get(i + 1)?, *b.get(i + 2)?, *b.get(i + 3)?])
}

fn slice8(b: &[u8], i: usize) -> Option<[u8; 8]> {
    Some([
        *b.get(i)?, *b.get(i + 1)?, *b.get(i + 2)?, *b.get(i + 3)?,
        *b.get(i + 4)?, *b.get(i + 5)?, *b.get(i + 6)?, *b.get(i + 7)?,
    ])
}

fn u16x2(b: &[u8], i: usize) -> Option<(u16, u16)> {
    Some((
        u16::from_le_bytes([*b.get(i)?, *b.get(i + 1)?]),
        u16::from_le_bytes([*b.get(i + 2)?, *b.get(i + 3)?]),
    ))
}

/// Little-endian u32 at `i`, or None when the slice is short.
fn u32_of(b: &[u8], i: usize) -> Option<[u8; 4]> {
    slice4(b, i)
}

/// Little-endian u64 at `i`, or None when the slice is short.
fn u64_of(b: &[u8], i: usize) -> Option<[u8; 8]> {
    slice8(b, i)
}

/// Two consecutive little-endian u16 at `i`, or None when short.
fn u16x2_of(b: &[u8], i: usize) -> Option<(u16, u16)> {
    u16x2(b, i)
}

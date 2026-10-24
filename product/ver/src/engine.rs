//! The measured field model (docs/18 §3/§4).
//!
//! Groups render in a fixed order -- 代码/数据, PE 头信息, 固定, 翻译, 变化
//! -- and every row's text comes from an archived cell (m112 V1..V8,
//! m112b W1..W12).  Nothing here is invented: each constant cites the probe
//! cell that pinned it.

use crate::collation::compare_key;
use crate::values;
use crate::VersionInfo;

/// The field rows of the two-column table.
pub struct Field {
    /// The group this field belongs to (0 = 代码, 1 = PE 头信息, ...).
    pub group: usize,
    /// The name text INCLUDING the box connector prefix ('+' '/' '\\' '|'),
    /// as rendered on the LEFT column.
    pub name: String,
    /// The name text for the RIGHT column; empty means "same as `name`"
    /// (m112 V5: each side's last visible row of a group takes '\\' on its
    /// own, so the prefixes can differ within one row).
    pub rname: String,
    /// The left value text (empty when the side has no value).
    pub left: String,
    /// The right value text.
    pub right: String,
    /// True when this row is a GROUP HEADER (a name with no value).
    pub is_group: bool,
    /// The comparison outcome.
    pub marker: Marker,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Marker {
    Same,
    Diff,
    /// The left side has a value, the right side is PRESENT but has none for
    /// this row (m112b W3: the right name column prints '|').
    LeftOnly,
    /// The left side is PRESENT but has no value for this row; the right side
    /// has one (m112 V5: the left name column prints '|').
    RightOnly,
    /// The right side has NO version info at all (m112 V5: the whole right
    /// half of a `+-` row stays blank).
    LeftAbsent,
    /// The LEFT side has NO version info at all (m112b W8: the left half of
    /// the 固定/翻译/变化 rows stays blank, no '|').
    LeftSideAbsent,
    /// A group header: no marker is printed.
    None,
}

/// The measured rendering locale (docs/17 §6 precedent: the labels are
/// locale parameters, the geometry rides on them).
pub struct Locale {
    pub is_zh: bool,
    /// The header labels (m112 V1: `名称`/`值`; the EN install: Name/Value).
    pub name: &'static str,
    pub value: &'static str,
    /// The five group headings.
    pub group_code: &'static str,
    pub group_pe: &'static str,
    pub group_fixed: &'static str,
    pub group_translation: &'static str,
    pub group_strings: &'static str,
    /// The file-size unit (m112: `字节` / "bytes").
    pub bytes_unit: &'static str,
    /// The row labels (docs/18 section 3; each EN form is measured on the
    /// verify/ver golden's own table -- see v-sbs-equal.txt).
    pub size_name: &'static str,
    pub os_name: &'static str,
    pub machine_name: &'static str,
    pub created_name: &'static str,
    pub flags_name: &'static str,
    pub linker_name: &'static str,
    pub image_base_name: &'static str,
    pub image_version_name: &'static str,
    pub checksum_name: &'static str,
    pub subsystem_name: &'static str,
    pub dll_flags_name: &'static str,
    pub file_version_name: &'static str,
    pub product_version_name: &'static str,
    pub file_type_name: &'static str,
    pub languages_name: &'static str,
    pub language_name: &'static str,
}

impl Locale {
    pub const ZH: Locale = Locale {
        is_zh: true,
        name: "名称",
        value: "值",
        group_code: "代码",
        group_pe: "PE 头信息",
        group_fixed: "固定",
        group_translation: "翻译",
        group_strings: "变化",
        bytes_unit: "字节",
        size_name: "\\数据",
        os_name: "+操作系统",
        machine_name: "+处理器",
        created_name: "+创建日期",
        flags_name: "+标志",
        linker_name: "+链接器版本",
        image_base_name: "+图像库",
        image_version_name: "+图像版本",
        checksum_name: "+校验",
        subsystem_name: "+用户界面",
        dll_flags_name: "\\DLL 旗帜",
        file_version_name: "+文件版本",
        product_version_name: "+产品版本",
        file_type_name: "\\文件类型",
        languages_name: "\\语言",
        language_name: "+语言",
    };

    pub const EN: Locale = Locale {
        is_zh: false,
        name: "Name",
        value: "Value",
        group_code: "Code",
        group_pe: "PE Header",
        group_fixed: "Fixed",
        group_translation: "Translation",
        // Measured on the v-sbs-equal golden (verify/ver): the PE group is
        // "PE Header" (no "Info") and the Strings group is "Variable".
        group_strings: "Variable",
        bytes_unit: "bytes",
        size_name: "\\Data",
        os_name: "+Operating System",
        machine_name: "+Processor",
        created_name: "+Creation Date",
        flags_name: "+Flags",
        linker_name: "+Linker Version",
        image_base_name: "+Image Base",
        image_version_name: "+Image Version",
        checksum_name: "+Checksum",
        subsystem_name: "+User Interface",
        dll_flags_name: "\\DLL Flags",
        file_version_name: "+File Version",
        product_version_name: "+Product Version",
        file_type_name: "\\File Type",
        languages_name: "\\Languages",
        language_name: "+Language",
    };
}

/// The summary counters (m112 V2/V4: `26 个相同项` / `16 个相同项`).
#[derive(Default)]
pub struct Counts {
    pub same: usize,
    pub diff: usize,
}

/// The zone the measured reports render timestamps in: the ORACLE HOST's
/// local zone (UTC+8, Asia/Shanghai -- every archived cell agrees, e.g. m112
/// V1's 2026-03-20 18:52:34 UTC renders 2026/3/21 2:52:34).  The engine keeps
/// the offset explicit so the crate stays hermetic.
pub const LOCAL_ZONE_SECS: i64 = 8 * 3600;

pub fn build_fields(left: Option<&VersionInfo>, right: Option<&VersionInfo>, loc: &Locale) -> Vec<Field> {
    let mut out: Vec<Field> = Vec::new();
    let lpe = left.and_then(|v| v.pe.as_ref());
    let rpe = right.and_then(|v| v.pe.as_ref());
    let any_pe = lpe.is_some() || rpe.is_some();
    let any_res = left.map(|v| v.fixed.is_some()).unwrap_or(false)
        || right.map(|v| v.fixed.is_some()).unwrap_or(false);
    // Per-side RESOURCE presence: the 固定/翻译/变化 groups come from the
    // version blob, not the PE header, so a truncated file with a header but
    // no blob renders those groups on one side only (m112b W8).
    let lres = left.map(|v| v.fixed.is_some()).unwrap_or(false);
    let rres = right.map(|v| v.fixed.is_some()).unwrap_or(false);

    if !any_pe && !any_res {
        // Both sides are non-PE (m112 V8): no groups at all -- the report is
        // just the header and the rule.
        return out;
    }

    // --- 代码 / 数据 -------------------------------------------------------
    push_group(&mut out, 0, loc.group_code, loc, left.is_some(), right.is_some());
    let size_l = left.map(|v| values::size_text(v.file_size, loc)).unwrap_or_default();
    let size_r = right.map(|v| values::size_text(v.file_size, loc)).unwrap_or_default();
    push_value_sided(&mut out, 0, loc.size_name, &size_l, &size_r, left.is_some(), right.is_some());

    // --- PE 头信息 ---------------------------------------------------------
    if any_pe {
        push_group(&mut out, 1, loc.group_pe, loc, left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.os_name,
                   &lpe.map(|p| values::os_text(p.os_version)).unwrap_or_default(),
                   &rpe.map(|p| values::os_text(p.os_version)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.machine_name,
                   &lpe.map(|p| values::machine_text(p.machine)).unwrap_or_default(),
                   &rpe.map(|p| values::machine_text(p.machine)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.created_name,
                   &lpe.map(|p| values::timestamp_text(p.time_date_stamp, LOCAL_ZONE_SECS)).unwrap_or_default(),
                   &rpe.map(|p| values::timestamp_text(p.time_date_stamp, LOCAL_ZONE_SECS)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.flags_name,
                   &lpe.map(|p| values::characteristics_text(p.characteristics, p.machine, loc)).unwrap_or_default(),
                   &rpe.map(|p| values::characteristics_text(p.characteristics, p.machine, loc)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.linker_name,
                   &lpe.map(|p| values::linker_text(p.linker_version)).unwrap_or_default(),
                   &rpe.map(|p| values::linker_text(p.linker_version)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.image_base_name,
                   &lpe.map(|p| values::image_base_text(p.image_base, values::is_pe32_plus_dummy(p), loc)).unwrap_or_default(),
                   &rpe.map(|p| values::image_base_text(p.image_base, values::is_pe32_plus_dummy(p), loc)).unwrap_or_default(), left.is_some(), right.is_some());
        // [图像版本] is present only when non-zero (m112 V6/W6).
        let has_image_version = lpe.and_then(|p| p.image_version).is_some()
            || rpe.and_then(|p| p.image_version).is_some();
        if has_image_version {
            let f = |p: &crate::parse::PeHeader| p.image_version
                .map(|(a, b)| format!("{a}.{b}")).unwrap_or_default();
            push_value_sided(&mut out, 1, loc.image_version_name,
                       &lpe.map(f).unwrap_or_default(),
                       &rpe.map(f).unwrap_or_default(), left.is_some(), right.is_some());
        }
        push_value_sided(&mut out, 1, loc.checksum_name,
                   &lpe.map(|p| values::checksum_text(p.check_sum)).unwrap_or_default(),
                   &rpe.map(|p| values::checksum_text(p.check_sum)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.subsystem_name,
                   &lpe.map(|p| values::subsystem_text(p.subsystem, p.subsystem_version)).unwrap_or_default(),
                   &rpe.map(|p| values::subsystem_text(p.subsystem, p.subsystem_version)).unwrap_or_default(), left.is_some(), right.is_some());
        push_value_sided(&mut out, 1, loc.dll_flags_name,
                   &lpe.map(|p| values::dll_flags_text(p.dll_characteristics, loc)).unwrap_or_default(),
                   &rpe.map(|p| values::dll_flags_text(p.dll_characteristics, loc)).unwrap_or_default(), left.is_some(), right.is_some());
    }

    // --- 固定 --------------------------------------------------------------
    if left.and_then(|v| v.fixed.as_ref()).is_some() || right.and_then(|v| v.fixed.as_ref()).is_some() {
        push_group(&mut out, 2, loc.group_fixed, loc, lres, rres);
        let fv = |v: Option<&VersionInfo>, k: fn(&crate::parse::FixedInfo) -> String| {
            v.and_then(|x| x.fixed.as_ref()).map(k).unwrap_or_default()
        };
        push_value_sided(&mut out, 2, loc.file_version_name,
                   &fv(left, |f| values::version_text(f.file_version)),
                   &fv(right, |f| values::version_text(f.file_version)), lres, rres);
        push_value_sided(&mut out, 2, loc.product_version_name,
                   &fv(left, |f| values::version_text(f.product_version)),
                   &fv(right, |f| values::version_text(f.product_version)), lres, rres);
        // The 固定/操作系统 text is a CONSTANT on every measured cell, but a
        // side without the resource renders NOTHING there (m112b W8's left).
        let fixed_os = if loc.is_zh { values::FIXED_OS_TEXT_ZH } else { values::FIXED_OS_TEXT_EN };
        push_value_sided(&mut out, 2, loc.os_name, fixed_os, fixed_os, lres, rres);
        let ft = |v: Option<&VersionInfo>| {
            v.and_then(|x| x.fixed.as_ref())
                .map(|f| values::file_type_text(f.file_type, loc))
                .unwrap_or_default()
        };
        push_value_sided(&mut out, 2, loc.file_type_name, &ft(left), &ft(right), lres, rres);
    }

    // --- 翻译 --------------------------------------------------------------
    let tl = left.and_then(|v| v.translation.clone()).unwrap_or_default();
    let tr = right.and_then(|v| v.translation.clone()).unwrap_or_default();
    if !tl.is_empty() || !tr.is_empty() {
        push_group(&mut out, 3, loc.group_translation, loc, lres, rres);
        push_value_sided(&mut out, 3, loc.languages_name, &tl, &tr, lres, rres);
    }

    // --- 变化 (the StringFileInfo entries) ---------------------------------
    let mut keys: Vec<String> = left.map(|v| v.strings.iter().map(|(k, _)| k.clone()).collect())
        .unwrap_or_default();
    for (k, _) in right.map(|v| v.strings.iter()).into_iter().flatten() {
        if !keys.iter().any(|x| x == k) {
            keys.push(k.clone());
        }
    }
    // The measured sort (m112 V1/V5): two tiers.  The keys WITH a localized
    // label render first in the alphabetical order of the ENGLISH key (W3:
    // Comments < CompanyName < FileDescription < ... < ProductName); the
    // remaining keys render after them, alphabetical among themselves (V1:
    // CompileDate < Subversion Revision, both after ProductVersion although
    // "C" < "F" would place CompileDate mid-list in one flat sort).
    keys.sort_by(|a, b| match (is_known_key(a), is_known_key(b)) {
        (false, true) => std::cmp::Ordering::Greater,
        (true, false) => std::cmp::Ordering::Less,
        _ => compare_key(a, b),
    });
    if !keys.is_empty() {
        push_group(&mut out, 4, loc.group_strings, loc, lres, rres);
        // The group starts with the language row (measured: 变化/语言 comes
        // first, and it repeats the 翻译/语言 text).
        push_value_sided(&mut out, 4, loc.language_name, &tl, &tr, lres, rres);
        for k in &keys {
            let get = |v: Option<&VersionInfo>| {
                v.and_then(|x| x.strings.iter().find(|(kk, _)| kk == k))
                    .map(|(_, vv)| vv.clone())
                    .unwrap_or_default()
            };
            let label = label_for(k, loc);
            let lval = get(left);
            let rval = get(right);
            // A key whose value is empty on BOTH sides renders nothing at all
            // (m112 V1/V5: DevBranch is empty everywhere and the archive has
            // no such row; W3 shows a blank value only renders when the key
            // exists with a value on one side).
            if lval.is_empty() && rval.is_empty() {
                continue;
            }
            // A KNOWN label renders its name column on every side; an
            // unknown 其它 (...) only where that side has the key.
            let known = is_known_key(k);
            let right_renders = right.map(|x| known || x.strings.iter().any(|(kk, _)| kk == k)).unwrap_or(known) && rres;
            push_value_sided(&mut out, 4, &label, &lval, &rval, lres, right_renders);
        }
    }
    // The LAST VISIBLE row of each group takes the `\` connector, PER SIDE
    // (m112 V5: the 固定 group's right side ends at 产品版本 because 文件类型
    // has no right value, and the archive renders `\产品版本` on the right
    // while the left keeps `+产品版本`).  Applied after the fact because
    // "last" is only known once the group is complete.
    fix_last_connectors(&mut out);
    out
}

fn push_group(out: &mut Vec<Field>, group: usize, text: &str, _loc: &Locale, left_present: bool, right_present: bool) {
    out.push(Field {
        group,
        // An ABSENT side renders nothing, not even the group heading
        // (m112b W8: the truncated left side shows a blank before 固定).
        name: if left_present { text.to_string() } else { String::new() },
        rname: if right_present { text.to_string() } else { String::new() },
        left: String::new(),
        right: String::new(),
        is_group: true,
        marker: Marker::None,
    });
}

fn push_value_sided(out: &mut Vec<Field>, group: usize, name: &str, left: &str, right: &str, left_present: bool, right_renders: bool) {
    // An ABSENT side renders NO value, even for constant rows (m112b W8:
    // the truncated left side shows nothing before the '-+').
    let left = if left_present { left } else { "" };
    let marker = match (left.is_empty(), right.is_empty()) {
        (false, false) if left == right => Marker::Same,
        (false, false) => Marker::Diff,
        (true, true) => Marker::Same,
        // The right side renders this row's name column: a KNOWN label always
        // prints (m112b W3: the right Comments patched empty renders `|`;
        // m112 V24: the DLL lacks LegalTrademarks and still renders `|`),
        // while an unknown `其它 (...)` prints only when that side actually
        // holds the key (m112 V5: CompileDate/Subversion stay blank).
        (false, true) if right_renders => Marker::LeftOnly,
        (false, true) => Marker::LeftAbsent,
        // The LEFT side exists but has nothing for this row -> '|' in the
        // left name column (m112 V5's 注释 row); an ABSENT left side leaves
        // the whole left half blank (m112b W8: groups 2..4 of the truncated
        // left file).
        (true, false) if left_present => Marker::RightOnly,
        (true, false) => Marker::LeftSideAbsent,
    };
    out.push(Field {
        group,
        name: name.to_string(),
        rname: String::new(),
        left: left.to_string(),
        right: right.to_string(),
        is_group: false,
        marker,
    });
}

/// The LAST VISIBLE row of each group takes the `\` connector, PER SIDE.
fn fix_last_connectors(fields: &mut [Field]) {
    // (group, side) -> index of the last row with a value on that side.
    let mut last: Vec<[Option<usize>; 2]> = Vec::new();
    for (i, f) in fields.iter().enumerate() {
        if f.is_group {
            continue;
        }
        if last.len() <= f.group {
            last.resize(f.group + 1, [None, None]);
        }
        if !f.left.is_empty() {
            last[f.group][0] = Some(i);
        }
        if !f.right.is_empty() {
            last[f.group][1] = Some(i);
        }
    }
    for per_group in last.into_iter() {
        let [l, r] = per_group;
        if let Some(i) = l {
            let f = &mut fields[i];
            f.name = with_backslash(&f.name);
        }
        if let Some(i) = r {
            let f = &mut fields[i];
            f.rname = with_backslash(if f.rname.is_empty() { f.name.as_str() } else { &f.rname });
        }
    }
}

/// The name with the connector forced to the backslash form.
fn with_backslash(name: &str) -> String {
    const BS: char = '\\';
    if let Some(rest) = name.strip_prefix('+') {
        format!("{BS}{rest}")
    } else if name.starts_with(BS) {
        name.to_string()
    } else {
        format!("{BS}{name}")
    }
}

/// Whether the StringFileInfo key has a localized label (the same table
/// `label_for` consults).
fn is_known_key(key: &str) -> bool {
    matches!(key,
        "Comments" | "CompanyName" | "FileDescription" | "FileVersion"
        | "InternalName" | "LegalCopyright" | "LegalTrademarks"
        | "OriginalFilename" | "PrivateBuild" | "ProductName"
        | "ProductVersion" | "SpecialBuild")
}

/// The localized field label for a StringFileInfo key. Unknown keys render as
/// `其它 (<Key>)` / `Other (<Key>)` (m112: `其它 (CompileDate)`,
/// `其它 (Subversion Revision)`).  Every row carries a connector prefix; the
/// plain '+' form is what `fix_last_connectors` rewrites on the last rows.
pub fn label_for(key: &str, loc: &Locale) -> String {
    let zh = match key {
        "Comments" => "注释",
        "CompanyName" => "公司名称",
        "FileDescription" => "文件描述",
        "FileVersion" => "文件版本",
        "InternalName" => "内部名称",
        "LegalCopyright" => "合法版权",
        "LegalTrademarks" => "合法商标",
        "OriginalFilename" => "原始文件名",
        "PrivateBuild" => "专用内部版本说明",
        "ProductName" => "产品名称",
        "ProductVersion" => "产品版本",
        "SpecialBuild" => "特殊内部版本说明",
        _ => "",
    };
    let en = match key {
        "Comments" => "Comments",
        "CompanyName" => "Company Name",
        "FileDescription" => "File Description",
        "FileVersion" => "File Version",
        "InternalName" => "Internal Name",
        "LegalCopyright" => "Legal Copyright",
        "LegalTrademarks" => "Legal Trademarks",
        "OriginalFilename" => "Original Filename",
        "PrivateBuild" => "Private Build",
        "ProductName" => "Product Name",
        "ProductVersion" => "Product Version",
        "SpecialBuild" => "Special Build",
        _ => "",
    };
    let base = if loc.is_zh { zh } else { en };
    if base.is_empty() {
        let name = if loc.is_zh {
            format!("其它 ({key})")
        } else {
            format!("Other ({key})")
        };
        format!("+{name}")
    } else {
        format!("+{base}")
    }
}

/// Count the same/difference fields (m112 V2/V4: "26 个相同项" /
/// "16 个相同项" + "10 个重要的差异项").
pub fn count(fields: &[Field]) -> Counts {
    let mut c = Counts::default();
    for f in fields {
        if f.is_group {
            continue;
        }
        match f.marker {
            Marker::Same => c.same += 1,
            Marker::Diff => c.diff += 1,
            Marker::LeftOnly | Marker::LeftAbsent | Marker::RightOnly | Marker::LeftSideAbsent => c.diff += 1,
            Marker::None => {}
        }
    }
    c
}

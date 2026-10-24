"""Insert the measured `version` extension mask into `vfs/src/pe.rs`.

Run from the repository root. Idempotent: refuses if the function already exists.
"""
import pathlib

p = pathlib.Path("product/vfs/src/pe.rs")
text = p.read_text(encoding="utf-8")

if "version_applies_to" in text:
    raise SystemExit("version_applies_to already present; nothing to do")

anchor = "fn is_pe(bytes: &[u8]) -> bool {"
assert text.count(anchor) == 1, f"anchor count = {text.count(anchor)}"

addition = '''/// Extensions for which BC reads a version resource (`criteria version`).
///
/// **Measured**, not inferred (`probes/U9-FINDINGS.md`): BC compares the version
/// only for these names and returns `same` for everything else — including a
/// `.cpl` (a genuine PE) and a `.txt` carrying real PE bytes. The list includes
/// the obsolete VxD formats `.vxd` and `.386`, which no "common executable
/// extensions" intuition would produce, and excludes `.efi`, `.ax`, `.tsp`,
/// `.olb` and `.vbx`, which that intuition would.
///
/// Matching is a case-insensitive comparison of the **last** extension, exactly
/// as measured: `prog.tar.exe` is compared, `probe.exe2` is not.
const VERSION_EXTENSIONS: &[&str] = &[
    "exe", "dll", "ocx", "scr", "sys", "drv", "vxd", "386",
];

/// True when BC would read a version resource for a file with this name.
///
/// The name gate is *admission*: a compared name whose content is not a PE still
/// yields a directional result when the other side has a version (u9c
/// `textonly.exe`), so callers must apply this and then read the resource,
/// rather than treating a failed read as "skip the criterion".
///
/// Only the last extension is examined, and only after the last `.` in the
/// **file name** — a dot in a directory component does not count, which is why
/// the caller passes a name and not a path.
pub fn version_applies_to(name: &str) -> bool {
    // Only the file-name portion counts; a path is reduced to its last
    // component so a dotted directory cannot admit a file.
    let file = match name.rfind(['\\\\', '/']) {
        Some(i) => &name[i + 1..],
        None => name,
    };
    let Some(dot) = file.rfind('.') else {
        // No extension at all: ignored (u9c `noext`).
        return false;
    };
    let ext = &file[dot + 1..];
    if ext.is_empty() {
        // A trailing dot means "no extension" here, and is not in the mask.
        return false;
    }
    VERSION_EXTENSIONS
        .iter()
        .any(|known| ext.eq_ignore_ascii_case(known))
}

'''

text = text.replace(anchor, addition + anchor)
p.write_text(text, encoding="utf-8")
print("inserted; new size", len(text))

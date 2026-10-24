"""Append the mask tests to `vfs/src/pe.rs` (idempotent)."""
import pathlib

p = pathlib.Path("product/vfs/src/pe.rs")
text = p.read_text(encoding="utf-8")

if "version_mask_matches_the_measured_oracle" in text:
    raise SystemExit("mask tests already present")

# Insert before the final closing brace of `mod tests`.
marker = "    #[test]\n    fn a_truncated_fixed_file_info_is_none_not_a_panic() {"
assert text.count(marker) == 1, f"marker count = {text.count(marker)}"

tests = '''    // ---------------------------------------------------------------
    // The measured extension mask (U9, `probes/U9-FINDINGS.md`)
    // ---------------------------------------------------------------

    #[test]
    fn version_mask_matches_the_measured_oracle() {
        // Compared: the six modern names plus the two VxD-era formats. The
        // latter two are the ones an intuition-based list would omit.
        for name in ["prog.exe", "lib.dll", "ctrl.ocx", "screen.scr",
                     "driver.sys", "legacy.drv", "old.vxd", "setup.386"] {
            assert!(version_applies_to(name), "{name} must be admitted");
        }
        // Ignored: real PEs the Oracle refuses (.cpl), an EFI image (.efi), and
        // every non-executable name — even when it carries PE bytes.
        for name in ["panel.cpl", "firmware.efi", "plugin.ax", "t.olb",
                     "control.vbx", "setup.msi", "command.com", "notes.txt",
                     "data.bin", "blob.dat", "archive.zip", "readme",
                     "page.html", "sheet.xls", "probe.pif", "probe.acm",
                     "probe.mun", "probe.rll", "probe.elf", "probe.so",
                     "probe.fon", "probe.fnt", "probe.prx", "probe.pyd",
                     "probe.cab", "probe.vbs"] {
            assert!(!version_applies_to(name), "{name} must be refused");
        }
    }

    #[test]
    fn version_mask_is_case_insensitive_and_takes_the_last_extension() {
        // Case-insensitive (u9 `upper.EXE`, `mixed.Dll`).
        assert!(version_applies_to("upper.EXE"));
        assert!(version_applies_to("mixed.Dll"));
        assert!(version_applies_to("Odd.ScR"));
        // The last extension decides (u9c `double.tar.exe` compared).
        assert!(version_applies_to("double.tar.exe"));
        // Exact match only: a longer extension sharing the prefix is refused
        // (u9c `probe.exe2`, `probe.dllx`, `probe.sysx`).
        assert!(!version_applies_to("probe.exe2"));
        assert!(!version_applies_to("probe.dllx"));
        assert!(!version_applies_to("probe.sysx"));
    }

    #[test]
    fn version_mask_ignores_directory_components() {
        // A dot in a directory does not admit the file (u9c `dot.dir/prog.exe`
        // is admitted because of `prog.exe`, not the directory).
        assert!(version_applies_to("dot.dir/prog.exe"));
        assert!(!version_applies_to("dot.dir/prog.txt"));
        assert!(version_applies_to("dotnonexec.dir/prog.exe"));
        assert!(!version_applies_to("dotnonexec.dir/prog.txt"));
        // Windows separators too.
        assert!(version_applies_to("dot.dir\\\\prog.exe"));
        assert!(!version_applies_to("dot.dir\\\\prog.txt"));
    }

    #[test]
    fn version_mask_handles_the_name_shape_edges() {
        // A name that is only an extension (u9c `onlyext/.exe` compared).
        assert!(version_applies_to(".exe"));
        // No extension, or a trailing dot: refused (u9c `noext`,
        // `trailingdot.`).
        assert!(!version_applies_to("noext"));
        assert!(!version_applies_to("prog."));
        assert!(!version_applies_to(""));
        // A long name is fine (u9c measured an 80-char stem).
        let long = format!("{}.exe", "n".repeat(80));
        assert!(version_applies_to(&long));
    }

'''

text = text.replace(marker, tests + marker)
p.write_text(text, encoding="utf-8")
print("tests appended; new size", len(text))

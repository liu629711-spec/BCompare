---
name: reacompare-audit-findings
description: ReaCompare architecture audit — verified facts about the current
  BCompare install, the clone prototype, golden-data provenance, and the working
  folder-report oracle recipe
metadata:
  node_type: memory
  type: project
  originSessionId: sess_7cdaae35-9b46-4d85-8685-3c40185a069a
---

Architecture audit performed 2026-10-13 for the ReaCompare project (workspace `D:\Rea`). All facts below were verified by command output, not inferred from the older reports.

**Current target binary.** `D:\BCompare\BCompare\BCompare.exe` = Beyond Compare 5.2.1.32035, 50,680,536 bytes, Scooter Software, SHA-256 `7b6033aa8b2777f5d009e4af5fd2e0ff4045c20d7fe646ac4ceb9acfb35ce762`. This is a **Chinese-localized repack** (contains `BCompare.tr`, Chinese-named `!)添删右键菜单.bat`, a 423Down.url), which localizes report output.

**Second install.** `D:\bc-official\app\BCompare.exe` = 5.2.6.32774, 50,565,160 bytes, SHA-256 `4e44c526722d6420e89b372460c519e293c417723305b83ed0eff853db16ce5d`. Clean English install. This is the binary the older reports target — it is NOT the declared project target.

**BComp.com is byte-identical between the two installs**: size 125592, SHA-256 `d8d9d88a203feb473761b54f0979520d405baf198ea2eee59833a8e1e0359cc9`. So the console oracle engine is the same file in both.

**Oracle must run in place.** Copying `BCompare.exe`/`BComp.com` to another directory breaks the license check and yields "Trial mode error / Error = 5" (exit 104). Always invoke from the real install directory.

**Golden-data provenance (resolved).** `verify/golden` (45 anchors) and `verify/layouts` (30 layouts) were captured from the **5.2.6.32774** install. Re-running both installs against the corpus: status sequences are **45/45 identical on BOTH** installs. XML is byte-identical 45/45 (stale) vs 41/45 (current); all 4 current-version differences are pure **localization strings** (`<mode>差异</mode>` vs `<mode>Differences</mode>`, `<error1>文件编码错误…` vs `File Encoding Error…`). Layout reports: 30/30 (stale) vs 5/30 (current), where the current install additionally translates data-row labels (`2 个相同行` vs `2 same line(s)`) — body-only comparison gives 25/30 with all 5 diffs being summary-layout labels. **Conclusion: the two engines are behaviourally equivalent on this corpus; the differences are localization only.**

**Report header wrapping is path-length dependent**, not install- or COLUMNS-dependent: long `Left file:`+`Right file:` paths wrap onto two lines. Comparison harnesses must hold input paths constant or normalize the header.

**Folder-compare oracle recipe (previously broken).** The existing `verify/dir/` attempt failed with exit 106 / 0 bytes because it used `folder-report ... "%1" "%2"`. Per `help/scripting_reference.html`, `folder-report` reports the **currently loaded** base folders, so a `load` command must precede it:
```
load "%1" "%2"
expand all            # include subfolders
folder-report layout:xml output-to:"%3"
```
This returns exit 0 and 2026 bytes with `expand all`. (`text-report` is the opposite — it takes its two file paths directly.)

**Folder criteria model (measured).** Default folder comparison is timestamp+size, NOT content: fixtures whose content differs (`aaaa` vs `bbbb`) report `status="same"` by default. `criteria size` → same; `criteria CRC` / `criteria binary` / `criteria rules-based` → `diff`. `criteria content` and `criteria binary-content` are invalid script criteria (exit 106). Official criteria list: `attrib:`, `version`, `timestamp[:Nsec][;IgnoreDST]`, `size|CRC|binary|rules-based`, `timezone:`, `follow-symlinks`, `ignore-unimportant`, `owner`, `group`, `permissions`.

**Clone prototype (`D:\Rea\clone`, crate `bcx`, ~660 LOC Rust).** It is explicitly a *specification validator*, not a product. Verified by running it: `cargo build` succeeds; `cargo test` runs **0 tests** (`tests/` is an EMPTY directory — the README's "45/45" refers to the Python harness, not cargo). `tools/bcx-verify.py` → **45/45 status sequences match**; `tools/bcx-layout-verify.py` → **29/30 layouts byte-match** (only `mixed-side-by-side` fails, where BC omits the marker glyph on a full-width paired line). Implemented: line splitting/encoding (CRLF≡LF≡CR≡CRCRLF, BOM equivalence, invalid-UTF-8→U+FFFD), LCS alignment with front-first duplicates and no move detection, importance normalization (whitespace always unimportant; case important in syntax-aware files, unimportant in .txt), XML report, and 6 text layouts. Not implemented: syntax tokenizer, per-element importance, 3-way merge, folder compare, any binary/table/image engine, VFS, GUI, scripting.

**Nine report commands exist** (from scripting reference), mapping 1:1 to the nine content engines: `text-report`, `folder-report`, `data-report`, `hex-report`, `table-report`, `picture-report`, `media-report`, `registry-report`, `version-report` — plus `file-report`.

**Toolchains available**: rustc/cargo 1.95.0, .NET 8.0.422, Node v24.15.0, Python 3.14.4, CMake 4.4.0. No Qt/qmake on PATH.

**Tool-output quirk**: this environment renders long hex strings as all-zero placeholders in tool output. Real SHA-256 values must be recovered in chunked form (e.g. 8-hex groups) to be read back. This affects any future evidence-capture step — do not record a hash read from a plain `sha256sum` line.

See [[rea-project-state]] for the pre-existing Ghidra/BCompare reverse-engineering workspace and [[bcompare-clone-goal]] for the earlier clone-scope assessment.

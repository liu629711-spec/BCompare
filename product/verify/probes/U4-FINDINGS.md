# U4 probe findings -- the five unlocked folder criteria (task: criteria round)

- Drivers: `probes/u4_folder_criteria.py`, `u4b_version_isolation.py`,
  `u4c_version_semantics.py`, `u4d_sizes_and_folders.py`,
  `u4e_criteria_scopes.py`, `u4f_combos.py`, `u4g_rb_iu_disagreement.py`,
  `u4h_version_pe_and_iu_alone.py`, `u4i_token_reset.py`,
  `u4j_version_inert.py`, `u4k_fixture_vs_u4j.py`
- Runs: `runs/u4-probe-*` … `runs/u4k-probe-*`
- Gate rounds that verified the implementation: `runs/A3-folder-gate-serial-05`
  (three findings), `-06` (one), `-07` (**0 fail**)
- Oracle: current install 5.0.3.30240 (zh), live `BComp.com`, folder recipe
  (`criteria …` then `load`/`expand all`/`folder-report layout:xml`), Job-Object
  containment on every call, serial.

## 1. `version` (O)

Compares the **FileVersion** of a PE's `VS_FIXEDFILEINFO`; the result is
**directional**, and it **outranks every other criterion**:

| observation | evidence |
|---|---|
| higher FileVersion on the left → `ltnewer`; on the right → `rtnewer` | u4j `v-differs` (mtimes frozen), u4k `full-fields`, serial-07 |
| equal FileVersion → `same`, even when bytes/size differ | u4k `msword-only`, serial-07 `equal.dll` |
| a **ProductVersion-only** difference is ignored | u4c `ver-product-only-field` |
| a side with NO version resource is OLDER than a side with one | u4f `f-version-pe-left`/`-right`, serial-07 `one_sided.dll` |
| two files with no version resource → `same` (no version difference) | u4c `ver-txt-files` |
| the direction outranks a SIZE difference | serial-06 → `crit-version-size` `one_sided.dll` |
| **a valid PE is required**: the `VS_FIXEDFILEINFO` signature inside a blob
without `MZ`/`PE\0\0` headers is ignored (treated as version-less) | u4h `synth-*` (all `same`) vs `real-*` (directional) |

The U4h finding is why the fixture generator now patches a **real system DLL**
(`C:\Windows\System32\version.dll`) instead of synthesizing a blob, and why
`reacmp_vfs::pe::file_version` gates on [`is_pe`] before scanning.

## 2. `owner` / `group` / `permissions` (O: inert on Windows)

The Oracle accepts all three (exit 0) and they contribute **nothing** on this
platform — the help text calls them "Unix owner/group/permissions":

* `owner-equal-files`, `group-equal-files`, `permissions-equal-files` → `same`
* `permissions-acl-differs` (an extra `deny Everyone:(R)` ACE) → **`same`**
* u4b `perm-dir-acl` (a directory deny ACE) → `same`
* u4b `owner-systemdir` / `group-systemdir` (ACL copied from a SYSTEM-owned
  file) → `same`

## 3. The criteria SET semantics (O — this corrected an A-3 model error)

**Naming ANY token clears the default size+timestamp pair.** U4i measured every
modifier-shaped token alone against a pair whose size differed by 2048 bytes
AND whose mtime differed by two hours:

| criteria | result |
|---|---|
| *(none)* | `rtnewer` (the default pair is active) |
| `timezone:ignore` | **`same`** |
| `follow-symlinks` | **`same`** |
| `attrib:z` | **`same`** |
| `ignore-unimportant` | **`same`** |
| `timestamp` | `rtnewer` (only the timestamp is compared) |
| `size` | `diff` (only the size is compared) |

So `criteria X` means "compare exactly what X names", not "start from the
default". A-3's `attrib-z-inert` case drew the right conclusion ("the pair is
replaced") from a single observation; u4i is the general rule.

Corollary: `ignore-unimportant` alone names no comparison at all, so nothing is
compared (u4h `iu-alone-real-diff` reports `same` for byte-different contents).
It only folds when a **rules-based** comparison is also named (u4e/u4f/u4g).

## 4. `ignore-unimportant` scope (O)

* Only a `rules-based` content comparison folds; `binary`/`CRC` do **not**
  (u4g `binary-iu` reports `diff` where `rb-iu` reports `same`).
* Folding covers comment-only AND whitespace-only differences, in syntax files
  **and** plain text (u4g `plain.txt`, `whitespace_only.c` → `same`), while a
  real change stays `diff` (u4e `rb-real-diff-iu`, u4f `f-iu-rb-real`).
* Under `rules-based`, a size difference does **not** short-circuit the
  comparison (u4g) — content is compared by rules, so equal-after-folding wins.

## 5. `<size>` rendering (O)

* Thousands separators: `6017` → `6,017`, `55192` → `55,192`, `5000` → `5,000`;
  values under 1000 render bare. **Not locale-dependent** (identical on the
  English reference install, u4d `size-big`).
* A zero-byte FILE renders `<size>0</size>` (u4d `size-zero`) — this settles
  the previously **U**-grade question in `dir/src/report.rs` about whether it
  is the self-closing form.
* Directory rows aggregate the whole subtree per side (`size-dir-big`), and
  directory rows carry no `status` attribute (the `<foldercomp>` wrapper's
  child rows are `<lt>`/`<rt>` plus nested `<foldercomp>`).

## Corpus impact

* `product/dir/fixtures/trees/` gained three pairs: `versioned`, `rules-based`,
  `posix-metadata` (14 pairs total).
* `product/dir/fixtures/cases.json`: 75 → **79** cases (the five
  `reject-*-not-probed` refusals are gone; nine `crit-*` cases were added).
* Gate: `A3-folder-gate-serial-05` → 3 findings, `-06` → 1, **`-07` → 0 fail**
  (75 pass + 4 info).

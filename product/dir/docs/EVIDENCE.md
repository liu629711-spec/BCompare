# M3 — folder comparison: evidence ledger

> Task A-3. Written 2026-10-13.
> This file records, claim by claim, **what was measured and what was inferred**,
> following `product/docs/02-version-and-evidence.md` section 1
> (`O` observed / `D` derived / `I` inferred / `U` unknown).

---

## 1. The honesty boundary, first

**There is no golden folder report anywhere in this workspace.** `product/verify/README.md`
section 9 says so explicitly:

> There is **no golden folder report** to compare against — the stored
> `verify/dir/reports/manifest.json` records the pre-fix failure (exit 106,
> 0 bytes) and is surfaced as historical evidence, not regenerated. The few
> folder fixtures **do not imply folder compatibility**.

and:

> Folder criteria modes (size/timestamp/CRC/binary/rules-based), timestamp
> tolerance, attributes, symlinks, deep/empty structures, `newer`/`older`/
> `orphan`/`hollow` statuses: **not covered**.

Task A-3 was additionally forbidden from invoking the Oracle, because a live
`BCompare.exe` call would corrupt its single-instance and process-tree state while
task A-2 ran.

**Therefore:**

| Claim | Status |
|---|---|
| The criteria model (default = size + timestamp, etc.) | **O** — measured by the audit; this task reproduces it |
| The XML report skeleton, byte layout, status tokens | **O** — read from the stored Oracle artifact |
| Byte-identity with the one stored Oracle report for `verify/dir/trees` | **measured by this task** (see section 4) |
| Status behaviour on every *other* fixture pair | **I/D** — the reference model, not measured against BC |
| BC parity for folder comparison overall | **NOT CLAIMED** |

The single most important number to read correctly: the fixture runner's 75/75 is
**this engine's behaviour matching its own committed expectations**, 14 of which
are anchored to real Oracle artifacts and 61 of which are derived. It is *not* a
75-case BC parity result. `product/verify/README.md` section 9's warning applies.

---

## 2. Where each artifact came from

| Artifact | Grade | Produced by |
|---|---|---|
| `tools/_audit/dir-load-expand-report.xml` | **O** | the audit's Oracle probe (`probe-dir-oracle.py`), read-only |
| `tools/_audit/dir-load-then-report.xml` | **O** | the same probe without `expand all` |
| `product/verify/runs/A1-final/raw/folder-current-trees.xml` | **O** | task A-1's harness run |
| `product/docs/00-current-state.md` section 6 | **O** | the audit's criteria probe |
| `extracted/pseudocode/140fd1e90.c` | **D** | decompiler output for the folder-report XML writer (`DlgDirReport.pas`); not original source |
| `extracted/string-function-index.tsv` | **D** | string→function attribution |
| `specs/dir/DirTree.md` | **D** | reverse-engineering spec; carries its own confidence labels |
| `help/*.html` | **O** | the shipped help, consistent with the target version |
| This task's fixtures, engine, reports | **own work** | `D:\Rea\product\dir`, `D:\Rea\product\vfs` |

`product/docs/02-version-and-evidence.md` section 7 rule 6 is respected:
`extracted/pseudocode/*.c` is decompiled output, and no claim in this task says
otherwise.

---

## 3. Evidence per implemented behaviour

### 3.1 The criteria model — **O**

`product/docs/00-current-state.md` section 6 records the criteria probe against
BCompare 5.2.1.32035. With `diff.txt` = `aaaa` vs `bbbb` (same size, same
timestamp):

| criteria | verdict | implemented as |
|---|---|---|
| default (none) | `same` | `ContentCriteria::Size` + `Timestamp` (`Criteria::default`) |
| `size` | `same` | `ContentCriteria::Size` |
| `timestamp` | `same` | `ContentCriteria::Timestamp` |
| `CRC` | `diff` | `ContentCriteria::Crc` |
| `binary` | `diff` | `ContentCriteria::Binary` |
| `rules-based` | `diff` | `ContentCriteria::RulesBased` |
| `content`, `binary-content` | exit 106 | `CriteriaError::InvalidCriteria`, `exit_code() == 106` |

The default is **not** a content comparison. `Criteria::observed_default()`
encodes this, and `tools/make_cases.py::_validate_observed_anchors` re-checks the
whole table against the stored artifacts every time the manifest is regenerated.

### 3.2 The report status vocabulary — **O**

Six tokens, from two independent sources:

* observed output: `same` (80), `ltonly` (20), `rtonly` (20) occur across the
  stored runs (`grep -ho 'filecomp status="[a-z]*"' product/verify/runs/*/raw/*.xml`);
* the writer's string table and code: `FUN_140fd1e90` owns the literals `ltnewer`,
  `rtnewer`, `ltonly`, `rtonly`, `same`, `diff`
  (`extracted/string-function-index.tsv` lines 11893-11896) and switches on a
  status byte (`extracted/pseudocode/140fd1e90.c`).

`Status::xml_token` emits exactly those six and returns `None` for `Unknown`, so
the writer **refuses** rather than inventing a token.

**Deliberately not implemented:** `leftolder`, `rightolder`, `orphan` and
`conflict` appear in `product/verify/harness/normalize.py::KNOWN_FILECOMP_STATUS`
but have never been observed in output and are absent from the writer's string
table. They are not emitted. (`orphan` does exist in the binary but belongs to
`FUN_1417d1d20`, not to the folder-report writer —
`extracted/string-function-index.tsv` line 18039.)

**Also out of scope:** `DirHollow` and `DirFiltered` are real `DlgDirReport`
status names (**O**: `extracted/pseudocode/140fccbf0.c`), but "hollow" is a
*scan-in-progress* state, not a comparison result:

> Folders may appear hollow when you first start the comparison. This happens when
> the background scanning process has not yet completed those folders.
> — `help/dir_understanding_the_display.html`

A completed read-only batch comparison has nothing scanning, so neither can occur.

### 3.3 The XML report structure — **O**, element by element

Byte-level facts taken from `tools/_audit/dir-load-expand-report.xml`:

| Fact | Evidence |
|---|---|
| UTF-8 BOM `EF BB BF` first | first 3 bytes |
| `<?xml version="1.0" encoding="utf-8"?>` then CRLF | bytes 3..39 |
| `<bcreport created="YYYY/MM/DD HH:MM:SS">` | line 2 |
| one tab per nesting level | `\t<foldercomp>` at offset 0x8C |
| CRLF throughout, trailing CRLF at EOF | 88 CRLF, 88 LF, file ends `0d 0a` |
| root `<foldercomp>` holds `<ltpath>` then `<rtpath>` | lines 3-5 |
| a subdirectory is a nested `<foldercomp>` | lines 6-36 |
| a file is `<filecomp status="…">` | lines 37-48 |
| a one-sided row omits the missing side entirely | lines 49-62 |
| `<size/>` empty for an unexpanded directory, numeric once expanded | `dir-load-then-report.xml` vs `dir-load-expand-report.xml` |
| `<modified>` is local wall clock | see 3.4 |

This task's writer reproduces all of it. See section 4 for the verification.

`<mode>`, `ignoreunimportant`, `filters` and `advfilters` exist in the binary
(**O**: strings owned by `FUN_140fd2340`) but are **absent from every stored
report**, so when BC emits them is **U**; this task does not emit them.

### 3.4 Timestamp rendering is local wall clock — **O → D**

The report shows `2026/10/13 10:06:12`. Reading the fixture's own metadata:

```
$ python -c "import os,datetime;st=os.stat(r'verify/dir/trees/L/diff.txt');
             print(datetime.datetime.fromtimestamp(st.st_mtime))"
2026-10-13 10:06:12      # local, UTC+08:00 on this host
2026-10-13 02:06:12      # the same instant in UTC
```

The report matches **local**, not UTC. So rendering applies the local offset; the
offset actually used is recorded on every comparison
(`FolderComparison::offset_minutes`) and printed by the CLI as the criteria
provenance. When the offset is unknown it stays `None` and the report does not
claim local accuracy.

### 3.5 Report ordering — **D**

The observed report lists `emptydir`, `sub`, then `diff.txt`, `leftonly.txt`,
`rightonly.txt`, `same.txt`, `samesize.bin`. `diff.txt` sorts before `emptydir`
ordinally, so directories are **not** interleaved with files: directories first,
then files, each name-sorted. `sort_entries` implements that.

Whether the sort is ordinal or a natural/case-insensitive collation is **U**
(one sample cannot distinguish them) — see U-M3-6.

### 3.6 Directory size and status — **O** structure, **I** for the aggregate rule

Observed: an unexpanded directory renders `<size/>`; after `expand all` the same
directory renders `<size>3</size>` and an empty one `<size>0</size>`. Observed
help:

> Generally, these criteria are used to compare files, and not folders directly.
> For instance, a folder's timestamp does not affect the comparison. A folder is
> classified as "newer" if it contains newer files. Folders are compared by
> aggregating the comparisons of files within them.
> — `help/dir_how_to_compare.html`

So a directory's status is an aggregate and never its own timestamp. Whether the
reported size sums the whole subtree or only immediate children is **U** (the
sample's `sub` has one file and no nested directory); this implementation sums the
whole subtree — U-M3-7.

### 3.7 The kind-conflict rule — **I**

A name that is a file on one side and a directory on the other is reported `diff`
and written as a `<filecomp>` row (it cannot be expanded). No Oracle report
containing a kind conflict exists here, so both halves of that choice are this
project's **inference**, grounded in `extracted/pseudocode/140f4b8b0.c`, which
records the comparison core returning its code 9 ("different") for the
mismatched-kind arm. U-M3-8.

### 3.8 `criteria rules-based` is byte equality — **explicitly partial**

The per-format importance rules that `rules-based` implies are M2 work
(`product/docs/04-milestones.md` M2.2/M2.3) and are **not implemented**. The
criterion is evaluated as byte equality and every such comparison carries
`ComparisonNote::RulesBasedTextRulesNotImplemented`, which is rendered into both
text layouts. The limitation travels with the output instead of living only in a
document.

### 3.9 Criteria that are documented but not implemented — **refused, not faked**

`version`, `owner`, `group`, `permissions` and `ignore-unimportant` are documented
by `help/scripting_reference.html` (**O**) but have not been probed in this
workspace. `Criteria::parse` returns `CriteriaError::NotProbed` for each, which
`product/docs/04-milestones.md` section 5 requires ("只实现已对拍的模式，报告中列出
未支持项"). They are not silently accepted and not approximated.

---

## 4. What this task measured itself

### 4.1 Byte-identity with the one stored Oracle report

Running this engine over the read-only audit tree pair
(`D:\Rea\verify\dir\trees\L` vs `R`) under the default criteria, with the
wall-clock `created` attribute removed, produced output **byte-identical** to
`tools/_audit/dir-load-expand-report.xml`:

```
$ python tools/verify_against_oracle_xml.py
oracle report : D:\Rea\tools\_audit\dir-load-expand-report.xml
  bytes       : 2026 raw
  BOM present : True
local engine  : D:\Rea\product\dir\target\oracle-parity-check.xml
  bytes       : 1996 raw
  BOM present : True

PASS: byte-identical to the observed Beyond Compare folder report
      (one tree pair, default criteria — NOT a general parity claim)
```

The reports differ in raw length only by the length of the `created` attribute,
which is the generation wall-clock and is deliberately not compared. Both begin
with the UTF-8 BOM, which is itself an observed property of the Oracle's output.

This is the strongest claim in this task and it is deliberately scoped: it is
**one** tree pair, under **one** criteria setting, against the **one** stored
Oracle folder report that exists. It is not evidence of general parity.

Reproduce with `tools/verify_against_oracle_xml.py`.

`created` is omitted by default so a report is byte-reproducible; pass
`--created "2026/10/13 14:17:16"` to emit the attribute.

### 4.2 Two independent Oracle artifacts agree

`tools/make_cases.py::_validate_observed_anchors` reads **both** stored Oracle
reports (`tools/_audit/dir-load-expand-report.xml` and
`product/verify/runs/A1-final/raw/folder-current-trees.xml`) with an independent
parser and requires them to yield the same status map — they do:

```
{'emptydir': 'rtonly', 'sub': 'same', 'sub/inner.txt': 'same', 'diff.txt': 'same',
 'leftonly.txt': 'ltonly', 'rightonly.txt': 'rtonly', 'same.txt': 'same',
 'samesize.bin': 'same'}
```

It then requires the Python reference model to reproduce that map, and requires
the criteria table of section 3.1. A negative control was run: forcing the
reference model's default to a content criterion produced 5 problems and refused
to regenerate the manifest.

### 4.3 Two independent implementations

`tools/make_cases.py::ref_compare` is a second implementation of the comparison,
in Python, reading the same files with `os`/`stat`. The fixture runner checks the
Rust engine against it. A transcription slip in either shows up as a
disagreement. This is how four real engine defects were found during this task
(see section 6).

---

## 5. Unknowns — what would settle each

| ID | Unknown | Current handling | What would settle it |
|---|---|---|---|
| **U-M3-1** | The exact trigger boundary for `ltnewer`/`rtnewer` vs `diff` | implemented as: timestamp-only difference to `ltnewer`/`rtnewer`, any other difference to `diff` | `folder-report` over a pair differing only in mtime, and one differing in both mtime and content |
| **U-M3-2** | Whether a difference of exactly `N` seconds is inside a tolerance of `N` | implemented as inside (`diff <= tolerance`) | `criteria timestamp:2sec` over files 2 s apart |
| **U-M3-3** | Whether a single-digit hour renders `9:06:12` or `09:06:12` | always two-digit `%02d` | any report whose mtime has a single-digit hour |
| **U-M3-4** | The direction `timezone:left+N` shifts, and what `timezone:ignore` suppresses | left shift is `+N` hours on the left timestamp; `ignore` suppresses whole-hour differences | `folder-report` with `timezone:left+1` over a 1 h difference |
| **U-M3-5** | Whether entry-name comparison is case-insensitive, and its default | ordinal by default; `CompareOptions::case_insensitive_names` exists | `folder-report` over a pair differing only in name case (needs a case-sensitive filesystem) |
| **U-M3-6** | Whether the report sort is ordinal or natural/collation-aware | ordinal | a report containing names such as `a2` and `a10` |
| **U-M3-7** | Whether a directory's reported size sums the whole subtree or immediate children only | whole subtree | a report containing a directory with a nested directory and files at both levels |
| **U-M3-8** | How BC represents a file-vs-directory kind conflict | `diff` in a `<filecomp>` row | a report over a pair with a name conflict |
| **U-M3-9** | When BC emits `<mode>`, `ignoreunimportant`, `filters`, `advfilters` | not emitted | any report produced with a non-default mode, an ignoreunimportant setting, or filters |
| **U-M3-10** | Whether an unfollowed symlink is compared by target text | yes, and the inapplicability is recorded | a report over a pair of links |
| **U-M3-11** | Whether `<size/>` (self-closing) is also used for a zero-byte **file** | emits `<size>0</size>` for a file | a report containing a zero-byte file |
| **U-M3-12** | The exact text-layout formats (`side-by-side`, `summary`) | not imitated: both layouts state "NOT byte-compatible" in their own output | any stored text-layout folder report |

The CLI's `--help` and the report headers name the unimplemented items, per
`product/docs/05-acceptance-strategy.md` section 6 checks 3 and 4.

---

## 6. Defects this task found and fixed

Each was found by a failing test or a fixture, not by inspection. They are listed
because they show what the verification was actually worth.

| # | Defect | How it surfaced | Fix |
|---|---|---|---|
| 1 | A forward-slash root path failed with `os error 123` | CLI smoke test on `D:/Rea/...` | `\\?\` requires backslashes; separators are converted on the private syscall path only |
| 2 | A **relative** root silently produced an **empty** comparison | fixture runner: 12 cases "passed" comparing nothing | `\\?\` needs a fully qualified path; relative roots are resolved against the CWD. Regression test added |
| 3 | A file-vs-directory name collision was reported `diff` but written as an expandable `<foldercomp>` | fixture runner | `TreeNode::is_dir_row` decides the row type separately from `is_dir` |
| 4 | A link-vs-file collision returned `Unknown`, so the XML writer refused | fixture runner, exit 106 | kind conflict now covers **any** differing kind |
| 5 | Attribute comparison was all-or-nothing: two entries that each lacked *all* of a set compared equal | `attrib-*` fixtures | compared per attribute (`Attributes::compare_selected`) |
| 6 | A `[[`-style shallow dict copy in the fixture generator made both sides of the `deep` pair identical | 13 nested rows came out `same` | a factory function builds each side independently |
| 7 | `_is_junction` returned false for an existing junction, so `--check` tried to recreate it | `make_fixtures.py --check` | probe the reparse-point attribute bit |
| 8 | Junction targets resolved one directory too high | `--check` reported "target does not exist" | target is a sibling inside the same side's tree |
| 9 | The runner compared XML-escaped names to literal manifest names, so `amp&name.txt` looked missing | `names` fixture | `unescape_xml` in the runner |
| 10 | **`make_fixtures.py --check` could never detect drift**: it regenerated the trees *before* comparing digests, so writing made the digests agree by construction | negative control: tampering an mtime did not fail `--check` | `check()` now reads only, comparing each tree against both the recorded digest and the digest the current spec implies |
| 11 | `rglob` **descends through a junction**, adding a `<junction>/inside.txt` row per link so the `links` digests could never match | the new `--check` reported `links/L` and `links/R` | `os.scandir` with `follow_symlinks=False`, so a junction is one row and is not traversed — which is also how the engine reads it |
| 12 | `trailing.dot.` is created on disk as `trailing.dot` (Windows strips a trailing dot), so the spec and the tree disagreed | the new `--check` reported `names/L` and `names/R` | the fixture uses the name Windows stores; round-tripping an arbitrary given name is covered by unit tests instead |
| 13 | Junction mtimes cannot be stamped on this platform (`os.utime(..., follow_symlinks=False)` raises `NotImplementedError`), so recording the real value made the digest unstable | `--check` on `links/*` | a junction's row records mtime `0` on both the spec and disk sides, since it is not a compared property |

Three negative controls were run against the corrected `--check` and all three now
fail it as they should: tampering a file's mtime, deleting a fixture file, and
editing a fixture *definition* without regenerating.

Two further errors were mine in the test data, not in the code: wrong epoch
seconds for a known instant, and a wrong expectation about which side is "newer".
Both were corrected by computing the value rather than adjusting the assertion.

---

## 7. Reproducing everything in this document

```bash
cd D:\Rea\product\vfs  && cargo test                        # M3.1
cd D:\Rea\product\dir  && cargo test                        # M3.2-M3.5

cd D:\Rea\product\dir
python tools/make_fixtures.py          # create/refresh the 11 tree pairs
python tools/make_fixtures.py --check  # verify the corpus has not drifted
python tools/make_cases.py             # rebuild the manifest (re-checks the O anchors)
python tools/compare_fixtures.py       # run all 75 cases
python tools/compare_fixtures.py --verbose --emit-reports D:\temp\reports
python tools/verify_against_oracle_xml.py   # the byte-identity check of section 4.1
```

`compare_fixtures.py` refuses to run when the corpus or its expectations have
drifted from the artifacts they came from; pass `--skip-staleness-check` to
override. Both refusal paths were tested with negative controls.

## 8. Platform limits on what a corpus here can express

Three constraints were measured while building the corpus. They are recorded
because they bound what a Windows fixture set can cover, and because each one
initially looked like an engine bug.

| Limit | Measurement | Consequence |
|---|---|---|
| File names cannot contain `< > : " / \ \| ? *` | writing `lt<gt>.txt` raises `OSError: [Errno 22] Invalid argument` | XML-escaping coverage uses `&` (the case that matters: an unescaped `&` makes the report unparseable) and the single quote; `<`/`>` can only be covered at the string level |
| A trailing dot is stripped | the spec name `trailing.dot.` lands on disk as `trailing.dot` | the fixture uses the stored name |
| Creating a symbolic link needs `SeCreateSymbolicLinkPrivilege` | `os.symlink` raises `WinError 1314` on this host | link coverage uses **NTFS junctions**, which need no privilege and which the documented `follow-symlinks` names explicitly ("symbolic links and NTFS junctions") |


---

## 9. Round-2 addendum -- the serial Oracle gate (2026-10-13)

After this ledger was written, the project lead ran a serial live-Oracle gate
over the whole corpus (`tools/_audit/a3-folder-gate.py`; acceptance record in
`product/verify/runs/A3-folder-gate-serial-04/REPORT.md`). Round 1 found 21
divergences; round 2 fixed the engine against them and the final gate is
**75 cases = 66 pass + 9 documented divergences + 0 fail, with 49/49 xml
reports byte-identical to the live Oracle**.

Unknowns SETTLED by the gate (upgraded from the sections above):

| ID | Settled answer |
|---|---|
| U-M3-2 | a difference of exactly N seconds is INSIDE a tolerance of N (diff <= N) |
| U-M3-3 | month/day/hour render UNPADDED, minute/second two-digit |
| U-M3-4 | `timezone:left/right±N` is REJECTED by the script command (exit 106); `timezone:ignore` suppresses whole-hour differences |
| U-M3-6 | rows sort with digit runs NUMERIC and the first differing position LINGUISTIC case-insensitively; `CompareStringW` rejects `SORT_DIGITSASNUMBERS` (measured) |
| U-M3-7 | a directory's `<size>` is the whole-subtree file-byte sum, PER SIDE |
| U-M3-8 | a kind conflict emits TWO one-sided rows (expanded dir + file), never one merged `diff` |
| U-M3-10 | an unfollowed junction renders its own mtime and `<size>0</size>`; differing targets are `diff` under default criteria |
| U-M3-12 | BC text-layout folder reports now EXIST as archived samples (`oracle/*.out`); byte-compat for them is still not modelled |

NEW observed facts (beyond the original unknown list):

* `criteria attrib:z` is accepted (exit 0): unknown attribute letters are
  inert; naming an attribute set REPLACES the default size+timestamp pair.
* A content criterion (CRC/binary/rules-based) REPLACES the attribute
  comparison (`attrib:h CRC` judges a hidden-bit difference `same`).
* BC ACCEPTS `criteria version / owner / group / permissions /
  ignore-unimportant` (exit 0, full reports). The engine's not-probed refusal
  is a documented divergence pending implementation; the archived reports in
  the gate run are their spec.

The manifest validator (`make_cases.py` check 4) now anchors every xml case of
the gate run against the reference model, so a corpus regeneration cannot
drift from measured BC behaviour.

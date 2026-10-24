# `product/verify/` — unified Oracle verification harness (task A-1 / M0)

Black-box comparison of Beyond Compare installs and of candidate CLI
implementations, against the existing golden corpora. This directory is the
**only** thing task A-1 owns; it writes nowhere else.

> **Status:** M0 acceptance gate met (see `runs/A1-final/REPORT.md`). Previous
> baseline: **M111-gate-01 1018/1035** (registry channel, docs/17); the M112
> version channel adds 25 `verify/ver/` goldens (English-authored) + norm-6
> + the reacmp `version-report` replay — see docs/18 and
> `product/docs/12-maintenance-regression.md` for the refreshed baseline
> table. The registry 17 non-passes are the Chinese install's side-by-side
> TABLE lines: that geometry is locale-dependent (the column floors are the
> header-label widths), the goldens are the English form the product
> renders, and the Chinese geometry is locked by `reacmp-reg`'s own
> 103-table corpus instead (docs/17 §6/§9). The version channel reproduces
> the same shape (docs/18 §8): 19 sbs geometry non-passes + the recorded
> U-ver-1 size row.

---

## 1. Install identity (measured, not assumed)

Version identity is read **from the binaries**, in-process, with no external
tool. Hashes are emitted in 8-hex-digit groups because this environment renders
long contiguous hex strings as an all-zero placeholder
(`product/docs/00-current-state.md` section 7).

| | current (project target) | reference (label reference only) |
|---|---|---|
| Oracle `BComp.com` | `D:\BCompare\BCompare\BComp.com` | `D:\bc-official\app\BComp.com` |
| Oracle version | `5.0.3.30240` | `5.0.3.30240` |
| Oracle sha256 | `d8d9d88a 203feb47 3761b54f 0979520d 405baf19 8ea2eee5 9833a8e1 e0359cc9` | **identical** |
| Engine `BCompare.exe` | `D:\BCompare\BCompare\BCompare.exe` | `D:\bc-official\app\BCompare.exe` |
| Engine version | `5.2.1.32035` | `5.2.6.32774` |
| Engine sha256 | `7b6033aa 8b2777f5 d009e4af 5fd2e0ff 4045c20d 7fe646ac 4ceb9acf b35ce762` | `4e44c526 722d6420 e89b3724 60c519e2 93c41772 3305b83e d0eff853 db16ce5d` |
| Locale | `zh` — `BCompare.tr` present (439,296 bytes) | `en` — no `BCompare.tr` |

Two consequences the harness depends on:

1. **The Oracle is the same binary in both installs.** Version differences come
   from `BCompare.exe`, the engine host. So a report difference between installs
   is an engine difference, not an Oracle difference.
2. The current install is a **Chinese repack**. It translates report *labels*.
   The harness normalizes only confirmed label pairs and corroborates every pair
   by running the reference install on the same fixtures (`labels` suite).

The harness prints this table (`--identity-only`) and writes it to
`runs/<run>/install-identity.json`.

---

## 2. Execution flow

```
run_cli  ->  installs.discover()            measure version/hash/locale
         ->  manifests.load_*()             read the read-only fixtures
         ->  oracle.write_script()          script under runs/<run>/scripts/
         ->  oracle.run()                   BComp.com /silent @script L R OUT
         ->  normalize.normalize_*()        structural comparison key
         ->  verdict + report               runs/<run>/REPORT.md + report.json
```

### Oracle recipes (both verified in this workspace)

**Text** — `text-report` takes the two file paths directly as `%1`/`%2`:

```
BComp.com /silent @<script> <left> <right> <output>
script: text-report layout:<layout> [options:<options>] output-to:"%3" "%1" "%2"
```

**Folder** — `folder-report` reports the *currently loaded* base folders, so
`load` **must** come first. Without it the exit code is 106 and the report is
0 bytes (this is the pre-existing `verify/dir/reports/manifest.json` failure):

```
script: load "%1" "%2"
        expand all
        folder-report layout:xml output-to:"%3"
```

### Two hard rules the code enforces

* **Run in place.** The Oracle is always started with `cwd` set to its own
  install directory and is never copied. Relocating `BCompare.exe`/`BComp.com`
  triggers `Trial mode error ... Error = 5` and exit 104.
  `oracle.FATAL_EXITS` treats 104 as fatal: the install's probing is aborted
  rather than recorded 45 times.
* **Write scope.** See section 3a below.

### 3a. Process-tree containment (why the Oracle runs inside a Job Object)

`BComp.com` is a **launcher stub**: it spawns `BCompare.exe` as a GUI host,
which is its **grandchild**. Measured in this workspace:

```
BComp.com pid=31788  ->  BCompare.exe pid=38160   (same cmdline + /BCompWnd=)
```

A plain `subprocess.run(cmd, timeout=...)` kills only the direct child on
timeout, which caused two coupled defects:

1. **Orphan.** The grandchild `BCompare.exe` survived the kill. Because
   BCompare.exe is single-instance, a leftover host can adopt later invocations.
2. **Unbounded wait.** The orphan inherits the `stdout`/`stderr` pipes.
   `subprocess.run` drains those pipes after killing the child, and that drain
   blocks until every writer closes them — i.e. **forever** if the orphan is
   showing a modal dialog. This is what stalled the acceptance run for ~20
   minutes; no Python-side timeout could reclaim it.

Measured before the fix (killing only the direct child mid-comparison):

```
before:                          []
mid-flight:                      ['31788 BComp.com', '38160 BCompare']
killed direct child only
AFTER:                           ['38160 BCompare']      <- ORPHAN LEAKED
```

**Fix.** The Oracle now runs inside a Windows **Job Object** with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (`harness/oracle.py::ProcessTree`).
Children of a job member inherit job membership, so assigning the launcher is
enough to own the grandchild; closing the job handle terminates the whole tree
in the kernel. The process is created `CREATE_SUSPENDED` and resumed only after
assignment, closing the race where the launcher could spawn its child first.
The job is closed on **every** exit path — success, error and timeout — so
nothing survives a call. The post-timeout pipe drain is additionally bounded
(10 s) as defence in depth.

A Job Object was chosen over `taskkill /T` because a Job Object costs nothing
per call: killing 257 invocations via `taskkill` or a PowerShell `Get-CimInstance`
sweep (measured **0.49 s per call**) was not affordable.

Measured after the fix:

```
before:                          []
timed_out=True tree_killed=True containment=job-object elapsed=0.612s
AFTER timeout:                   []                      <- reaped
```

`OracleRun.containment` and `OracleRun.tree_killed` record this per result, so a
run's report shows whether containment was active rather than assuming it.

### 3b. Write scope

`runner.assert_writable` is an **allow-list inversion**, applied in this order:

1. the target must resolve under a writable root — the configured
   `results_dir` when the caller supplies one, else
   `DEFAULT_WRITABLE_ROOT` (`D:\Rea\product\verify\runs`). Anything outside is
   refused, including directories that do not exist yet and therefore could not
   appear in any deny-list;
2. it must not fall inside a `READ_ONLY_ROOTS` tree;
3. it must not match `READ_ONLY_FILE_PATTERNS` (currently `D:\Rea\report-*.md`,
   a glob so a newly written report file is protected without a code change);
4. inside `product\verify` only `runs\` may be written, so the harness cannot
   overwrite its own source or tests.

Rules 2–4 are defence in depth: a mis-configured results root pointed at, say,
`verify\golden` is refused by rule 2 rather than honoured. Each refusal names
the rule that fired:

```
refusing to write outside the writable results tree: ...
refusing to write inside read-only asset tree: ... (protected: ...)
refusing to write read-only file: ...
refusing to write inside the harness source tree: ...
```

Covered by `READ_ONLY_ROOTS`: `verify`, `clone`, `extracted`, `specs`, `tools`
(including `tools\_audit\`), `ghidra-project`, `help`, `rea-snapshot`,
`product\docs`, `D:\BCompare`, `D:\bc-official`.

---

## 3. Exit statuses

Observed and encoded in `harness/oracle.py::EXIT_MEANINGS`:

| Exit | Meaning | Observed by |
|---|---|---|
| 0 | success | every passing case |
| 104 | licensing / trial error — **the Oracle was relocated** | fatal, aborts the install |
| 105 | script error | not reproduced in this run |
| 106 | script command error — e.g. `folder-report` without `load`, or an unknown layout name | `test_folder_report_without_load_fails_with_106`, `test_bad_layout_name_exits_106` |
| 107 | file not found / argument error | `test_missing_input_file_exits_107` |

Test verdicts are a **separate, disjoint** taxonomy
(`harness/taxonomy.py::Verdict`): `pass`, `fail`, `error`, `missing_output`,
`timeout`, `unparseable`, `not_run`. Only `pass` counts as a pass.
`summarize()` reports `pass_rate_of_compared` separately from
`pass_rate_of_total`, and `pass_rate_of_compared` is `None` when nothing was
compared — an all-error run reports no rate at all rather than 0% or 100%.

---

## 4. Normalization boundaries

Rule set version: **`norm-1`** (`harness/normalize.py::RULESET_VERSION`),
recorded on every result and in every run header. Two runs are only comparable
when their rule-set versions agree.

### What is normalized (complete list)

| Kind | Source (as emitted) | Normalized to |
|---|---|---|
| xml label | `<mode>差异</mode>` | `<mode>Differences</mode>` |
| xml label | `<mode>相同</mode>` | `<mode>Same</mode>` |
| xml label | `<mode>差异, 带上下文</mode>` | `<mode>Differences, With Context</mode>` |
| xml label | `<error1>文件编码错误 (第 N 行)</error1>` | `<error1>File Encoding Error (Line N)</error1>` — **N preserved** |
| text label | `文本比较(T)` | `Text Compare` |
| text label | `已产生：` | `Produced:` |
| text label | `模式：  全部` | `Mode:  All` |
| text label | `源文件,比较文件,I最初,…` | `SourceFile,CompareFile,IOriginal,…` |
| text count | `N 个相同行` | `N same line(s)` — **N preserved** |
| text count | `N 个不重要的差异行` | `N unimportant difference line(s)` |
| text count | `N 个重要的左边独有行` | `N important left orphan line(s)` |
| text count | `N 个重要右边独有行` | `N important right orphan line(s)` |
| text count | `N 个重要差异行` | `N important difference line(s)` |
| text count | `N 个差异部分` | `N difference section(s)` |
| text header | `左边文件： P    右边文件： Q` | `Left file: P Right file: Q` — paths preserved, padding collapsed |
| text header | header wrapped onto 2 lines | re-joined onto 1 line |
| volatile | `已产生： <ts>` / `Produced: <ts>` | `Produced: TIME` |
| volatile | `created="<ts>"` | `created="TIME"` |
| structural | SsXML `&#1;`/`&#7;`/`&#26;`/`&#0;` | round-tripped through a PUA escape so a conforming XML parser accepts it, then restored **verbatim** |

The Chinese count-label table is deliberately **incomplete**: the repack's own
translation is inconsistent (`重要的左边独有行` carries `的` but
`重要右边独有行` does not). Unobserved variants are *not* guessed — they raise
`unknown_count_label` so the table is extended from evidence.

### What is explicitly NOT normalized

* `linecomp/@status` — validated against the observed vocabulary, never rewritten.
* `ltid` / `rtid` line numbers.
* left/right `<text>` content, including tabs, control characters and emoji.
* element ordering.
* any text-layout body line, diff marker, separator, `<`/`>` prefix or line number.
* `Left file:` / `Right file:` **paths** (only the label and inter-field padding move).

### Refusals instead of guesses

`NormalizerRefusal` is raised — and mapped to the `unparseable` verdict — for an
unknown XML tag or attribute, an unknown `linecomp`/`filecomp` status value, an
unknown `<mode>` or `<error1>` label, an unknown Chinese count label, malformed
XML, an unexpected timestamp format, and any report that is neither a
`<?xml`/`<bcreport` document nor plain text. Nothing is deleted silently.

### Traceability

Both the **raw** report (`runs/<run>/raw/`) and the **normalized** report
(`runs/<run>/normalized/`) are kept for every case, and each result lists
`rules_applied` — so any changed comparison outcome can be traced to the exact
rule that changed it.

### Byte-faithful reading

Reports are read with `normalize.read_report`, which decodes raw bytes. This is
deliberate: `Path.read_text` applies universal-newline translation, which would
turn a CRLF report into LF and could hide a real line-ending difference.

### Reconciling with the audit's independently reported figures

Every run's report contains a "Layout agreement" table with three levels. On the
`A1-final` run these are:

| version | subject | normalized==golden | raw==golden after time-only | raw bytes == golden |
|---|---|---|---|---|
| 5.2.1.32035 | oracle | 30/30 | 5/30 | 5/30 |
| 5.2.6.32774 | oracle | 30/30 | 30/30 | 5/30 |
| bcx-prototype | candidate | 29/30 | 0/30 | 0/30 |

The `raw==golden after time-only` column reproduces the audit's independently
measured `30/30` (reference) and `5/30` (current). `raw bytes == golden` is
5/30 for **both** installs and is not a defect: the golden reports embed their
own generation wall-clock, and the 5 cases that match byte-for-byte are exactly
the 5 `patch` layouts, which carry no header or timestamp at all.

---

## 5. Candidate adapter (the reserved product seam)

The product CLI does not exist yet. `harness/candidate.py` provides the seam:
candidates are **declarative entries** (path, argv template, flag templates,
output routing), so wiring in the real `reacmp` is a config change, not a code
change. `load_candidates(path)` accepts an external JSON config.

Two entries exist:

| Key | Kind | Status |
|---|---|---|
| `bcx-prototype` | prototype | `D:\Rea\clone\target\debug\bcx.exe` — **the OLD PROTOTYPE, not the product** |
| `reacmp` | product | declared, absent — reported as `not_run` with an explicit reason |

Every candidate result carries `artifacts.is_product`, `candidate_key` and
`candidate_label`, so prototype numbers can never be read as product numbers.
The prototype's own `cargo test` runs **0 tests**; its 45/45 came from the
Python script `tools/bcx-verify.py`.

The prototype does not implement BC's script interface, so the adapter calls its
own CLI (`bcx <left> <right> <out> [--opt=] [--layout=]`). The comparison is
therefore **candidate-CLI-vs-golden**, not script-vs-script, and the harness
says so in the run notes.

---

## 6. Running it

```bash
cd D:\Rea\product\verify

# identity only -- no Oracle calls
python -m harness.run_cli --identity-only

# the full gate: anchors + layouts + table + hex + pic + reg + ver + folder + labels + candidate
python -m harness.run_cli --install current --install reference --candidate reacmp --run-name my-run

# current install only, no reference, no candidate
python -m harness.run_cli --install current --run-name current-only

# include the old prototype as a candidate
python -m harness.run_cli --candidate bcx-prototype --run-name with-prototype

# one suite
python -m harness.run_cli --suite anchor --run-name anchors-only
```

Equivalent from the repo root:

```bash
cd D:\Rea
python -c "import sys; sys.path.insert(0,r'D:\Rea\product\verify'); from harness import run_cli; raise SystemExit(run_cli.main(['--install','current']))"
```

`run_cli` exits non-zero when anything executed but did not pass, so it can gate
CI. `not_run` alone does not fail the run.

### Automated tests

```bash
cd D:\Rea
python -m pytest product/verify/tests -q -p no:cacheprovider
```

**157 tests, all passing** (measured). `-p no:cacheprovider` is included because
pytest otherwise creates `.pytest_cache/` at the repository root, i.e. outside
this task's write scope. The tests pass either way; the flag just keeps the
repository clean.

No third-party dependency beyond `pytest`; everything else is the standard
library (`xml.etree.ElementTree`, `subprocess`, `hashlib`, `struct`, `ctypes`).
`test_oracle_live.py` and `test_process_tree.py` invoke the real Oracle and skip
with an explicit reason if no install is present — they are not skipped on this
machine.

| File | Tests | Covers |
|---|---|---|
| `tests/test_normalize.py` | 41 | label pairs, volatile fields, header wrap, **negative** body/status/line-number/order preservation, refusals, rule versioning, generalisation |
| `tests/test_runner.py` | 77 | verdict taxonomy, aggregation, manifest loading, **write-scope allow-list**, candidate config, identity reader |
| `tests/test_mutation_control.py` | 10 | end-to-end: mutated golden bodies/statuses/ids/order must still FAIL; label-only mutation must pass |
| `tests/test_oracle_live.py` | 20 | Oracle recipes, exit codes, determinism, the 45/45 gate, folder recipe, cross-locale corroboration, prototype adapter, agreement reconciliation |
| `tests/test_process_tree.py` | 9 | Job-Object containment: grandchild reaped on job close and on timeout, the pre-fix orphan reproduced as a control, no orphan after a real Oracle call, next call succeeds after a timeout, exit codes preserved |

---

## 7. Output layout

```
runs/<run-name>/
  REPORT.md               per-version counts, label table, uncovered scope, every non-pass
  report.json             machine-readable payload, one record per test
  install-identity.json   measured identity of every install used
  scripts/                every BComp script written for this run
  raw/                    every report as written, pre-normalization
  normalized/             the same reports after normalization
```

Each result record carries: test id, suite, subject, fixture paths, Oracle
version + path, full command line, script text, exit code, elapsed time, raw
report path, normalized report path, parsed result, expected value, normalizer
rule-set version, applied rules, verdict, detail, and known-difference marker.

The input manifest formats are documented in
[`MANIFEST-FORMAT.md`](MANIFEST-FORMAT.md).

---

## 8. Known differences (preserved, never special-cased)

### `mixed-side-by-side` — candidate only

When a paired line's left content exactly fills the left column, Beyond Compare
omits the diff-marker glyph:

```
golden (BC):   real diff 1    real diff 9
prototype:     real diff 1 <> real diff 9
```

`verify/layouts/README.md` already records this as an unmodelled trigger
condition. It is **not** a localization issue and it is **not** normalized away.
The harness keeps it as a `FAIL`, attaches `known_difference` text to the
result, and prints it under "Known differences" in every report. It is scoped to
`candidate`; the Oracle is unaffected.

---

## 9. Uncovered scope — read before quoting any number

* **1018/1035 (M111-gate-01) is the pass rate on the tested corpus: 212 text
  anchors + 31 layout cases + 19 table + 13 hex + 36 picture + 23 registry +
  2 folder goldens over both installs, plus the candidate replay.** It is
  *not* a statement of overall feature compatibility. All 17 non-passes are
  the Chinese install's registry side-by-side table lines (locale-dependent
  geometry; docs/17 §6), documented in every run's "Registry suite scope
  note" and never folded away.
* The text corpus (212 anchors + 31 layouts) does not exercise large files or
  performance; those are guarded offline by `cargo test --test large_input`
  and the m26 replay.
* **Folder comparison is one fixture pair** (`verify/dir/trees/{L,R}`) asserted
  as "the documented `load` → `expand all` → `folder-report` recipe exits 0
  and yields a structurally valid XML report" (the 2 folder results are that
  recipe re-run under both installs). There is **no golden folder report**;
  the stored `verify/dir/reports/manifest.json` records the pre-fix failure
  (exit 106, 0 bytes) and is surfaced as historical evidence, not regenerated.
  The few folder fixtures **do not imply full folder compatibility**.
* Folder criteria modes (size/timestamp/CRC/binary/rules-based), timestamp
  tolerance, attributes, symlinks, deep/empty structures, `newer`/`older`/
  `orphan`/`hollow` statuses: **not covered as goldens** (measured in
  `product/docs/08/15`; sync/copy semantics pinned by CLI integration tests,
  not by Oracle goldens).
* Covered channels: table/CSV (M6.4, docs/13), hex/binary (M7, docs/14),
  folder sync `sync` (M8, docs/15), picture `picture-report` (M9, docs/16 —
  PNG/BMP decoded; **GIF/JPEG are error-line cells only, no decoder**, a
  recorded known difference), registry `registry-report` (M10/M11, docs/17 —
  23 goldens authored from the reference install; the Chinese install's
  side-by-side table geometry is a recorded, measured difference, see the
  run's "Registry suite scope note").
* Still uncovered: version (`version-report`), media, per-type `file-report`,
  3-way merge, VFS (FTP/SFTP/WebDAV/archive), GUI, printing, clipboard,
  session persistence.
* The reference install is used to corroborate **label text** and to re-run
  the goldens in English (pic/table/hex pass there too); it is never merged
  into a current-install-only number.

---

## 10. Adding a new fixture

See [`MANIFEST-FORMAT.md`](MANIFEST-FORMAT.md) section 3. In short: fixtures and
manifests are discovered, so a new anchor/layout case needs no runner change —
add the input files and a manifest entry, then run the suite. **Never** point a
manifest at a fixture outside `D:\Rea\verify\`, and never regenerate an existing
golden file.

---

## 11. Known gaps in this harness

* **A modal dialog cannot be prevented from Python — only survived.** `/silent`
  suppresses dialogs raised by *script issues* (the help text: "any unresolved
  issue that would normally show a dialog will log an error instead"). It does
  **not** cover the application-crash dialog
  (`一个错误发生在应用程序中`), which is raised by the GUI host itself. No BC
  command-line switch found in `help/command_line_reference.html` disables a
  crash dialog. The harness therefore does not claim to prevent it: it
  **contains** it, via the Job Object (section 3a), so a dialog cannot outlive
  its call or stall the suite. If a crash dialog appears, the affected call
  reports `TIMEOUT` (or a non-zero exit) and the tree is reaped; the modal may
  still be visible on the desktop until it is dismissed, but it no longer owns
  any harness resource. Any process still listed as `BCompare.exe` after a run
  should be treated as an Oracle crash worth investigating.
* **Job Objects are Windows-only.** On a non-Windows host `ProcessTree` reports
  `containment = "none"` (or `unsupported`) and falls back to killing the direct
  child only. The harness is measured on Windows; the non-Windows path is
  untested here and the report states which containment was in force.
* **Folder coverage is one case.** `load_folder_cases` models the fixture set as
  a single L/R tree pair because that is what exists; extending to many named
  pairs is a contained change in `harness/manifests.py`.
* **No golden folder report**, so the folder suite verifies the *recipe*, not
  compatibility. This is stated in every folder result.
* **`--json-only`** suppresses the per-test console listing but does not change
  what is written to disk.
* **Exit code 105** is documented in `EXIT_MEANINGS` but was not reproduced by
  any probe in this task; it is carried over from
  `product/docs/05-acceptance-strategy.md` and is not independently confirmed
  here.
* The normalizer handles **only** the labels observed in the current corpus. A
  new Chinese label will produce `unparseable` until the table is extended —
  that is the intended behaviour, not a defect.
* `runs/` accumulates; old runs are not pruned automatically.

---

## 12. Files in this directory

| Path | Role |
|---|---|
| `README.md` | this file |
| `MANIFEST-FORMAT.md` | input manifest + output listing format |
| `harness/__init__.py` | versions (`HARNESS_VERSION`, `RULESET_VERSION`) |
| `harness/taxonomy.py` | verdicts, `TestResult`, aggregation |
| `harness/normalize.py` | versioned normalization rules + refusals |
| `harness/installs.py` | install identity (PE version reader, digests, locale) |
| `harness/oracle.py` | Oracle invocation, exit-code semantics, `ProcessTree` Job-Object containment |
| `harness/candidate.py` | candidate adapter / product seam |
| `harness/manifests.py` | read-only fixture manifest loaders |
| `harness/runner.py` | suites, judging, write-scope guard |
| `harness/report.py` | report rendering, known differences, uncovered scope |
| `harness/run_cli.py` | CLI entry point |
| `tests/test_normalize.py` | normalizer unit tests |
| `tests/test_runner.py` | runner/taxonomy/manifest/identity unit tests |
| `tests/test_mutation_control.py` | end-to-end "differences survive" controls |
| `tests/test_oracle_live.py` | live Oracle integration tests |
| `tests/test_process_tree.py` | Job-Object containment / orphan-leak regression tests |
| `runs/<name>/` | run outputs (reports, scripts, raw + normalized reports) |

### What this task did NOT touch

`D:\Rea\verify\` (golden data, fixtures, manifests), `D:\Rea\clone\`,
`D:\Rea\extracted\`, `D:\Rea\ghidra-project\`, `D:\Rea\specs\`,
`D:\Rea\report-*.md`, `D:\Rea\tools\bc-*.py`, `D:\Rea\tools\_audit\`,
`D:\BCompare\`, and `D:\Rea\product\docs\`. Those were read only. The fixture
manifests are byte-identical before and after a run — asserted by
`test_anchor_manifest_is_not_rewritten_by_loading`.

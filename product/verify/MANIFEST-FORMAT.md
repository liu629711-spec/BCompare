# Test manifest / listing format

This document describes the fixture listing formats the harness consumes and
the format it produces. It exists so a new fixture can be added without reading
the runner source.

## 1. Input manifests (read-only)

These files already exist under `D:\Rea\verify\` and are **never modified** by
the harness. They are the harness's input, not its output.

### 1.1 Text anchors -- `verify/golden/manifest.json`

A JSON object: top-level key = anchor name, value = the anchor record.

```json
{
  "al-insert": {
    "unit": "SsLineList",
    "note": "pure insertion",
    "exit_code": 0,
    "statuses": ["same", "rightorphan", "same"],
    "seconds": 0.63,
    "left":  "D:\\Rea\\verify\\golden\\al-insert-L.txt",
    "right": "D:\\Rea\\verify\\golden\\al-insert-R.txt",
    "report":"D:\\Rea\\verify\\golden\\al-insert.xml"
  }
}
```

| Field | Meaning | Used by the harness as |
|---|---|---|
| `unit` | BC unit the anchor targets | reported, and grouped in the JSON payload |
| `note` | free text; **also carries the option** | parsed for `options:<name>` |
| `exit_code` | exit code the golden generator observed | recorded as `golden_exit_code` |
| `statuses` | expected `linecomp/@status` sequence | the primary assertion |
| `seconds` | generation time | recorded only |
| `left` / `right` | input fixture paths | passed unchanged to the Oracle |
| `report` | the golden report | parsed and normalised for structural comparison |

**Option discovery.** An option is encoded in the `note` field as
`options:<name>`. The extractor is
`harness.manifests.option_of`, pattern `options:([A-Za-z0-9+\-]+)`.

```
"options:display-matches on mixed pair"   ->  display-matches
"options:display-context on mixed pair"   ->  display-context
"options:ignore-unimportant on mixed pair"->  ignore-unimportant
"pure insertion"                          ->  None
```

The recovered option is injected into the Oracle script as
` options:<name>` and into the candidate command as `--opt=<name>`.

### 1.2 Text layouts -- `verify/layouts/manifest.json`

```json
{
  "mixed-side-by-side": {
    "layout": "side-by-side",
    "case": "mixed",
    "exit_code": 0,
    "bytes": 339,
    "report": "D:\\Rea\\verify\\layouts\\mixed-side-by-side.txt"
  }
}
```

The input fixtures are **derived, not stored** in the manifest:
`<case>-L.txt` and `<case>-R.txt` next to the manifest. This matters because
five layouts share one fixture pair; a manifest that stored its own copies of
the inputs would let the pairs drift apart.

| Field | Meaning |
|---|---|
| `layout` | one of `side-by-side`, `interleaved`, `patch`, `summary`, `statistics`, `over-under` |
| `case` | fixture pair name; inputs are `<case>-L.txt` / `<case>-R.txt` |
| `bytes` | golden report size, recorded for reference |
| `report` | the golden layout report |

### 1.3 Table goldens -- `verify/table/manifest.json`

```json
{
  "t-sbs-changed": {
    "layout": "side-by-side",
    "ext": "csv",
    "title": null,
    "note": "T1 lineage: header + one changed row pair",
    "exit_code": 0,
    "bytes": 320,
    "report": "D:\\Rea\\verify\\table\\t-sbs-changed.txt"
  }
}
```

Like the layouts suite, fixture pairs are **derived from the case name**
(`-L.<ext>` / `-R.<ext>`; a mixed pair — one side `.csv`, one side not —
stores `ext_right` for the right file, e.g. `t-mixed-csvp` pins fixed
comma for BOTH files from either side's `.csv`, docs/13 §9); a `title`
(when non-null) is emitted into the
`data-report` script as `title:"<value>"` (X4). The channel has no XML
layout, so goldens are text reports compared line-wise under
`normalize_text` (norm-3 folds the table title/count labels). Space-split
cases are deliberately absent: their acceptance rule is a recorded
permanent KNOWN (docs/13 §8). Append-only:
`tools/m64_add_table_goldens.py` / `tools/m68_add_table_goldens.py`
refuse an existing key and snapshot the previous manifest.

### 1.4 Hex goldens -- `verify/hex/manifest.json`

```json
{
  "h-sbs-equal": {
    "layout": "side-by-side",
    "note": "Y1: all-same report -> zone width 1 (` = ` once), single block rule",
    "exit_code": 0,
    "bytes": 823,
    "report": "D:\Rea\verify\hex\h-sbs-equal.txt"
  }
}
```

Fixture pairs are **derived from the case name** (`<name>-L.bin` /
`<name>-R.bin`). `title` (when present) goes into the `hex-report` script
(V3/Y11). The channel has no XML layout, so goldens are text reports
compared line-wise under `normalize_text` (norm-3 folds the hex title and
byte-count labels). Append-only: `tools/m71_add_hex_goldens.py` refuses an
existing key and snapshots the previous manifest.

### 1.5 Picture goldens -- `verify/pic/manifest.json`

```json
{
  "p-sum-equal": {
    "layout": "summary",
    "note": "Q1: identical pair -> only the same count line",
    "script": "picture-report layout:summary output-to:\"%3\" \"%1\" \"%2\"",
    "left": "D:\\Rea\\verify\\pic\\p-sum-equal-L.png",
    "right": "D:\\Rea\\verify\\pic\\p-sum-equal-R.png",
    "exit_code": 0,
    "bytes": 182,
    "report": "D:\\Rea\\verify\\pic\\p-sum-equal.txt"
  }
}
```

Unlike the hex/table suites, picture fixtures carry **real image extensions**
(`.png`/`.bmp`/`.gif`/`.bin`), so the manifest names `left`/`right` explicitly
instead of deriving `<name>-L.bin`, and stores the exact probe **`script`**
line -- the goldens re-run the measured script bytes, including `options:`/
`title:` forms and the zero-file shell cells (whose `left`/`right` are `""`).
The channel has no XML layout, so goldens are text reports compared line-wise
under `normalize_text` (norm-4 folds the picture title/header/error lines and
pixel-count labels, and strips a leading BOM -- the zero-file shells are the
first text goldens carrying one). Append-only:
`tools/m91_add_pic_goldens.py` refuses an existing key and snapshots the
previous manifest; fixture bytes are copied verbatim from the probe archive
(never regenerated) and the Oracle re-runs in the final tree so the report's
embedded paths match the golden location.

### 1.5b Registry goldens -- `verify/reg/manifest.json`

```json
{
  "r-sbs-equal": {
    "layout": "side-by-side",
    "note": "frame: title/Produced/Mode/file lines + basekey suffix; orphan-end rows",
    "script": "registry-report layout:side-by-side output-to:\"%3\" \"%1\" \"%2\"",
    "left": "D:\\Rea\\verify\\reg\\r-sbs-equal-L.reg",
    "right": "D:\\Rea\\verify\\reg\\r-sbs-equal-R.reg",
    "exit_code": 0,
    "bytes": 414,
    "report": "D:\\Rea\\verify\\reg\\r-sbs-equal.txt",
    "authored_by": "reference (English 5.2.6.32774); ..."
  }
}
```

Same shape as the picture manifest (explicit `left`/`right`, verbatim probe
`script`, append-only via `tools/m111_add_reg_goldens.py`). **The goldens are
authored from the REFERENCE (English) install**, and `authored_by` records why
on every entry: the registry side-by-side TABLE geometry is locale-dependent
(the column floors are the header-label widths, so the Chinese
名称/类型/数据 labels produce a narrower table than English Name/Type/Data for
the same fixtures -- measured on both installs, runs/m101f-regbox-current vs
m101f-regbox-reference, 29 shared cells). The product renders the English
frame (the dir/pic/hex precedent), so the English golden is the only text the
candidate replay can byte-match; the Chinese geometry is locked by
`reacmp-reg/tests/corpus_cases.rs` (103 archived tables, 85 ZH + 18 EN)
instead. norm-5 folds the Chinese labels (title, Mode lines, error lines,
item counts) so the Chinese install's oracle re-run matches the
**summary** cells and fails only on the table lines -- reported as the
documented "Registry suite scope note", never as a silent pass.

### 1.6 Folder fixtures -- `verify/dir/`

```
verify/dir/trees/L/      left base folder
verify/dir/trees/R/      right base folder
verify/dir/_script.txt   the historical (broken) script
verify/dir/reports/manifest.json
```

Discovery is directory-based: `verify/dir/trees/{L,R}`. The stored
`reports/manifest.json` records the **pre-fix failure** (`exit 106`, `0 bytes`)
and is surfaced verbatim in each folder result as historical evidence. It is not
regenerated and there is no golden folder report.

## 2. Output listing format

Every run writes a directory under `product/verify/runs/<run-name>/`:

```
runs/<run-name>/
  REPORT.md              human-readable report (see below)
  report.json            machine-readable payload
  install-identity.json  measured identity of every install used
  scripts/               every BComp script written for this run
  raw/                   every Oracle/candidate report, pre-normalization
  normalized/            the same reports after normalization
```

### 2.1 Per-result record

One JSON object per test, in `report.json` -> `results[]`. The fields below are
the minimum required for a result to be traceable back to its evidence.

| Group | Field | Notes |
|---|---|---|
| identity | `test_id`, `suite`, `subject` | `suite` ∈ anchor/layout/table/hex/folder/labels; `subject` ∈ oracle/candidate |
| subject | `oracle_version`, `oracle_path` | for candidates, the candidate path/version land in `artifacts` |
| invocation | `command`, `script_text` | the **full** command line, as executed |
| invocation | `exit_code`, `elapsed_s` | `exit_code` is `null` only if the process never started |
| fixtures | `left`, `right`, `golden_report` | absolute paths, unchanged from the manifests |
| reports | `raw_report`, `normalized_report` | both kept, so a rule's effect is traceable |
| comparison | `parsed`, `expected` | the normalized comparison key / structure |
| normalizer | `normalizer_ruleset`, `rules_applied` | rule-set version + which rules fired |
| verdict | `verdict`, `detail`, `known_difference` | see below |

### 2.2 Verdicts

| Verdict | Meaning | Counted as pass? |
|---|---|---|
| `pass` | both sides parsed and the compared structure matched | yes |
| `fail` | both sides parsed and the compared structure differed | no |
| `error` | the process could not run, or the Oracle exited non-zero (104/105/106/107) | **no** |
| `missing_output` | exit 0 but the report is absent or zero bytes | **no** |
| `timeout` | exceeded `--timeout` | **no** |
| `unparseable` | the report exists but the normalizer refused it (unknown tag/format change) | **no** |
| `not_run` | skipped before execution (missing fixture, candidate unavailable) | **no** |

`unparseable` is the "needs-normalizer-update" signal. It is never silently
downgraded: a new tag, an unknown status value or a new label wording stops the
comparison and names the offending rule.

## 3. Adding a new fixture

The harness discovers fixtures from the manifests, so no runner change is
needed for a new case that fits an existing manifest shape.

**New text anchor**

1. Create `verify/golden/<name>-L.<ext>` and `<name>-R.<ext>`.
   *Do not overwrite an existing anchor.*
2. Add an entry to `verify/golden/manifest.json` with `unit`, `note`, `left`,
   `right`, `report`, plus `statuses` and `exit_code` captured from the Oracle.
   If the case needs an option, write it into `note` as `options:<name>`.
3. Run `python -m harness.run_cli --suite anchor`. The new anchor is picked up
   automatically and will show up as `fail` until the expected `statuses` match.

**New layout case**

1. Create `verify/layouts/<case>-L.txt` and `<case>-R.txt`.
2. Add entries for each layout you want, with `layout`, `case`, `bytes`,
   `report`.
3. Run `python -m harness.run_cli --suite layout`.

**New table case**

1. Create the case as its own `verify/table` entry (table goldens are one
   cell per case; the pair stem carries the case name, not a shared case).
2. Run `tools/m64_add_table_goldens.py` (serial Oracle, append-only; it
   writes fixture pair + report + manifest entry in one pass).
3. Run `python -m harness.run_cli --suite table`.

**New hex case**

1. Create the case as its own `verify/hex` entry (hex goldens are one cell
   per case; the pair stem carries the case name and both sides are `.bin`).
2. Run `tools/m71_add_hex_goldens.py` (serial Oracle, append-only; it
   writes fixture pair + report + manifest entry in one pass).
3. Run `python -m harness.run_cli --suite hex`.

**New folder case**

Drop another `trees/<name>/{L,R}` pair under `verify/dir/`. Note that
`load_folder_cases` currently models the fixture set as one L/R tree pair
because that is what exists; extending it to many named pairs is a small,
contained change in `harness/manifests.py`.

**Never** point a manifest at a fixture outside `D:\Rea\verify\` without reading
`harness/runner.py::assert_writable` first — the guard exists so the harness can
never write next to read-only golden data.

## 4. Normalizer rule-set versioning

`harness/normalize.py::RULESET_VERSION` is recorded on **every** result and in
the run header. Bump it whenever a rule is added or changed. Two runs may only
be compared when their rule-set versions agree; a difference in rule-set version
means the numbers are not directly comparable.

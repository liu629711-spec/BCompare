# M3 — read-only folder comparison (`product/vfs` + `product/dir`)

> Task A-3. Two standalone crates implementing M3.1 – M3.5 of
> `product/docs/04-milestones.md`, plus the VFS seam from
> `product/docs/03-architecture-options.md` section 2.

---

## Read this first

**There is no golden folder report in this workspace**, and this task was not
allowed to invoke the Oracle. So:

* the criteria model, the XML skeleton and the status vocabulary are backed by
  **observed** evidence and are re-validated against the stored artifacts on every
  manifest regeneration;
* everything else is this engine's **committed behaviour under that observed
  model**, checked by an independent second implementation — not a measured
  Beyond Compare parity claim.

The one measured parity result is in `docs/EVIDENCE.md` section 4.1: for the
read-only audit tree pair under the default criteria, this engine's XML is
byte-identical to the single stored Oracle folder report. One tree pair, one
criteria setting.

`docs/EVIDENCE.md` records the grade (`O`/`D`/`I`/`U`) of every behaviour and
lists twelve unknowns with what would settle each.

---

## Layout

| Path | Milestone | Contents |
|---|---|---|
| `product/vfs/` | M3.1 | read-only `FileSystem` trait, `LocalFs`, opaque paths, timestamps and zones |
| `product/dir/` | M3.2 – M3.5 | tree model, criteria engine, reports, CLI |
| `product/dir/fixtures/` | M3.4 | 11 generated tree pairs and the case manifest |
| `product/dir/tools/` | M3.4 | fixture generator, case generator, fixture runner, Oracle check |
| `product/dir/docs/EVIDENCE.md` | — | the evidence ledger |

Both crates are **standalone workspaces** (each `Cargo.toml` carries an empty
`[workspace]` table) so a `Cargo.toml` added above them by a parallel task cannot
absorb them. `reacmp-dir` depends on `reacmp-vfs` by relative path, so there is no
registry access and the build is offline.

## Requirements met

### M3.1 — read-only `FileSystem` trait + `LocalFs`

* **Paths are opaque strings** (ADR-4): `VfsPath`, never `std::path::Path`. The
  observed report echoes `<ltpath>D:\Rea\verify\dir\trees\L</ltpath>` verbatim, and
  `ftp://host/dir` has no faithful local `Path`. Nothing normalises or resolves a
  path value.
* **Read-only and writable are separate traits** (ADR-3): `FileSystem` is the only
  trait the engine accepts; `WritableFileSystem` is declared so the boundary is in
  the type system, and **nothing implements it**.
* **Shaped for an archive or remote backend** (ADR-2): `ArchiveFs`/`RemoteFs` can
  be added without touching the engine, because the engine only asks for a
  listing, metadata and bytes.
* Explicit errors everywhere: a listing failure never degrades to an empty
  listing, a directory reports no size rather than zero, attributes are
  `Option<bool>` so "unknown" is distinct from "clear".

### M3.2 — the tree model

Recursion, name-based alignment within each relative directory, and per-entry
status. A directory's status is an aggregate of its children, never its own
timestamp. Report order is directories first, then files, each name-sorted.

### M3.3 — the criteria engine

The **observed** model only:

| criteria | behaviour | grade |
|---|---|---|
| default (none) | size + timestamp | **O** |
| `size`, `timestamp` | as named | **O** |
| `CRC`, `binary`, `rules-based` | content comparison | **O** |
| `content`, `binary-content` | **rejected**, exit 106 | **O** |
| `timestamp:Nsec`, `;IgnoreDST` | tolerance | **O** grammar, **U** boundary |
| `attrib:ashr` | per-attribute DOS comparison | **O** grammar |
| `timezone:ignore`, `left±N`, `right±N` | shift or suppress | **O** grammar, **U** direction |
| `follow-symlinks` | treat links and junctions as their targets | **O** grammar |
| `version`, `owner`, `group`, `permissions`, `ignore-unimportant` | **rejected** as not probed | refused on purpose |

`rules-based` is evaluated as **byte equality**: the per-format importance rules
it implies are M2 work and are not implemented. Every such comparison carries a
note that is rendered into the reports.

### M3.4 — fixtures

**11 tree pairs / 182 entries / 12 case pairs / 75 cases** (target was ≥ 40 cases).

Coverage against the plan in `product/docs/05-acceptance-strategy.md` section 4.2:

| Category from §4.2 | Target | Cases | Notes |
|---|---:|---:|---|
| status coverage | 8 | 40 | every observed token: `same`, `diff`, `ltonly`, `rtonly`, `ltnewer`, `rtnewer` |
| criteria matrix | 12 | 34 | default / `size` / `timestamp` / `CRC` / `binary` / `rules-based`, across four tree pairs |
| timestamp tolerance | 4 | 7 | `:1sec`, `:30sec`, `:60sec`, `:7200sec`, `;IgnoreDST` |
| structural boundaries | 8 | 12 | 12-level nesting (beyond `MAX_PATH`), empty dirs, file-vs-directory conflicts, 60+ siblings, orphan trees, XML-escaping names |
| attributes | 4 | 7 | `attrib:h`, `:s`, `:r`, `:a`, `:hs`, `:ashr`, and combined with `CRC` |
| symlinks | 4 | 4 | the junction pair under default / followed / CLI-flag / with a content criterion |
| *(additional)* timezone | — | 5 | `ignore`, `left±N`, `right±N` |
| *(additional)* rejections | — | 19 | invalid and not-probed criteria, unknown layouts |

Measured row coverage: 228 `same`, 74 `diff`, 80 `ltonly`, 48 `rtonly`, 9
`ltnewer`, 36 `rtnewer`.

`fixtures/cases.json` is machine-readable and labels every case
`observed` (14) or `predicted` (61).

### M3.5 — three report layouts

* **`xml`** — reproduces the observed structure element for element, including the
  UTF-8 BOM, CRLF line endings, one tab per nesting level, `<ltpath>`/`<rtpath>`,
  nested `<foldercomp>` for directories, `<filecomp status="…">` for files, and
  omission of a missing side. **Measured byte-identical** to the stored Oracle
  report for the audit tree pair.
* **`side-by-side`** and **`summary`** — **no observed sample exists**, so both
  state `NOT byte-compatible` in their own header rather than imitating a format
  nobody has seen. `summary` also prints the criteria that produced it.

---

## Building and testing

```bash
cd D:\Rea\product\vfs && cargo test
cd D:\Rea\product\dir && cargo test
```

Both are green with a bare `cargo test`; no feature flag is needed.
`reacmp_dir::testing` exposes an in-memory `FileSystem` used by the integration
tests and available to anyone embedding the engine.

## Running the fixture corpus

```bash
cd D:\Rea\product\dir
python tools/make_fixtures.py            # (re)create the tree corpus
python tools/make_fixtures.py --check     # detect drift
python tools/make_cases.py                # rebuild cases.json; re-checks the O anchors
python tools/compare_fixtures.py          # run everything
```

`compare_fixtures.py --help` lists the options (`--case`, `--verbose`,
`--emit-reports`, `--json`). It **refuses to run** when the corpus or the
expectations have drifted from the artifacts they came from.

## The Oracle correspondence

Every non-rejection case in the manifest carries the exact Beyond Compare script
that would reproduce it, so the project lead's serial Oracle pass can run the same
corpus:

```
load "<left>" "<right>"
expand all
folder-report layout:<layout> output-to:"<out>"
```

That is the recipe verified in `product/verify/README.md` section 2. The fixtures
are deterministic — every mtime comes from a fixed epoch (`make_fixtures.py::EPOCH`)
and directory mtimes are stamped after their children — so the same corpus
produces the same report on any machine in any timezone when `--tz-offset` is
given.

The one existing Oracle report can be checked at any time:

```bash
python tools/verify_against_oracle_xml.py
```

## Exit codes

`reacmp-dir` uses `0` (ran, nothing differs), `1` (ran, something differs),
`2` (error), `106` (script-command error: an invalid criteria keyword or an unknown
layout — matching the Oracle's observed code for `criteria content`) and `107`
(path not found).

## Deliberately not implemented

| Not implemented | Why |
|---|---|
| File copy / move / sync / delete | the only destructive surface; `product/docs/04-milestones.md` section 0 excludes it, section 4 P9 requires an independent safety review |
| Archive (`zip`/`7z`/`tar`) and remote backends | `02-version-and-evidence.md` U7, `04-milestones.md` P7/P10; the trait is shaped for them but implementing without a probed spec would be guessing |
| `criteria rules-based` per-format importance | M2 work |
| `criteria version`, `owner`, `group`, `permissions`, `ignore-unimportant` | documented but not probed here — refused, not approximated |
| `DirHollow` / `DirFiltered` statuses | scan-in-progress / filter states, not comparison results of a completed batch run |
| `leftolder`, `rightolder`, `orphan`, `conflict` status tokens | never observed in output and absent from the report writer's string table |
| Text-layout byte compatibility | no observed sample exists |
| GUI, printing, clipboard, sessions | out of MVP scope |

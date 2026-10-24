# `reacmp-vfs` — the read-only filesystem seam (M3.1)

Task A-3. Implements M3.1 of `product/docs/04-milestones.md` per
`product/docs/03-architecture-options.md` section 2 and ADR-2/3/4.

## The three binding constraints, and where they show up

**ADR-4 — paths are opaque strings, not `std::path::Path`.**
`VfsPath` wraps a `String`. It never normalises, canonicalises or resolves `.`/`..`,
because the observed report echoes `<ltpath>D:\Rea\verify\dir\trees\L</ltpath>`
verbatim and a remote or archive path has no faithful local `Path`. Path *joining*
is a backend operation (`FileSystem::join` supplies the separator), so the
comparison engine never has to know which backend it is talking to. `LocalFs`
converts to a real path only at the syscall boundary, in a private helper.

**ADR-3 — read-only and writable are separate traits.**
`FileSystem` has only `read_dir`, `metadata`, `read_file`, `open_read`, `join`,
`exists` and `local_offset_minutes`. `WritableFileSystem` is declared so the
boundary is visible in the type system and is **implemented by nothing**, and no
read-only entry point accepts one. Comparison therefore cannot write, not even by
accident.

**ADR-2 — the engine talks to a trait, not to `std::fs`.**
Adding an `ArchiveFs` (zip/7z/tar) or a `RemoteFs` later needs no change in the
comparison engine: it only asks for a listing, metadata and bytes.

## What this crate deliberately does not do

* No archive backend (`02-version-and-evidence.md` U7 — the spec has not been
  probed; the trait is shaped for it).
* No remote backend (ADR-9 excludes remote from the first year).
* No writable implementation at all.
* No path normalisation: a silent rewrite of an opaque string would corrupt the
  value that goes into a report.

## Files

| File | Contents |
|---|---|
| `src/traits.rs` | `FileSystem`, `WritableFileSystem`, `Entry`, `Metadata`, `EntryKind`, `Attributes`, `AttributeSet`, `SymlinkPolicy` |
| `src/path.rs` | `VfsPath` — the opaque path |
| `src/local.rs` | `LocalFs` — the read-only local backend |
| `src/time.rs` | `Timestamp`, civil-date conversion, DST-aware offset computation |
| `src/error.rs` | `VfsError` and `VfsResult` |

## Behaviours the API guarantees

* A listing failure is **never** an empty listing: an empty directory and an
  unreadable one are different observations and the report shows them differently
  (`<size>0</size>` versus an error).
* A directory reports **no size**, not zero — the observed report distinguishes
  them (`<size/>` before `expand all`).
* DOS attributes are `Option<bool>` per flag, so "unknown" is distinct from
  "clear". On non-Windows platforms they are all unknown, because the help text
  says "the macOS and Linux versions do not support `attrib`" — unknown is the
  honest answer and a known `false` would be a fabricated measurement.
* A symlink is reported as a link unless `SymlinkPolicy::Follow` is asked for; a
  dangling link under `Follow` is an explicit error, not a zero-byte file.
* `metadata_opt` maps **absence only** to `Ok(None)`; every other failure
  propagates.

## Timestamps

`Timestamp` holds milliseconds since the Unix epoch. Rendering uses the local
offset, because the observed report does: the audit fixture's `st_mtime` converts
to `2026-10-13 10:06:12` local (`UTC+08:00` on this host) and `02:06:12` UTC, and
the report says `10:06:12`. See `src/time.rs` for the measurement.

The offset comes from an injected `OffsetProvider`. `SystemZone` reads
`TIME_ZONE_INFORMATION` on Windows and **self-checks** the parsed value against
`GetLocalTime()` vs `GetSystemTime()` for the current instant, so a wrong struct
interpretation fails loudly instead of producing a silently wrong offset. DST
transition rules are evaluated with all three relevant years considered, because a
southern-hemisphere regime starts in one year and ends in the next.

## Testing

```bash
cargo test
```

Includes a synthetic DST test for both hemispheres (the northern one uses known
2026 calendar facts) and a regression test for forward-slash and relative roots,
both of which were real bugs.

## A note on two deviations from the sketch in `03-architecture-options.md` section 2

The audit's sketch used an associated type (`type Entry`) and returned
`Box<dyn Read>`. This implementation returns owned `Entry` values and a `Vec<u8>`
from `read_file` (with `open_read` offered separately for streaming):

* an associated type would force the comparison engine to be generic over both
  sides' backends at once, which makes "compare a local folder against an archive"
  — the exact case ADR-2 exists to enable — awkward;
* the content criteria hash whole files, so a byte vector is the natural shape;
  `open_read` exists so a future large-file path can stream instead, and its
  default implementation delegates to `read_file` so a backend that cannot stream
  is still complete.

"""Run report rendering (machine-readable JSON + human-readable Markdown)."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from .taxonomy import TestResult, Verdict, summarize, summarize_by

#: Differences that are known, understood and deliberately preserved.
#: They are reported as such, never special-cased into a pass.
KNOWN_DIFFERENCES: dict[str, str] = {
    "mixed-side-by-side": (
        "Candidate-only divergence. When a paired line's left content exactly "
        "fills the left column, Beyond Compare omits the diff marker glyph "
        "(golden: 'real diff 1    real diff 9'); the prototype emits "
        "'real diff 1 <> real diff 9'. The exact trigger condition is not "
        "modelled. verify/layouts/README.md already records this. NOT a "
        "label/localization issue and NOT normalised away."
    ),
}

KNOWN_DIFFERENCES_SCOPE = {
    "mixed-side-by-side": "candidate",
}

#: Scope notes that only apply to the registry suite (norm-5, M11).  The
#: registry side-by-side TABLE geometry is locale-dependent: the column
#: floors are the header-label widths, so the Chinese 名称/类型/数据 labels
#: (2 columns) produce a narrower table than English Name/Type/Data (4) for
#: the very same fixtures (measured on BOTH installs, runs/m101f-regbox-
#: current vs m101f-regbox-reference, 29 shared cells; docs/17 §geometry).
#: The goldens are therefore authored from the REFERENCE (English) install
#: -- the form the product renders -- and the Chinese install's oracle
#: re-run legitimately differs on the table lines.  That is NOT a defect on
#: either side: the Chinese geometry is locked by the product's own corpus
#: tests (reacmp-reg/tests/corpus_cases.rs, 103 archived tables byte-exact:
#: 85 ZH + 18 EN).  Summary-layout cells (no table) fold to identical
#: structures on both installs, which is exactly what the norm-5 label
#: rules are for.
REGISTRY_SCOPE_NOTE = (
    "reg/oracle on the CURRENT (Chinese) install fails on the side-by-side "
    "TABLE lines only (17/23): the table geometry is locale-dependent "
    "(column floors are the header-label widths, so 名称/类型/数据 is "
    "narrower than Name/Type/Data). The goldens are the English "
    "(reference-install) form -- what the product renders -- and the "
    "Chinese geometry is locked by reacmp-reg's own corpus tests instead. "
    "Summary cells (6/23) fold identically on both installs under norm-5, "
    "corroborating the item-count and error-line label pairs."
)

VERSION_SCOPE_NOTE = (
    "ver/oracle on the CURRENT (Chinese) install fails on the side-by-side "
    "TABLE lines only (19/25): the same locale-dependent geometry as the "
    "registry channel (docs/18 §6, the docs/17 §6 precedent). The goldens "
    "are the English (reference-install) form -- what the product renders -- "
    "and the Chinese geometry is locked by reacmp-ver's own 18-cell corpus "
    "instead. Summary/shell cells (6/25) fold identically on both installs "
    "under norm-6. The CANDIDATE replay's 18 fails are all the recorded "
    "U-ver-1 residual (the Data size field, docs/18 §8): every other byte "
    "of every candidate report matches its golden."
)

#: What this run does NOT establish.  Printed verbatim into every report so a
#: pass count can never be read as a compatibility claim.
UNCOVERED_SCOPE = (
    "45/45 is the pass rate on the **tested text anchors only**. It is not a "
    "statement of overall feature compatibility.",
    "The text corpus is 45 anchors + 30 layout reports over 5 fixture pairs. "
    "It does not exercise large files, performance, or the >=80-anchor target "
    "in product/docs/04-milestones.md.",
    "Folder comparison is covered by ONE fixture pair (trees/L vs trees/R) and "
    "is asserted only as 'the documented load -> expand all -> folder-report "
    "recipe exits 0 and yields a structurally valid XML report'. There is no "
    "golden folder report to compare against, and this does NOT imply folder "
    "compatibility. See product/docs/05-acceptance-strategy.md section 4.2.",
    "Folder criteria modes (size/timestamp/CRC/binary/rules-based), timestamps "
    "tolerance, attributes, symlinks and deep/empty structures are NOT covered.",
    "Binary, hex, table, picture, registry, version, 3-way merge, VFS "
    "(FTP/SFTP/WebDAV/archive), GUI, printing, clipboard, session persistence "
    "and file sync/copy are entirely uncovered.",
    "The Oracle covers the current install's behaviour on these inputs; the "
    "reference install is used only to corroborate label text.",
    "Candidate numbers describe whichever candidate binary was wired; today "
    "that is the OLD PROTOTYPE, not the product.",
)


def label_mapping_table() -> list[tuple[str, str, str]]:
    """Return the confirmed label pairs as (kind, source, target)."""
    from . import normalize as N

    rows: list[tuple[str, str, str]] = []
    for (_tag, zh), (_tag2, en) in sorted(N.XML_LABEL_PAIRS.items()):
        rows.append(("xml label", f"<mode>{zh}</mode>", f"<mode>{en}</mode>"))
    rows.append(("xml label", "<error1>文件编码错误 (第 N 行)</error1>",
                 "<error1>File Encoding Error (Line N)</error1>  (N preserved)"))
    for zh, en in sorted(N.TEXT_LABEL_PAIRS.items()):
        rows.append(("text label", zh, en))
    for zh, en in sorted(N.TEXT_COUNT_LABELS.items(), key=lambda kv: kv[0]):
        rows.append(("text count label", f"N {zh}", f"N {en}  (N preserved)"))
    rows.append(("text header", "左边文件： P      右边文件： Q",
                 "Left file: P Right file: Q  (paths preserved, padding collapsed)"))
    rows.append(("text header", "wrapped onto 2 lines",
                 "re-joined onto 1 line  (same as the unwrapped form)"))
    rows.append(("volatile", "已产生： <timestamp> / Produced: <timestamp>",
                 f"Produced: {N.TIME_PLACEHOLDER}"))
    rows.append(("volatile", 'created="<timestamp>"',
                 f'created="{N.TIME_PLACEHOLDER}"'))
    return rows


def _verdict_table(results: list[TestResult]) -> list[str]:
    rows = ["| test | subject | version | verdict | detail |",
            "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: (x.suite, x.test_id)):
        det = (r.detail or "").replace("|", "\\|")
        rows.append(f"| `{r.test_id}` | {r.subject} | {r.oracle_version or '-'} "
                    f"| **{r.verdict.value}** | {det[:160]} |")
    return rows


def _version_key(r: TestResult) -> str:
    """Group key that never merges subjects or versions.

    An Oracle result is keyed by the engine version measured from the install.
    A candidate result is keyed by the candidate's own identity; when the binary
    carries no PE version resource (true of the Rust prototype) the key says so
    explicitly rather than collapsing to a bare "unknown" that could be mistaken
    for the Oracle's version.
    """
    if r.subject == "candidate":
        name = r.artifacts.get("candidate_key", "candidate")
        ver = r.artifacts.get("candidate_version") or ""
        return f"{name} {ver or '(no version resource)'} [candidate]"
    return f"{r.oracle_version or '(version unknown)'} [oracle]"


def fixture_integrity() -> list[dict[str, Any]]:
    """Digest the read-only input manifests so a run ties to exact inputs.

    A digest change means the golden corpus moved under the harness, and runs
    made before and after such a change are not comparable. Recorded per run
    rather than asserted: the harness must never be the thing that decides the
    golden data is wrong.
    """
    import hashlib

    from . import manifests as man_mod

    rows: list[dict[str, Any]] = []
    for p in (man_mod.GOLDEN_DIR / "manifest.json",
              man_mod.LAYOUTS_DIR / "manifest.json",
              man_mod.DIR_DIR / "reports" / "manifest.json"):
        if not p.exists():
            rows.append({"path": str(p), "exists": False})
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        st = p.stat()
        rows.append({
            "path": str(p),
            "exists": True,
            "bytes": st.st_size,
            "sha256": digest,
            "sha256_grouped": " ".join(digest[i:i + 8] for i in range(0, 64, 8)),
            "mtime_local": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        })
    return rows


def _layout_agreement(results: list[dict[str, Any]]) -> list[str]:
    """Show how much of each layout match is engine vs normalizer.

    Three levels are reported side by side, because collapsing them into one
    number is exactly how a localization difference gets mistaken for an engine
    difference (see product/docs/02-version-and-evidence.md section 3.5).

    Takes result *dicts* (the JSON payload form) so it can run at render time
    without re-running anything.
    """
    rows = [r for r in results
            if r.get("suite") == "layout" and isinstance(r.get("parsed"), dict)]
    if not rows:
        return []
    out = ["| version | subject | cases | normalized==golden | "
           "raw==golden after time-only | raw bytes == golden |",
           "|---|---|---|---|---|---|"]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        key = (r.get("oracle_version")
               or r.get("artifacts", {}).get("candidate_version") or "(none)",
               r.get("subject", "?"))
        groups.setdefault(key, []).append(r)
    for (ver, subj), rs in sorted(groups.items()):
        n = len(rs)
        norm_ok = sum(1 for r in rs if r["parsed"].get("normalized_matches_golden"))
        time_ok = sum(1 for r in rs if r["parsed"].get("raw_equal_after_volatile_only"))
        raw_ok = sum(1 for r in rs if r["parsed"].get("raw_bytes_equal_golden"))
        out.append(f"| {ver} | {subj} | {n} | {norm_ok}/{n} | {time_ok}/{n} | {raw_ok}/{n} |")
    return out


def oracle_containment_summary(results: list[dict[str, Any]]) -> list[str]:
    """Report how the Oracle's process tree was contained on this run.

    Recorded rather than assumed: if Job-Object containment was unavailable, the
    run must say so, because that is the condition under which an orphaned
    ``BCompare.exe`` can stall or interfere with later calls.
    """
    rows = [r for r in results if r.get("subject") == "oracle"]
    if not rows:
        return []
    kinds: dict[str, int] = {}
    for r in rows:
        kind = (r.get("artifacts") or {}).get("containment", "unrecorded")
        kinds[kind] = kinds.get(kind, 0) + 1
    lines = ["| containment | Oracle calls |", "|---|---|"]
    for k, n in sorted(kinds.items()):
        lines.append(f"| `{k}` | {n} |")
    if kinds.get("job-object", 0) == 0 and rows:
        lines.append("")
        lines.append("**Warning:** Job-Object containment was not in force for "
                     "any Oracle call on this run. Orphaned `BCompare.exe` "
                     "processes cannot be ruled out; see README section 3a.")
    return lines


def build_payload(*, started: datetime, finished: datetime, harness_version: str,
                  ruleset_version: str, installs: dict[str, Any],
                  candidates: dict[str, Any], results: list[TestResult],
                  notes: list[str], commands: dict[str, str],
                  results_dir: str) -> dict[str, Any]:
    by_suite = summarize_by(results, lambda r: r.suite)
    by_suite_subject = summarize_by(results, lambda r: f"{r.suite}/{r.subject}")
    by_version = summarize_by(results, _version_key)
    failures = [
        {
            "test_id": r.test_id, "suite": r.suite, "subject": r.subject,
            "verdict": r.verdict.value, "detail": r.detail,
            "oracle_version": r.oracle_version, "exit_code": r.exit_code,
            "command": r.command, "raw_report": r.raw_report,
            "known_difference": r.known_difference,
        }
        for r in results if r.verdict != Verdict.PASS
    ]
    return {
        "harness_version": harness_version,
        "normalizer_ruleset": ruleset_version,
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "results_dir": results_dir,
        "install_identity": installs,
        "candidates": candidates,
        "fixture_integrity": fixture_integrity(),
        "totals": summarize(results),
        "by_suite": by_suite,
        "by_suite_subject": by_suite_subject,
        "by_version_and_subject": by_version,
        "non_pass": failures,
        "known_differences": KNOWN_DIFFERENCES,
        "label_mapping": [{"kind": k, "source": s, "normalised_to": d}
                          for k, s, d in label_mapping_table()],
        "uncovered_scope": list(UNCOVERED_SCOPE),
        "registry_scope_note": REGISTRY_SCOPE_NOTE,
        "version_scope_note": VERSION_SCOPE_NOTE,
        "notes": notes,
        "reproduce": commands,
        "results": [r.to_json() for r in results],
    }


def write_json(payload: dict[str, Any], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


def render_markdown(payload: dict[str, Any]) -> str:
    t = payload["totals"]
    L: list[str] = []
    L.append("# A-1 / M0 unified Oracle harness -- actual run report")
    L.append("")
    L.append(f"- harness version: `{payload['harness_version']}`")
    L.append(f"- normalizer rule-set: `{payload['normalizer_ruleset']}`")
    L.append(f"- started (UTC): {payload['started_utc']}")
    L.append(f"- finished (UTC): {payload['finished_utc']}")
    L.append(f"- results directory: `{payload['results_dir']}`")
    L.append("")
    L.append("## Install identity (measured from the files)")
    L.append("")
    for key, i in payload["install_identity"].items():
        L.append(f"### `{key}` -- {i['label']}")
        L.append("")
        L.append(f"- locale: `{i['locale']}` (evidence: {', '.join(i['localization_evidence'])})")
        L.append(f"- Oracle `BComp.com`: `{i['oracle_path']}`")
        L.append(f"  - version `{i['oracle_version'] or 'UNKNOWN'}`, {i['oracle_size']} bytes")
        L.append(f"  - sha256 `{i['oracle_sha256_grouped']}`")
        L.append(f"- engine `BCompare.exe`: `{i['app_path']}`")
        L.append(f"  - version `{i['app_version'] or 'UNKNOWN'}`, {i['app_size']} bytes")
        L.append(f"  - sha256 `{i['app_sha256_grouped']}`")
        L.append("")
    L.append("## Input fixture integrity (read-only; recorded, not modified)")
    L.append("")
    L.append("| manifest | bytes | sha256 (grouped) | mtime |")
    L.append("|---|---|---|---|")
    for row in payload.get("fixture_integrity", []):
        if not row.get("exists"):
            L.append(f"| `{row['path']}` | - | **MISSING** | - |")
        else:
            L.append(f"| `{row['path']}` | {row['bytes']} | `{row['sha256_grouped']}` "
                     f"| {row['mtime_local']} |")
    L.append("")
    L.append("## Totals (all subjects, all versions -- NOT a compatibility claim)")
    L.append("")
    L.append("| total | pass | fail | error | missing_output | timeout | unparseable | not_run |")
    L.append("|---|---|---|---|---|---|---|---|")
    L.append(f"| {t['total']} | {t['pass']} | {t['fail']} | {t['error']} | "
             f"{t['missing_output']} | {t['timeout']} | {t['unparseable']} | {t['not_run']} |")
    L.append("")
    L.append("## Per suite / subject")
    L.append("")
    L.append("| group | total | pass | fail | error | missing_output | timeout | unparseable | not_run |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k, s in payload["by_suite_subject"].items():
        L.append(f"| {k} | {s['total']} | {s['pass']} | {s['fail']} | {s['error']} | "
                 f"{s['missing_output']} | {s['timeout']} | {s['unparseable']} | {s['not_run']} |")
    L.append("")
    L.append("## Per version and subject (never merged)")
    L.append("")
    L.append("| version [subject] | total | pass | fail | error | missing_output | timeout | unparseable | not_run |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k, s in payload["by_version_and_subject"].items():
        L.append(f"| {k} | {s['total']} | {s['pass']} | {s['fail']} | {s['error']} | "
                 f"{s['missing_output']} | {s['timeout']} | {s['unparseable']} | {s['not_run']} |")
    L.append("")
    L.append("## Known differences (preserved, not special-cased)")
    L.append("")
    for k, v in payload["known_differences"].items():
        scope = KNOWN_DIFFERENCES_SCOPE.get(k, "?")
        L.append(f"- **`{k}`** (scope: {scope}) -- {v}")
    L.append("")
    L.append("## Oracle process containment (per call)")
    L.append("")
    L.append("`BComp.com` spawns `BCompare.exe` as a grandchild. Containment is "
             "recorded per call so a run cannot silently proceed without it; see "
             "README section 3a.")
    L.append("")
    L.extend(oracle_containment_summary(payload.get("results", []))
             or ["_no Oracle results in this run_"])
    L.append("")
    L.append("## Layout agreement: engine vs normalizer (per version, per subject)")
    L.append("")
    L.append("`normalized==golden` is the verdict basis. The two raw columns are "
             "diagnostic: they show how much of the match survives WITHOUT the "
             "label table, which is what distinguishes a localization difference "
             "from an engine difference.")
    L.append("")
    L.append("`raw bytes == golden` is 5/30 for **both** installs, and that is "
             "expected rather than a defect: the golden reports embed their own "
             "generation wall-clock, and the 5 cases that match byte-for-byte "
             "are exactly the 5 `patch` layouts, which carry no header or "
             "timestamp at all. The `raw==golden after time-only` column is "
             "therefore the meaningful one -- it reproduces the audit's "
             "independently measured 30/30 (reference) and 5/30 (current, "
             "remaining 25 are Chinese labels).")
    L.append("")
    L.extend(_layout_agreement(payload.get("results", []))
             or ["_no layout results in this run_"])
    L.append("")
    L.append("## Confirmed normalisation label pairs")
    L.append("")
    L.append("Every pair below was observed by running both installs on the same "
             "fixtures and diffing. No pair is inferred.")
    L.append("")
    L.append("| kind | source (as emitted) | normalised to |")
    L.append("|---|---|---|")
    for kind, src, dst in label_mapping_table():
        L.append(f"| {kind} | `{src}` | `{dst}` |")
    L.append("")
    L.append("## Uncovered scope (read this before quoting any number)")
    L.append("")
    for u in UNCOVERED_SCOPE:
        L.append(f"- {u}")
    L.append("")
    # The registry suite carries its own scope note: its oracle failures on
    # the Chinese install are the locale-dependent table geometry, not a
    # defect (see REGISTRY_SCOPE_NOTE for the measurement trail).
    if any(r["suite"] == "reg" for r in payload["results"]):
        L.append("### Registry suite scope note")
        L.append("")
        L.append(REGISTRY_SCOPE_NOTE)
        L.append("")
    if any(r["suite"] == "ver" for r in payload["results"]):
        L.append("### Version suite scope note")
        L.append("")
        L.append(VERSION_SCOPE_NOTE)
        L.append("")
    if payload["non_pass"]:
        L.append("## Every non-pass result")
        L.append("")
        L.append("| test | suite | subject | verdict | detail |")
        L.append("|---|---|---|---|---|")
        for f in payload["non_pass"]:
            det = (f["detail"] or "").replace("|", "\\|")
            L.append(f"| `{f['test_id']}` | {f['suite']} | {f['subject']} | "
                     f"**{f['verdict']}** | {det[:200]} |")
        L.append("")
    else:
        L.append("## Every non-pass result")
        L.append("")
        L.append("_none_")
        L.append("")
    L.append("## Notes")
    L.append("")
    for n in payload["notes"]:
        L.append(f"- {n}")
    L.append("")
    L.append("## Reproduce")
    L.append("")
    L.append("```bash")
    for k, v in payload["reproduce"].items():
        L.append(f"# {k}")
        L.append(v)
    L.append("```")
    L.append("")
    return "\n".join(L)


def write_markdown(payload: dict[str, Any], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(payload), encoding="utf-8")

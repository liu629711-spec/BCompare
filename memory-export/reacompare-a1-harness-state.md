---
name: reacompare-a1-harness-state
description: A-1/M0 Oracle verification harness state in product/verify —
  measured pass rates, the process-tree containment fix, and the
  guard/normalizer invariants that must not regress
metadata:
  node_type: memory
  type: project
  originSessionId: sess_7cdaae35-9b46-4d85-8685-3c40185a069a
---

Task A-1 / M0 (unified Oracle verification harness) completed and verified 2026-10-13. It lives in `D:\Rea\product\verify\` and is the acceptance gate for all later ReaCompare work.

**Measured results** (reproduce: `cd D:\Rea && python -m pytest product/verify/tests -q -p no:cacheprovider`, and `cd D:\Rea\product\verify && python -m harness.run_cli --install current --install reference --candidate bcx-prototype --run-name <name>`):

- Unit tests: **157 passed** (41 normalize / 77 runner / 10 mutation / 20 live Oracle / 9 process-tree).
- Full runner: **257 total, 256 pass, 1 fail, 0 error/timeout/unparseable/not_run**.
- Text anchors on current 5.2.1.32035: **45/45**. On reference 5.2.6.32774: **45/45**. Reported separately, never merged.
- Layouts: Oracle **30/30**; candidate (`bcx-prototype`) **29/30**.
- Folder recipe: 1 fixture pair × 2 installs, exit 0, 2026 bytes. Recipe-only, explicitly NOT a compatibility claim.
- Labels corroboration: 30/30 (zh and en reports normalize identically).

**Known difference, deliberately preserved:** `mixed-side-by-side` fails for the candidate only (`real diff 1 <> real diff 9` vs `real diff 1    real diff 9`). It appears TWICE — as layout/oracle (pass) and layout/candidate (fail). Tagged `known_difference` but the verdict stays `fail`; the tagging code only annotates when verdict is already fail, it never converts. Never add a special case for it.

**Process-tree containment (the important robustness fix).** `BComp.com` is a launcher stub (its version resource says 5.0.3.30240 in BOTH installs; the real engine is `BCompare.exe`). It spawns `BCompare.exe` as a GUI-host grandchild. A plain `subprocess.run(timeout=...)` kills only the direct child, orphaning the grandchild — and the orphan holds the inherited stdout/stderr pipes, so `communicate()`'s post-kill drain blocks unbounded. That is what caused a modal crash dialog to stall an acceptance run for ~20 minutes.

Fix: Windows **Job Object** with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, process created `CREATE_SUSPENDED` and resumed (via `NtResumeProcess`) only after job assignment, to close the spawn race. Closed on every exit path. Verified: forced-timeout probe gives `tree_killed=True containment=job-object` and zero orphans at +0/+5/+10s.

**A modal crash dialog cannot be prevented from Python — only survived.** `/silent` does not suppress BC's application-crash dialog. The harness contains rather than prevents it; this is documented as a known gap in README §11. Do not claim it is fixed.

**Normalizer invariants (must not regress).** Rule set is versioned (`norm-1`). It only rewrites confirmed label text and volatile timestamps; unknown tags/attributes/statuses/labels raise `NormalizerRefusal` (`unparseable` / `needs-normalizer-update`) rather than guessing. Status vocabulary is validated but never rewritten. Both pre- and post-normalization reports are retained.

Proven to genuinely detect erasure: I injected an adversarial weakening of `_xml_key` (dropping attributes and text) and **5 mutation tests immediately failed** — the ones guarding XML status, `ltid`/`rtid`, text content, element order, and the error line number. Paired controls (`test_unmutated_golden_still_passes`, `test_label_only_mutation_is_normalized_away`) prevent vacuous passing. Re-run this experiment before trusting any future normalizer change.

**Write guard** (`assert_writable`) is now an **allow-list inversion**: only the run's own directory under `product/verify/runs/` is writable; everything else is refused, including not-yet-existing paths and `report-*.md` via glob. Verified 17/17 cases. Both `harness/` and `tests/` inside `product/verify` are themselves refused so the harness cannot overwrite its own source.

**Environment traps rediscovered and handled in code:** `Path.read_text` silently translates CRLF→LF (would hide real line-ending differences — the harness reads raw bytes); 3 golden XMLs contain XML-illegal character references (`&#1;`, `&#0;`, `&#26;`) and fail strict parsers; the Chinese repack's own count labels are inconsistent (`个重要的左边独有行` has 的, `个重要右边独有行` does not) so only observed variants are listed.

See [[reacompare-audit-findings]] for the install identities and localization facts this harness depends on.

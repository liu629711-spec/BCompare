---
name: bcompare-clone-goal
description: The user's goal is to build a Beyond Compare product (capabilities
  fully inherited, UI self-designed since 2026-10-22 — see
  [[reacompare-product-direction]]); records the verified oracle harness, BC's
  real default importance rules, and the honest scope assessment
metadata:
  node_type: memory
  type: project
  originSessionId: sess_58b1b22a-e920-40ba-a069-e7e582126d17
---

The user's goal for the `D:\Rea` work is **to clone Beyond Compare as a product**, not merely to study it. Recorded 2026-10-12.

**Verified oracle (the key enabler).** `BComp.com` works headlessly in evaluation mode (30-day trial active). The working invocation is `BComp.com /silent @<script> <left> <right> <output>` with script line `text-report layout:xml output-to:"%3" "%1" "%2"`. Critical gotcha: **`load` only accepts folders** — using it on files fails with exit code 107 and `Fatal Scripting Error: Unable to load base folder`. File comparisons must pass paths straight to `text-report`. Exit codes: 104 = trial expired, 105 = error loading script, 106 = syntax error, 107 = failed to load folders/files. Tools: `tools/bc-oracle.py`, `tools/bc-align-verify.py`, `tools/bc-anchors.py` (8/8 anchors pass). BC's `layout:xml` report is the ideal oracle — one `<linecomp status=...>` per alignment group with `ltid`/`rtid`.

**BC's real default importance rules (measured, corrected an earlier inference):** whitespace is NOT important by default (leading, embedded, trailing, and operator-adjacent spacing all yield `similar`); case IS important by default (identifiers, keywords, string contents all yield `different`); operators, numbers, and Directives always yield `different`. Enabling `ignore-unimportant` collapses `similar` to `same` (merging the line ids) and leaves `different` untouched.

**Scope reality.** Full BC clone ≈ 11× the text-comparison core: 11 view types, 398 commands, 7 content engines, 25 format grammars, a 17-unit VFS layer, 211 UI forms. Estimate 3–5 person-years. Commercial third-party components are the real blocker — **FlexCel** (Excel) and **SecureBlackbox** (SSH/TLS) are paid; Indy10/Abbrevia/JCL are open source. BC's license forbids copying its code or resources, so the clone must be an independent implementation guided by observed behavior and extracted specs.

**Agreed direction:** build the text-comparison MVP first (lexer from `bcfileformats-spec.json` → Myers alignment → three-state importance → BC-compatible XML report), with anchor pass rate as the acceptance metric. Official help docs extracted to `D:\Rea\help\` (469 files from BCompare.chm) for feature boundary reference. See [[rea-project-state]] for the reverse-engineering toolchain.

**Decompilation layer COMPLETE (2026-10-12, later same day).** The user held the build until full RE — correct call. Function attribution was propagated from the 1,337 assertion anchors to 28,126 functions via Delphi's contiguous unit linking (`tools/attribute-functions.py`), revealing **19,014 BC-own functions across 190 units**. A 49-batch campaign (`tools/build-campaign.py`, `tools/run-campaign.py`) decompiled all of them: **19,014/19,014, zero failures, 16 MB of pseudocode** in `D:\Rea\extracted\pseudocode\` (~15 minutes of compute — batch decompile is ~400 fns/15 s). Watch out: unit attribution is only as good as the anchor coverage; ViewText.pas (503 fns) was initially missing from the phase list and needed a fill batch.

**What "fully reverse-engineered" still requires** — the decompilation is raw material, not understanding. Remaining layers: (1) analysis: read 19,014 functions into per-unit specs (triage: ~45% trivial getters/thunks, ~30% UI plumbing, ~25% substantive logic ≈ 4,700 functions needing real analysis — the 55 KB `SsEditStack` functions are the giants); (2) behavioral anchors: 8 → hundreds via the oracle; (3) per-module clone specs. The user's principle: no building until a module's spec is complete and oracle-verified.

# U2/U2b/U3 probe findings -- importance edges, orphans, summary (task M2)

- Drivers: `probes/u2_element_edges.py`, `probes/u2b_orphan_semantics.py`,
  `probes/u3_leftsimilar_options.py`, `probes/u3b_summary_order.py`
- Raw runs: `runs/u2-probe-20261013T172214Z/`, `runs/u2b-probe-20261013T172924Z/`,
  `runs/u3-probe-leftsimilar/`, `runs/u3b-probe-summary-order/`
- Oracle: current install (5.0.3.30240 zh), live `BComp.com`, `text-report`,
  two modes (default / `options:ignore-unimportant`) unless noted; all exits 0;
  job-object containment on every call; serial.

Together with `U1-FINDINGS.md` these are the O-level spec the M2 engine
(`product/core/src/importance.rs`) implements.

## 1. The per-element rule generalizes (U2)

| probe (.c unless noted) | default | ignore-unimportant | verdict |
|---|---|---|---|
| mixed-trailing-comment (`x = 1; // note` vs `// other`) | similar | **same** | unimportant |
| mixed-lead-comment (`/* head */ int x;`) | similar | **same** | unimportant |
| block-comment-body (3-line `/* */`) | same,similar,same,same | all same | unimportant, **cross-line state** |
| block-continuation-star (` * alpha`) | similar line | same | unimportant |
| string-internal-ws (`"a b"` vs `"a  b"`) | different | different | IMPORTANT |
| string-case / string-unterminated / string-escaped-quote | different | different | IMPORTANT |
| comment-syntax-swap (`// a` vs `/* a */`) | similar | same | unimportant |
| comment-vs-empty (`// note` vs ``) | similar | same | unimportant — same align class |
| blank-vs-ws (`` vs `   `) | similar | same | unimportant |
| number-hex / number-exponent | different | different | IMPORTANT |
| py-comment / py-hash-midline / py-trailing-ws | similar | same | unimportant |
| **py-indent** (`x = 1` vs `    x = 1`) | **different** | different | IMPORTANT (BC's `Indent` element) |
| py-triple-quote (body line) | different | different | IMPORTANT, **cross-line state** |
| js-comment | similar | same | unimportant |
| js-regex-literal / js-regex-ws | different | different | IMPORTANT (regex literals are strings) |
| js-template-literal (backticks) | different | different | IMPORTANT (no grammar element) |
| **foo-case** (`.foo`, `Alpha` vs `alpha`) | **similar** | same | unknown extensions are PLAIN TEXT |
| **foo-comment** (`.foo`, `// a` vs `// b`) | **different** | different | no comment rules in plain text |
| foo-syntax / foo-comment-vs-code (`.foo`) | different | different | plain text |

**Model settled:** a changed pair is unimportant iff every differing element
is comment/whitespace (U1) — and it holds for mixed lines, cross-line block
comments, triple-quoted strings, and Python indent is the notable IMPORTANT
whitespace-shaped exception. Unknown extensions compare as plain text
(case-insensitive, no comments), replacing the M1 guess.

## 2. One-sided unimportant lines get their own statuses (U2b)

A leftover (one-sided) line is **`leftsimilar`/`rightsimilar`** when its
content is entirely unimportant (comment, blank, whitespace-only, empty) and
`leftorphan`/`rightorphan` when it has any important content. Per-line within
one leftover run (`orphan-comment-trailing`: `different, leftorphan,
leftsimilar`). The M1 anchor `al-empty-left` stays `rightorphan` because its
orphaned line has content.

Under `ignore-unimportant` these fold to `same` and carry a **borrowed id**:

* folded leftsimilar row: `<text ltid="own" rtid="borrowed">left text</text>`
  — the borrowed rtid comes from the nearest preceding paired row, `0` if
  none (`orphan-comment-lead+iu`: `rtid="0"`; `iu-three-comments-one+iu`:
  three rows all reuse `rtid="1"`).
* folded rightsimilar row: `<text ltid="borrowed" rtid="own"/>` —
  **self-closing, no content** (`orphan-right-comment+iu`).
* comment-vs-code and empty-vs-code stay `different` under ignore-unimportant
  (paired, important difference).
* `leftorphan`/`rightorphan` are never folded.

## 3. Block pairing tie-break (U2b + M2 anchors)

Inside an unmatched block, BC pairs content lines with content lines (k-th ↔
k-th) and leaves unimportant lines as one-sided, **but only when that pairs
as many lines as plain top-first positional pairing**:

* `orphan-comment-lead` (`// c, int b;` vs `int x;`): `[leftsimilar, different]`
* `orphan-comment-mid` (`int a;, // c, int b;` vs `int x;, int y;`):
  `[different, leftsimilar, different]`
* `orphan-comment-trailing` (`int a;, int b;, // c` vs `int x;`):
  `[different, leftorphan, leftsimilar]`
* but `orphan-comment-inside-replace` (`// a, int b;` vs `int x;, int y;`):
  positional wins (`[different, different]`) because it pairs 2 lines instead of 1.

Implemented as `align::pair_block`'s two strategies. **Known divergence (not
anchored):** in files with SEVERAL unimportant lines adjacent to replace runs,
BC's Myers tie-break can pick a different (equal-cost) match set than ours —
u3b `all-kinds` (`// a, int p;, // q, int r;` vs `int x;, // b, int y;, // s`)
produces BC `[leftsimilar, different, similar, different, rightsimilar]` while
ours produces a different equal-cost grouping. Closing this needs a weighted
diff (free deletion of unimportant lines); recorded in
`07-m2-importance.md` as follow-up work.

## 4. Display options and summary (U3/U3b)

* `display-mismatches` keeps `similar` AND `leftsimilar` rows;
  `display-matches` drops them; `display-context` keeps everything.
* Summary count-line order (zero counts omitted):
  `same → unimportant left orphan → unimportant right orphan → unimportant
  difference → important left orphan → important right orphan → important
  difference → difference section(s)`.
* The English reference install prints exactly
  `unimportant left orphan line(s)` / `unimportant right orphan line(s)` —
  the labels the product uses. (The zh current install prints
  `个不重要的左边独有行` / `个不重要的右边独有行`.)
* Statistics uses an I/U column model (a leftsimilar row counts as U-deleted);
  our statistics layout keeps M1 semantics — recorded as a known difference,
  no statistics anchor.

## Corpus impact

56 new XML anchors (`m2-*` keys, `verify/golden/manifest.json` 45 → 101) and
one new layout case (`comments-summary`, golden report from the English
reference install so the layout corpus stays consistent). Generated by
`tools/m2_add_golden_anchors.py`.

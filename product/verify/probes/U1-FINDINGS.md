# U1 probe findings -- element importance, observed (task A-4, 2026-10-13)

- Driver: `probes/u1_element_importance.py`
- Raw runs: `runs/u1-probe-20261013T155009Z/` and `runs/u1-probe-20261013T155059Z/` (the second adds whitespace classes)
- Oracle: current install, live `BComp.com`, `text-report layout:xml`, two modes per pair
- Containment: job-object on every call; all exits 0

## The observed table (syntax-aware `.c` format)

| token class (only difference on the line) | default | `options:ignore-unimportant` | verdict |
|---|---|---|---|
| directive (`#include <stdio.h>` vs `<stdlib.h>`) | different | **different** | IMPORTANT |
| operator (`a + b` vs `a - b`) | different | **different** | IMPORTANT |
| identifier (`alpha1` vs `alpha2`) | different | **different** | IMPORTANT |
| number (`10` vs `20`) | different | **different** | IMPORTANT |
| string (`"abc"` vs `"abd"`) | different | **different** | IMPORTANT |
| keyword (`unsigned` vs `signed`) | different | **different** | IMPORTANT |
| identifier case (`Alpha` vs `alpha`) | different | **different** | IMPORTANT |
| comment (`// alpha` vs `// beta`) | similar | **same** | unimportant -- folded |
| whitespace internal (`int  x` vs `int x`) | similar | **same** | unimportant -- folded |
| whitespace trailing (`int x;   ` vs `int x;`) | similar | **same** | unimportant -- folded |
| control (identical) | same | same | — |

## Verdict (upgrades U1 from I to O)

**"Element index 6/9 forced important" is not needed as an implementation
spec.** The observable rule for syntax-aware formats is line-level and simple:

> A changed line is **unimportant** (`similar`, folded to `same` by
> `ignore-unimportant`) **iff every differing element on it is a comment or
> whitespace element.** Any difference in a directive, operator, identifier,
> number, string, keyword, or identifier case makes the line **important**
> (`different`), and `ignore-unimportant` never folds it.

The internal index-6/9 mapping stays I-level forever (not CLI-observable);
the behavioural table above is the O-level spec M2 implements.

## Boundaries of this evidence

- Single-line pairs, one class per pair; **mixed** lines (comment+identifier
  on one line) are implied by the per-element rule but not directly probed --
  M2 should add that anchor.
- Format `.c` only. Non-syntax-aware `.txt` already has its own observed rule
  (case → similar, `case-txt` anchor). M2 implements per-format tables; this
  probe is the `.c`/syntax-aware baseline.
- "Forced" in the strong sense (immune to user Weights) is not CLI-testable;
  the two modes above are the observable contract.

"""Anchored behavior tests for a Beyond Compare-compatible text differ.

Each case states an input pair and the alignment BC itself produces, captured
from `text-report layout:xml` via tools/bc-oracle.py. A candidate differ is
checked against these anchors, so "compatible with BC" becomes a measurable
claim instead of an opinion.

Status vocabulary BC uses (verified, not assumed):
  same         - lines align and match
  similar      - lines align; differences are all unimportant
  different    - lines align; at least one important difference
  leftorphan   - line exists only on the left
  rightorphan  - line exists only on the right
  ignore-unimportant collapses `similar` to `same` and merges the line ids.
"""
import importlib.util
import pathlib
import subprocess

TOOLS = pathlib.Path(r"D:\Rea\tools")
WORK = pathlib.Path(r"D:\Rea\verify\cases")

# Load the oracle driver by path (the module name has a hyphen).
_spec = importlib.util.spec_from_file_location("bc_oracle", TOOLS / "bc-oracle.py")
bc_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc_oracle)

CASES = [
    {
        "name": "line-replace-and-append",
        "left": "line one\nline two\nline three\ncommon\n",
        "right": "line one\nline TWO changed\nline three\ncommon\nadded at end\n",
        "expect": ["same", "different", "same", "same", "rightorphan"],
    },
    {
        "name": "whitespace-is-similar",
        "left": "void main() { }\n",
        "right": "void main( ) { }\n",
        "expect": ["similar"],
    },
    {
        "name": "directive-is-important",
        "left": "#include <stdio.h>\n",
        "right": "#include <stdlib.h>\n",
        "expect": ["different"],
    },
    {
        "name": "leading-orphan",
        "left": "added first\nshared\n",
        "right": "shared\n",
        "expect": ["leftorphan", "same"],
    },
    {
        "name": "pure-insertion",
        "left": "a\nc\n",
        "right": "a\nb\nc\n",
        "expect": ["same", "rightorphan", "same"],
    },
    {
        "name": "pure-deletion",
        "left": "a\nb\nc\n",
        "right": "a\nc\n",
        "expect": ["same", "leftorphan", "same"],
    },
    {
        "name": "identical",
        "left": "x\ny\n",
        "right": "x\ny\n",
        "expect": ["same", "same"],
    },
    {
        "name": "empty-vs-content",
        "left": "",
        "right": "only line\n",
        "expect": ["rightorphan"],
    },
]


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    print("Anchored tests against Beyond Compare's own output")
    print("=" * 66)
    failures = 0

    for case in CASES:
        left = WORK / f"{case['name']}-L.txt"
        right = WORK / f"{case['name']}-R.txt"
        out = WORK / f"{case['name']}.xml"
        left.write_text(case["left"], encoding="utf-8", newline="")
        right.write_text(case["right"], encoding="utf-8", newline="")

        result = bc_oracle.run_report(left, right, out, layout="xml",
                                      options="display-all")
        if result["exit_code"] != 0:
            print(f"  FAIL {case['name']:<26} oracle exit={result['exit_code']}")
            failures += 1
            continue

        # Parse statuses in order.
        statuses = []
        for line in result["output"].splitlines():
            stripped = line.strip()
            if stripped.startswith("<linecomp"):
                statuses.append(stripped.split('status="')[1].split('"')[0])

        ok = statuses == case["expect"]
        mark = "ok  " if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  {mark} {case['name']:<26} {statuses}")
        if not ok:
            print(f"       expected: {case['expect']}")

    print()
    print(f"{len(CASES) - failures}/{len(CASES)} anchors captured")
    if failures:
        print("Note: a FAIL here means the *capture* disagrees with the assumption,")
        print("      not that BC is wrong - update the expectation to BC's actual output.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

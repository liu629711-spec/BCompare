"""Compare a candidate differ's output against Beyond Compare's XML report.

BC's `text-report layout:xml` emits one <linecomp> per alignment group with a
status of same / different / leftorphan / rightorphan, plus the line numbers on
each side. That is a precise, machine-readable statement of BC's alignment
decision, which makes it the right oracle for checking a reimplementation.

This module extracts that structure from a BC report and diffs it against a
candidate produced in the same shape, so alignment disagreements are reported
per line rather than as a blob.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class LineComp:
    """One alignment group from a BC XML report."""
    status: str
    left_texts: list[str] = field(default_factory=list)
    right_texts: list[str] = field(default_factory=list)
    left_ids: list[int] = field(default_factory=list)
    right_ids: list[int] = field(default_factory=list)


def parse_bc_xml(text: str) -> list[LineComp]:
    """Extract the ordered alignment groups from a BC XML report."""
    # BC writes no XML declaration namespace, but stray control chars can appear.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    root = ET.fromstring(text)
    comps: list[LineComp] = []
    for node in root.iter("linecomp"):
        comp = LineComp(status=node.get("status", ""))
        for text_node in node.findall("text"):
            value = text_node.text or ""
            if text_node.get("ltid") is not None:
                comp.left_texts.append(value)
                comp.left_ids.append(int(text_node.get("ltid")))
            if text_node.get("rtid") is not None:
                comp.right_texts.append(value)
                comp.right_ids.append(int(text_node.get("rtid")))
        comps.append(comp)
    return comps


def compare_alignments(oracle: list[LineComp], candidate: list[LineComp]) -> dict:
    """Report per-position agreement between two alignment sequences."""
    mismatches = []
    for index in range(max(len(oracle), len(candidate))):
        expected = oracle[index] if index < len(oracle) else None
        actual = candidate[index] if index < len(candidate) else None
        if expected is None or actual is None:
            mismatches.append({
                "index": index,
                "kind": "length",
                "expected": expected.status if expected else None,
                "actual": actual.status if actual else None,
            })
            continue
        if expected.status != actual.status:
            mismatches.append({
                "index": index,
                "kind": "status",
                "expected": expected.status,
                "actual": actual.status,
                "expected_left": expected.left_texts,
                "actual_left": actual.left_texts,
            })
        elif expected.left_texts != actual.left_texts or expected.right_texts != actual.right_texts:
            mismatches.append({
                "index": index,
                "kind": "content",
                "expected": expected.left_texts + expected.right_texts,
                "actual": actual.left_texts + actual.right_texts,
            })

    same = sum(1 for a, b in zip(oracle, candidate) if a.status == b.status)
    return {
        "oracle_groups": len(oracle),
        "candidate_groups": len(candidate),
        "matching_status": same,
        "agreement": same / max(1, len(oracle)),
        "mismatches": mismatches,
    }


if __name__ == "__main__":
    import pathlib

    report = pathlib.Path(r"D:\Rea\verify\oracle\report-xml.txt").read_text(encoding="utf-8")
    groups = parse_bc_xml(report)
    print(f"BC alignment groups: {len(groups)}\n")
    for index, group in enumerate(groups, 1):
        left = " | ".join(group.left_texts) or "—"
        right = " | ".join(group.right_texts) or "—"
        print(f"  {index}. {group.status:<12} L[{left}]  R[{right}]")

    # Self-comparison must be a perfect match; that validates the harness itself.
    verdict = compare_alignments(groups, groups)
    print(f"\nself-check agreement: {verdict['agreement']:.0%} "
          f"(mismatches={len(verdict['mismatches'])})")

"""Propagate unit attribution across the whole function table.

Delphi's linker places each compiled unit's code contiguously, so a function
that asserts from ``SsLineList.pas`` marks an address inside that unit's block.
With 1,337 such anchors over 121,485 functions (1.1%), every gap between two
anchors of the *same* unit can be attributed to that unit with high confidence;
gaps bounded by two different units are split at the boundary heuristic and
marked lower confidence.

This turns partial assertion-based attribution into a near-complete
function-to-unit map, which is what makes a full-coverage reverse-engineering
campaign addressable module by module.
"""
import json
import pathlib
import collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
OUT = ROOT / "function-attribution.json"

functions: list[tuple[str, int]] = []
for line in (ROOT / "functions.tsv").read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
    parts = line.split("\t")
    if len(parts) >= 4:
        functions.append((parts[0], int(parts[2])))

mods = json.loads((ROOT / "source-modules.json").read_text(encoding="utf-8"))
anchor_unit: dict[str, str] = {}
anchor_path: dict[str, str] = {}
for path, fns in mods["path_to_functions"].items():
    unit = path.split("\\")[-1]
    for fn in fns:
        anchor_unit[fn] = unit
        anchor_path[fn] = path

index_of = {addr: i for i, (addr, _) in enumerate(functions)}
anchors = sorted((index_of[a], a, u) for a, u in anchor_unit.items() if a in index_of)

SAME_UNIT_MAX_GAP = 60          # functions between two anchors of one unit
BOUNDARY_MAX_GAP = 15           # gap bounded by two different units

attribution: dict[str, dict] = {}
stats = collections.Counter()

for i, (addr, size) in enumerate(functions):
    if addr in anchor_unit:
        attribution[addr] = {
            "unit": anchor_unit[addr], "path": anchor_path[addr],
            "confidence": "anchor", "size": size,
        }
        stats["anchor"] += 1
        continue

    # Nearest anchor above and below.
    lo = i - 1
    while lo >= 0 and functions[lo][0] not in anchor_unit:
        lo -= 1
    hi = i + 1
    while hi < len(functions) and functions[hi][0] not in anchor_unit:
        hi += 1

    lo_anchor = anchors[[a for a, _, _ in anchors].index(lo)] if lo >= 0 else None
    # Simpler: look up units directly.
    lo_unit = anchor_unit[functions[lo][0]] if lo >= 0 else None
    hi_unit = anchor_unit[functions[hi][0]] if hi < len(functions) else None
    lo_dist = i - lo if lo >= 0 else None
    hi_dist = hi - i if hi < len(functions) else None

    def unit_matches(unit: str) -> bool:
        return unit is not None and (
            (lo_unit == unit and lo_dist is not None and lo_dist <= SAME_UNIT_MAX_GAP)
            or (hi_unit == unit and hi_dist is not None and hi_dist <= SAME_UNIT_MAX_GAP)
        )

    assigned = None
    confidence = None
    if lo_unit and lo_unit == hi_unit and lo_dist <= SAME_UNIT_MAX_GAP and hi_dist <= SAME_UNIT_MAX_GAP:
        assigned, confidence = lo_unit, "interior-same-unit"
    elif lo_unit and lo_dist <= SAME_UNIT_MAX_GAP and (hi_dist is None or hi_dist > SAME_UNIT_MAX_GAP):
        assigned, confidence = lo_unit, "edge-nearest"
    elif hi_unit and hi_dist <= SAME_UNIT_MAX_GAP and (lo_dist is None or lo_dist > SAME_UNIT_MAX_GAP):
        assigned, confidence = hi_unit, "edge-nearest"
    elif lo_unit and hi_unit and lo_dist <= BOUNDARY_MAX_GAP and hi_dist <= BOUNDARY_MAX_GAP:
        # Boundary between two units: attribute to the nearer anchor, flagged.
        assigned = lo_unit if lo_dist <= hi_dist else hi_unit
        confidence = "boundary-guess"

    if assigned:
        attribution[addr] = {
            "unit": assigned,
            "confidence": confidence,
            "size": size,
        }
        stats[confidence] += 1
    else:
        stats["unattributed"] += 1

total = len(functions)
covered = len(attribution)
print(f"总函数: {total:,}")
print(f"可归属: {covered:,} ({covered/total*100:.1f}%)")
print(f"  anchor:              {stats['anchor']:,}")
print(f"  interior-same-unit:  {stats['interior-same-unit']:,}")
print(f"  edge-nearest:        {stats['edge-nearest']:,}")
print(f"  boundary-guess:      {stats['boundary-guess']:,}")
print(f"  unattributed:        {stats['unattributed']:,}")
print()

by_unit = collections.Counter()
by_unit_bytes = collections.Counter()
for addr, info in attribution.items():
    by_unit[info["unit"]] += 1
    by_unit_bytes[info["unit"]] += info["size"]
print(f"归属后的单元数: {len(by_unit)}")
print()
print(f'{"单元":<28} {"函数":>7} {"字节":>10}')
print("-" * 50)
for unit, n in by_unit.most_common(30):
    print(f"{unit:<28} {n:>7} {by_unit_bytes[unit]:>10,}")

OUT.write_text(json.dumps({
    "total_functions": total,
    "attributed": covered,
    "by_unit": dict(by_unit),
    "functions": attribution,
}, ensure_ascii=False), encoding="utf-8")
print(f"\nwrote {OUT}")

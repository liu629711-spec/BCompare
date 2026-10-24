"""Batch-parse every TPF0 stream in rcdata into one consolidated UI spec.

The existing single-file parser reports `consumed` vs `size`, which is the honest
measure of how much of each stream was understood. This driver runs it across all
211 UI blobs, keeps the ones that parse cleanly, and emits a per-form summary plus
a combined object census so the whole UI surface is inspectable at once.
"""
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tpf0_parse import flatten, parse_stream  # noqa: E402

RCDATA = pathlib.Path(r"D:\Rea\extracted\rcdata")
OUT = pathlib.Path(r"D:\Rea\extracted\ui-spec.json")

blobs = sorted(f for f in RCDATA.glob("*.bin") if f.read_bytes()[:4] == b"TPF0")

forms = []
class_census = collections.Counter()
prop_census = collections.Counter()
failures = []

for blob in blobs:
    data = blob.read_bytes()
    try:
        parsed = parse_stream(data)
    except Exception as exc:  # record rather than silently drop
        failures.append({"name": blob.stem, "error": f"{type(exc).__name__}: {exc}"})
        continue

    flat = [item for root in parsed["roots"] for item in flatten(root)]
    for item in flat:
        class_census[item["class"]] += 1
        for prop in item["props"]:
            prop_census[prop] += 1

    forms.append({
        "name": blob.stem,
        "bytes": parsed["size"],
        "consumed": parsed["consumed"],
        "complete": parsed["consumed"] == parsed["size"],
        "object_count": len(flat),
        "roots": [r["class"] for r in parsed["roots"]],
        "objects": flat,
    })

complete = [f for f in forms if f["complete"]]
OUT.write_text(json.dumps({
    "form_count": len(forms),
    "fully_parsed": len(complete),
    "top_classes": class_census.most_common(40),
    "top_properties": prop_census.most_common(40),
    "failures": failures,
    "forms": forms,
}, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"TPF0 blobs: {len(blobs)}")
print(f"parsed: {len(forms)}  fully consumed: {len(complete)}  partial/failed: {len(blobs) - len(complete)}")
print(f"total objects: {sum(f['object_count'] for f in forms)}")
print(f"\ntop classes:")
for cls, count in class_census.most_common(20):
    print(f"  {count:5d}  {cls}")
print(f"\ntop properties:")
for prop, count in prop_census.most_common(15):
    print(f"  {count:5d}  {prop}")
if failures:
    print(f"\nfailures: {len(failures)}")
    for item in failures[:10]:
        print(f"  {item['name']}: {item['error']}")
print(f"\nwrote {OUT}")

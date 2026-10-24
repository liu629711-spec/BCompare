"""Extract Beyond Compare's internal module layout from assertion source paths.

BC's assertion helpers embed the original build paths, e.g.
``C:\\BCBuild\\BCompare\\Source\\Ss\\SsPersistent.pas``. Those paths survived
compilation into the shipped binary, so they expose the program's real module
structure — something no amount of decompiling would hand over so cleanly.

This reads the string-to-function index, collects every embedded build path, and
groups them by module so the architecture is visible at a glance.
"""
import collections
import json
import pathlib
import re

INDEX = pathlib.Path(r"D:\Rea\extracted\string-function-index.tsv")
OUT = pathlib.Path(r"D:\Rea\extracted\source-modules.json")

PATH_PATTERN = re.compile(r"C:\\BCBuild\\[^\s\"']+")

path_to_functions: dict[str, set[str]] = collections.defaultdict(set)
for line in INDEX.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
    parts = line.split("\t")
    if len(parts) < 4:
        continue
    text, entry = parts[1], parts[2]
    for match in PATH_PATTERN.findall(text):
        path_to_functions[match].add(entry)

modules: dict[str, list[str]] = collections.defaultdict(list)
unit_names: dict[str, str] = {}
for path in sorted(path_to_functions):
    parts = path.split("\\")
    # ...\BCompare\Source\<module>\<file>
    if len(parts) >= 5:
        modules[parts[3]].append(path)
    unit_names[path] = path.split("\\")[-1]

OUT.write_text(json.dumps({
    "path_count": len(path_to_functions),
    "function_count": len({fn for fns in path_to_functions.values() for fn in fns}),
    "modules": {name: sorted(paths) for name, paths in sorted(modules.items())},
    "path_to_functions": {path: sorted(fns) for path, fns in sorted(path_to_functions.items())},
}, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"distinct source paths: {len(path_to_functions)}")
print(f"functions carrying a build path: {len({fn for fns in path_to_functions.values() for fn in fns})}")
print(f"modules: {len(modules)}")
print()
print("=== by module ===")
for name, paths in sorted(modules.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(paths):4d}  {name}")
print()
print("=== text/diff-related units ===")
for name in sorted(modules):
    if name.lower() in {"ss", "text", "dir", "core", "cmp", "common", "file", "rules", "grammar"}:
        for path in sorted(modules[name]):
            print(f"  {path.split(chr(92))[-1]}")
print(f"\nwrote {OUT}")

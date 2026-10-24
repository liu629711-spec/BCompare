"""Map BC's source units to the functions that assert from them.

Each assertion helper in BC embeds its originating source path, so a function
that asserts from ``BcAlignLines.pas`` *is* part of the line-alignment algorithm.
That gives a precise address map for the modules that matter, which is far better
than guessing from function size or string proximity.

Reads the extracted module map and writes one TSV per requested unit so the next
batch-decompile wave can be aimed at real algorithm code.
"""
import json
import pathlib

MODULES = pathlib.Path(r"D:\Rea\extracted\source-modules.json")
OUT_DIR = pathlib.Path(r"D:\Rea\extracted")

# Units worth decompiling, chosen because their names state their job.
TARGETS = {
    "Source\\Bc\\BcAlignLines.pas": "line alignment algorithm",
    "Source\\Bc\\BcAlign.pas": "alignment core",
    "Source\\Text\\TextMap.pas": "text diff map",
    "Source\\Text\\TextContent.pas": "text content model",
    "Source\\Ss\\SsLineParse.pas": "line lexer/parser",
    "Source\\Ss\\SsLineList.pas": "line list storage",
    "Source\\Text\\TextFormat.pas": "text format/grammar",
    "Source\\Text\\TextREParser.pas": "regex parser",
    "Source\\Text\\TextSession.pas": "text compare session",
    "Source\\Text\\TextFiltered.pas": "filtered text view",
    "Source\\Bc\\BcSyntaxElements.pas": "syntax elements",
    "Source\\Bc\\BcFileFormat.pas": "file format layer",
}

data = json.loads(MODULES.read_text(encoding="utf-8"))
path_to_functions = data["path_to_functions"]

prefix = "C:" + chr(92) + "BCBuild" + chr(92) + "BCompare" + chr(92)
by_unit: dict[str, list[str]] = {unit: [] for unit in TARGETS}
for path, functions in path_to_functions.items():
    relative = path[len(prefix):]
    if relative in by_unit:
        by_unit[relative].extend(functions)

print("functions asserting from algorithm units:")
total = 0
for unit, note in TARGETS.items():
    functions = sorted(set(by_unit[unit]))
    total += len(functions)
    print(f"  {len(functions):4d}  {unit:44s} ({note})")

lines = []
seen = set()
for unit, note in TARGETS.items():
    for function in sorted(set(by_unit[unit])):
        if function in seen:
            continue
        seen.add(function)
        lines.append(f"{function}\t{unit.split(chr(92))[-1]} - {note}")

target = OUT_DIR / "wave3-addresses.txt"
target.write_text("\n".join(lines), encoding="utf-8")
print(f"\ntotal distinct functions: {len(lines)}")
print(f"wrote {target}")

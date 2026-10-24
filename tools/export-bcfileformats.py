"""Export BCFILEFORMATS into a machine-readable grammar spec.

BCFILEFORMATS ships as a Delphi-flavoured XML document: element values that
reference a localized resource string carry an escaped marker such as
``&#2;CPP``, which is not a legal XML character reference. Replace those markers
with a readable prefix before parsing, then flatten each format's grammar.

The grammar nodes are ``TListTextGrammarItem`` blocks. Each block names its
element via ``ElementStr`` (Keyword, Identifier, Number, String, ...) and lists
its patterns or literal items under ``Items``. Everything else on a format
(``Mask``, ``TabSize``, ``CaseSensitive``, ``Dlm*``, ``StopText``) is captured
verbatim so the exported spec keeps the ordering BC itself uses.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

SOURCE = pathlib.Path(r"D:\Rea\extracted\rcdata\BCFILEFORMATS.bin")
OUT = pathlib.Path(r"D:\Rea\extracted\bcfileformats-spec.json")

MARKER = re.compile(r"&#(\d+);")


EMBEDDED_MARKER = re.compile(r"MARK\d+")

def strip_marker(value: str) -> str:
    # XML escapes the localization marker as &#2;, which becomes MARK2 after the
    # pre-parse substitution; expose the plain resource-text value instead.
    return EMBEDDED_MARKER.sub("", value or "")


def walk(node: ET.Element) -> dict:
    """Flatten one element, preserving the positional _N child ordering Delphi uses."""
    entry: dict = {}
    items = []
    for child in node:
        if child.tag == "Items":
            for item in child:
                items.append(strip_marker(item.get("Value", "")))
        elif len(child) == 0:
            entry[child.tag] = strip_marker(child.get("Value", ""))
        else:
            entry[child.tag] = walk(child)
    if items:
        entry["Items"] = items
    return entry


def walk_list(node: ET.Element) -> list:
    """Flatten a Delphi <>-style list element whose children are _0, _1, ... entries.

    Each entry is either an inline grammar item (``TListTextGrammarItem`` with an
    ``ElementStr`` plus ``Items``) or a nested list of the same shape, so the
    recursion keeps the tree rather than collapsing it to strings.
    """
    entries = []
    for child in node:
        if len(child) == 0:
            entries.append(strip_marker(child.get("Value", "")))
            continue
        record: dict = {}
        for field in child:
            if field.tag == "Items":
                record[field.tag] = walk_list(field)
            elif len(field) == 0:
                record[field.tag] = strip_marker(field.get("Value", ""))
            else:
                record[field.tag] = walk_list(field)
        entries.append(record)
    return entries


raw = SOURCE.read_text(encoding="utf-8")
root = ET.fromstring(MARKER.sub(lambda m: f"MARK{m.group(1)}", raw))

formats = []
for child in root:
    name = strip_marker(child.get("Value", ""))
    definition: dict = {}
    for field in child:
        if len(field) == 0:
            definition[field.tag] = strip_marker(field.get("Value", ""))
        elif field.tag in {"Grammar", "Description"}:
            definition[field.tag] = walk_list(field)
        else:
            definition[field.tag] = walk(field)
    formats.append({"kind": child.tag, "name": name, "definition": definition})

OUT.write_text(
    json.dumps({"format_count": len(formats), "formats": formats}, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(f"formats: {len(formats)}")
for fmt in formats:
    definition = fmt["definition"]
    grammar = definition.get("Grammar")
    element = None
    token_count = 0
    if isinstance(grammar, list) and grammar:
        first = grammar[0]
        if isinstance(first, dict):
            element = first.get("ElementStr")
            token_count = len(first.get("Items") or [])
    extra = [key for key in definition if key not in {"Description", "Grammar"}]
    print(f'{fmt["name"]:12s} {fmt["kind"]:14s} firstElement={element} patterns={token_count} extra={extra}')

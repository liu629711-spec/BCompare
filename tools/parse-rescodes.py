"""Parse the decompressed RES_CODES Delphi resource-string table.

Layout per record: <u32 resID> <u32 length> <length bytes of text>.
Delphi stores the text as the platform's string encoding; ASCII identifiers
dominate, so decode latin-1 and let non-ASCII bytes through unchanged.
"""
import json
import pathlib
import re
import struct

SRC = pathlib.Path(r"D:\Rea\extracted\rcdata\RES_CODES.out")
OUT = pathlib.Path(r"D:\Rea\extracted\rcdata\res-codes-parsed.json")

data = SRC.read_bytes()
off = 0
entries = []
while off + 8 <= len(data):
    resid = struct.unpack_from("<I", data, off)[0]
    length = struct.unpack_from("<I", data, off + 4)[0]
    if length == 0 or length > 4000:
        off += 1
        continue
    start = off + 8
    end = start + length
    if end > len(data):
        off += 1
        continue
    raw = data[start:end]
    text = raw.decode("latin-1")
    # A record is plausible when the payload has no control bytes other than tab/newline.
    if all(ch >= " " or ch in "\r\n\t" for ch in text):
        entries.append({"id": f"0x{resid:08x}", "text": text})
        off = end
    else:
        off += 1

identifiers = [e for e in entries if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", e["text"])]
OUT.write_text(
    json.dumps({"entries": entries, "identifier_count": len(identifiers)}, ensure_ascii=False, indent=1),
    encoding="utf-8",
)
print(f"parsed entries: {len(entries)}")
print(f"identifier-like: {len(identifiers)}")
for entry in identifiers[:15]:
    print(entry["id"], entry["text"])

"""Parse Beyond Compare TPF0 (binary DFM) streams.

Value tags follow Delphi Classes.TValueType. Object prefixes are
$F0 | TFilerFlags (ffInherited=1, ffChildPos=2, ffInline=4).
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

VA = {
    0: "vaNull",
    1: "vaList",
    2: "vaInt8",
    3: "vaInt16",
    4: "vaInt32",
    5: "vaExtended",
    6: "vaString",
    7: "vaIdent",
    8: "vaFalse",
    9: "vaTrue",
    10: "vaBinary",
    11: "vaSet",
    12: "vaLString",
    13: "vaNil",
    14: "vaCollection",
    15: "vaSingle",
    16: "vaCurrency",
    17: "vaDate",
    18: "vaWString",
    19: "vaInt64",
    20: "vaUTF8String",
    21: "vaUString",
    22: "vaQWord",
}


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.data)

    def peek(self) -> int:
        return -1 if self.eof() else self.data[self.pos]

    def take(self, n: int = 1) -> bytes:
        chunk = self.data[self.pos : self.pos + n]
        if len(chunk) < n:
            raise EOFError(f"need {n} bytes at {self.pos}")
        self.pos += n
        return chunk

    def u8(self) -> int:
        return self.take(1)[0]

    def short_str(self) -> str:
        n = self.u8()
        return self.take(n).decode("latin-1")

    def read_integer(self) -> int:
        """Delphi's TReader.ReadInteger: a signed SmallInt, with -1 as the escape
        that announces a full 4-byte LongInt follows. Reading 4 bytes
        unconditionally desynchronises the stream."""
        value = struct.unpack("<h", self.take(2))[0]
        if value == -1:
            return struct.unpack("<i", self.take(4))[0]
        return value


def read_value(r: Reader, tag: int):
    if tag == 0:
        return None
    if tag == 1:
        items = []
        while True:
            t = r.u8()
            if t == 0:
                break
            items.append(read_value(r, t))
        return items
    if tag == 2:
        return struct.unpack("b", r.take(1))[0]
    if tag == 3:
        # vaInt16 goes through TReader.ReadInteger: a SmallInt, with -1 escaping
        # to a full LongInt. Reading two bytes unconditionally desynchronises the
        # stream, because the writer does emit the escape form (e.g. TAG values).
        return r.read_integer()
    if tag == 4:
        # vaInt32 is a plain LongInt and never uses the SmallInt escape.
        return struct.unpack("<i", r.take(4))[0]
    if tag == 5:
        return {"extended": r.take(10).hex()}
    if tag == 6:
        return r.short_str()
    if tag == 7:
        return {"ident": r.short_str()}
    if tag == 8:
        return False
    if tag == 9:
        return True
    if tag == 10:
        n = struct.unpack("<i", r.take(4))[0]
        blob = r.take(n)
        return {"binary_len": n, "binary_sha": _sha(blob), "binary_ascii": _ascii_preview(blob)}
    if tag == 11:
        names = []
        while True:
            t = r.peek()
            if t == 0:
                r.u8()
                break
            names.append(r.short_str())
        return {"set": names}
    if tag == 12:
        n = struct.unpack("<i", r.take(4))[0]
        return r.take(n).decode("latin-1", "replace")
    if tag == 13:
        return None
    if tag == 14:
        # TReader.ReadCollection: every item is wrapped by ReadListBegin /
        # ReadListEnd (vaList ... vaNull), and the collection itself closes with
        # a final vaNull. Treating the whole block as one property list makes the
        # item markers look like property names.
        items = []
        while True:
            marker = r.peek()
            if marker == 0:
                r.u8()  # collection terminator
                break
            if marker == 1:
                r.u8()  # item list begin
            item: dict = {}
            children = []
            while True:
                nxt = r.peek()
                if nxt == 0:
                    r.u8()  # item list end
                    break
                if nxt >= 0xF0 or looks_like_class_name(r):
                    children.append(read_object(r))
                    continue
                name = r.short_str()
                vtag = r.u8()
                item[name] = read_value(r, vtag)
            if children:
                item["children"] = children
            items.append(item)
        return items
    if tag == 15:
        return struct.unpack("<f", r.take(4))[0]
    if tag == 16:
        return {"currency": r.take(8).hex()}
    if tag == 17:
        return {"date": struct.unpack("<d", r.take(8))[0]}
    if tag == 18:
        n = struct.unpack("<i", r.take(4))[0]
        return r.take(n * 2).decode("utf-16le", "replace")
    if tag == 19:
        return struct.unpack("<q", r.take(8))[0]
    if tag == 20:
        n = struct.unpack("<i", r.take(4))[0]
        return r.take(n).decode("utf-8", "replace")
    if tag == 21:
        n = struct.unpack("<i", r.take(4))[0]
        return r.take(n * 2).decode("utf-16le", "replace")
    if tag == 22:
        return struct.unpack("<Q", r.take(8))[0]
    raise ValueError(f"unknown value tag 0x{tag:02X} at {r.pos}")


def follows_shortstring_identifier(data: bytes, start: int) -> bool:
    """True when a valid shortstring identifier begins at `start`."""
    if start >= len(data):
        return False
    length = data[start]
    if length < 1 or length > 60:
        return False
    end = start + 1 + length
    if end > len(data):
        return False
    body = data[start + 1 : end]
    return all(48 <= b <= 57 or 65 <= b <= 90 or 97 <= b <= 122 or b == 95 for b in body)


def looks_like_component_record(r: Reader) -> bool:
    """True when the next bytes are a flag-less component record.

    In the children and root positions a record is either prefixed with $F0|flags
    or, when it carries no flags, begins directly with its class shortstring
    followed by its component-name shortstring. A property name never appears
    after a terminator, so in these positions the class/name pairing is enough —
    and it must be lenient, because BC also uses classes without the Delphi `T`
    prefix (the media forms use ``INVButton``).
    """
    data = r.data
    start = r.pos
    if start >= len(data):
        return False
    class_length = data[start]
    if class_length < 2 or class_length > 60:
        return False
    class_end = start + 1 + class_length
    if class_end > len(data):
        return False
    class_name = data[start + 1 : class_end]
    if not all(48 <= b <= 57 or 65 <= b <= 90 or 97 <= b <= 122 or b == 95 for b in class_name):
        return False
    return follows_shortstring_identifier(data, class_end)


def looks_like_class_name(r: Reader) -> bool:
    """True when the next bytes are a flag-less component record whose class
    carries the Delphi `T` prefix.

    This stricter form is used inside a property list, where a property name such
    as ``Top`` or ``OnClick`` could otherwise be mistaken for the start of a
    child record. Requiring the class to begin with `T`, to contain a lowercase
    letter, and to be followed by a component name keeps real property names out.
    """
    data = r.data
    start = r.pos
    if start >= len(data):
        return False
    class_length = data[start]
    if class_length < 4 or class_length > 60:
        return False
    class_end = start + 1 + class_length
    if class_end >= len(data):
        return False
    class_name = data[start + 1 : class_end]
    if class_name[:1] != b"T":
        return False
    if not all(48 <= b <= 57 or 65 <= b <= 90 or 97 <= b <= 122 or b == 95 for b in class_name):
        return False
    # Real BC classes are CamelCase; "Top"/"TabOrder"/"Timer" are single words.
    if not any(97 <= b <= 122 for b in class_name[1:]):
        return False
    return follows_shortstring_identifier(data, class_end)


def read_object(r: Reader, allow_prefixless: bool = True) -> dict:
    prefix = r.u8()
    if prefix >= 0xF0:
        flags_byte = prefix & 0x0F
    else:
        if not allow_prefixless:
            raise ValueError(f"expected object prefix at {r.pos-1}, got 0x{prefix:02X}")
        # No prefix byte: this record carries no flags (see looks_like_class_name).
        r.pos -= 1
        flags_byte = 0
    flags = []
    if flags_byte & 1:
        flags.append("inherited")
    if flags_byte & 2:
        flags.append("childPos")
        # TReader.ReadComponent reads the position through ReadInteger as well.
        child_pos = r.read_integer()
    else:
        child_pos = None
    if flags_byte & 4:
        flags.append("inline")
    cls = r.short_str()
    name = r.short_str()
    props = {}
    while True:
        b = r.peek()
        if b == 0:
            r.u8()
            break
        # A child record can begin directly in the property section: either with
        # an explicit $F0|flags prefix, or (flag-less) with its class shortstring.
        if b >= 0xF0 or looks_like_class_name(r):
            break
        pname = r.short_str()
        vtag = r.u8()
        props[pname] = read_value(r, vtag)
    children = []
    while not r.eof():
        b = r.peek()
        if b == 0:
            r.u8()
            break
        if b >= 0xF0 or looks_like_component_record(r):
            children.append(read_object(r))
            continue
        break
    obj = {"class": cls, "name": name, "flags": flags, "props": props, "children": children}
    if child_pos is not None:
        obj["childPos"] = child_pos
    return obj


def parse_stream(data: bytes) -> dict:
    if data[:4] != b"TPF0":
        raise ValueError("not TPF0")
    r = Reader(data)
    r.pos = 4
    roots = []
    while not r.eof():
        if r.peek() == 0:
            r.u8()
            continue
        if r.peek() >= 0xF0 or looks_like_component_record(r):
            roots.append(read_object(r))
            continue
        break
    return {"roots": roots, "consumed": r.pos, "size": len(data)}


def _sha(blob: bytes) -> str:
    import hashlib

    return hashlib.sha256(blob).hexdigest()


def _ascii_preview(blob: bytes, n: int = 160) -> str:
    return "".join(chr(b) if 32 <= b < 127 else "." for b in blob[:n])


def flatten(obj: dict, acc: list | None = None) -> list:
    acc = acc if acc is not None else []
    acc.append({"class": obj["class"], "name": obj["name"], "flags": obj["flags"], "props": obj["props"]})
    for ch in obj["children"]:
        flatten(ch, acc)
    return acc


def main() -> None:
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    data = src.read_bytes()
    parsed = parse_stream(data)
    parsed["flat"] = [item for root in parsed["roots"] for item in flatten(root)]
    text = json.dumps(parsed, ensure_ascii=False, indent=2)
    if out:
        out.write_text(text, encoding="utf-8")
        print(f"{src.name}: objects={len(parsed['flat'])} consumed={parsed['consumed']}/{parsed['size']} -> {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

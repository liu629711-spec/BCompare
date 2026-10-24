#!/usr/bin/env python3
"""Decode Delphi binary DFM (TPF0) resources out of a PE into text .dfm files.

The DFM stream is Delphi's serialized form definition, compiled into the EXE as an
RCDATA resource. Decoding it recovers the complete UI structure of every form,
frame and dialog: the full control tree with geometry, captions, and the names of
every event handler method referenced by a control.

Format notes (validated against BCompare.exe):
  - signature 'TPF0' then root object record.
  - Strings are Delphi ShortStrings with TReader.ReadStr length escaping:
      byte L != 0; if (L & 0xF0) == 0xF0, the low nibble is the count of following
      little-endian bytes giving the real length; else L is the length.
  - Object record = ClassName:ShortStr InstanceName:ShortStr
      (Name:ShortStr Value)* until empty name
      (ChildObject)* until a 0x00 byte.
  - vaBinary (0x0A) = int32 length + raw bytes; for TPicture.Data the blob starts
    with a ShortString naming the image class (e.g. 'TPngImage').

Usage:
  python tools/dfm-extract.py [exe] [outdir] [--filter SUBSTR]
"""
import struct, sys, os, json, collections

vaNull, vaList, vaInt8, vaInt16, vaInt32, vaExtended = 0, 1, 2, 3, 4, 5
vaString, vaIdent, vaFalse, vaTrue, vaBinary, vaSet = 6, 7, 8, 9, 10, 11
vaLString, vaNil, vaCollection, vaSingle, vaCurrency, vaDate = 12, 13, 14, 15, 16, 17
vaWString, vaInt64, vaUTF8String, vaDouble = 18, 19, 20, 21


class Reader:
    def __init__(self, buf, p=0):
        self.b = buf
        self.p = p

    def eof(self):
        return self.p >= len(self.b)

    def u8(self):
        if self.p >= len(self.b):
            raise EOFError(f'u8 at eof ({self.p})')
        v = self.b[self.p]; self.p += 1; return v

    def peek(self):
        return self.b[self.p] if self.p < len(self.b) else None

    def take(self, n):
        if self.p + n > len(self.b):
            raise EOFError(f'need {n} bytes at {self.p}, have {len(self.b) - self.p}')
        v = self.b[self.p:self.p + n]; self.p += n; return v

    def i16(self):
        return struct.unpack_from('<h', self.take(2))[0]

    def i32(self):
        return struct.unpack_from('<i', self.take(4))[0]

    def short(self):
        """Delphi ShortString with binary-DFM length escaping (TReader.ReadStr)."""
        L = self.u8()
        if L == 0:
            return ''
        if (L & 0xF0) == 0xF0:
            n = L & 0x0F
            length = int.from_bytes(self.take(n), 'little') if n else 0
        else:
            length = L
        return self.take(length).decode('latin-1')


def esc(s):
    out = []
    for ch in s:
        o = ord(ch)
        if ch == "'":
            out.append("''")
        elif o < 32 or o == 0x7f or o > 126:
            out.append('#' + str(o))
        else:
            out.append(ch)
    return "'" + ''.join(out) + "'"


def num(x):
    if isinstance(x, int):
        return str(x)
    if x == int(x):
        return str(int(x))
    return repr(x)


class Dfm:
    def __init__(self, buf):
        self.r = Reader(buf, 4)

    def value(self):
        """Return (text, kind); kind 'null' marks a list terminator."""
        r = self.r
        t = r.u8()
        if t == vaNull:
            return '', 'null'
        if t == vaList:
            items = []
            while True:
                sub, k = self.value()
                if k == 'null':
                    break
                items.append(sub)
            return '(' + ', '.join(items) + ')', 'list'
        if t == vaInt8:
            return str(struct.unpack('<b', r.take(1))[0]), 'int'
        if t == vaInt16:
            return str(r.i16()), 'int'
        if t == vaInt32:
            return str(r.i32()), 'int'
        if t == vaInt64:
            return str(struct.unpack_from('<q', r.take(8))[0]), 'int'
        if t == vaExtended:
            return num(struct.unpack_from('<e', r.take(10))[0]), 'float'
        if t == vaSingle:
            return num(struct.unpack_from('<f', r.take(4))[0]), 'float'
        if t == vaDouble:
            return num(struct.unpack_from('<d', r.take(8))[0]), 'float'
        if t == vaCurrency:
            return num(struct.unpack_from('<q', r.take(8))[0] / 10000.0), 'float'
        if t == vaDate:
            return num(struct.unpack_from('<d', r.take(8))[0]), 'float'
        if t == vaString:            # 0x06: ShortString (byte length, TReader.ReadStr escaping)
            return esc(r.short()), 'str'
        if t == vaLString:           # 0x0c: int32 byte length + ANSI bytes
            n = r.i32()
            return esc(r.take(n).decode('latin-1')), 'str'
        if t == vaWString:
            n = r.i32()
            raw = r.take(n * 2)
            return esc(raw.decode('utf-16le', 'replace')), 'str'
        if t == vaUTF8String:
            n = r.i32()
            return esc(r.take(n).decode('utf-8', 'replace')), 'str'
        if t == vaIdent:
            return r.short(), 'ident'
        if t == vaFalse:
            return 'False', 'bool'
        if t == vaTrue:
            return 'True', 'bool'
        if t == vaNil:
            return 'nil', 'nil'
        if t == vaBinary:
            n = r.i32()
            raw = r.take(n)
            # Picture data blobs begin with the image class ShortString
            head = ''
            if len(raw) > 1:
                ln = raw[0]
                if 0 < ln < len(raw) and all(32 <= b < 127 for b in raw[1:1 + ln]):
                    head = raw[1:1 + ln].decode('latin-1') + ' '
            return '{' + head + str(n) + ' bytes}', 'binary'
        if t == vaSet:
            items = []
            while True:
                s = r.short()
                if s == '':
                    break
                items.append(s)
            return '[' + ', '.join(items) + ']', 'set'
        if t == vaCollection:
            # vaCollection: repeated vaList-led property groups; each group's
            # property terminator (00) doubles as the item terminator, and the
            # collection itself ends with one more 00. No count prefix.
            items = []
            while True:
                b = r.u8()
                if b == vaNull:
                    break
                if b != vaList:
                    raise ValueError(f'collection item must be vaList, got 0x{b:02x} at {r.p - 1}')
                props = []
                while True:
                    pn = r.short()
                    if pn == '':
                        break
                    v, k = self.value()
                    props.append((pn, v, k))
                items.append(props)
            return (items, 'COLLECTION')
        raise ValueError(f'unknown value type 0x{t:02x} at {r.p - 1}')

    def read_object(self, out, indent):
        r = self.r
        # Object marker. Delphi writes a prefix byte here when the component
        # carries flags: (b & 0xF0) == 0xF0 -> flags in the low nibble, and
        # flag 2 (ffChildPos) is followed by a typed integer position.
        # Otherwise this byte is already the class-name length.
        b = r.u8()
        if b == 0:
            raise ValueError(f'unexpected list terminator where object expected at {r.p - 1}')
        child_pos = None
        if (b & 0xF0) == 0xF0:
            flags = b & 0x0F
            if flags & 0x02:
                v, _ = self.value()
                child_pos = v
        else:
            r.p -= 1
        cls = r.short()
        name = r.short()
        out.append(f'{indent}object {name}: {cls}')
        here = indent + '  '
        while True:
            pn = r.short()
            if pn == '':
                break
            v, k = self.value()
            if k == 'COLLECTION':
                out.append(f'{here}{pn} = <')
                for props in v:
                    out.append(f'{here}  item')
                    for (pn2, v2, k2) in props:
                        if k2 == 'COLLECTION':
                            out.append(f'{here}    {pn2} = <')
                            for p2 in v2:
                                for (pn3, v3, _k3) in p2:
                                    out.append(f'{here}      {pn3} = {v3}')
                            out.append(f'{here}    >')
                        else:
                            out.append(f'{here}    {pn2} = {v2}')
                    out.append(f'{here}  end')
                out.append(f'{here}>')
            else:
                out.append(f'{here}{pn} = {v}')
        while True:
            b = r.u8()
            if b == 0:
                break
            r.p -= 1
            self.read_object(out, here)
        out.append(f'{indent}end')


def parse_stream(buf):
    if buf[:4] != b'TPF0':
        raise ValueError(f'bad DFM signature {buf[:4]!r}')
    d = Dfm(buf)
    out = []
    d.read_object(out, '')
    return '\n'.join(out) + '\n', d.r.p


# ---- PE resource walk ---------------------------------------------------
def pe_resource_leaves(data):
    e = struct.unpack_from('<I', data, 0x3c)[0]
    coff = e + 4
    num_sec, = struct.unpack_from('<H', data, coff + 2)
    opt_sz, = struct.unpack_from('<H', data, coff + 16)
    opt = coff + 20
    magic, = struct.unpack_from('<H', data, opt)
    dd_off = opt + (0x70 if magic == 0x20b else 0x60)
    res_rva, _res_sz = struct.unpack_from('<II', data, dd_off + 2 * 8)
    secs = []
    so = opt + opt_sz
    for _ in range(num_sec):
        vsz, va, rsz, ro = struct.unpack_from('<IIII', data, so + 8)
        secs.append((va, vsz, ro, rsz))
        so += 40

    def rva2off(rva):
        for va, vsz, ro, rsz in secs:
            if va <= rva < va + max(vsz, rsz):
                off = ro + (rva - va)
                if 0 <= off < len(data):
                    return off
        return None

    base = rva2off(res_rva)
    leaves = []

    def walk(off, path, depth):
        if depth > 4 or off is None:
            return
        n_named, n_id = struct.unpack_from('<HH', data, off + 12)
        for i in range(n_named + n_id):
            ent = off + 16 + i * 8
            name_raw, off2 = struct.unpack_from('<II', data, ent)
            if name_raw & 0x80000000:
                noff = base + (name_raw & 0x7fffffff)
                ln, = struct.unpack_from('<H', data, noff)
                nm = data[noff + 2:noff + 2 + ln * 2].decode('utf-16le', 'replace')
            else:
                nm = name_raw
            if off2 & 0x80000000:
                walk(base + (off2 & 0x7fffffff), path + [nm], depth + 1)
            else:
                drva, dsz = struct.unpack_from('<II', data, base + off2)
                leaves.append((tuple(path), nm, drva, dsz))

    walk(base, [], 0)
    return leaves, rva2off


def main():
    argv = sys.argv[1:]
    filt = None
    if '--filter' in argv:
        i = argv.index('--filter')
        filt = argv[i + 1]
        del argv[i:i + 2]
    exe = argv[0] if argv else r'D:\bc-official\app\BCompare.exe'
    outdir = argv[1] if len(argv) > 1 else r'D:\Rea\extracted\forms'
    os.makedirs(outdir, exist_ok=True)
    data = open(exe, 'rb').read()
    leaves, rva2off = pe_resource_leaves(data)

    results = []
    for path, leaf, drva, dsz in leaves:
        if not path or path[0] != 10:
            continue
        off = rva2off(drva)
        if off is None:
            continue
        body = data[off:off + dsz]
        if body[:4] != b'TPF0':
            continue
        name = str(path[1]) if len(path) > 1 else str(leaf)
        if filt and filt.lower() not in name.lower():
            continue
        rec = {'name': name, 'size': dsz}
        try:
            text, used = parse_stream(body)
            rec['status'] = 'ok' if used == dsz else f'partial {used}/{dsz}'
        except Exception as ex:
            results.append({**rec, 'status': f'ERROR {ex}'})
            continue
        with open(os.path.join(outdir, f'{name}.dfm'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        objs = events = 0
        classes = collections.Counter()
        for ln in text.splitlines():
            s = ln.strip()
            if s.startswith('object ') and ':' in s:
                cls = s.split(': ', 1)[1]
                classes[cls] += 1
                objs += 1
            elif s.startswith('On') and ' = ' in s:
                events += 1
        results.append({**rec, 'status': rec['status'], 'objects': objs,
                        'events': events, 'classes': classes.most_common(6)})

    ok = [r for r in results if r['status'].startswith(('ok', 'partial'))]
    bad = [r for r in results if r not in ok]
    print(f'exe            : {exe}')
    print(f'outdir         : {outdir}')
    print(f'forms decoded  : {len(ok)}/{len(results)}')
    print(f'control objects: {sum(r.get("objects", 0) for r in ok):,}')
    print(f'event bindings : {sum(r.get("events", 0) for r in ok):,}')
    parts = [r for r in ok if r['status'].startswith('partial')]
    if parts:
        print(f'partial parses : {len(parts)} (first few: '
              + ', '.join(f"{r['name']}({r['status'].split()[1]})" for r in parts[:5]) + ')')
    if bad:
        print(f'FAILURES       : {len(bad)}')
        for r in bad[:10]:
            print(f'   {r["name"]}: {r["status"]}')
    with open(os.path.join(outdir, 'forms-index.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(results, key=lambda x: x['name']), f, indent=1)
    print(f'index          : {os.path.join(outdir, "forms-index.json")}')


if __name__ == '__main__':
    main()

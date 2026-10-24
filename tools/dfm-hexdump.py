#!/usr/bin/env python3
"""Hexdump + step-decode a DFM resource at a byte offset to diagnose parse desync."""
import sys, struct, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dfmx', os.path.join(HERE, 'dfm-extract.py'))
dfmx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfmx)

VT = {0: 'vaNull', 1: 'vaList', 2: 'vaInt8', 3: 'vaInt16', 4: 'vaInt32',
      5: 'vaExtended', 6: 'vaString', 7: 'vaIdent', 8: 'vaFalse', 9: 'vaTrue',
      10: 'vaBinary', 11: 'vaSet', 12: 'vaLString', 13: 'vaNil',
      14: 'vaCollection', 15: 'vaSingle', 16: 'vaCurrency', 17: 'vaDate',
      18: 'vaWString', 19: 'vaInt64', 20: 'vaUTF8String', 21: 'vaDouble'}


def get_res(exe, want):
    data = open(exe, 'rb').read()
    leaves, rva2off = dfmx.pe_resource_leaves(data)
    for path, leaf, drva, dsz in leaves:
        if not path or path[0] != 10:
            continue
        name = str(path[1]) if len(path) > 1 else str(leaf)
        if name == want:
            off = rva2off(drva)
            return data[off:off + dsz]
    return None


def dump(buf, lo, hi, mark):
    lo = max(0, lo)
    hi = min(len(buf), hi)
    for off in range(lo - lo % 16, hi, 16):
        chunk = buf[off:off + 16]
        hexs = ' '.join(f'{b:02x}' for b in chunk)
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        m = '  <<<' if off <= mark < off + 16 else ''
        print(f'{off:7d}  {hexs:<47s} |{txt}|{m}')


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else 'TFILEVIEW'
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 else start + 200
    buf = get_res(r'D:\bc-official\app\BCompare.exe', want)
    print(f'=== {want}: {len(buf)} bytes ===')
    dump(buf, start, end, (start + end) // 2)
    print('\n--- context as latin-1 ---')
    print(repr(buf[max(0, start - 32):min(len(buf), end + 32)].decode('latin-1')))


if __name__ == '__main__':
    main()

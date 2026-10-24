#!/usr/bin/env python3
"""Trace the binary DFM parser to find the exact byte where it desyncs."""
import sys, struct, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dfmx', os.path.join(HERE, 'dfm-extract.py'))
dfmx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfmx)


def get_res(exe, want):
    data = open(exe, 'rb').read()
    leaves, secs = dfmx.walk_resources(data)
    for path, leaf, drva, dsz in leaves:
        if not path or path[0] != 10:
            continue
        name = str(path[1]) if len(path) > 1 else str(leaf)
        if name == want:
            off = dfmx.rva2off(secs, data, drva)
            return data[off:off + dsz]
    return None


def main():
    exe = r'D:\bc-official\app\BCompare.exe'
    want = sys.argv[1] if len(sys.argv) > 1 else 'TABOUTDIALOG'
    buf = get_res(exe, want)
    if buf is None:
        print('resource not found'); return
    print(f'{want}: {len(buf)} bytes, sig={buf[:4]!r}')

    log = []

    class TraceReader(dfmx.Reader):
        def u8(self):
            p = self.p
            v = dfmx.Reader.u8(self)
            log.append(('u8', p, v))
            return v

        def short(self):
            p = self.p
            v = dfmx.Reader.short(self)
            log.append(('short', p, v))
            return v

        def i32(self):
            p = self.p
            v = dfmx.Reader.i32(self)
            log.append(('i32', p, v))
            return v

        def take(self, n):
            p = self.p
            v = dfmx.Reader.take(self, n)
            log.append(('take', p, n))
            return v

    p = dfmx.DfmParser(buf)
    p.r = TraceReader(buf)
    p.r.p = 4
    out = []
    try:
        p.read_object(out, '', '')
        print("parse OK")
    except Exception as ex:
        print(f"FAILED: {ex}")
        print(f"parser position: {p.r.p}")
    print("\n--- last 60 trace entries (kind, byte-offset, value) ---")
    for kind, pos, val in log[-60:]:
        s = repr(val) if not isinstance(val, int) else f'{val} (0x{val:02x})'
        print(f'  {pos:6d}  {kind:6s} {s}')

    lo = max(0, p.r.p - 64)
    hi = min(len(buf), p.r.p + 48)
    print(f"\n--- hexdump {lo}..{hi} (error at {p.r.p}) ---")
    for off in range(lo, hi, 16):
        chunk = buf[off:off + 16]
        hexs = ' '.join(f'{b:02x}' for b in chunk)
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        mark = '  <<<' if off <= p.r.p < off + 16 else ''
        print(f'  {off:6d}  {hexs:<47s} {txt}{mark}')
    print(f"\n--- bytes are ASCII? ---")
    print('  ', ''.join(chr(b) if 32 <= b < 127 else '·' for b in buf[lo:hi]))


if __name__ == '__main__':
    main()

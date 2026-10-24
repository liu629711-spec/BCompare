#!/usr/bin/env python3
"""Diagnose DFM parse desync: trace every read, then on failure dump the last
successful reads plus raw hex context around the failure point.

This is the tool that isolates the anomalous prefix bytes (e.g. f2 02 00) that
appear between an object's property terminator and its first child.
"""
import sys, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dfmx', os.path.join(HERE, 'dfm-extract.py'))
dfmx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfmx)


def get_res(want):
    data = open(r'D:\bc-official\app\BCompare.exe', 'rb').read()
    leaves, rva2off = dfmx.pe_resource_leaves(data)
    for path, leaf, drva, dsz in leaves:
        if not path or path[0] != 10:
            continue
        name = str(path[1]) if len(path) > 1 else str(leaf)
        if name == want:
            off = rva2off(drva)
            return data[off:off + dsz]
    return None


class TraceReader(dfmx.Reader):
    def __init__(self, buf, p=0):
        super().__init__(buf, p)
        self.log = []

    def short(self):
        p = self.p
        try:
            v = dfmx.Reader.short(self)
        except Exception:
            self.log.append(('SHORT-FAIL', p, ''))
            raise
        self.log.append(('short', p, v))
        return v

    def u8(self):
        p = self.p
        v = dfmx.Reader.u8(self)
        self.log.append(('u8', p, v))
        return v

    def i32(self):
        p = self.p
        v = dfmx.Reader.i32(self)
        self.log.append(('i32', p, v))
        return v

    def take(self, n):
        p = self.p
        v = dfmx.Reader.take(self, n)
        self.log.append(('take', p, n))
        return v


def main():
    names = sys.argv[1:] or ['TFILEVIEW', 'TDIRBASEVIEW', 'TCHECKFORUPDATESDIALOG']
    for want in names:
        buf = get_res(want)
        if buf is None:
            print(f'{want}: NOT FOUND'); continue
        print(f'\n{"=" * 72}\n{want}: {len(buf)} bytes')
        d = dfmx.Dfm(buf)
        d.r = TraceReader(buf)
        d.r.p = 4
        out = []
        err = None
        try:
            d.read_object(out, '')
        except Exception as ex:
            err = ex
        pos = d.r.p
        print(f'status: {"OK" if not err else f"FAIL@ {pos}: {err}"}   '
              f'consumed {pos}/{len(buf)}   objects so far={sum(1 for l in out if l.strip().startswith("object"))}')
        print('\n-- last 14 trace entries --')
        for kind, p, v in d.r.log[-14:]:
            s = f'{v} (0x{v:02x})' if isinstance(v, int) else repr(v)[:90]
            print(f'  {p:6d}  {kind:9s} {s}')
        print('\n-- raw context around failure --')
        lo = max(0, pos - 40); hi = min(len(buf), pos + 24)
        for off in range(lo - lo % 16, hi, 16):
            chunk = buf[off:off + 16]
            mark = '  <<<' if off <= pos < off + 16 else ''
            print(f'  {off:6d}  {" ".join(f"{b:02x}" for b in chunk):<47s} |'
                  + ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk) + f'|{mark}')
        # look for the f? escape bytes nearby
        print('\n-- 0xF?-escapes in window --')
        for i in range(lo, hi):
            if 0xf0 <= buf[i] <= 0xff:
                ctx = buf[max(0, i - 4):i + 10]
                print(f'  {i:6d}: 0x{buf[i]:02x}  ctx=' + ' '.join(f'{x:02x}' for x in ctx))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""M111 box-prefix simulator: replays every archived m101 sbs fixture pair
and compares the rendered prefix pattern against the archived table body.

Box model hypotheses (to falsify):
 - items sorted linguistically (CompareStringW NORM_IGNORECASE + ASCII digit
   runs numeric, same as the dir crate); keys+values interleaved per level.
 - orphan/continuation markers '+','|','\' derived from a pending-stack.
"""
from __future__ import annotations
import json, glob, pathlib, ctypes, ctypes.wintypes, re

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")

# ---- collation via kernel32 CompareStringW (mirrors collation.rs) -------
k32 = ctypes.windll.kernel32
k32.CompareStringW.restype = ctypes.wintypes.INT
LOCALE_USER_DEFAULT = 0x0400
NORM_IGNORECASE = 1

def cs_cmp(a: str, b: str) -> int:
    r = k32.CompareStringW(LOCALE_USER_DEFAULT | NORM_IGNORECASE, 0, a, len(a), b, len(b))
    return r - 2  # Less=1 Greater=2 Equal=3

def split_digit(s: str):
    m = re.match(r"^\d+", s)
    if not m: return None, s
    return m.group(), s[m.end():]

def key_order(a: str, b: str) -> int:
    # digit-run aware, then linguistic
    da, ra = split_digit(a); db, rb = split_digit(b)
    if da is not None and db is not None:
        ia, ib = int(da), int(db)
        if ia != ib: return -1 if ia < ib else 1
        if ra and rb:
            return key_order(ra, rb)
        if ra != rb: return -1 if ra else 1
        return 0
    return cs_cmp(a, b)

# ---- .reg parse (mirrors reacmp-reg, no join; error stops) --------------
class Val:
    def __init__(self, kind, code, disp, width, bytes_=None):
        self.kind, self.code, self.disp, self.width = kind, code, disp, width
        self.bytes = bytes_
    @property
    def type_name(self):
        return {"sz": "REG_SZ", "dword": "REG_DWORD", "bin": "REG_BINARY",
                "typed": {0:"REG_NONE",1:"REG_SZ",2:"REG_EXPAND_SZ",3:"REG_BINARY",
                          7:"REG_MULTI_SZ"}.get(self.code, f"0x{self.code:02X}")}[self.kind]

def parse_hexdata(payload):
    toks = [t for t in payload.split(",") if t.strip()]
    try:
        return [int(t, 16) for t in toks]
    except ValueError:
        return None

def parse_reg_text(text):
    # decode not needed: callers decode
    lines = text.replace("\r\n", "\n").replace("\r", "\x00").split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip(): i += 1
    if i >= len(lines) or lines[i].strip() not in (
            "Windows Registry Editor Version 5.00", "REGEDIT4"):
        return dict(error="unsupported", roots=[], valued=[], all_keys=[])
    i += 1
    roots = {}
    cur = None
    valued = []
    all_keys = []
    error = None
    for lnum in range(i+1, len(lines)+1):
        ln = lines[lnum-1]
        s = ln.strip()
        if not s: continue
        if s.startswith("["):
            if not s.endswith("]"):
                error = (lnum, len(ln)+1); break
            body = s[1:-1]
            if body.startswith("-"): continue
            segs = body.split("\\")
            if len(segs) < 2 or any(not x for x in segs):
                error = (lnum, first_ns(ln)); break
            key = "\\".join(segs)
            if key not in [k.lower() for k in all_keys]:
                all_keys.append(key)
            cur = segs
            node = roots
            for seg in segs[1:]:
                node = node.setdefault("__c_"+fold(seg), {})
                # store name too
            node.setdefault("__name", segs[-1])
        elif s.startswith('"') or s.startswith("@"):
            m = re.match(r'^"((?:[^"\]|\.)*)"\s*=(.*)$', s)
            if not m:
                if s.startswith("@"):
                    mm = re.match(r'^@\s*=(.*)$', s)
                    if mm: name, payload = "@", mm.group(1).strip()
                    else: error = (lnum, len(ln)+1); break
                else:
                    error = (lnum, len(ln)+1); break
            else:
                name, payload = m.group(1).replace('\\"','"'), m.group(2).strip()
            # find node path
            node = roots
            for seg in (cur[1:] if cur else []):
                node = node["__c_"+fold(seg)]
            vals = node.setdefault("__v", {})
            if payload == "-": continue
            v = parse_payload(payload, lnum, len(ln))
            if v is None:
                error = (lnum, len(ln)+1); break
            foldname = fold(name)
            if foldname not in vals:
                vals[foldname] = (name, v)
                pv = "\\".join(cur)
                if pv not in valued: valued.append(pv)
        else:
            error = (lnum, first_ns(ln)); break
    return dict(error=error, roots=roots, valued=valued, all_keys=all_keys)

def fold(x): return x.upper()

def first_ns(ln):
    return len(ln) - len(ln.lstrip()) + 1

def parse_payload(p, lnum, rawlen):
    if p.startswith('"'):
        m = re.match(r'^"((?:[^"\]|\.)*)"$', p)
        if not m: return None
        s = m.group(1).replace('\\"','"').replace('\\','\')
        return Val("sz", None, s, max(2, len(s)))
    m = re.match(r'^dword:([0-9a-fA-F]+)$', p)
    if m:
        v = int(m.group(1), 16)
        disp = f"0x{v:08X} ({v})"
        return Val("dword", None, disp, max(2, len(disp)))
    m = re.match(r'^hex\(([0-9a-fA-F]+)\):(.*)$', p)
    if m:
        code = int(m.group(1), 16)
        bs = parse_hexdata(m.group(2))
        if bs is None: return None
        return Val("typed", code, bytes_disp(code, bs), data_width(code, bs), bs)
    m = re.match(r'^hex:(.*)$', p)
    if m:
        bs = parse_hexdata(m.group(1))
        if bs is None: return None
        return Val("bin", None, bytes_disp(3, bs), data_width(3, bs), bs)
    return None

PLACEHOLDER = "(零长度二进制值)"
def bytes_disp(code, bs):
    if not bs: return PLACEHOLDER
    if code in (1, 2):
        u = to_utf16(bs); return u.split("\x00")[0] if u else PLACEHOLDER
    if code == 7:
        return join_utf16_all(bs) + "\x00"
    return " ".join(f"{b:02X}" for b in bs)

def data_width(code, bs):
    if not bs: return max(2, len(PLACEHOLDER))
    if code in (0, 3) or code is None or code >= 0x100:  # binary-ish incl unknown? see S1 0x11
        return 3 * len(bs)
    d = bytes_disp(code, bs)
    return max(2, len(d))

def to_utf16(bs):
    try:
        return bs.decode("utf-16-le")
    except Exception:
        return None

def join_utf16_all(bs):
    s = to_utf16(bs) or ""
    return "".join(s.split("\x00"))

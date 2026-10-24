#!/usr/bin/env python3
"""Offline simulator for the BC table channel (M6.2 design loop).

Model (docs/13 §4 + batch-5/6 runs/m62-delimiter / m62-autodetect):
  * *.csv -> delimiter FIXED comma (D2/D3/D4/D11/D12: tab/;/| stay inside
    cells).  Other extensions auto-detect (candidates {, ; | space \\t},
    comma first) -- out of M6.2 product scope until batch-7 settles priority.
  * row = parsed CSV record (quotes; embedded newlines stay ONE row, T21).
  * alignment = content LCS over whole files; inside a replaced gap the rows
    zip positionally to `<>`, leftovers become orphans (P1/P2/P12).
  * cell equality = decode + trim per cell; interior whitespace matters
    (P3/P4); blank rows participate (F4).
  * side-by-side: column COUNT n = max column count over BOTH sides (T18,
    W7/m62b: each side renders the missing trailing columns as EMPTY cells at
    width 1); column WIDTHS are per-side, from that side's rows only (plus
    header letter, min 1) -- no cross-side forcing (measured m62b W1/W2:
    left 'wwww,1' vs right 'q,3','r,4' -> rw stays [1,1]).  Cells joined by
    ' '; numeric cells rjust, text ljust; the line end is rstripped once
    (empty last cells appear as padding only when something follows them:
    F1 `a   c`, T18 left `a 1  `, F4 row `   `).  Marker fields: ' =  '
    (' = ' all-same), ' <> ', ' +- ', ' -+ '.  An orphan's blank side is
    render_cells over ITS OWN widths with gi=None: full padded blank fields
    (F3 `    -+`, m62b W1 `       -+` from lw [4,1]); left orphans rstrip
    after the marker.  Header: letters padded exactly like cells joined by
    ' '; LEFT block kept UN-rstripped (its trailing column padding is part
    of the left field), blank field (same widths as the ' =  ' / ' = '
    marker: 4 resp. 3), right block, then rstrip the line end (measured
    T15/T17/F2 gaps 7/8/6 = lw-padding + marker).  Top + trailing rule at
    the widest line.
  * interleaved: SHARED column widths per column (max of both sides);
    number fields left=lw_ = digits of the last LEFT number, right=rw_ =
    digits of the last RIGHT number, rjust; layout 'L R cells' with cells
    joined like sbs but ALL cells ljust (numbers left-aligned too --
    measured T19 'q  1', T21 'z 3   4', m62b W1/W3).  '=' rows show BOTH
    numbers; a '<>' pair is one block with two lines: left line shows only
    the left number, right line only the right number; '+-'/'-+' show their
    side's number.  Every group (or pair) ends with a rule line; a rule also
    precedes the first block; rule width = widest line (header counts).
    Trailing rule present.
  * row parsing note (m62b W4, OUT of M6.2 scope -- split_records frozen):
    BCompare counts a TRAILING empty line ('\n\n' at EOF) as one more empty
    row (line-count semantics); split_records follows RFC-4180 and drops it.
    No archived 56-case exercises this.
  * summary: same / difference / left-orphan / right-orphan counts, zeros
    omitted, that order.  en: "N same row(s)", "N important difference
    row(s)", "N important left orphan row(s)", "N important right orphan
    row(s)".  zh: N 个相同排 / N 个重要差异排 / N 个重要的左边独有排 /
    N 个重要右边独有排 (的 asymmetry observed; repack quirk).
  * report frame (en): "Table Compare", "Produced: <stamp>", "",
    ["Mode:  All" for sbs/interleaved], "Left file: <L>", "Right file: <R>"
    (five-space gap, same HEADER_GAP as text), then the body.  CRLF, no BOM.

Replay: replay_table.py compares against archived Oracle bodies.
"""
from __future__ import annotations
import difflib, re

NUM_RE = re.compile(r"-?\d+(\.\d+)?")

# ---------------------------------------------------------------- parsing

def split_records(text: str) -> list[list[str]]:
    """RFC-4180 rows over comma; quoted cells may contain newlines."""
    rows: list[list[str]] = []
    field, row, i, inq = [], [], 0, False
    if text.endswith("\n"):
        text = text[:-1]
    if text.endswith("\r"):
        text = text[:-1]
    def end_field():
        row.append("".join(field)); field.clear()
    def end_row():
        end_field(); rows.append(list(row)); row.clear()
    while i < len(text):
        c = text[i]
        if inq:
            if c == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    field.append('"'); i += 2; continue
                inq = False; i += 1; continue
            field.append(c); i += 1; continue
        if c == '"' and not "".join(field).strip():
            inq = True; i += 1; continue
        if c == ",":
            end_field(); i += 1; continue
        if c in "\r\n":
            i += 2 if (c == "\r" and i + 1 < len(text) and text[i + 1] == "\n") else 1
            end_row(); continue
        field.append(c); i += 1
    if field or row:
        end_row()
    return rows

# ---------------------------------------------------------------- alignment

def align(left_rows, right_rows):
    """Groups (l,r,status); status in {=,<>,+-, -+}.

    Custom LCS DP with an explicit tie rule: when the maximum does not
    require the diagonal, prefer advancing the LEFT axis (a left row is
    orphaned first), which pins the shared match at the EARLIER right index
    (measured on T12-swap: oracle `x+- / y= / x-+`, not difflib's mirror;
    same preference settles T13-cont).  Inside replaced gaps the rows zip
    positionally (P1/P2).  The Rust product uses myers.rs with this
    direction verified on the archive.
    """
    a = [tuple(c.strip() for c in r) for r in left_rows]
    b = [tuple(c.strip() for c in r) for r in right_rows]
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    pairs = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            pairs.append((i, j)); i += 1; j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1                      # prefer orphaning the LEFT row first
        else:
            j += 1
    out = []
    pi = pj = 0
    for l, r in pairs:
        ls = list(range(pi, l)); rs = list(range(pj, r))
        k = min(len(ls), len(rs))
        for t in range(k):
            out.append((ls[t], rs[t], "<>"))
        for t in range(k, len(ls)):
            out.append((ls[t], None, "+-"))
        for t in range(k, len(rs)):
            out.append((None, rs[t], "-+"))
        out.append((l, r, "="))
        pi, pj = l + 1, r + 1
    ls = list(range(pi, n)); rs = list(range(pj, m))
    k = min(len(ls), len(rs))
    for t in range(k):
        out.append((ls[t], rs[t], "<>"))
    for t in range(k, len(ls)):
        out.append((ls[t], None, "+-"))
    for t in range(k, len(rs)):
        out.append((None, rs[t], "-+"))
    return out

# ---------------------------------------------------------------- rendering

def numeric(s: str) -> bool:
    return bool(s) and bool(NUM_RE.fullmatch(s))

def display(v: str) -> str:
    """Cell display text: trimmed, and newlines inside a quoted cell render
    as NUL (measured raw bytes in T21 side-by-side and interleaved reports).
    """
    return v.strip().replace("\n", "\x00")

def column_widths(groups, left, right, shared=False):
    """Column widths (incl. header letter, min 1).  The column COUNT is the
    max over both sides (T18: LEFT renders the right-only C column, empty,
    width 1); the widths themselves come only from that side's rows.
    `shared=True` merges both sides per column.  (Whether a RIGHT orphan row
    whose cells are narrower than the left widths forces those columns wider
    -- "forcing" -- is probed in m62b-width; the archive has no pinning case,
    and the plain per-side rule reproduces all 56.)"""
    n = max([len(left[g[0]]) for g in groups if g[0] is not None] +
            [len(right[g[1]]) for g in groups if g[1] is not None] +
            [0])
    def widths(rows, pick):
        ws = []
        for c in range(n):
            w = 1
            for g in groups:
                idx = pick(g)
                if idx is None:
                    continue
                v = display(rows[idx][c]) if c < len(rows[idx]) else ""
                w = max(w, len(v))
            ws.append(w)
        return ws
    lw = widths(left, lambda g: g[0])
    rw = widths(right, lambda g: g[1])
    if not shared:
        return lw, rw
    return [max(a, b) for a, b in zip(lw, rw)], None

def render_cells(rows, gi, ws, num_right=True):
    """Cells padded to column widths (EMPTY cells included -- they
    contribute their width as spaces; only the far END is trimmed, see the
    joiners), joined by ' '.  num_right: numeric cells rjust (side-by-side)
    else ljust (interleaved, measured T19 `q  1`, T21 `z 3   4`)."""
    parts = []
    for c in range(len(ws)):
        v = "" if gi is None or c >= len(rows[gi]) else rows[gi][c].strip()
        d = display(v)
        pad = d.rjust if (num_right and numeric(v)) else d.ljust
        parts.append(pad(ws[c]))
    return " ".join(parts)

def render_header(ws, rstrip=True):
    """Column letters padded exactly like cells, joined by one space
    (measured: widths [2,1] -> 'A  B'; [1,3,1] -> 'A B   C').  Side-by-side
    keeps the LEFT block UN-rstripped -- the trailing padding of the last
    column is part of the left field and the header's blank marker field
    starts after it (T15: 'A  B   ' + 4 spaces; T19 'A  B ' + 4; F2/T17
    same) -- only the whole line end is trimmed."""
    out = " ".join(chr(ord("A") + c).ljust(ws[c]) for c in range(len(ws)))
    return out.rstrip() if rstrip else out

HEADER_GAP = "     "  # five spaces, same as text layouts::HEADER_GAP

def frame(title, stamp, mode, lang):
    zh = lang == "zh"
    t = "表格比较(B)" if zh else "Table Compare"
    prod = "已产生： " if zh else "Produced: "
    lines = [t, f"{prod}{stamp}", ""]
    if mode:
        lines.append("模式：  全部" if zh else "Mode:  All")
    return lines

def sbs_body(groups, left, right):
    lw, rw = column_widths(groups, left, right)
    all_same = all(g[2] == "=" for g in groups)
    lf = " = " if all_same else " =  "
    rendered_l = [render_cells(left, g[0], lw) for g in groups]
    rendered_r = [render_cells(right, g[1], rw) for g in groups]
    rows_out = []
    for (l, r, st), lt, rt in zip(groups, rendered_l, rendered_r):
        f = lf if st == "=" else " " + st + " "
        if l is not None and r is not None:
            line = lt + f + rt
        elif r is None:
            line = lt + f          # left orphan: nothing after the marker
        else:
            line = lt + f + rt     # right orphan: lt is the full blank field
        rows_out.append(line.rstrip())
    blank = "   " if all_same else "    "
    header = (render_header(lw, rstrip=False) + blank
              + render_header(rw)).rstrip()
    width = max([len(header)] + [len(x) for x in rows_out])
    rule = "-" * width
    return [header, rule] + rows_out + [rule]

def interleaved_body(groups, left, right):
    ws, _ = column_widths(groups, left, right, shared=True)
    lnum_of, rnum_of = {}, {}
    li = ri = 0
    for g in groups:
        if g[0] is not None:
            lnum_of[g[0]] = li + 1; li += 1
        if g[1] is not None:
            rnum_of[g[1]] = ri + 1; ri += 1
    lw_, rw_ = len(str(li)), len(str(ri))
    hdr_cells = render_header(ws)
    header = (" " * lw_ + " " + " " * rw_ + " " + hdr_cells).rstrip()
    lines = []
    def row(l, r):
        # BOTH numbers show for '=' rows and for each '<>' line of the pair
        a = str(lnum_of[l]).rjust(lw_) if l is not None else " " * lw_
        b = str(rnum_of[r]).rjust(rw_) if r is not None else " " * rw_
        cells = (render_cells(left, l, ws, num_right=False) if l is not None
                 else render_cells(right, r, ws, num_right=False))
        return (a + " " + b + " " + cells).rstrip()
    for l, r, st in groups:
        if st == "<>":
            lines.append(row(l, None))
            lines.append(row(None, r))
        else:
            lines.append(row(l, r))
        lines.append("-")  # block separator marker; width fixed later
    width = max(len(header), *(len(x) for x in lines if x != "-"))
    out = [header, "-" * width]
    for x in lines:
        out.append("-" * width if x == "-" else x)
    return out

def summary_body(groups, lang="en"):
    same = sum(1 for g in groups if g[2] == "=")
    diff = sum(1 for g in groups if g[2] == "<>")
    lo = sum(1 for g in groups if g[2] == "+-")
    ro = sum(1 for g in groups if g[2] == "-+")
    if lang == "en":
        items = [(same, "same row(s)"), (diff, "important difference row(s)"),
                 (lo, "important left orphan row(s)"),
                 (ro, "important right orphan row(s)")]
    else:
        items = [(same, "个相同排"), (diff, "个重要差异排"),
                 (lo, "个重要的左边独有排"), (ro, "个重要右边独有排")]
    return [f"{n} {lab}" for n, lab in items if n]

def render(layout, left_text, right_text, stamp="STAMP", lang="en"):
    left = split_records(left_text)
    right = split_records(right_text)
    groups = align(left, right)
    return body(layout, groups, left, right, lang)

def body(layout, groups, left, right, lang="en"):
    if layout == "side-by-side":
        return sbs_body(groups, left, right)
    if layout == "interleaved":
        return interleaved_body(groups, left, right)
    if layout == "summary":
        return summary_body(groups, lang)
    raise ValueError(layout)

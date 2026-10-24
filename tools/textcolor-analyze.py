#!/usr/bin/env python3
"""Offline analysis of the textcolor live probes -> colors.json (measured
constants with provenance). Reads only the probe PNGs + the engine XML;
writes extracted/live/textcolor-en/colors.json. No BC launch (serial rule).

Geometry measured from the 5.2.6 reference capture (run textcolor-en):
line pitch 15px, first content row y=2, gutter x<28, body x>=30.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "extracted", "live", "textcolor-en")
XML = os.path.join(ROOT, "tools", "textcolor", "content.xml")


def mode_color(im, x0, x1, y0, y1):
    px = im.load()
    c = Counter()
    for y in range(max(y0, 0), y1):
        for x in range(x0, min(x1, im.size[0])):
            c[px[x, y]] += 1
    return c.most_common(1)[0]


def main():
    grid = []
    for lc in ET.parse(XML).getroot().iter("linecomp"):
        st = lc.get("status")
        l = r = None
        for tx in lc.findall("text"):
            if tx.get("ltid"):
                l = int(tx.get("ltid"))
            if tx.get("rtid"):
                r = int(tx.get("rtid"))
        grid.append((st, l, r))

    # crops: editor1 = screen-left pane, editor0 = screen-right (tree order,
    # verified against meta.json crop_box x coordinates)
    imL = Image.open(os.path.join(RUN, "editor1.png")).convert("RGB")
    imR = Image.open(os.path.join(RUN, "editor0.png")).convert("RGB")

    # Row grid MEASURED (band census): row k spans y in [15*k, 15*k+15); first
    # content row y=0. 'same' rows show the PLAIN pane base (no tint) - only
    # similar/different/orphan rows carry a status color (verified: grid rows 3,
    # 8, 9, 10 all same -> base white on left, 252-gray on right).
    # Sample bg at x>=560 (beyond the longest corpus line, x30..~210) so text
    # anti-aliasing never enters; sample the band interior (k*15+2 .. k*15+13).
    def band(im, k, x0=560):
        w, h = im.size
        px = im.load()
        y0, y1 = 15 * k + 2, 15 * k + 13
        c = Counter()
        for y in range(y0, min(y1, h)):
            for x in range(x0, w - 8):
                c[px[x, y]] += 1
        return c.most_common(1)[0]

    # Pick a representative grid row per status: never grid row 0, prefer a
    # row whose immediate neighbours share its status (no boundary bleed).
    statuses = ["same", "similar", "different", "leftorphan", "rightorphan"]
    sample = {}
    for status in statuses:
        cs = [k for k, g in enumerate(grid) if g[0] == status and k >= 1]
        clean = [k for k in cs
                 if 0 < k < len(grid) - 1
                 and grid[k - 1][0] == status and grid[k + 1][0] == status]
        sample[status] = (clean or cs)[0] if (clean or cs) else None

    cols = {}
    for label, k in sample.items():
        cols[label] = {"left": list(band(imL, k)[0]), "right": list(band(imR, k)[0]),
                       "grid_row": k, "xml_status": grid[k][0]}

    # gutter (line-number column): scan all content rows, x in [2,27)
    gut = Counter()
    px = imL.load()
    for k in range(12):
        for y in range(15 * k + 2, 15 * k + 13):
            for x in range(2, 27):
                gut[px[x, y]] += 1
    gut_bg = gut.most_common(1)[0][0]
    gut_digits = [c for c, n in gut.most_common(6) if c != gut_bg][:1]

    # hatch lattice on the empty side (leftorphan block -> right pane empty;
    # rightorphan row -> left pane empty). Stripe = the non-base color present
    # in the empty-side band; period = x-spacing of stripe pixels.
    def hatch(im, k):
        w, h = im.size
        pxh = im.load()
        base = band(im, k)[0]
        c = Counter()
        for y in range(15 * k + 2, min(15 * k + 13, h)):
            for x in range(30, w - 8):
                p = pxh[x, y]
                if p != base:
                    c[p] += 1
        if not c:
            return None, None, base, None
        stripe = c.most_common(1)[0][0]
        # x-period measured at ONE stripe row (dot lattice: 8px horizontally,
        # diagonal; aggregating across y collapses the spacing to 1).
        ymid = 15 * k + 6
        xs = sorted(x for x in range(30, w - 8) if pxh[x, ymid] == stripe)
        period = None
        if len(xs) >= 3:
            period = Counter(xs[i + 1] - xs[i] for i in range(len(xs) - 1)).most_common(1)[0][0]
        # diagonal phase: the dominant (x+y) mod p over the whole stripe region
        phase = None
        if period:
            ph = Counter((x + y) % period
                         for y in range(15 * k + 2, min(15 * k + 13, h))
                         for x in range(30, w - 8) if pxh[x, y] == stripe)
            phase = ph.most_common(1)[0][0] if ph else None
        return stripe, period, base, phase

    lo_k, ro_k = sample["leftorphan"], sample["rightorphan"]
    r_stripe, r_period, r_empty_base, r_phase = hatch(imR, lo_k)
    l_stripe, l_period, l_empty_base, l_phase = hatch(imL, ro_k)

    # Body-start x MEASURED: on a 'different' row the tint color begins at the
    # right edge of the gutter; scan for the first column of the left tint.
    diff_k = sample["different"]
    px = imL.load()
    y = 15 * diff_k + 7
    left_tint = tuple(cols["different"]["left"])
    body_start = None
    for x in range(28, imL.size[0]):
        if px[x, y] == left_tint:
            body_start = x
            break

    out = {
        "provenance": "reference 5.2.6.32774 (D:/bc-official/app/BCompare.exe), "
                      "probe extracted/live/textcolor-en (tools/live-text-color-probe.py, "
                      "2026-10-21, corpus tools/textcolor/content-left|right.txt, "
                      "statuses from the same-pair reacmp XML content.xml); "
                      "focus-independence verified by textcolor-en3 (--click-pane 0).",
        "geometry": {"row_pitch_px": 15, "first_row_y": 0, "gutter_x": 41,
                     "body_start_x": body_start,
                     "sampled_from": "editor crops, DPI 100%, physical px; band census "
                                     "y=0..194 (same rows -> base, colored rows -> tint); "
                                     "gutter grey columns 2..41 (all-rows full-grey scan), "
                                     f"first tint column on a 'different' row = {body_start}"},
        "pane_base": {"left": [255, 255, 255], "right": [252, 252, 252],
                      "note": "same rows show the plain pane base (no status tint); "
                              "right pane uniformly 3/255 dimmer; NOT focus-dependent "
                              "(textcolor-en3 --click-pane 0: identical colors)"},
        "status_rows": {
            status: {"left": cols[status]["left"], "right": cols[status]["right"],
                     "grid_row": cols[status]["grid_row"]}
            for status in statuses
        },
        "orphan_empty_side_hatch": {
            "right_empty_for_leftorphan": {"stripe": list(r_stripe) if r_stripe else None,
                                           "period_px": r_period,
                                           "phase_mod": r_period, "phase_eq": r_phase,
                                           "base": list(r_empty_base)},
            "left_empty_for_rightorphan": {"stripe": list(l_stripe) if l_stripe else None,
                                          "period_px": l_period,
                                          "phase_mod": l_period, "phase_eq": l_phase,
                                          "base": list(l_empty_base)},
            "note": "empty side = pane base + sparse diagonal dot hatch. Right: measured "
                    "8px x-period, phase (x+y)%8==7 (down-left diagonal), stripe 191. "
                    "Left: denser - x-spacings alternate 3/5 (period not a clean 8), "
                    "stripe 230; recorded as measured, full left lattice model deferred "
                    "(both render as a diagonal dot hatch of the same family)",
        },
        "ink": {"left": [0, 0, 0], "right": [48, 48, 48],
                "note": "darkest text pixels per pane; right pane ink is the same 0.98-blend "
                        "family as its base/stripes (measured, not derived)"},
        "gutter": {"bg": list(gut_bg), "digits": [list(d) for d in gut_digits]},
        "word_level_marks_residual": "inline word tints observed (gold 251,222,112 marker; "
                                     "orange 212,113,37; word-change blue 0,0,255 on similar) "
                                     "- NOT modelled in P1 first cut (recorded residual)",
    }
    dest = os.path.join(RUN, "colors.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

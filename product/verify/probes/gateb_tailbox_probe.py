#!/usr/bin/env python3
"""Tail-NW box geometry probe: pin WHY the tail DP reaches 7 cells past the
collect box (archived truth: W-off1990 needs WT=2000 = cursor+1999 to match
the Oracle; WT=1994..1996 and 2001..2003 all regress).

Candidate models (predictions stated BEFORE the run):

  M1  wave origin = (cursorL + 7, cursorR + 7): the do-while head-steps once
      unconditionally (140e733b0.c:52-56), and the tail NW box is clamped to
      *param_4 = origin-side end => box = [origin .. origin + W - 1], i.e.
      shifted +7 relative to the cursor.  PREDICTION for shape S1..S100 @ off:
        -- block START offset (cursor 0-based: L=100, R=off) --
           reachable R start pairs <= 100 + (W-1) - 7  = cursorR + 1992 - 7?
           Actually: boxR = min(end, (off+7) + W - 1); pairs block while
           off <= 100-? ... net effect: pairing dies 7 SOONER than W=1993
           would allow (boundary off = 1992 - 7 = 1985, and the block end
           constraint unchanged at 2085).
        -- pure-DP (K=2) start offset: first pairable start = originL - W + 1?
           DP box covers rows cursor..bxR shifted: start pairs while
           start + W - 1 >= 1993 => start >= 1993 - (W-1) + 7 => 1999? NO:
           with the +7 shift, boxR = start + 7 + 1992 => DP reach boundary
           moves from 1992 to 1999.
      M1 predicts: K2 boundary PAIR at 1993..1998, UNPAIRED at 1999..2002.
      (matches the empirical WT=2000 == reach-1999 only partially: M1 keeps
      collect at 1993 from cursor, pairs block <= 1985.)

  M2  tail box = [cursor, cursor + W + 6] (sim WT=2000 knob): collect box is
      1993 from cursor, tail box is 2000 from cursor.
      M2 predicts: K2 boundary UNPAIRED starting at 2000; block-pair boundary
      unchanged 2085.

  M3  job+0x98 (window) == 2000 and the *collect* wave is clipped by 7 from
      the seen/visited grid allocation => collect box [cursor .. cursor + 1992]
      and tail box [cursor .. cursor + 1999]. Same as M2 for the tail; for
      collection the 2085 boundary must stay (it does: bxR=cursor+1992).
      Indistinguishable from M2 on THIS family; distinguish via K2 pure-DP
      offset 1993: M2/M3 pair (tail box reach), M1 does NOT pair at 1993?
      NO -- wait: archived truth: K2-off1993 (gateb-width8) is in the 137 and
      PASSES at WT=2000/router. Read the archived XMLs first (done in notes).

Discriminating fixtures (K=2 -> run weight 62 <= 500, NO candidates -> pure
NW; the pairing boundary pins the tail-box reach directly):

  KD-off1993..1999, KD-off2000..2003   (start offset sweep, pure DP)
  WD-off1985..1992                     (block start sweep near collect end)

Usage (serial):  cd D:\Rea\product\verify && python probes/gateb_tailbox_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

N = 10000
K = 100
K2 = 2

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')

def rows_of(body):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2)); rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("gateb-tailbox-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    cases = []
    # pure-DP start-offset sweep (no run collector contribution)
    for off in range(1990, 2006):
        left = [f"S{i}" for i in range(K2)] + [f"A{i}" for i in range(N)]
        right = ([f"B{i}" for i in range(off)] + [f"S{i}" for i in range(K2)]
                 + [f"B{i}" for i in range(off, N)])
        cases.append((f"KD-off{off}", left, right, K2))
    # block-start sweep at high offsets (collect-box end boundary + tail interplay)
    for off in range(1980, 1994):
        left = [f"S{i}" for i in range(K)] + [f"A{i}" for i in range(N)]
        right = ([f"B{i}" for i in range(off)] + [f"S{i}" for i in range(K)]
                 + [f"B{i}" for i in range(off, N)])
        cases.append((f"WD-off{off}", left, right, K))

    results = []
    for tag, left, right, k in cases:
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        o_rows = rows_of(o_body)
        # how many block lines 1..k got paired (ltid in 1..k with an rtid)?
        pairs = [(l, r) for s, l, r in o_rows if l is not None and r is not None and 1 <= l <= k]
        rec = {"tag": tag, "elapsed": run.elapsed_s, "paired": len(pairs),
               "first_unpaired_l": next((i + 1 for i in range(k)
                    if not any(l == i + 1 for l, r in pairs)), None)}
        results.append(rec)
        print(f"{tag}: paired {len(pairs):4}/{k:4}  first_unpaired_l={rec['first_unpaired_l']}  ({run.elapsed_s:.1f}s)")
    (run_dir / "tailbox.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

# Mode3 (banded window engine) simulator — main-session kickoff 2026-10-16

## Established this session (before dispatch)

1. **Architecture (O+D, D1 probe)**: CLI `text-report` aligns with strategy
   descriptor `0x140e71510` whose interval vtable slot is `140e73b40`
   (`_scratch/align-strategy-classes.txt` lines 71-73) = **pure mode3 banded
   engine, no anchor pass, no gate B**. D1 fixture
   (`runs/gateb-alwaysbanded-20261016T043802Z`, min side 4500 < 5000, zero
   duplicate keys, block at off=4500): oracle block pairs = **0** → banded
   regardless of size. The `140e74b60` gate/anchor branch is never taken in CLI
   mode. §24.3's "anchor doesn't preempt" tension is resolved: anchors don't
   exist on this path at all.
2. **Width (O, 13/13 replay)**: window W = `job+0x98` = 1993; box
   `[start..start+1992]` both sides, clipped to interval end.
3. **Candidate gate (O)**: `weight > 500`; line weight non-blank `len+30`,
   blank `2*len+50`, missing 2 (140e75c50 corrected). Explains K=1/K=2
   anomalies; soft-assert `>4999` branch does not terminate.
4. **Off=1000 ground truth** (segment dump): right orphans R1..1000, S-block
   100 pairs, then 8000 shifted `different` pairs L101..8100 ↔ R1101..9100,
   then left orphans L8101..9100, then diagonal pairs L9101..10100↔R9101..10100.
   The whole-table NW (product) instead pairs 9100 shifted + 1000 tail-left
   orphans. Orphan placement + shifted/diagonal split are banded artifacts.
5. **Band walk structure (O from pseudocode)**:
   - `140e73b40`: loop; one-sided → orphan chunks of ≤200 rows (step +199);
     resume cursor = clipped box end + 1.
   - `140e733b0`: box = start+1992 clipped both sides; anti-diagonal wave
     collects runs via `140e73040`; seen-bitmap skip; runs extend past box,
     bounded by interval end (flag +0xb8); `uVar3`(=param_6 in emit) = interval
     touches table end — **always 1 in CLI mode**.
   - `140e74100`: clip runs to box ONLY when param_6==0 (never in CLI); sort
     (-weight, startR, startL); nested-overlap resolution (truncate/shift/kill
     with reweight <500→0); sort (startR, startL); cursor walk: gap NW
     (stop_at_edge=0) before each run, run emitted 1:1, then because
     param_6==1 and runs emitted: **tail is skipped entirely, box end clips to
     last run end** (`140e74100.c:164-167`). When no run: tail NW
     stop_at_edge=1 → clips band end to consumed coordinate.
   - `140e74660`: DP match=pair_similarity(plain: whitespace-removed, case
     preserved — f0092 rule), gap -20, tie diag>skipLeft>skipRight, walk starts
     at reversed corner (pair (Lstart,Rstart) first), stop_at_edge halts when
     either index reaches 0 and clips.
6. **Open puzzle for the simulator**: at the table-edge bands the oracle shows
   28-shifted/1000-orphan/1000-diagonal instead of 1028-shifted. The exact
   box sizes / walk stops must be reproduced empirically (38 archived oracle
   XMLs across runs/gateb-*). Candidate explanation to test: run-extension cap
   at box end (`+0xb8` semantics), stop_at_edge details, or tie direction.

## Fixtures inventory
- runs/gateb-window-*/S1..S7 (disjoint/rotated ≤5000: expect SAME with NW)
- runs/gateb-width-*/W-off{1000..9000} (paired-count 100/0 + full row layout)
- runs/gateb-width2..8-* + width6/7 (K=2/50/100/200/neg/big1 boundary cases)
- runs/gateb-alwaysbanded-*/D1

## Deliverable
`_scratch/mode3/simulate_mode3.py`: read fixtures + oracle XMLs, emit rows
(status, ltid, rtid 1-based, matching oracle row XML), compare per fixture.
Iterate until 100% match on ALL archived fixtures. Then a Rust port spec.

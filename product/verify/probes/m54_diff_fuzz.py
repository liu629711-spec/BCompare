#!/usr/bin/env python3
"""M5.4 probe -- differential fuzz: product vs BC on randomized inputs.

M5.1's alignment rewrite (closeness objective + tie rules) and M5.2's
statistics change were each validated on targeted shapes. This probe throws
randomized small files at both engines and compares the XML pairing
(status, ltid, rtid) per linecomp -- the same raw truth the m51b probe used,
language-neutral so the localized Oracle needs no label table.

Generator: a seeded PRNG builds a shared line pool per case (words, comments,
duplicates, blanks, case pairs), then derives left/right by independent
insert/delete/replace/case/whitespace mutations. Fixtures land under
`runs/m54-fuzz-<ts>/fixtures/` so any disagreement can be replayed by hand.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m54_diff_fuzz.py [count] [seed]
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

WORDS = ["alpha", "beta", "gamma", "delta", "x", "yy", "int", "value",
         "item", "node", "tmp", "data"]

#: comment openers per extension (closed by nothing -- line comments only)
COMMENT = {".txt": None, ".c": "//", ".py": "#"}


def make_pool(rng: random.Random, ext: str) -> list[str]:
    """A pool of plausible lines, biased toward collisions."""
    pool: list[str] = []
    cmt = COMMENT[ext]
    for _ in range(rng.randint(8, 16)):
        n = rng.randint(1, 4)
        line = " ".join(rng.choice(WORDS) for _ in range(n))
        style = rng.random()
        if style < 0.15 and cmt:
            line = f"{cmt} {line}"
        elif style < 0.25:
            line = line.upper() if rng.random() < 0.5 else line.capitalize()
        elif style < 0.33:
            line = line + "  " if rng.random() < 0.5 else " " + line
        pool.append(line)
    pool.append("")          # blanks collide too
    pool.append("")
    return pool


def mutate(rng: random.Random, base: list[str], pool: list[str]) -> list[str]:
    lines = list(base)
    for _ in range(rng.randint(0, 4)):
        op = rng.random()
        if op < 0.3 and lines:
            del lines[rng.randrange(len(lines))]
        elif op < 0.6:
            lines.insert(rng.randint(0, len(lines)), rng.choice(pool))
        elif op < 0.8 and lines:
            i = rng.randrange(len(lines))
            lines[i] = rng.choice(pool)
        elif op < 0.9 and lines:
            i = rng.randrange(len(lines))
            lines[i] = lines[i].upper() if rng.random() < 0.5 else lines[i].lower()
        elif lines:
            i = rng.randrange(len(lines))
            lines[i] = lines[i].strip() if rng.random() < 0.5 else f"{lines[i]} "
    return lines


def pairing(body: str) -> list[tuple[str, str, str]]:
    out = []
    for m in re.finditer(r'<linecomp status="(\w+)">(.*?)</linecomp>', body, re.S):
        lt = re.search(r'ltid="(-?\d+)"', m.group(2))
        rt = re.search(r'rtid="(-?\d+)"', m.group(2))
        out.append((m.group(1), lt.group(1) if lt else "-",
                    rt.group(1) if rt else "-"))
    return out


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261014
    rng = random.Random(seed)

    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m54-fuzz-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"fuzz    : {count} cases, seed {seed}\n")

    agree = 0
    mismatches: list[dict] = []
    for case in range(count):
        ext = rng.choice([".txt", ".c", ".py"])
        pool = make_pool(rng, ext)
        base = [rng.choice(pool) for _ in range(rng.randint(2, 12))]
        left = mutate(rng, base, pool)
        right = mutate(rng, base, pool)
        if left == right:
            right = right + [rng.choice(pool)]

        tag = f"f{case:04d}"
        lp = fx / f"{tag}-L{ext}"
        rp = fx / f"{tag}-R{ext}"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")

        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if run.report_exists and run.report_bytes else ""

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                       capture_output=True, timeout=120)
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if p_out.exists() else ""

        o_p, p_p = pairing(o_body), pairing(p_body)
        if o_p == p_p:
            agree += 1
        else:
            mismatches.append({
                "tag": tag, "left_file": str(lp), "right_file": str(rp),
                "oracle": o_p, "product": p_p,
            })
            print(f"  DIFF {tag}: oracle={o_p}")
            print(f"            product={p_p}")

    print(f"\n{agree}/{count} pairings agree (seed {seed})")
    (run_dir / "m54-results.json").write_text(json.dumps(
        {"count": count, "seed": seed, "agree": agree,
         "mismatches": mismatches}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"raw: {run_dir / 'm54-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

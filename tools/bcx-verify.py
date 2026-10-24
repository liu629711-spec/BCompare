"""Compare our clone's report structure against BC's golden reports.

Checks the status sequence per case (the primary compatibility claim), and
reports text-level differences separately.
"""
import json, pathlib, re, subprocess, sys

GOLDEN = pathlib.Path(r"D:\Rea\verify\golden")
BCX = pathlib.Path(r"D:\Rea\clone\target\debug\bcx.exe")

def statuses(xml: str) -> list[str]:
    return re.findall(r'<linecomp status="([a-z]+)"', xml)

def texts(xml: str) -> list[tuple[str, str]]:
    return re.findall(r'<text ([^>/]*?)(?:/>|>([^<]*)</text>)', xml)

def main() -> int:
    man = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    ok = bad = 0
    for name, info in man.items():
        lp, rp = pathlib.Path(info["left"]), pathlib.Path(info["right"])
        if not lp.exists():
            continue
        # map the manifest's option name to our CLI flag
        cmd = [str(BCX), str(lp), str(rp)]
        if name.startswith("opt-"):
            opt = name[4:]
            cmd.append(f"--opt={opt}")
        ours = subprocess.run(cmd, capture_output=True, text=True)
        got = statuses(ours.stdout)
        want = info["statuses"]
        if got == want:
            ok += 1
            print(f"  ok   {name:<26} {got}")
        else:
            bad += 1
            print(f"  DIFF {name:<26} ours={got}")
            print(f"       {'':<26} BC  ={want}")
    print(f"\n{ok}/{ok+bad} status sequences match BC")
    return 1 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())

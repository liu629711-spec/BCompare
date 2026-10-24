"""Byte-level comparison of our layouts against BC's captured reports."""
import json, pathlib, re, subprocess

LAY = pathlib.Path(r"D:\Rea\verify\layouts")
BCX = pathlib.Path(r"D:\Rea\clone\target\debug\bcx.exe")

def normalize(s: str) -> str:
    """Blank out volatile fields (timestamps, absolute paths)."""
    s = re.sub(r"Produced: [0-9/: ]+", "Produced: <TIME>", s)
    s = s.replace(str(LAY), "<DIR>")
    s = s.replace("\\", "/")
    return s

def main() -> int:
    man = json.loads((LAY / "manifest.json").read_text(encoding="utf-8"))
    ok = bad = 0
    for name, info in man.items():
        case, layout = info["case"], info["layout"]
        lp = LAY / f"{case}-L.txt"
        rp = LAY / f"{case}-R.txt"
        bc = (LAY / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
        ours = subprocess.run([str(BCX), str(lp), str(rp), f"--layout={layout}"],
                              capture_output=True, text=True).stdout
        if normalize(ours) == normalize(bc):
            ok += 1
            print(f"  ok   {name}")
        else:
            bad += 1
            print(f"  DIFF {name}")
            a, b = normalize(ours).splitlines(), normalize(bc).splitlines()
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else "<none>"
                y = b[i] if i < len(b) else "<none>"
                if x != y:
                    print(f"        ours: {x!r}")
                    print(f"        BC  : {y!r}")
                    break
    print(f"\n{ok}/{ok+bad} layouts byte-match BC")
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())

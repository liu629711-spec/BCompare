"""Directory-comparison anchors: capture BC's folder-report output.

Complements the text anchors: same oracle technique, folder mode.
"""
import importlib.util, json, pathlib, shutil

TOOLS = pathlib.Path(r"D:\Rea\tools")
WORK = pathlib.Path(r"D:\Rea\verify\dir")
OUT = WORK / "reports"

_spec = importlib.util.spec_from_file_location("bc_oracle", TOOLS / "bc-oracle.py")
bc_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc_oracle)

def build_fixture(root: pathlib.Path) -> None:
    """Two folder trees with a controlled set of differences."""
    if root.exists():
        shutil.rmtree(root)
    L = root / "L"
    R = root / "R"
    L.mkdir(parents=True); R.mkdir(parents=True)
    # identical file
    (L/"same.txt").write_text("hello\n", encoding="utf-8")
    (R/"same.txt").write_text("hello\n", encoding="utf-8")
    # differing content, same size? (make same length to test CRC/content rules)
    (L/"diff.txt").write_text("aaaa\n", encoding="utf-8")
    (R/"diff.txt").write_text("bbbb\n", encoding="utf-8")
    # same size, different bytes
    (L/"samesize.bin").write_bytes(b"\x01\x02\x03\x04")
    (R/"samesize.bin").write_bytes(b"\x01\x02\x03\x05")
    # left-only / right-only
    (L/"leftonly.txt").write_text("L\n", encoding="utf-8")
    (R/"rightonly.txt").write_text("R\n", encoding="utf-8")
    # subfolder, one differing file inside
    (L/"sub").mkdir(); (R/"sub").mkdir()
    (L/"sub"/"inner.txt").write_text("x\n", encoding="utf-8")
    (R/"sub"/"inner.txt").write_text("y\n", encoding="utf-8")
    # empty folder on the right
    (R/"emptydir").mkdir()

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_fixture(WORK/"trees")
    L = WORK/"trees"/"L"
    R = WORK/"trees"/"R"
    results = {}
    for layout in ("folder-report", "xml"):
        out = OUT / f"dir-{layout}.txt"
        script = WORK/"_script.txt"
        script.write_text(
            f'folder-report layout:{layout} output-to:"%3" "%1" "%2"\n',
            encoding="utf-8")
        import subprocess, time
        t0 = time.time()
        p = subprocess.run([str(bc_oracle.BC), "/silent", f"@{script}", str(L), str(R), str(out)],
                           capture_output=True, timeout=120)
        dt = round(time.time()-t0, 2)
        txt = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
        results[layout] = {"exit": p.returncode, "bytes": len(txt), "seconds": dt}
        print(f"  {layout:<14} exit={p.returncode} {len(txt):>5}B {dt}s")
        if p.returncode != 0:
            print("    stderr:", p.stderr.decode('utf-8','replace')[:200])
    (OUT/"manifest.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

import subprocess, sys, os, time
views = ["Home","Text Compare","Text Merge","Hex Compare","Table Compare","Picture Compare",
         "Registry Compare","Version Compare","Folder Compare","Folder Merge","Folder Sync","Media Compare"]
env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
green=[]; red=[]
for v in views:
    r = subprocess.run([sys.executable, "tools/uia-menu-check.py",
                        "extracted/_scratch/menu-spec.json", "--view", v],
                       env=env, capture_output=True, text=True, timeout=120)
    out = (r.stdout+r.stderr).strip()
    fails = [l for l in out.splitlines() if "FAIL" in l]
    if r.returncode==0 and not fails:
        green.append(v); print(f"OK   {v}: {out.splitlines()[0] if out else ''}")
    else:
        red.append((v, r.returncode, fails or out.splitlines()[-3:]))
        print(f"FAIL {v} (rc={r.returncode}):")
        for f in (fails or [out]): print("   ", str(f)[:200])
    time.sleep(1.0)
    # residue guard: kill any lingering reacmp-gui
    subprocess.run("taskkill //F //IM reacmp-gui.exe", shell=True, capture_output=True)
print(f"\n=== live top-bar: {len(green)}/12 green ===")
for v,rc,f in red: print("  RED", v, f)

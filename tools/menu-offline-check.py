#!/usr/bin/env python3
"""OFFLINE gate: replay every view's product ledger against the Oracle matrices.

  dump = dotnet reacmp-gui.dll --menu-spec spec.json --view V --dump out.json
  menu    : ledger items (menu,label,shortcut,enabled) vs presence-matrix
            (membership+order) and enabled-matrix (state) — 845-item axis
  chrome  : ledger toolbars/statusbars triples vs chrome-matrix — 410 axis
  skeleton: ledger skeleton preorder triples vs the spec skeleton (itself
            rebuilt from the 12 home_tree snapshots by skel.py) — 290 axis

Exit 0 only with zero violations on every axis of every view.

Usage: python tools/menu-offline-check.py [spec.json] [--only VIEW]
"""
import json
import os
import subprocess
import sys

ROOT = r"D:\Rea"
DLL = os.path.join(ROOT, r"product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll")
LIVE = os.path.join(ROOT, "extracted", "live")


def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def dump_ledger(spec, view, out):
    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    r = subprocess.run(["dotnet", DLL, "--menu-spec", spec, "--view", view, "--dump", out],
                       env=env, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"dump {view}: rc={r.returncode} {r.stderr[:300]}")
    return json.load(open(out, encoding="utf-8"))


def flat_skel(nodes, acc):
    for n in nodes:
        acc.append((n["ct"], n["cls"], n["name"]))
        flat_skel(n.get("children", []), acc)
    return acc


def main():
    spec = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, r"extracted\_scratch\menu-spec.json")
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    sp = load(spec)
    pres = load(os.path.join("extracted", "live", "presence-matrix.json"))
    enbl = load(os.path.join("extracted", "live", "enabled-matrix.json"))
    chrom = load(os.path.join("extracted", "live", "chrome-matrix.json"))
    views = [only] if only else list(sp["top_menus_per_view"].keys())
    led_path = os.path.join(ROOT, "_tmp", "offline-ledger.json")
    os.makedirs(os.path.dirname(led_path), exist_ok=True)

    total_items = total_chrome = total_skel = 0
    problems = []
    for v in views:
        led = dump_ledger(spec, v, led_path)
        # --- menu axis: presence-matrix item_order keyed "view|menu" ---
        expect = {}
        for key, labels in pres["item_order"].items():
            vv, m = key.split("|", 1)
            if vv == v:
                expect[m] = labels
        got = {}
        for it in led["items"]:
            got.setdefault(it["menu"], []).append(it["label"])
        for m in expect:
            if expect[m] != got.get(m, []):
                problems.append(f"[{v}] menu {m}: order/labels differ")
                a_, b_ = expect[m], got.get(m, [])
                for i, a in enumerate(a_):
                    b = b_[i] if i < len(b_) else None
                    if a != b:
                        problems.append(f"   [{i}] oracle={a!r} product={b!r}")
                        break
                if len(a_) != len(b_):
                    problems.append(f"   counts oracle={len(a_)} product={len(b_)}")
        total_items += len(led["items"])
        # --- brand axis (D1, docs/20): display == ApplyBrand(label), single-point,
        # Oracle label kept in 'label' for matrix replay; 'display' carries our
        # brand; no display row may leak the reference product's name. ---
        for it in led["items"]:
            want_disp = it["label"].replace("Beyond Compare", "LiuCompare")
            if it.get("display") != want_disp:
                problems.append(f"[{v}] brand display {it['menu']}/{it['label']!r}: "
                                f"want={want_disp!r} got={it.get('display')!r}")
            if "Beyond Compare" in (it.get("display") or ""):
                problems.append(f"[{v}] brand leak in display: {it!r}")
        # --- enabled axis: matrix 'item' = label + '\t' + shortcut, captured
        # state = empty session (the same baseline the replay describes) ---
        enmap = {}
        for row in enbl["items"]:
            key = (row["menu"], row["item"])
            if v in row.get("enabled_in", []):
                enmap[key] = True
            elif v in row.get("disabled_in", []):
                enmap[key] = False
        for it in led["items"]:
            full = it["label"] + ("\t" + it["shortcut"] if it.get("shortcut") else "")
            key = (it["menu"], full)
            if key in enmap and bool(it["enabled"]) != enmap[key]:
                problems.append(f"[{v}] enabled {key}: oracle={enmap[key]} product={it['enabled']}")
        # --- chrome axis ---
        ch = chrom.get(v, {"toolbars": [], "statusbars": []})
        for sec, key in (("toolbars", "toolbars"), ("statusbars", "statusbars")):
            want = [[(i["ct"], i["cls"], i["name"]) for i in row] for row in ch[key]]
            gotc = [[(i["ct"], i["cls"], i["name"]) for i in row["items"]] for row in led.get(key, [])]
            if want != gotc:
                problems.append(f"[{v}] chrome {sec}: rows {len(want)} vs {len(gotc)}")
                for i, (a, b) in enumerate(zip(want, gotc)):
                    if a != b:
                        problems.append(f"   row {i} oracle={a[:2]} product={b[:2]}")
                        break
            total_chrome += sum(len(r) for r in want)
        # --- skeleton axis (triples incl row markers) ---
        want = flat_skel(sp["skeleton"].get(v, []), [])
        got = [(s["ct"], s["cls"], s["name"]) for s in led.get("skeleton", [])]
        if want != got:
            problems.append(f"[{v}] skeleton: spec={len(want)} ledger={len(got)}")
            for i, (a, b) in enumerate(zip(want, got)):
                if a != b:
                    problems.append(f"   [{i}] spec={a} ledger={b}")
                    break
        total_skel += len(want)
        print(f"OK   {v}: items={len(led['items'])} chrome-rows={sum(len(r['items']) for r in led['toolbars']+led['statusbars'])} skeleton={len(got)}")

    print(f"\ntotals: menu-items={total_items} chrome-items={total_chrome} skeleton-nodes={total_skel}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("OFFLINE GATE GREEN (0 violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

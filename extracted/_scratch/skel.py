"""Content-view skeleton extractor (prune rule is the measurement basis):
- Rebuild the flat depth-indented home_tree into a nested tree.
- Take each Window node's children; drop the TUiMainDock subtree (menu axis,
  gate 6.6) and the TitleBar subtree (OS chrome).
- Keep nodes whose cls != '' (BC-classed widgets); unnamed leaf Button/Separator/
  Text/MenuItem/Edit children are covered by the chrome rows / menu ledger.
- For each kept ToolBar/StatusBar container: attach its chrome row (pre-order)
  and do not descend (items live in the row ledger).
- Window node itself is dropped from the compared list (WPF window reports
  HwndWrapper class; TViewForm is a native-alias identity).
"""
import json, os
SNAP = {
    "Home": "ref-5.2.6-uia/gui-home-en.json", "Text Compare": "ref-5.2.6-uia/gui-text-session-en.json",
    "Text Merge": "view-textmerge/gui-home.json", "Hex Compare": "view-hex/gui-home.json",
    "Table Compare": "view-table/gui-home.json", "Picture Compare": "view-picture/gui-home.json",
    "Registry Compare": "view-registry/gui-home.json", "Version Compare": "view-version/gui-home.json",
    "Folder Compare": "view-folder/gui-home.json", "Folder Merge": "view-foldermerge/gui-home.json",
    "Folder Sync": "view-foldersync/gui-home.json", "Media Compare": "view-media/gui-home.json",
}

def rebuild(flat):
    kids, stack = [], []
    for n in flat:
        node = {"ct": n["ct"], "cls": n.get("cls", ""), "name": n.get("name", ""), "kids": []}
        while stack and stack[-1][0] >= n["d"]:
            stack.pop()
        (stack[-1][1]["kids"] if stack else kids).append(node)
        stack.append((n["d"], node))
    return kids

def prune(nodes, tbs, sbs, ti=None, si=None, depth=0):
    # NOTE: never default-mutable lists here — shared state across calls poisoned
    # row consumption between views (found by the Text Merge count assert).
    if ti is None: ti = [0]
    if si is None: si = [0]
    out = []
    for n in nodes:
        if n["cls"] == "TUiMainDock" or n["ct"] == "TitleBar":
            continue
        if n["cls"] == "":
            out.extend(prune(n["kids"], tbs, sbs, ti, si, depth))
            continue
        node = {"ct": n["ct"], "cls": n["cls"], "name": n["name"], "kids": [], "row": None}
        if n["cls"] == "TUiToolbar":
            if ti[0] < len(tbs):
                node["row"] = ("tb", ti[0]); ti[0] += 1
        elif n["cls"] == "TUiStatusBar":
            if si[0] < len(sbs):
                node["row"] = ("sb", si[0]); si[0] += 1
        else:
            node["kids"] = prune(n["kids"], tbs, sbs, ti, si, depth + 1)
        out.append(node)
    return out

def skel_json(view, home_dir=r"extracted\live"):
    """Serializable skeleton for the spec: nested (ct, cls, name, row=[sec,idx]).
    row references the chrome block by index — pairing is pre-order and verified
    by extract()'s row-consumption assert."""
    def ser(nodes):
        return [{"ct": n["ct"], "cls": n["cls"], "name": n["name"],
                 "row": list(n["row"]) if n["row"] else None,
                 "children": ser(n["kids"])} for n in nodes]
    return ser(extract(view, home_dir))

def extract(view, home_dir=r"extracted\live"):
    d = json.load(open(os.path.join(home_dir, SNAP[view]), encoding="utf-8"))
    ch = json.load(open(os.path.join(home_dir, "chrome-matrix.json"), encoding="utf-8"))[view]
    tree = rebuild(d["home_tree"])
    wins = [t for t in tree if t["ct"] == "Window"]
    assert wins, view
    body = [c for w in wins for c in w["kids"]]
    skel = prune(body, ch["toolbars"], ch["statusbars"])
    # verify all rows consumed
    used = count_rows(skel)
    assert used[0] == len(ch["toolbars"]) and used[1] == len(ch["statusbars"]), (view, used, len(ch["toolbars"]), len(ch["statusbars"]))
    return skel

def count_rows(skel):
    t = s = 0
    for n in skel:
        if n["row"] is not None:
            t += n["row"][0] == "tb"; s += n["row"][0] == "sb"
        tt, ss = count_rows(n["kids"]); t += tt; s += ss
    return (t, s)

def flat(skel):
    out = []
    for n in skel:
        out.append((n["ct"], n["cls"], n["name"]))
        out.extend(flat(n["kids"]))
    return out

if __name__ == "__main__":
    for v in SNAP:
        sk = extract(v)
        f = flat(sk)
        print(f"{v:17} roots={[n['cls'] for n in sk]} nodes={len(f)}")
        if v in ("Text Compare", "Folder Sync"):
            for t in f: print("   ", t)

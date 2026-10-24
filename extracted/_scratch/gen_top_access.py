import json

# Derive per-view top-menu access keys from the live baseline: BC assigns each
# top menu the access key of its FIRST submenu item (measured: Session->n from
# 'New Session', File->o from 'Open File...', Edit->u from 'Undo', Search->t from
# 'Next Difference', Tools->o from 'Options...', Help->c from 'Contents',
# View->'' from 'Show All' — View has no access key at all).
LIVE = {
    "Home": "ref-5.2.6-uia/gui-home-en.json",
    "Text Compare": "ref-5.2.6-uia/gui-text-session-en.json",
    "Text Merge": "view-textmerge/gui-home.json",
    "Hex Compare": "view-hex/gui-home.json",
    "Table Compare": "view-table/gui-home.json",
    "Picture Compare": "view-picture/gui-home.json",
    "Registry Compare": "view-registry/gui-home.json",
    "Version Compare": "view-version/gui-home.json",
    "Folder Compare": "view-folder/gui-home.json",
    "Folder Merge": "view-foldermerge/gui-home.json",
    "Folder Sync": "view-foldersync/gui-home.json",
    "Media Compare": "view-media/gui-home.json",
}
BASE = "extracted/live"
out = {}
for view, p in LIVE.items():
    r = json.load(open(f"{BASE}/{p}", encoding="utf-8"))
    acc = {}
    for menu, items in r["tops"].items():
        first = next((i for i in items if i.get("ct") == 50011 and i.get("name")), None)
        if first:
            a = first.get("acc", "") or ""
            acc[menu] = a.lower() if a else ""
    out[view] = acc
    print(view, acc)

spec = json.load(open("extracted/_scratch/menu-spec.json", encoding="utf-8"))
spec["top_access"] = out
json.dump(spec, open("extracted/_scratch/menu-spec.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("spec updated with top_access for", len(out), "views")

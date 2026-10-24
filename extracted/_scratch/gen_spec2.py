import json

pres = json.load(open('extracted/live/presence-matrix.json', encoding='utf-8'))
acts = json.load(open('extracted/guibaseline/actions-en.json', encoding='utf-8'))
enbl = json.load(open('extracted/live/enabled-matrix.json', encoding='utf-8'))
chrom = json.load(open('extracted/live/chrome-matrix.json', encoding='utf-8'))

import sys, os
sys.path.insert(0, os.path.join('extracted', '_scratch'))
from skel import extract as skel_extract, skel_json, SNAP as SKEL_VIEWS

# per-view mounted action forms (TBCACTIONS/TSESSIONACTIONS are global; each
# view adds its own table). Derived from the DFM action-table names.
FORMS = {
    "Home": ["TBCACTIONS", "THOMEACTIONS"],
    "Text Compare": ["TBCACTIONS", "TFILEACTIONS", "TTEXTACTIONS", "TSESSIONACTIONS"],
    "Text Merge": ["TBCACTIONS", "TFILEACTIONS", "TTEXTACTIONS", "TSESSIONACTIONS"],
    "Hex Compare": ["TBCACTIONS", "TFILEACTIONS", "THEXACTIONS", "TSESSIONACTIONS"],
    "Table Compare": ["TBCACTIONS", "TFILEACTIONS", "TTABLEACTIONS", "TSESSIONACTIONS"],
    "Picture Compare": ["TBCACTIONS", "TFILEACTIONS", "TPIXACTIONS", "TSESSIONACTIONS"],
    "Registry Compare": ["TBCACTIONS", "TFILEACTIONS", "TREGACTIONS", "TSESSIONACTIONS"],
    "Version Compare": ["TBCACTIONS", "TFILEACTIONS", "TVERACTIONS", "TSESSIONACTIONS"],
    "Media Compare": ["TBCACTIONS", "TFILEACTIONS", "TMEDIAACTIONS", "TSESSIONACTIONS"],
    "Folder Compare": ["TBCACTIONS", "TDIRBASEACTIONS", "TDIRACTIONS", "TSESSIONACTIONS"],
    "Folder Merge": ["TBCACTIONS", "TDIRBASEACTIONS", "TDIRACTIONS", "TSESSIONACTIONS"],
    "Folder Sync": ["TBCACTIONS", "TDIRBASEACTIONS", "TDIRSYNCACTIONS", "TSESSIONACTIONS"],
}
ordered = [{'key': k, 'caption': a['caption'] or '', 'shortcut': a['shortcut'] or '',
            'category': a['category'] or '', 'hint': a['hint'] or '', 'form': a['form']}
           for k, a in acts.items()]

spec = {
    "top_menus_per_view": pres["top_menus_per_view"],
    "view_forms": FORMS,
    "actions": ordered,
    "presence": [{"menu": c["menu"], "item": c["item"], "present_in": c["present_in"]}
                 for c in pres["capability_items"]],
    "item_order": pres["item_order"],
    # live enabled/gray states (TMenuUpdater equivalent input): 264 rows, labels
    # stripped of '\t<shortcut>' to align with presence items (264/264 covered).
    "enabled": [{"menu": i["menu"], "label": i["item"].split("\t")[0],
                 "cls": i["class"], "enabled_in": i["enabled_in"],
                 "disabled_in": i["disabled_in"]}
                for i in enbl["items"]],
    # live toolbar/statusbar rows (U-gui-4 closure, chrome-matrix.json):
    # per-view ordered (control_type, class, name) triples, replayed verbatim.
    "chrome": {v: {"toolbars": c["toolbars"], "statusbars": c["statusbars"]}
               for v, c in chrom.items()},
    # --- dispatch matrix (U-gui-5): view routing measured per cell. Each entry
    # cites the live artifact that proves it; the fallback cell was measured by
    # view-fallback-zqq probe (2026-10-21). Unmeasured extensions fall back.
    "dispatch": {
        "cells": [
            {"kind": "ext", "match": [".txt"], "view": "Text Compare",
             "evidence": "ref-5.2.6-uia/gui-text-session-en.json home_tree root TViewForm title 'Text Compare'"},
            {"kind": "ext", "match": [".bin"], "view": "Hex Compare",
             "evidence": "view-hex/gui-home.json title 'h-int-600-L.bin <--> h-int-600-R.bin - Hex Compare'"},
            {"kind": "ext", "match": [".csv"], "view": "Table Compare",
             "evidence": "view-table/gui-home.json active_view+files"},
            {"kind": "ext", "match": [".png"], "view": "Picture Compare",
             "evidence": "view-picture/gui-home.json title 'p-alpha-ignored-L.png <--> ... - Picture Compare'"},
            {"kind": "dirs", "match": [], "view": "Folder Compare",
             "evidence": "view-folder/gui-home.json active_view=['TDirCompareView','TDirTreeView'] files=dirs L/R"},
            {"kind": "ext", "match": [".reg"], "view": "Text Compare",
             "evidence": "U-gui-5: live probe .reg pair opened TText session, NOT Registry Compare (docs/19)"},
        ],
        "fallback": {"view": "Text Compare",
                     "evidence": "view-fallback-zqq/gui-home.json title 'fb-L.zqq <--> fb-R.zqq - Text Compare'"},
        # task-only views: reached via Home task buttons only (no file dispatch;
        # measured: file pairs never opened these views in 12 view snapshots).
        "task_only": ["Text Merge", "Registry Compare", "Version Compare",
                      "Folder Merge", "Folder Sync", "Media Compare"],
        # unconfirmed picture-family hint from static RE of the shipped binary
        # (0x140ef0870 mask string), NOT behavior-measured: recorded as hint only.
        "hint_ext_picture": [".htm", ".html", ".xml", ".jpg", ".gif"],
        "title_rule": "{L} <--> {R} - {View} - Beyond Compare",
    },
    # content-view skeleton (per-view): BC-classed widget tree under the window,
    # menu/titlebar subtrees pruned; ToolBar/StatusBar nodes carry the index of
    # the chrome row they consume (pre-order pairing, verified by skel.py).
    "skeleton": {v: skel_json(v) for v in SKEL_VIEWS},
    "captured_state": enbl["captured_state"],
    "top_access": json.load(open('extracted/_scratch/menu-spec.json', encoding='utf-8'))["top_access"],
}
json.dump(spec, open('extracted/_scratch/menu-spec.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('spec now per-view: top_menus_per_view + view_forms for', len(spec['view_forms']), 'views')

"""Render the parsed TPF0 UI spec into human-readable markdown tables.

`ui-spec.json` holds every decoded form with its objects and properties. This
renders the parts that describe behavior — actions with captions/accelerators,
and menu/toolbar structure — so the command surface is reviewable without
reading raw JSON.
"""
import json
import pathlib

SPEC = pathlib.Path(r"D:\Rea\extracted\ui-spec.json")
OUT = pathlib.Path(r"D:\Rea\extracted\ui-commands.md")

spec = json.loads(SPEC.read_text(encoding="utf-8"))

lines: list[str] = []
lines.append("# BCompare UI 命令面（由 TPF0 资源解码）")
lines.append("")
lines.append(f"- 表单数：{spec['form_count']}（完整解析 {spec['fully_parsed']}）")
lines.append(f"- 对象总数：{sum(f['object_count'] for f in spec['forms'])}")
lines.append("")

# Action tables hold the命令 definitions: caption carries the accelerator (&X).
action_forms = [f for f in spec["forms"] if "ACTIONS" in f["name"]]
lines.append(f"## 动作表（{len(action_forms)} 个）")
lines.append("")

for form in action_forms:
    actions = [o for o in form["objects"] if o["class"].endswith("Action")]
    if not actions:
        continue
    lines.append(f"### {form['name']} — {len(actions)} 个动作")
    lines.append("")
    lines.append("| 名称 | 标题/加速键 | 提示 |")
    lines.append("|---|---|---|")
    for obj in actions:
        caption = obj["props"].get("Caption") or ""
        hint = obj["props"].get("Hint") or ""
        if isinstance(caption, dict) or isinstance(hint, dict):
            caption, hint = str(caption), str(hint)
        caption = str(caption).replace("|", "\\|")
        hint = str(hint).replace("|", "\\|")[:70]
        lines.append(f"| `{obj['name']}` | {caption} | {hint} |")
    lines.append("")

# Forms with menu items reveal menu structure.
menu_forms = [
    f for f in spec["forms"]
    if any(o["class"] == "TUiMenuItem" for o in f["objects"])
]
lines.append(f"## 含菜单项的表单（{len(menu_forms)} 个）")
lines.append("")
for form in menu_forms:
    items = [o for o in form["objects"] if o["class"] == "TUiMenuItem"]
    lines.append(f"### {form['name']} — {len(items)} 个菜单项")
    lines.append("")
    for obj in items:
        caption = obj["props"].get("Caption") or obj["name"]
        shortcut = obj["props"].get("ShortCut") or obj["props"].get("MacShortCutStr") or ""
        lines.append(f"- `{obj['name']}` — {caption} {f'({shortcut})' if shortcut else ''}")
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
print(f"action tables: {len(action_forms)}  menu forms: {len(menu_forms)}")

#!/usr/bin/env python3
"""Structure-layer comparator for the GUI (docs/19 §2.1/§4; P1 "UI 自动化测试" 门槛骨架)。

把一份"被测窗体描述 JSON"（任何 GUI 框架导出的窗体树）与 BC 的 DFM 结构金标准
`extracted/guibaseline/forms-en.json` 逐格对比，输出差异并给退出码。

刻意让"被测描述"与金标准**同构**（`{name, cls, props, children}`）：这就是 ADR-7
"数据驱动窗体"的契约——产品渲染器输出这个形状即可接此门禁。与框架无关：
egui / WPF / 原生只要导出同构 JSON 都能测。

比对级别（逐级叠加）：
  structure — 类名、实例名、父子层级+声明顺序、Caption/Hint/HelpKeyword（语义文案）
  layout    — + 几何/布局键（Left/Top/Width/Height/Anchors/Align/Constraints/TabOrder …）
  full      — + 其余每个属性（含 On* 事件绑定、Images/ImageIndex 等）

用法:
  python tools/ui-structure-check.py <candidate.json> --form NAME [--level LEVEL]
  python tools/ui-structure-check.py --selftest
  python tools/ui-structure-check.py --emit-sample NAME --out FILE
退出码：0=无差异/自测全过；1=有差异；2=用法或加载错误。
"""
import argparse
import copy
import json
import os
import sys

GOLDEN = r"D:\Rea\extracted\guibaseline\forms-en.json"

TEXT_KEYS = ["Caption", "Hint", "HelpKeyword"]
GEOM_KEYS = ["Left", "Top", "Width", "Height", "Anchors", "Align", "AlignWithMargins",
             "Margins", "Constraints", "TabOrder", "TabStop", "ParentBackground",
             "AutoSize", "BevelOuter", "BorderStyle"]

_ABSENT = object()


def props_required(level):
    if level == "structure":
        return TEXT_KEYS
    if level == "layout":
        return TEXT_KEYS + GEOM_KEYS
    return None  # full: compare every golden prop key


def compare(g_node, c_node, path, level, diffs):
    gc = g_node.get("cls")
    cc = c_node.get("cls")
    if gc != cc:
        diffs.append({"path": path, "kind": "cls", "golden": gc, "candidate": cc})
    gn = g_node.get("name")
    cn = c_node.get("name")
    if gn != cn:
        diffs.append({"path": path, "kind": "name", "golden": gn, "candidate": cn})

    gp = g_node.get("props", {}) or {}
    cp = c_node.get("props", {}) or {}
    if level == "full":
        keys = sorted(gp.keys())
    else:
        keys = [k for k in props_required(level) if k in gp]
    for k in keys:
        gv = gp.get(k, _ABSENT)
        cv = cp.get(k, _ABSENT)
        if gv == cv:
            continue
        if cv is _ABSENT:
            diffs.append({"path": f"{path}.{k}", "kind": "prop-missing", "golden": gv})
        elif gv is _ABSENT:
            diffs.append({"path": f"{path}.{k}", "kind": "prop-added", "candidate": cv})
        else:
            diffs.append({"path": f"{path}.{k}", "kind": "prop-value", "golden": gv, "candidate": cv})

    gch = g_node.get("children", []) or []
    cch = c_node.get("children", []) or []
    gidx = {c.get("name"): c for c in gch}
    cidx = {c.get("name"): c for c in cch}
    for name in gch:
        nm = name.get("name")
        if nm not in cidx:
            diffs.append({"path": f"{path}/{nm}", "kind": "child-missing", "golden_cls": name.get("cls")})
    for name in cch:
        nm = name.get("name")
        if nm not in gidx:
            diffs.append({"path": f"{path}/{nm}", "kind": "child-added", "candidate_cls": name.get("cls")})
    common_g = [c.get("name") for c in gch if c.get("name") in cidx]
    common_c = [c.get("name") for c in cch if c.get("name") in gidx]
    if common_g != common_c:
        diffs.append({"path": path, "kind": "child-order", "golden": common_g, "candidate": common_c})
    for nm in common_g:
        compare(gidx[nm], cidx[nm], f"{path}/{nm}", level, diffs)


def run_check(cand_path, form, level, golden_map=None):
    gm = golden_map if golden_map is not None else json.load(open(GOLDEN, encoding="utf-8"))
    if form not in gm:
        print(f"form {form!r} not in golden ({len(gm)} forms)", file=sys.stderr)
        return 2, None
    cand = json.load(open(cand_path, encoding="utf-8"))
    # candidate may be the bare form tree or wrapped {form: tree}
    if "cls" not in cand and form in cand:
        cand = cand[form]
    diffs = []
    compare(gm[form], cand, form, level, diffs)
    return (1 if diffs else 0), diffs


def summarize(diffs):
    from collections import Counter
    c = Counter(d["kind"] for d in diffs)
    return c


def selftest():
    gm = json.load(open(GOLDEN, encoding="utf-8"))
    # pick a form with at least 3 children to exercise ordering/removal
    form = next(k for k in sorted(gm)
                if len(gm[k].get("children", [])) >= 3 and any(
                    c.get("props", {}).get("Caption") for c in gm[k].get("children", [])))
    base = gm[form]

    def clone():
        return copy.deepcopy(base)

    cases = []

    def expect(label, node, level, want_kinds):
        diffs = []
        compare(base, node, form, level, diffs)
        got = {d["kind"] for d in diffs}
        if want_kinds:  # must surface at least these kinds
            ok = want_kinds <= got
        else:           # must surface nothing
            ok = not diffs
        cases.append((label, ok, sorted(got)))

    # 1: faithful copy -> 0 diffs
    expect("faithful-structure", clone(), "structure", set())
    expect("faithful-full", clone(), "full", set())

    # 2: wrong class on root
    n = clone(); n["cls"] = "TBogus"
    expect("cls-changed", n, "structure", {"cls"})

    # 3: drop one child
    n = clone(); n["children"] = n["children"][:-1]
    expect("child-removed", n, "structure", {"child-missing"})

    # 4: change a Caption somewhere
    n = clone()
    for ch in n["children"]:
        if ch.get("props", {}).get("Caption") is not None:
            ch["props"]["Caption"] = "MUTATED"; break
    expect("caption-changed", n, "structure", {"prop-value"})

    # 5: change Left -> only caught at layout (not structure); search whole tree
    n = clone()
    target = None

    def find_geom(node):
        if node.get("props", {}).get("Left") is not None:
            return node
        for c in node.get("children", []):
            r = find_geom(c)
            if r:
                return r
        return None

    target = find_geom(n)
    if target is not None:
        # locate same node in base for path-based compare (match by name)
        n2 = clone()
        t2 = find_geom(n2)
        t2["props"]["Left"] = t2["props"]["Left"] + 7
        expect("left-changed-at-layout", n2, "layout", {"prop-value"})
        expect("left-changed-not-at-structure", n2, "structure", set())

    # 6: reorder two children (instance names unique => must surface a difference)
    n = clone()
    if len(n["children"]) >= 2:
        a1, a2 = n["children"][0]["name"], n["children"][1]["name"]
        if a1 != a2:
            n["children"][0], n["children"][1] = n["children"][1], n["children"][0]
            diffs = []
            compare(base, n, form, "structure", diffs)
            got = {d["kind"] for d in diffs}
            ok = bool(got)  # swap must be detected as order-diff or add/remove
            cases.append(("child-swapped-detected", ok, sorted(got)))

    print(f"selftest form={form}")
    allok = True
    for label, ok, got in cases:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}  got={got}")
        allok = allok and ok
    return 0 if allok else 1


def _order_or_swap(base, mutated, form):
    diffs = []
    compare(base, mutated, form, "structure", diffs)
    return {d["kind"] for d in diffs}


def emit_sample(form, out, level="full"):
    gm = json.load(open(GOLDEN, encoding="utf-8"))
    if form not in gm:
        print(f"form {form!r} not in golden", file=sys.stderr)
        return 2
    node = copy.deepcopy(gm[form])
    if level != "full":
        def prune(n):
            req = props_required(level)
            n["props"] = {k: v for k, v in (n.get("props", {}) or {}).items()
                          if k in (req or n.get("props", {}).keys())}
            for c in n.get("children", []):
                prune(c)
        prune(node)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(node, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote sample {form} (level={level}) -> {out}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", nargs="?")
    ap.add_argument("--form")
    ap.add_argument("--level", default="layout", choices=["structure", "layout", "full"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--emit-sample", dest="sample_form")
    ap.add_argument("--out")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.sample_form:
        if not a.out:
            print("--out required with --emit-sample", file=sys.stderr)
            return 2
        return emit_sample(a.sample_form, a.out, a.level)
    if not a.candidate or not a.form:
        print(__doc__)
        return 2
    rc, diffs = run_check(a.candidate, a.form, a.level)
    if diffs is None:
        return rc
    for d in diffs:
        print(json.dumps(d, ensure_ascii=False))
    c = summarize(diffs)
    print(f"form={a.form} level={a.level} diffs={len(diffs)} by-kind={dict(c)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

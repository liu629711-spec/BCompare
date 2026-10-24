#!/usr/bin/env python3
"""DFM -> machine-readable structure baseline (docs/19 §2.1 / §4).

Parses the decoded text .dfm files (tools/dfm-extract.py output grammar)
into normalized JSON so the future GUI implementation can be diffed
byte-for-byte against BC's design-time structure WITHOUT screenshots.

Grammar faces (surveyed over all 211 forms):
  object Name: Class            property = scalar/string/ident/True/False
  [Prop = value]  set  [a, b]   -> list of idents
  inline list  (..)             -> list of scalars/strings
  collection  = <  item..end >  -> list of dicts (prop order preserved)
  binary value rendered as {N bytes} by the extractor
  strings use '' as the quote escape; multi-line continuation NOT seen.

Outputs:
  extracted/guibaseline/forms.json      {form: {cls,name,props,children}}
  extracted/guibaseline/actions.json    per-action catalog table
  extracted/guibaseline/index.json      counts + digests (sha256 per form)

Deterministic: keys sorted in JSON output; child/item order preserved as-is.
"""
import hashlib
import json
import os
import re
import sys

FORMS_DIRS = {
    "en": r"D:\Rea\extracted\forms",
    "zh": r"D:\Rea\extracted\_scratch\forms-zh",
}
OUT = r"D:\Rea\extracted\guibaseline"


class Tok:
    def __init__(self, lines):
        self.lines = [l.rstrip() for l in lines]
        self.i = 0

    def peek(self):
        return self.lines[self.i] if self.i < len(self.lines) else None

    def next(self):
        l = self.lines[self.i]
        self.i += 1
        return l


IDENT_RE = re.compile(r"^-?\d+$|^-?\d*\.\d+$|^-?\d+[eE][-+]?\d+$")


def parse_scalar(tokstr):
    t = tokstr.strip()
    if t in ("True",):
        return True
    if t in ("False",):
        return False
    if IDENT_RE.match(t):
        try:
            return int(t)
        except ValueError:
            return float(t)
    return t  # identifier/enum value kept as string


def parse_string_literal(s):
    """'abc''def' -> abc'def ; also handles trailing embedded text."""
    assert s.startswith("'") and s.endswith("'"), s[:40]
    return s[1:-1].replace("''", "'")


def parse_value(line):
    """Parse a value starting after '=' on `line`. Returns (value, next_line)."""
    v = line.strip()
    if v.startswith("("):  # inline list (possibly multi-line)
        items, buf = [], v
        while not buf.rstrip().endswith(")"):
            buf += " " + TOK.next().strip()
        inner = buf.strip()[1:-1]
        for part in split_top_commas(inner):
            part = part.strip()
            if not part:
                continue
            if part.startswith("'"):
                items.append(parse_string_literal(part))
            else:
                items.append(parse_scalar(part))
        return items, None
    if v.startswith("["):  # set [a, b]
        inner = v.strip()[1:-1]
        return [x.strip() for x in inner.split(",") if x.strip()], None
    if v.startswith("{"):  # binary {N bytes}
        return {"binary": v.strip()}, None
    if v.startswith("<"):  # collection: parse item/end blocks until '>'
        coll = []
        while True:
            l = TOK.next()
            if l is None:
                raise ValueError("unterminated collection")
            ls = l.strip()
            if ls == ">":
                break
            if ls.startswith("item"):
                props = {}
                while True:
                    l2 = TOK.next().strip()
                    if l2 == "end":
                        break
                    m = re.match(r"^([A-Za-z0-9_.]+) = (.*)$", l2)
                    if not m:
                        raise ValueError(f"collection prop line: {l2!r}")
                    val, nxt = parse_value_after_eq(m.group(1), m.group(2), l2)
                    props[m.group(1)] = val
                coll.append(props)
            else:
                raise ValueError(f"unexpected collection line: {ls!r}")
        return coll, None
    if v.startswith("'"):
        # possibly string continuing across lines with ' + or plain wrap: not seen
        return parse_string_literal(v), None
    return parse_scalar(v), None


def parse_value_after_eq(propname, rest, line):
    return parse_value(rest)


def split_top_commas(s):
    out, depth, in_str, cur = [], 0, False, ""
    i = 0
    while i < len(s):
        c = s[i]
        if in_str:
            cur += c
            if c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    cur += "'"
                    i += 1
                else:
                    in_str = False
        elif c == "'":
            in_str = True
            cur += c
        elif c in "([<":
            depth += 1
            cur += c
        elif c in ")]>":
            depth -= 1
            cur += c
        elif c == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    out.append(cur)
    return out


TOK = None


def parse_object_body(t):
    """Current line already consumed is 'object ...' — caller passes Tok at body start."""
    props = {}
    children = []
    while True:
        l = TOK.next()
        if l is None:
            raise ValueError("unexpected EOF in object")
        ls = l.strip()
        if ls == "end":
            return props, children
        m = re.match(r"^([A-Za-z0-9_.]+) = (.*)$", ls)
        if m:
            val, _ = parse_value(m.group(2))
            props[m.group(1)] = val
            continue
        m = re.match(r"^object ([A-Za-z0-9_]+): ([A-Za-z0-9_.]+)$", ls)
        if m:
            cprops, ckids = parse_object_body(TOK)
            children.append({"name": m.group(1), "cls": m.group(2),
                             "props": cprops, "children": ckids})
            continue
        raise ValueError(f"unparsed line: {ls!r}")


def parse_form(text):
    global TOK
    TOK = Tok(text.splitlines())
    first = TOK.next().strip()
    m = re.match(r"^object ([A-Za-z0-9_]+): ([A-Za-z0-9_.]+)$", first)
    if not m:
        raise ValueError(f"bad header: {first!r}")
    props, children = parse_object_body(TOK)
    if TOK.peek() is not None and TOK.peek().strip():
        raise ValueError(f"trailing content: {TOK.peek()!r}")
    return {"name": m.group(1), "cls": m.group(2), "props": props, "children": children}


def count_objects(node):
    n = 1
    for c in node["children"]:
        n += count_objects(c)
    return n


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "en"
    forms_dir = FORMS_DIRS[src]
    os.makedirs(OUT, exist_ok=True)
    forms = {}
    actions = {}
    errors = {}
    for fn in sorted(os.listdir(forms_dir)):
        if not fn.endswith(".dfm"):
            continue
        path = os.path.join(forms_dir, fn)
        text = open(path, encoding="utf-8").read()
        try:
            tree = parse_form(text)
        except Exception as e:
            errors[fn] = str(e)[:160]
            continue
        forms[fn[:-4]] = tree
        # action catalog extraction from *ACTIONS forms
        if fn.endswith("ACTIONS.dfm"):
            def walk(node, cat_form):
                for c in node["children"]:
                    if c["cls"] in ("TUiAction", "TUiActionMenuItem", "TUiCustomAction"):
                        p = c["props"]
                        sc = p.get("ShortCutStr") or None
                        # key = (form, action name): the same action NAME is
                        # redefined per view form (OpenAction = '&Open Session'
                        # in TBCACTIONS vs '&Open File...' in TFILEACTIONS) —
                        # dict-by-name silently dropped the view variants.
                        # caption source ladder (measured): Caption is the menu
                        # label; ShortCaption is the toolbar/short form used when
                        # Caption is absent (UndoAction); the remaining 80 actions
                        # (Fav*/Tog*/Go*/Exists*...) build their label at runtime
                        # from view state and carry NO text in the DFM at all.
                        cap = p.get("Caption")
                        cap_src = "Caption" if cap else (
                            "ShortCaption" if p.get("ShortCaption") else "runtime")
                        if cap is None:
                            cap = p.get("ShortCaption")
                        actions[f"{cat_form}.{c['name']}"] = {
                            "form": cat_form,
                            "cls": c["cls"],
                            "caption": cap,
                            "caption_source": cap_src,
                            "hint": p.get("Hint"),
                            "shortcut": sc,
                            "category": p.get("Category"),
                            "scope": p.get("Scope"),
                            "visible_when": {k: v for k, v in p.items()
                                             if k.startswith(("Visible", "DynVisible", "Checked"))},
                        }
                    walk(c, cat_form)
            walk(tree, fn[:-4])
    payload = {k: forms[k] for k in sorted(forms)}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with open(os.path.join(OUT, f"forms-{src}.json"), "w", encoding="utf-8") as f:
        f.write(blob)
    with open(os.path.join(OUT, f"actions-{src}.json"), "w", encoding="utf-8") as f:
        json.dump({k: actions[k] for k in sorted(actions)}, f, ensure_ascii=False,
                  sort_keys=True, indent=1)
    idx = {
        "source": forms_dir,
        "forms": len(forms),
        "form_objects_total": sum(count_objects(v) for v in forms.values()),
        "actions": len(actions),
        "errors": errors,
        "sha256_forms": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
    }
    with open(os.path.join(OUT, f"index-{src}.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: idx[k] for k in idx if k != "errors"}, indent=1))
    print("errors:", len(errors))
    for k, v in list(errors.items())[:10]:
        print("  ", k, "->", v)


if __name__ == "__main__":
    main()

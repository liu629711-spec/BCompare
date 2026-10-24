"""Teach the reference model the measured `version` extension mask (U9).

`product/dir/tools/make_cases.py` is the *reference model* the folder gate
compares against, so it must encode the same rules as the engine. It currently
compares a PE version for every file name, which U9 measured BC does **not** do.

Run from the repository root. Idempotent: refuses if already applied.
"""
import pathlib

p = pathlib.Path("product/dir/tools/make_cases.py")
text = p.read_text(encoding="utf-8")

if "VERSION_EXTENSIONS" in text:
    raise SystemExit("mask already present in the reference model")

# 1. The mask constant + predicate, placed next to the other module helpers.
helper_anchor = "def pe_file_version(path: pathlib.Path)"
assert text.count(helper_anchor) == 1, text.count(helper_anchor)

helper = '''#: Extensions for which BC reads a version resource, measured in U9
#: (`product/verify/probes/U9-FINDINGS.md`). BC returns `same` for every other
#: name even when the file is a real PE, so the name is an admission test and
#: the resource is only the value source.
VERSION_EXTENSIONS = ("exe", "dll", "ocx", "scr", "sys", "drv", "vxd", "386")


def version_applies_to(name: str) -> bool:
    """True when BC would read a version resource for a file with this name."""
    file = name.replace("\\\\", "/").rsplit("/", 1)[-1]
    if "." not in file:
        return False
    ext = file.rsplit(".", 1)[1]
    if not ext:
        return False
    return ext.lower() in VERSION_EXTENSIONS


'''

text = text.replace(helper_anchor, helper + helper_anchor)

# 2. Gate the reference model's version branch the same way.
old_branch = '''            elif c == "version":
                # u4c/u4f: directional FileVersion comparison. A side with no
                # version resource is older than a side with one; both empty
                # means equal. The direction is carried out through
                # `version_newer` because it is not a plain diff.
                if l.kind != "file" or r.kind != "file":
                    continue
                va = pe_file_version(l.path)
                vb = pe_file_version(r.path)'''

new_branch = '''            elif c == "version":
                # u4c/u4f: directional FileVersion comparison. A side with no
                # version resource is older than a side with one; both empty
                # means equal. The direction is carried out through
                # `version_newer` because it is not a plain diff.
                #
                # U9: the criterion only applies to the measured extension set.
                # A name outside it contributes nothing at all, so the row falls
                # through as equal even when the file is a real PE.
                if l.kind != "file" or r.kind != "file":
                    continue
                if not (version_applies_to(l.name)
                        and version_applies_to(r.name)):
                    continue
                va = pe_file_version(l.path)
                vb = pe_file_version(r.path)'''

assert text.count(old_branch) == 1, text.count(old_branch)
text = text.replace(old_branch, new_branch)

p.write_text(text, encoding="utf-8")
print("reference model updated; new size", len(text))

"""Add U9 mask rows to the `versioned` fixture tree (idempotent).

The rows exercise the measured extension gate in both directions:

* `masked.txt` / `masked.cpl` carry **real PEs** with different FileVersions but
  sit outside the mask, so BC reports `same` and so must the engine. These are the
  rows that would have caught the pre-U9 behaviour (it reported `ltnewer`).
* `included.vxd` / `included.386` are inside the mask but sit outside the
  "common executable extensions" intuition, so they guard the other direction.

Run from the repository root.
"""
import pathlib

p = pathlib.Path("product/dir/tools/make_fixtures.py")
text = p.read_text(encoding="utf-8")

if "included.vxd" in text:
    raise SystemExit("U9 mask rows already present")

old = '''            "padded.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)) + b"\\x00" * 4096, T0),
        }),
    }'''

new = '''            "padded.dll": file_node(_pe_blob((1, 0, 0, 0), (1, 0, 0, 0)) + b"\\x00" * 4096, T0),
        }),
    }
    # U9: the version criterion applies only to a measured extension set, so the
    # same PE content must be read under an admitted name and ignored under any
    # other. `masked.*` are real PEs whose difference must go unreported;
    # `included.*` are admitted names no intuition-based list would contain.
    for _tree, _ver in (("L", (9, 9, 9, 9)), ("R", (1, 0, 0, 0))):
        _side = trees["versioned"][_tree]["children"]
        for _name in ("masked.txt", "masked.cpl", "masked.efi", "masked.exe2",
                      "masked.zip", "masked"):
            _side[_name] = file_node(_pe_blob(_ver, _ver), T0)
        for _name in ("included.vxd", "included.386"):
            _side[_name] = file_node(_pe_blob(_ver, _ver), T0)
    trees["versioned"]["note"] += (
        "; masked.* are real PEs outside the measured extension gate and must be "
        "reported `same` (U9), included.vxd/.386 are admitted names"'''

assert text.count(old) == 1, text.count(old)
text = text.replace(old, new)
p.write_text(text, encoding="utf-8")
print("fixture rows added; new size", len(text))

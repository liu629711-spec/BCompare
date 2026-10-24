import io

p = r"D:\Rea\product\core\src\table.rs"
t = io.open(p, encoding="utf-8").read()

# 1) remove the misplaced fn block injected INSIDE the enum: it starts right
# after `pub enum TableLayout {` and ends at the `SideBySide,` variant.
head = "pub enum TableLayout {"
bad_start = t.find(head)
assert bad_start >= 0
bad_start += len(head)
bad_start += 1 if t[bad_start] == "\n" else 0
bad_end = t.find("SideBySide,", bad_start)
assert bad_start < bad_end
misplaced = t[bad_start:bad_end]
assert "fn frame_is_crlf_no_gap_and_dashed_stamp" in misplaced, repr(misplaced[:80])
t = t[:bad_start] + "\n    " + t[bad_end:]

# 2) replace the trailing frame test (raw-newline literals) with an escaped one.
fn_marker = "    fn frame_is_crlf_no_gap_and_dashed_stamp() {"
s = t.find(fn_marker)
assert s > 0
e = t.rfind("}")  # final tests-mod close
old_tail = t[s:e]
assert "assert!(text.starts_with(" in old_tail
new_fn = (
    "    fn frame_is_crlf_no_gap_and_dashed_stamp() {\n"
    "        let stamp = Stamp::from_parts(2026, 10, 18, 0, 36, 32);\n"
    "        let text = render_report(\n"
    "            TableLayout::Summary,\n"
    '            "a,1\\n",\n'
    '            "a,1\\n",\n'
    '            "L.csv",\n'
    '            "R.csv",\n'
    "            &stamp,\n"
    "        )\n"
    "        .unwrap();\n"
    '        let want = "Table Compare\\r\\nProduced: 2026-10-18 0:36:32\\r\\n\\r\\n"\n'
    '            "Left file: L.csv\\r\\nRight file: R.csv\\r\\n";\n'
    '        assert!(text.starts_with(want), "got {text:?}");\n'
    '        assert!(!text.contains("Mode:")); // summary has no Mode line\n'
    "    }\n"
)
t = t[:s] + new_fn + t[e:]
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("repaired")

"""Large-scale anchored behavior capture against Beyond Compare (the oracle).

Extends bc-anchors.py (8 cases) to a suite covering the testable anchors of all
14 Ss spec units: line endings, encodings, charset/importance rules, alignment
patterns, XML escaping, report metadata, and option variations.

For every case it:
  * writes the exact input bytes to verify/golden/<name>-L.bin / -R.bin
  * runs BComp.com with text-report layout:xml options:display-all
  * stores BC's raw report as verify/golden/<name>.xml
  * records statuses + metadata in verify/golden/manifest.json

The golden files are the regression target for the Rust clone: a candidate
implementation must reproduce the same status sequence (and, where stated, the
same escaping/structure) for the same input bytes.
"""
import importlib.util
import json
import pathlib

TOOLS = pathlib.Path(r"D:\Rea\tools")
GOLDEN = pathlib.Path(r"D:\Rea\verify\golden")

_spec = importlib.util.spec_from_file_location("bc_oracle", TOOLS / "bc-oracle.py")
bc_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc_oracle)


def b(s: str) -> bytes:
    return s.encode("utf-8")


BOM8 = b"\xef\xbb\xbf"
BOM16LE = b"\xff\xfe"
BOM16BE = b"\xfe\xff"


def u16le(s: str) -> bytes:
    return BOM16LE + s.encode("utf-16-le")


def u16be(s: str) -> bytes:
    return BOM16BE + s.encode("utf-16-be")


# (name, unit, note, left_bytes, right_bytes, ext)
CASES: list[tuple[str, str, str, bytes, bytes, str]] = [
    # ---- SsLineParse: line endings -------------------------------------
    ("le-crlf-vs-lf", "SsLineParse", "CRLF vs LF must compare equal",
     b("a\r\nb\r\n"), b("a\nb\n"), "txt"),
    ("le-crlf-vs-cr", "SsLineParse", "CRLF vs CR",
     b("a\r\nb\r\n"), b("a\rb\r"), "txt"),
    ("le-crcrlf", "SsLineParse", "CRCRLF vs CRLF",
     b("a\r\r\nb\r\r\n"), b("a\r\nb\r\n"), "txt"),
    ("le-mixed", "SsLineParse", "mixed endings in one file",
     b("a\r\nb\nc\rd"), b("a\nb\nc\nd"), "txt"),
    ("le-no-final-nl", "SsLineParse", "missing final newline",
     b("a\nb"), b("a\nb\n"), "txt"),
    # ---- SsLineParse: encodings ----------------------------------------
    ("enc-utf8-bom", "SsLineParse", "UTF-8 BOM vs no BOM",
     BOM8 + b("a\nb\n"), b("a\nb\n"), "txt"),
    ("enc-utf16le", "SsLineParse", "UTF-16LE BOM vs UTF-8",
     u16le("a\nb\n"), b("a\nb\n"), "txt"),
    ("enc-utf16be", "SsLineParse", "UTF-16BE BOM vs UTF-8",
     u16be("a\nb\n"), b("a\nb\n"), "txt"),
    ("enc-latin1", "SsLineParse", "Latin-1 bytes vs UTF-8",
     "caf\xe9\n".encode("latin-1"), "caf\xe9\n".encode("utf-8"), "txt"),
    ("enc-ctrlz-eof", "SsLineParse", "Ctrl-Z (0x1a) mid-file",
     b("abc\x1adef\n"), b("abc\n"), "txt"),
    ("enc-nul-binary", "SsLineParse", "NUL bytes (binary-ish)",
     b("a\x00b\nc\n"), b("a\x00c\nc\n"), "txt"),
    # ---- SsClasses: whitespace / case / syntax elements ----------------
    ("ws-trailing", "SsClasses", "trailing spaces (txt)",
     b("a \nb\n"), b("a\nb\n"), "txt"),
    ("ws-leading", "SsClasses", "leading spaces (txt)",
     b("  a\nb\n"), b("a\nb\n"), "txt"),
    ("ws-tab-vs-space", "SsClasses", "tab vs spaces",
     b("a\tb\n"), b("a b\n"), "txt"),
    ("ws-internal", "SsClasses", "internal spacing",
     b("void main( )\n"), b("void main()\n"), "txt"),
    ("case-txt", "SsClasses", "case change in .txt",
     b("alpha\n"), b("ALPHA\n"), "txt"),
    ("case-c-ident", "SsClasses", "identifier case change in .c",
     b("int Abc = 1;\n"), b("int abc = 1;\n"), "c"),
    ("case-c-string", "SsClasses", "string literal case change in .c",
     b('printf("Hello");\n'), b('printf("hello");\n'), "c"),
    ("num-c", "SsClasses", "number change in .c",
     b("int x = 10;\n"), b("int x = 11;\n"), "c"),
    ("op-c", "SsClasses", "operator change in .c",
     b("x = a + b;\n"), b("x = a - b;\n"), "c"),
    ("dir-c", "SsClasses", "directive change in .c",
     b("#include <stdio.h>\n"), b("#include <stdlib.h>\n"), "c"),
    ("comment-c", "SsClasses", "comment content change in .c",
     b("// old note\nx;\n"), b("// new note\nx;\n"), "c"),
    ("kw-c", "SsClasses", "keyword change in .c",
     b("int a;\n"), b("long a;\n"), "c"),
    ("txt-syntax-chars", "SsClasses", "syntax-looking chars in .txt",
     b("int x = 10; // c\n"), b("long x = 20; // c\n"), "txt"),
    # ---- SsLineList / diff: alignment ----------------------------------
    ("al-insert", "SsLineList", "pure insertion",
     b("a\nc\n"), b("a\nb\nc\n"), "txt"),
    ("al-delete", "SsLineList", "pure deletion",
     b("a\nb\nc\n"), b("a\nc\n"), "txt"),
    ("al-replace-block", "SsLineList", "block replace",
     b("h1\nx\ny\nz\nh2\n"), b("h1\np\nq\nr\nh2\n"), "txt"),
    ("al-move-down", "SsLineList", "moved line",
     b("a\nb\nc\nd\n"), b("a\nc\nd\nb\n"), "txt"),
    ("al-swap-blocks", "SsLineList", "swapped blocks",
     b("a\nb\nc\nd\n"), b("c\nd\na\nb\n"), "txt"),
    ("al-duplicates", "SsLineList", "duplicate lines (ambiguous)",
     b("x\nx\nx\n"), b("x\nx\n"), "txt"),
    ("al-identical", "SsLineList", "identical files",
     b("x\ny\n"), b("x\ny\n"), "txt"),
    ("al-empty-left", "SsLineList", "empty vs content",
     b(""), b("only\n"), "txt"),
    ("al-empty-both", "SsLineList", "both empty",
     b(""), b(""), "txt"),
    ("al-similar-then-diff", "SsLineList", "similar + different mix",
     b("same\nbeta\ndiff1\n"), b("same\nBETA\ndiff2\n"), "txt"),
    # ---- SsXML / SsPersistent: report structure & escaping -------------
    ("xml-ctrl-chars", "SsXML", "control chars 0x01 0x07 0x1a 0x7f",
     b("a\x01b\nc\x07d\n"), b("a\x01b\nc\x1ad\n"), "txt"),
    ("xml-entities", "SsXML", "& < > \" ' in content",
     b("a & b < c > d\n"), b("a & b < c > e\n"), "txt"),
    ("xml-quotes", "SsXML", "quotes in content",
     b('say "hi" & <ok>\n'), b("say 'hi' & <ok>\n"), "txt"),
    ("xml-unicode", "SsXML", "CJK + emoji",
     "中文行\nemoji \U0001f600\n".encode("utf-8"), "中文行2\nemoji \U0001f600\n".encode("utf-8"), "txt"),
    ("xml-tabs", "SsXML", "tabs preserved in output",
     b("col1\tcol2\n"), b("col1\tcol3\n"), "txt"),
    ("xml-long-line", "SsXML", "long line (no wrap)",
     b(("x" * 500) + "\n"), b(("x" * 500) + "y\n"), "txt"),
]

# Option-variation cases run on one fixed mixed pair.
OPT_PAIR_L = b("same line\ncase diff\nCase Diff\nws diff \nreal diff 1\nreal diff 2\n")
OPT_PAIR_R = b("same line\ncase diff\nCASE DIFF\nws diff\nreal diff 9\nreal diff 2\n")
OPTIONS = ["display-all", "display-mismatches", "display-context",
           "display-matches", "ignore-unimportant"]


def parse_statuses(xml: str) -> list[str]:
    out = []
    for line in xml.splitlines():
        s = line.strip()
        if s.startswith("<linecomp"):
            out.append(s.split('status="')[1].split('"')[0])
    return out


def run_all() -> int:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    failures = 0

    for name, unit, note, left, right, ext in CASES:
        lp = GOLDEN / f"{name}-L.{ext}"
        rp = GOLDEN / f"{name}-R.{ext}"
        out = GOLDEN / f"{name}.xml"
        lp.write_bytes(left)
        rp.write_bytes(right)
        r = bc_oracle.run_report(lp, rp, out, layout="xml", options="display-all")
        statuses = parse_statuses(r["output"]) if r["exit_code"] == 0 else []
        manifest[name] = {
            "unit": unit, "note": note, "exit_code": r["exit_code"],
            "statuses": statuses, "seconds": r["seconds"],
            "left": str(lp), "right": str(rp), "report": str(out),
        }
        if r["exit_code"] != 0:
            failures += 1
        mark = "ok  " if r["exit_code"] == 0 else "FAIL"
        print(f"  {mark} {name:<22} {unit:<12} {statuses}")

    # Option matrix on one pair.
    lp = GOLDEN / "opt-pair-L.txt"
    rp = GOLDEN / "opt-pair-R.txt"
    lp.write_bytes(OPT_PAIR_L)
    rp.write_bytes(OPT_PAIR_R)
    for opt in OPTIONS:
        out = GOLDEN / f"opt-{opt}.xml"
        r = bc_oracle.run_report(lp, rp, out, layout="xml", options=opt)
        statuses = parse_statuses(r["output"]) if r["exit_code"] == 0 else []
        manifest[f"opt-{opt}"] = {
            "unit": "SsLineList", "note": f"options:{opt} on mixed pair",
            "exit_code": r["exit_code"], "statuses": statuses,
            "left": str(lp), "right": str(rp), "report": str(out),
        }
        if r["exit_code"] != 0:
            failures += 1
        print(f"  {'ok  ' if r['exit_code'] == 0 else 'FAIL'} opt-{opt:<17} SsLineList   {statuses}")

    (GOLDEN / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    total = len(manifest)
    print()
    print(f"{total - failures}/{total} anchors captured -> {GOLDEN}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run_all())

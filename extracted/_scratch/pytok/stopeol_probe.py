"""Offline: run the current product binary on StopEOL-shaped cases to show the
gap before changing importance.rs. Fixtures written to this scratch dir only.
"""
import pathlib, re, subprocess
S = pathlib.Path(r'D:\Rea\extracted\_scratch\pytok')
EXE = r'D:\Rea\product\cli\target\release\reacmp.exe'
ROW_RE = re.compile(r'<linecomp status="([a-z]+)"')

def run(name, left, right, ext):
    lp = S / f'{name}-L.{ext}'; rp = S / f'{name}-R.{ext}'; op = S / f'{name}.xml'
    lp.write_text('\n'.join(left) + '\n', encoding='utf-8')
    rp.write_text('\n'.join(right) + '\n', encoding='utf-8')
    subprocess.run([EXE, str(lp), str(rp), str(op)], capture_output=True, check=True)
    return ROW_RE.findall(op.read_text(encoding='utf-8-sig'))

cases = [
    # py: whitespace inside an unterminated quote: BC spec says the String
    # element runs to EOL (StopEOL=True) -> content is important.
    # Oracle-shape expectation: different (a b vs a  b inside one string span).
    ('py-unterm-ws', ["x = 'a b"], ["x = 'a  b"], 'py'),
    # py: # after an unterminated quote is string content, not a comment.
    # Expectation: different ('a # b' vs 'a # c' inside one string span).
    ('py-unterm-hash', ["x = 'a # b"], ["x = 'a # c"], 'py'),
    # c: unterminated quote must not leak /* into block-comment state.
    # Expectation: line1 different (string content), line2 same, line3 same.
    ('c-unterm-leak', ['a = "x /*', 'int y;', 'int z;'],
                      ['a = "x /*', 'int Y;', 'int z;'], 'c'),
]
for name, l, r, ext in cases:
    print(name, run(name, l, r, ext))

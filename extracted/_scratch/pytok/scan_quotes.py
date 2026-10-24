import pathlib
fx = pathlib.Path(r'D:\Rea\product\verify\runs\m54-fuzz-20261014T170917Z\fixtures')
BS = chr(92)

def scan_line_for_odd(line):
    for q in ('"', "'"):
        n = 0
        i = 0
        while i < len(line):
            if line[i] == BS:
                i += 2
                continue
            if line[i] == q:
                n += 1
            i += 1
        trip = line.count(q * 3)
        if n % 2 == 1 and trip == 0:
            return q
    return None

hits = []
for p in sorted(fx.glob('*.py')) + sorted(fx.glob('*.c')):
    for k, ln in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        q = scan_line_for_odd(ln)
        if q:
            hits.append((p.name, k, q, ln))
print("odd-quote lines:", len(hits))
for h in hits[:40]:
    print(h)

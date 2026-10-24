#!/usr/bin/env python3
# Instrumented: how many unique pairs does the big test's interval hold?
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(r"D:\Rea") / "product" / "verify"))
sys.path.insert(0, str(pathlib.Path(r"D:\Rea") / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from handler_eval import unique_pairs
LINES=100_000
left=[f"line {i}" for i in range(LINES)]
right=[]
for i in range(LINES):
    if i==10: right.append("line TEN CHANGED")
    elif i==LINES//2: right += ["inserted a","inserted b","inserted c","inserted d","inserted e", f"line {i}"]
    elif i in (LINES-5, LINES-4): pass
    else: right.append(f"line {i}")
print("len L,R:", len(left), len(right))
# simulate scan: first mismatch at i=10
ids_l=left; ids_r=right
# interval after scan break at 10:
ls=list(range(10,len(left))); rs=list(range(10,len(right)))
from collections import Counter
cl=Counter(ls and [ids_l[i] for i in ls] or [])
up=unique_pairs(ls, rs, ids_l, ids_r)
print("interval size:", len(ls), len(rs), "unique pairs:", len(up))

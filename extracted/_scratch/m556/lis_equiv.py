# proof sketch: tails is strictly increasing -> linear first-ge scan ==
# partition_point. Verify on randomized sequences vs current product logic.
import random
def lin(seq):
    tails=[]
    for r in seq:
        k=0
        while k < len(tails) and tails[k] < r: k+=1
        if k==len(tails): tails.append(r)
        else: tails[k]=r
    return tails
def bin_(seq):
    tails=[]
    import bisect
    for r in seq:
        k=bisect.bisect_left(tails, r)
        if k==len(tails): tails.append(r)
        else: tails[k]=r
    return tails
random.seed(7)
for t in range(3000):
    seq=[random.randrange(-5, 200) for _ in range(random.randrange(1, 60))]
    assert lin(seq)==bin_(seq), seq
print("equivalent on", t+1, "random trials")

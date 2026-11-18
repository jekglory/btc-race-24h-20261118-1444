"""Fine grid around the dip2 candidate + neighbour sensitivity (research)."""
import gzip
import json
import sys

sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/research")
from search import load, sim, NEW, OLD

new_c = load(NEW)
old_c = load(OLD)
new_o = [int(json.loads(l)["o"]) / 1e5 for l in gzip.open(NEW, "rt")]
old_o = [int(json.loads(l)["o"]) / 1e5 for l in gzip.open(OLD, "rt")]

print("fine grid dip2, worst-window first:")
rows = []
for n in (45, 60, 75, 90, 120):
    for d in (60, 70, 80, 90, 100):
        for trail in (40, 60, 80, 100, 150):
            pn, tr, dd = sim(new_c, new_o, "dip2", n, d, trail, 250)
            po, tro, ddo = sim(old_c, old_o, "dip2", n, d, trail, 250)
            rows.append((min(pn, po), pn, po, n, d, trail, tr, tro, dd, ddo))
rows.sort(reverse=True)
for r in rows[:20]:
    print("worst $%6.2f new $%6.2f (tr %d dd %.1f%%) old $%6.2f (tr %d dd %.1f%%) n=%d d=%d trail=%d"
          % (r[0], r[1], r[6], r[8], r[2], r[7], r[9], r[3], r[4], r[5]))

print("\nneighbourhood of the pick n=60 d=80 trail=80:")
for n in (50, 60, 70):
    for d in (70, 80, 90):
        for trail in (60, 80, 100):
            pn, tr, dd = sim(new_c, new_o, "dip2", n, d, trail, 250)
            po, tro, ddo = sim(old_c, old_o, "dip2", n, d, trail, 250)
            print("n=%d d=%d trail=%d -> new $%6.2f old $%6.2f tr %d/%d"
                  % (n, d, trail, pn, po, tr, tro))

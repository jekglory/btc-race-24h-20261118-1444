"""Fine grid around the target-family pick (research)."""
import sys

sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/research")
from search import load, NEW, OLD
from search3 import sim_target

new_b = load(NEW)
old_b = load(OLD)

print("target family, n=60, stop=250, trail=200, half size:")
for d in (80, 90, 100, 110, 120):
    for target in (100, 120, 140, 160, 180, 200):
        pn, tr, dd = sim_target(new_b, 60, d, target, 200, 250)
        po, tro, ddo = sim_target(old_b, 60, d, target, 200, 250)
        print("d=%3d target=%3d -> new $%6.2f (tr %d) old $%6.2f (tr %d) worst $%6.2f"
              % (d, target, pn, tr, po, tro, min(pn, po)))

print("\ntrail sensitivity at d=100 target=160:")
for trail in (80, 120, 160, 200, 300):
    pn, tr, dd = sim_target(new_b, 60, 100, 160, trail, 250)
    po, tro, ddo = sim_target(old_b, 60, 100, 160, trail, 250)
    print("trail=%3d -> new $%6.2f (tr %d) old $%6.2f (tr %d)"
          % (trail, pn, tr, po, tro))

print("\nn sensitivity at d=100 target=160 trail=200:")
for n in (30, 45, 60, 90, 120):
    pn, tr, dd = sim_target(new_b, n, 100, 160, 200, 250)
    po, tro, ddo = sim_target(old_b, n, 100, 160, 200, 250)
    print("n=%3d -> new $%6.2f (tr %d) old $%6.2f (tr %d)"
          % (n, pn, tr, po, tro))

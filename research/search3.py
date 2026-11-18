"""Ladder + fixed-target search (research tooling, NOT shipped).

Families (exact integer fills, same engine as search.py):
  ladder:  60-bar SMA reference. Tranche 1 buys half the cash when two
           closes sit D1 bps below the SMA; tranche 2 buys the rest when
           two closes sit D2 bps below it. Sell ALL on recovery to the
           SMA, or trailing stop T off peak value, or hard stop S.
  target:  dip2 entry (two closes D bps below the N-bar SMA), sell when
           the position value reaches T bps above cost, or trailing
           stop, or hard stop (no SMA-recovery exit).
"""
import gzip
import json
import sys

sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/research")
from run_bot import buy_fill, sell_fill, value_of, START_CASH
from search import load, NEW, OLD

BPS = 10000


def sim_ladder(bars, n, d1, d2, trail, stop):
    cash, qty, cost = START_CASH, 0, 0
    peak = 0
    trades = 0
    peak_eq = START_CASH
    max_dd = 0.0
    pending = None  # ("buy", frac_num, frac_den) or ("sell",)
    closes = [int(b["c"]) for b in bars]
    tranche = 0
    for k in range(len(bars)):
        if pending is not None and k > 0:
            open_px = int(bars[k]["o"])
            depth = int(bars[k]["o_depth"][0])
            if pending[0] == "buy" and cash >= 1000000:
                notional = cash * pending[1] // pending[2]
                f = buy_fill(notional, open_px, depth)
                if f["price"] * BPS <= closes[k - 1] * (BPS + 100):
                    cash -= notional
                    qty += f["qty"]
                    cost += notional
                    peak = max(peak, f["spend"])
                    trades += 1
                    tranche += 1
            elif pending[0] == "sell" and qty > 0:
                f = sell_fill(qty, open_px, depth)
                if f["price"] * BPS >= closes[k - 1] * (BPS - 100):
                    cash += f["proceeds"]
                    cost = 0
                    qty = 0
                    trades += 1
                    tranche = 0
            pending = None
        c = closes[k]
        eq = cash + (value_of(qty, c) if qty else 0)
        peak_eq = max(peak_eq, eq)
        max_dd = max(max_dd, (peak_eq - eq) / START_CASH)
        if k < n - 1 or k == len(bars) - 1:
            continue
        total = sum(closes[k - n + 1:k + 1])
        if qty > 0:
            val = value_of(qty, c)
            peak = max(peak, val)
            if val * BPS <= cost * (BPS - stop):
                pending = ("sell",)
            elif val * BPS <= peak * (BPS - trail):
                pending = ("sell",)
            elif c * n >= total:
                pending = ("sell",)
            elif tranche == 1 and closes[k - 1] * n * BPS <= total * (BPS - d2) \
                    and c * n * BPS <= total * (BPS - d2):
                pending = ("buy", 1, 1)
        else:
            if closes[k - 1] * n * BPS <= total * (BPS - d1) \
                    and c * n * BPS <= total * (BPS - d1):
                pending = ("buy", 1, 2)
    if qty > 0:
        last = bars[-1]
        f = sell_fill(qty, int(last["c"]), int(last["c_depth"][0]))
        cash += f["proceeds"]
        trades += 1
    return (cash - START_CASH) / 1e6, trades, max_dd * 100


def sim_target(bars, n, d, target, trail, stop):
    cash, qty, cost = START_CASH, 0, 0
    peak = 0
    trades = 0
    peak_eq = START_CASH
    max_dd = 0.0
    pending = None
    closes = [int(b["c"]) for b in bars]
    for k in range(len(bars)):
        if pending is not None and k > 0:
            open_px = int(bars[k]["o"])
            depth = int(bars[k]["o_depth"][0])
            if pending == "buy" and cash >= 1000000:
                notional = cash // 2
                f = buy_fill(notional, open_px, depth)
                if f["price"] * BPS <= closes[k - 1] * (BPS + 100):
                    cash -= notional
                    qty += f["qty"]
                    cost += notional
                    peak = f["spend"]
                    trades += 1
            elif pending == "sell" and qty > 0:
                f = sell_fill(qty, open_px, depth)
                if f["price"] * BPS >= closes[k - 1] * (BPS - 100):
                    cash += f["proceeds"]
                    cost = 0
                    qty = 0
                    trades += 1
            pending = None
        c = closes[k]
        eq = cash + (value_of(qty, c) if qty else 0)
        peak_eq = max(peak_eq, eq)
        max_dd = max(max_dd, (peak_eq - eq) / START_CASH)
        if k < n - 1 or k == len(bars) - 1:
            continue
        total = sum(closes[k - n + 1:k + 1])
        if qty > 0:
            val = value_of(qty, c)
            peak = max(peak, val)
            if val * BPS <= cost * (BPS - stop):
                pending = "sell"
            elif val * BPS <= peak * (BPS - trail):
                pending = "sell"
            elif val * BPS >= cost * (BPS + target):
                pending = "sell"
        else:
            if closes[k - 1] * n * BPS <= total * (BPS - d) \
                    and c * n * BPS <= total * (BPS - d):
                pending = "buy"
    if qty > 0:
        last = bars[-1]
        f = sell_fill(qty, int(last["c"]), int(last["c_depth"][0]))
        cash += f["proceeds"]
        trades += 1
    return (cash - START_CASH) / 1e6, trades, max_dd * 100


def main():
    new_b = load(NEW)
    old_b = load(OLD)
    print("=== ladder (n=60) ===")
    rows = []
    for d1 in (70, 80, 90, 100):
        for d2 in (120, 150, 180, 220):
            for trail in (60, 80, 120, 200):
                for stop in (250, 400):
                    pn, tr, dd = sim_ladder(new_b, 60, d1, d2, trail, stop)
                    po, tro, ddo = sim_ladder(old_b, 60, d1, d2, trail, stop)
                    rows.append((min(pn, po), pn, po, d1, d2, trail, stop, tr, tro, dd, ddo))
    rows.sort(reverse=True)
    for r in rows[:12]:
        print("worst $%6.2f new $%6.2f (tr %d dd %.1f%%) old $%6.2f (tr %d dd %.1f%%) d1=%d d2=%d trail=%d stop=%d"
              % (r[0], r[1], r[7], r[9], r[2], r[8], r[10], r[3], r[4], r[5], r[6]))
    print("=== target (half size, n=60) ===")
    rows = []
    for d in (70, 80, 90, 100, 120):
        for target in (40, 60, 80, 120, 160):
            for trail in (60, 80, 120, 200):
                for stop in (250, 400):
                    pn, tr, dd = sim_target(new_b, 60, d, target, trail, stop)
                    po, tro, ddo = sim_target(old_b, 60, d, target, trail, stop)
                    rows.append((min(pn, po), pn, po, d, target, trail, stop, tr, tro, dd, ddo))
    rows.sort(reverse=True)
    for r in rows[:12]:
        print("worst $%6.2f new $%6.2f (tr %d dd %.1f%%) old $%6.2f (tr %d dd %.1f%%) d=%d target=%d trail=%d stop=%d"
              % (r[0], r[1], r[7], r[9], r[2], r[8], r[10], r[3], r[4], r[5], r[6]))


if __name__ == "__main__":
    main()

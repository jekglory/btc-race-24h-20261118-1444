"""Strategy search for btc-race-24h-20261118-1444 (research tooling, NOT shipped).

EXACT integer simulator: fills use the kit harness's own pool model
(run_bot.py buy_fill/sell_fill, copied from sim/bars/engine.ts), so
search numbers must match the protocol driver exactly. Decisions are
made at a bar's close and fill at the NEXT bar's open; a position still
held at the end flattens at the last close. Long only, $1,000 start,
all-in/all-out. All integer math, price_scale 5.

The bot trades from the 60th bar (index 59): len(closes) >= WINDOW.

Families:
  snapback: buy when close is D bps below the N-bar SMA of closes;
            sell when close recovers to the SMA, or trailing stop T,
            or hard stop S below cost.
  breakout: buy when close breaks above the max close of the last N bars;
            sell on trailing stop T, hard stop S, or close back below the
            N-bar SMA.
  dip2:     buy when close AND the previous close are both D bps below
            the N-bar SMA, sell on recovery to SMA / trail / stop.
"""
import gzip
import json
import sys

sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/research")
from run_bot import buy_fill, sell_fill, value_of, START_CASH

NEW = "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/kit/btc-race-24h-20261118-1444-kit/dataset/bars/CBBTC.ndjson.gz"
OLD = "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603-kit/dataset/bars/CBBTC.ndjson.gz"
BPS = 10000


def load(path):
    bars = [json.loads(l) for l in gzip.open(path, "rt")]
    for b in bars:
        b["symbol"] = "CBBTC"
    return bars


def sim(bars, family, n, d, trail, stop, size_frac_num=1, size_frac_den=1):
    cash, qty, cost = START_CASH, 0, 0
    peak = 0
    trades = 0
    peak_eq = START_CASH
    max_dd = 0.0
    pending = None  # ("buy",) or ("sell",)
    closes = [int(b["c"]) for b in bars]
    for k in range(len(bars)):
        if pending is not None and k > 0:
            open_px = int(bars[k]["o"])
            depth = int(bars[k]["o_depth"][0])
            if pending == "buy" and cash >= 1000000:
                notional = cash * size_frac_num // size_frac_den
                f = buy_fill(notional, open_px, depth)
                # max_slippage vs the previous close
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
            elif family in ("snapback", "dip2") and c * n >= total:
                pending = "sell"
            elif family == "breakout" and c * n < total:
                pending = "sell"
        else:
            if family == "snapback":
                if c * n * BPS <= total * (BPS - d):
                    pending = "buy"
            elif family == "dip2":
                if (c * n * BPS <= total * (BPS - d)
                        and closes[k - 1] * n * BPS <= total * (BPS - d)):
                    pending = "buy"
            elif family == "breakout":
                if c >= max(closes[max(0, k - n):k]):
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
    results = []
    for family in ("snapback", "dip2", "breakout"):
        for n in (30, 45, 60, 90, 120):
            for d in (40, 50, 60, 70, 80, 90, 100, 120):
                for trail in (40, 60, 80, 120, 200):
                    for stop in (150, 250, 400):
                        for snum, sden in ((1, 1), (1, 2), (1, 4)):
                            pn, tr, dd = sim(new_b, family, n, d, trail, stop, snum, sden)
                            po, tro, ddo = sim(old_b, family, n, d, trail, stop, snum, sden)
                            results.append((min(pn, po), pn, po, family, n, d, trail, stop, snum, sden, tr, tro, dd, ddo))
    results.sort(reverse=True)
    print("top 25 by worst-window PnL (exact integer fills):")
    for r in results[:25]:
        print("worst $%6.2f  new $%6.2f (tr %d dd %.1f%%)  old $%6.2f (tr %d dd %.1f%%)  %s n=%d d=%d trail=%d stop=%d size=%d/%d"
              % (r[0], r[1], r[10], r[12], r[2], r[11], r[13], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
    print("\ntop 10 by NEW window only:")
    by_new = sorted(results, key=lambda r: r[1], reverse=True)
    for r in by_new[:10]:
        print("new $%6.2f  old $%6.2f  %s n=%d d=%d trail=%d stop=%d size=%d/%d tr=%d/%d"
              % (r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]))


if __name__ == "__main__":
    main()

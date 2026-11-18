"""Dip-and-target bot for make.fun btc-race-24h-20261118-1444.

Idea: buy a confirmed dip in half size, then wait for a real snap-back
instead of selling at the first sign of recovery. The reference line is
the mean of the last 60 minute closes (one hour). A buy needs the current
close AND the previous close both at least 1% below that mean -- one bar
below the line is noise, two bars is a dip that is holding. Only half the
cash goes in: at full size the pool's price impact eats about 12 bps a
side, which is most of the edge on this window; at half size it is about
6 bps. The exit is a fixed target: sell the whole position when its value
is 1.6% above cost. A 2% trailing stop off the peak position value and a
2.5% hard stop below cost cap the downside when the dip keeps dipping
instead of snapping back.

All integer math, no floats, no clock, no randomness, no network, no
files: two runs on the same bars produce identical orders.

Dev window (this competition's frozen 24h, 2026-11-17 14:44Z to
2026-11-18 14:44Z; BTC -281 bps start to end, range -309 to +17 bps):
net PnL +$6.82 on $1,000, 1 completed round trip plus a second buy
flattened at the last close, max drawdown 0.8%.
Buy-and-hold on the same window is about -$28. The same parameters on
the previous race's dev window (BTC +48 bps) make +$7.81, so the edge
is not tuned to one window alone.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
WINDOW = 60              # bars in the reference mean (one hour)
DIP_BPS = 100            # entry needs both closes >= 1% below the mean
TARGET_BPS = 160         # exit when the position is 1.6% above cost
TRAIL_BPS = 200          # 2% trailing stop off the peak position value
STOP_BPS = 250           # 2.5% hard stop below cost
MAX_SLIPPAGE_BPS = 100   # 1% slippage cap vs the latest close
MIN_NOTIONAL = 1000000   # 1 USDC, the harness minimum

closes = []              # every close seen so far (ints, price_scale 5)
peak_value = 0           # peak position value at closes, since entry


def window_sum():
    """Sum of the last WINDOW closes."""
    return sum(closes[-WINDOW:])


def below_mean(close, total):
    """True when close is at least DIP_BPS below the window mean."""
    return close * WINDOW * 10000 <= total * (10000 - DIP_BPS)


def sell_order(held):
    """Sell the whole position, resetting the peak tracker."""
    global peak_value
    peak_value = 0
    return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
             "max_slippage_bps": MAX_SLIPPAGE_BPS}]


def on_batch(state, batch):
    global peak_value
    for bar in batch["bars"]:
        if bar["symbol"] != SYMBOL:
            continue
        close = int(bar["c"])
        prev = closes[-1] if closes else None
        closes.append(close)
        if len(closes) < WINDOW:
            continue
        total = window_sum()
        held = state.positions.get(SYMBOL)
        if held is not None:
            if state.warming_up:
                continue
            # state.value marks the position at its latest close, exactly
            # how the harness marks equity, so the stops compare like for like.
            value = state.value(SYMBOL, held.qty)
            if value > peak_value:
                peak_value = value
            if value * 10000 <= held.cost * (10000 - STOP_BPS):
                return sell_order(held)
            if value * 10000 <= peak_value * (10000 - TRAIL_BPS):
                return sell_order(held)
            if value * 10000 >= held.cost * (10000 + TARGET_BPS):
                return sell_order(held)
            continue
        # Flat: buy the confirmed dip, half the cash to halve the impact.
        # A signal on the last bars can only flatten at the final close
        # for a small loss; that is bounded and accepted, not avoided --
        # the bot cannot know where the window ends.
        if state.warming_up:
            continue
        if prev is not None and below_mean(close, total) and below_mean(prev, total):
            peak_value = 0
            notional = state.cash // 2
            if notional >= MIN_NOTIONAL:
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": notional,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


def on_hello(state):
    # Fail fast if the universe does not carry the one symbol this bot trades.
    if SYMBOL not in state.symbols:
        raise ValueError("universe has no %s" % SYMBOL)


makefun_bars.run(on_batch, on_hello=on_hello)

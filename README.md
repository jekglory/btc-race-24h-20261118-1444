# btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/jekglory/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/jekglory/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A pure-stdlib Python bot that trades cbBTC/USDC minute by minute in make.fun's
bars-replay harness. It starts with $1,000 of paper money, long only.

## Strategy

- Reference line = mean of the last 60 minute closes (one hour).
- **Entry** (flat only): the current close AND the previous close are both at
  least 1% below the mean — a confirmed dip, not one noisy bar. Buys with
  half the cash: at full size the pool's price impact eats about 12 bps a
  side, most of the edge on this window; at half size it is about 6 bps.
- **Exit** (holding): sell the whole position when its value reaches 1.6%
  above cost. A 2% trailing stop off the peak position value and a 2.5% hard
  stop below cost cap the downside when the dip keeps dipping instead of
  snapping back.
- One position at most, max slippage 100 bps. All integer math — no floats,
  no clock, no randomness, no network — so two runs on the same data produce
  identical orders.

## Dev window result

On the kit's frozen 24h dev window (BTC -281 bps start to end): net PnL
**+$6.82** on $1,000, 1 completed round trip plus a second buy flattened at
the last close, max drawdown 0.75%. Buy-and-hold on the same window is about
-$28. The same parameters on the previous race's dev window (BTC +48 bps)
make +$7.81, so the edge is not tuned to one window alone. Validated by
driving the real `main.py` through the protocol on the dev bars with an exact
integer replica of the harness fill model — two runs byte-identical.

## Files

- `main.py` — the bot (entrypoint, Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python protocol
  shim (`sdk/makefun_bars.py`).
- `research/` — the offline strategy search and the exact protocol driver
  used to validate the entry.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wkrc9se2&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>

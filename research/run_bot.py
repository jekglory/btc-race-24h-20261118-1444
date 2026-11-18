"""Exact protocol driver (research tooling, NOT shipped).

Drives the real main.py through agent-fun/bars-replay/v1 on the dev bars,
implementing the harness fill/account logic in Python ints exactly as the
kit's own harness source does (sim/bars/engine.ts):
- buy:  spend = notional*9996//10000; price = open*10002*M.num//(10000*M.den)
         with M from BarsPool.buy(spend); qty = spend*10**13//(price*10**6)
- sell: value = qty*open//10**7; price = max(1, open*9998*M.den//(10000*M.num))
         with M from BarsPool.sell(value); gross = qty*price//10**7
         proceeds = gross*9996//10000
- max_slippage vs the latest close the bot was sent; flatten at the last
  close vs its c_depth, no max_slippage, no min notional.
- cost basis: buy adds notional; sell scales cost down pro-rata.
Run twice; the two action logs must match byte for byte.
"""
import gzip
import json
import subprocess
import sys
import os

KIT = "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/kit/btc-race-24h-20261118-1444-kit"
BOT = "/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/main.py"
BPS = 10000
FEE_BPS = 4
SLIP_BPS = 2
START_CASH = 1_000_000_000  # micro-USDC
MIN_NOTIONAL = 1_000_000


def load_bars():
    bars = [json.loads(l) for l in gzip.open(
        KIT + "/dataset/bars/CBBTC.ndjson.gz", "rt")]
    for b in bars:
        b["symbol"] = "CBBTC"
    return bars


class Pool:
    """BarsPool for a single hop, exact integer arithmetic (engine.ts)."""

    def __init__(self, depth):
        d = depth * 10 ** 6  # quote_scale 6
        self.yn, self.yd = d, 1
        self.kn, self.kd = d * d, 1
        self.unit = 10 ** 6

    def buy(self, spend):
        yn2 = self.yn + spend * self.unit * self.yd
        num = self.yn * yn2 * self.kd
        den = self.yd * self.yd * self.kn
        after = Pool.__new__(Pool)
        after.yn, after.yd, after.kn, after.kd, after.unit = (
            yn2, self.yd, self.kn, self.kd, self.unit)
        return num, den, after

    def sell(self, value):
        t = self.kn * self.yd + value * self.unit * self.yn * self.kd
        num = t * self.yd
        den = self.kd * self.yn * self.yn
        after = Pool.__new__(Pool)
        after.yn, after.yd, after.kn, after.kd, after.unit = (
            self.kn * self.yn, t, self.kn, self.kd, self.unit)
        return num, den, after


def buy_fill(notional, open_px, depth):
    spend = notional * (BPS - FEE_BPS) // BPS
    num, den, _ = Pool(depth).buy(spend)
    price = open_px * (BPS + SLIP_BPS) * num // (BPS * den)
    qty = spend * 10 ** (8 + 5) // (price * 10 ** 6)
    return {"price": price, "spend": spend, "fee": notional - spend, "qty": qty}


def sell_fill(qty, open_px, depth):
    value = qty * open_px * 10 ** 6 // 10 ** (8 + 5)
    num, den, _ = Pool(depth).sell(value)
    slipped = open_px * (BPS - SLIP_BPS) * den // (BPS * num)
    price = slipped if slipped >= 1 else 1
    gross = qty * price * 10 ** 6 // 10 ** (8 + 5)
    proceeds = gross * (BPS - FEE_BPS) // BPS
    return {"price": price, "gross": gross, "fee": gross - proceeds,
            "proceeds": proceeds}


def value_of(qty, price):
    return qty * price * 10 ** 6 // 10 ** (8 + 5)


def run_once():
    bars = load_bars()
    hello = {
        "type": "hello", "protocol": "agent-fun/bars-replay/v1", "seed": "1",
        "symbols": [{"symbol": "CBBTC",
                     "mint": "cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij",
                     "price_scale": 5, "qty_scale": 8}],
        "capital": {"quote": "USDC", "quote_scale": 6,
                    "quote_units": str(START_CASH)},
        "bar_interval": "1m", "first_close_ms": int(bars[0]["t"]),
        "caps": {"max_open_positions": 1, "max_orders_per_bar": 16,
                 "max_weight_bps": 10000},
        "fees": {"fee_bps": FEE_BPS, "slippage_bps": SLIP_BPS,
                 "min_notional_quote_units": str(MIN_NOTIONAL)},
    }
    env = dict(os.environ, PYTHONHASHSEED="0")
    proc = subprocess.Popen(
        [sys.executable, "-P", "-s", BOT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env=env)
    log = []          # action log: every reply line, byte for byte
    cash = START_CASH
    qty = 0
    cost = 0
    pending = []      # orders decided on previous batch
    prev_close = None
    equity_curve = []
    peak_eq = START_CASH
    max_dd = 0.0
    trades = 0
    fees = 0
    fills_log = []

    def account():
        eq = cash + (value_of(qty, int(bars[cur]["c"])) if qty else 0)
        pos = [{"symbol": "CBBTC", "qty": str(qty),
                "cost_quote_units": str(cost)}] if qty else []
        return {"cash_quote_units": str(cash), "positions": pos,
                "equity_quote_units": str(eq)}

    def send(obj):
        proc.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
        proc.stdin.flush()

    def read_reply():
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("bot exited early; stderr: " +
                               proc.stderr.read()[:2000])
        log.append(line.rstrip("\n"))
        return json.loads(line)

    send(hello)
    for k, bar in enumerate(bars):
        cur = k
        # resolve pending orders at this bar's open
        fills = []
        open_px = int(bar["o"])
        depth = int(bar["o_depth"][0])
        for o in pending:
            if o["side"] == "buy":
                f = buy_fill(int(o["notional_quote_units"]), open_px, depth)
                rej = None
                if prev_close is not None and f["price"] * BPS > prev_close * (BPS + int(o["max_slippage_bps"])):
                    rej = "max_slippage"
                if rej is None and int(o["notional_quote_units"]) > cash:
                    rej = "insufficient_cash"
                if rej is None and int(o["notional_quote_units"]) < MIN_NOTIONAL:
                    rej = "below_min_notional"
                if rej:
                    fills.append({"client_id": o["client_id"], "side": "buy",
                                  "symbol": "CBBTC", "status": "rejected",
                                  "reason": rej})
                else:
                    cash -= int(o["notional_quote_units"])
                    qty += f["qty"]
                    cost += int(o["notional_quote_units"])
                    fees += f["fee"]
                    trades += 1
                    fills.append({"client_id": o["client_id"], "side": "buy",
                                  "symbol": "CBBTC", "status": "filled",
                                  "price": str(f["price"]),
                                  "qty": str(f["qty"])})
            else:
                q = int(o["qty"])
                f = sell_fill(q, open_px, depth)
                rej = None
                if q > qty:
                    rej = "insufficient_position"
                elif prev_close is not None and f["price"] * BPS < prev_close * (BPS - int(o["max_slippage_bps"])):
                    rej = "max_slippage"
                if rej:
                    fills.append({"client_id": o["client_id"], "side": "sell",
                                  "symbol": "CBBTC", "status": "rejected",
                                  "reason": rej})
                else:
                    cash += f["proceeds"]
                    cost = cost * (qty - q) // qty if qty else 0
                    qty -= q
                    fees += f["fee"]
                    trades += 1
                    fills.append({"client_id": o["client_id"], "side": "sell",
                                  "symbol": "CBBTC", "status": "filled",
                                  "price": str(f["price"]),
                                  "qty": str(q)})
        fills_log.extend(fills)
        eq = cash + (value_of(qty, int(bar["c"])) if qty else 0)
        equity_curve.append(eq)
        peak_eq = max(peak_eq, eq)
        max_dd = max(max_dd, (peak_eq - eq) / START_CASH)
        batch = {"type": "batch", "seq": k, "t": int(bar["t"]),
                 "bars": [bar], "fills": fills, "account": account()}
        send(batch)
        reply = read_reply()
        assert reply["type"] == "reply" and reply["seq"] == k, reply
        pending = reply["orders"]
        prev_close = int(bar["c"])
    # last batch's orders are rejected (after_end); flatten at last close
    last = bars[-1]
    flat = None
    if qty > 0:
        f = sell_fill(qty, int(last["c"]), int(last["c_depth"][0]))
        cash += f["proceeds"]
        fees += f["fee"]
        flat = {"price": f["price"], "qty": qty, "proceeds": f["proceeds"]}
        qty = 0
        cost = 0
    done = {"type": "done", "seq": len(bars),
            "account": {"cash_quote_units": str(cash), "positions": [],
                        "equity_quote_units": str(cash)}}
    send(done)
    proc.stdin.close()
    rc = proc.wait(timeout=60)
    err = proc.stderr.read()
    if rc != 0:
        raise RuntimeError(f"bot exited {rc}: {err[:2000]}")
    if err.strip():
        print("bot stderr:", err[:500])
    pnl = (cash - START_CASH) / 1e6
    return {"pnl_usd": pnl, "final_cash": cash, "trades": trades,
            "fees_usd": fees / 1e6, "max_dd_pct": max_dd * 100,
            "log": log, "fills": fills_log, "flatten": flat,
            "equity_curve": equity_curve}


if __name__ == "__main__":
    r1 = run_once()
    r2 = run_once()
    same = r1["log"] == r2["log"]
    print("run1 PnL $%.2f trades %d fees $%.2f maxDD %.2f%%" % (
        r1["pnl_usd"], r1["trades"], r1["fees_usd"], r1["max_dd_pct"]))
    print("run2 PnL $%.2f trades %d fees $%.2f maxDD %.2f%%" % (
        r2["pnl_usd"], r2["trades"], r2["fees_usd"], r2["max_dd_pct"]))
    print("action logs byte-identical:", same)
    print("fills:")
    for f in r1["fills"]:
        print(" ", f)
    print("flatten:", r1["flatten"])
    json.dump({"run1": {k: v for k, v in r1.items() if k != "log"},
               "run2": {k: v for k, v in r2.items() if k != "log"},
               "identical": same},
              open("/home/hatch/workspace/makefun/btc-race-24h-20261118-1444/research/driver-result.json", "w"), indent=1)

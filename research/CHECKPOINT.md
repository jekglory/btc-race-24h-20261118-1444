# btc-race-24h-20261118-1444 — checkpoint log

- Competition: btc-race-24h-20261118-1444, $250 (top 10, 1st $60), entries close
  2026-11-18T20:44:00Z (03:44 WIB 19 Nov), result due 2026-12-11.
- Kit: ~/workspace/makefun/btc-race-24h-20261118-1444/kit/btc-race-24h-20261118-1444-kit
  (downloaded from https://make.fun/c/btc-race-24h-20261118-1444/kit, 7,519,918 bytes).
  Dev window 1440 bars, 0 gaps, 2026-11-17 ~14:44Z to 2026-11-18 14:44Z.
- Dev window shape: start $65,083.31, end $63,260.75 (-281 bps), min $63,076.34,
  max $65,189.54. Buy-and-hold approx -$28.10 before costs.
- Account @gentle-owl-26, wallet 8rCWeWgLhbrjRJnW3sLDfPBVLR481kFnoGVsghPPCJjG.
  API key via command substitution only.
- Strategy search (research/search.py, float sim, fills at next open, 6 bps cost):
  3 families x grid, scored on NEW window and the 17 Nov window (old, +48 bps).
## Strategy decision (CORRECTED 2026-11-18 ~22:40 WIB)
- CORRECTION: the first float search sim had TWO bugs — fills landed one bar
  late, and it ignored the pool price impact (~12.5 bps per side at full
  $1,000 size vs ~$800k depth). Its +$4.88 pick for dip2 n=60 d=70 scored
  -$5.63 on the exact protocol driver. The float numbers in the earlier
  section are WRONG; do not trust them.
- Rewrote the search with EXACT integer fills (run_bot.py buy_fill/sell_fill
  from the kit harness source) and the bot's exact bar-59 window start.
  With exact fills, no full-size combo is positive on both windows — the
  impact kills small edges. Half-size trades cut impact to ~6 bps/side.
- DECISION (new family, "dip-and-target", NOT a copy of either earlier bot):
  60-bar SMA of closes; buy HALF the cash when the current close AND the
  previous close are both >= 100 bps below the SMA; sell the full position
  when its value reaches +160 bps above cost, or on a 200 bps trailing stop
  off peak value, or a 250 bps hard stop below cost. All-in on exit,
  max slippage 100 bps, all integer math.
- Exact-sim results for the pick (n=60, d=100, target=160, trail=200,
  stop=250, half size): NEW window +$6.82 (2 round trips, maxDD 0.8%),
  OLD window +$7.81 (1 round trip, maxDD 0.3%). Neighbourhood smooth:
  target 100/120/140/160/180 all positive on both windows
  (+$4.08..+$7.75 new, +$4.39..+$8.47 old); cliff only at target=200
  (new -$2.16). Trail 160-300 identical; stop never binds. Pick sits
  mid-band (target 160 of the 100-180 working range), not on the cliff.
- Trade detail (new): buy bar 64 $63,993 -> target sell bar 506 $64,976
  (+$7.27); second buy bar 1438 flattens at the last close (-$0.45,
  penultimate-bar tail artifact, bounded). Old: one clean trip +$7.81.
- Next: rewrite main.py for the new strategy, validate with the exact
  protocol driver x2 (research/run_bot.py), repo + README + LICENSE +
  owner.json, commit, push, kit check, submit.

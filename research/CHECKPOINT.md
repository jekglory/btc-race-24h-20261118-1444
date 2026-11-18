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
## Protocol-driver validation (2026-11-18 ~22:25 WIB)
- Real main.py driven through the exact protocol driver (research/run_bot.py,
  integer fill model copied from the kit's harness source): run1 PnL +$6.82,
  run2 PnL +$6.82, action logs byte-identical, 3 fills + flatten, fees $0.81,
  maxDD 0.75%. Matches the exact search sim exactly (+$6.82). DEV GATE PASSES.
- Fills: buy $63,993.37 -> target sell $64,975.97 (+$7.27 on $500);
  second buy $63,206.23 flattened at the last close (-$0.45).
- main.py revised twice after the first write (docstring PnL accuracy +
  tail-buy comment); driver re-run after the edits, same +$6.82 x2.

## SUBMITTED (2026-11-18 22:30 WIB / 15:30:14Z)
- Submission ID 01a1ef47-ae34-717c-8caa-cc19dd64e012, commit
  c1fdfd572d4301a389a2d9f4c45ae2129df856ba (repo jekglory/btc-race-24h-20261118-1444,
  public, MIT, created 15:16:08Z after the 14:44:00Z open).
- Bundle /tmp/btc-race-bundle.tar.gz (215,620 bytes, sha256
  f878a2723c626c73a41fdd88e615babbe6e2521636518be2fb922f3491b97c4d):
  2 sessions (builder c753167c 82 turns + parent e133e866 14 turns) + 1 usage
  row (parent's; builder rows are written when this subagent run completes)
  + prompt file (cron body, origin scheduled) + system prompt uploaded.
  First bundle attempt refused run-record (harness version "unknown" not
  accepted; fixed with --harness-version 1.3 --provider meta --model
  muse-spark-1.3, noting 1.3 is the Muse Spark version from the runtime).
  Kit check on the exact bundle: 14 passed, 0 failed, 4 skipped,
  5 at-submission; thinking_reproduces 59.2% (main.py 54 authored lines).
- Live stage verified (makefun status): "checked, round 1" — ALL server
  intake checks pass, incl. quota, duplicate_snapshot, security_audit,
  transcripts_run_record; dev_profitable pending (dev grade under way).
  The entry RACES once its dev grade ends above $0 (local +$6.82).
- Claim code recorded ONLY in ~/workspace/makefun/submissions-2026-11-13.md
  section 18. Quota: 3rd submission this UTC day (7 of 10/day remain);
  1st for this competition. Final window starts 2026-11-18T20:59:00Z;
  result due 2026-12-11T20:59:00Z.

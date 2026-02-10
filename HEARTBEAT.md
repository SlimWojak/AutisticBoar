# AutistBoar Heartbeat Checklist

Follow these steps IN ORDER on every heartbeat. Do not skip steps.
Do not improvise. Do not add steps. This is the cycle.

## 1. Killswitch Check
```bash
python3 -m lib.guards.killswitch
```
- If status is `ACTIVE` → reply HEARTBEAT_OK immediately. Do nothing else.

## 2. State Orientation
- Read `state/latest.md` for current positions and recent activity.
- Read `state/state.json` for exact portfolio numbers.

## 3. Drawdown Guard (INV-DRAWDOWN-50)
```bash
python3 -m lib.guards.drawdown
```
- If status is `HALTED` → reply HEARTBEAT_OK. Do nothing else.
- If `alert: true` → send Telegram message to G:
  "DRAWDOWN HALT: pot at {current_pct}% of starting. Trading halted for 24h."

## 4. Risk Limits Check (INV-DAILY-EXPOSURE-30)
```bash
python3 -m lib.guards.risk
```
- If status is `BLOCKED` → no new entries this cycle. Continue to step 7 (watchdog only).
- If warnings present → note them, reduce sizing if needed.

## 5. Smart Money Oracle
```bash
python3 -m lib.skills.oracle_query
```
- Review whale accumulation signals.
- Note any tokens with 3+ independent wallets buying.

## 6. Narrative Hunter
```bash
python3 -m lib.skills.narrative_scan
```
- Review social + onchain momentum.
- Cross-reference with oracle signals from step 5.

## 7. Position Watchdog
- For each open position in state.json:
  - Check current price vs entry price.
  - If stop-loss triggered (-20%): prepare exit.
  - If take-profit triggered (+100%): prepare exit.
  - If liquidity dropped significantly: prepare exit.

## 8. Execute Exits
- For any positions flagged for exit in step 7:
```bash
python3 -m lib.skills.execute_swap --direction sell --token <MINT> --amount <AMOUNT>
```
- Write autopsy bead for each exit:
```bash
python3 -m lib.skills.bead_write --type exit --data '<JSON>'
```

## 9. Evaluate New Opportunities
- Cross-reference oracle signals (step 5) with narrative signals (step 6).
- Apply conviction framework:
  - 2+ independent signals → consider entry
  - 1 signal only → document, do not trade
  - Conflicting signals → stand down

## 10. Edge Bank Query (Before Any Entry)
```bash
python3 -m lib.skills.bead_query --context '<SIGNAL_SUMMARY>'
```
- Review: "Last N similar patterns: X rugged, Y succeeded"
- Factor historical outcomes into conviction assessment.

## 11. Pre-Trade Validation (INV-RUG-WARDEN-VETO)
- For any candidate token:
```bash
python3 -m lib.skills.warden_check --token <MINT_ADDRESS>
```
- If `FAIL` → do not trade. Log reason. Move to next candidate.
- If `WARN` → require 3+ signal convergence to proceed.
- If `PASS` → proceed to execution.

## 12. Execute Entries
- Determine trade size based on conviction:
  - ≤$50 → auto-execute
  - $50-$100 → require 2+ signal convergence
  - >$100 → send Telegram alert to G, DO NOT execute (INV-HUMAN-GATE-100)
```bash
python3 -m lib.skills.execute_swap --direction buy --token <MINT> --amount <SOL_AMOUNT>
```
- Write autopsy bead:
```bash
python3 -m lib.skills.bead_write --type entry --data '<JSON>'
```

## 13. Update State
- Update `state/state.json` with:
  - New/closed positions
  - Updated PnL
  - Daily exposure
  - Last heartbeat timestamp
- Regenerate `state/latest.md` summary.

## 14. Report
- If any trade was executed, position exited, or notable event occurred:
  → Send concise Telegram summary to G.
  → Lead with action, follow with why, end with numbers.
- If nothing happened:
  → Reply HEARTBEAT_OK

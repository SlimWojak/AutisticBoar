# AutistBoar Heartbeat Checklist

Follow these steps IN ORDER on every heartbeat. Do not skip steps.
Do not improvise. Do not add steps. This is the cycle.

**CRITICAL:** All commands must run from workspace root with venv active:
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m <module>
```

## 0. Dry-Run Mode Check
- Read `state/state.json` and check `dry_run_mode` field.
- If `dry_run_mode: true`:
  - Run all steps normally but DO NOT execute trades (skip step 12).
  - Log conviction scores and recommendations to console.
  - Increment `dry_run_cycles_completed` in state.json.
  - If `dry_run_cycles_completed >= dry_run_target_cycles`: alert G with 📊 DIGEST showing sample scores.

## 1. Killswitch Check
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.guards.killswitch
```
- If status is `ACTIVE` → reply HEARTBEAT_OK immediately. Do nothing else.

## 2. State Orientation
- Read `state/checkpoint.md` for strategic context from the last heartbeat.
- Read `state/latest.md` for current positions and recent activity.
- Read `state/state.json` for exact portfolio numbers.

## 3. Drawdown Guard (INV-DRAWDOWN-50)
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.guards.drawdown
```
- If status is `HALTED` → reply HEARTBEAT_OK. Do nothing else.
- If `alert: true` → send Telegram message to G:
  "🔴 CRITICAL: DRAWDOWN HALT — pot at {current_pct}% of starting. Trading halted for 24h."

## 4. Risk Limits Check (INV-DAILY-EXPOSURE-30)
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.guards.risk
```
- If status is `BLOCKED` → no new entries this cycle. Continue to step 7 (watchdog only).
- If warnings present → note them, reduce sizing if needed.

## 5. Smart Money Oracle
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.oracle_query
```
- Review whale accumulation signals.
- Extract: number of distinct whales accumulating per token.

## 6. Narrative Hunter
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.narrative_scan
```
- Review social + onchain momentum.
- Extract: volume spike multiple, KOL detection, narrative age.

## 7. Position Watchdog (Exit Tier Logic)
- For each open position in state.json:
  - Check current price vs entry price and peak price.
  - **Stop-loss (-20%):** Exit 100% immediately.
  - **Take-profit tier 1 (+100% / 2x):** Exit 50% of position.
  - **Take-profit tier 2 (+400% / 5x):** Exit 30% of remaining position.
  - **Trailing stop:** If position is in profit and drops 20% from peak → exit remainder.
  - **Time decay:** If no price movement >5% after 60min → exit.
  - **Liquidity drop:** If liquidity drops >50% from entry → prepare exit.

## 8. Execute Exits
- For any positions flagged for exit in step 7:
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.execute_swap --direction sell --token <MINT> --amount <AMOUNT>
```
- Write autopsy bead for each exit:
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.bead_write --type exit --data '<JSON>'
```

## 9. Conviction Scoring (Replaces Old "Evaluate Opportunities")
- For each candidate token detected in steps 5-6:
  - Gather signal inputs:
    - `smart_money_whales`: count from step 5
    - `narrative_volume_spike`: multiple from step 6
    - `narrative_kol_detected`: boolean from step 6
    - `narrative_age_minutes`: time since first detection
    - `rug_warden_status`: from step 11 (run warden first)
    - `edge_bank_match_pct`: from step 10 (run query first)
  
  - Run conviction scorer:
    ```bash
    cd /home/autistboar/autisticboar && .venv/bin/python3 lib/scoring.py \
      --whales <N> \
      --volume-spike <X> \
      --kol \  # if detected
      --narrative-age <MIN> \
      --rug-warden <STATUS> \
      --edge-match <PCT> \
      --pot <CURRENT_SOL>
    ```
  
  - Parse output: `total_score`, `breakdown`, `recommendation`, `position_size_sol`
  
  - **Decision logic:**
    - `VETO`: Rug Warden FAIL → do not trade, log reason.
    - `DISCARD` (score < 60): Ignore, no alert.
    - `WATCHLIST` (60-84): Log with 🟢 INFO alert to G showing score breakdown.
    - `AUTO_EXECUTE` (≥85): Proceed to step 12 (subject to tier gates + dry-run check).

## 10. Edge Bank Query (Before Scoring)
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.bead_query --context '<SIGNAL_SUMMARY>'
```
- Extract: historical match percentage for similar setups.
- Feed this into conviction scoring as `edge_bank_match_pct`.

## 11. Pre-Trade Validation (INV-RUG-WARDEN-VETO)
- For any candidate token:
```bash
cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.warden_check --token <MINT_ADDRESS>
```
- Extract: `PASS`, `WARN`, or `FAIL`.
- Feed this into conviction scoring as `rug_warden_status`.
- **If FAIL:** Conviction scorer returns VETO → do not trade.

## 12. Execute Entries (Subject to Dry-Run + Tier Gates)
- **IF dry_run_mode is true:** Log the trade that WOULD execute, but DO NOT call execute_swap.
- **ELSE (live trading):**
  - Check tier gates:
    - Position size >$100 equivalent → send 🟡 WARNING to G with thesis, await approval (INV-HUMAN-GATE-100). DO NOT execute until G responds.
    - Position size ≤$100 → auto-execute.
  
  - Execute:
    ```bash
    cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.execute_swap \
      --direction buy \
      --token <MINT> \
      --amount <SOL_AMOUNT>
    ```
  
  - Write autopsy bead:
    ```bash
    cd /home/autistboar/autisticboar && .venv/bin/python3 -m lib.skills.bead_write \
      --type entry \
      --data '<JSON_WITH_CONVICTION_BREAKDOWN>'
    ```

## 13. Update State
- Update `state/state.json` with:
  - New/closed positions
  - Updated PnL
  - Daily exposure
  - Last heartbeat timestamp
  - If dry-run: increment `dry_run_cycles_completed`
- Regenerate `state/latest.md` summary.

## 14. Report
- **NEVER reply with just "HEARTBEAT_OK"** — always use the template format below (day 1 testing).
- If any trade was executed, position exited, or notable event occurred:
  → Send full template (🟢 ENTRY / 🟢 EXIT / 🟡 WARNING / 🔴 CRITICAL).
- If dry-run cycle completed and `dry_run_cycles_completed >= dry_run_target_cycles`:
  → Send 📊 DIGEST to G with sample scored opportunities from the 10 cycles.
- If nothing happened (no signals, no positions, no alerts):
  → Send exactly: `🟢 HB #{cycle} | {pot} SOL | 0 pos | no signals | dry-run {n}/10`
  → Example: `🟢 HB #1 | 14.0 SOL | 0 pos | no signals | dry-run 1/10`

## 15. Write Checkpoint (ALWAYS — even on HEARTBEAT_OK)
Write `state/checkpoint.md` with your current strategic thinking.
This is what the NEXT spawn reads for orientation. Keep it to 5 lines:

```markdown
thesis: "<what you're watching, what you expect to happen>"
regime: <green|yellow|red|halted>
open_positions: <N>
next_action: "<what the next heartbeat should prioritize>"
concern: "<any system issue, API degradation, or market worry — or 'none'>"
```

This checkpoint persists your strategic context across spawns.
Without it, the next spawn starts cold. Write it EVERY cycle.

## Post-Heartbeat Checklist

Before replying HEARTBEAT_OK or sending report, verify:

- [ ] `state/state.json` updated with latest portfolio numbers
- [ ] `state/latest.md` regenerated from state.json
- [ ] `state/checkpoint.md` written with strategic context
- [ ] If trade executed: autopsy bead written to `beads/`
- [ ] If notable event: Telegram alert sent to G with tier prefix
- [ ] If dry-run cycle: `dry_run_cycles_completed` incremented

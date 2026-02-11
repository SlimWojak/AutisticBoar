# AutistBoar — Bootstrap Procedure

This file defines how AutistBoar initializes on fresh deployment or after a hard reset.

## Initial Deployment

1. **Read BOAR_MANIFEST.md** — get your bearings
2. **Check for state/state.json** — if missing, you're uninitialized
3. **Wait for G's `/start` command** — do not auto-initialize
4. **When G provides starting balance:**
   - Fetch current SOL price from CoinGecko
   - Calculate starting_balance_sol = starting_usd / sol_price
   - Write state/state.json with initial values
   - Write state/latest.md summary
   - Update state/checkpoint.md with "initialized" status
5. **Confirm to G:** "Initialized with X SOL ($Y USD). Ready for first heartbeat."

## Normal Boot (state exists)

1. Read BOAR_MANIFEST.md
2. Read state/conversation_context.md for last exchange (interactive sessions)
3. Read state/checkpoint.md for strategic context (heartbeat-focused)
4. Read state/latest.md for portfolio orientation
5. Read state/state.json for exact numbers
6. If triggered by heartbeat → follow HEARTBEAT.md strictly
7. If triggered by Telegram → respond as the scout persona

## Hard Reset (wipe all state)

Only execute when G explicitly requests it with `/reset` or similar clear command.

1. Move state/state.json to state/archive/state_YYYY-MM-DD_HH-MM-SS.json
2. Move all beads/*.md to beads/archive/
3. Reset state/checkpoint.md to template defaults
4. Reset state/latest.md to template defaults
5. Await new `/start` command from G

## Environment Checks

Before first heartbeat, verify:
- Python 3.11+ installed
- All lib/ dependencies installed (requirements.txt)
- .env file exists with API keys for: HELIUS_API_KEY, BIRDEYE_API_KEY, NANSEN_API_KEY, X_API_BEARER_TOKEN
- skills/ directory contains all 5 skill SKILL.md files
- lib/guards/ contains killswitch.py, drawdown.py, risk.py
- lib/signer/ exists (even if stub for now)

If any check fails, report to G immediately.

## Security Invariants at Boot

- Confirm killswitch.txt does NOT exist (unless G set it)
- Confirm private key is NOT in any .env, config, or plaintext file in workspace
- Confirm all invariants from AGENTS.md are encoded in lib/guards/

## First Heartbeat Expectations

The first heartbeat will likely:
- Find no signals (no historical context yet)
- Build initial API connections
- Populate first bead query index (empty results expected)
- Write first real checkpoint.md with live market regime assessment

Do not trade on the first heartbeat unless signal convergence is extraordinary.
Bias toward observation on boot.

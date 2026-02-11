# Idea Bank

Future enhancements and extensions for AutistBoar. Items are PARKED until core trading loop is validated.

## Ideas

| # | Date       | Idea | Source | Status |
|---|------------|------|--------|--------|
| 1 | 2026-02-10 | Telegram inline buttons for >$100 trade approvals — one-tap approve/reject instead of typed responses | G | PARKED — after INV-HUMAN-GATE-100 tested in production |
| 2 | 2026-02-10 | Multi-token position heat map in daily digest — visual representation of portfolio exposure by sector/narrative | G | PARKED |
| 3 | 2026-02-10 | Weekly autopsy digest — most valuable beads from the week, pattern synthesis, what worked/what didn't | G | PARKED |
| 4 | 2026-02-11 | `state/feedback/` directory — structured G approvals/rejections that persist into future heartbeat decisions. Closes the loop between Edge Bank (what happened) and behavioral change (what G thought about it). Pattern validated by shared-context architecture in OpenClaw community. | CTO Claude | PARKED |
| 5 | 2026-02-11 | Roundtable synthesis in daily digest — not just "what happened" but "what cross-signals emerged across all strategies today." Curator pattern. | CTO Claude | PARKED |
| 6 | 2026-02-11 | Multi-strategy shared context — when running memecoins + predictions + perps, each strategy writes to its own subdirectory. Strategist (Sonnet) reads across all for cross-signals. | CTO Claude | PARKED |
| 7 | 2026-02-11 | ChronoBets prediction market skill — place small USDC bets on Pyth oracle markets (BTC/ETH/SOL) as conviction calibration. Prepare/submit pattern fits Blind KeyMan. | G + CTO Claude | PARKED — after core trading loop validated |
| 8 | 2026-02-10 | Structured reasoning chains at decision time, not just post-trade autopsy. Strategist (Sonnet) outputs logic tree with every trade decision, persisted in bead for fast human review. Pattern: evidence bundle → reasoning chain → decision → G audits the logic, not the trade. | G | PARKED |
| 9 | 2026-02-11 | Tiered bead context loading (L0/L1/L2) — when Edge Bank beads/ hits 100+ entries, implement manual tiering: `recent.md` (last 10 trades, full detail), `monthly_summary.md` (win rate + patterns, compressed), `archive/` (30+ days old, lightly indexed). Queries hit recent first, fall back to summaries only if needed. Inspired by claw-compactor's progressive context pattern but implemented our way — no lossy compression on trade data. | G + claw-compactor review | PARKED — revisit when beads/ > 50 entries |
| 10 | 2026-02-11 | SkillRL pattern — replace raw bead retrieval with distilled SkillBank. Opus daily job reads beads, extracts reusable skills (success heuristics + failure avoidance rules), writes to state/skillbank/. Heartbeats retrieve skills not beads. See detailed notes below table. | CTO Claude + SkillRL paper | PARKED — requires 50+ beads before meaningful distillation |

## Selection Criteria

Ideas move from PARKED → ACTIVE when:
1. Core trading loop has 30+ days of production data
2. Edge Bank has meaningful pattern density (50+ beads)
3. G explicitly prioritizes the enhancement
4. The idea solves a demonstrated pain point (not speculative optimization)

---

## DETAILED NOTES

### Idea #10: SkillRL Pattern — Edge Bank Evolution

**Problem it solves:**  
Edge Bank currently stores raw trade beads (logs). Conviction scoring does vector search for "similar setups" — matching on surface features, not extracted wisdom. This works early but plateaus: more beads = more noise, not more intelligence. The agent re-derives insights from raw data every cycle instead of building on distilled knowledge.

**The SkillRL pattern (3 components):**

1. **DISTILLATION** — Strong model (Opus) periodically reads batches of raw beads and extracts two types of skills:
   - **Success skills:** generalized heuristics from winning trades  
     Example: *"Whale accumulation preceding social momentum by 10-30min has >60% win rate. Whale-first = genuine accumulation. Social-first = manufactured pump."*
   - **Failure skills:** avoidance rules from losing trades  
     Example: *"Avoid tokens where KOL posts precede whale activity. This pattern correlates with pump-and-dump. 4 of 5 such entries resulted in >20% loss."*

2. **HIERARCHICAL SKILLBANK** — Skills organized in two tiers:
   - **General skills:** apply across all tokens/strategies (e.g., "timing of whale vs social signal matters more than absolute volume")
   - **Task-specific skills:** apply to specific token categories or market regimes (e.g., "AI narrative tokens have ~1hr momentum window vs ~4hr for meme tokens")
   - Stored in: `state/skillbank/general.md` + `state/skillbank/specific.md` (or similar structure — implementation detail, not architecture decision)

3. **RECURSIVE CO-EVOLUTION** — The critical loop:
   - **Daily:** Opus reads last N beads → distills new/updated skills → writes to SkillBank
   - **Every heartbeat:** Strategist retrieves relevant SKILLS (not raw beads) during conviction evaluation
   - Better skills → better trades → richer beads → better distillation → repeat
   - The library and the trading performance co-evolve over time

**How it changes the current pipeline:**

**CURRENT:**  
Heartbeat → score opportunity → vector search Edge Bank for similar beads → crude pattern match (10 pts in conviction) → trade decision

**UPGRADED:**  
Heartbeat → score opportunity → retrieve relevant skills from SkillBank → Strategist applies distilled heuristics + avoidance rules → sharper conviction → trade decision

Meanwhile (async, daily):  
Opus reads new beads → distills/updates SkillBank → next day's heartbeats are smarter

**Implementation prerequisites:**
- 50+ real trade beads (success + failure) before first distillation is meaningful
- Opus daily job scheduled (cost: ~$0.10-0.30 per run depending on bead volume)
- SkillBank directory structure created
- Conviction scoring updated to retrieve skills instead of (or in addition to) raw beads
- Edge Bank raw beads preserved for audit — SkillBank is derived layer, not replacement

**Why this matters for a8ra:**  
This is the exact mechanism the Research Lab needs. Research generates raw findings (beads). A distillation layer extracts reusable strategies (skills). The Strategy Office retrieves skills, not raw research. The human gate reviews reasoning chains built on distilled skills — faster review, higher quality decisions. Same pattern, larger scale.

**Reference:**  
SkillRL paper — recursive skill evolution in RL for LLM agents. Key claims: 33% faster convergence, ~20% fewer tokens, higher final success rate vs raw trajectory memory.

---

## Archive

Rejected ideas and reasons go here.

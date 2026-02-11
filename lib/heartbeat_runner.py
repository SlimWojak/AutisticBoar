#!/usr/bin/env python3
"""
Heartbeat Runner — Execute full HEARTBEAT.md cycle with scoring integration.
This script is called by the agent to run steps 0-15 in a single execution.
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from lib.clients.nansen import NansenClient
from lib.clients.birdeye import BirdeyeClient
from lib.clients.x_api import XClient
from lib.scoring import ConvictionScorer, SignalInput
from lib.utils.narrative_tracker import NarrativeTracker


async def run_heartbeat() -> dict[str, Any]:
    """Execute full heartbeat cycle."""
    
    # Load state
    state_path = Path("state/state.json")
    with open(state_path, 'r') as f:
        state = json.load(f)
    
    dry_run = state.get("dry_run_mode", True)
    cycle_num = state.get("dry_run_cycles_completed", 0) + 1
    
    result = {
        "cycle": cycle_num,
        "timestamp": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
        "opportunities": [],
        "decisions": [],
        "errors": [],
    }
    
    # Step 5: Smart Money Oracle
    nansen = NansenClient()
    try:
        oracle_data = await nansen.get_smart_money_transactions(limit=50)
        oracle_signals = parse_oracle_signals(oracle_data)
        result["oracle_signals"] = oracle_signals
    except Exception as e:
        result["errors"].append(f"Oracle error: {e}")
        oracle_signals = []
    finally:
        await nansen.close()
    
    # Step 6: Narrative Hunter
    birdeye = BirdeyeClient()
    x_client = XClient()
    narrative_tracker = NarrativeTracker()
    
    try:
        # Get trending tokens
        trending = await birdeye.get_token_list_trending(limit=10)
        tokens = trending.get("data", trending.get("items", []))
        
        narrative_signals = []
        for token_data in (tokens[:5] if isinstance(tokens, list) else []):
            mint = token_data.get("address", "")
            if not mint:
                continue
            
            # Scan narrative for this token
            signal = await scan_token_narrative(mint, birdeye, x_client, narrative_tracker)
            if signal:
                narrative_signals.append(signal)
        
        result["narrative_signals"] = narrative_signals
    except Exception as e:
        result["errors"].append(f"Narrative error: {e}")
        narrative_signals = []
    finally:
        await birdeye.close()
        await x_client.close()
    
    # Step 9: Conviction Scoring
    scorer = ConvictionScorer()
    
    # Merge signals by token mint
    all_mints = set()
    for sig in oracle_signals:
        all_mints.add(sig["token_mint"])
    for sig in narrative_signals:
        all_mints.add(sig["token_mint"])
    
    for mint in all_mints:
        # Gather inputs
        oracle_sig = next((s for s in oracle_signals if s["token_mint"] == mint), None)
        narrative_sig = next((s for s in narrative_signals if s["token_mint"] == mint), None)
        
        whales = oracle_sig["wallet_count"] if oracle_sig else 0
        volume_spike = 0.0
        kol_detected = False
        age_minutes = 0
        
        if narrative_sig:
            volume_str = narrative_sig.get("volume_vs_avg", "0x")
            volume_spike = float(volume_str.replace("x", ""))
            kol_detected = narrative_sig.get("kol_mentions", 0) > 0
            age_minutes = narrative_tracker.get_age_minutes(mint)
        
        # Run Rug Warden (stub for now — returns PASS)
        rug_status = "PASS"  # TODO: integrate actual warden call
        
        # Score
        signal_input = SignalInput(
            smart_money_whales=whales,
            narrative_volume_spike=volume_spike,
            narrative_kol_detected=kol_detected,
            narrative_age_minutes=age_minutes,
            rug_warden_status=rug_status,
            edge_bank_match_pct=0.0,  # No beads yet
        )
        
        score = scorer.score(signal_input, pot_sol=state["current_balance_sol"])
        
        opportunity = {
            "token_mint": mint,
            "token_symbol": (oracle_sig or narrative_sig or {}).get("token_symbol", "UNKNOWN"),
            "score": score.total,
            "breakdown": score.breakdown,
            "recommendation": score.recommendation,
            "position_size_sol": score.position_size_sol,
            "reasoning": score.reasoning,
            "signals": {
                "whales": whales,
                "volume_spike": volume_spike,
                "kol": kol_detected,
                "age_min": age_minutes,
                "rug": rug_status,
            }
        }
        
        result["opportunities"].append(opportunity)
        
        # Decision logic
        if score.recommendation == "VETO":
            result["decisions"].append(f"VETO: {mint[:8]} — {score.reasoning}")
        elif score.recommendation == "DISCARD":
            result["decisions"].append(f"DISCARD: {mint[:8]} — score {score.total} < 60")
        elif score.recommendation == "WATCHLIST":
            result["decisions"].append(f"WATCHLIST: {mint[:8]} — score {score.total} (60-84)")
        elif score.recommendation == "AUTO_EXECUTE":
            if dry_run:
                result["decisions"].append(
                    f"DRY-RUN LOG: {mint[:8]} — would execute {score.position_size_sol:.4f} SOL (score {score.total})"
                )
            else:
                result["decisions"].append(
                    f"EXECUTE: {mint[:8]} — {score.position_size_sol:.4f} SOL (score {score.total})"
                )
                # TODO: Call execute_swap here in live mode
    
    # Step 13: Update state
    if dry_run:
        state["dry_run_cycles_completed"] = cycle_num
    state["last_heartbeat_time"] = datetime.utcnow().isoformat()
    
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    result["state_updated"] = True
    result["next_cycle"] = cycle_num + 1
    
    return result


def parse_oracle_signals(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse Nansen smart money transactions into signals."""
    SOL_MINT = "So11111111111111111111111111111111111111112"
    token_wallets: dict[str, dict[str, Any]] = {}
    
    transactions = data.get("data", [])
    if not isinstance(transactions, list):
        return []
    
    for tx in transactions:
        token_sold = tx.get("token_sold_address", "")
        token_bought = tx.get("token_bought_address", "")
        
        if token_sold == SOL_MINT and token_bought != SOL_MINT:
            mint = token_bought
            symbol = tx.get("token_bought_symbol", "UNKNOWN")
            value_usd = tx.get("trade_value_usd", 0)
        else:
            continue
        
        wallet = tx.get("trader_address", "")
        if not mint or not wallet:
            continue
        
        if mint not in token_wallets:
            token_wallets[mint] = {
                "token_mint": mint,
                "token_symbol": symbol,
                "wallets": set(),
                "total_value_usd": 0.0,
            }
        
        token_wallets[mint]["wallets"].add(wallet)
        token_wallets[mint]["total_value_usd"] += float(value_usd)
    
    signals = []
    for info in token_wallets.values():
        wallet_count = len(info["wallets"])
        if wallet_count >= 3:
            signals.append({
                "token_mint": info["token_mint"],
                "token_symbol": info["token_symbol"],
                "wallet_count": wallet_count,
                "total_buy_usd": round(info["total_value_usd"], 2),
            })
    
    return signals


async def scan_token_narrative(
    mint: str,
    birdeye: BirdeyeClient,
    x_client: XClient,
    tracker: NarrativeTracker,
) -> dict[str, Any] | None:
    """Scan single token for narrative signals."""
    try:
        overview = await birdeye.get_token_overview(mint)
        data = overview.get("data", overview)
        symbol = data.get("symbol", "UNKNOWN")
        
        volume_1h = float(data.get("v1hUSD", 0))
        volume_24h = float(data.get("v24hUSD", 0))
        avg_hourly = volume_24h / 24 if volume_24h > 0 else 0
        volume_ratio = round(volume_1h / avg_hourly, 1) if avg_hourly > 0 else 0
        
        # Only track if volume spike detected
        if volume_ratio >= 5.0:
            tracker.record_detection(mint)
        
        x_data = await x_client.search_recent(f"${symbol} OR {symbol} solana", max_results=50)
        tweets = x_data.get("data", [])
        mention_count = len(tweets) if isinstance(tweets, list) else 0
        
        kol_count = 0
        users = {}
        for u in x_data.get("includes", {}).get("users", []):
            users[u.get("id")] = u
        if isinstance(tweets, list):
            for tweet in tweets:
                author = users.get(tweet.get("author_id", ""), {})
                followers = author.get("public_metrics", {}).get("followers_count", 0)
                if followers >= 10000:
                    kol_count += 1
        
        return {
            "token_mint": mint,
            "token_symbol": symbol,
            "x_mentions_1h": mention_count,
            "kol_mentions": kol_count,
            "volume_vs_avg": f"{volume_ratio}x",
        }
    except Exception:
        return None


async def main():
    result = await run_heartbeat()
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

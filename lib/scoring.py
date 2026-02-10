#!/usr/bin/env python3
"""
Conviction Scoring System
Weighted signal aggregation for trade decision-making.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SignalInput:
    """Input signals from various detectors."""
    smart_money_whales: int = 0          # Number of distinct whales accumulating
    narrative_volume_spike: float = 0.0  # Volume multiple vs average
    narrative_kol_detected: bool = False
    narrative_age_minutes: int = 0       # Age of narrative signal
    rug_warden_status: str = "UNKNOWN"   # PASS, WARN, FAIL
    edge_bank_match_pct: float = 0.0     # Similarity to past winners


@dataclass
class ConvictionScore:
    """Output conviction score with breakdown."""
    total: int
    breakdown: Dict[str, int]
    recommendation: str  # AUTO_EXECUTE, WATCHLIST, DISCARD
    position_size_sol: float
    reasoning: str


class ConvictionScorer:
    """Calculate conviction scores from signal inputs."""
    
    def __init__(self, config_path: Path = Path("config/risk.yaml")):
        """Load scoring configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.weights = self.config['conviction']['weights']
        self.thresholds = self.config['conviction']['thresholds']
        self.sizing = self.config['conviction']['sizing']
        self.portfolio = self.config['portfolio']
        self.trade_limits = self.config['trade']
    
    def score_smart_money_oracle(self, whales: int) -> tuple[int, str]:
        """Score whale accumulation signals."""
        if whales == 0:
            return 0, "No whale accumulation detected"
        
        # +15 per whale, cap at 40 (requires 3+ whales for max)
        score = min(whales * 15, self.weights['smart_money_oracle'])
        
        if whales >= 3:
            return score, f"{whales} distinct whales accumulating (max points)"
        else:
            return score, f"{whales} whale(s) detected (+15 each)"
    
    def score_narrative_hunter(
        self, 
        volume_spike: float, 
        kol_detected: bool, 
        age_minutes: int
    ) -> tuple[int, str]:
        """Score social momentum + volume signals."""
        max_points = self.weights['narrative_hunter']
        
        # No signal
        if volume_spike < 5.0 and not kol_detected:
            return 0, "No narrative momentum"
        
        # Base score from volume spike
        if volume_spike >= 5.0:
            # Scale: 5x = 15pts, 10x = 25pts, 20x+ = 30pts
            base = min(int((volume_spike / 5.0) * 15), 25)
        else:
            base = 0
        
        # KOL bonus
        kol_bonus = 10 if kol_detected else 0
        
        # Time decay: full points until 30min, then decay to 0 at 60min
        if age_minutes <= 30:
            decay_factor = 1.0
        elif age_minutes < 60:
            decay_factor = 1.0 - ((age_minutes - 30) / 30)
        else:
            decay_factor = 0.0
        
        score = int((base + kol_bonus) * decay_factor)
        score = min(score, max_points)
        
        reasoning_parts = []
        if volume_spike >= 5.0:
            reasoning_parts.append(f"{volume_spike:.1f}x volume spike")
        if kol_detected:
            reasoning_parts.append("KOL detected")
        if age_minutes > 30:
            reasoning_parts.append(f"decayed ({age_minutes}min old)")
        
        reasoning = ", ".join(reasoning_parts) if reasoning_parts else "No narrative signal"
        
        return score, reasoning
    
    def score_rug_warden(self, status: str) -> tuple[int, str]:
        """Score Rug Warden validation."""
        if status == "PASS":
            return self.weights['rug_warden'], "Rug Warden: PASS"
        elif status == "WARN":
            return int(self.weights['rug_warden'] * 0.5), "Rug Warden: WARN (partial points)"
        else:  # FAIL or UNKNOWN
            return 0, f"Rug Warden: {status}"
    
    def score_edge_bank(self, match_pct: float) -> tuple[int, str]:
        """Score historical pattern match."""
        max_points = self.weights['edge_bank']
        
        if match_pct < 70.0:
            return 0, "No strong historical match"
        
        # Linear scale from 70% (5pts) to 100% (10pts)
        score = int(((match_pct - 70) / 30) * max_points)
        score = min(score, max_points)
        
        return score, f"{match_pct:.0f}% match to past winners"
    
    def calculate_position_size(
        self, 
        score: int, 
        pot_balance_sol: float,
        volatility_factor: float = 1.0
    ) -> float:
        """Calculate position size based on conviction score."""
        # Formula: size = (score / 100) × (pot × 0.01) × (1 / volatility_factor)
        base_size = (score / 100) * (pot_balance_sol * self.sizing['base_multiplier'])
        adjusted_size = base_size / volatility_factor
        
        # Cap at max_position_pct
        max_size = pot_balance_sol * (self.trade_limits['max_position_pct'] / 100)
        return min(adjusted_size, max_size)
    
    def score(
        self, 
        signals: SignalInput,
        pot_balance_sol: float,
        volatility_factor: float = 1.0
    ) -> ConvictionScore:
        """
        Calculate total conviction score and recommendation.
        
        Args:
            signals: Input signals from detectors
            pot_balance_sol: Current pot balance in SOL
            volatility_factor: Volatility adjustment (default 1.0)
        
        Returns:
            ConvictionScore with total, breakdown, and recommendation
        """
        breakdown = {}
        reasoning_parts = []
        
        # RUG WARDEN VETO CHECK (INV-RUG-WARDEN-VETO)
        if signals.rug_warden_status == "FAIL":
            return ConvictionScore(
                total=0,
                breakdown={"rug_warden": 0},
                recommendation="VETO",
                position_size_sol=0.0,
                reasoning="Rug Warden FAIL — trade vetoed (INV-RUG-WARDEN-VETO)"
            )
        
        # Score each signal
        oracle_score, oracle_reason = self.score_smart_money_oracle(signals.smart_money_whales)
        breakdown['smart_money_oracle'] = oracle_score
        reasoning_parts.append(f"Oracle: {oracle_reason}")
        
        narrative_score, narrative_reason = self.score_narrative_hunter(
            signals.narrative_volume_spike,
            signals.narrative_kol_detected,
            signals.narrative_age_minutes
        )
        breakdown['narrative_hunter'] = narrative_score
        reasoning_parts.append(f"Narrative: {narrative_reason}")
        
        warden_score, warden_reason = self.score_rug_warden(signals.rug_warden_status)
        breakdown['rug_warden'] = warden_score
        reasoning_parts.append(f"Warden: {warden_reason}")
        
        edge_score, edge_reason = self.score_edge_bank(signals.edge_bank_match_pct)
        breakdown['edge_bank'] = edge_score
        reasoning_parts.append(f"Edge: {edge_reason}")
        
        # Total score
        total = sum(breakdown.values())
        
        # Determine recommendation
        if total >= self.thresholds['auto_execute']:
            recommendation = "AUTO_EXECUTE"
        elif total >= self.thresholds['watchlist']:
            recommendation = "WATCHLIST"
        else:
            recommendation = "DISCARD"
        
        # Calculate position size
        position_size = self.calculate_position_size(total, pot_balance_sol, volatility_factor)
        
        return ConvictionScore(
            total=total,
            breakdown=breakdown,
            recommendation=recommendation,
            position_size_sol=position_size,
            reasoning=" | ".join(reasoning_parts)
        )


def main():
    """CLI for testing conviction scoring."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Calculate conviction score")
    parser.add_argument("--whales", type=int, default=0, help="Number of whales accumulating")
    parser.add_argument("--volume-spike", type=float, default=0.0, help="Volume multiple vs avg")
    parser.add_argument("--kol", action="store_true", help="KOL detected")
    parser.add_argument("--narrative-age", type=int, default=0, help="Narrative age in minutes")
    parser.add_argument("--rug-warden", default="UNKNOWN", choices=["PASS", "WARN", "FAIL", "UNKNOWN"])
    parser.add_argument("--edge-match", type=float, default=0.0, help="Edge bank match %")
    parser.add_argument("--pot", type=float, required=True, help="Current pot balance in SOL")
    parser.add_argument("--volatility", type=float, default=1.0, help="Volatility factor")
    
    args = parser.parse_args()
    
    signals = SignalInput(
        smart_money_whales=args.whales,
        narrative_volume_spike=args.volume_spike,
        narrative_kol_detected=args.kol,
        narrative_age_minutes=args.narrative_age,
        rug_warden_status=args.rug_warden,
        edge_bank_match_pct=args.edge_match
    )
    
    scorer = ConvictionScorer()
    result = scorer.score(signals, args.pot, args.volatility)
    
    output = {
        "total_score": result.total,
        "breakdown": result.breakdown,
        "recommendation": result.recommendation,
        "position_size_sol": round(result.position_size_sol, 4),
        "reasoning": result.reasoning
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

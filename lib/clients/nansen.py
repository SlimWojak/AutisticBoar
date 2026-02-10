"""Nansen API client — Smart money flows and wallet intelligence.

Used by Smart Money Oracle to detect whale accumulation patterns.
"""

from __future__ import annotations

import os
from typing import Any

from lib.clients.base import BaseClient


class NansenClient:
    """Nansen Pro: smart money flows, wallet PnL, entity labels."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("NANSEN_API_KEY", "")
        self._client = BaseClient(
            base_url="https://api.nansen.ai/v1",
            headers={"Authorization": f"Bearer {self.api_key}"},
            rate_limit=2.0,
            timeout=15.0,
            provider_name="nansen",
        )

    async def get_smart_money_transactions(
        self,
        chain: str = "solana",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get recent smart money transactions on Solana."""
        return await self._client.get(
            "/smart-money/transactions",
            params={"chain": chain, "limit": limit},
            cache_ttl=120,
        )

    async def get_token_smart_money(self, mint: str) -> dict[str, Any]:
        """Get smart money activity for a specific token."""
        return await self._client.get(
            "/token/smart-money",
            params={"address": mint, "chain": "solana"},
            cache_ttl=120,
        )

    async def get_wallet_profile(self, address: str) -> dict[str, Any]:
        """Get wallet profile: PnL, labels, entity type."""
        return await self._client.get(
            f"/wallet/{address}/profile",
            params={"chain": "solana"},
            cache_ttl=300,
        )

    async def get_wallet_tokens(self, address: str) -> dict[str, Any]:
        """Get tokens held by a wallet."""
        return await self._client.get(
            f"/wallet/{address}/tokens",
            params={"chain": "solana"},
            cache_ttl=120,
        )

    async def close(self) -> None:
        await self._client.close()

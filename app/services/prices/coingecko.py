from __future__ import annotations

from typing import Iterable
import aiohttp
from .types import CoinSearchResult

class CoinGeckoClient:
    BASE = "https://api.coingecko.com/api/v3"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def search(self, query: str, limit: int = 5) -> list[CoinSearchResult]:
        q = query.strip()
        if not q:
            return []
        url = f"{self.BASE}/search"
        async with self._session.get(url, params={"query": q}, timeout=aiohttp.ClientTimeout(total=15)) as r:
            r.raise_for_status()
            data = await r.json()

        coins = (data.get("coins") or [])[:limit]
        out: list[CoinSearchResult] = []
        for c in coins:
            out.append(
                CoinSearchResult(
                    id=str(c.get("id")),
                    name=str(c.get("name")),
                    symbol=str(c.get("symbol")),
                    market_cap_rank=c.get("market_cap_rank"),
                )
            )
        return out

    async def simple_price(self, coin_ids: Iterable[str], vs_currencies: Iterable[str]) -> dict[str, dict[str, float]]:
        ids = ",".join(sorted(set([c.strip().lower() for c in coin_ids if c])))
        vs = ",".join(sorted(set([v.strip().lower() for v in vs_currencies if v])))
        if not ids or not vs:
            return {}
        url = f"{self.BASE}/simple/price"
        async with self._session.get(
            url,
            params={"ids": ids, "vs_currencies": vs},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as r:
            r.raise_for_status()
            return await r.json()

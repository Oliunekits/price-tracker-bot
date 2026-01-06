from dataclasses import dataclass

@dataclass(frozen=True)
class CoinSearchResult:
    id: str
    name: str
    symbol: str
    market_cap_rank: int | None

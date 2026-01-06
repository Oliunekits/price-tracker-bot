from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.services.prices.types import CoinSearchResult

def coins_kb(coins: list[CoinSearchResult]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in coins:
        rank = f" (#{c.market_cap_rank})" if c.market_cap_rank else ""
        kb.button(
            text=f"{c.name} ({c.symbol.upper()}){rank}",
            callback_data=f"add:coin:{c.id}:{c.symbol.upper()}",
        )
    kb.button(text="🔎 Searcing again", callback_data="add:coin:retry")
    kb.adjust(1)
    return kb.as_markup()

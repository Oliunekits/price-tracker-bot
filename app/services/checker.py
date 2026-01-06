from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import aiohttp
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tracker, TrackerKind, Direction
from app.services.prices.coingecko import CoinGeckoClient
from app.services.prices.frankfurter import FrankfurterClient


def _to_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, float):
        return x
    if isinstance(x, int):
        return float(x)
    if isinstance(x, Decimal):
        return float(x)
    try:
        return float(x)
    except Exception:
        return None


def _crossed(direction: Direction, last_price: float | None, current_price: float, target: float) -> bool:
    if direction == Direction.gte:
        if last_price is None:
            return current_price >= target
        return last_price < target and current_price >= target

    if last_price is None:
        return current_price <= target
    return last_price > target and current_price <= target


def _fmt_tracker(t: Tracker) -> str:
    arrow = "≥" if t.direction == Direction.gte else "≤"
    status = "🟢" if t.is_active else "⏸"
    return f"{status} #{t.id} • {t.base}/{t.quote} • alert: {arrow} {t.target}"


async def check_prices_and_notify(bot: Bot, session: AsyncSession) -> None:
    res = await session.execute(select(Tracker).where(Tracker.is_active == True))
    trackers: list[Tracker] = list(res.scalars().all())
    if not trackers:
        return

    now = datetime.now(timezone.utc)

    crypto = [t for t in trackers if t.kind == TrackerKind.crypto]
    fx = [t for t in trackers if t.kind == TrackerKind.fx]

    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
        cg = CoinGeckoClient(http)
        ff = FrankfurterClient(http)

        crypto_by_quote: dict[str, list[Tracker]] = defaultdict(list)
        for t in crypto:
            crypto_by_quote[t.quote.lower()].append(t)

        crypto_prices: dict[tuple[str, str], float] = {}
        for quote, items in crypto_by_quote.items():
            ids = [t.coin_id for t in items if t.coin_id]
            if not ids:
                continue
            data = await cg.simple_price(ids, [quote])
            for t in items:
                if not t.coin_id:
                    continue
                p = (data.get(t.coin_id) or {}).get(quote)
                if p is not None:
                    crypto_prices[(t.coin_id, quote)] = float(p)

        fx_by_base: dict[str, list[Tracker]] = defaultdict(list)
        for t in fx:
            fx_by_base[t.base.upper()].append(t)

        fx_prices: dict[tuple[str, str], float] = {}
        for base, items in fx_by_base.items():
            quotes = [t.quote.upper() for t in items]
            rates = await ff.latest(base, quotes)
            for t in items:
                rate = rates.get(t.quote.upper())
                if rate is not None:
                    fx_prices[(t.base.upper(), t.quote.upper())] = float(rate)

    updates = 0
    for t in trackers:
        current_price: float | None = None

        if t.kind == TrackerKind.crypto and t.coin_id:
            current_price = crypto_prices.get((t.coin_id, t.quote.lower()))
        elif t.kind == TrackerKind.fx:
            current_price = fx_prices.get((t.base.upper(), t.quote.upper()))

        t.last_checked_at = now

        if current_price is None:
            continue

        last = _to_float(t.last_price)
        target = float(t.target)

        if _crossed(t.direction, last, current_price, target):
            arrow = "≥" if t.direction == Direction.gte else "≤"
            txt = (
                "🔔 <b>Price alert!</b>\n\n"
                f"{t.base}/{t.quote}\n"
                f"Current price: <b>{current_price:.8f}</b>\n"
                f"Condition: <b>{t.base}/{t.quote} {arrow} {target}</b>\n\n"
                "Manage: /trackers"
            )
            try:
                await bot.send_message(t.tg_user_id, txt, parse_mode="HTML")
                t.last_triggered_at = now
            except Exception:
                pass

        t.last_price = current_price
        updates += 1

    if updates:
        await session.commit()

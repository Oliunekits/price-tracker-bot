from __future__ import annotations
import re
import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.bot.states import AddTracker
from app.bot.keyboards.common import choose_kind_kb, choose_direction_kb, back_to_menu_kb
from app.bot.keyboards.coins import coins_kb
from app.db.models import Tracker, TrackerKind, Direction
from app.db.session import SessionLocal
from app.services.prices.coingecko import CoinGeckoClient
from app.services.prices.frankfurter import FrankfurterClient

router = Router()


def _is_ccy(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{3}", s.strip()))


async def _nbu_to_uah(http: aiohttp.ClientSession, ccy: str) -> float:
    ccy = ccy.upper()
    if ccy == "UAH":
        return 1.0
    url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={ccy}&json"
    async with http.get(url, timeout=15) as r:
        r.raise_for_status()
        data = await r.json()
    if not data:
        raise ValueError(f"NBU: unknown currency {ccy}")
    return float(data[0]["rate"])


async def _fx_rate(base: str, quote: str) -> float:
    """
    Returns base/quote exchange rate.
    If UAH is involved — fallback to NBU (Frankfurter often doesn't support UAH).
    """
    base = base.upper()
    quote = quote.upper()

    if base == quote:
        return 1.0

    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:

        if base == "UAH" or quote == "UAH":
            if quote == "UAH":
                return await _nbu_to_uah(http, base)

            q_to_uah = await _nbu_to_uah(http, quote)
            return 1.0 / q_to_uah


        ff = FrankfurterClient(http)
        rates = await ff.latest(base, [quote])
        rate = rates.get(quote)
        if rate is None:
            raise ValueError("No rate returned")
        return float(rate)


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddTracker.kind)
    await message.answer("What would you like to track?", reply_markup=choose_kind_kb())


@router.callback_query(F.data.startswith("add:kind:"))
async def cb_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[-1]
    if kind == "crypto":
        await state.update_data(kind=TrackerKind.crypto.value)
        await state.set_state(AddTracker.crypto_query)
        await call.message.edit_text(
            "🪙 Type a coin name or symbol, e.g. `bitcoin`, `btc`, `ethereum`:",
            parse_mode="Markdown",
        )
    else:
        await state.update_data(kind=TrackerKind.fx.value)
        await state.set_state(AddTracker.fx_base)
        await call.message.edit_text(
            "💱 Enter the base currency (3 letters), e.g. `USD`:",
            parse_mode="Markdown",
        )
    await call.answer()


@router.message(AddTracker.crypto_query)
async def crypto_query(message: Message, state: FSMContext):
    q = message.text.strip()
    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
        cg = CoinGeckoClient(http)
        coins = await cg.search(q, limit=5)

    if not coins:
        await message.answer("Nothing found 😿 Try another query:", reply_markup=back_to_menu_kb())
        return

    await state.set_state(AddTracker.choose_coin)
    await message.answer("Choose a coin:", reply_markup=coins_kb(coins))


@router.callback_query(AddTracker.choose_coin, F.data == "add:coin:retry")
async def coin_retry(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddTracker.crypto_query)
    await call.message.edit_text("Okay, type another coin/symbol:", reply_markup=None)
    await call.answer()


@router.callback_query(AddTracker.choose_coin, F.data.startswith("add:coin:"))
async def coin_choose(call: CallbackQuery, state: FSMContext):
    _, _, coin_id, symbol = call.data.split(":")
    await state.update_data(coin_id=coin_id, base=symbol.upper())
    await state.set_state(AddTracker.quote)
    await call.message.edit_text(
        f"OK ✅ Coin: **{symbol.upper()}**\n\n"
        "Enter quote currency (3 letters), e.g. `USD` or `UAH`:",
        parse_mode="Markdown",
    )
    await call.answer()


@router.message(AddTracker.quote)
async def set_quote(message: Message, state: FSMContext):
    quote = message.text.strip().upper()
    if not _is_ccy(quote):
        await message.answer("Quote currency must be 3 letters, e.g. `USD` or `UAH`.", parse_mode="Markdown")
        return

    data = await state.get_data()
    base = str(data["base"]).upper()
    coin_id = data.get("coin_id")

    await state.update_data(quote=quote)

    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
            cg = CoinGeckoClient(http)
            prices = await cg.simple_price([coin_id], [quote.lower()])

        price = (prices.get(coin_id) or {}).get(quote.lower())
        if price is None:
            await message.answer(
                "Couldn't fetch the current price 😿 Try another currency (USD/UAH/EUR).",
                reply_markup=back_to_menu_kb(),
            )
            return

        await message.answer(
            f"📈 Current price:\n<b>{base}/{quote}</b> = <b>{float(price):.8f}</b>\n\n"
            "Now choose an alert condition:",
            parse_mode="HTML",
        )
    except Exception:
        await message.answer(
            "Couldn't fetch the current price 😿 Please try again in a minute.",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.set_state(AddTracker.direction)
    await message.answer("Choose an alert condition:", reply_markup=choose_direction_kb())


@router.message(AddTracker.fx_base)
async def fx_base(message: Message, state: FSMContext):
    base = message.text.strip().upper()
    if not _is_ccy(base):
        await message.answer("Currency code must be 3 letters, e.g. `USD`.", parse_mode="Markdown")
        return
    await state.update_data(base=base)
    await state.set_state(AddTracker.fx_quote)
    await message.answer("Enter quote currency, e.g. `UAH`:", parse_mode="Markdown")


@router.message(AddTracker.fx_quote)
async def fx_quote(message: Message, state: FSMContext):
    quote = message.text.strip().upper()
    if not _is_ccy(quote):
        await message.answer("Quote currency must be 3 letters, e.g. `UAH`.", parse_mode="Markdown")
        return

    data = await state.get_data()
    base = str(data["base"]).upper()
    await state.update_data(quote=quote)

    try:
        current_rate = await _fx_rate(base, quote)
    except Exception:
        await message.answer(
            "Couldn't fetch the current exchange rate 😿 Check currency codes or try later.",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await message.answer(
        f"📈 Current exchange rate:\n<b>{base}/{quote}</b> = <b>{current_rate:.6f}</b>\n\n"
        "Now choose an alert condition:",
        parse_mode="HTML",
    )

    await state.set_state(AddTracker.direction)
    await message.answer("Choose an alert condition:", reply_markup=choose_direction_kb())


@router.callback_query(AddTracker.direction, F.data.startswith("add:dir:"))
async def set_direction(call: CallbackQuery, state: FSMContext):
    direction = call.data.split(":")[-1]
    await state.update_data(direction=direction)
    await state.set_state(AddTracker.target)
    await call.message.edit_text(
        "Enter target price (a number). Example: `40000` or `38.5`",
        parse_mode="Markdown",
        reply_markup=None,
    )
    await call.answer()


@router.message(AddTracker.target)
async def set_target(message: Message, state: FSMContext):
    raw = message.text.strip().replace(",", ".")
    try:
        target = float(raw)
        if target <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("Target must be a positive number. Example: `40000`.", parse_mode="Markdown")
        return

    data = await state.get_data()
    kind = TrackerKind(data["kind"])
    base = str(data["base"]).upper()
    quote = str(data["quote"]).upper()
    direction = Direction(data["direction"])
    coin_id = str(data["coin_id"]) if kind == TrackerKind.crypto else None

    async with SessionLocal() as session:
        trk = Tracker(
            tg_user_id=message.from_user.id,
            kind=kind,
            coin_id=coin_id,
            base=base,
            quote=quote,
            direction=direction,
            target=target,
            is_active=True,
        )
        session.add(trk)
        await session.commit()
        await session.refresh(trk)

    arrow = "≥" if direction == Direction.gte else "≤"
    await message.answer(
        f"✅ Tracker added #{trk.id}\n"
        f"{base}/{quote} • alert: {arrow} {target}\n\n"
        "View/manage: /trackers",
        reply_markup=back_to_menu_kb(),
    )
    await state.clear()

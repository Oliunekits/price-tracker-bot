from __future__ import annotations

import re
import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.states import Rate
from app.bot.keyboards.common import choose_kind_kb, back_to_menu_kb
from app.bot.keyboards.coins import coins_kb
from app.services.prices.coingecko import CoinGeckoClient
from app.services.prices.frankfurter import FrankfurterClient

router = Router()


def _is_ccy(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{3}", s.strip()))


@router.message(Command("rate"))
async def cmd_rate(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Rate.kind)
    await message.answer("📈 What are we checking now?", reply_markup=choose_kind_kb())


@router.callback_query(F.data == "menu:rate")
async def cb_rate(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Rate.kind)
    await call.message.edit_text("📈 What are we checking now?", reply_markup=choose_kind_kb())
    await call.answer()


@router.callback_query(Rate.kind, F.data.startswith("add:kind:"))
async def rate_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[-1]

    if kind == "crypto":
        await state.update_data(kind="crypto")
        await state.set_state(Rate.crypto_query)
        await call.message.edit_text(
            "🪙 Type a coin (name or symbol), e.g. `bitcoin`, `btc`, `ethereum`:",
            parse_mode="Markdown",
        )
    else:
        await state.update_data(kind="fx")
        await state.set_state(Rate.fx_base)
        await call.message.edit_text(
            "💱 Enter the base currency (3 letters), e.g. `USD`:",
            parse_mode="Markdown",
        )

    await call.answer()


@router.message(Rate.crypto_query)
async def rate_crypto_query(message: Message, state: FSMContext):
    query = message.text.strip()

    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
        cg = CoinGeckoClient(http)
        coins = await cg.search(query, limit=5)

    if not coins:
        await message.answer(
            "Couldn't find anything 😿 Try a different query.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await state.set_state(Rate.choose_coin)
    await message.answer("Choose a coin:", reply_markup=coins_kb(coins))


@router.callback_query(Rate.choose_coin, F.data == "add:coin:retry")
async def rate_coin_retry(call: CallbackQuery, state: FSMContext):
    await state.set_state(Rate.crypto_query)
    await call.message.edit_text("OK, type another coin or symbol:")
    await call.answer()


@router.callback_query(Rate.choose_coin, F.data.startswith("add:coin:"))
async def rate_coin_choose(call: CallbackQuery, state: FSMContext):
    _, _, coin_id, symbol = call.data.split(":")

    await state.update_data(coin_id=coin_id, base=symbol.upper())
    await state.set_state(Rate.quote)

    await call.message.edit_text(
        f"✅ Coin: **{symbol.upper()}**\n\n"
        "Enter the quote currency (3 letters), e.g. `USD` or `UAH`:",
        parse_mode="Markdown",
    )
    await call.answer()


@router.message(Rate.quote)
async def rate_crypto_quote(message: Message, state: FSMContext):
    quote = message.text.strip().upper()

    if not _is_ccy(quote):
        await message.answer("Quote must be 3 letters, e.g. `USD`.", parse_mode="Markdown")
        return

    data = await state.get_data()
    coin_id = data["coin_id"]
    base = data["base"]

    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
        cg = CoinGeckoClient(http)
        prices = await cg.simple_price([coin_id], [quote.lower()])

    price = (prices.get(coin_id) or {}).get(quote.lower())
    if price is None:
        await message.answer(
            "Failed to get the price 😿",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await message.answer(
        f"📈 Current rate:\n<b>{base}/{quote}</b> = <b>{float(price):.8f}</b>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
    await state.clear()


@router.message(Rate.fx_base)
async def rate_fx_base(message: Message, state: FSMContext):
    base = message.text.strip().upper()

    if not _is_ccy(base):
        await message.answer("Currency must be 3 letters, e.g. `USD`.", parse_mode="Markdown")
        return

    await state.update_data(base=base)
    await state.set_state(Rate.fx_quote)

    await message.answer(
        f"✅ Base: **{base}**\nEnter the quote currency (3 letters, NOT {base}):",
        parse_mode="Markdown",
    )


@router.message(Rate.fx_quote)
async def rate_fx_quote(message: Message, state: FSMContext):
    quote = message.text.strip().upper()

    if not _is_ccy(quote):
        await message.answer("Quote must be 3 letters, e.g. `UAH`.", parse_mode="Markdown")
        return

    data = await state.get_data()
    base = data["base"]

    if base == quote:
        await message.answer(
            f"📈 Current rate:\n<b>{base}/{quote}</b> = <b>1.000000</b>",
            parse_mode="HTML",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    async with aiohttp.ClientSession(headers={"User-Agent": "price-tracker-bot/1.0"}) as http:
        ff = FrankfurterClient(http)
        rates = await ff.latest(base, [quote])

    rate = rates.get(quote)
    if rate is None:
        await message.answer(
            "Failed to get the rate 😿 Check the currency codes.",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await message.answer(
        f"📈 Current rate:\n<b>{base}/{quote}</b> = <b>{float(rate):.6f}</b>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
    await state.clear()

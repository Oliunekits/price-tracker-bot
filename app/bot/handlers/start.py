from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from app.bot.keyboards.common import main_menu_kb, choose_kind_kb, back_to_menu_kb

router = Router()

HELP_TEXT = (
    "I'm a price tracking bot 🧠\n\n"
    "What I can do:\n"
    "• Crypto (CoinGecko) — BTC/USD, ETH/UAH...\n"
    "• FX (Frankfurter) — USD/UAH, EUR/USD...\n"
    "• Alerts when a threshold is crossed (≥ or ≤)\n\n"
    "Commands:\n"
    "/add — add a tracker\n"
    "/trackers — list trackers\n"
    "/help — help"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("🏠 Menu", reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=back_to_menu_kb())


@router.callback_query(F.data == "menu:help")
async def cb_help(call: CallbackQuery):
    await call.message.edit_text(HELP_TEXT, reply_markup=back_to_menu_kb())
    await call.answer()


@router.callback_query(F.data.in_({"menu:home", "menu:back"}))
async def cb_menu(call: CallbackQuery):
    await call.message.edit_text("🏠 Menu", reply_markup=main_menu_kb())
    await call.answer()


@router.message(Command("add"))
async def cmd_add(message: Message):
    await message.answer("What do we track?", reply_markup=choose_kind_kb())


@router.callback_query(F.data == "menu:add")
async def cb_add(call: CallbackQuery):
    await call.message.edit_text("What do we track?", reply_markup=choose_kind_kb())
    await call.answer()

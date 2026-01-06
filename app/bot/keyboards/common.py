from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📈 Current rate", callback_data="menu:rate")
    kb.button(text="➕ Add tracker", callback_data="menu:add")
    kb.button(text="📋 My trackers", callback_data="menu:list")
    kb.button(text="❓ Help", callback_data="menu:help")
    kb.adjust(1)
    return kb.as_markup()


def choose_kind_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🪙 Crypto", callback_data="add:kind:crypto")
    kb.button(text="💱 FX", callback_data="add:kind:fx")
    kb.button(text="⬅️ Back", callback_data="menu:back")
    kb.adjust(2, 1)
    return kb.as_markup()


def choose_direction_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Notify when ≥ target", callback_data="add:dir:gte")
    kb.button(text="Notify when ≤ target", callback_data="add:dir:lte")
    kb.adjust(1)
    return kb.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Menu", callback_data="menu:home")
    kb.adjust(1)
    return kb.as_markup()

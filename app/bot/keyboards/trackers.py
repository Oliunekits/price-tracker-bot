from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.db.models import Tracker

def trackers_manage_kb(trackers: list[Tracker]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in trackers[:10]:
        status = "🟢" if t.is_active else "⏸"
        kb.button(text=f"{status} Toggle #{t.id}", callback_data=f"trk:toggle:{t.id}")
        kb.button(text=f"🗑 Delete #{t.id}", callback_data=f"trk:del:{t.id}")
    kb.button(text="🏠 Меню", callback_data="menu:home")
    kb.adjust(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    return kb.as_markup()

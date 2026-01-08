from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, delete, update
from app.bot.keyboards.trackers import trackers_manage_kb
from app.bot.keyboards.common import back_to_menu_kb, main_menu_kb
from app.db.models import Tracker
from app.db.session import SessionLocal

router = Router()


def _render(trackers: list[Tracker]) -> str:
    if not trackers:
        return "You don't have any trackers yet. Add one: /add"
    lines = ["📋 <b>Your trackers</b>\n"]
    for t in trackers:
        status = "🟢" if t.is_active else "⏸"
        arrow = "≥" if t.direction.value == "gte" else "≤"
        lines.append(f"{status} #{t.id} • {t.base}/{t.quote} • alert: {arrow} {float(t.target)}")
    lines.append("\nPress Toggle to pause/enable, or Delete to remove.")
    return "\n".join(lines)


@router.message(Command("trackers"))
async def cmd_trackers(message: Message):
    async with SessionLocal() as session:
        res = await session.execute(
            select(Tracker)
            .where(Tracker.tg_user_id == message.from_user.id)
            .order_by(Tracker.id.desc())
        )
        trackers = list(res.scalars().all())

    await message.answer(_render(trackers), parse_mode="HTML", reply_markup=trackers_manage_kb(trackers))


@router.callback_query(F.data == "menu:list")
async def cb_list(call: CallbackQuery):
    async with SessionLocal() as session:
        res = await session.execute(
            select(Tracker)
            .where(Tracker.tg_user_id == call.from_user.id)
            .order_by(Tracker.id.desc())
        )
        trackers = list(res.scalars().all())
    await call.message.edit_text(_render(trackers), parse_mode="HTML", reply_markup=trackers_manage_kb(trackers))
    await call.answer()


@router.callback_query(F.data.startswith("trk:toggle:"))
async def cb_toggle(call: CallbackQuery):
    trk_id = int(call.data.split(":")[-1])
    async with SessionLocal() as session:
        res = await session.execute(
            select(Tracker).where(Tracker.id == trk_id, Tracker.tg_user_id == call.from_user.id)
        )
        trk = res.scalar_one_or_none()
        if trk is None:
            await call.answer("Not found", show_alert=True)
            return
        trk.is_active = not trk.is_active
        await session.commit()

        res2 = await session.execute(
            select(Tracker)
            .where(Tracker.tg_user_id == call.from_user.id)
            .order_by(Tracker.id.desc())
        )
        trackers = list(res2.scalars().all())

    await call.message.edit_text(_render(trackers), parse_mode="HTML", reply_markup=trackers_manage_kb(trackers))
    await call.answer("OK")


@router.callback_query(F.data.startswith("trk:del:"))
async def cb_delete(call: CallbackQuery):
    trk_id = int(call.data.split(":")[-1])
    async with SessionLocal() as session:
        await session.execute(
            delete(Tracker).where(Tracker.id == trk_id, Tracker.tg_user_id == call.from_user.id)
        )
        await session.commit()
        res2 = await session.execute(
            select(Tracker)
            .where(Tracker.tg_user_id == call.from_user.id)
            .order_by(Tracker.id.desc())
        )
        trackers = list(res2.scalars().all())

    await call.message.edit_text(_render(trackers), parse_mode="HTML", reply_markup=trackers_manage_kb(trackers))
    await call.answer("Deleted")

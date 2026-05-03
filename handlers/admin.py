# handlers/admin.py
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from config import settings
from db.database import async_session_factory
from db.models import User
from sqlalchemy import select, func
from utils.keyboards import admin_menu_kb, back_kb, yes_no_kb

admin_router = Router()

class AdminStates(StatesGroup):
    broadcast_text = State()
    broadcast_confirm = State()

def check_admin(user_id: int) -> bool:
    # आपकी ID हमेशा एडमिन रहेगी
    if user_id == 7631540413:
        return True
    # साथ ही config में दी गई IDs भी एडमिन होंगी
    if user_id in settings.ADMIN_IDS:
        return True
    return False

@admin_router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not check_admin(message.from_user.id):
        await message.answer("⛔ Admin access required.")
        return
    await message.answer("⚙️ <b>Admin Panel</b>", reply_markup=admin_menu_kb())

@admin_router.message(Command("stats"))
async def quick_stats(message: Message) -> None:
    if not check_admin(message.from_user.id):
        return
    async with async_session_factory() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar()
    await message.answer(f"👥 Total Users: {total_users}")

@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery) -> None:
    if not check_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    action = callback.data.replace("admin_", "")

    if action == "stats":
        async with async_session_factory() as session:
            total_users = (await session.execute(select(func.count(User.id)))).scalar()
        text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🕐 Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await callback.message.edit_text(text, reply_markup=back_kb("admin"))

    elif action == "broadcast":
        await callback.message.edit_text(
            "📢 <b>Broadcast Message</b>\n\n"
            "Send the message you want to broadcast to all users.\n"
            "Use /cancel to cancel.",
        )

    elif action == "users":
        await callback.message.edit_text(
            "👥 <b>User Management</b>\n\nFeature coming soon...",
            reply_markup=back_kb("admin")
        )

    else:
        await callback.message.edit_text(
            "Coming soon...", reply_markup=back_kb("admin")
        )

    await callback.answer()

@admin_router.message(Command("cancel"), StateFilter(AdminStates))
async def cancel_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Cancelled.", reply_markup=admin_menu_kb())

@admin_router.message(StateFilter(AdminStates.broadcast_text))
async def broadcast_message(message: Message, state: FSMContext) -> None:
    if not check_admin(message.from_user.id):
        return
    text = message.html_text or message.text
    await state.update_data(broadcast_text=text)
    preview = text[:200] + "..." if len(text) > 200 else text
    await message.answer(
        f"📢 <b>Preview:</b>\n\n{preview}\n\nSend this to all users?",
        reply_markup=yes_no_kb("admin_broadcast_confirm", "admin"),
    )
    await state.set_state(AdminStates.broadcast_confirm)

@admin_router.callback_query(F.data == "admin_broadcast_confirm", StateFilter(AdminStates))
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not check_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text", "")
    await callback.message.edit_text("📤 Broadcasting... This may take a while.")

    async with async_session_factory() as session:
        users = (await session.execute(select(User))).scalars().all()
        sent = 0
        failed = 0
        for u in users:
            try:
                await callback.bot.send_message(u.telegram_id, broadcast_text)
                sent += 1
            except Exception as e:
                failed += 1

    await callback.message.edit_text(
        f"📢 <b>Broadcast Complete</b>\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"👥 Total: {len(users)}",
        reply_markup=back_kb("admin"),
    )
    await state.clear()
    await callback.answer()

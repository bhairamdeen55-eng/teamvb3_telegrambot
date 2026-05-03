# handlers/admin.py
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from states.admin_states import AdminStates
from utils.keyboards import admin_menu_kb, back_kb, yes_no_kb
from db.models import User, UserRole
from db.crud import UserCRUD, QuizCRUD
from config import settings

admin_router = Router()


def check_admin(user_id: int, user_obj=None) -> bool:
    """
    2 tarike se admin check karo:
    1. ADMIN_IDS mein hai (config se)
    2. DB mein role ADMIN/SUPERADMIN hai
    """
    if user_id in settings.ADMIN_IDS:
        return True
    if user_obj and hasattr(user_obj, 'role'):
        return user_obj.role in (UserRole.ADMIN, UserRole.SUPERADMIN)
    return False


@admin_router.message(Command("admin"))
async def admin_panel(message: Message, user=None) -> None:
    if not check_admin(message.from_user.id, user):
        await message.answer("⛔ Admin access required.")
        return
    await message.answer("⚙️ <b>Admin Panel</b>", reply_markup=admin_menu_kb())


@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery, user=None, session=None) -> None:
    if not check_admin(callback.from_user.id, user):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    action = callback.data.replace("admin_", "")

    if action == "stats":
        total_users = await UserCRUD.get_user_count(session)
        total_quizzes = len(await QuizCRUD.get_active_quizzes(session))
        text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📝 Active Quizzes: {total_quizzes}\n"
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

    elif action == "quizzes":
        quizzes = await QuizCRUD.get_active_quizzes(session)
        text = "📝 <b>Manage Quizzes</b>\n\n"
        if quizzes:
            for i, q in enumerate(quizzes[:10], 1):
                text += f"{i}. {q.title} ({q.topic}) — {q.question_count} Qs\n"
        else:
            text += "No quizzes available."
        await callback.message.edit_text(text, reply_markup=back_kb("admin"))

    elif action == "dpps":
        await callback.message.edit_text(
            "📚 <b>Manage DPPs</b>\n\nFeature coming soon...",
            reply_markup=back_kb("admin")
        )

    elif action == "subs":
        await callback.message.edit_text(
            "⭐ <b>Manage Subscriptions</b>\n\nFeature coming soon...",
            reply_markup=back_kb("admin")
        )

    await callback.answer()


@admin_router.message(Command("cancel"), StateFilter(AdminStates))
async def cancel_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Cancelled.", reply_markup=admin_menu_kb())


@admin_router.message(StateFilter(AdminStates.broadcast_text))
async def broadcast_message(message: Message, state: FSMContext, session=None) -> None:
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
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, session=None) -> None:
    if not check_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text", "")
    await callback.message.edit_text("📤 Broadcasting... This may take a while.")

    users = await UserCRUD.get_all_users(session)
    sent = 0
    failed = 0

    for u in users[:100]:
        try:
            await callback.bot.send_message(u.id, broadcast_text)
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
    

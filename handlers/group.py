"""
Guruh hodisalari handler'i.
Bot guruhga qo'shilganda avtomatik guruh ID ni saqlaydi.
"""
import logging

from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR

from config import ADMIN_IDS
from database import queries

logger = logging.getLogger(__name__)

router = Router()


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def bot_added_to_group_as_member(event: ChatMemberUpdated, bot: Bot):
    """Bot guruhga oddiy a'zo sifatida qo'shilganda."""
    await _handle_bot_added(event, bot)


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR)
)
async def bot_added_to_group_as_admin(event: ChatMemberUpdated, bot: Bot):
    """Bot guruhga admin sifatida qo'shilganda."""
    await _handle_bot_added(event, bot)


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> ADMINISTRATOR)
)
async def bot_promoted_to_admin(event: ChatMemberUpdated, bot: Bot):
    """Bot guruhda admin qilinganda."""
    chat = event.chat
    logger.info(f"Bot admin qilindi: {chat.title} (ID: {chat.id})")

    # Admin ga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"👑 Bot <b>admin</b> qilindi!\n\n"
                    f"📌 Guruh: {chat.title}\n"
                    f"🆔 ID: <code>{chat.id}</code>"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Admin ga xabar yuborishda xato: {e}")


async def _handle_bot_added(event: ChatMemberUpdated, bot: Bot):
    """Bot guruhga qo'shilganda guruh ID ni saqlaydi va adminlarga xabar beradi."""
    chat = event.chat

    # Faqat guruh va superguruhlar uchun
    if chat.type not in ("group", "supergroup"):
        return

    group_id = str(chat.id)
    group_title = chat.title or "Nomsiz guruh"

    # Guruh ID ni bazaga saqlash
    await queries.set_setting("group_id", group_id)
    logger.info(f"Bot guruhga qo'shildi va ID saqlandi: {group_title} (ID: {group_id})")

    # Admin(lar)ga private chatda xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"✅ Bot guruhga muvaffaqiyatli qo'shildi!\n\n"
                    f"📌 Guruh: <b>{group_title}</b>\n"
                    f"🆔 ID: <code>{group_id}</code>\n\n"
                    f"Endi eslatmalar shu guruhga yuboriladi.\n"
                    f"⚠️ Botni guruhda <b>admin</b> qiling, aks holda xabar yubora olmaydi!"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Admin ga xabar yuborishda xato: {e}")

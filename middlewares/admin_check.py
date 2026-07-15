"""
Admin tekshirish middleware.
Faqat ADMIN_IDS ro'yxatidagi foydalanuvchilar buyruqlarni ishlata oladi.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import ADMIN_IDS


class AdminCheckMiddleware(BaseMiddleware):
    """Private chatdagi xabarlarni faqat admin uchun ruxsat beradi."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Faqat private chat xabarlarini tekshiramiz
        if event.chat.type != "private":
            return await handler(event, data)

        user_id = event.from_user.id

        # .env dagi adminlarni tekshiramiz
        if user_id in ADMIN_IDS:
            return await handler(event, data)
        
        # Bazadagi adminlarni tekshiramiz
        from database import queries
        admin_in_db = await queries.get_admin(user_id)
        if admin_in_db:
            return await handler(event, data)

        await event.answer(
            "⛔ Sizda bu botdan foydalanish huquqi yo'q.\n"
            "Faqat admin buyruqlarni ishlata oladi."
        )
        return  # handler'ni chaqirmaymiz

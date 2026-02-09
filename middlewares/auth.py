# middlewares/auth.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable
from database.mongo import db
from loguru import logger


class LastPerson07_AuthMiddleware(BaseMiddleware):
    """Robust auth middleware: safe DB usage, safe user extraction."""

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        try:
            # --- extract from_user in a resilient way ---
            from_user = None

            # event may be Message or CallbackQuery when middleware is registered per-type
            if isinstance(event, Message):
                from_user = event.from_user
            elif isinstance(event, CallbackQuery):
                # callback_query.from_user is available; fallback to message.from_user
                from_user = event.from_user or (event.message.from_user if event.message else None)
            else:
                # sometimes the middleware receives an Update-like object
                if isinstance(event, Update):
                    if event.message and event.message.from_user:
                        from_user = event.message.from_user
                    elif event.callback_query and event.callback_query.from_user:
                        from_user = event.callback_query.from_user

            # if no user found, continue (e.g., channel posts or non-user updates)
            if not from_user:
                return await handler(event, data)

            user_id = from_user.id

            # --- check ban safely (db.is_banned handles connection internally) ---
            try:
                banned = await db.is_banned(user_id)
            except Exception as e:
                logger.warning(f"DB ban-check failed (proceeding): {e}")
                banned = False

            if banned:
                # reply politely depending on update type
                try:
                    if isinstance(event, CallbackQuery):
                        await event.answer("❌ You are banned from this bot.", show_alert=True)
                    elif isinstance(event, Message):
                        await event.answer("❌ You are banned from this bot.")
                    else:
                        # fallback for Update
                        cq = getattr(event, "callback_query", None)
                        if cq:
                            await cq.answer("❌ You are banned from this bot.", show_alert=True)
                except Exception:
                    # ignore errors sending the ban notice
                    pass
                return  # stop the chain for banned users

            # --- upsert user (best-effort) ---
            try:
                username = getattr(from_user, "username", "") or ""
                first_name = getattr(from_user, "first_name", "") or "User"
                await db.upsert_user(user_id, username, first_name)
            except Exception as e:
                logger.warning(f"DB upsert failed (ignored): {e}")

            # --- continue to handler ---
            return await handler(event, data)

        except Exception as e:
            # never crash middleware — log and continue
            logger.exception(f"Middleware crash (continuing): {e}")
            return await handler(event, data)

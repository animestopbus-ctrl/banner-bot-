# handlers/start.py
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from aiogram.filters import Command
from loguru import logger
from typing import Any, Optional
import io

from database.mongo import db
from services.anime_api import anime_api

router = Router()


# ------------- helpers ------------- #
async def safe_upsert(user: Any) -> None:
    """Best-effort user upsert using new db.upsert_user API."""
    if not user:
        return
    try:
        await db.upsert_user(user.id, user.username or "", user.first_name or "User")
    except Exception as e:
        logger.warning(f"DB upsert failed (ignored): {e}")


async def safe_edit_or_send(target: Any, text: str, reply_markup: Optional[Any] = None):
    """
    Try to edit the provided message-like object. If edit fails (media/non-text),
    fall back to sending a new message using the underlying message or .answer().
    `target` may be a Message or CallbackQuery or CallbackQuery.message.
    """
    parse_mode = "HTML"

    # Attempt edit_text where possible
    try:
        if hasattr(target, "edit_text") and target is not None:
            await target.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            return
    except Exception as e:
        logger.debug(f"edit_text failed (will fallback to answer/send): {e}")

    # Fallback: try .answer on target (works for CallbackQuery and Message)
    try:
        if hasattr(target, "answer"):
            await target.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
            return
    except Exception as e:
        logger.debug(f"answer fallback failed: {e}")

    # Final fallback: if target has a `.message`, try to send from there
    try:
        if hasattr(target, "message") and target.message:
            await target.message.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
            return
    except Exception as e:
        logger.debug(f"final message fallback failed: {e}")

    # If all else fails, log (we intentionally don't raise)
    logger.warning("Failed to deliver message (all fallbacks exhausted)")


# ------------- /start handler ------------- #
@router.message(Command("start"))
async def start_handler(message: Message):
    """Send a welcome caption + anime wallpaper (if available) with menu buttons."""
    user = message.from_user

    # Ensure DB upsert (best-effort)
    await safe_upsert(user)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
        [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
        [
            InlineKeyboardButton(text="📊 STATS", callback_data="stats"),
            InlineKeyboardButton(text="❓ HELP", callback_data="help")
        ]
    ])

    caption = (
        "<b>🚀 LastPerson07x BannerBot</b>\n\n"
        "Create stunning <b>anime banners</b> in seconds.\n\n"
        "✨ HD Wallpapers  \n"
        "⚡ Ultra Fast Generation  \n"
        "🎨 Pro Templates  \n"
        "🧠 Smart Text Engine  \n\n"
        "<b>Tap CREATE BANNER to begin.</b>"
    )

    # Fetch wallpaper bytes (best-effort). The service returns raw bytes or None.
    wallpaper_bytes = None
    try:
        wallpaper_bytes = await anime_api.get_anime_wallpaper()
    except Exception as e:
        logger.warning(f"Failed to fetch wallpaper: {e}")
        wallpaper_bytes = None

    try:
        if wallpaper_bytes:
            # Wrap bytes in a buffer for BufferedInputFile
            bio = io.BytesIO(wallpaper_bytes)
            bio.name = "wallpaper.jpg"  # helpful for some clients
            photo = BufferedInputFile(bio, filename="wallpaper.jpg")

            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            # Fallback: send text-only welcome
            await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

        logger.info(f"User {user.id} started bot")

    except Exception as e:
        logger.exception(f"Failed to send start message to user {getattr(user,'id',None)}: {e}")
        # final fallback — try a minimal message
        try:
            await message.answer("🚀 BannerBot started. Use /start to see options.")
        except Exception:
            logger.exception("Final fallback send also failed.")


# ------------- HELP ------------- #
@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.answer()
    text = (
        "<b>📖 BannerBot Help</b>\n\n"
        "🎨 CREATE → Generate banners  \n"
        "📱 Templates → Ready designs  \n"
        "📊 Stats → Bot usage  \n\n"
        "<b>Powered by @LastPerson07</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
    ])

    await safe_edit_or_send(callback.message or callback, text, reply_markup=kb)


# ------------- HOME ------------- #
@router.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery):
    await callback.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
        [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
        [
            InlineKeyboardButton(text="📊 STATS", callback_data="stats"),
            InlineKeyboardButton(text="❓ HELP", callback_data="help")
        ]
    ])
    text = "<b>🏠 Welcome Back</b>\n\nReady to create another banner?"
    await safe_edit_or_send(callback.message or callback, text, reply_markup=kb)


# ------------- STATS ------------- #
@router.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    await callback.answer()

    try:
        stats = await db.get_stats()
    except Exception as e:
        logger.warning(f"Failed to get stats: {e}")
        stats = {"total_users": 0, "total_banners": 0, "active_24h": 0}

    text = (
        "<b>📊 Bot Stats</b>\n\n"
        f"👥 Users: <code>{stats['total_users']:,}</code>\n"
        f"🖼 Banners: <code>{stats['total_banners']:,}</code>\n"
        f"🔥 Active: <code>{stats['active_24h']:,}</code>\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
    ])

    await safe_edit_or_send(callback.message or callback, text, reply_markup=kb)

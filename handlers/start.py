from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.filters import Command
from loguru import logger

from database.mongo import db
from services.anime_api import anime_api

router = Router()


# ✅ SAFE DB CALL
async def safe_upsert(user):
    try:
        await db.LastPerson07_upsert_user(
            user.id,
            user.username or "",
            user.first_name or "User"
        )
    except Exception as e:
        logger.error(f"DB error: {e}")


# ✅ SAFE EDIT
async def safe_edit(msg, text, kb):
    try:
        await msg.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except:
        await msg.answer(text, parse_mode="HTML", reply_markup=kb)


# ================= START =================

@router.message(Command("start"))
async def start_handler(message: Message):

    user = message.from_user
    await safe_upsert(user)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
        [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
        [
            InlineKeyboardButton(text="📊 STATS", callback_data="stats"),
            InlineKeyboardButton(text="❓ HELP", callback_data="help")
        ]
    ])

    caption = """
<b>🚀 LastPerson07x BannerBot</b>

Create stunning <b>anime banners</b> in seconds.

✨ HD Wallpapers  
⚡ Ultra Fast Generation  
🎨 Pro Templates  
🧠 Smart Text Engine  

<b>Tap CREATE BANNER to begin.</b>
"""

    # 🔥 FETCH WALLPAPER
    wallpaper = await anime_api.get_anime_wallpaper()

    if wallpaper:
        photo = BufferedInputFile(
            wallpaper,
            filename="wallpaper.jpg"
        )

        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    logger.info(f"User {user.id} started bot")


# ================= HELP =================

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.answer()

    text = """
<b>📖 BannerBot Help</b>

🎨 CREATE → Generate banners  
📱 Templates → Ready designs  
📊 Stats → Bot usage  

<b>Powered by @LastPerson07</b>
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
    ])

    await safe_edit(callback.message, text, kb)


# ================= HOME =================

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

    text = """
<b>🏠 Welcome Back</b>

Ready to create another banner?
"""

    await safe_edit(callback.message, text, kb)


# ================= STATS =================

@router.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    await callback.answer()

    try:
        stats = await db.LastPerson07_get_stats()
    except:
        stats = {
            "total_users": 0,
            "total_banners": 0,
            "active_24h": 0
        }

    text = f"""
<b>📊 Bot Stats</b>

👥 Users: <code>{stats['total_users']}</code>
🖼 Banners: <code>{stats['total_banners']}</code>
🔥 Active: <code>{stats['active_24h']}</code>
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
    ])

    await safe_edit(callback.message, text, kb)

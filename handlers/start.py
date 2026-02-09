from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from loguru import logger
from pathlib import Path
import asyncio
from database.mongo import db

router = Router()

# ✅ PROPER ESCAPING FUNCTION
def escape_markdown_v2(text: str) -> str:
    """Escape ALL MarkdownV2 special characters"""
    chars_to_escape = r'_*[]()~`>#+-=|{}.!'
    for char in chars_to_escape:
        text = text.replace(char, f'\\{char}')
    return text

@router.message(Command("start"))
async def LastPerson07_start(message: Message):
    """✅ FIXED Start handler - NO ESCAPING ERRORS"""
    try:
        user_id = message.from_user.id
        
        # Track user
        await db.LastPerson07_upsert_user(
            user_id, 
            message.from_user.username or "",
            message.from_user.first_name or "User"
        )
        
        # Logo (plain text - NO Markdown)
        logo_path = Path("assets/logo.txt")
        if logo_path.exists():
            try:
                logo = logo_path.read_text(encoding="utf-8").strip()
                if logo:
                    await message.answer(logo)
                    await asyncio.sleep(1)
            except:
                pass
        
        # ✅ MAIN MENU - PROPERLY ESCAPED
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
            [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
            [InlineKeyboardButton(text="❓ HELP", callback_data="help")]
        ])
        
        # ✅ NO SPECIAL CHARS - HTML FORMAT
        caption = """
🚀 <b>LastPerson07x-BannerBot v3.1</b>

✨ Professional Anime Banners

✅ Free unlimited usage
✅ Real anime wallpapers  
✅ Pro templates included
✅ HD quality (1080x1920)
✅ Custom text effects

<b>Click CREATE BANNER to start!</b>
        """.strip()
        
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        logger.info(f"✅ User {user_id} started bot")
        
    except Exception as e:
        logger.error(f"❌ Start error: {e}")
        # ✅ FALLBACK - Plain text
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")]
        ])
        await message.answer(
            "🚀 BannerBot Started!\n\nClick CREATE BANNER to make anime banners!",
            reply_markup=kb
        )

@router.callback_query(F.data == "help")
async def LastPerson07_help(callback: CallbackQuery):
    """✅ FIXED Help - HTML format"""
    try:
        await callback.answer("📖")
        
        text = """
📖 <b>LastPerson07x-BannerBot Help</b>

🎨 <b>CREATE</b> - Make custom banners
📱 <b>TEMPLATES</b> - Pro samples  
📊 <b>STATS</b> - Bot statistics

<b>Features:</b>
• Real anime wallpapers
• Professional text effects
• HD export (1080x1920)
• Instant generation

<b>Admin:</b> /admin, /ban_user, /unban_user

Made by @LastPerson07
        """.strip()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Help error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "home")
async def LastPerson07_home(callback: CallbackQuery):
    """✅ FIXED Home"""
    try:
        await callback.answer("🏠")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
            [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
            [InlineKeyboardButton(text="❓ HELP", callback_data="help")]
        ])
        
        text = """
🚀 <b>LastPerson07x-BannerBot v3.1</b>

✨ Professional Anime Banners

✅ HD Quality
✅ Anime Wallpapers  
✅ Pro Templates
✅ Custom Text

<b>Click CREATE BANNER!</b>
        """.strip()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Home error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "templates")
async def LastPerson07_templates(callback: CallbackQuery):
    """✅ FIXED Templates"""
    try:
        await callback.answer("📱")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ BTH S5 E125", callback_data="template:1")],
            [InlineKeyboardButton(text="✝️ The Chosen", callback_data="template:2")],
            [InlineKeyboardButton(text="⚔️ BTH S5 E124", callback_data="template:3")],
            [InlineKeyboardButton(text="⚔️ BTH S5 E123", callback_data="template:4")],
            [],
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        text = """
📱 <b>SELECT TEMPLATE</b>

Choose your favorite style:
        """.strip()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Templates error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "stats")
async def LastPerson07_stats(callback: CallbackQuery):
    """✅ FIXED Stats"""
    try:
        await callback.answer("📊")
        
        # Safe stats
        try:
            stats = await db.LastPerson07_get_stats()
        except:
            stats = {"total_users": 0, "total_banners": 0, "active_24h": 0}
        
        text = f"""
📊 <b>Bot Statistics</b>

👥 Users: <code>{stats['total_users']}</code>
🖼️ Banners: <code>{stats['total_banners']:,}</code>
🔥 Active 24h: <code>{stats['active_24h']}</code>

<b>Powered by @LastPerson07</b>
        """.strip()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        await callback.answer("❌ Error", show_alert=True)

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command  # ✅ FIXED: CommandStart → Command("start")
from loguru import logger
from pathlib import Path
from database.mongo import db  # ✅ Added for user tracking

router = Router()

@router.message(Command("start"))
async def LastPerson07_start(message: Message):
    """✅ WORKING Start handler"""
    try:
        user_id = message.from_user.id
        
        # Track user
        await db.LastPerson07_upsert_user(
            user_id, 
            message.from_user.username or "",
            message.from_user.first_name or "User"
        )
        
        # Try to load logo
        logo = ""
        logo_path = Path("assets/logo.txt")
        if logo_path.exists():
            try:
                logo = logo_path.read_text(encoding="utf-8")
            except:
                pass
        
        # Send logo first (if exists)
        if logo.strip():
            try:
                await message.answer(
                    f"```\n{logo}\n```", 
                    parse_mode="MarkdownV2"  # ✅ FIXED MarkdownV2
                )
                await asyncio.sleep(1)  # Small delay for better UX
            except:
                pass
        
        # Main welcome message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
            [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
            [InlineKeyboardButton(text="❓ HELP", callback_data="help")]
        ])
        
        caption = """
🚀 *LastPerson07x-BannerBot v3.1*

*✨ Professional Anime Banners*

✅ Free unlimited usage
✅ Real anime wallpapers
✅ Pro templates included  
✅ HD quality \\(1080x1920\\)
✅ Custom text effects

*Click CREATE BANNER to start!*
        """.strip()
        
        await message.answer(caption, parse_mode="MarkdownV2", reply_markup=keyboard)
        logger.info(f"✅ User {user_id} started bot")
        
    except Exception as e:
        logger.error(f"❌ Start error: {e}")
        # Fallback message
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")]
        ])
        await message.answer(
            "🚀 *BannerBot Started!*\n\nClick CREATE BANNER to make anime banners!", 
            parse_mode="MarkdownV2", 
            reply_markup=kb
        )

@router.callback_query(F.data == "help")
async def LastPerson07_help(callback: CallbackQuery):
    """Help handler"""
    try:
        await callback.answer("📖")
        
        text = """
📖 *LastPerson07x-BannerBot Help*

🎨 *CREATE* \\- Make custom banners
📱 *TEMPLATES* \\- Pro samples
📊 *STATS* \\- Bot statistics

*Features:*
• Real anime wallpapers
• Professional text effects
• HD export \\(1080x1920\\)
• Instant generation

*Admin:* /admin, /ban\\_user, /unban\\_user

Made by @LastPerson07
        """.strip()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Help error: {e}")
        await callback.answer("❌ Error loading help", show_alert=True)

@router.callback_query(F.data == "home")
async def LastPerson07_home(callback: CallbackQuery):
    """Home handler"""
    try:
        await callback.answer("🏠")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
            [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
            [InlineKeyboardButton(text="❓ HELP", callback_data="help")]
        ])
        
        caption = """
🚀 *LastPerson07x-BannerBot v3.1*

*✨ Professional Anime Banners*

✅ HD Quality
✅ Anime Wallpapers
✅ Pro Templates
✅ Custom Text

*Click CREATE BANNER!*
        """.strip()
        
        await callback.message.edit_text(caption, parse_mode="MarkdownV2", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Home error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "templates")
async def LastPerson07_templates(callback: CallbackQuery):
    """Templates handler"""
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
📱 *SELECT TEMPLATE*

Choose your favorite style:
        """.strip()
        
        await callback.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Templates error: {e}")
        await callback.answer("❌ Error loading templates", show_alert=True)

@router.callback_query(F.data == "stats")
async def LastPerson07_stats(callback: CallbackQuery):
    """Stats handler"""
    try:
        await callback.answer("📊")
        
        # Safe stats fetch
        try:
            stats = await db.LastPerson07_get_stats()
        except:
            stats = {"total_users": 0, "total_banners": 0, "active_24h": 0}
        
        text = f"""
📊 *Bot Statistics*

👥 Users: `{stats['total_users']}`
🖼️ Banners: `{stats['total_banners']:,}`
🔥 Active 24h: `{stats['active_24h']}`

*Powered by @LastPerson07*
        """.strip()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        await callback.answer("❌ Error loading stats", show_alert=True)

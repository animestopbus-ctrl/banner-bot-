from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from loguru import logger
from pathlib import Path

router = Router()

@router.message(CommandStart())
async def LastPerson07_start(message: Message):
    """Start handler"""
    try:
        user_id = message.from_user.id
        
        # Try to load logo
        logo = ""
        logo_path = Path("assets/logo.txt")
        if logo_path.exists():
            try:
                with open(logo_path, "r", encoding="utf-8") as f:
                    logo = f.read()
            except:
                pass
        
        # Send logo if available
        if logo:
            try:
                await message.answer(f"```\n{logo}\n```", parse_mode="Markdown")
            except:
                pass
        
        # Main menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 CREATE BANNER", callback_data="create")],
            [InlineKeyboardButton(text="📱 TEMPLATES", callback_data="templates")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
            [InlineKeyboardButton(text="❓ HELP", callback_data="help")]
        ])
        
        caption = """
🚀 **LastPerson07x-BannerBot v3.0**

> Create professional anime banners in seconds!

✅ Free unlimited usage
✅ Pro templates included  
✅ HD quality (1080x1920)
✅ Custom text support

**Ready to create?**
        """
        
        await message.answer(caption, parse_mode="Markdown", reply_markup=keyboard)
        logger.info(f"✅ User {user_id} started bot")
        
    except Exception as e:
        logger.error(f"Start error: {e}")
        await message.answer("❌ Error starting bot. Try again!")

@router.callback_query(F.data == "help")
async def LastPerson07_help(callback: CallbackQuery):
    """Help handler"""
    try:
        await callback.answer("📖")
        
        text = """
📖 **LastPerson07x-BannerBot Help**

🎨 **CREATE** - Make custom banners with your text
📱 **TEMPLATES** - Choose from professional samples
📊 **STATS** - View bot statistics
❓ **HELP** - This message

**Features:**
• Anime backgrounds
• Professional effects
• Custom text overlay
• HD export (1080x1920)
• Instant generation

**Admin Commands:**
/admin - Admin panel
/ban_user <id> - Ban user
/unban_user <id> - Unban user

Made with ❤️ by @LastPerson07
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK TO MENU", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Help error: {e}")
        await callback.answer("❌ Error", show_alert=True)

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
🚀 **LastPerson07x-BannerBot v3.0**

> Create professional anime banners in seconds!
        """
        
        await callback.message.edit_text(caption, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Home error: {e}")
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
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        text = "📱 **SELECT TEMPLATE**\n\nChoose from professional samples:"
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Templates error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "stats")
async def LastPerson07_stats(callback: CallbackQuery):
    """Stats handler"""
    try:
        await callback.answer("📊")
        
        from database.mongo import db
        stats = await db.LastPerson07_get_stats()
        
        text = f"""
📊 **LastPerson07x-BannerBot Statistics**

👥 Total Users: `{stats['total_users']}`
🖼️ Total Banners: `{stats['total_banners']:,}`
🔥 Active 24h: `{stats['active_24h']}`

> Professional banner generator by LastPerson07
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 BACK", callback_data="home")]
        ])
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await callback.answer("❌ Error", show_alert=True)

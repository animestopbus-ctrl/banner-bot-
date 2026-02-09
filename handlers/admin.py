# handlers/admin.py
from aiogram import Router
from aiogram.types import Message, InputFile
from aiogram.filters import Command
from config import config
from database import mongo  # type: ignore
from database.mongo import db
from loguru import logger
from pathlib import Path
from typing import Optional
import asyncio
import io
import os

router = Router()


def is_admin(user_id: int) -> bool:
    """Check admin membership using config.ADMIN_IDS safely."""
    try:
        return user_id in getattr(config, "ADMIN_IDS", [])
    except Exception:
        return False


@router.message(Command("admin"))
async def LastPerson07_admin_panel(message: Message):
    """Admin panel - shows stats + available commands"""
    try:
        uid = message.from_user.id
        if not is_admin(uid):
            await message.answer("🔒 Admin only")
            return

        # fetch stats (safe)
        try:
            stats = await db.get_stats()
        except Exception as e:
            logger.warning(f"Failed to fetch stats: {e}")
            stats = {"total_users": 0, "total_banners": 0, "active_24h": 0}

        text = (
            "<b>🔨 ADMIN PANEL - LastPerson07</b>\n\n"
            "<b>📊 Bot Statistics:</b>\n"
            f"• Total Users: <code>{stats['total_users']}</code>\n"
            f"• Total Banners: <code>{stats['total_banners']:,}</code>\n"
            f"• Active 24h: <code>{stats['active_24h']}</code>\n\n"
            "<b>Available Commands:</b>\n"
            "/ban_user &lt;user_id&gt; - Ban a user\n"
            "/unban_user &lt;user_id&gt; - Unban a user\n"
            "/logs - View recent logs (last 200 lines)\n"
            "/search_user &lt;username|user_id&gt; - Search user\n\n"
            "<b>Example:</b>\n"
            "<code>/ban_user 123456789</code>"
        )

        await message.answer(text, parse_mode="HTML")
        logger.info(f"Admin {uid} accessed admin panel")

    except Exception as e:
        logger.exception(f"Admin panel error: {e}")
        await message.answer("❌ Error accessing admin panel")


# ---------------- BAN ---------------- #
@router.message(Command("ban_user"))
async def LastPerson07_ban(message: Message):
    """Ban a user: /ban_user <user_id> [reason]"""
    try:
        uid = message.from_user.id
        if not is_admin(uid):
            await message.answer("🔒 Admin only")
            return

        parts = message.text.strip().split(maxsplit=2)
        if len(parts) < 2:
            await message.answer("❌ Usage: /ban_user <user_id> [reason]")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("❌ Invalid user ID")
            return

        reason = parts[2].strip() if len(parts) > 2 else "Admin ban"

        try:
            await db.ban_user(target_id, uid, reason)
            await message.answer(
                f"✅ User <code>{target_id}</code> has been banned.\n\nReason: {reason}",
                parse_mode="HTML"
            )
            logger.info(f"Admin {uid} banned user {target_id} | {reason}")
        except Exception as e:
            logger.exception(f"Ban error: {e}")
            await message.answer("❌ Error banning user")

    except Exception as e:
        logger.exception(f"Ban command failure: {e}")
        await message.answer("❌ Unexpected error while processing ban")


# ---------------- UNBAN ---------------- #
@router.message(Command("unban_user"))
async def LastPerson07_unban(message: Message):
    """Unban a user: /unban_user <user_id>"""
    try:
        uid = message.from_user.id
        if not is_admin(uid):
            await message.answer("🔒 Admin only")
            return

        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ Usage: /unban_user <user_id>")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("❌ Invalid user ID")
            return

        try:
            await db.unban_user(target_id)
            await message.answer(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
            logger.info(f"Admin {uid} unbanned user {target_id}")
        except Exception as e:
            logger.exception(f"Unban error: {e}")
            await message.answer("❌ Error unbanning user")

    except Exception as e:
        logger.exception(f"Unban command failure: {e}")
        await message.answer("❌ Unexpected error while processing unban")


# ---------------- LOGS ---------------- #
def tail_file(path: Path, lines: int = 200) -> str:
    """Return last `lines` lines from a file efficiently."""
    try:
        with path.open("rb") as f:
            avg_line_len = 200
            to_read = lines * avg_line_len
            try:
                f.seek(-to_read, os.SEEK_END)
            except OSError:
                f.seek(0)
            data = f.read().decode(errors="replace")
            splitted = data.splitlines()
            return "\n".join(splitted[-lines:])
    except Exception:
        return "Failed to read log file."


@router.message(Command("logs"))
async def LastPerson07_view_logs(message: Message):
    """Send recent logs to admin (last 200 lines or as file if large)."""
    try:
        uid = message.from_user.id
        if not is_admin(uid):
            await message.answer("🔒 Admin only")
            return

        log_path = getattr(config, "LOGS_DIR", None)
        if not log_path:
            await message.answer("❌ Log directory not configured.")
            return

        log_file = Path(log_path) / "bot.log"
        if not log_file.exists():
            await message.answer("❌ Log file not found.")
            return

        # If file is small send as text, otherwise send as file
        max_inline_size = 4000  # chars
        last_lines = tail_file(log_file, lines=200)

        if len(last_lines) <= max_inline_size:
            await message.answer(f"<b>Recent Logs (last 200 lines)</b>\n\n<pre>{last_lines}</pre>", parse_mode="HTML")
        else:
            # send as file
            try:
                await message.answer_document(InputFile(path_or_bytesio=str(log_file), filename="bot.log"))
            except Exception:
                # fallback: stream bytes
                try:
                    content = log_file.read_bytes()
                    await message.answer_document(InputFile(io.BytesIO(content), filename="bot.log"))
                except Exception as e:
                    logger.exception(f"Failed to send log file: {e}")
                    await message.answer("❌ Failed to send log file.")

    except Exception as e:
        logger.exception(f"Logs error: {e}")
        await message.answer("❌ Error retrieving logs")


# ---------------- SEARCH USER ---------------- #
@router.message(Command("search_user"))
async def LastPerson07_search_user(message: Message):
    """
    Search user by numeric user_id or username.
    Usage:
        /search_user 123456789
        /search_user someusername
        /search_user @someusername
    """
    try:
        uid = message.from_user.id
        if not is_admin(uid):
            await message.answer("🔒 Admin only")
            return

        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ Usage: /search_user <username|user_id>")
            return

        query = parts[1].strip()

        # try numeric id first
        user: Optional[dict] = None
        if query.isdigit():
            try:
                user = await db.get_user(int(query))
            except Exception as e:
                logger.warning(f"get_user by id failed: {e}")

        if not user:
            # username search (strip leading @)
            if query.startswith("@"):
                query = query[1:]

            try:
                # ensure DB connected and perform username lookup directly
                # using direct collection query as helper
                await db._ensure_connected()
                user = await db.db.users.find_one({"username": query})
            except Exception as e:
                logger.exception(f"Username search failed: {e}")
                user = None

        if not user:
            await message.answer("❌ User not found.")
            return

        # format user info
        user_id = user.get("user_id") or user.get("_id")
        username = user.get("username", "—")
        first_name = user.get("first_name", "—")
        banners = user.get("banners_generated", 0)
        created_at = user.get("created_at")
        last_active = user.get("last_active")

        info = (
            f"<b>User Info</b>\n"
            f"• ID: <code>{user_id}</code>\n"
            f"• Username: @{username}\n"
            f"• Name: {first_name}\n"
            f"• Banners: {banners}\n"
            f"• Created: {created_at}\n"
            f"• Last active: {last_active}\n"
        )

        await message.answer(info, parse_mode="HTML")

    except Exception as e:
        logger.exception(f"Search_user error: {e}")
        await message.answer("❌ Error searching user")

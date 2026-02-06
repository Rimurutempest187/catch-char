#!/usr/bin/env python3
# coding: utf-8
"""
Catch Character Bot - Robust main.py
- Async-safe DB injection
- Typed ContextTypes
- Admin decorator supports commands and callback queries
- Centralized error handling & logging
- Startup/shutdown hooks
- Detailed admin notifications
"""
import os
import logging
import traceback
from functools import wraps
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from modules.db import Database
from modules import summon, shop, drop, admin
from modules.shop import buy_callback

load_dotenv()

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set in environment")

ADMIN_IDS = []
_raw_admins = os.getenv("ADMIN_IDS", "").strip()
if _raw_admins:
    for part in _raw_admins.split(","):
        part = part.strip()
        if part:
            try:
                ADMIN_IDS.append(int(part))
            except ValueError:
                print(f"Warning: invalid ADMIN_IDS entry: {part}")

DB_PATH = os.getenv("DB_PATH", "bot.db")
LOG_PATH = os.getenv("LOG_PATH", "bot.log")

# --- Logging ---
logger = logging.getLogger("catchbot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# console
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# file
fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)

# --- Helper decorators ---
def admin_only(func):
    """Decorator to restrict access to admins (supports commands and callbacks)."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = getattr(update.effective_user, "id", None)
        if user_id not in ADMIN_IDS:
            msg = update.effective_message or getattr(update.callback_query, "message", None)
            if msg:
                await msg.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def with_db(func, db):
    """Decorator to inject database into handler safely (works for commands and callbacks)."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, db=db, *args, **kwargs)
        except Exception as e:
            # Log
            logger.exception("Error in handler %s", func.__name__)
            # Reply safely
            msg = update.effective_message or getattr(update.callback_query, "message", None)
            if msg:
                await msg.reply_text("An internal error occurred. The admin has been notified.")
            # Notify admins
            tb = traceback.format_exc()
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"Error in handler `{func.__name__}`:\n<pre>{tb}</pre>",
                        parse_mode="HTML"
                    )
                except Exception:
                    logger.exception("Failed to notify admin %s", admin_id)
    return wrapper

# --- Commands ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Catch Character Bot!\nCommands:\n"
        "/summon - summon a character\n"
        "/shop - view shop\n"
        "/simulate_drop - simulate a character drop\n"
        "/backup - admin only"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /start to see all commands.\nContact admin for more info."
    )

# --- Main ---
async def main():
    db = Database(DB_PATH)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- Startup / Shutdown hooks ---
    async def on_startup(app):
        try:
            await db.connect()
            logger.info("Database connected")
        except Exception:
            logger.exception("Database connection failed")

    async def on_shutdown(app):
        try:
            await db.close()
            logger.info("Database closed")
        except Exception:
            logger.exception("Database closing failed")

    # --- Error handler ---
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception("Unhandled exception")
        tb = traceback.format_exc()
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"Unhandled exception:\n<pre>{tb}</pre>",
                    parse_mode="HTML"
                )
            except Exception:
                logger.exception("Failed to notify admin %s", admin_id)

    app.add_error_handler(error_handler)

    # --- Register command handlers ---
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("summon", with_db(summon.summon_command, db)))
    app.add_handler(CommandHandler("shop", with_db(shop.shop_command, db)))
    app.add_handler(CommandHandler("simulate_drop", with_db(drop.simulate_drop, db)))
    app.add_handler(CommandHandler("backup", admin_only(with_db(admin.backup_command, db))))

    # --- CallbackQuery handler (shop buttons) ---
    app.add_handler(CallbackQueryHandler(with_db(buy_callback, db)))

    # --- Run bot ---
    try:
        await app.initialize()
        await on_startup(app)
        await app.start()
        await app.updater.start_polling()
        logger.info("Bot started")
        await app.idle()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    except Exception:
        logger.exception("Unexpected exception in main")
    finally:
        await on_shutdown(app)
        try:
            await app.stop()
        except Exception:
            pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

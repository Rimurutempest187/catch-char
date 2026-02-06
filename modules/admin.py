import os
import shutil
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

BACKUPS_DIR = Path(__file__).resolve().parents[1] / "backups" / "db_backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db_path: str, admin_ids=None):
    uid = update.effective_user.id
    if admin_ids and uid not in admin_ids:
        await update.message.reply_text("You are not authorized to run this command.")
        return

    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / f"bot_db_backup_{now}.db"
    shutil.copy(db_path, dest)
    await update.message.reply_text(f"Backup created: {dest.name}")

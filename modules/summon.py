from telegram import Update
from telegram.ext import ContextTypes
from modules.utils import load_json, weighted_choice

CHARS_PATH = "data/characters.json"

async def summon_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db=None):
    user_id = update.effective_user.id
    chars = load_json(CHARS_PATH)
    picked = weighted_choice(chars, "weight")
    if not picked:
        await update.message.reply_text("No characters available.")
        return

    # store in db
    await db.add_character(user_id, picked)

    text = f"You summoned **{picked['name']}**! (Rarity: {picked.get('rarity', 'unknown')})"
    if picked.get("description"):
        text += "\n" + picked["description"]

    await update.message.reply_text(text, parse_mode="Markdown")

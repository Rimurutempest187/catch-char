import random
from telegram import Update
from telegram.ext import ContextTypes
from modules.utils import load_json, weighted_choice

CHARS_PATH = "data/characters.json"

async def simulate_drop(update: Update, context: ContextTypes.DEFAULT_TYPE, db=None):
    # For testing: simulate a random drop and award to the invoking user
    user_id = update.effective_user.id
    chars = load_json(CHARS_PATH)
    picked = weighted_choice(chars, "weight")
    if not picked:
        await update.message.reply_text("No characters available for drop.")
        return
    await db.add_character(user_id, picked)
    await update.message.reply_text(f"A wild card dropped: {picked['name']}! It's yours.")

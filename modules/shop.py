from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.utils import load_json

SHOP_PATH = "data/shop_items.json"

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db=None):
    items = load_json(SHOP_PATH)
    if not items:
        await update.message.reply_text("Shop is empty.")
        return

    keyboard = []
    text_lines = []
    for it in items:
        text_lines.append(f"{it['name']} — {it['price']} coins\n{it.get('description','')}")
        keyboard.append([InlineKeyboardButton(f"Buy {it['name']}", callback_data=f"buy:{it['id']}")])

    await update.message.reply_text("\n\n".join(text_lines), reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_callback(update, context, db=None):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("buy:"):
        return
    item_id = data.split(":", 1)[1]
    items = load_json(SHOP_PATH)
    item = next((x for x in items if x['id'] == item_id), None)
    if not item:
        await query.edit_message_text("Item not found.")
        return

    user_id = query.from_user.id
    coins = await db.get_coins(user_id)
    if coins < item['price']:
        await query.answer("Not enough coins", show_alert=True)
        return

    await db.add_coins(user_id, -item['price'])
    await query.answer("Purchase successful!", show_alert=True)

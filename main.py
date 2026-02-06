import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from modules.db import Database
from modules import summon, shop, drop, admin
from modules.shop import buy_callback

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = os.getenv("DB_PATH", "bot.db")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
)
logger = logging.getLogger(__name__)

async def main():
    db = Database(DB_PATH)
    await db.connect()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Basic commands
    async def start(update, context):
        await update.message.reply_text("Welcome to Catch Character Bot! Use /summon to summon a character.")

    # Wrap handlers so they can access db
    async def summon_wrap(update, context):
        await summon.summon_command(update, context, db=db)

    async def shop_wrap(update, context):
        await shop.shop_command(update, context, db=db)

    async def drop_wrap(update, context):
        await drop.simulate_drop(update, context, db=db)

    async def backup_wrap(update, context):
        await admin.backup_command(update, context, db_path=DB_PATH, admin_ids=ADMIN_IDS)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summon", summon_wrap))
    app.add_handler(CommandHandler("shop", shop_wrap))
    app.add_handler(CommandHandler("simulate_drop", drop_wrap))
    app.add_handler(CommandHandler("backup", backup_wrap))

    # callback for buy buttons
    app.add_handler(CallbackQueryHandler(lambda u, c: buy_callback(u, c, db=db)))

    # Run the bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("Bot started. Press Ctrl+C to stop.")
    try:
        await app.idle()
    finally:
        await db.close()
        await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

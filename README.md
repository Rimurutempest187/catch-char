# Catch Character Telegram Bot - Starter


1. Copy `.env.example` to `.env` and set your `BOT_TOKEN`.
2. `pip install -r requirements.txt`
3. Run: `python main.py`


Commands:
- /start — welcome message
- /summon — summons a random character and gives it to the user
- /shop — view shop items
- /simulate_drop — simulate a character drop (for testing)
- /backup — admin only: creates a DB backup in `backups/db_backups/`


Notes:
- The bot will create `bot.db` automatically.
- Update `data/characters.json` and `data/shop_items.json` to add your content.

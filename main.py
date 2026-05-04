import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from bot.handlers import (
    help_handler,
    match_handler,
    start_handler,
    summarize_handler,
)
from config import config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("summarize", summarize_handler))
    app.add_handler(CommandHandler("match", match_handler))

    logging.getLogger(__name__).info("Bot started — polling for updates")
    app.run_polling()


if __name__ == "__main__":
    main()

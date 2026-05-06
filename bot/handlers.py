import logging
from functools import wraps
from typing import Awaitable, Callable

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from ai.matcher import match_properties
from ai.summarizer import summarize_chat
from bot.formatters import format_matches, format_summary
from config import config
from data.sheets import get_listings

logger = logging.getLogger(__name__)


WELCOME_MESSAGE = (
    "Hello! 🏠 Real Estate AI Assistant\n\n"
    "Available commands:\n"
    "/summarize — Summarize a customer chat\n"
    "/match — Find matching properties\n"
    "/help — How to use"
)

HELP_MESSAGE = (
    "🤖 *How to use*\n\n"
    "*/summarize*\n"
    "Paste a customer chat to get a structured lead summary.\n\n"
    "Example:\n"
    "/summarize\n"
    "Hi, I'm looking for a 1BR near BTS Asok...\n\n"
    "*/match*\n"
    "Describe what the client needs to find matching properties.\n\n"
    "Example:\n"
    "/match BTS Asok 25k 1BR pet-friendly parking"
)

SUMMARIZE_USAGE = (
    "Please paste the customer chat after the command.\n\n"
    "Example:\n/summarize\nHi, I'm looking for a 1BR near BTS Asok..."
)

MATCH_USAGE = (
    "Please describe what the client needs after the command.\n\n"
    "Example:\n/match BTS Asok 25k 1BR pet-friendly"
)

OPENAI_ERROR = (
    "Something went wrong while processing your request. "
    "Please try again in a moment."
)

SHEETS_ERROR = "Could not load property data. Please contact your administrator."


Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def restricted(handler: Handler) -> Handler:
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        command = handler.__name__.replace("_handler", "")
        if user is None or user.id not in config.ALLOWED_IDS:
            uid = user.id if user else "?"
            logger.warning("access denied: /%s from user %s", command, uid)
            if update.message is not None:
                await update.message.reply_text("Access denied.")
            return
        logger.info("/%s from user %s", command, user.id)
        await handler(update, context)

    return wrapper


def _extract_argument(update: Update) -> str:
    message = update.message
    if message is None or message.text is None:
        return ""
    parts = message.text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


async def _send_typing(update: Update) -> None:
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
    except Exception:
        logger.warning("send_action failed; continuing without typing indicator")


@restricted
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


@restricted
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)


@restricted
async def summarize_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    raw_chat = _extract_argument(update)
    if not raw_chat:
        await update.message.reply_text(SUMMARIZE_USAGE)
        return

    await _send_typing(update)

    try:
        data = summarize_chat(raw_chat)
        text = format_summary(data)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("summarize_handler failed")
        await update.message.reply_text(OPENAI_ERROR)


@restricted
async def match_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    requirement = _extract_argument(update)
    if not requirement:
        await update.message.reply_text(MATCH_USAGE)
        return

    await _send_typing(update)

    try:
        listings = get_listings()
    except Exception:
        logger.exception("get_listings failed")
        await update.message.reply_text(SHEETS_ERROR)
        return

    logger.info("loaded %d available listings", len(listings))

    try:
        result = match_properties(requirement, listings)
        logger.info("matcher returned %d matches", len(result.get("matches") or []))
        text = format_matches(result, listings)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("match_handler failed")
        await update.message.reply_text(OPENAI_ERROR)

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

WEBAPP_URL = os.environ.get("WEBAPP_URL", "http://localhost:3000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user else "Коллега"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🩺 Открыть тренажёр",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]])
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "Это AI-тренажёр по медицинским регламентам.\n\n"
        "Нажмите кнопку ниже, чтобы начать тренировку или управлять документами:",
        reply_markup=keyboard,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Как пользоваться:*\n\n"
        "1. Нажмите /start чтобы открыть приложение\n"
        "2. *Врачи* видят список доступных тренировок\n"
        "3. *Администраторы* могут загружать регламенты и генерировать задания\n\n"
        "По вопросам обращайтесь к администратору.",
        parse_mode="Markdown",
    )


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    logger.info(f"Бот запущен. WebApp URL: {WEBAPP_URL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

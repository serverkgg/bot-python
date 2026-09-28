import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hi {update.effective_user.first_name}! Your bot is running.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)


async def announce(app: Application) -> None:
    print(f"Logged in as @{app.bot.username}", flush=True)


def main() -> None:
    app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).post_init(announce).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Bot is polling for messages")
    app.run_polling()


if __name__ == "__main__":
    main()

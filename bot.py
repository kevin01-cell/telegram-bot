import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Get the token from environment variable (Render)
TOKEN = os.getenv("BOT_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! 🎥\n\nHere’s a sample product for sale:\n\n"
        "👉 [Click here to view](https://example.com/video)\n\n"
        "To purchase, reply with your phone number 📱"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
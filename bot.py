import os
import threading
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests

# ========================
# ENV VARIABLES (set these in Render dashboard)
# ========================
TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
PAYHERO_BUSINESS_ID = os.getenv("1206")  # Your PayHero business ID
PAYHERO_AUTH = os.getenv("Basic XleABExPtMle7JLebns4:BPwcBFbVf5b4ZFr0dslCCO3PnfCMZeL6IgwxJg1m")  # Base64 auth string ("Basic dGVzdDpzZWNyZXQ=")

# Store users temporarily (phone -> telegram_id)
user_data = {}

# Telegram bot
bot_app = Application.builder().token(TOKEN).build()

# Flask app for PayHero webhook
flask_app = Flask(__name__)


# ========================
# Telegram Bot Handlers
# ========================

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📱 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "🎥 Welcome to Movie Store!\n\n"
        "👉 Today’s product: *Sample Video*\n\n"
        "Please share your phone number to continue 📱",
        reply_markup=reply_markup
    )


# Handle phone number
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number
    user_id = update.message.from_user.id

    # Save mapping
    user_data[phone] = user_id

    # Create PayHero payment request
    amount = 10  # fixed price for now
    url = "https://api.payhero.co.ke/pay"

    headers = {
        "Authorization": PAYHERO-AUTH,
        "Content-Type": "application/json"
    }

    payload = {
        "business": PAYHERO_BUSINESS_ID,
        "amount": amount,
        "phone": phone
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        res = r.json()
        print("PayHero response:", res)

        if res.get("success"):
            await update.message.reply_text(
                f"✅ Got your number: {phone}\n\n"
                f"💵 Please complete payment of KES {amount}.\n"
                f"You should see an M-Pesa prompt shortly."
            )
        else:
            await update.message.reply_text("⚠️ Payment request failed. Try again later.")

    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("❌ Error connecting to payment gateway.")


# ========================
# PayHero Webhook
# ========================
@flask_app.route("/payhero-webhook", methods=["POST"])
def payhero_webhook():
    data = request.json
    print("Webhook received:", data)

    phone = data.get("phone")
    status = data.get("status")

    if status == "SUCCESS" and phone in user_data:
        user_id = user_data[phone]
        bot_app.create_task(send_video(user_id))

    return {"ok": True}


# Send video after payment
async def send_video(user_id):
    await bot_app.bot.send_message(chat_id=user_id, text="✅ Payment confirmed! Delivering your movie 🎬")
    await bot_app.bot.send_video(chat_id=user_id, video=open("video.mp4", "rb"))


# ========================
# Run both Flask + Telegram Bot
# ========================
def run():
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    threading.Thread(target=lambda: bot_app.run_polling()).start()
    flask_app.run(host="0.0.0.0", port=10000)


if __name__ == "__main__":
    run()

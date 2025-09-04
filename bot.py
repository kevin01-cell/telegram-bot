import os
import logging
import requests
from flask import Flask, request
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ---------------- CONFIG ----------------
TELEGRAM_TOKEN = os.getenv("8212437895:AAEDfDgl9L6N2Jm7sgz-fAHnlWS-MU8sKdw")
PAYHERO_API_KEY = os.getenv("https://app.payhero.co.ke/lipwa/1206")
PAYHERO_BASE_URL = "https://payhero.co.ke/api/v2/payments"  # check latest docs
MOVIE_FILE_ID = "<https://t.me/c/1805614988/17120>"

# Flask app for PayHero callback
app = Flask(__name__)

# ---------------- TELEGRAM BOT ----------------
logging.basicConfig(level=logging.INFO)

application = Application.builder().token(TELEGRAM_TOKEN).build()

# Step 1: Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Karibu! Click below to get the movie.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎬 Buy Movie", callback_data="buy_movie")]]
        )
    )

# Step 2: Button click → ask phone number
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_movie":
        kb = [[KeyboardButton("Send Phone Number", request_contact=True)]]
        await query.message.reply_text(
            "Please share your M-Pesa phone number:",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
        )

# Step 3: Get phone number → initiate PayHero STK push
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    # Call PayHero API
    payload = {
        "api_key": PAYHERO_API_KEY,
        "amount": 10,  # movie price
        "phone": phone,
        "reference": f"movie_{update.effective_user.id}",
        "callback_url": "https://telegram-bot-kyb8.onrender.com"
    }
    r = requests.post(PAYHERO_BASE_URL, json=payload)
    res = r.json()

    if res.get("status") == "success":
        await update.message.reply_text("✅ STK push sent! Enter M-Pesa PIN to complete.")
    else:
        await update.message.reply_text("❌ Failed to initiate payment. Try again later.")

# ---------------- PAYHERO CALLBACK ----------------
@app.route("/payhero-callback", methods=["POST"])
def payhero_callback():
    data = request.json
    logging.info(f"PayHero callback: {data}")

    if data.get("status") == "paid":
        ref = data.get("reference")  # e.g. movie_userid
        user_id = int(ref.split("_")[1])

        # Send movie after payment
        application.bot.send_message(
            chat_id=user_id,
            text="🎉 Payment successful! Here’s your movie:"
        )
        application.bot.send_document(chat_id=user_id, document=MOVIE_FILE_ID)

    return {"ok": True}

# ---------------- MAIN ----------------
if __name__ == "__main__":
    # Run bot polling in background
    import threading

    def run_bot():
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.CONTACT | filters.TEXT, phone_handler))
        application.run_polling()

    t = threading.Thread(target=run_bot)
    t.start()

    # Run Flask app for callback
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

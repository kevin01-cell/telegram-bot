import os
import logging
import requests
from flask import Flask, request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
import threading

# ---------------- CONFIG ----------------
TELEGRAM_TOKEN = "8311436073:AAH_90W-fdG_d2bv96Qpuoe7ax4bw5QY1Z8"  # your bot token
PAYHERO_API_KEY = os.getenv("PAYHERO_API_KEY")  # set this in Render dashboard
PAYHERO_BASE_URL = "https://payhero.co.ke/api/v2/payments"
MOVIE_FILE_ID = "BQACAgQAAxkBAAIBGWYlS5..."  # replace with real file_id

# Flask app for PayHero callback
app = Flask(__name__)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------- TELEGRAM BOT ----------------
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Step 1: /start → show button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Karibu! Click below to buy the movie 🎬",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎬 Buy Movie", callback_data="buy_movie")]]
        )
    )

# Step 2: Button click → ask phone number
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_movie":
        kb = [[KeyboardButton("📱 Send Phone Number", request_contact=True)]]
        await query.message.reply_text(
            "Please share your M-Pesa phone number:",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
        )

# Step 3: Receive phone number → initiate PayHero STK push
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    payload = {
        "api_key": PAYHERO_API_KEY,
        "amount": 10,  # movie price
        "phone": phone,
        "reference": f"movie_{update.effective_user.id}",
        "callback_url": "https://telegram-bot-kyb8.onrender.com/payhero-callback"
    }
    try:
        r = requests.post(PAYHERO_BASE_URL, json=payload)
        res = r.json()
        logging.info(f"PayHero response: {res}")
    except Exception as e:
        logging.error(f"Error calling PayHero: {e}")
        await update.message.reply_text("⚠️ Error connecting to payment system.")
        return

    if res.get("status") == "success":
        await update.message.reply_text("✅ STK push sent! Enter your M-Pesa PIN to complete payment.")
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

        application.bot.send_message(
            chat_id=user_id,
            text="🎉 Payment successful! Here’s your movie:"
        )
        application.bot.send_document(chat_id=user_id, document=MOVIE_FILE_ID)

    return {"ok": True}

# ---------------- MAIN ----------------
def run_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.CONTACT | filters.TEXT, phone_handler))
    application.run_polling()

if __name__ == "__main__":
    # Run Telegram bot in background thread
    t = threading.Thread(target=run_bot)
    t.start()

    # Run Flask app for PayHero callbacks
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

import logging
import sys
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, WEBHOOK_URL, PORT
from downloader import get_formats, download_video
from utils import safe_remove

logging.basicConfig(level=logging.INFO)

app = FastAPI()

user_data = {}

# ---------------- BOT INIT ----------------
if BOT_TOKEN == "MISSING_TOKEN":
    print("❌ BOT_TOKEN missing! Bot will not start webhook mode.")
    USE_WEBHOOK = False
else:
    USE_WEBHOOK = True

bot = ApplicationBuilder().token(BOT_TOKEN if USE_WEBHOOK else "0:dummy").build()

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send video link 🎬")

# ---------------- MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    user_data[chat_id] = url

    formats = get_formats(url)

    buttons = [
        [InlineKeyboardButton(f["q"], callback_data=f"v|{f['id']}")]
        for f in formats
    ]

    await update.message.reply_text(
        "Choose quality:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- BUTTON ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_data.get(chat_id)

    await query.edit_message_text("Downloading... ⏬")

    try:
        format_id = query.data.split("|")[1]
        file_path = download_video(url, format_id)

        await context.bot.send_document(chat_id, open(file_path, "rb"))
        safe_remove(file_path)

    except Exception as e:
        await context.bot.send_message(chat_id, f"Error: {e}")

# ---------------- ROUTES ----------------
bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot.add_handler(CallbackQueryHandler(button))

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot.bot)
    await bot.process_update(update)
    return {"ok": True}

@app.get("/")
async def home():
    return {
        "status": "V9 running",
        "webhook_mode": USE_WEBHOOK
    }

# ---------------- STARTUP SAFE ----------------
@app.on_event("startup")
async def startup():
    await bot.initialize()

    if USE_WEBHOOK and WEBHOOK_URL:
        await bot.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        print("✅ Webhook enabled")
    else:
        print("⚠️ Running without webhook (safe mode)")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
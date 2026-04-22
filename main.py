import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import BOT_TOKEN, WEBHOOK_URL, PORT

logging.basicConfig(level=logging.INFO)

app = FastAPI()

user_data = {}

# ---------------- SAFE CHECK ----------------
if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing - bot disabled")
    bot_app = None
else:
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video link 🎬")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id] = update.message.text
    await update.message.reply_text("Received link ✔️")

# ---------------- REGISTER ----------------
if bot_app:
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def webhook(req: Request):
    if not bot_app:
        return {"error": "bot not running"}

    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# ---------------- HOME ----------------
@app.get("/")
async def home():
    return {
        "status": "V9 STABLE RUNNING",
        "webhook": bool(WEBHOOK_URL)
    }

# ---------------- STARTUP SAFE ----------------
@app.on_event("startup")
async def startup():
    try:
        if bot_app:
            await bot_app.initialize()

            if WEBHOOK_URL:
                await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
                print("✅ Webhook enabled")
            else:
                print("⚠️ No WEBHOOK_URL - running without webhook")

    except Exception as e:
        print("❌ Startup error:", e)

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

from datetime import datetime
import os
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.ext import Dispatcher

# =================== CONFIG ===================
BOT_TOKEN = os.getenv("7796994967:AAFrF9Dl9eFn8EtHnbKGpXjkt2XJXBuCo6M")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
BASE_URL = os.getenv("https://telegram-bot-2-xvs8.onrender.com")  # เช่น https://your-service.onrender.com
# ==============================================

user_data = {}

app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# ====== Telegram Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🟢 เข้างาน", "🔴 เลิกงาน"],
        ["🚻 เข้าห้องน้ำ", "🔙 กลับที่นั่ง"],
        ["📋 ดูประวัติ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 ยินดีต้อนรับ! กรุณาเลือกเมนู:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_id not in user_data:
        user_data[user_id] = {
            "start_time": None,
            "bathroom_time": None,
            "bathroom_msg_id": None,
            "last_action": None
        }

    data = user_data[user_id]

    if text != "🟢 เข้างาน" and data["start_time"] is None:
        await update.message.reply_text("⚠️ กรุณากด 'เข้างาน' ก่อนใช้งานเมนูอื่น", reply_to_message_id=update.message.message_id)
        return

    if text == "🟢 เข้างาน":
        if data["last_action"] == "🟢 เข้างาน" or data["start_time"]:
            await update.message.reply_text("❗ คุณเข้างานแล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"]:
            await update.message.reply_text("❌ คุณยังไม่กลับจากห้องน้ำ", reply_to_message_id=data["bathroom_msg_id"])
            return
        data["start_time"] = datetime.now()
        data["last_action"] = "🟢 เข้างาน"
        await update.message.reply_text(f"✅ คุณ {user.first_name} เข้างานแล้ว {now}", reply_to_message_id=update.message.message_id)

    elif text == "🔴 เลิกงาน":
        if data["last_action"] == "🔴 เลิกงาน" or not data["start_time"]:
            await update.message.reply_text("❗ ไม่สามารถเลิกงานได้", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"]:
            await update.message.reply_text("❌ คุณยังไม่กลับจากห้องน้ำ", reply_to_message_id=data["bathroom_msg_id"])
            return
        end_time = datetime.now()
        total_duration = end_time - data["start_time"]
        if data["bathroom_time"]:
            total_duration -= (end_time - data["bathroom_time"])
        await update.message.reply_text(
            f"📋 คุณ {user.first_name} เลิกงานแล้ว\nรวมเวลาทำงาน: {str(total_duration).split('.')[0]}",
            reply_to_message_id=update.message.message_id
        )
        data.update(start_time=None, bathroom_time=None, bathroom_msg_id=None, last_action="🔴 เลิกงาน")

    elif text == "🚻 เข้าห้องน้ำ":
        if data["bathroom_time"]:
            await update.message.reply_text("❗ คุณเข้าห้องน้ำอยู่แล้ว", reply_to_message_id=data["bathroom_msg_id"])
            return
        data["bathroom_time"] = datetime.now()
        sent = await update.message.reply_text(f"🚻 คุณ {user.first_name} เข้าห้องน้ำ {now}", reply_to_message_id=update.message.message_id)
        data["bathroom_msg_id"] = sent.message_id
        data["last_action"] = "🚻 เข้าห้องน้ำ"

    elif text == "🔙 กลับที่นั่ง":
        if not data["bathroom_time"]:
            await update.message.reply_text("❌ คุณยังไม่ได้เข้าห้องน้ำ", reply_to_message_id=update.message.message_id)
            return
        back_time = datetime.now()
        bathroom_duration = back_time - data["bathroom_time"]
        await update.message.reply_text(
            f"🔙 คุณ {user.first_name} กลับจากห้องน้ำ ใช้เวลา: {str(bathroom_duration).split('.')[0]}",
            reply_to_message_id=data["bathroom_msg_id"]
        )
        data.update(bathroom_time=None, bathroom_msg_id=None, last_action="🔙 กลับที่นั่ง")

    elif text == "📋 ดูประวัติ":
        await update.message.reply_text("📋 ฟีเจอร์ดูประวัติยังไม่เปิดใช้งาน")
        data["last_action"] = "📋 ดูประวัติ"

    else:
        await update.message.reply_text("กรุณาเลือกเมนูจากปุ่มด้านล่าง")

# ====== Add handlers ======
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ====== Flask Routes ======
@app.route("/")
def index():
    return "🤖 Bot is live!"

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok"
    return "not allowed", 405

# ====== Setup Webhook ======
@app.before_first_request
def init_webhook():
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    application.bot.set_webhook(webhook_url)
    print(f"✅ Webhook set: {webhook_url}")

# ====== Run Flask ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

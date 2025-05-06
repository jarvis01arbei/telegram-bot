from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ข้อมูลผู้ใช้ทั้งหมด
user_data = {}

# เมนูเริ่มต้น
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🟢 เข้างาน", "🔴 เลิกงาน"],
        ["🚻 เข้าห้องน้ำ", "🔙 กลับที่นั่ง"],
        ["📋 ดูประวัติ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 ยินดีต้อนรับ! กรุณาเลือกเมนู:", reply_markup=reply_markup)

# ฟังก์ชันหลักสำหรับจัดการข้อความ
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
        if data["last_action"] == "🟢 เข้างาน":
            await update.message.reply_text("❗ คุณเข้างานแล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["start_time"] is not None:
            await update.message.reply_text("❗ คุณเข้างานแล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"] is not None:
            await update.message.reply_text("❌ คุณยังไม่กลับจากห้องน้ำ", reply_to_message_id=data["bathroom_msg_id"])
            return

        data["start_time"] = datetime.now()
        data["bathroom_time"] = None
        data["bathroom_msg_id"] = None
        data["last_action"] = "🟢 เข้างาน"

        await update.message.reply_text(f"✅ คุณ {user.first_name} เข้างานแล้ว {now}", reply_to_message_id=update.message.message_id)

    elif text == "🔴 เลิกงาน":
        if data["last_action"] == "🔴 เลิกงาน":
            await update.message.reply_text("❗ คุณเลิกงานแล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["start_time"] is None:
            await update.message.reply_text("❗ คุณยังไม่ได้เข้างาน", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"] is not None:
            await update.message.reply_text("❌ คุณยังไม่กลับจากห้องน้ำ", reply_to_message_id=data["bathroom_msg_id"])
            return

        end_time = datetime.now()
        total_duration = end_time - data["start_time"]

        if data["bathroom_time"]:
            bathroom_duration = end_time - data["bathroom_time"]
            total_duration -= bathroom_duration

        await update.message.reply_text(
            f"📋 คุณ {user.first_name} เลิกงานแล้ว\nรวมเวลาทำงาน: {str(total_duration).split('.')[0]}",
            reply_to_message_id=update.message.message_id
        )

        data["start_time"] = None
        data["bathroom_time"] = None
        data["bathroom_msg_id"] = None
        data["last_action"] = "🔴 เลิกงาน"

    elif text == "🚻 เข้าห้องน้ำ":
        if data["last_action"] == "🚻 เข้าห้องน้ำ":
            await update.message.reply_text("❗ คุณเข้าห้องน้ำอยู่แล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"] is not None:
            await update.message.reply_text("❌ คุณยังไม่กลับจากห้องน้ำ", reply_to_message_id=data["bathroom_msg_id"])
            return

        data["bathroom_time"] = datetime.now()
        sent = await update.message.reply_text(f"🚻 คุณ {user.first_name} เข้าห้องน้ำ {now}", reply_to_message_id=update.message.message_id)
        data["bathroom_msg_id"] = sent.message_id
        data["last_action"] = "🚻 เข้าห้องน้ำ"

    elif text == "🔙 กลับที่นั่ง":
        if data["last_action"] == "🔙 กลับที่นั่ง":
            await update.message.reply_text("❗ คุณกลับที่นั่งแล้ว ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        if data["bathroom_time"] is None:
            await update.message.reply_text("❌ คุณยังไม่ได้เข้าห้องน้ำ", reply_to_message_id=update.message.message_id)
            return

        back_time = datetime.now()
        bathroom_duration = back_time - data["bathroom_time"]
        await update.message.reply_text(
            f"🔙 คุณ {user.first_name} กลับจากห้องน้ำ ใช้เวลา: {str(bathroom_duration).split('.')[0]}",
            reply_to_message_id=data["bathroom_msg_id"]
        )

        data["bathroom_time"] = None
        data["bathroom_msg_id"] = None
        data["last_action"] = "🔙 กลับที่นั่ง"

    elif text == "📋 ดูประวัติ":
        if data["last_action"] == "📋 ดูประวัติ":
            await update.message.reply_text("❗ คุณเพิ่งดูประวัติไป ไม่สามารถกดซ้ำได้", reply_to_message_id=update.message.message_id)
            return
        await update.message.reply_text("📋 ฟีเจอร์ดูประวัติยังไม่เปิดใช้งาน")
        data["last_action"] = "📋 ดูประวัติ"

    else:
        await update.message.reply_text("กรุณาเลือกเมนูจากปุ่มด้านล่าง")

# เริ่มต้นบอท
if __name__ == "__main__":
    app = ApplicationBuilder().token("7796994967:AAFrF9Dl9eFn8EtHnbKGpXjkt2XJXBuCo6M").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

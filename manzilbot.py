from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

import asyncio
from datetime import datetime

TOKEN = "8375527745:AAE50nIvvlJg0nta_nZZMf5CmzSSxGy7ILQ"
ADMIN_ID = 8036404646

GROUPS = set()
user_state = {}
stats = {"sent": 0, "failed": 0}


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("🎯 Aksiya", callback_data="aksiya")],
            [InlineKeyboardButton("📅 Kunlik", callback_data="daily")],
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
        ]

        await update.message.reply_text(
            "👑 Admin panel",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("🌍 Travel botga xush kelibsiz!")


# ---------------- GROUP TRACK ----------------
async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        GROUPS.add(chat.id)


# ---------------- BUTTON ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        return

    if query.data in ["aksiya", "daily"]:
        user_state[user_id] = {"type": query.data, "step": "photo"}
        await query.message.reply_text("🖼 Banner rasm yuboring:")

    elif query.data == "stats":
        await query.message.reply_text(
            f"📊 Statistika\nYuborilgan: {stats['sent']}\nXatolik: {stats['failed']}"
        )

    elif query.data == "send_now":
        data = user_state.get(user_id)

        for g in GROUPS:
            try:
                await context.bot.send_photo(
                    chat_id=g,
                    photo=data["photo"],
                    caption=data["final_text"]
                )
                stats["sent"] += 1
            except:
                stats["failed"] += 1

        await query.message.reply_text("✅ Reklama darhol yuborildi!")

    elif query.data == "set_time":
        user_state[user_id]["step"] = "time"
        await query.message.reply_text("⏰ Vaqt kiriting (18:30):")


# ---------------- MESSAGE ----------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        return

    if user_id not in user_state:
        return

    data = user_state[user_id]
    step = data["step"]

    # PHOTO
    if step == "photo":
        if not update.message.photo:
            await update.message.reply_text("Iltimos rasm yuboring 🖼")
            return

        data["photo"] = update.message.photo[-1].file_id
        data["step"] = "yonalish"
        await update.message.reply_text("🌍 Yo‘nalish:")
        return

    if step == "yonalish":
        data["yonalish"] = update.message.text
        data["step"] = "paket"
        await update.message.reply_text("🏨 Paket:")
        return

    if step == "paket":
        data["paket"] = update.message.text
        data["step"] = "kun"
        await update.message.reply_text("📆 Kun:")
        return

    if step == "kun":
        data["kun"] = update.message.text

        if data["type"] == "aksiya":
            data["step"] = "chegirma"
            await update.message.reply_text("💸 Chegirma:")
        else:
            data["step"] = "inclusion"
            await update.message.reply_text("🎁 Paket ichida:")
        return

    if step == "chegirma":
        data["chegirma"] = update.message.text
        data["step"] = "muddat"
        await update.message.reply_text("⏳ Muddat:")
        return

    if step == "muddat":
        data["muddat"] = update.message.text
        data["step"] = "inclusion"
        await update.message.reply_text("🎁 Paket ichida:")
        return

    if step == "inclusion":
        data["inclusion"] = update.message.text
        data["step"] = "phone"
        await update.message.reply_text("📞 Telefon:")
        return

    if step == "phone":
        data["phone"] = update.message.text
        data["step"] = "telegram"
        await update.message.reply_text("💬 Telegram:")
        return

    if step == "telegram":
        data["telegram"] = update.message.text
        data["step"] = "instagram"
        await update.message.reply_text("📸 Instagram:")
        return

    if step == "instagram":
        data["instagram"] = update.message.text

        text = f"""
🌍 {data['yonalish']}
🏨 {data['paket']}
📆 {data['kun']} kun

🎁 {data['inclusion']}

📞 {data['phone']}
💬 {data['telegram']}
📸 {data['instagram']}
"""

        if data["type"] == "aksiya":
            text = "🔥 AKSIYA 🔥\n\n" + text + f"\n💸 {data['chegirma']}%\n⏳ {data['muddat']}"

        data["final_text"] = text

        keyboard = [
            [InlineKeyboardButton("🔥 Hozir yuborish", callback_data="send_now")],
            [InlineKeyboardButton("⏰ Vaqt belgilash", callback_data="set_time")]
        ]

        await update.message.reply_photo(
            photo=data["photo"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # TIME
    if step == "time":
        try:
            h, m = map(int, update.message.text.split(":"))

            asyncio.create_task(schedule_send(
                data["final_text"],
                data["photo"],
                h,
                m
            ))

            await update.message.reply_text("✅ Vaqt saqlandi!")

        except:
            await update.message.reply_text("❌ Format noto‘g‘ri (18:30 yozing)")


# ---------------- SCHEDULE ----------------
async def schedule_send(text, photo, hour, minute):

    sent = False

    while True:
        now = datetime.now()

        if not sent and now.hour == hour and now.minute == minute:

            for g in GROUPS:
                try:
                    await app.bot.send_photo(g, photo=photo, caption=text)
                    stats["sent"] += 1
                except:
                    stats["failed"] += 1

            sent = True

        await asyncio.sleep(60)


# ---------------- MAIN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ChatType.GROUPS, track_groups))
app.add_handler(MessageHandler(filters.ChatType.PRIVATE, message_handler))

print("BOT STARTED")
app.run_polling()
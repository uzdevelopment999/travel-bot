from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

import asyncio
import os
from datetime import datetime

# 🔐 TOKEN — Renderdan olinadi (GitHubga yozilmaydi)
TOKEN = os.getenv("TOKEN")

# 👑 ADMIN ID
ADMIN_ID = 8036404646

# 📢 GROUPLAR (keyin qo‘shasan)
GROUPS = []

# 💾 TEMP DATA
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
        await update.message.reply_text(
            "🌍 Xush kelibsiz!\n"
            "✈️ Sayohat bot\n\n"
            "📍 Yo‘nalishlar\n"
            "🏨 Paketlar\n"
            "📞 Admin bilan bog‘lanish"
        )


# ---------------- BUTTON ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        await query.message.reply_text("❌ Sizda ruxsat yo‘q")
        return

    if query.data in ["aksiya", "daily"]:
        user_state[user_id] = {"type": query.data, "step": "photo"}
        await query.message.reply_text("🖼 Banner rasm yuboring:")

    elif query.data == "stats":
        await query.message.reply_text(
            f"📊 Statistika\n\n"
            f"Yuborilgan: {stats['sent']}\n"
            f"Xatolar: {stats['failed']}"
        )

    elif query.data == "setup_send":
        keyboard = [
            [InlineKeyboardButton("📅 Har kuni", callback_data="send_daily")],
            [InlineKeyboardButton("📆 Haftalik", callback_data="send_weekly")],
            [InlineKeyboardButton("🗓 Oylik", callback_data="send_monthly")]
        ]

        await query.message.reply_text(
            "⏰ Yuborish vaqti:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("send_"):
        user_state[user_id]["step"] = "time"
        await query.message.reply_text("⏰ Vaqt kiriting (16:45)")


# ---------------- MESSAGE ----------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        return

    if update.effective_chat.type != "private":
        return

    if user_id not in user_state:
        return

    data = user_state[user_id]
    step = data["step"]

    # PHOTO
    if step == "photo" and update.message.photo:
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
        await update.message.reply_text("📆 Necha kun:")
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
        await update.message.reply_text("⏳ Aksiya muddati:")
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

    # FINAL
    if step == "instagram":
        data["instagram"] = update.message.text

        if data["type"] == "aksiya":
            text = f"""
🔥 AKSIYA 🔥

🌍 {data['yonalish']}
🏨 {data['paket']}
📆 {data['kun']} kun
💸 Chegirma: {data['chegirma']}%
⏳ Muddat: {data['muddat']}

🎁 {data['inclusion']}

📞 {data['phone']}
💬 {data['telegram']}
📸 {data['instagram']}
"""
        else:
            text = f"""
🌍 {data['yonalish']}
🏨 {data['paket']}
📆 {data['kun']} kun

🎁 {data['inclusion']}

📞 {data['phone']}
💬 {data['telegram']}
📸 {data['instagram']}
"""

        data["final_text"] = text

        keyboard = [
            [InlineKeyboardButton("📤 Yuborish sozlash", callback_data="setup_send")]
        ]

        await update.message.reply_photo(
            photo=data["photo"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # TIME
    if step == "time":
        h, m = map(int, update.message.text.split(":"))

        asyncio.create_task(schedule_send(
            data["final_text"],
            data["photo"],
            h,
            m
        ))

        await update.message.reply_text("✅ Saqlandi!")


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

        await asyncio.sleep(5)


# ---------------- MAIN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, message_handler))

print("BOT STARTED")
app.run_polling()
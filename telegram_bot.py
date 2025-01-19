from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
# Bot tokeni va guruh ID
BOT_TOKEN = "7514443189:AAHXwgj871d9UWzPYgFRg2K7BDgQqAu9-zA"  # Tokeningizni kiriting
GROUP_CHAT_ID = -4648326817  # Guruh ID

# Holatlar
NAME, PHONE, AGE, COURSE, FACULTY, MENU, ASK_QUESTION, SEND_CV = range(8)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ismingizni bilsam bo'ladimi?")
    return NAME

# Ismni qabul qilish
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    keyboard = [
        [KeyboardButton("📱 Share my number", request_contact=True)],
    ]
    await update.message.reply_text(
        "Iltimos, telefon raqamingizni ulashing.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return PHONE

# Telefon raqamini qabul qilish
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.contact.phone_number if update.message.contact else update.message.text
    await update.message.reply_text("Yoshingiz nechida?")
    return AGE

# Yoshni qabul qilish
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Nechinchi kurssiz?")
    return COURSE

# Kursni qabul qilish
async def get_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["course"] = update.message.text
    await update.message.reply_text("Qaysi fakultetda tahsil olasiz?")
    return FACULTY

# Fakultetni qabul qilish va menyuni ko'rsatish
async def get_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["faculty"] = update.message.text

    keyboard = [
        [KeyboardButton("Savol va takliflar yo'llash")],
    ]
    await update.message.reply_text(
        "Menyuni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return MENU

# Savolni qabul qilish va guruhga yuborish
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Savolingizni yozing:", reply_markup=ReplyKeyboardRemove())
    return ASK_QUESTION

# Savolni guruhga jo'natish
async def send_question_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    question = update.message.text

    # Guruhga foydalanuvchi ma'lumotlari bilan savolni yuborish
    forwarded_message = await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"Yangi savol kelib tushdi:\n\n"
             f"*Foydalanuvchi:* {context.user_data['name']} (@{user.username})\n"
             f"*Yoshi:* {context.user_data['age']}\n"
             f"*Kurs:* {context.user_data['course']}\n"
             f"*Fakulteti:* {context.user_data['faculty']}\n"
             f"*Telefon:* {context.user_data['phone']}\n\n"
             f"*Savol:* {question}",
        parse_mode="Markdown",
    )

    # Xabar ID va foydalanuvchi IDni saqlash
    context.bot_data[forwarded_message.message_id] = user.id

    # Foydalanuvchiga tasdiq yuborish
    await update.message.reply_text("Savolingiz guruhga yuborildi!")
    await update.message.reply_text("Endi, iltimos, CV'ingizni yuboring (faqat PDF formatda).")
    return SEND_CV

# CV yuborishni so'rash
async def ask_for_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.document:
        # Check if the MIME type is PDF
        if update.message.document.mime_type == 'application/pdf':
            # Handle the PDF file (you can save it or process it as needed)
            await update.message.reply_text("CV qabul qilindi!")
            return ConversationHandler.END
        else:
            await update.message.reply_text("Iltimos, faqat PDF formatda CV yuboring.")
            return SEND_CV
    else:
        await update.message.reply_text("Iltimos, CV yuboring (faqat PDF formatda).")
        return SEND_CV

# Admin reply qilib foydalanuvchiga javob berish
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        original_message_id = update.message.reply_to_message.message_id

        # Reply qilingan xabardan foydalanuvchi IDni olish
        user_id = context.bot_data.get(original_message_id)
        if user_id:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Admin javobi:\n\n{update.message.text}",
            )
        else:
            await update.message.reply_text("Foydalanuvchini aniqlab bo'lmadi.")
    else:
        await update.message.reply_text("Foydalanuvchiga reply qilib javob bering.")

# Bekor qilish komandasi
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Asosiy funksiya
async def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Delete any existing webhook
    await application.bot.delete_webhook()  # Ensure you await this here

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            FACULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_faculty)],
            MENU: [
                MessageHandler(
                    filters.Regex("^(Savol va takliflar yo'llash)$"), ask_question
                )
            ],
            ASK_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_question_to_group)
            ],
            SEND_CV: [
                MessageHandler(filters.Document.ALL, ask_for_cv),  # Check if a document is sent
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ALL & filters.REPLY, reply_to_user))

    # Run polling after clearing any existing webhooks
    await application.run_polling(drop_pending_updates=True)

# Avoid using asyncio.run(main()) in environments where event loop is already running
if __name__ == "__main__":
    import sys
    from asyncio import get_event_loop
    loop = get_event_loop()
    loop.run_until_complete(main())  # Run the bot without asyncio.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Ensure to run the main function as an async task

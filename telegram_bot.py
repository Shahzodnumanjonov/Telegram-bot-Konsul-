from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "your_bot_token_here"
GROUP_CHAT_ID = -1234567890  # Replace with your group chat ID

# States
NAME, AGE, COURSE, FACULTY, MENU, ASK_QUESTION, CV = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ismingizni bilsam bo'ladimi?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Yoshingiz nechida?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Nechinchi kurssiz?")
    return COURSE

async def get_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["course"] = update.message.text
    await update.message.reply_text("Qaysi fakultetda tahsil olasiz?")
    return FACULTY

async def get_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["faculty"] = update.message.text
    keyboard = [[KeyboardButton("Savol va takliflar yo'llash")]]
    await update.message.reply_text("Menyuni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MENU

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Savolingizni yozing:", reply_markup=ReplyKeyboardRemove())
    return ASK_QUESTION

async def send_question_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    question = update.message.text
    forwarded_message = await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"Yangi savol kelib tushdi:\n\n"
             f"*Foydalanuvchi:* {context.user_data['name']} (@{user.username})\n"
             f"*Yoshi:* {context.user_data['age']}\n"
             f"*Kurs:* {context.user_data['course']}\n"
             f"*Fakulteti:* {context.user_data['faculty']}\n\n"
             f"*Savol:* {question}",
        parse_mode="Markdown",
    )
    context.bot_data[forwarded_message.message_id] = user.id
    await update.message.reply_text("Savolingiz guruhga yuborildi!")
    return MENU

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        original_message_id = update.message.reply_to_message.message_id
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

async def ask_for_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Iltimos, CVingizni PDF formatda yuboring.\n(Format: PDF)")
    return CV

async def handle_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.document:
        file = update.message.document
        if file.mime_type == "application/pdf":
            await context.bot.send_document(
                chat_id=GROUP_CHAT_ID,
                document=file.file_id,
                caption=f"Yangi CV:\nFoydalanuvchi: {context.user_data['name']} (@{update.effective_user.username})"
            )
            await update.message.reply_text("CV guruhga yuborildi!")
            return MENU
        else:
            await update.message.reply_text("Iltimos, faqat PDF formatidagi faylni yuboring.")
    return CV

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            FACULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_faculty)],
            MENU: [MessageHandler(filters.Regex("^(Savol va takliflar yo'llash)$"), ask_question)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_question_to_group)],
            CV: [MessageHandler(filters.MIME_TYPE("application/pdf"), handle_cv)],  # Correct MIME type filter
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ALL & filters.REPLY, reply_to_user))

    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

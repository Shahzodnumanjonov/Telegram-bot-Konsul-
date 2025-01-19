import gspread
from oauth2client.service_account import ServiceAccountCredentials
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

# Token va guruh ID
BOT_TOKEN = "7514443189:AAHXwgj871d9UWzPYgFRg2K7BDgQqAu9-zA"  # O'zingizning tokeningizni kiriting
GROUP_CHAT_ID = -4648326817  # Guruh ID

# Holatlar
NAME, AGE, COURSE, FACULTY, MENU, ASK_QUESTION = range(6)

# Google Sheets API orqali ulanish
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("path_to_your_credentials.json", scope)
    client = gspread.authorize(creds)
    return client

# Savolni Google Sheetsga saqlash
def save_question_to_sheets(name, age, course, faculty, question):
    client = connect_to_google_sheets()
    sheet = client.open("Savollar").sheet1  # "Savollar" - siz yaratgan Google Sheetning nomi
    sheet.append_row([name, age, course, faculty, question])

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ismingizni bilsam bo'ladimi?")
    return NAME

# Ismni qabul qilish
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
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
    user = update.effective_user
    await update.message.reply_text("Savolingizni yozing:", reply_markup=ReplyKeyboardRemove())
    return ASK_QUESTION

# Savolni guruhga jo'natish va saqlash
async def send_question_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    question = update.message.text

    # Google Sheetsga saqlash
    save_question_to_sheets(
        context.user_data["name"],
        context.user_data["age"],
        context.user_data["course"],
        context.user_data["faculty"],
        question
    )

    # Guruhga foydalanuvchi ma'lumotlari bilan savolni yuborish
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

    # Xabar ID va foydalanuvchi ID saqlash
    context.bot_data[forwarded_message.message_id] = user.id

    # Foydalanuvchiga tasdiq yuborish
    await update.message.reply_text("Savolingiz guruhga yuborildi!")
    return MENU

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
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Reply handlerni qo'shish
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ALL & filters.REPLY, reply_to_user))

    # Botni ishga tushirish
    application.run_polling()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

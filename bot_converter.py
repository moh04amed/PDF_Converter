import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

# ---------------- CONFIG ---------------- #
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@riyad_Elsalihin"  # ⚠️ change this

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "pdfs"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

DOCUMENT_EXTENSIONS = (".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv")
PPT_EXTENSIONS = (".ppt", ".pptx")

# ---------------- SUBSCRIPTION CHECK ---------------- #

async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ I Joined", callback_data="recheck")]
    ])

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        await update.message.reply_text(
            "🔒 *Access Restricted*\n\n"
            "You must join our channel to use this bot 👇",
            parse_mode="Markdown",
            reply_markup=join_keyboard()
        )
        return

    await update.message.reply_text(
        "📄 *PDF Ninja*\n\n"
        "Send me a document and I will convert it to PDF.\n\n"
        "✅ Word / Excel / PowerPoint / Text / CSV",
        parse_mode="Markdown"
    )

# ---------------- CALLBACK ---------------- #

async def recheck_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_subscribed(update, context):
        await query.message.edit_text(
            "✅ *Subscription verified!*\n\n"
            "You can now send files to convert 📄",
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ *Not subscribed yet*\n\n"
            "Please join the channel first 👇",
            parse_mode="Markdown",
            reply_markup=join_keyboard()
        )

# ---------------- CONVERSION ---------------- #

def convert_with_libreoffice(input_path: str) -> str:
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", OUTPUT_DIR,
            input_path,
        ],
        check=True,
    )
    filename = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(OUTPUT_DIR, f"{filename}.pdf")

# ---------------- HANDLER ---------------- #

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        await update.message.reply_text(
            "🔒 You must subscribe first 👇",
            reply_markup=join_keyboard()
        )
        return

    if not update.message.document:
        await update.message.reply_text("❌ No document detected.")
        return

    file = update.message.document
    filename = file.file_name.lower()
    input_path = os.path.join(DOWNLOAD_DIR, file.file_name)

    tg_file = await file.get_file()
    file_bytes = await tg_file.download_as_bytearray()
    with open(input_path, "wb") as f:
        f.write(file_bytes)

    await update.message.reply_text("⏳ Converting, please wait...")

    try:
        if filename.endswith(DOCUMENT_EXTENSIONS + PPT_EXTENSIONS):
            pdf_path = convert_with_libreoffice(input_path)
        else:
            await update.message.reply_text("❌ Unsupported file type.")
            return

        await update.message.reply_document(
            open(pdf_path, "rb"),
            caption="✅ Conversion complete!"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(recheck_subscription, pattern="recheck"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🤖 PDF Ninja is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


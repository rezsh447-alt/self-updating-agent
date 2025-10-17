from safe_exec import safe_run_code
import os, json, glob, shutil, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from self_editor import append_snippet, safe_replace_in_file
from github_updater import git_commit_and_push
from ai_agent import ai_agent
from session_manager import advanced_session_manager

with open("config.json","r",encoding="utf-8") as f:
    CFG = json.load(f)

ADMIN_ID = str(os.getenv("ADMIN_ID") or CFG.get("ADMIN_ID",""))
USER_STATES = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری.")
        return

    keyboard = [
        [InlineKeyboardButton("📝 افزودن snippet", callback_data="mode_snippet")],
        [InlineKeyboardButton("🔧 جایگزینی کد", callback_data="mode_replace")],
        [InlineKeyboardButton("🤖 دستور AI", callback_data="ai_mode")],
        [InlineKeyboardButton("🧠 وضعیت حافظه", callback_data="memory_status")],
        [InlineKeyboardButton("❌ لغو حالت", callback_data="cancel_mode")]
    ]
    await update.message.reply_text(
        "🤖 Self-Updating AI Agent\n\nانتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری.")
        return

    # ایجاد سشن اگر وجود ندارد
    session = advanced_session_manager.get_current_session(user_id)
    if not session:
        advanced_session_manager.create_session(user_id, "چت عمومی")
        print(f"✅ سشن جدید ساخته شد برای کاربر {user_id}")

    text = update.message.text.strip()
    if text.lower().startswith("تست کن") or text.lower().startswith("اجرا") or "run" in text.lower():

        await update.message.reply_text("⚙️ در حال اجرای امن کد...")

        code_part = text.replace("تست کن", "").replace("اجرا", "").strip()

        if not code_part:

            await update.message.reply_text("❗ لطفاً کد پایتون رو بعد از عبارت بنویس.")

            return

        result = safe_run_code(code_part)

        await update.message.reply_text(result)

        return

    # دستورات مدیریتی
    if text.lower() in ['/menu', 'منو', 'menu']:
        await start(update, context)
        return

    if text.lower() in ['/cancel', 'cancel', 'لغو', 'خروج']:
        USER_STATES[user_id] = None
        await update.message.reply_text("✅ حالت ویژه لغو شد.")
        return

    # دستور وضعیت حافظه
    if text.lower() in ['/memory', 'حافظه', 'memory']:
        session_info = advanced_session_manager.get_current_session_info(user_id)
        await update.message.reply_text(f"🧠 وضعیت حافظه:\n{session_info}")
        return

    # اگر پیام با /ai شروع شد
    if text.startswith("/ai "):
        await ai_command(update, context)
        return

    # اگر پیام معمولی هست، مستقیماً به AI بفرست
    await ai_chat(update, context)

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ مستقیم به پیام‌های کاربر با AI"""
    user_id = str(update.message.from_user.id)
    user_message = update.message.text.strip()

    await update.message.reply_text("🤔 در حال پردازش...")

    # استفاده از AI برای پاسخ به پیام کاربر
    ai_response = ai_agent.chat_response(user_message, user_id)

    await update.message.reply_text(f"🤖 AI:\n{ai_response}")

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری.")
        return

    user_command = update.message.text.strip()

    if user_command.startswith("/ai "):
        command = user_command[4:].strip()
        await update.message.reply_text(f"🤔 در حال پردازش دستور: {command}")

        ai_response = ai_agent.analyze_command(command)

        try:
            lines = ai_response.strip().split('\n')
            file_name, marker, code = None, None, None

            for line in lines:
                if line.startswith("FILE:"):
                    file_name = line.split("FILE:")[1].strip()
                elif line.startswith("MARKER:"):
                    marker = line.split("MARKER:")[1].strip()
                elif line.startswith("CODE:"):
                    code = line.split("CODE:")[1].strip()

            if file_name and marker and code:
                res = append_snippet(file_name, marker, code)

                if res["changed"]:
                    result = git_commit_and_push(commit_message=f"ai: {command}", auto_push=True)

                    if result.get("ok"):
                        await update.message.reply_text(f"✅ دستور AI اجرا شد!\n📁 فایل: {file_name}\n🔄 در حال ریستارت...")
                        import sys
                        import os
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    else:
                        await update.message.reply_text(f"❌ خطا در push: {result.get('error')}")
                else:
                    await update.message.reply_text("ℹ️ تغییر اعمال نشد یا تکراری بود.")
            else:
                await update.message.reply_text(f"❌ پاسخ AI نامعتبر")

        except Exception as e:
            await update.message.reply_text(f"❌ خطا در اجرای دستور AI: {e}")

    else:
        await update.message.reply_text(
            "🤖 دستور AI\n\nفرمت: /ai [دستور]\n\nمثال:\n/ai اضافه کردن دکمه وضعیت"
        )

async def handle_snippet_mode(update: Update, text: str):
    try:
        parts = text.split('\n')
        if len(parts) < 3:
            await update.message.reply_text("❌ فرمت نادرست!")
            return

        file, marker, snippet = parts[0], parts[1], '\n'.join(parts[2:])
        res = append_snippet(file, marker, snippet)

        if res["changed"]:
            kb = [
                [InlineKeyboardButton("✅ Commit & Push", callback_data=f"push::{file}")],
                [InlineKeyboardButton("❌ Revert", callback_data=f"revert::{file}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
            ]
            await update.message.reply_text(f"✅ تغییر اعمال شد!\n📁 فایل: {file}", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text("ℹ️ تغییر اعمال نشد یا تکراری بود.")

        USER_STATES[str(update.message.from_user.id)] = None

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def handle_replace_mode(update: Update, text: str):
    try:
        parts = text.split('\n')
        if len(parts) < 3:
            await update.message.reply_text("❌ فرمت نادرست!")
            return

        file, pattern, replacement = parts[0], parts[1], '\n'.join(parts[2:])
        res = safe_replace_in_file(file, pattern, replacement)

        if res["changed"]:
            kb = [
                [InlineKeyboardButton("✅ Commit & Push", callback_data=f"push::{file}")],
                [InlineKeyboardButton("❌ Revert", callback_data=f"revert::{file}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
            ]
            await update.message.reply_text(f"✅ جایگزینی انجام شد!\n📁 فایل: {file}", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text("ℹ️ هیچ تغییری اعمال نشد.")

        USER_STATES[str(update.message.from_user.id)] = None

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ دسترسی ندارید.")
        return

    if data == "mode_snippet":
        USER_STATES[user_id] = 'snippet'
        await query.edit_message_text("📝 حالت افزودن snippet فعال شد\n\nلطفاً به این فرمت ارسال کن:\nفایل\nمارکر\nکد\n\nبرای لغو: cancel")

    elif data == "mode_replace":
        USER_STATES[user_id] = 'replace'
        await query.edit_message_text("🔧 حالت جایگزینی کد فعال شد\n\nلطفاً به این فرمت ارسال کن:\nفایل\nالگو\nجایگزین\n\nبرای لغو: cancel")

    elif data == "ai_mode":
        USER_STATES[user_id] = 'ai'
        await query.edit_message_text("🤖 حالت دستور AI فعال شد\n\nدستورات رو به این فرمت بفرست:\n/ai [دستور شما]\n\nمثال:\n/ai اضافه کردن دکمه وضعیت")

    elif data == "memory_status":
        session_info = advanced_session_manager.get_current_session_info(user_id)
        await query.edit_message_text(f"🧠 وضعیت حافظه:\n{session_info}")

    elif data == "cancel_mode":
        USER_STATES[user_id] = None
        await query.edit_message_text("✅ حالت ویژه لغو شد.")

    elif data == "back_to_menu":
        USER_STATES[user_id] = None
        keyboard = [
            [InlineKeyboardButton("📝 افزودن snippet", callback_data="mode_snippet")],
            [InlineKeyboardButton("🔧 جایگزینی کد", callback_data="mode_replace")],
            [InlineKeyboardButton("🤖 دستور AI", callback_data="ai_mode")],
            [InlineKeyboardButton("🧠 وضعیت حافظه", callback_data="memory_status")],
            [InlineKeyboardButton("❌ لغو حالت", callback_data="cancel_mode")]
        ]
        await query.edit_message_text("🤖 Self-Updating AI Agent\n\nانتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("push::"):
        file = data.split("::",1)[1]
        await query.edit_message_text("⏳ در حال commit و push ...")
        result = git_commit_and_push(commit_message=f"agent: edit {file}", auto_push=True)
        if result.get("ok"):
            await query.edit_message_text(f"✅ تغییرات push شد!\n{result.get('message','')}")
        else:
            await query.edit_message_text(f"❌ خطا در push:\n{str(result.get('error'))}")

    elif data.startswith("revert::"):
        file = data.split("::",1)[1]
        b = glob.glob("backup/" + os.path.basename(file) + ".*.bak")
        if not b:
            await query.edit_message_text("❌ هیچ بکاپی یافت نشد.")
            return
        latest = sorted(b)[-1]
        shutil.copy2(latest, file)
        await query.edit_message_text(f"⏪ فایل بازیابی شد از {latest}")

def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_TOKEN env var")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

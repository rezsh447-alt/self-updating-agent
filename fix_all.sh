#!/bin/bash
echo "🔧 در حال اصلاح ربات برای Termux..."

# ایجاد فایل اصلاح کننده
cat > fix_main.py << 'PYEOF'
import os

NEW_MAIN = '''import os
import time
import sys
from telegram_handler import run_bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

REQUIRED_ENV_VARS = ["TELEGRAM_TOKEN", "ADMIN_ID", "GEMINI_API_KEY"]

def check_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(f"❌ Environment variables missing: {', '.join(missing)}")
        return False
    return True

if __name__ == "__main__":
    if check_env_vars():
        print("🤖 Self-Updating Agent Started!")
        print("🔄 Starting bot...")
        try:
            run_bot()
        except KeyboardInterrupt:
            print("🛑 Bot stopped by user.")
        except Exception as e:
            print(f"❌ خطا: {e}")
    else:
        print("❌ لطفاً متغیرهای محیطی رو تنظیم کن")
'''

with open("main.py", "w", encoding="utf-8") as f:
    f.write(NEW_MAIN)
print("✅ main.py اصلاح شد")
PYEOF

# اصلاح main.py
python fix_main.py

# اصلاح telegram_handler.py برای اضافه کردن سشن
cat > fix_telegram.py << 'PYEOF'
import re

with open("telegram_handler.py", "r", encoding="utf-8") as f:
    content = f.read()

# پیدا کردن تابع handle_message و اضافه کردن کد سشن
old_pattern = r'async def handle_message\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):\s*\n\s*user_id = str\(update\.message\.from_user\.id\)'
new_code = '''async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری.")
        return

    # ایجاد سشن اگر وجود ندارد
    session = smart_session_manager.get_current_session(user_id)
    if not session:
        smart_session_manager.create_session(user_id, "چت عمومی")
        print(f"✅ سشن جدید ساخته شد برای کاربر {user_id}")

    text = update.message.text.strip()'''

new_content = re.sub(old_pattern, new_code, content)

with open("telegram_handler.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ telegram_handler.py اصلاح شد")
PYEOF

python fix_telegram.py

# پاک کردن فایل‌های موقت
rm -f fix_main.py fix_telegram.py

echo "🎯 تمام اصلاحات انجام شد!"
echo "🚀 حالا ربات رو اجرا کن:"
echo "python main.py"

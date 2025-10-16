#!/usr/bin/env python3
import os
import re

# اصلاح main.py
NEW_MAIN = '''import os
import time
import importlib
import traceback
import threading
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

REQUIRED_ENV_VARS = ["TELEGRAM_TOKEN", "ADMIN_ID", "GEMINI_API_KEY"]

def check_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(f"❌ Environment variables missing: {', '.join(missing)}")
        print("⚙️ لطفاً با دستور زیر تنظیم کن:")
        print("   export TELEGRAM_TOKEN='...'")
        print("   export ADMIN_ID='...'") 
        print("   export GEMINI_API_KEY='...'")
        return False
    return True

def run_bot():
    from telegram_handler import run_bot as telegram_run_bot
    
    def run_in_thread():
        try:
            print("🤖 Self-Updating Agent Started!")
            print("🔄 Starting bot...")
            telegram_run_bot()
        except Exception as e:
            print(f"❌ خطا در اجرای بات: {e}")
            traceback.print_exc()
    
    bot_thread = threading.Thread(target=run_in_thread, daemon=True)
    bot_thread.start()
    return bot_thread

def watch_for_changes(interval=5):
    file_timestamps = {}
    while True:
        try:
            changed = False
            for filename in os.listdir(BASE_DIR):
                if filename.endswith(".py"):
                    filepath = os.path.join(BASE_DIR, filename)
                    ts = os.path.getmtime(filepath)
                    if filename not in file_timestamps:
                        file_timestamps[filename] = ts
                    elif file_timestamps[filename] != ts:
                        file_timestamps[filename] = ts
                        print(f"♻️ تغییر شناسایی شد در: {filename}")
                        changed = True

            if changed:
                print("🔁 Reloading updated modules...")
                print("🔄 Restarting bot...")
                os.execv(sys.executable, [sys.executable] + sys.argv)

            time.sleep(interval)
        except KeyboardInterrupt:
            print("🛑 Agent stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ خطای غیرمنتظره در Watcher: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if check_env_vars():
        bot_thread = run_bot()
        print("👀 Watching for file changes...")
        watch_for_changes()
'''

def fix_main():
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(NEW_MAIN)
    print("✅ main.py اصلاح شد")

def fix_telegram():
    with open("telegram_handler.py", "r", encoding="utf-8") as f:
        content = f.read()
    
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
    
    pattern = r'(async def handle_message\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):)\s*\n\s*(user_id = str\(update\.message\.from_user\.id\))'
    new_content = re.sub(pattern, new_code, content)
    
    with open("telegram_handler.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ telegram_handler.py اصلاح شد")

if __name__ == "__main__":
    fix_main()
    fix_telegram()
    print("🎯 تمام اصلاحات انجام شد! حالا ربات رو اجرا کن:")
    print("python main.py")

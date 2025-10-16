import os
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

#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "🔧 در حال ساخت و تنظیم Safe Runner برای ربات..."

AGENT_DIR="$HOME/agent"
cd "$AGENT_DIR" || { echo "❌ مسیر agent پیدا نشد"; exit 1; }

# 1️⃣ ساخت فایل safe_exec.py
cat > safe_exec.py <<'PYCODE'
import json, subprocess, tempfile, os
from pathlib import Path

BASE_DIR = Path.home() / "agent"
RUNNER = BASE_DIR / "safe_runner.py"

def safe_run_code(code: str):
    """اجرای امن کد با safe_runner.py"""
    try:
        tmp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=BASE_DIR)
        job_data = {"files": {"main.py": code}}
        json.dump(job_data, open(tmp_json.name, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        result = subprocess.run(
            ["python3", str(RUNNER), tmp_json.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        os.unlink(tmp_json.name)
        if result.returncode != 0 and not result.stdout.strip():
            return f"❌ خطا در اجرا:\n{result.stderr[:800]}"
        return f"📤 نتیجه تست:\n{result.stdout[:1000]}"
    except subprocess.TimeoutExpired:
        return "⏱️ زمان اجرای کد بیش از حد مجاز بود (Timeout)"
    except Exception as e:
        return f"❌ خطا در اجرای امن: {e}"
PYCODE

# 2️⃣ افزودن import در telegram_handler.py
if ! grep -q "from safe_exec import safe_run_code" telegram_handler.py; then
    sed -i '1ifrom safe_exec import safe_run_code' telegram_handler.py
    echo "✅ import safe_exec اضافه شد"
else
    echo "ℹ️ import safe_exec قبلاً اضافه شده بود"
fi

# 3️⃣ افزودن منطق تست کد داخل handle_message
if ! grep -q "تست کن" telegram_handler.py; then
    sed -i '/text = update.message.text.strip()/a \
    if text.lower().startswith("تست کن") or text.lower().startswith("اجرا") or "run" in text.lower():\n\
        await update.message.reply_text("⚙️ در حال اجرای امن کد...")\n\
        code_part = text.replace("تست کن", "").replace("اجرا", "").strip()\n\
        if not code_part:\n\
            await update.message.reply_text("❗ لطفاً کد پایتون رو بعد از عبارت بنویس.")\n\
            return\n\
        result = safe_run_code(code_part)\n\
        await update.message.reply_text(result)\n\
        return' telegram_handler.py
    echo "✅ دستور اجرای امن به handle_message اضافه شد"
else
    echo "ℹ️ دستور تست قبلاً وجود دارد"
fi

# 4️⃣ پاکسازی و راه‌اندازی مجدد
echo "🔄 پاک‌سازی کش پایتون..."
rm -rf __pycache__ || true

echo "🚀 اجرای مجدد ربات با Safe Runner جدید..."
nohup python3 main.py > log.txt 2>&1 &

echo "✅ نصب و اتصال Safe Runner با موفقیت انجام شد!"
echo "📱 حالا در تلگرام بنویس: تست کن print('سلام از محیط ایمن!')"

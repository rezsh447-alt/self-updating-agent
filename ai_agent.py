import os
import requests
import datetime

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def analyze_command(self, user_command):
        """آنالیز دستور کاربر و تولید کد مناسب"""
        prompt = f"""
        تو یک دستیار برنامه‌نویس هستی. کاربر این دستور رو داده: "{user_command}"
        
        باید کد پایتون مناسب برای اضافه کردن این قابلیت به ربات تلگرام تولید کنی.
        
        مشخصات ربات:
        - از کتابخانه python-telegram-bot نسخه 20 استفاده می‌کنه
        - فایل‌های اصلی: telegram_handler.py, main.py, self_editor.py, github_updater.py
        - قابلیت ویرایش خودکار کد رو داره
        
        خروجی باید به این فرمت باشه:
        FILE: [نام فایل]
        MARKER: [مارکر در فایل]
        CODE: [کد پایتون]
        
        فقط خروجی خالص بده بدون توضیح اضافه.
        """
        
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                response = requests.post(self.api_url, json=data, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"AI API error: {e}")
        
        # Fallback
        return self.fallback_response(user_command)
    
    def fallback_response(self, command):
        """پیش‌فرض اگر API در دسترس نبود"""
        if "منو" in command or "menu" in command:
            return """FILE: telegram_handler.py
MARKER: # KEYBOARD_MARKER
CODE: [InlineKeyboardButton('🤖 دستور AI', callback_data='ai_command')]"""
        elif "وضعیت" in command or "status" in command:
            return """FILE: telegram_handler.py
MARKER: async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
CODE:     await update.message.reply_text(f"🤖 وضعیت ربات: فعال\\\\n📊 آخرین آپدیت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")"""
        else:
            return """FILE: telegram_handler.py
MARKER: # KEYBOARD_MARKER  
CODE: [InlineKeyboardButton('🔧 ' + '$command', callback_data='custom_$command')]"""

ai_agent = AIAgent()

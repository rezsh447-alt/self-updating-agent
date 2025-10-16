import os
import json
import requests
import datetime
from session_manager import advanced_session_manager

class AIAgent:
    def __init__(self):
        with open("config.json", "r") as f:
            config = json.load(f)
        
        self.api_key = os.getenv("GEMINI_API_KEY") or config.get("GEMINI_API_KEY")
        self.service = "gemini"
        self.timeout = 30
    
    def chat_response(self, user_message, user_id="default"):
        if not self.api_key:
            return "❌ API Key تنظیم نشده!"
        
        # دریافت context هوشمند (شبیه ChatGPT)
        smart_context = advanced_session_manager.get_smart_context(user_id)
        
        # تولید پاسخ
        response = self._gemini_chat(user_message, smart_context, user_id)
        
        # ذخیره در session
        if not response.startswith("❌"):
            advanced_session_manager.add_chat(user_id, user_message, response)
        
        return response
    
    def _gemini_chat(self, user_message, smart_context, user_id):
        """پاسخ با Gemini با context هوشمند"""
        try:
            session = advanced_session_manager.get_current_session(user_id)
            session_title = session['title'] if session else "چت عمومی"
            
            system_context = f"""
            تو یک دستیار هوشمند برای ربات "Self-Updating AI Agent" هستی.
            
            کاربر در حال کار روی پروژه "{session_title}" هست.
            
            مشخصات ربات:
            - می‌تونی کد خودش رو ویرایش کنه و آپدیت کنه
            - از کاربر دستور می‌گیری و کد پایتون تولید می‌کنی
            - فایل‌های اصلی: telegram_handler.py, main.py, self_editor.py, github_updater.py
            - از کتابخانه python-telegram-bot نسخه 20 استفاده می‌کنه
            - می‌تونی تغییرات رو commit کنی و به گیت‌هاب push کنی
            
            با توجه به زمینه پروژه و تاریخچه، پاسخ مرتبط و مفید بده.
            """
            
            prompt = f"{system_context}\n\n"
            
            if smart_context:
                prompt += f"{smart_context}\n\n"
            
            prompt += f"**پیام جدید کاربر:** '{user_message}'\n\n"
            prompt += "با توجه به زمینه پروژه، به صورت مفید و دوستانه پاسخ بده."
            
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "❌ پاسخ نامعتبر از Gemini"
            else:
                return f"❌ خطای Gemini {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"❌ خطا در ارتباط با Gemini: {e}"
    
    def analyze_command(self, user_command):
        """برای دستورات /ai - تولید کد"""
        if not self.api_key:
            return "❌ API Key تنظیم نشده!"
            
        prompt = f"""
        تو یک دستیار برنامه‌نویس هستی. کاربر این دستور رو داده: "{user_command}"
        
        باید کد پایتون مناسب برای اضافه کردن این قابلیت به ربات تلگرام تولید کنی.
        
        ربات از کتابخانه python-telegram-bot نسخه 20 استفاده می‌کنه.
        فایل‌های اصلی: telegram_handler.py, main.py, self_editor.py, github_updater.py
        
        خروجی باید به این فرمت باشه:
        FILE: [نام فایل]
        MARKER: [مارکر در فایل] 
        CODE: [کد پایتون]
        
        فقط خروجی خالص بده بدون توضیح اضافه.
        """
        
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "❌ پاسخ نامعتبر از Gemini"
            else:
                return f"❌ خطای Gemini {response.status_code}"
                    
        except Exception as e:
            return f"❌ خطا در ارتباط: {e}"

ai_agent = AIAgent()

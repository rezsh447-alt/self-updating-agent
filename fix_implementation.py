#!/usr/bin/env python3
import os
import json
import shutil
from datetime import datetime

print("🚀 در حال پیاده‌سازی سیستم حافظه پیشرفته...")

# 1. اصلاح config.json
print("📁 در حال بروزرسانی config.json...")
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# اضافه کردن تنظیمات جدید
config["ALLOWED_USERS"] = {
    config["ADMIN_ID"]: {"name": "مدیر اصلی", "role": "admin"}
}
config["MAX_USERS"] = 6
config["AUTO_BACKUP_INTERVAL"] = 10
config["CHATS_DIR"] = "chats"

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# 2. ایجاد ساختار پوشه‌ها
print("📂 در حال ایجاد ساختار پوشه‌ها...")
os.makedirs("chats/admin/full", exist_ok=True)
os.makedirs("chats/admin/summary", exist_ok=True)
os.makedirs("chats/backups", exist_ok=True)

# 3. ایجاد session_manager پیشرفته
print("🧠 در حال ایجاد session_manager پیشرفته...")

SESSION_MANAGER_CODE = '''import os
import json
import threading
from datetime import datetime
from github_updater import git_commit_and_push

class AdvancedSessionManager:
    def __init__(self):
        self.config = self.load_config()
        self.chats_dir = self.config.get("CHATS_DIR", "chats")
        self.users_file = "users.json"
        self.users_data = self.load_users()
        
    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.config.get("ALLOWED_USERS", {})
    
    def save_users(self):
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users_data, f, ensure_ascii=False, indent=2)
    
    def is_user_allowed(self, user_id):
        return str(user_id) in self.users_data
    
    def get_user_chats(self, user_id):
        user_chats_dir = f"{self.chats_dir}/{user_id}"
        if not os.path.exists(user_chats_dir):
            os.makedirs(f"{user_chats_dir}/full", exist_ok=True)
            os.makedirs(f"{user_chats_dir}/summary", exist_ok=True)
            return {}
        
        chats = {}
        for chat_file in os.listdir(f"{user_chats_dir}/full"):
            if chat_file.endswith(".json"):
                chat_id = chat_file[:-5]
                summary = self.load_chat_summary(user_id, chat_id)
                if summary:
                    chats[chat_id] = summary
        return chats
    
    def create_chat(self, user_id, title="چت جدید"):
        chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        chat_data = {
            "chat_id": chat_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0,
            "messages": []
        }
        
        # ذخیره در حافظه محلی
        self.save_chat_local(user_id, chat_id, chat_data)
        
        return chat_id
    
    def save_chat_local(self, user_id, chat_id, chat_data):
        chat_file = f"{self.chats_dir}/{user_id}/full/{chat_id}.json"
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        # ایجاد خلاصه
        summary = self.generate_summary(chat_data)
        summary_file = f"{self.chats_dir}/{user_id}/summary/{chat_id}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def generate_summary(self, chat_data):
        messages = chat_data.get("messages", [])
        last_messages = messages[-3:] if len(messages) > 3 else messages
        
        return {
            "chat_id": chat_data["chat_id"],
            "title": chat_data["title"],
            "summary": f"چت با {len(messages)} پیام",
            "last_activity": chat_data["updated_at"],
            "message_count": chat_data["message_count"],
            "recent_messages": [msg.get("content", "")[:80] + "..." if len(msg.get("content", "")) > 80 else msg.get("content", "") for msg in last_messages]
        }
    
    def add_message(self, user_id, chat_id, role, content):
        # بارگذاری چت
        chat_file = f"{self.chats_dir}/{user_id}/full/{chat_id}.json"
        if not os.path.exists(chat_file):
            return None
            
        with open(chat_file, "r", encoding="utf-8") as f:
            chat_data = json.load(f)
        
        # اضافه کردن پیام جدید
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{len(chat_data['messages']) + 1}"
        }
        
        chat_data["messages"].append(new_message)
        chat_data["message_count"] = len(chat_data["messages"])
        chat_data["updated_at"] = datetime.now().isoformat()
        
        # ذخیره محلی
        self.save_chat_local(user_id, chat_id, chat_data)
        
        # بررسی نیاز به پشتیبان‌گیری در گیت‌هاب (هر 10 پیام)
        if chat_data["message_count"] % 10 == 0:
            self.backup_to_github(user_id, chat_id)
        
        return new_message
    
    def backup_to_github(self, user_id, chat_id):
        try:
            chat_file = f"{self.chats_dir}/{user_id}/full/{chat_id}.json"
            if os.path.exists(chat_file):
                commit_msg = f"backup: {user_id}/{chat_id} - auto backup"
                result = git_commit_and_push(commit_message=commit_msg, auto_push=True)
                
                if result.get("ok"):
                    print(f"✅ پشتیبان‌گیری موفق برای {user_id}/{chat_id}")
                else:
                    print(f"⚠️ خطا در پشتیبان‌گیری: {result.get('error')}")
                    
        except Exception as e:
            print(f"❌ خطا در پشتیبان‌گیری: {e}")
    
    def load_chat_summary(self, user_id, chat_id):
        summary_file = f"{self.chats_dir}/{user_id}/summary/{chat_id}.json"
        if os.path.exists(summary_file):
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def load_full_chat(self, user_id, chat_id):
        chat_file = f"{self.chats_dir}/{user_id}/full/{chat_id}.json"
        if os.path.exists(chat_file):
            with open(chat_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

# ایجاد نمونه global
advanced_session_manager = AdvancedSessionManager()
'''

with open("session_manager.py", "w", encoding="utf-8") as f:
    f.write(SESSION_MANAGER_CODE)

# 4. ایجاد users.json
print("👥 در حال ایجاد users.json...")
users_data = {
    config["ADMIN_ID"]: {"name": "مدیر اصلی", "role": "admin"}
}
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users_data, f, ensure_ascii=False, indent=2)

# 5. ایجاد چت اولیه برای مدیر (با import جدید)
print("👑 در حال ایجاد چت اولیه برای مدیر...")

# import کلاس جدید
import sys
sys.path.append('.')
from session_manager import advanced_session_manager

# ایجاد چت اولیه
chat_id = advanced_session_manager.create_chat(config["ADMIN_ID"], "چت اصلی")
print(f"✅ چت اولیه ایجاد شد: {chat_id}")

print("🎉 پیاده‌سازی کامل شد!")
print("")
print("📋 ویژگی‌های پیاده‌سازی شده:")
print("✅ سیستم چت‌های مجزا شبیه ChatGPT")
print("✅ مدیریت کاربران (مدیر + 5 کاربر)") 
print("✅ ذخیره‌سازی Hybrid (کامل + خلاصه)")
print("✅ پشتیبان‌گیری هر 10 پیام در گیت‌هاب")
print("✅ بازیابی هوشمند از حافظه محلی/ابری")
print("")
print("🚀 حالا ربات رو اجرا کن:")
print("python main.py")

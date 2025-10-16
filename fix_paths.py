#!/usr/bin/env python3
import os
import json
from datetime import datetime

print("🔧 در حال اصلاح مسیرها و ساختار پوشه‌ها...")

# 1. ایجاد پوشه‌های لازم
os.makedirs("chats/247818318/full", exist_ok=True)
os.makedirs("chats/247818318/summary", exist_ok=True)
os.makedirs("chats/backups", exist_ok=True)

print("✅ پوشه‌ها ایجاد شدند")

# 2. اصلاح session_manager برای مدیریت بهتر مسیرها
print("📝 در حال اصلاح session_manager.py...")

FIXED_SESSION_MANAGER = '''import os
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
        user_id_str = str(user_id)
        return user_id_str in self.users_data
    
    def ensure_user_dirs(self, user_id):
        """اطمینان از وجود پوشه‌های کاربر"""
        user_id_str = str(user_id)
        full_dir = f"{self.chats_dir}/{user_id_str}/full"
        summary_dir = f"{self.chats_dir}/{user_id_str}/summary"
        
        os.makedirs(full_dir, exist_ok=True)
        os.makedirs(summary_dir, exist_ok=True)
        return full_dir, summary_dir
    
    def get_user_chats(self, user_id):
        user_id_str = str(user_id)
        full_dir, summary_dir = self.ensure_user_dirs(user_id_str)
        
        chats = {}
        if os.path.exists(full_dir):
            for chat_file in os.listdir(full_dir):
                if chat_file.endswith(".json"):
                    chat_id = chat_file[:-5]
                    summary = self.load_chat_summary(user_id_str, chat_id)
                    if summary:
                        chats[chat_id] = summary
        return chats
    
    def create_chat(self, user_id, title="چت جدید"):
        user_id_str = str(user_id)
        full_dir, summary_dir = self.ensure_user_dirs(user_id_str)
        
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
        self.save_chat_local(user_id_str, chat_id, chat_data)
        print(f"✅ چت جدید ایجاد شد: {chat_id} برای کاربر {user_id_str}")
        
        return chat_id
    
    def save_chat_local(self, user_id, chat_id, chat_data):
        full_dir, summary_dir = self.ensure_user_dirs(user_id)
        
        chat_file = f"{full_dir}/{chat_id}.json"
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        # ایجاد خلاصه
        summary = self.generate_summary(chat_data)
        summary_file = f"{summary_dir}/{chat_id}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def generate_summary(self, chat_data):
        messages = chat_data.get("messages", [])
        last_messages = messages[-3:] if len(messages) > 3 else messages
        
        recent_previews = []
        for msg in last_messages:
            content = msg.get("content", "")
            if len(content) > 80:
                content = content[:80] + "..."
            recent_previews.append(content)
        
        return {
            "chat_id": chat_data["chat_id"],
            "title": chat_data["title"],
            "summary": f"چت با {len(messages)} پیام",
            "last_activity": chat_data["updated_at"],
            "message_count": chat_data["message_count"],
            "recent_messages": recent_previews
        }
    
    def add_message(self, user_id, chat_id, role, content):
        user_id_str = str(user_id)
        full_dir, summary_dir = self.ensure_user_dirs(user_id_str)
        
        # بارگذاری چت
        chat_file = f"{full_dir}/{chat_id}.json"
        if not os.path.exists(chat_file):
            print(f"❌ فایل چت پیدا نشد: {chat_file}")
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
        self.save_chat_local(user_id_str, chat_id, chat_data)
        
        # بررسی نیاز به پشتیبان‌گیری در گیت‌هاب (هر 10 پیام)
        if chat_data["message_count"] % 10 == 0:
            print(f"🔄 پشتیبان‌گیری برای چت {chat_id} (پیام {chat_data['message_count']})")
            self.backup_to_github(user_id_str, chat_id)
        
        return new_message
    
    def backup_to_github(self, user_id, chat_id):
        try:
            full_dir, _ = self.ensure_user_dirs(user_id)
            chat_file = f"{full_dir}/{chat_id}.json"
            
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
        _, summary_dir = self.ensure_user_dirs(user_id)
        summary_file = f"{summary_dir}/{chat_id}.json"
        
        if os.path.exists(summary_file):
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def load_full_chat(self, user_id, chat_id):
        full_dir, _ = self.ensure_user_dirs(user_id)
        chat_file = f"{full_dir}/{chat_id}.json"
        
        if os.path.exists(chat_file):
            with open(chat_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

# ایجاد نمونه global
advanced_session_manager = AdvancedSessionManager()
'''

with open("session_manager.py", "w", encoding="utf-8") as f:
    f.write(FIXED_SESSION_MANAGER)

print("✅ session_manager.py اصلاح شد")

# 3. ایجاد چت اولیه
print("👑 در حال ایجاد چت اولیه...")

# import کلاس جدید
import importlib
import sys

# حذف کش ماژول قبلی
if 'session_manager' in sys.modules:
    del sys.modules['session_manager']

from session_manager import advanced_session_manager

# ایجاد چت اولیه برای مدیر
admin_id = "247818318"
chat_id = advanced_session_manager.create_chat(admin_id, "چت اصلی")
print(f"✅ چت اولیه ایجاد شد: {chat_id}")

# 4. بررسی ساختار ایجاد شده
print("📂 بررسی ساختار ایجاد شده:")
for root, dirs, files in os.walk("chats"):
    level = root.replace("chats", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}📁 {os.path.basename(root)}/")
    sub_indent = " " * 2 * (level + 1)
    for file in files:
        print(f"{sub_indent}📄 {file}")

print("🎉 پیاده‌سازی کامل شد!")
print("🚀 حالا ربات رو اجرا کن: python main.py")

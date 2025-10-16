import os
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
        self.user_current_chats = {}  # چت فعلی هر کاربر
        
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
    
    # توابع جدید برای سازگاری با کد قدیمی
    def get_current_session(self, user_id):
        """برگرداندن چت فعلی کاربر (برای سازگاری با کد قدیمی)"""
        user_id_str = str(user_id)
        
        # اگر چت فعلی وجود نداره، یکی ایجاد کن
        if user_id_str not in self.user_current_chats:
            chats = self.get_user_chats(user_id_str)
            if chats:
                # اولین چت رو انتخاب کن
                self.user_current_chats[user_id_str] = list(chats.keys())[0]
            else:
                # چت جدید ایجاد کن
                new_chat_id = self.create_chat(user_id_str, "چت عمومی")
                self.user_current_chats[user_id_str] = new_chat_id
        
        chat_id = self.user_current_chats[user_id_str]
        chat_data = self.load_full_chat(user_id_str, chat_id)
        
        # تبدیل به فرمت قدیمی برای سازگاری
        if chat_data:
            return {
                "title": chat_data.get("title", "چت عمومی"),
                "file": None,
                "created_at": chat_data.get("created_at", ""),
                "updated_at": chat_data.get("updated_at", ""),
                "chats": chat_data.get("messages", []),
                "summary": "",
                "key_points": [],
                "message_count": chat_data.get("message_count", 0),
                "last_summary_at": None
            }
        return None
    
    def create_session(self, user_id, title):
        """ایجاد سشن جدید (برای سازگاری با کد قدیمی)"""
        user_id_str = str(user_id)
        chat_id = self.create_chat(user_id_str, title)
        self.user_current_chats[user_id_str] = chat_id
        return chat_id
    
    def get_smart_context(self, user_id, max_recent_chats=5):
        """دریافت context هوشمند (برای سازگاری با کد قدیمی)"""
        session = self.get_current_session(user_id)
        if not session or not session.get("chats"):
            return ""

        context = ""
        messages = session.get("chats", [])
        total_messages = len(messages)

        # نمایش ۵ پیام اخیر
        recent_messages = messages[-max_recent_chats:] if total_messages > max_recent_chats else messages
        
        if recent_messages:
            context += "💬 **مکالمات اخیر:**\n"
            for i, msg in enumerate(recent_messages, 1):
                role = "👤" if msg.get("role") == "user" else "🤖"
                content = msg.get("content", "")
                if len(content) > 80:
                    content = content[:80] + "..."
                context += f"{i}. {role} {content}\n"
            context += "\n"

        return context
    
    def add_chat(self, user_id, user_message, ai_response):
        """اضافه کردن چت (برای سازگاری با کد قدیمی)"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_current_chats:
            self.get_current_session(user_id_str)  # ایجاد چت اگر وجود نداره
        
        chat_id = self.user_current_chats[user_id_str]
        
        # اضافه کردن پیام کاربر
        self.add_message(user_id_str, chat_id, "user", user_message)
        
        # اضافه کردن پاسخ AI
        self.add_message(user_id_str, chat_id, "assistant", ai_response)
        
        return True
    
    def get_current_session_info(self, user_id):
        """اطلاعات چت فعلی (برای سازگاری با کد قدیمی)"""
        session = self.get_current_session(user_id)
        if not session:
            return "❌ هیچ چت فعالی ندارید!"

        time_ago = self._get_time_ago(session.get("updated_at", ""))

        info = f"📋 **چت فعلی:** {session.get('title', 'چت عمومی')}\n"
        info += f"💬 **تعداد پیام‌ها:** {session.get('message_count', 0)}\n"
        info += f"🕒 **آخرین فعالیت:** {time_ago}\n"

        return info
    
    def _get_time_ago(self, timestamp):
        """محاسبه زمان گذشته"""
        try:
            if not timestamp:
                return "نامشخص"
                
            past = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - past

            if diff.days > 0:
                return f"{diff.days} روز پیش"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600} ساعت پیش"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60} دقیقه پیش"
            else:
                return "همین الان"
        except:
            return "نامشخص"
    
    # توابع اصلی جدید
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

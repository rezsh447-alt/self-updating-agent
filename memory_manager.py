import json
import os
import requests
import base64
from datetime import datetime

class SmartMemory:
    def __init__(self):
        self.local_dir = "memory/local"
        self.github_owner = "rezsh447-alt"
        self.github_repo = "self-updating-agent"
        self.github_token = os.getenv("GITHUB_TOKEN")
        os.makedirs(self.local_dir, exist_ok=True)
        
        # الگوهای یادگیری
        self.user_patterns = {}
    
    def save_chat(self, user_id, user_message, ai_response):
        """ذخیره چت در حافظه هوشمند"""
        # ذخیره لوکال
        local_success = self._save_local(user_id, user_message, ai_response)
        
        # یادگیری الگوهای کاربر
        self._learn_user_patterns(user_id, user_message)
        
        # هر ۵ چت یکبار با گیت‌هاب همگام‌سازی کن
        chats = self._load_local(user_id)
        if len(chats) % 5 == 0:
            self._sync_to_github(user_id, chats)
        
        return local_success
    
    def get_chat_history(self, user_id, current_question="", max_chats=3):
        """دریافت هوشمند تاریخچه - فقط چت‌های مرتبط"""
        all_chats = self._load_local(user_id)
        
        # اگر سوال درباره حافظه نیست، تاریخچه نفرست (صرفه‌جویی در توکن)
        needs_history = any(keyword in current_question for keyword in 
                           ["یادت", "قبلی", "گفتی", "چت قبل", "صحبت کردیم", "یادم"])
        
        if not needs_history:
            return ""  # 🎯 هوشمند!
        
        # پیدا کردن چت‌های مرتبط
        related_chats = self._find_related_chats(all_chats, current_question)
        
        # اگر مرتبطی پیدا نشد، ۲ چت آخر رو بفرست
        if not related_chats:
            related_chats = all_chats[-2:]
        
        return self._format_chats(related_chats[-max_chats:])
    
    def _find_related_chats(self, all_chats, current_question):
        """پیدا کردن هوشمند چت‌های مرتبط"""
        if not all_chats:
            return []
        
        related = []
        current_lower = current_question.lower()
        
        # دسته‌بندی‌های هوشمند
        categories = {
            "کد": ["کد", "برنامه", "تغییر", "اضافه کن", "حذف کن", "تابع", "کلاس", "پایتون"],
            "خطا": ["خطا", "مشکل", "ایراد", "درست کن", "رفع", "اشکال", "باگ"],
            "قابلیت": ["چکار", "قابلیت", "توانایی", "می‌تونی", "امکان", "کارایی"],
            "حافظه": ["یادت", "قبلی", "گفتی", "چت قبل", "صحبت کردیم", "یادم"],
            "api": ["api", "توکن", "کلید", "authentication", "key"],
            "گیت": ["گیت", "گیت‌هاب", "commit", "push", "ریپازیتوری"]
        }
        
        # پیدا کردن دسته سوال فعلی
        current_category = None
        for category, keywords in categories.items():
            if any(keyword in current_lower for keyword in keywords):
                current_category = category
                break
        
        # جستجوی هوشمند در چت‌ها
        for chat in all_chats[-25:]:  # فقط ۲۵ چت آخر
            user_msg = chat['user'].lower()
            ai_msg = chat['ai'].lower()
            
            # روش‌های مختلف پیدا کردن مرتبط‌ها:
            
            # ۱. هم‌دسته بودن
            if current_category and any(keyword in user_msg for keyword in categories[current_category]):
                related.append(chat)
                continue
                
            # ۲. تشابه متنی مستقیم
            similarity = self._calculate_similarity(current_lower, user_msg)
            if similarity > 0.5:  # ۵۰٪ تشابه
                related.append(chat)
                continue
                
            # ۳. کلمات مشترک مهم
            important_words = set(current_lower.split()) & set(user_msg.split())
            if len(important_words) >= 2:  # حداقل ۲ کلمه مشترک
                related.append(chat)
                continue
            
            # ۴. اگر سوال درباره کد هست، چت‌های کد رو پیدا کن
            if "کد" in current_lower and any(word in user_msg for word in ["کد", "برنامه", "پایتون"]):
                related.append(chat)
        
        # حذف duplicates
        unique_related = []
        seen_content = set()
        for chat in related:
            content_hash = hash(chat['user'][:50] + chat['ai'][:50])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_related.append(chat)
        
        return unique_related
    
    def _calculate_similarity(self, text1, text2):
        """محاسبه تشابه بین دو متن"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0
        
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))
    
    def _learn_user_patterns(self, user_id, user_message):
        """یادگیری الگوهای کاربر"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                "common_words": {},
                "request_types": {},
                "active_times": {}
            }
        
        # یادگیری کلمات پرکاربرد
        words = user_message.split()
        for word in words:
            if len(word) > 2:  # کلمات کوتاه رو نادیده بگیر
                self.user_patterns[user_id]["common_words"][word] = \
                    self.user_patterns[user_id]["common_words"].get(word, 0) + 1
        
        # یادگیری نوع درخواست
        request_type = self._classify_request(user_message)
        self.user_patterns[user_id]["request_types"][request_type] = \
            self.user_patterns[user_id]["request_types"].get(request_type, 0) + 1
        
        # یادگیری زمان فعالیت
        hour = datetime.now().hour
        time_slot = f"{hour}:00-{hour+1}:00"
        self.user_patterns[user_id]["active_times"][time_slot] = \
            self.user_patterns[user_id]["active_times"].get(time_slot, 0) + 1
    
    def _classify_request(self, message):
        """دسته‌بندی هوشمند نوع درخواست"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["کد", "برنامه", "پایتون", "تابع", "کلاس"]):
            return "کد‌نویسی"
        elif any(word in message_lower for word in ["خطا", "مشکل", "ایراد", "درست کن", "رفع"]):
            return "رفع خطا"
        elif any(word in message_lower for word in ["اضافه", "جدید", "ساخت", "ایجاد"]):
            return "افزودن قابلیت"
        elif any(word in message_lower for word in ["یادت", "قبلی", "گفتی"]):
            return "سوال حافظه"
        elif any(word in message_lower for word in ["چکار", "قابلیت", "توانایی"]):
            return "سوال قابلیت"
        else:
            return "سوال عمومی"
    
    def get_user_insights(self, user_id):
        """دریافت بینش‌های کاربر"""
        if user_id not in self.user_patterns:
            return "هنوز الگوی خاصی یاد نگرفتم! 🎯"
        
        patterns = self.user_patterns[user_id]
        
        # پرکاربردترین کلمات
        top_words = dict(sorted(patterns["common_words"].items(), 
                              key=lambda x: x[1], reverse=True)[:5])
        
        # پرتکرارترین نوع درخواست
        top_requests = dict(sorted(patterns["request_types"].items(),
                                 key=lambda x: x[1], reverse=True)[:3])
        
        insights = "🎯 الگوهای یادگیری شما:\n"
        insights += f"• کلمات پرکاربرد: {', '.join(top_words.keys())}\n"
        insights += f"• درخواست‌های متداول: {', '.join(top_requests.keys())}\n"
        
        return insights
    
    def _save_local(self, user_id, user_message, ai_response):
        """ذخیره در حافظه لوکال"""
        try:
            memory_file = os.path.join(self.local_dir, f"{user_id}.json")
            
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
            else:
                memory = {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "chats": []
                }
            
            # اضافه کردن چت جدید
            memory["chats"].append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "ai": ai_response
            })
            
            # محدود کردن به ۲۰۰۰ چت آخر
            memory["chats"] = memory["chats"][-2000:]
            memory["updated_at"] = datetime.now().isoformat()
            memory["total_chats"] = len(memory["chats"])
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ خطای ذخیره لوکال: {e}")
            return False
    
    def _load_local(self, user_id):
        """بارگذاری از حافظه لوکال"""
        try:
            memory_file = os.path.join(self.local_dir, f"{user_id}.json")
            
            if not os.path.exists(memory_file):
                return []
            
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
            
            return memory.get("chats", [])
        except Exception as e:
            print(f"❌ خطای بارگذاری لوکال: {e}")
            return []
    
    def _sync_to_github(self, user_id, chats):
        """همگام‌سازی با گیت‌هاب"""
        if not self.github_token:
            return False
        
        try:
            file_path = f"memory/users/{user_id}.json"
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contents/{file_path}"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Content-Type": "application/json"
            }
            
            # داده برای ذخیره
            memory_data = {
                "user_id": user_id,
                "last_sync": datetime.now().isoformat(),
                "total_chats": len(chats),
                "chats": chats[-1000:]  # در گیت‌هاب فقط ۱۰۰۰ چت آخر
            }
            
            content = json.dumps(memory_data, ensure_ascii=False, indent=2)
            encoded_content = base64.b64encode(content.encode()).decode()
            
            # چک کردن وجود فایل
            response = requests.get(url, headers=headers)
            sha = None
            if response.status_code == 200:
                sha = response.json().get("sha")
            
            # آپلود
            payload = {
                "message": f"Auto-sync: {user_id} memory ({len(chats)} chats)",
                "content": encoded_content,
                "sha": sha
            }
            
            response = requests.put(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                print(f"✅ همگام‌سازی {len(chats)} چت برای کاربر {user_id}")
                return True
            else:
                print(f"❌ خطای همگام‌سازی: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ خطای همگام‌سازی: {e}")
            return False
    
    def _format_chats(self, chats):
        """فرمت کردن چت‌ها برای نمایش"""
        if not chats:
            return ""
        
        formatted = "📚 چت‌های مرتبط:\n"
        for i, chat in enumerate(chats, 1):
            formatted += f"{i}. 👤 {chat['user'][:80]}\n"
            if len(chat['ai']) > 100:
                formatted += f"   🤖 {chat['ai'][:100]}...\n"
            else:
                formatted += f"   🤖 {chat['ai']}\n"
        
        return formatted
    
    def get_user_stats(self, user_id):
        """آمار کاربر"""
        local_chats = self._load_local(user_id)
        
        stats = {
            "local_chats": len(local_chats),
            "last_chat": local_chats[-1]["timestamp"][:19] if local_chats else "ندارد",
            "memory_usage": f"{(len(local_chats) * 0.00025):.2f} MB"  # تقریبی
        }
        
        # آمار الگوهای یادگیری
        if user_id in self.user_patterns:
            patterns = self.user_patterns[user_id]
            stats["learned_words"] = len(patterns["common_words"])
            stats["request_types"] = len(patterns["request_types"])
        else:
            stats["learned_words"] = 0
            stats["request_types"] = 0
        
        return stats

# ایجاد نمونه global
smart_memory = SmartMemory()

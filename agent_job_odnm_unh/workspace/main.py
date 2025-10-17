cd ~/agent
cat > memory_manager.py <<'EOL'
import json, os, subprocess, datetime

class MemoryManager:
    def init(self):
        self.file_path = "memory.json"
        self.repo_path = os.path.expanduser("~/agent")
        self.memory = {}
        self.load_memory()

    def load_memory(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            else:
                self.memory = {}
        except Exception as e:
            print(f"❌ خطا در بارگذاری حافظه: {e}")
            self.memory = {}

    def save_memory(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            self.git_backup()
        except Exception as e:
            print(f"❌ خطا در ذخیره حافظه: {e}")

    def add_chat(self, user_id, user_message, ai_response):
        if user_id not in self.memory:
            self.memory[user_id] = []
        self.memory[user_id].append({
            "user": user_message,
            "ai": ai_response,
            "time": datetime.datetime.now().isoformat()
        })
        self.save_memory()

    def get_recent_chats(self, user_id, n=5):
        if user_id in self.memory:
            return self.memory[user_id][-n:]
        return []

    def git_backup(self):
        """ارسال خودکار حافظه به GitHub"""
        try:
            subprocess.run(["git", "add", "memory.json"], cwd=self.repo_path)
            subprocess.run(["git", "commit", "-m", "🧠 Auto backup memory"], cwd=self.repo_path)
            subprocess.run(["git", "push"], cwd=self.repo_path)
            print("✅ حافظه روی GitHub پشتیبان‌گیری شد")
        except Exception as e:
            print(f"⚠️ خطا در پشتیبان‌گیری گیت: {e}")

    def git_restore(self):
        """دریافت آخرین نسخه حافظه از GitHub"""
        try:
            subprocess.run(["git", "pull"], cwd=self.repo_path)
            self.load_memory()
            print("✅ حافظه از GitHub بازیابی شد")
        except Exception as e:
            print(f"⚠️ خطا در بازیابی از GitHub: {e}")

memory_manager = MemoryManager()
EOL

این بدردت میخوره؟
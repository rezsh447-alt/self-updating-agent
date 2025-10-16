#!/usr/bin/env python3
import os
import json

print("🔄 در حال بروزرسانی config.json...")

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

config["ALLOWED_USERS"] = {
    config["ADMIN_ID"]: {"name": "مدیر اصلی", "role": "admin"}
}
config["MAX_USERS"] = 6
config["AUTO_BACKUP_INTERVAL"] = 10
config["CHATS_DIR"] = "chats"

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# ایجاد پوشه‌ها
os.makedirs("chats/admin/full", exist_ok=True)
os.makedirs("chats/admin/summary", exist_ok=True)

print("✅ بروزرسانی انجام شد!")
print("🚀 حالا ربات رو اجرا کن: python main.py")

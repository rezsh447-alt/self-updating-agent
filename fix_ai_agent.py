#!/usr/bin/env python3
import re

print("🔧 در حال اصلاح ai_agent.py...")

with open("ai_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# جایگزینی import قدیمی با جدید
old_import = "from session_manager import smart_session_manager"
new_import = "from session_manager import advanced_session_manager"

content = content.replace(old_import, new_import)

# جایگزینی تمام استفاده‌ها از smart_session_manager
content = content.replace("smart_session_manager", "advanced_session_manager")

with open("ai_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ ai_agent.py اصلاح شد")

# همچنین اصلاح telegram_handler.py
print("🔧 در حال اصلاح telegram_handler.py...")

with open("telegram_handler.py", "r", encoding="utf-8") as f:
    telegram_content = f.read()

# جایگزینی import در telegram_handler
telegram_old_import = "from session_manager import smart_session_manager"
telegram_new_import = "from session_manager import advanced_session_manager"

telegram_content = telegram_content.replace(telegram_old_import, telegram_new_import)
telegram_content = telegram_content.replace("smart_session_manager", "advanced_session_manager")

with open("telegram_handler.py", "w", encoding="utf-8") as f:
    f.write(telegram_content)

print("✅ telegram_handler.py اصلاح شد")
print("🎯 تمام import ها به روز شدند!")
print("🚀 حالا ربات رو اجرا کن: python main.py")

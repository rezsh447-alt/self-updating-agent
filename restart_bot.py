#!/usr/bin/env python3
import os
import sys
import time

print("🔄 در حال ریستارت ربات...")
time.sleep(2)
os.execv(sys.executable, [sys.executable, "main.py"])

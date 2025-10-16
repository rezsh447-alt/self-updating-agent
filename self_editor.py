import os, shutil, re, json, datetime

CFG_PATH = "config.json"
with open(CFG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

ALLOWED = set(CFG.get("FILES_ALLOWED", []))
BACKUP = CFG.get("BACKUP_PATH", "backup")
os.makedirs(BACKUP, exist_ok=True)

def backup_file(path):
    """ایجاد بکاپ از فایل"""
    basename = os.path.basename(path)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(BACKUP, f"{basename}.{ts}.bak")
    shutil.copy2(path, dest)
    return dest

def safe_replace_in_file(path, pattern, replacement):
    """جایگزینی امن در فایل با regex"""
    if os.path.basename(path) not in ALLOWED:
        raise PermissionError(f"File {path} not allowed for edit")
    
    backup = backup_file(path)
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # استفاده از regex برای جایگزینی
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return {"backup": backup, "changed": content != new_content}

def append_snippet(path, marker, snippet):
    """افزودن snippet بعد از مارکر"""
    if os.path.basename(path) not in ALLOWED:
        raise PermissionError(f"File {path} not allowed for edit")
    
    backup = backup_file(path)
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # بررسی وجود snippet
    if snippet.strip() in content:
        return {"backup": backup, "changed": False}
    
    # افزودن بعد از مارکر
    if marker in content:
        new_content = content.replace(marker, marker + "\n" + snippet)
    else:
        # اگر مارکر پیدا نشد، به انتهای فایل اضافه کن
        new_content = content + "\n" + snippet
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return {"backup": backup, "changed": True}

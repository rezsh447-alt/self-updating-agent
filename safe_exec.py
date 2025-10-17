import json, subprocess, tempfile, os
from pathlib import Path

BASE_DIR = Path.home() / "agent"
RUNNER = BASE_DIR / "safe_runner.py"

def safe_run_code(code: str):
    """اجرای امن کد با safe_runner.py"""
    try:
        tmp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=BASE_DIR)
        job_data = {"files": {"main.py": code}}
        json.dump(job_data, open(tmp_json.name, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        result = subprocess.run(
            ["python3", str(RUNNER), tmp_json.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        os.unlink(tmp_json.name)
        if result.returncode != 0 and not result.stdout.strip():
            return f"❌ خطا در اجرا:\n{result.stderr[:800]}"
        return f"📤 نتیجه تست:\n{result.stdout[:1000]}"
    except subprocess.TimeoutExpired:
        return "⏱️ زمان اجرای کد بیش از حد مجاز بود (Timeout)"
    except Exception as e:
        return f"❌ خطا در اجرای امن: {e}"

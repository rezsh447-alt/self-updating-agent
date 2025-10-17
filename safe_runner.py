import os, sys, shutil, subprocess, tempfile, time, json
from pathlib import Path

BASE = Path.home() / "agent"
WHITELIST_PKGS = {"pytest", "requests"}
MAX_RUNTIME_SECONDS = 30

def shell(cmd, cwd=None, timeout=None, env=None):
    try:
        proc = subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", (e.stderr or "") + f"\n[Timeout after {timeout}s]"

def safe_create_job(code_files: dict, requirements: list=None):
    jobdir = Path(tempfile.mkdtemp(prefix="agent_job_", dir=str(BASE)))
    (jobdir / "workspace").mkdir(parents=True, exist_ok=True)
    ws = jobdir / "workspace"

    for fname, content in code_files.items():
        fp = ws / fname
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

    venv_dir = jobdir / "venv"
    rc, out, err = shell(f"python3 -m venv {venv_dir}")
    if rc != 0:
        cleanup(jobdir)
        return {"ok": False, "error": "venv failed", "out": out, "err": err}

    py = venv_dir / "bin" / "python"
    pip = venv_dir / "bin" / "pip"

    if requirements:
        to_install = []
        for p in requirements:
            name = p.split("==")[0]
            if name not in WHITELIST_PKGS:
                cleanup(jobdir)
                return {"ok": False, "error": "require_approval", "package": name}
            to_install.append(p)
        if to_install:
            rc, out, err = shell(f"{pip} install --no-deps " + " ".join(to_install), cwd=ws, timeout=120)
            if rc != 0:
                cleanup(jobdir)
                return {"ok": False, "error": "pip install failed", "out": out, "err": err}

    if (ws / "tests").exists() or any(str(x).endswith("_test.py") for x in ws.glob("**/*.py")):
        run_cmd = f"{venv_dir}/bin/pytest -q"
    elif (ws / "run_tests.py").exists():
        run_cmd = f"{py} run_tests.py"
    elif (ws / "main.py").exists():
        run_cmd = f"{py} main.py"
    else:
        cleanup(jobdir)
        return {"ok": False, "error": "no_test_found"}

    safe_env = os.environ.copy()
    for k in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]:
        safe_env.pop(k, None)
    safe_env["PATH"] = str(venv_dir / "bin") + ":" + safe_env.get("PATH", "")

    start = time.time()
    rc, out, err = shell(run_cmd, cwd=ws, timeout=MAX_RUNTIME_SECONDS, env=safe_env)
    duration = time.time() - start

    result = {
        "ok": True,
        "rc": rc,
        "out": out,
        "err": err,
        "duration": duration,
        "jobdir": str(jobdir)
    }
    return result

def cleanup(jobdir):
    try:
        shutil.rmtree(jobdir)
    except Exception:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: safe_runner.py job.json")
        sys.exit(1)
    jobfile = Path(sys.argv[1])
    data = json.loads(jobfile.read_text(encoding="utf-8"))
    res = safe_create_job(data.get("files", {}), data.get("requirements"))
    print(json.dumps(res, ensure_ascii=False, indent=2))

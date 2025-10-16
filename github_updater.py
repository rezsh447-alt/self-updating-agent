import os, subprocess, shlex

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def git_commit_and_push(commit_message="agent: automated edit", branch=None, auto_push=False):
    run("git add -A")
    run(f'git commit -m "{commit_message}" || true')
    if branch:
        run(f"git checkout -b {branch}")
    if not GITHUB_TOKEN:
        return {"ok": True, "message": "local commit created; no GITHUB_TOKEN to push"}
    code, origin, err = run("git remote get-url origin")
    origin = origin.strip()
    if origin.startswith("https://"):
        toks = origin.split("https://",1)[1]
        secure_url = f"https://{GITHUB_TOKEN}@{toks}"
        run("git remote add _tmp_push_remote " + shlex.quote(secure_url))
        rc, out, err = run("git push _tmp_push_remote HEAD:refs/heads/" + (branch or "main"))
        run("git remote remove _tmp_push_remote")
        if rc != 0:
            return {"ok": False, "error": err}
        return {"ok": True, "message": "pushed to github"}
    else:
        rc, out, err = run("git push origin " + (branch or "main"))
        if rc != 0:
            return {"ok": False, "error": err}
        return {"ok": True, "message": "pushed via origin"}

import json
import os
import shutil
import subprocess
import tempfile
import requests


REPO_NAME = "tradermind"
API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_username(token: str) -> str:
    r = requests.get(f"{API}/user", headers=_headers(token))
    r.raise_for_status()
    return r.json()["login"]


def _enable_pages(token: str, username: str):
    r = requests.post(
        f"{API}/repos/{username}/{REPO_NAME}/pages",
        headers=_headers(token),
        json={"source": {"branch": "main", "path": "/"}},
    )
    if r.status_code not in (201, 409, 422):
        print(f"  Note: couldn't auto-enable Pages (status {r.status_code}). You may need to enable it manually.")


def _run(cmd: list, cwd: str):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git error: {result.stderr.strip()}")
    return result.stdout.strip()


def publish(html_content: str, analysis: dict) -> str:
    token = os.environ["GITHUB_TOKEN"]
    print("Publishing to GitHub Pages...")

    username = _get_username(token)
    repo_url = f"https://{username}:{token}@github.com/{username}/{REPO_NAME}.git"

    with tempfile.TemporaryDirectory() as tmpdir:
        print("  Cloning repo...")
        _run(["git", "clone", repo_url, tmpdir], cwd=None)

        # Write files into the cloned repo
        with open(os.path.join(tmpdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(os.path.join(tmpdir, "latest.json"), "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)

        from datetime import date
        month_label = date.today().strftime("%B %Y")

        _run(["git", "config", "user.email", "tradermind@bot.local"], cwd=tmpdir)
        _run(["git", "config", "user.name", "TraderMind Bot"], cwd=tmpdir)
        _run(["git", "add", "index.html", "latest.json"], cwd=tmpdir)
        _run(["git", "commit", "-m", f"TraderMind report — {month_label}"], cwd=tmpdir)
        print("  Pushing...")
        _run(["git", "push"], cwd=tmpdir)

    _enable_pages(token, username)

    url = f"https://{username}.github.io/{REPO_NAME}/"
    print(f"Published! URL: {url}")
    print("(GitHub Pages takes 1-2 minutes to go live on first publish)")
    return url

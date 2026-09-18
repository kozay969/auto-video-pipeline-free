"""
Step 6: Upload the final dubbed video to GitHub instead of Telegram.

Creates a new GitHub Release on this repository (tagged per run) and
attaches the dubbed video as a release asset. Uses the workflow's built-in
`GITHUB_TOKEN` — no extra secret needed, since this only ever talks to the
repo the workflow is already running in.

GitHub Actions outputs (written to $GITHUB_OUTPUT):
    release_url = the release's HTML URL (also written to $GITHUB_STEP_SUMMARY)
"""

import os
import json
import requests
from pathlib import Path

OUTPUT_DIR = Path("output")
FINAL_PATH = OUTPUT_DIR / "final_dubbed_video.mp4"

API_ROOT = "https://api.github.com"
GITHUB_RELEASE_ASSET_LIMIT_MB = 2000  # GitHub's per-file release-asset cap is 2 GB


def set_github_output(name: str, value: str):
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"{name}={value}\n")


def append_step_summary(text: str):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def build_release_notes(script_data: dict) -> tuple[str, str]:
    title = script_data.get("title") or "Dubbed Video"
    description = script_data.get("description", "")
    key_facts = script_data.get("key_facts", [])
    duration = script_data.get("video_duration_seconds", 0)
    size_mb = script_data.get("final_video_size_mb")

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    facts_md = "\n".join([f"- {f}" for f in key_facts[:5]])

    body = (
        f"{description}\n\n"
        + (f"**အဓိက အချက်များ:**\n{facts_md}\n\n" if facts_md else "")
        + f"- ⏱️ ကြာချိန်: {minutes}:{seconds:02d} မိနစ်\n"
        + (f"- 📦 ဖိုင်အရွယ်အစား: {size_mb} MB\n" if size_mb else "")
        + "- 🗣️ Auto-dubbed"
    )
    return title, body


def create_release(token: str, repo: str, tag: str, name: str, body: str) -> dict:
    url = f"{API_ROOT}/repos/{repo}/releases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "tag_name": tag,
        "name": name,
        "body": body,
        "draft": False,
        "prerelease": False,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Creating GitHub release failed ({resp.status_code}): {resp.text}")
    return resp.json()


def upload_asset(token: str, upload_url_template: str, asset_name: str, file_path: Path) -> dict:
    # upload_url_template looks like ".../assets{?name,label}" - strip the template part.
    upload_url = upload_url_template.split("{")[0]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "video/mp4",
    }
    print(f"📤 Uploading {file_path} ({file_path.stat().st_size / 1024 / 1024:.1f} MB) to GitHub release...")
    with open(file_path, "rb") as f:
        resp = requests.post(
            upload_url,
            headers=headers,
            params={"name": asset_name},
            data=f,
            timeout=600,
        )
    if resp.status_code >= 300:
        raise RuntimeError(f"Uploading release asset failed ({resp.status_code}): {resp.text}")
    return resp.json()


def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]  # auto-set by Actions, e.g. "owner/repo"
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "0")
    run_id = os.environ.get("GITHUB_RUN_ID", "0")

    if not FINAL_PATH.exists():
        print("❌ Final video file not found! Nothing to upload.")
        append_step_summary("⚠️ Dubbing pipeline ran but the final video file is missing.")
        raise SystemExit(1)

    size_mb = FINAL_PATH.stat().st_size / 1024 / 1024
    if size_mb > GITHUB_RELEASE_ASSET_LIMIT_MB:
        raise RuntimeError(
            f"Final video is {size_mb:.1f} MB, over GitHub's "
            f"{GITHUB_RELEASE_ASSET_LIMIT_MB} MB release-asset limit."
        )

    script_path = OUTPUT_DIR / "translated_script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    title, body = build_release_notes(script_data)
    tag = f"dub-run-{run_number}"
    release_name = f"🎬 {title} (#{run_number})"

    release = create_release(token, repo, tag, release_name, body)
    upload_asset(token, release["upload_url"], "dubbed_video.mp4", FINAL_PATH)

    release_url = release["html_url"]
    print(f"✅ Release created and video attached: {release_url}")

    set_github_output("release_url", release_url)
    append_step_summary(f"### 🎬 Dubbed video uploaded\n\n[{release_name}]({release_url})")
    print(f"\n🎉 Pipeline complete! Dubbed video uploaded to GitHub (run id {run_id}).")


if __name__ == "__main__":
    main()

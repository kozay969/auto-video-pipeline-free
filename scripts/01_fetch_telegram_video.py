"""
Step 1: Poll the Telegram Bot API for new incoming messages, find the newest
video (or video-document), and download it.

Tracking:
    state/last_update_id.txt keeps the highest Telegram `update_id` already
    processed, so every run only looks at *new* messages. The workflow commits
    this file back to the repo after each run.

GitHub Actions outputs (written to $GITHUB_OUTPUT):
    has_video = "true" / "false"  -> gates the rest of the pipeline
"""

import os
import json
import requests
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "last_update_id.txt"

API_BASE = "https://api.telegram.org/bot{token}"


def read_last_update_id() -> int:
    if STATE_FILE.exists():
        raw = STATE_FILE.read_text().strip()
        if raw.isdigit():
            return int(raw)
    return 0


def write_last_update_id(update_id: int):
    STATE_FILE.write_text(str(update_id))


def set_github_output(name: str, value: str):
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"{name}={value}\n")


def get_updates(token: str, offset: int) -> list[dict]:
    """Long-poll-free fetch: just grab whatever's queued since `offset`."""
    url = API_BASE.format(token=token) + "/getUpdates"
    resp = requests.get(
        url,
        params={
            "offset": offset,
            "timeout": 0,
            "allowed_updates": json.dumps(["message", "channel_post"]),
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates failed: {data}")
    return data["result"]


def extract_video(message: dict) -> dict | None:
    """Return {file_id, file_name, mime_type, duration} for the video in a
    message, whether it was sent as a native video or as a video file
    document. Returns None if the message has no usable video."""

    if "video" in message:
        v = message["video"]
        return {
            "file_id": v["file_id"],
            "file_name": v.get("file_name", "video.mp4"),
            "mime_type": v.get("mime_type", "video/mp4"),
            "duration": v.get("duration"),
        }

    if "document" in message:
        d = message["document"]
        mime = d.get("mime_type", "")
        name = d.get("file_name", "")
        if mime.startswith("video/") or name.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
            return {
                "file_id": d["file_id"],
                "file_name": name or "video.mp4",
                "mime_type": mime or "video/mp4",
                "duration": None,
            }

    return None


def download_file(token: str, file_id: str, dest: Path):
    url = API_BASE.format(token=token) + "/getFile"
    resp = requests.get(url, params={"file_id": file_id}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getFile failed: {data}")

    file_path = data["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"

    print(f"⬇️  Downloading: {file_path}")
    with requests.get(download_url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    print(f"✅ Saved: {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    # Optional: only accept videos coming from this chat (e.g. a specific
    # user, group or channel). Leave unset to accept from anywhere the bot
    # can see messages.
    source_chat_id = os.environ.get("TELEGRAM_SOURCE_CHAT_ID", "").strip()

    last_update_id = read_last_update_id()
    print(f"🔎 Polling for updates after id={last_update_id}")

    updates = get_updates(token, offset=last_update_id + 1)
    print(f"📬 {len(updates)} new update(s)")

    if not updates:
        set_github_output("has_video", "false")
        return

    # Advance the watermark past everything we saw, video or not, so we
    # never re-scan the same messages.
    highest_update_id = max(u["update_id"] for u in updates)

    best_message = None
    best_video = None
    best_chat_id = None

    for u in updates:
        message = u.get("message") or u.get("channel_post")
        if not message:
            continue

        chat_id = str(message.get("chat", {}).get("id", ""))
        if source_chat_id and chat_id != source_chat_id:
            continue

        video = extract_video(message)
        if video:
            # Keep the most recent one if several arrived since last run.
            best_message = message
            best_video = video
            best_chat_id = chat_id

    write_last_update_id(highest_update_id)

    if not best_video:
        print("ℹ️  No video found in this batch of updates.")
        set_github_output("has_video", "false")
        return

    video_path = OUTPUT_DIR / "source_video.mp4"
    download_file(token, best_video["file_id"], video_path)

    meta = {
        "source_chat_id": best_chat_id,
        "source_message_id": best_message.get("message_id"),
        "caption": best_message.get("caption", ""),
        "file_name": best_video["file_name"],
        "mime_type": best_video["mime_type"],
        "reported_duration_seconds": best_video["duration"],
    }
    with open(OUTPUT_DIR / "source_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"🎬 Source video ready: {video_path}")
    print(f"   From chat: {best_chat_id} | caption: {meta['caption'][:80]!r}")

    set_github_output("has_video", "true")


if __name__ == "__main__":
    main()
        

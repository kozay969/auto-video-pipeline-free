"""
Step 6: Send the final dubbed video + caption to the target Telegram
chat/channel.
"""

import os
import json
import asyncio
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode

OUTPUT_DIR = Path("output")
FINAL_PATH = OUTPUT_DIR / "final_dubbed_video.mp4"


def build_caption(script_data: dict) -> str:
    title = script_data.get("title", "Dubbed Video")
    description = script_data.get("description", "")
    key_facts = script_data.get("key_facts", [])
    duration = script_data.get("video_duration_seconds", 0)

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    facts_text = "\n".join([f"  ✦ {f}" for f in key_facts[:3]])

    caption = (
        f"🎬 *{title}*\n\n"
        f"{description}\n\n"
        + (f"🔑 *အဓိက အချက်များ:*\n{facts_text}\n\n" if facts_text else "")
        + f"━━━━━━━━━━━━━━━\n"
        f"⏱️ ကြာချိန် - {minutes}:{seconds:02d} မိနစ်\n"
        f"🗣️ Auto-dubbed"
    )

    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    return caption


async def send_video(bot_token: str, chat_id: str, video_path: Path, caption: str):
    bot = Bot(token=bot_token)

    print(f"📤 Sending dubbed video to Telegram...")
    print(f"   Chat ID: {chat_id}")
    print(f"   Video: {video_path} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")

    async with bot:
        with open(video_path, "rb") as video_file:
            message = await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60,
            )

    print(f"✅ Video sent! Message ID: {message.message_id}")
    return message.message_id


async def send_notification(bot_token: str, chat_id: str, text: str):
    bot = Bot(token=bot_token)
    async with bot:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
    print("📨 Fallback notification sent")


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    # Where the finished dubbed video gets posted. Falls back to the source
    # chat the video came from if no explicit output chat is configured.
    chat_id = os.environ.get("TELEGRAM_OUTPUT_CHAT_ID", "").strip()

    script_path = OUTPUT_DIR / "translated_script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    if not chat_id:
        meta_path = OUTPUT_DIR / "source_meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            chat_id = meta.get("source_chat_id", "")

    if not chat_id:
        raise RuntimeError(
            "No destination chat: set TELEGRAM_OUTPUT_CHAT_ID or ensure "
            "output/source_meta.json has a source_chat_id."
        )

    if not FINAL_PATH.exists():
        print("❌ Final video file not found!")
        asyncio.run(send_notification(
            bot_token, chat_id,
            "⚠️ Dubbing pipeline ran but the final video file is missing."
        ))
        return

    caption = build_caption(script_data)
    print(f"📝 Caption ({len(caption)} chars):\n{caption}\n")

    try:
        asyncio.run(send_video(bot_token, chat_id, FINAL_PATH, caption))
        print("\n🎉 Pipeline complete! Dubbed video sent to Telegram.")
    except Exception as e:
        print(f"❌ Failed to send video: {e}")
        asyncio.run(send_notification(
            bot_token, chat_id,
            f"⚠️ Failed to send dubbed video: {e}"
        ))
        raise


if __name__ == "__main__":
    main()

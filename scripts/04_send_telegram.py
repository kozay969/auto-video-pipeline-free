"""
Step 4: Send final video + caption to Telegram channel/group
Uses python-telegram-bot
"""

import os
import json
import asyncio
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode

OUTPUT_DIR = Path("output")


def build_caption(script_data: dict) -> str:
    """Build Telegram post caption with formatting."""

    title = script_data.get("title", "")
    description = script_data.get("description", "")
    key_facts = script_data.get("key_facts", [])
    category = script_data.get("category", "General Knowledge")
    duration = script_data.get("video_duration_seconds", 180)

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    facts_text = "\n".join([f"  ✦ {f}" for f in key_facts[:3]])

    caption = (
        f"📚 *{title}*\n\n"
        f"{description}\n\n"
        f"🔑 *အဓိက အချက်များ:*\n"
        f"{facts_text}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏷️ #{category.split('(')[0].strip().replace(' ', '_')}\n"
        f"⏱️ ကြာချိန် - {minutes}:{seconds:02d} မိနစ်\n"
        f"🇲🇲 Myanmar Knowledge Channel"
    )

    # Telegram caption max 1024 chars
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    return caption


async def send_video(
    bot_token: str,
    chat_id: str,
    video_path: Path,
    caption: str,
):
    """Send video to Telegram."""

    bot = Bot(token=bot_token)

    print(f"📤 Sending video to Telegram...")
    print(f"   Chat ID: {chat_id}")
    print(f"   Video: {video_path} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")

    async with bot:
        # Send video
        with open(video_path, "rb") as video_file:
            message = await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                # Thumbnail optional - skip if not available
                width=1080,
                height=1920,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60,
            )

    print(f"✅ Video sent! Message ID: {message.message_id}")
    return message.message_id


async def send_notification(bot_token: str, chat_id: str, script_data: dict):
    """Fallback: send text notification if video send fails."""
    bot = Bot(token=bot_token)

    title = script_data.get("title", "New Content")
    text = (
        f"🎬 *New Video Generated*\n\n"
        f"📚 {title}\n\n"
        f"⚠️ Video file could not be sent directly.\n"
        f"Check GitHub Actions artifacts for the video file."
    )

    async with bot:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )
    print("📨 Fallback notification sent")


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    # Load script metadata
    script_path = OUTPUT_DIR / "script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    video_path = OUTPUT_DIR / "final_video.mp4"

    if not video_path.exists():
        print("❌ Video file not found!")
        asyncio.run(send_notification(bot_token, chat_id, script_data))
        return

    caption = build_caption(script_data)
    print(f"📝 Caption ({len(caption)} chars):\n{caption}\n")

    try:
        asyncio.run(send_video(bot_token, chat_id, video_path, caption))
        print("\n🎉 Pipeline complete! Video sent to Telegram.")
    except Exception as e:
        print(f"❌ Failed to send video: {e}")
        print("📨 Sending fallback notification...")
        asyncio.run(send_notification(bot_token, chat_id, script_data))
        raise


if __name__ == "__main__":
    main()

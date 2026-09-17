"""
Step 3: Render video using FFmpeg
- Audio from edge-tts
- Background: animated gradient + title overlay
- Subtitle-style text display
- Output: 1080x1920 (vertical/reels format) or 1920x1080 (landscape)
"""

import os
import json
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # Vertical (Telegram/Reels friendly)
FPS = 30
FONT_SIZE_TITLE = 72
FONT_SIZE_BODY = 52


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def create_background_image(title: str, key_facts: list[str]) -> Path:
    """Create a single high-quality background PNG."""

    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), color=(15, 15, 30))
    draw = ImageDraw.Draw(img)

    # Gradient background simulation
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        r = int(15 + ratio * 20)
        g = int(15 + ratio * 10)
        b = int(30 + ratio * 40)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

    # Decorative circles (blurred effect via layered drawing)
    for cx, cy, cr, alpha_color in [
        (900, 200, 300, (255, 180, 50, 30)),
        (100, 1700, 250, (50, 150, 255, 25)),
        (540, 960, 400, (200, 100, 255, 15)),
    ]:
        for offset in range(0, 30, 5):
            glow_color = (
                alpha_color[0],
                alpha_color[1],
                alpha_color[2],
            )
            draw.ellipse(
                [cx - cr - offset, cy - cr - offset,
                 cx + cr + offset, cy + cr + offset],
                outline=glow_color, width=2
            )

    # Try to load Noto Sans Myanmar font (installed via apt)
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansMyanmar-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    title_font = None
    body_font = None

    for fp in font_paths:
        if Path(fp).exists():
            try:
                title_font = ImageFont.truetype(fp, FONT_SIZE_TITLE)
                body_font = ImageFont.truetype(fp, FONT_SIZE_BODY)
                break
            except Exception:
                continue

    if title_font is None:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # ── TOP BADGE ──
    badge_text = "📚 General Knowledge"
    draw.rounded_rectangle(
        [50, 120, VIDEO_WIDTH - 50, 210],
        radius=40, fill=(255, 200, 50, 200)
    )
    draw.text((VIDEO_WIDTH // 2, 165), badge_text,
              font=body_font, fill=(30, 30, 30), anchor="mm")

    # ── TITLE ──
    wrapped_title = textwrap.fill(title, width=20)
    title_y = 280
    for line in wrapped_title.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2
        # Shadow
        draw.text((x + 3, title_y + 3), line, font=title_font, fill=(0, 0, 0, 180))
        # Text
        draw.text((x, title_y), line, font=title_font, fill=(255, 255, 255))
        title_y += FONT_SIZE_TITLE + 15

    # ── DIVIDER ──
    draw.line([(80, title_y + 20), (VIDEO_WIDTH - 80, title_y + 20)],
              fill=(255, 200, 50), width=4)
    title_y += 60

    # ── KEY FACTS ──
    draw.text((VIDEO_WIDTH // 2, title_y), "🔑 အဓိက အချက်များ",
              font=body_font, fill=(255, 200, 50), anchor="mm")
    title_y += FONT_SIZE_BODY + 30

    for fact in key_facts[:3]:
        wrapped = textwrap.fill(f"• {fact}", width=28)
        for line in wrapped.split("\n"):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            w = bbox[2] - bbox[0]
            x = (VIDEO_WIDTH - w) // 2
            draw.text((x, title_y), line, font=body_font, fill=(220, 220, 220))
            title_y += FONT_SIZE_BODY + 10
        title_y += 10

    # ── BOTTOM BRANDING ──
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 120),
              "🇲🇲 Myanmar Knowledge Channel",
              font=body_font, fill=(150, 150, 150), anchor="mm")

    bg_path = OUTPUT_DIR / "background.png"
    img.save(bg_path, "PNG")
    print(f"🎨 Background image created: {bg_path}")
    return bg_path


def render_video(bg_path: Path, audio_path: Path, duration: float) -> Path:
    """Render final video using FFmpeg."""

    output_path = OUTPUT_DIR / "final_video.mp4"

    # FFmpeg command:
    # - Loop background image for full duration
    # - Add audio
    # - Fade in/out
    # - H264 encoding for Telegram compatibility
    cmd = [
        "ffmpeg", "-y",
        # Input: looped background image
        "-loop", "1",
        "-i", str(bg_path),
        # Input: audio
        "-i", str(audio_path),
        # Map streams
        "-map", "0:v",
        "-map", "1:a",
        # Duration matches audio
        "-t", str(duration),
        # Video codec
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        # Audio codec
        "-c:a", "aac",
        "-b:a", "192k",
        # Resolution
        "-vf", (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            "fade=t=in:st=0:d=1,"
            f"fade=t=out:st={duration-2:.1f}:d=2"
        ),
        # Framerate
        "-r", str(FPS),
        # Telegram max file size optimization
        "-movflags", "+faststart",
        str(output_path),
    ]

    print("🎬 Rendering video with FFmpeg...")
    print(f"   Duration: {duration:.1f}s | Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-2000:])
        raise Exception(f"FFmpeg failed with code {result.returncode}")

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Video rendered: {output_path} ({file_size_mb:.1f} MB)")

    # Telegram limit check (50MB for bots)
    if file_size_mb > 45:
        print("⚠️  Video > 45MB, re-encoding at lower quality...")
        output_path = compress_video(output_path)

    return output_path


def compress_video(input_path: Path) -> Path:
    """Compress video if too large for Telegram."""
    output_path = OUTPUT_DIR / "final_video_compressed.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-crf", "28", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True)
    input_path.unlink()  # Remove original
    output_path.rename(input_path)
    print(f"✅ Compressed: {input_path.stat().st_size / 1024 / 1024:.1f} MB")
    return input_path


def main():
    # Load script data
    script_path = OUTPUT_DIR / "script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    audio_path = OUTPUT_DIR / "audio.mp3"

    # Get actual audio duration
    duration = get_audio_duration(audio_path)
    print(f"⏱️  Audio duration: {duration:.1f}s ({duration/60:.1f} min)")

    # Create background
    bg_path = create_background_image(
        title=script_data.get("title", "General Knowledge"),
        key_facts=script_data.get("key_facts", [])
    )

    # Render video
    video_path = render_video(bg_path, audio_path, duration)

    # Update metadata
    script_data["video_duration_seconds"] = round(duration, 1)
    script_data["video_size_mb"] = round(video_path.stat().st_size / 1024 / 1024, 2)

    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Video ready: {video_path}")


if __name__ == "__main__":
    main()

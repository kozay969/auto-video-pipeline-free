"""
Step 5: Replace the original video's audio track with the dubbed track,
keeping the picture untouched. Output duration is pinned to the original
video's duration so the two stay in sync.
"""

import json
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("output")
VIDEO_PATH = OUTPUT_DIR / "source_video.mp4"
AUDIO_PATH = OUTPUT_DIR / "dubbed_audio.mp3"
FINAL_PATH = OUTPUT_DIR / "final_dubbed_video.mp4"


def merge(video_path: Path, audio_path: Path, duration: float, output_path: Path):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        "-shortest",
        str(output_path),
    ]
    print("🎬 Merging dubbed audio into original video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr (copy mode):", result.stderr[-1500:])
        print("↩️  Retrying with re-encode (source codec may be incompatible with copy)...")
        cmd_reencode = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.3f}",
            "-movflags", "+faststart",
            "-shortest",
            str(output_path),
        ]
        result2 = subprocess.run(cmd_reencode, capture_output=True, text=True)
        if result2.returncode != 0:
            print("FFmpeg stderr (re-encode):", result2.stderr[-1500:])
            raise RuntimeError("Merging video + dubbed audio failed")


def compress_video(path: Path) -> Path:
    """Re-encode to a smaller file if it's over GitHub's release-asset limit."""
    compressed = OUTPUT_DIR / "final_dubbed_video_compressed.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", str(path),
        "-c:v", "libx264", "-crf", "28", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(compressed),
    ]
    subprocess.run(cmd, capture_output=True)
    path.unlink()
    compressed.rename(path)
    print(f"✅ Compressed: {path.stat().st_size / 1024 / 1024:.1f} MB")
    return path


def main():
    script_path = OUTPUT_DIR / "translated_script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    duration = script_data["video_duration_seconds"]

    merge(VIDEO_PATH, AUDIO_PATH, duration, FINAL_PATH)

    size_mb = FINAL_PATH.stat().st_size / 1024 / 1024
    print(f"✅ Final video: {FINAL_PATH} ({size_mb:.1f} MB)")

    if size_mb > 2000:
        print("⚠️  Video > 2GB (GitHub release-asset limit), re-encoding at lower quality...")
        compress_video(FINAL_PATH)
        size_mb = FINAL_PATH.stat().st_size / 1024 / 1024

    script_data["final_video_size_mb"] = round(size_mb, 2)
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Dubbed video ready: {FINAL_PATH}")


if __name__ == "__main__":
    main()
    

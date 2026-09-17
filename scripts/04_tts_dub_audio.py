"""
Step 4: Turn each translated segment into speech (edge-tts, free) and
time-stretch it to fit the original segment's start/end window, so the
final dubbed audio track lines up with the picture. Gaps between segments
(and before the first one) are filled with silence.

Output: output/dubbed_audio.mp3
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts

OUTPUT_DIR = Path("output")
WORK_DIR = OUTPUT_DIR / "tts_chunks"
WORK_DIR.mkdir(parents=True, exist_ok=True)

# Myanmar voices available in edge-tts:
#   my-MM-ThihaNeural  (male)
#   my-MM-NilarNeural  (female)
DEFAULT_VOICE = "my-MM-ThihaNeural"

MIN_ATEMPO = 0.5
MAX_ATEMPO = 2.0


def get_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    out = result.stdout.strip()
    return float(out) if out else 0.0


async def synthesize(text: str, voice: str, dest: Path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(dest))


def make_silence(duration: float, dest: Path):
    duration = max(duration, 0.02)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono",
        "-t", f"{duration:.3f}",
        "-q:a", "9",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True)


def atempo_filter_chain(factor: float) -> str:
    """ffmpeg's atempo filter only accepts 0.5–2.0 per instance; chain
    multiple instances for factors outside that range."""
    factor = max(min(factor, 4.0), 0.25)  # sane outer bound
    filters = []
    remaining = factor
    while remaining < MIN_ATEMPO or remaining > MAX_ATEMPO:
        step = MAX_ATEMPO if remaining > MAX_ATEMPO else MIN_ATEMPO
        filters.append(f"atempo={step}")
        remaining /= step
    filters.append(f"atempo={remaining:.4f}")
    return ",".join(filters)


def stretch_to_duration(src: Path, dest: Path, target_duration: float):
    src_duration = get_duration(src)
    if src_duration <= 0:
        make_silence(target_duration, dest)
        return

    factor = src_duration / target_duration if target_duration > 0 else 1.0
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-filter:a", atempo_filter_chain(factor),
        "-t", f"{target_duration:.3f}",
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-1000:])
        # Fall back to silence rather than crashing the whole pipeline
        make_silence(target_duration, dest)


def concat_pieces(pieces: list[Path], dest: Path):
    list_file = WORK_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in pieces:
            f.write(f"file '{p.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-2000:])
        raise RuntimeError("Concat of dubbed audio pieces failed")


async def run(voice: str):
    script_path = OUTPUT_DIR / "translated_script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    segments = script_data["segments"]
    video_duration = script_data["video_duration_seconds"]

    pieces = []
    cursor = 0.0

    for seg in segments:
        start, end = seg["start"], seg["end"]
        text = seg["translated_text"].strip()

        # Silence to fill the gap before this segment starts
        gap = start - cursor
        if gap > 0.05:
            gap_path = WORK_DIR / f"gap_{seg['id']:04d}.mp3"
            make_silence(gap, gap_path)
            pieces.append(gap_path)

        target_duration = max(end - start, 0.1)

        if text:
            raw_path = WORK_DIR / f"raw_{seg['id']:04d}.mp3"
            print(f"  🔊 [{seg['id']}] TTS: {text[:40]!r}...")
            await synthesize(text, voice, raw_path)

            fitted_path = WORK_DIR / f"fit_{seg['id']:04d}.mp3"
            stretch_to_duration(raw_path, fitted_path, target_duration)
            pieces.append(fitted_path)
        else:
            silence_path = WORK_DIR / f"empty_{seg['id']:04d}.mp3"
            make_silence(target_duration, silence_path)
            pieces.append(silence_path)

        cursor = end

    # Trailing silence so the audio track covers the whole video
    trailing = video_duration - cursor
    if trailing > 0.05:
        trail_path = WORK_DIR / "trail.mp3"
        make_silence(trailing, trail_path)
        pieces.append(trail_path)

    print(f"🔗 Concatenating {len(pieces)} audio piece(s)...")
    dubbed_path = OUTPUT_DIR / "dubbed_audio.mp3"
    concat_pieces(pieces, dubbed_path)

    final_duration = get_duration(dubbed_path)
    print(f"✅ Dubbed audio: {dubbed_path} ({final_duration:.1f}s, video is {video_duration:.1f}s)")

    script_data["dubbed_audio_duration_seconds"] = round(final_duration, 2)
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)


def main():
    voice = os.environ.get("EDGE_TTS_VOICE", DEFAULT_VOICE)
    asyncio.run(run(voice))


if __name__ == "__main__":
    main()

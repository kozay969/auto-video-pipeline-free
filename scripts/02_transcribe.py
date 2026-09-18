"""
Step 2: Extract audio from the downloaded video and transcribe it with
faster-whisper (runs locally, free, no API key — auto-detects the spoken
language).

Output: output/transcript.json
{
  "source_language": "en",
  "video_duration_seconds": 187.4,
  "full_text": "...",
  "segments": [
    {"id": 0, "start": 0.0, "end": 4.2, "text": "..."},
    ...
  ]
}
"""

import os
import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_PATH = OUTPUT_DIR / "source_video.mp4"
AUDIO_PATH = OUTPUT_DIR / "source_audio.wav"


def get_video_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def extract_audio(video_path: Path, audio_path: Path):
    """Pull a 16kHz mono WAV out of the video for Whisper."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        str(audio_path),
    ]
    print("🎧 Extracting audio track...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-2000:])
        raise RuntimeError("Audio extraction failed")


def transcribe(audio_path: Path, model_size: str) -> dict:
    print(f"🧠 Loading faster-whisper model: {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print("📝 Transcribing (this can take a while on CPU)...")
    segments_iter, info = model.transcribe(
        str(audio_path),
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segments = []
    full_text_parts = []
    for i, seg in enumerate(segments_iter):
        text = seg.text.strip()
        if not text:
            continue
        segments.append({
            "id": i,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": text,
        })
        full_text_parts.append(text)

    print(f"🌐 Detected language: {info.language} (p={info.language_probability:.2f})")
    print(f"📦 {len(segments)} segment(s) transcribed")

    return {
        "source_language": info.language,
        "source_language_probability": round(info.language_probability, 3),
        "full_text": " ".join(full_text_parts),
        "segments": segments,
    }


def main():
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"{VIDEO_PATH} not found — run step 1 first")

    model_size = os.environ.get("WHISPER_MODEL_SIZE", "small")

    duration = get_video_duration(VIDEO_PATH)
    extract_audio(VIDEO_PATH, AUDIO_PATH)

    data = transcribe(AUDIO_PATH, model_size)
    data["video_duration_seconds"] = round(duration, 2)

    transcript_path = OUTPUT_DIR / "transcript.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved: {transcript_path}")
    print(f"📄 Preview: {data['full_text'][:200]}...")


if __name__ == "__main__":
    main()
  

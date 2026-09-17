"""
Step 2: Convert Myanmar script to audio using edge-tts (free, Microsoft Edge voices)
No API key required.
"""

import os
import json
import asyncio
import edge_tts
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Myanmar voices available in edge-tts:
#   my-MM-ThihaNeural  (male)
#   my-MM-NilarNeural  (female)
DEFAULT_VOICE = "my-MM-ThihaNeural"


def split_text_chunks(text: str, max_chars: int = 4000) -> list[str]:
    """Split long text into chunks respecting paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


async def text_to_speech(text: str, voice: str, output_path: Path):
    """Call edge-tts and save audio directly to output_path."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def merge_audio_files(file_paths: list[Path], output_path: Path):
    """Merge multiple MP3 files using binary concatenation."""
    with open(output_path, "wb") as out_f:
        for fp in file_paths:
            with open(fp, "rb") as in_f:
                out_f.write(in_f.read())
    print(f"🔗 Merged {len(file_paths)} audio chunks → {output_path}")


async def run(voice: str):
    # Load script
    script_path = OUTPUT_DIR / "script.json"
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    script_text = script_data["script"]
    print(f"📖 Script loaded: {len(script_text)} characters")

    chunks = split_text_chunks(script_text)
    print(f"📦 Split into {len(chunks)} chunk(s)")

    audio_path = OUTPUT_DIR / "audio.mp3"

    if len(chunks) == 1:
        print(f"🔊 Sending to edge-tts... ({len(chunks[0])} chars)")
        await text_to_speech(chunks[0], voice, audio_path)
        print(f"✅ Audio saved: {audio_path}")
    else:
        chunk_paths = []
        for i, chunk in enumerate(chunks):
            print(f"  🔄 Processing chunk {i+1}/{len(chunks)}...")
            chunk_path = OUTPUT_DIR / f"audio_chunk_{i:02d}.mp3"
            await text_to_speech(chunk, voice, chunk_path)
            chunk_paths.append(chunk_path)

        merge_audio_files(chunk_paths, audio_path)

        for cp in chunk_paths:
            cp.unlink()

    audio_size = audio_path.stat().st_size
    script_data["audio_size_kb"] = round(audio_size / 1024, 1)

    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ TTS complete! Audio: {audio_size/1024:.1f} KB")


def main():
    voice = os.environ.get("EDGE_TTS_VOICE", DEFAULT_VOICE)
    asyncio.run(run(voice))


if __name__ == "__main__":
    main()

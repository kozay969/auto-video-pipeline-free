"""
Step 3: Translate every transcript segment into the target language
(default: Myanmar) using the Gemini API (free tier), keeping the segment
order/count intact so timestamps still line up 1:1.

Also asks Gemini for a short title + description in the target language,
used later for the Telegram caption.

Output: output/translated_script.json
{
  "source_language": "en",
  "target_language": "my",
  "title": "...",
  "description": "...",
  "video_duration_seconds": 187.4,
  "segments": [
    {"id": 0, "start": 0.0, "end": 4.2,
     "source_text": "...", "translated_text": "..."},
    ...
  ]
}
"""

import os
import json
from pathlib import Path
from google import genai
from google.genai import types

OUTPUT_DIR = Path("output")

LANGUAGE_NAMES = {
    "my": "Myanmar (Burmese)",
    "en": "English",
}


def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def translate_batch(client: genai.Client, texts: list[str], target_lang_name: str) -> list[str]:
    """Translate a batch of strings, returning the same number of strings in order."""

    numbered = "\n".join(f"{i}: {t}" for i, t in enumerate(texts))

    prompt = f"""You are a professional subtitle/dubbing translator.
Translate each numbered line below into {target_lang_name}.
Keep the tone natural for spoken narration (not overly literal).
Keep each translation reasonably close in length to the original so it fits
a similar amount of speaking time.

Lines:
{numbered}

Respond with ONLY a JSON array of {len(texts)} strings, in the same order,
one translated string per input line. No other text, no markdown fences."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.LOW
            ),
        ),
    )

    raw = (response.text or "").strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    result = json.loads(raw)
    if len(result) != len(texts):
        raise ValueError(
            f"Translation batch size mismatch: sent {len(texts)}, got {len(result)}"
        )
    return result


def generate_title_description(client: genai.Client, full_text: str, target_lang_name: str) -> dict:
    prompt = f"""Read this video narration (may be in any language):

\"\"\"{full_text[:3000]}\"\"\"

Write, in {target_lang_name}:
- a short catchy video title
- a 2-sentence description
- up to 3 key facts / highlights from the content

Respond with ONLY this JSON object, no markdown fences:
{{"title": "...", "description": "...", "key_facts": ["...", "...", "..."]}}"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1024,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.LOW
            ),
        ),
    )

    raw = (response.text or "").strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


def main():
    transcript_path = OUTPUT_DIR / "transcript.json"
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    target_lang = os.environ.get("TARGET_LANGUAGE", "my")
    target_lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    segments = transcript["segments"]
    texts = [s["text"] for s in segments]

    print(f"🌐 Translating {len(texts)} segment(s) into {target_lang_name}...")

    translated_texts = []
    for batch in chunk(texts, 40):  # keep prompts small enough for one call
        translated_texts.extend(translate_batch(client, batch, target_lang_name))

    print("📝 Generating title/description...")
    meta = generate_title_description(client, transcript["full_text"], target_lang_name)

    out_segments = []
    for seg, translated in zip(segments, translated_texts):
        out_segments.append({
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "source_text": seg["text"],
            "translated_text": translated,
        })

    data = {
        "source_language": transcript.get("source_language"),
        "target_language": target_lang,
        "title": meta.get("title", "Dubbed Video"),
        "description": meta.get("description", ""),
        "key_facts": meta.get("key_facts", []),
        "video_duration_seconds": transcript["video_duration_seconds"],
        "segments": out_segments,
    }

    out_path = OUTPUT_DIR / "translated_script.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved: {out_path}")
    print(f"📋 Title: {data['title']}")


if __name__ == "__main__":
    main()
  

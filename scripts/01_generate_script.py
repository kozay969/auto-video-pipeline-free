"""
Step 1: Generate General Knowledge content + Myanmar translation script
Uses Google Gemini API (free tier - no cost for this volume)
"""

import os
import json
import random
from google import genai
from google.genai import types
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# General Knowledge topic categories
TOPIC_CATEGORIES = [
    "သိပ္ပံနှင့် နည်းပညာ (Science & Technology)",
    "သဘာဝပတ်ဝန်းကျင် (Nature & Environment)",
    "သမိုင်း (History)",
    "ကျန်းမာရေး (Health & Body)",
    "အာကာသ (Space & Universe)",
    "တိရိစ္ဆာန်များ (Animals & Wildlife)",
    "ဘူမိဗေဒ (Geography & Earth)",
    "မျိုးစိတ်ထူးဆန်းမှုများ (Fascinating Facts)",
]

def generate_script(topic_hint: str = "") -> dict:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Pick random category if no hint
    category = topic_hint if topic_hint else random.choice(TOPIC_CATEGORIES)

    prompt = f"""သင်သည် မြန်မာဘာသာ YouTube/Telegram content creator တစ်ယောက်ဖြစ်သည်။

အောက်ပါ topic အတွက် **3 မိနစ်** ကြာသော video script တစ်ခု ရေးပေးပါ။
Topic: {category}

လိုအပ်ချက်များ:
- ကြာချိန်: 3 မိနစ် (စကားလုံး ~450-480 လုံး)
- ဘာသာ: မြန်မာဘာသာ (ရိုးရှင်းသော ပြောဆိုသည့် ဘာသာ)
- Format: YouTube/Telegram video narration (hook → content → outro)
- အစပိုင်းမှာ စိတ်ဝင်စားဖွယ် hook ထည့်ပါ
- အချက်အလက်များ မှန်ကန်ရမည်
- ဖတ်ရတာ အဆင်ပြေသော paragraph များ ခွဲရေးပါ

ထို့နောက် JSON format ဖြင့် ဤပုံစံအတိုင်း ထုတ်ပေးပါ:

```json
{{
  "topic": "topic name in Myanmar",
  "category": "{category}",
  "title": "video title (catchy, Myanmar)",
  "description": "short 2-sentence description",
  "script": "full narration script here...",
  "word_count": 0,
  "key_facts": ["fact1", "fact2", "fact3"]
}}
```

JSON တစ်ခုတည်းသာ ထုတ်ပေးပါ။ အခြား text မထည့်ပါနှင့်။"""

    print(f"📝 Generating script for: {category}")

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            # Keep thinking minimal — this is a straightforward generation task,
            # and thinking tokens count against max_output_tokens, so a high
            # thinking level can silently eat the whole budget and leave no
            # room for the actual answer.
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.LOW
            ),
        ),
    )

    raw = (response.text or "").strip()

    if not raw:
        # Surface the raw response for debugging instead of a bare JSON error
        raise RuntimeError(
            f"Empty response from Gemini. Full response: {response.model_dump_json(exclude_none=True)}"
        )

    # Extract JSON from response
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    data = json.loads(raw)

    # Count words
    data["word_count"] = len(data["script"].split())
    data["estimated_duration_seconds"] = int(data["word_count"] * 0.45 * 60 / 150)  # ~150 words/min for Myanmar

    print(f"✅ Script generated: {data['title']}")
    print(f"   Words: {data['word_count']} | Est. duration: {data['estimated_duration_seconds']}s")

    return data


def main():
    topic_hint = os.environ.get("TOPIC_HINT", "").strip()

    script_data = generate_script(topic_hint)

    # Save to output
    output_path = OUTPUT_DIR / "script.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved: {output_path}")
    print(f"📋 Title: {script_data['title']}")
    print(f"📄 Preview:\n{script_data['script'][:200]}...")


if __name__ == "__main__":
    main()
    

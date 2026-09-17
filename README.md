# 🎬 Auto Video Dub Pipeline — Telegram Video ➜ Myanmar Dub

Telegram ကို ပို့လိုက်တဲ့ video ကို auto scan ဖမ်းယူပြီး — **script ထုတ် (JSON) → ဘာသာပြန် → အသံသွင်း → မူရင်း video နဲ့ timing ကိုက်အောင် ပြန်ပေါင်း → Telegram ကို ပြန်ပို့** လုပ်ပေးတဲ့ GitHub Actions workflow။

---

## 📋 Pipeline Flow

```
Telegram Bot        faster-whisper       Gemini API         edge-tts (free)        FFmpeg              Telegram Bot
────────────   →   ───────────────  →  ─────────────  →  ──────────────────  →  ───────────────  →  ───────────
Video လက်ခံ         Script ထုတ်          ဘာသာပြန်          Segment တစ်ခုချင်း       Timing ကိုက်အောင်      Dub ထားသော
(auto scan)         (JSON, timestamp     (မြန်မာ)           အသံသွင်း                audio ကို video        video ပို့
                     အပါ)                                  (timing stretch)        ထဲပြန်ထည့်
```

> 💰 **API cost — Gemini free tier + edge-tts (key မလို) + faster-whisper (local, free) သုံးထားပါတယ်။**

---

## ⚙️ Setup — GitHub Secrets

Repository → Settings → Secrets and Variables → Actions → **Secrets** tab

| Secret Name | ဘာမလဲ | ဘယ်မှာရမလဲ |
|-------------|--------|------------|
| `GEMINI_API_KEY` | ဘာသာပြန်ဖို့ Gemini API key (**free**) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `TELEGRAM_BOT_TOKEN` | Bot token | [@BotFather](https://t.me/BotFather) |

Repository → Settings → Secrets and Variables → Actions → **Variables** tab (optional)

| Variable Name | ဘာမလဲ | Default |
|----------------|--------|---------|
| `TELEGRAM_SOURCE_CHAT_ID` | ဒီ chat ကလာတဲ့ video ကိုပဲ လက်ခံမယ် (မထည့်ရင် bot မြင်နိုင်တဲ့ chat ဘယ်ကမဆို လက်ခံမယ်) | (empty = any) |
| `TELEGRAM_OUTPUT_CHAT_ID` | Dub ပြီးသား video ကို ဘယ် chat/channel ကို ပို့မလဲ | (empty = video ရောက်လာတဲ့ chat ကို ပြန်ပို့) |
| `TARGET_LANGUAGE` | ဘာသာပြန်မယ့် ဘာသာစကား code | `my` (Myanmar) |
| `EDGE_TTS_VOICE` | Myanmar voice ရွေးချင်ရင် | `my-MM-ThihaNeural` (male). `my-MM-NilarNeural` က အမျိုးသမီးအသံ |
| `WHISPER_MODEL_SIZE` | Speech-to-text model size (`tiny`/`base`/`small`/`medium`) | `small` |

### Telegram Chat ID ရယူနည်း
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
ဆိုပြီး browser မှာ ဖွင့်ပါ၊ `"chat":{"id": ...}` ကို copy ယူပါ (group/channel အတွက် negative number ဖြစ်နိုင်ပါတယ်)။

---

## 🚀 အလုပ်လုပ်ပုံ

1. Video ကို bot ဆီ (DM / group / channel — bot ပါဝင်ထားရမယ်) ပို့ပါ။
2. Workflow က **၁၅ မိနစ်တစ်ခါ** auto run ဖြစ်ပြီး Telegram ကို scan လုပ်ပါလိမ့်မယ် (`getUpdates` polling)။ Video အသစ်တွေ့ရင်ပဲ ကျန်တဲ့ step တွေ run ပါလိမ့်မယ်။
3. Manual run ချင်ရင် **Actions → Auto Video Dub Pipeline → Run workflow** လုပ်နိုင်ပါတယ် (ဒါပေမယ့် video က Telegram ဘက်မှာ ရောက်နေဖို့လိုပါတယ်၊ ဒီ run က scan ပဲလုပ်ပေးတာပါ)။
4. Pipeline ပြီးရင် dub လုပ်ထားတဲ့ video ကို configured chat ကို ပြန်ပို့ပါလိမ့်မယ်။

### Processed-video tracking
`state/last_update_id.txt` ဖိုင်က နောက်ဆုံးကြည့်ပြီးသား Telegram update id ကို မှတ်ထားပါတယ် — run တိုင်းအလိုအလျောက် commit ပြန်တင်ပေးမှာဖြစ်လို့ video တစ်ခုကို ထပ်ခါထပ်ခါ မ process ပါဘူး။

---

## 📁 File Structure

```
.
├── .github/
│   └── workflows/
│       └── auto-video-pipeline.yml     # Main workflow (15 မိနစ်တစ်ခါ polling)
├── scripts/
│   ├── 01_fetch_telegram_video.py      # Telegram scan + video download
│   ├── 02_transcribe.py                # faster-whisper → transcript.json (timestamps)
│   ├── 03_translate_script.py          # Gemini → translated_script.json
│   ├── 04_tts_dub_audio.py             # edge-tts → segment-by-segment, timing ကိုက်အောင် stretch
│   ├── 05_merge_video.py               # FFmpeg → မူရင်း video + dub audio ပေါင်း
│   └── 06_send_telegram.py             # Telegram Bot → dub ပြီးသား video ပို့
├── state/
│   └── last_update_id.txt              # Processed watermark (auto-committed)
├── requirements.txt
└── README.md
```

---

## 📄 JSON Script Format (Step 2 & 3 output)

`output/transcript.json` (Step 2 — မူရင်းဘာသာ):
```json
{
  "source_language": "en",
  "video_duration_seconds": 187.4,
  "full_text": "...",
  "segments": [
    {"id": 0, "start": 0.0, "end": 4.2, "text": "..."}
  ]
}
```

`output/translated_script.json` (Step 3 — ဘာသာပြန်ပြီး, TTS/merge အတွက် သုံးမည်):
```json
{
  "source_language": "en",
  "target_language": "my",
  "title": "...",
  "description": "...",
  "key_facts": ["...", "..."],
  "video_duration_seconds": 187.4,
  "segments": [
    {"id": 0, "start": 0.0, "end": 4.2,
     "source_text": "...", "translated_text": "..."}
  ]
}
```

---

## 🎯 Timing ကိုက်ညီအောင် ဘယ်လို လုပ်ထားလဲ

Whisper က segment တစ်ခုချင်းစီရဲ့ `start`/`end` ကို ထုတ်ပေးလို့:
1. Segment တစ်ခုချင်းစီကို သီးခြား TTS လုပ်ပြီး
2. FFmpeg ရဲ့ `atempo` filter နဲ့ generate ထွက်လာတဲ့ audio ကို မူရင်း segment duration အတိုင်း stretch/compress လုပ်ပြီး
3. Segment ကြားက အချိန်ကွာဟမှုတွေကို silence နဲ့ဖြည့်ပြီး
4. အားလုံးကို concat လုပ်ပြီး မူရင်း video length အတိုင်း တစ်ခုတည်းသော audio track အဖြစ် ပေါင်းလိုက်ပါတယ်။

ဒါက စာသားအရှည်ကွာခြားမှုကြောင့် အသံနှုန်း အနည်းငယ် ပြောင်းသွားနိုင်ပေမယ့် video ရဲ့ ရှုပ်ထွေးတဲ့ lip-sync အထိ မမျှော်လင့်ပါနှင့် — scene timing/pacing ကိုပဲ တိကျအောင် ချိန်ညှိပေးတာပါ။

---

## 🎥 Output Video Specs

| Property | Value |
|----------|-------|
| Video | မူရင်း video stream (ဖြစ်နိုင်ရင် re-encode မလုပ်ဘဲ copy) |
| Audio | AAC 192kbps, dubbed |
| Duration | မူရင်း video duration အတိုင်း |
| Max Size | 45 MB (ကျော်ရင် auto-compress) |

---

## 🔧 Customization

- **Model size / speed vs accuracy**: `WHISPER_MODEL_SIZE` variable (`tiny` အမြန်ဆုံး, `medium` တိကျဆုံး)
- **Polling frequency**: `.github/workflows/auto-video-pipeline.yml` ထဲက cron `*/15 * * * *`
- **Voice**: `EDGE_TTS_VOICE` variable
- **Target language**: `TARGET_LANGUAGE` variable + `scripts/03_translate_script.py` ထဲက `LANGUAGE_NAMES` dict ထဲ ဘာသာစကားအသစ်ထည့်နိုင်

---

## ❓ Troubleshooting

**Video ကို bot မသိဘူး / pipeline run မဖြစ်ဘူး:**
- Bot ကို ပို့တဲ့ chat ထဲ ထည့်ထား/admin ချထားပါ (channel ဆို)
- `TELEGRAM_SOURCE_CHAT_ID` ထည့်ထားရင် video ပို့တဲ့ chat id နဲ့ တူမှ pick up လုပ်ပါလိမ့်မယ်
- Workflow run log ထဲက Step 1 output `has_video` ကို check ပါ

**Transcribe မှားနေရင် / ဘာသာစကား မှားသိရင်:**
- `WHISPER_MODEL_SIZE` ကို `medium` လို ပိုကြီးတဲ့ model ပြောင်းကြည့်ပါ (run time ပိုကြာပါလိမ့်မယ်)

**Dub audio က video နဲ့ timing မကိုက်ဘူးလို့ ခံစားရရင်:**
- မူရင်း video ရဲ့ speech segment တွေ အရမ်းတိုတိုတိုတိုနေရင် (fast cuts) stretch ratio က limit (0.5x–2x) ကို ကျော်နိုင်လို့ အနည်းငယ် timing လွဲနိုင်ပါတယ် — ဒါဆို `WHISPER_MODEL_SIZE` ပြောင်း (segment split ပိုကောင်းအောင်) သို့မဟုတ် script logic ကို ကိုယ်တိုင် ချိန်ညှိလို့ရပါတယ်

**FFmpeg / copy codec error:**
- Step 5 က `-c:v copy` ဖြင့် ကြိုးစားပြီး မအောင်မြင်ရင် အလိုအလျောက် re-encode (libx264) ပြန်ကြိုးစားပါတယ်

**Telegram send မအောင်မြင်ရင်:**
- `TELEGRAM_OUTPUT_CHAT_ID` (ရှိရင်) သို့မဟုတ် video ရောက်လာတဲ့ chat id မှန်မမှန် check ပါ
- Bot ကို destination chat/channel မှာ admin/post ခွင့် ရှိမရှိ check ပါ

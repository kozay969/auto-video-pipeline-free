# 🎬 Auto Video Pipeline — Myanmar General Knowledge

ပုံမှန်အလိုအလျောက် General Knowledge video တွေ generate လုပ်ပြီး Telegram ပို့သော GitHub Actions workflow။

---

## 📋 Pipeline Flow

```
Gemini API           edge-tts (free)        FFmpeg              Telegram Bot
────────────   →   ──────────────────  →  ───────────────  →  ───────────
Content ရှာ         Script → MP3 audio     Audio + BG image    Video ပို့
Script ရေး          (Myanmar voice)        → MP4 video (3min)
မြန်မာဘာသာ
```

> 💰 **ဒီ version က API cost လုံးဝ $0 — Gemini free tier + edge-tts (key မလို) သုံးထားပါတယ်။**

---

## ⚙️ Setup — GitHub Secrets

Repository → Settings → Secrets and Variables → Actions → New repository secret

| Secret Name | ဘာမလဲ | ဘယ်မှာရမလဲ |
|-------------|--------|------------|
| `GEMINI_API_KEY` | Gemini API key (**free**) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `TELEGRAM_BOT_TOKEN` | Bot token | [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Channel/Group ID | ကြည့်နည်း အောက်မှာ |

Repository → Settings → Secrets and Variables → Actions → **Variables** tab (optional):

| Variable Name | ဘာမလဲ | Default |
|----------------|--------|---------|
| `EDGE_TTS_VOICE` | Myanmar voice ရွေးချင်ရင် | `my-MM-ThihaNeural` (male). `my-MM-NilarNeural` က အမျိုးသမီးအသံ |

edge-tts က API key လုံးဝမလိုပါ — Microsoft Edge ရဲ့ free public TTS service ကို ခေါ်သုံးတာပါ။

### Telegram Chat ID ရယူနည်း

**Channel အတွက်:**
1. Channel ကို public ချိပြီး `@yourchannel` ကို note ယူ
2. Chat ID = `@yourchannel` (သို့) numeric ID

**Group/Channel numeric ID:**
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
ဆိုပြီး browser မှာ ဖွင့်ပါ၊ `"chat":{"id": -100xxxxxxxxx}` ကို copy ယူပါ

---

## 🚀 Run Workflow

### Automatic (Daily 3:30 PM Myanmar Time)
Workflow ကို push လုပ်ပြီးရင် ပုံမှန် run မည်

### Manual Run
1. GitHub Repository → **Actions** tab
2. **Auto Video Pipeline** → **Run workflow**
3. Topic hint ထည့်လို့ရ (optional) → **Run workflow**

---

## 📁 File Structure

```
.
├── .github/
│   └── workflows/
│       └── auto-video-pipeline.yml   # Main workflow
├── scripts/
│   ├── 01_generate_script.py         # Gemini API (free) → Script
│   ├── 02_tts_edge.py                # edge-tts (free) → Audio
│   ├── 03_render_video.py            # FFmpeg → Video
│   └── 04_send_telegram.py           # Telegram Bot → Send
├── requirements.txt
└── README.md
```

---

## 🎥 Output Video Specs

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1920 (Vertical) |
| Format | MP4 (H.264) |
| Duration | ~3 minutes (audio driven) |
| Audio | AAC 192kbps |
| Max Size | 45 MB (Telegram limit) |

---

## 💰 API Costs (Estimate per video)

| Service | Usage | Cost |
|---------|-------|------|
| Gemini API (free tier) | ~2000 tokens | $0 |
| edge-tts | ~450 chars | $0 |
| Telegram | Free | $0 |
| **Total** | | **$0/video** |

### Free tier limit — သတိထားရန်

Gemini 2.0 Flash free tier က daily/per-minute request limit ရှိပါတယ် (ရက်စဉ် video 1 ခုလောက်ဆို လုံလုံလောက်လောက်ပါ)။ Limit အသေးစိတ်ကို [ai.google.dev/pricing](https://ai.google.dev/pricing) မှာ စစ်ကြည့်နိုင်ပါတယ်။ edge-tts ကတော့ official rate limit မသတ်ထားပေမယ့် အလွန်အကျွံသုံးရင် Microsoft ဘက်က ခဏတရား block ဖြစ်နိုင်ပါတယ် — daily 1 video အတွက်တော့ ပြဿနာမရှိပါ။

---

## 🔧 Customization

### Topic ပြောင်းချင်ရင်
`scripts/01_generate_script.py` မှာ `TOPIC_CATEGORIES` list ပြင်

### Video style ပြောင်းချင်ရင်
`scripts/03_render_video.py` မှာ:
- `VIDEO_WIDTH`, `VIDEO_HEIGHT` — resolution
- Colors, fonts, layout

### Schedule ပြောင်းချင်ရင်
`.github/workflows/auto-video-pipeline.yml` မှာ cron expression ပြင်:
```yaml
- cron: '0 8 * * *'   # UTC time
```
[crontab.guru](https://crontab.guru) မှာ cron expression check လုပ်နိုင်

---

## ❓ Troubleshooting

**Video မ send မဖြစ်ရင်:**
- Telegram Bot ကို channel/group admin ချပါ
- Chat ID မှန်မှန်ကန်ကန် ထည့်ပါ (negative number for groups)

**edge-tts error / audio မထွက်ရင်:**
- Voice name မှန်မမှန် check ပါ (`my-MM-ThihaNeural` / `my-MM-NilarNeural`)
- GitHub Actions runner ကနေ Microsoft TTS endpoint ကို ခေတ္တခဏ block ဖြစ်ခဲ့ရင် workflow ကို ပြန် run ကြည့်ပါ

**Gemini error:**
- `GEMINI_API_KEY` secret မှန်မမှန် check ပါ
- Free tier request limit ကျော်သွားရင် တစ်ခဏစောင့်ပြီး ပြန် run ကြည့်ပါ

**FFmpeg font error:**
- Myanmar font မပါရင် fallback font သုံးမည် — normal ဖြစ်သည်

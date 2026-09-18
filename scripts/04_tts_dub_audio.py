import os
from gtts import gTTS

def generate_dubbed_audio():
    script_path = "processed/translated_script.txt"
    output_audio = "processed/dubbed_audio.mp3"

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"{script_path} not found - run step 3 first")

    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Warning: Script is empty. Using fallback text.")
        text = "မင်္ဂလာပါ"

    print("Generating voiceover using gTTS...")
    
    # Google TTS ဖြင့် မြန်မာအသံ ထုတ်ပေးခြင်း
    try:
        tts = gTTS(text=text, lang='my', slow=False)
        tts.save(output_audio)
        print("Successfully generated Myanmar audio using gTTS.")
    except Exception as e:
        print(f"gTTS Myanmar error: {e}. Falling back to English.")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_audio)

    print(f"Saved dubbed audio to {output_audio}")

if __name__ == "__main__":
    generate_dubbed_audio()
    

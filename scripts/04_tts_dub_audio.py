import os
import asyncio
import edge_tts

async def generate_audio():
    # File Path ကို processed/translated_script.txt ဟု ပြောင်းလဲပေးထားသည်
    script_path = "processed/translated_script.txt"
    output_audio = "processed/dubbed_audio.mp3"

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"{script_path} not found - run step 3 first")

    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Warning: Translated script is empty. Using fallback text.")
        text = "No content to process."

    print("Generating voiceover using Edge TTS...")
    # မြန်မာအသံအတွက် my-MM-NilarNeural သို့မဟုတ် my-MM-ThihaNeural သုံးနိုင်သည်
    voice = "my-MM-NilarNeural"
    communicate = edge_tts.Communicate(text, voice)
    
    os.makedirs("processed", exist_ok=True)
    await communicate.save(output_audio)
    print(f"Saved dubbed audio to {output_audio}")

def main():
    asyncio.run(generate_audio())

if __name__ == "__main__":
    main()
    

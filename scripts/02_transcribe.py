import os
from faster_whisper import WhisperModel

def main():
    # ဤနေရာတွင် လမ်းကြောင်းကို downloads/input_video.mp4 သို့ ပြောင်းပေးပါ
    VIDEO_PATH = "downloads/input_video.mp4"

    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"{VIDEO_PATH} not found - run step 1 first")

    print(f"Transcribing {VIDEO_PATH}...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, info = model.transcribe(VIDEO_PATH)

    os.makedirs("processed", exist_ok=True)
    transcript_path = "processed/transcript.txt"

    with open(transcript_path, "w", encoding="utf-8") as f:
        for segment in segments:
            f.write(f"{segment.text}\n")

    print(f"Saved transcript to {transcript_path}")

if __name__ == "__main__":
    main()
  

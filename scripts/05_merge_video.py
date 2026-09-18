import os
import sys
from moviepy.editor import VideoFileClip, AudioFileClip

def main():
    video_path = "downloads/input_video.mp4"
    audio_path = "processed/dubbed_audio.mp3"
    output_dir = "output"
    output_path = os.path.join(output_dir, "final_dubbed_video.mp4")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("Merging video and dubbed audio...")
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)

    # ဗီဒီယိုနှင့် အသံကို ပေါင်းစည်းခြင်း
    final_clip = video_clip.set_audio(audio_clip)

    # Output ဖိုင်အဖြစ် ထုတ်ယူခြင်း
    final_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    video_clip.close()
    audio_clip.close()
    print(f"Successfully created final video at {output_path}")

if __name__ == "__main__":
    main()
    

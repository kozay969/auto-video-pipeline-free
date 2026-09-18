import argparse
import os
import shutil
import urllib.request

def fetch_video(source_input, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    destination = os.path.join(output_dir, "input_video.mp4")

    # If the input is a URL (e.g. GitHub Release asset or raw link)
    if source_input.startswith("http://") or source_input.startswith("https://"):
        print(f"Downloading video from URL: {source_input}")
        urllib.request.urlretrieve(source_input, destination)
    # If the video is committed directly in the repo/workspace
    elif os.path.exists(source_input):
        print(f"Copying video from local path: {source_input}")
        shutil.copy(source_input, destination)
    else:
        raise FileNotFoundError(f"Video source not found: {source_input}")

    print(f"Video successfully saved to {destination}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch video for processing pipeline.")
    parser.add_argument("--input", required=True, help="URL or relative file path to the input video")
    args = parser.parse_args()

    fetch_video(args.input)

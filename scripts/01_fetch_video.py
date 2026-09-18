import os
import sys
import requests
import subprocess

def download_youtube(url, output_path):
    print(f"Downloading from YouTube using yt-dlp: {url}")
    command = [
        "yt-dlp",
        "-f", "b",  # best single file format
        "-o", output_path,
        url
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print("YouTube video downloaded successfully.")
    else:
        print(f"yt-dlp error: {result.stderr}")
        sys.exit(1)

def download_direct_file(url, output_path):
    print(f"Downloading direct file from URL: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded successfully: {output_path}")
    else:
        print(f"Failed to download video. Status code: {response.status_code}")
        sys.exit(1)

def main():
    video_url = os.environ.get("VIDEO_URL")
    video_path = os.environ.get("VIDEO_PATH")

    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "input_video.mp4")

    if video_url and video_url.strip():
        url = video_url.strip()
        # YouTube Link ဟုတ်မဟုတ် စစ်ဆေးခြင်း
        if "youtube.com" in url or "youtu.be" in url:
            download_youtube(url, output_file)
        else:
            download_direct_file(url, output_file)
            
    elif video_path and os.path.exists(video_path.strip()):
        import shutil
        shutil.copy(video_path.strip(), output_file)
        print(f"Copied local file from {video_path} to {output_file}")
    else:
        print("Error: Neither VIDEO_URL nor valid VIDEO_PATH was provided.")
        sys.exit(1)

    # ဖိုင်ရှိမရှိ စစ်ဆေးခြင်း
    if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
        print("Error: Video file is missing or corrupted.")
        sys.exit(1)

if __name__ == "__main__":
    main()
    

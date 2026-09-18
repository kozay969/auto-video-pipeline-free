import argparse
import os
import sys
import shutil
import requests
import gdown

def download_gdrive(url, output_path):
    print(f"Downloading from Google Drive: {url}")
    # gdown ၏ version အသစ်များအတွက် fuzzy parameter အသုံးမပြုဘဲ ဒေါင်းလုဒ်ဆွဲခြင်း
    gdown.download(url=url, output=output_path, quiet=False)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=False, help="Video URL or Path")
    args = parser.parse_args()

    # Command Line Argument သို့မဟုတ် Environment Variable မှ ရယူခြင်း
    source = args.input or os.environ.get("VIDEO_URL") or os.environ.get("VIDEO_PATH")

    if not source:
        print("Error: Neither VIDEO_URL nor valid VIDEO_PATH was provided.")
        sys.exit(1)

    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "input_video.mp4")

    source = source.strip()

    # Web URL ဖြစ်ပါက
    if source.startswith("http://") or source.startswith("https://"):
        if "drive.google.com" in source:
            download_gdrive(source, output_file)
        else:
            download_direct_file(source, output_file)
    # Repo ထဲရှိ Local File ဖြစ်ပါက
    elif os.path.exists(source):
        shutil.copy(source, output_file)
        print(f"Copied local file from {source} to {output_file}")
    else:
        print(f"Error: Provided path or link does not exist: {source}")
        sys.exit(1)

    # ဖိုင်ဒေါင်းလုဒ် အောင်မြင်မှုနှင့် အရွယ်အစား စစ်ဆေးခြင်း
    if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
        print("Error: Downloaded file is missing or corrupted.")
        sys.exit(1)

    print(f"Video file ready at {output_file} (Size: {os.path.getsize(output_file)} bytes)")

if __name__ == "__main__":
    main()
            

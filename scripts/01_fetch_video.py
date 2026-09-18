import argparse
import os
import sys
import subprocess
import gdown

def download_gdrive(url, output_path):
    print(f"Downloading from Google Drive: {url}")
    # Google Drive Link ထဲကနေ File ID ကို ဆွဲထုတ်၍ ဒေါင်းလုဒ်လုပ်ပေးခြင်း
    gdown.download(url=url, output=output_path, fuzzy=True, quiet=False)

def download_direct_file(url, output_path):
    import requests
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

    source = args.input or os.environ.get("VIDEO_URL") or os.environ.get("VIDEO_PATH")

    if not source:
        print("Error: Neither VIDEO_URL nor valid VIDEO_PATH was provided.")
        sys.exit(1)

    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "input_video.mp4")

    source = source.strip()
    if source.startswith("http://") or source.startswith("https://"):
        # Google Drive Link ဖြစ်ပါက gdown သုံးမည်
        if "drive.google.com" in source:
            download_gdrive(source, output_file)
        else:
            download_direct_file(source, output_file)
    elif os.path.exists(source):
        import shutil
        shutil.copy(source, output_file)
    else:
        print(f"Error: Provided path does not exist: {source}")
        sys.exit(1)

if __name__ == "__main__":
    main()
        

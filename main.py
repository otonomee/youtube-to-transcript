import os
import subprocess
import sys
import re
import whisper
from datetime import datetime

def sanitize_title(title):
    return "".join(x for x in title if x.isalnum() or x in " _-").rstrip()[:50]

def download_audio(video_url):
    output_dir = "extracted_audio"
    os.makedirs(output_dir, exist_ok=True)

    # Download video info to get the title
    command = f'yt-dlp --get-title {video_url}'
    video_title = subprocess.check_output(command, shell=True).decode().strip()

    sanitized_title = sanitize_title(video_title)

    # Check if a file starting with the sanitized title already exists
    if any(f.startswith(sanitized_title) for f in os.listdir(output_dir)):
        print(f"Skipping download, audio for '{video_title}' already exists.")
        return os.path.join(output_dir, f"{sanitized_title}.mp3")

    # Download audio
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    command = (
        f'yt-dlp --no-part -x --audio-format mp3 -o "{output_template}" {video_url}'
    )
    subprocess.run(command, shell=True)

    return os.path.join(output_dir, f"{sanitized_title}.mp3")

def remove_timestamps(text):
    return re.sub(r'\[.*?\]', '', text)

def remove_special_characters(text):
    return re.sub(r'[^A-Za-z0-9\s\.\,\?\!]', '', text)

def remove_duplicate_lines(text):
    lines = text.split('\n')
    seen = set()
    result = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            result.append(line)
    return '\n'.join(result)

def transcribe_audio(audio_path):
    output_folder = "transcripts"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    model = whisper.load_model("medium")
    filename = os.path.basename(audio_path)
    output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")

    result = model.transcribe(audio_path)

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            start_time = datetime.utcfromtimestamp(segment["start"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            text = segment["text"].strip()
            cleaned_text = remove_duplicate_lines(
                remove_special_characters(remove_timestamps(text))
            )
            f.write(f"{start_time}: {cleaned_text}\n")
            if not cleaned_text:
                f.write("\n")

    print(f"Transcribed: {filename}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <youtube_url>")
        sys.exit(1)

    video_url = sys.argv[1]

    print("Downloading audio...")
    audio_path = download_audio(video_url)
    
    print("Transcribing audio...")
    transcript_path = transcribe_audio(audio_path)
    
    print(f"Transcript saved to {transcript_path}")


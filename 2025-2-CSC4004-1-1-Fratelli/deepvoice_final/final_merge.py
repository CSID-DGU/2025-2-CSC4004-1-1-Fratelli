# direct_merge.py
import subprocess
import os

ffmpeg_path = "/home/2020112564/.local/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"

cmd = [
    ffmpeg_path,
    '-i', '21s.mp4',
    '-i', 'output.wav', 
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-map', '0:v:0',
    '-map', '1:a:0',
    '-y',
    'video_protected.mp4'
]

print("Merging with ffmpeg...")
print(" ".join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Success! Created video_protected.mp4")
else:
    print(f"Error: {result.stderr}")
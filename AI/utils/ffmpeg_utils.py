import subprocess
from config import FFMPEG_PATH

def merge_video_audio(video_path, audio_path, output_path):
    # cmd = [
    #     FFMPEG_PATH,
    #     "-i", video_path,
    #     "-i", audio_path,
    #     "-c:v", "copy",
    #     "-c:a", "aac",
    #     "-b:a", "192k",
    #     "-map", "0:v:0",
    #     "-map", "1:a:0",
    #     "-y",
    #     output_path
    # ]
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'libx264',       # 비디오 H.264 인코딩
        '-preset', 'fast',        # 인코딩 속도/품질
        '-crf', '23',             # 품질 (낮을수록 고품질)
        '-c:a', 'aac',            # 오디오 AAC
        '-b:a', '192k',           # 오디오 비트레이트
        '-map', '0:v:0',          # 영상 스트림
        '-map', '1:a:0',          # 오디오 스트림
        '-shortest',              # 영상 길이에 맞춤
        '-movflags', '+faststart',# 웹 친화적
        '-y',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(result.stderr)

    return output_path

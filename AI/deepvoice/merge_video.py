import subprocess
import sys
import os

def merge_video(video_path: str, audio_path: str, output_path: str):
    """
    동영상과 오디오 병합
    
    Args:
        video_path: 입력 동영상 경로
        audio_path: 입력 오디오 경로 (wav)
        output_path: 출력 동영상 경로 (mp4)
    """
    try:
        # ffmpeg 명령어 구성
        cmd = [
            'ffmpeg',
            '-i', video_path,      # 입력 비디오
            '-i', audio_path,      # 입력 오디오
            '-c:v', 'copy',        # 비디오 코덱 복사 (재인코딩 안함)
            '-c:a', 'aac',         # 오디오 AAC 인코딩
            '-b:a', '192k',        # 오디오 비트레이트
            '-map', '0:v:0',       # 첫 번째 입력의 비디오 스트림
            '-map', '1:a:0',       # 두 번째 입력의 오디오 스트림
            '-y',                  # 덮어쓰기 허용
            output_path
        ]
        
        print(f"Merging video: {video_path} + {audio_path} → {output_path}")
        
        # ffmpeg 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print("✅ Success! Created video_protected.mp4")
            print(f"✓ Video merged: {output_path}")
        else:
            print(f"FFmpeg Error: {result.stderr}")
        # if result.returncode != 0:
        #     raise RuntimeError(f"FFmpeg error: {result.stderr}")
        
    except Exception as e:
        print(f"Error merging video: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python merge_video.py input_video.mp4 input_audio.wav output_video.mp4")
        sys.exit(1)
    
    video = sys.argv[1]
    audio = sys.argv[2]
    output = sys.argv[3]
    
    merge_video(video, audio, output)
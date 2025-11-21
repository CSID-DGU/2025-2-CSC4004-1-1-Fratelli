# merge_only.py
from moviepy import VideoFileClip, AudioFileClip
import sys
import os

def merge_audio_video(video_file, audio_file, output_file):
    try:
        print("="*70)
        print("MERGING PROTECTED AUDIO WITH VIDEO")
        print("="*70)
        
        print(f"\nVideo: {video_file}")
        print(f"Audio: {audio_file}")
        print(f"Output: {output_file}")
        
        # 파일 확인
        if not os.path.exists(video_file):
            print(f"Error: {video_file} not found!")
            return
        if not os.path.exists(audio_file):
            print(f"Error: {audio_file} not found!")
            return
        
        # 비디오와 오디오 로드
        print("\nLoading files...")
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)
        
        # 길이 확인
        print(f"Video duration: {video.duration:.2f}s")
        print(f"Audio duration: {audio.duration:.2f}s")
        
        # 오디오 길이 조정 (필요시)
        if audio.duration > video.duration:
            print("Trimming audio to match video length...")
            audio = audio.subclip(0, video.duration)
        
        # 병합
        print("\nMerging...")
        final = video.set_audio(audio)
        
        # 저장
        print(f"Saving to {output_file}...")
        final.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac'
        )
        
        # 정리
        video.close()
        audio.close()
        final.close()
        
        print("\n✅ Done! Output saved:", output_file)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 기본값
    video_file = "21s.mp4"
    audio_file = "output.wav"
    output_file = "video1_protected.mp4"
    
    # 명령줄 인자 처리
    if len(sys.argv) >= 2:
        video_file = sys.argv[1]
    if len(sys.argv) >= 3:
        audio_file = sys.argv[2]
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]
    
    merge_audio_video(video_file, audio_file, output_file)
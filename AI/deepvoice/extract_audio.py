from moviepy import VideoFileClip
import sys

def extract_audio(video_path: str, audio_output_path: str):
    """
    동영상에서 오디오 추출
    
    Args:
        video_path: 입력 동영상 경로
        audio_output_path: 출력 오디오 경로 (wav)
    """
    try:
        # 비디오 파일 열기
        clip = VideoFileClip(video_path)
        
        # 오디오 부분만 추출
        audio = clip.audio
        
        if audio is None:
            raise ValueError("Video has no audio track")
        
        # 16kHz, 16bit PCM wav로 저장
        # audio.write_audiofile(audio_output_path, fps=16000, nbytes=2, verbose=False, logger=None)
        audio.write_audiofile(audio_output_path, fps=16000, nbytes=2)
                
        clip.close()
        print(f"✓ Audio extracted: {audio_output_path}")
        
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_audio.py input_video.mp4 output.wav")
        sys.exit(1)
    
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    
    extract_audio(in_file, out_file)

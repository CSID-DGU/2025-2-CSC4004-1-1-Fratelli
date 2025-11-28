import torch
from TTS.api import TTS

# 1. 모델 다운로드 및 로드 (최초 실행 시 모델을 자동 다운로드합니다)
# GPU가 있다면 gpu=True, 없으면 gpu=False
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading XTTS v2 on {device}...")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# 2. 테스트 설정
protected_audio_path = "original_audio.wav"  # 방금 만드신 보호된 파일 경로
output_path = "original_cloned_output.wav"             # 복제 시도 결과물

# 3. 목소리 복제 시도 (영어/한국어 모두 가능)
# XTTS는 speaker_wav에 들어온 오디오에서 목소리 특징을 추출합니다.
print("Attempting to clone voice...")

tts.tts_to_file(
    text="안녕하세요. 저는 최태성이고 한국사 강사 입니다",
    speaker_wav=protected_audio_path, # 여기에 보호된 오디오를 넣습니다.
    language="ko",                    # 한국어 설정
    file_path=output_path
)

print(f"Done! Check {output_path}")
"""
protect.py를 함수 형태로 래핑 (CMUA 기반 perturbation)
"""
import os
import cv2
import json
import random
import torch
from PIL import Image
from torchvision import transforms
import torchvision.utils as vutils


def load_config(config_path='./deepfake/setting.json'):
    """설정 파일 로드"""
    with open(config_path, 'r') as f:
        cfg = json.load(f)
    return cfg


def get_transform(size):
    """이미지 전처리 변환"""
    return transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])


def apply_perturbation(img_path, out_path, up, size, eps_scale):
    """이미지에 perturbation 적용"""
    # universal perturbation의 실제 크기 확인
    if up.dim() == 3:  # (C, H, W)
        up_size = up.shape[-1]
    else:
        raise ValueError(f"Unexpected perturbation shape: {up.shape}")
    
    # perturbation 크기에 맞춰 이미지 변환
    tf = get_transform((up_size, up_size))
    img = Image.open(img_path).convert("RGB")
    orig_size = img.size  # (width, height)
    
    img_t = tf(img).unsqueeze(0)

    # ε 적용: protected = img + eps_scale * up
    # up을 batch 차원에 맞춤
    if up.dim() == 3:
        up = up.unsqueeze(0)
    
    protected = img_t + eps_scale * up
    protected = torch.clamp(protected, -1, 1)

    # 원본 크기로 복원하여 저장
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # [-1, 1] -> [0, 1] 범위로 정규화
    protected = (protected + 1) / 2.0
    protected = torch.clamp(protected, 0, 1)
    
    # 저장 후 원본 크기로 리사이즈
    temp_path = out_path + ".temp.png"
    vutils.save_image(protected, temp_path)
    
    # 원본 크기로 복원
    protected_img = Image.open(temp_path)
    protected_img = protected_img.resize(orig_size, Image.LANCZOS)
    protected_img.save(out_path)
    
    # 임시 파일 삭제
    if os.path.exists(temp_path):
        os.remove(temp_path)


def protect_image(input_path, output_path, perturbation_path='./deepfake/models/perturbation.pt', 
                  eps=1.0, image_size=None):
    """
    이미지 보호 (CMUA 방식)
    
    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 이미지 경로
        perturbation_path: universal perturbation 파일 경로
        eps: perturbation 강도 (1.0 = 원본 강도)
        image_size: 사용되지 않음 (하위 호환성을 위해 유지)
    """
    print(f"[protect_image] Loading perturbation from {perturbation_path}")
    
    # perturbation 로드
    up = torch.load(perturbation_path, map_location='cpu')
    if up.dim() == 4:
        up = up[0]
    
    print(f"[protect_image] Applying perturbation (eps={eps})")
    # image_size는 apply_perturbation 내부에서 자동으로 결정됨
    apply_perturbation(input_path, output_path, up, None, eps)
    print(f"[protect_image] Protected image saved: {output_path}")


def protect_video(input_path, output_path, perturbation_path='./deepfake/models/perturbation.pt',
                  eps=1.0, image_size=None):
    """
    비디오 보호 (CMUA 방식)
    
    Args:
        input_path: 입력 비디오 경로
        output_path: 출력 비디오 경로
        perturbation_path: universal perturbation 파일 경로
        eps: perturbation 강도
        image_size: 사용되지 않음 (하위 호환성을 위해 유지)
    """
    print(f"[protect_video] Loading perturbation from {perturbation_path}")
    
    # perturbation 로드
    up = torch.load(perturbation_path, map_location='cpu')
    if up.dim() == 4:
        up = up[0]
    
    # 비디오 정보 가져오기
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 임시 프레임 디렉토리
    import tempfile
    frame_dir = tempfile.mkdtemp(prefix='frames_')
    out_dir = tempfile.mkdtemp(prefix='protected_frames_')
    
    print(f"[protect_video] Extracting {frame_count} frames...")
    
    # 프레임 추출
    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(frame_dir, f"{idx:06d}.png")
        cv2.imwrite(frame_path, frame)
        frames.append(frame_path)
        idx += 1
    cap.release()
    
    print(f"[protect_video] Applying perturbation to {len(frames)} frames...")
    
    # 보호 적용 (image_size는 자동으로 결정됨)
    for i, f_path in enumerate(frames):
        out_path = os.path.join(out_dir, f"{i:06d}.png")
        apply_perturbation(f_path, out_path, up, None, eps)
    
    print(f"[protect_video] Merging protected frames into video...")
    
    # 보호된 프레임 → 영상 합치기
    h, w = cv2.imread(os.path.join(out_dir, "000000.png")).shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    for i in range(len(frames)):
        frame = cv2.imread(os.path.join(out_dir, f"{i:06d}.png"))
        writer.write(frame)
    
    writer.release()
    
    # 임시 디렉토리 정리
    import shutil
    shutil.rmtree(frame_dir, ignore_errors=True)
    shutil.rmtree(out_dir, ignore_errors=True)
    
    print(f"[protect_video] Protected video saved: {output_path}")

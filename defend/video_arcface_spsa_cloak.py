#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
video_arcface_spsa_cloak.py

최종 방어용 영상 클로킹 스크립트 (roop / ArcFace + inswapper 소스 방어용)

References (defense design inspired by):
[1] NullSwap: Proactive Identity Cloaking Against Deepfake Face Swapping
[2] FaceSwapGuard: Safeguarding Facial Privacy from DeepFake Threats through Identity Obfuscation
[3] FaceShield: Proactive Defense Mechanism against Image-based Deepfake Attacks
[4] Disruptive Attacks on Face Swapping via Low-Frequency Perceptual Perturbations
[5] Defending against GAN-based Deepfake Attacks via Transformation-aware Adversarial Faces

아이디어 요약:
- ArcFace ONNX 인코더를 black-box로 사용
- 각 프레임에 대해 SPSA 기반 gradient 추정으로 identity distance 최대화
- L_inf ball (epsilon) 안에서 PGD-style 업데이트
- 랜덤 리사이즈/크롭(EOT)으로 roop / inswapper 전처리 변화에 강인하도록 설계

Usage 예시:

conda activate df12


python video_arcface_spsa_cloak.py \
  --input input/test2.mp4 \
  --output output/protected.mp4 \
  --arcface-onnx ~/.insightface/models/buffalo_l/w600k_r50.onnx \
  --epsilon 0.30 \
  --step-size 0.03 \
  --steps 80 \
  --spsa-k 4 \
  --spsa-c 0.03 \
  --device cuda

주의:
- SPSA 특성상 반복/방향 수가 많을수록 방어는 강해지지만, 속도는 느려집니다.
- 노이즈는 눈에 어느 정도 보이는 수준(eps~0.06~0.1)까지 허용하는 설정을 기본값으로 둡니다.
"""
import os
import sys
user_site = os.path.expanduser("~/.local/lib/python3.12/site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

import argparse
import os
from typing import Tuple

import numpy as np
import cv2

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import onnxruntime as ort
except ImportError:
    ort = None


# -------------------------------------------------
# 1. ArcFace ONNX 래퍼
# -------------------------------------------------


class ArcFaceONNXEncoder:
    """
    ArcFace ONNX 모델 (예: insightface w600k_r50.onnx)을 감싼 간단 래퍼.

    입력:  RGB tensor [B,3,H,W], [0,1]
    출력:  L2-normalized embedding [B,D]
    """

    def __init__(self, onnx_path: str):
        assert ort is not None, "onnxruntime(혹은 onnxruntime-gpu)를 먼저 설치하세요."
        if not os.path.exists(onnx_path):
            raise FileNotFoundError(f"ArcFace ONNX model not found: {onnx_path}")

        self.session = ort.InferenceSession(
            onnx_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def _preprocess_single(self, img_t: torch.Tensor) -> np.ndarray:
        """
        img_t: [3,H,W], RGB, [0,1] (torch)
        ArcFace 입력 형식으로 변환:
        - 112x112 resize
        - RGB→BGR
        - mean/std normalize
        """
        # resize to 112x112
        img = F.interpolate(img_t.unsqueeze(0), size=(112, 112),
                            mode="bilinear", align_corners=False)[0]
        img = img.detach().cpu().permute(1, 2, 0).numpy()  # [H,W,3], RGB
        img = img[:, :, ::-1] * 255.0  # BGR, [0,255]

        mean = np.array([127.5, 127.5, 127.5], dtype=np.float32)
        std = np.array([128.0, 128.0, 128.0], dtype=np.float32)
        img = (img - mean) / std

        # [H,W,3] -> [1,3,H,W]
        img = np.transpose(img, (2, 0, 1))[None].astype(np.float32)
        return img

    def __call__(self, img_batch: torch.Tensor) -> torch.Tensor:
        """
        img_batch: [B,3,H,W], RGB, [0,1]
        return:    [B,D] (L2 normalized)
        """
        embs = []
        for i in range(img_batch.shape[0]):
            inp = self._preprocess_single(img_batch[i])
            out = self.session.run([self.output_name], {self.input_name: inp})[0]  # [1,D]
            embs.append(torch.from_numpy(out[0]))
        embs = torch.stack(embs, dim=0)  # [B,D]
        embs = F.normalize(embs, p=2, dim=1)
        return embs


# -------------------------------------------------
# 2. 랜덤 변환 (EOT)
# -------------------------------------------------


class RandomTransform(nn.Module):
    """
    딥페이크 파이프라인의 전처리(리사이즈/크롭)를 대충 흉내내는 랜덤 변환.
    - 공격 노이즈가 약간의 리사이즈/크롭에도 버티도록 함.
    """

    def __init__(self, min_scale: float = 0.85, max_scale: float = 1.15):
        super().__init__()
        self.min_scale = min_scale
        self.max_scale = max_scale

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, C, H, W = x.shape
        # 랜덤 스케일
        scale = torch.empty(1).uniform_(self.min_scale, self.max_scale).item()
        new_h, new_w = int(H * scale), int(W * scale)

        x_resized = F.interpolate(x, size=(new_h, new_w),
                                  mode="bilinear", align_corners=False)

        # 다시 (H,W)로 크롭 또는 패딩
        if new_h < H or new_w < W:
            pad_h = H - new_h
            pad_w = W - new_w
            pad_top = pad_h // 2
            pad_bottom = pad_h - pad_top
            pad_left = pad_w // 2
            pad_right = pad_w - pad_left
            x_padded = F.pad(
                x_resized,
                (pad_left, pad_right, pad_top, pad_bottom),
                mode="reflect"
            )
            return x_padded
        else:
            top = torch.randint(0, new_h - H + 1, (1,)).item()
            left = torch.randint(0, new_w - W + 1, (1,)).item()
            return x_resized[:, :, top:top + H, left:left + W]


# -------------------------------------------------
# 3. Identity distance
# -------------------------------------------------


def identity_distance(e1: torch.Tensor, e2: torch.Tensor) -> torch.Tensor:
    """
    e1, e2: [B,D], L2 normalized
    D = (1 - cos) + MSE, 평균
    """
    cos_sim = F.cosine_similarity(e1, e2, dim=1)        # [B]
    mse = (e1 - e2).pow(2).mean(dim=1)                  # [B]
    d = (1.0 - cos_sim) + mse
    return d.mean()


# -------------------------------------------------
# 4. SPSA 기반 per-frame ArcFace cloaker
# -------------------------------------------------


class SPSAArcFaceFrameCloaker:
    """
    ArcFace ONNX + SPSA 기반 per-frame 강 공격.

    - encoder: ArcFaceONNXEncoder
    - epsilon: L_inf bound (예: 0.06 ~ 0.1)
    - step_size: PGD step size (예: 0.01)
    - steps: PGD 반복 횟수
    - spsa_c: SPSA perturbation 크기
    - spsa_k: 각 step당 SPSA 방향 개수 (2 * K 쿼리 발생)
    """

    def __init__(
        self,
        encoder: ArcFaceONNXEncoder,
        epsilon: float = 0.06,
        step_size: float = 0.01,
        steps: int = 40,
        spsa_c: float = 0.01,
        spsa_k: int = 4,
        device: str = "cuda",
    ):
        self.encoder = encoder
        self.eps = float(epsilon)
        self.alpha = float(step_size)
        self.num_steps = int(steps)
        self.spsa_c = float(spsa_c)
        self.spsa_k = int(spsa_k)
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        self.rand_trans = RandomTransform().to(self.device)

    @torch.no_grad()
    def _encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [1,3,H,W], [0,1]
        ArcFace 임베딩 반환 (L2 normalized)
        """
        return self.encoder(x)

    def _loss(self, x_adv: torch.Tensor, emb_src: torch.Tensor) -> torch.Tensor:
        """
        x_adv: [1,3,H,W], [0,1]
        emb_src: [1,D]
        """
        # EOT: 랜덤 변환
        x_trans = self.rand_trans(x_adv)
        emb_adv = self._encode(x_trans)
        loss = identity_distance(emb_adv, emb_src)
        return loss

    def cloak_frame(self, frame_rgb: np.ndarray) -> np.ndarray:
        """
        frame_rgb: [H,W,3], uint8, RGB
        return:    [H,W,3], uint8, RGB (cloaked)
        """
        # [0,1] tensor 변환
        img = torch.from_numpy(frame_rgb.astype(np.float32) / 255.0).permute(2, 0, 1)  # [3,H,W]
        img = img.unsqueeze(0).to(self.device)  # [1,3,H,W]
        x = img

        # baseline embedding (원본 기준)
        with torch.no_grad():
            emb_src = self._encode(x)  # [1,D]

        # 초기 xp (작은 랜덤으로 시작)
        xp = x + (torch.rand_like(x) * 2 - 1) * (self.eps * 0.1)
        xp = xp.clamp(0.0, 1.0)

        for step in range(self.num_steps):
            # SPSA를 위한 gradient 추정
            grad_est = torch.zeros_like(xp)

            for k in range(self.spsa_k):
                # Rademacher noise (+1/-1)
                v = torch.randint_like(xp, low=0, high=2, dtype=torch.int8).float()
                v = (v * 2.0 - 1.0)   # {-1, +1}

                xp_plus = (xp + self.spsa_c * v).clamp(0.0, 1.0)
                xp_minus = (xp - self.spsa_c * v).clamp(0.0, 1.0)

                loss_plus = self._loss(xp_plus, emb_src)
                loss_minus = self._loss(xp_minus, emb_src)

                # gradient approximation
                g = ((loss_plus - loss_minus) / (2.0 * self.spsa_c)) * v
                grad_est += g

            grad_est /= float(self.spsa_k)

            # PGD-style 업데이트 (gradient ascent: identity distance 최대화)
            xp = xp + self.alpha * torch.sign(grad_est)

            # L_inf 제한 및 [0,1] 클램프
            xp = torch.max(torch.min(xp, x + self.eps), x - self.eps)
            xp = xp.clamp(0.0, 1.0)

        # 최종 결과를 uint8 RGB로 변환
        xp_img = (xp[0].detach().cpu().permute(1, 2, 0).numpy() * 255.0).round().astype(np.uint8)
        return xp_img


# -------------------------------------------------
# 5. 비디오 처리 루틴
# -------------------------------------------------


def process_video(
    input_path: str,
    output_path: str,
    encoder: ArcFaceONNXEncoder,
    epsilon: float = 0.06,
    step_size: float = 0.01,
    steps: int = 40,
    spsa_c: float = 0.01,
    spsa_k: int = 4,
    device: str = "cuda",
    frame_skip: int = 1,
) -> None:
    """
    input_path 영상의 각 프레임에 방어 노이즈를 입혀 output_path로 저장.

    - frame_skip = 1 : 모든 프레임 공격
    - frame_skip = 2 : 1,3,5... 프레임만 공격 (나머지는 원본 복사)
    """

    cloaker = SPSAArcFaceFrameCloaker(
        encoder=encoder,
        epsilon=epsilon,
        step_size=step_size,
        steps=steps,
        spsa_c=spsa_c,
        spsa_k=spsa_k,
        device=device,
    )

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open input video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 비디오 코덱 설정 (mp4v / H.264 등 환경에 맞게 조정 가능)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_idx = 0

    print(f"[INFO] Start processing video: {input_path}")
    print(f"[INFO] Resolution: {w}x{h}, FPS: {fps:.2f}")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        if frame_idx % frame_skip == 0:
            # 방어 적용
            protected_rgb = cloaker.cloak_frame(frame_rgb)
        else:
            # 스킵한 프레임은 원본 사용
            protected_rgb = frame_rgb

        protected_bgr = cv2.cvtColor(protected_rgb, cv2.COLOR_RGB2BGR)
        out.write(protected_bgr)

        frame_idx += 1
        if frame_idx % 10 == 0:
            print(f"\r[INFO] Processed {frame_idx} frames", end="")

    print(f"\n[INFO] Done. Saved to: {output_path}")

    cap.release()
    out.release()


# -------------------------------------------------
# 6. CLI
# -------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="ArcFace + roop 소스 방어용 영상 클로킹 (SPSA 기반 강 공격)",
    )
    p.add_argument("--input", type=str, required=True, help="입력 영상 경로 (mp4 등)")
    p.add_argument("--output", type=str, required=True, help="출력 보호 영상 경로")
    p.add_argument("--arcface-onnx", type=str, required=True, help="ArcFace ONNX 모델 경로 (w600k_r50.onnx 등)")

    p.add_argument("--epsilon", type=float, default=0.06, help="L_inf epsilon (기본: 0.06)")
    p.add_argument("--step-size", type=float, default=0.01, help="PGD step size (기본: 0.01)")
    p.add_argument("--steps", type=int, default=40, help="PGD steps (기본: 40)")

    p.add_argument("--spsa-c", type=float, default=0.01, help="SPSA perturbation 크기 (기본: 0.01)")
    p.add_argument("--spsa-k", type=int, default=4, help="SPSA 방향 개수 (기본: 4)")

    p.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="torch 연산 장치")
    p.add_argument("--frame-skip", type=int, default=1, help="프레임 스킵 간격 (1=모든 프레임 공격)")

    return p.parse_args()


def main():
    args = parse_args()

    encoder = ArcFaceONNXEncoder(args.arcface_onnx)

    process_video(
        input_path=args.input,
        output_path=args.output,
        encoder=encoder,
        epsilon=args.epsilon,
        step_size=args.step_size,
        steps=args.steps,
        spsa_c=args.spsa_c,
        spsa_k=args.spsa_k,
        device=args.device,
        frame_skip=args.frame_skip,
    )


if __name__ == "__main__":
    main()

# LMB.py  (Landmark Breaker - SPSA/Blackbox, GPU 강제 기본 + LandmarksType 호환 + RGB fix)
# Usage (예시):
#   python LMB.py \
#     --input ../input/testvideo_480p.mp4 \
#     --output ../output/testvideo_LB_gpu.mp4 \
#     --mode video \
#     --epsilon 8 --alpha 1 --steps 3 --k 68 --sigma_pix 0.5 \
#     --face_detector blazeface --stride 3 \
#     --device cuda

import os
import cv2
import math
import argparse
import numpy as np
from typing import Tuple, List

# 랜드마크 추출: face_alignment(FAN)
# pip install face-alignment
import face_alignment


# ---------------------------
# 유틸
# ---------------------------
def to_uint8(img01):
    img = np.clip(img01 * 255.0, 0, 255).astype(np.uint8)
    return img

def from_uint8(img):
    return img.astype(np.float32) / 255.0

def choose_k_indices(num_points: int, k: int) -> np.ndarray:
    if (k is None) or (k <= 0) or (k >= num_points):
        return np.arange(num_points)
    step = num_points / float(k)
    idx = np.floor(np.arange(k) * step).astype(int)
    idx = np.clip(idx, 0, num_points - 1)
    return np.unique(idx)

def gaussian_2d(h, w, cx, cy, sigma):
    """ (h, w) 격자에 중심 (cx, cy), 표준편차 sigma 픽셀 가우시안 """
    yy, xx = np.mgrid[0:h, 0:w]
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * sigma * sigma))
    return g

def make_heatmap_from_landmarks(landmarks_xy: np.ndarray, H: int, W: int,
                                sigma_pix: float = 1.5, k: int = 68) -> np.ndarray:
    """
    landmarks_xy: (68, 2) or (num, 2) 이미지 좌표 (x, y)
    반환: [K, H, W] float32
    """
    if landmarks_xy is None or len(landmarks_xy) == 0:
        return np.zeros((1, H, W), dtype=np.float32)

    pts = landmarks_xy.reshape(-1, 2)
    use_idx = choose_k_indices(len(pts), k)
    pts = pts[use_idx]

    hm = np.zeros((len(pts), H, W), dtype=np.float32)
    for i, (x, y) in enumerate(pts):
        hm[i] = gaussian_2d(H, W, x, y, sigma_pix)
    return hm

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    a,b: [K,H,W]
    반환: 평균 코사인 유사도(높을수록 닮음)
    """
    a_f = a.reshape(a.shape[0], -1)
    b_f = b.reshape(b.shape[0], -1)
    a_n = a_f / (np.linalg.norm(a_f, axis=1, keepdims=True) + 1e-8)
    b_n = b_f / (np.linalg.norm(b_f, axis=1, keepdims=True) + 1e-8)
    cos = (a_n * b_n).sum(axis=1)
    return float(np.mean(cos))

def largest_face(landmarks_list: List[np.ndarray]) -> np.ndarray:
    """
    face_alignment.get_landmarks는 다얼굴의 68x2 리스트를 반환 가능.
    가장 큰 얼굴(바운딩 박스 면적 기준) 1개 선택.
    """
    if (landmarks_list is None) or (len(landmarks_list) == 0):
        return None
    if len(landmarks_list) == 1:
        return landmarks_list[0]

    def area(pts):
        x1, y1 = pts.min(axis=0)
        x2, y2 = pts.max(axis=0)
        return (x2 - x1) * (y2 - y1)

    sizes = [area(p) for p in landmarks_list]
    return landmarks_list[int(np.argmax(sizes))]


# ---------------------------
# SPSA 기반 노이즈 업데이트 (블랙박스)
# ---------------------------
def spsa_step(image01: np.ndarray,
              baseline_hm: np.ndarray,
              fa_detector,
              alpha: float,
              delta: float,
              sigma_pix: float,
              k: int,
              spsa_samples: int = 8) -> np.ndarray:
    """
    image01: [H,W,3] in [0,1]
    baseline_hm: [K,H,W]
    반환: 업데이트 스텝 (image 크기)  -> sign로 적용
    """
    H, W = image01.shape[:2]
    g_hat = np.zeros_like(image01, dtype=np.float32)

    # SPSA: u ~ Rademacher {-1,+1}, L+ L- 평가 → (L+ - L-)/(2 delta) * u
    for _ in range(spsa_samples):
        u = np.random.choice([-1.0, 1.0], size=image01.shape).astype(np.float32)

        # +delta
        img_p = np.clip(image01 + delta * u, 0.0, 1.0)
        # RGB 그대로 전달 (FIX)
        lm_p = fa_detector.get_landmarks(to_uint8(img_p))
        lm_p = largest_face(lm_p)
        hm_p = make_heatmap_from_landmarks(lm_p, H, W, sigma_pix=sigma_pix, k=k)
        Lp = cosine_similarity(hm_p, baseline_hm)

        # -delta
        img_m = np.clip(image01 - delta * u, 0.0, 1.0)
        # RGB 그대로 전달 (FIX)
        lm_m = fa_detector.get_landmarks(to_uint8(img_m))
        lm_m = largest_face(lm_m)
        hm_m = make_heatmap_from_landmarks(lm_m, H, W, sigma_pix=sigma_pix, k=k)
        Lm = cosine_similarity(hm_m, baseline_hm)

        # 목표: 유사도 ↓ → 손실 = cos → 감소시키는 방향
        g_hat += ((Lp - Lm) / (2.0 * delta)) * u

    g_hat /= float(max(1, spsa_samples))
    step = -alpha * np.sign(g_hat)  # cos 낮추기 위한 하강 방향
    return step


# ---------------------------
# 프레임 공격 (SPSA + L_inf 제약)
# ---------------------------
def attack_frame_blackbox(frame_bgr: np.ndarray,
                          fa_detector,
                          steps: int,
                          epsilon: float,
                          alpha: float,
                          k: int,
                          sigma_pix: float,
                          spsa_samples: int = 8,
                          debug_prefix: str = None) -> np.ndarray:
    """
    epsilon, alpha: [픽셀] 단위(예: 8, 1) → 내부에서 /255
    """
    H, W = frame_bgr.shape[:2]
    img01 = from_uint8(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))  # [0,1], RGB

    # 기준 랜드마크/히트맵 — RGB 그대로 전달 (FIX)
    lm0 = fa_detector.get_landmarks(to_uint8(img01))
    lm0 = largest_face(lm0)
    hm0 = make_heatmap_from_landmarks(lm0, H, W, sigma_pix=sigma_pix, k=k)

    if hm0.sum() == 0.0:
        # 얼굴이 없으면 그대로 반환
        return frame_bgr

    eps01 = epsilon / 255.0
    alpha01 = alpha / 255.0
    # SPSA 내부 탐색 스텝(너무 작으면 노이즈 추정이 불안정)
    delta01 = max(1.0, alpha) / 255.0

    x_adv = img01.copy()
    x_orig = img01.copy()

    for t in range(steps):
        step_dir = spsa_step(x_adv, hm0, fa_detector, alpha=alpha01,
                             delta=delta01, sigma_pix=sigma_pix, k=k,
                             spsa_samples=spsa_samples)
        x_adv = np.clip(x_adv + step_dir, 0.0, 1.0)

        # 원본 대비 L_inf 프로젝션
        diff = np.clip(x_adv - x_orig, -eps01, eps01)
        x_adv = np.clip(x_orig + diff, 0.0, 1.0)

        if debug_prefix:
            cv2.imwrite(f"{debug_prefix}_t{t:02d}.png",
                        cv2.cvtColor(to_uint8(x_adv), cv2.COLOR_RGB2BGR))

    out = cv2.cvtColor(to_uint8(x_adv), cv2.COLOR_RGB2BGR)
    return out


# ---------------------------
# 이미지/비디오 처리
# ---------------------------
def process_image(in_path, out_path, args, fa_detector):
    frame = cv2.imread(in_path, cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"이미지를 열 수 없습니다: {in_path}")

    adv = attack_frame_blackbox(
        frame, fa_detector,
        steps=args.steps, epsilon=args.epsilon, alpha=args.alpha,
        k=args.k, sigma_pix=args.sigma_pix,
        spsa_samples=args.spsa, debug_prefix=args.debug_dir if args.debug_dir else None
    )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cv2.imwrite(out_path, adv)
    print(f"[OK] Saved image: {out_path}")

def process_video(in_path, out_path, args, fa_detector):
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {in_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    writer = cv2.VideoWriter(out_path, fourcc, fps, (W, H))

    noise_cache = None
    f = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        debug_prefix = None
        if args.debug_dir and (args.dump_every > 0) and (f % args.dump_every == 0):
            os.makedirs(args.debug_dir, exist_ok=True)
            debug_prefix = os.path.join(args.debug_dir, f"frame{f:06d}")

        # stride: 매 n프레임마다 최적화, 그 사이 프레임은 이전 노이즈 재사용
        if (f % max(1, args.stride)) == 0:
            adv = attack_frame_blackbox(
                frame, fa_detector,
                steps=args.steps, epsilon=args.epsilon, alpha=args.alpha,
                k=args.k, sigma_pix=args.sigma_pix,
                spsa_samples=args.spsa, debug_prefix=debug_prefix
            )
            noise_cache = (adv.astype(np.int16) - frame.astype(np.int16))
        else:
            if noise_cache is None:
                adv = frame.copy()
            else:
                tmp = frame.astype(np.int16) + noise_cache
                tmp = np.clip(tmp, 0, 255).astype(np.uint8)
                adv = tmp

        writer.write(adv)
        f += 1

    cap.release()
    writer.release()
    print(f"[OK] Saved video: {out_path}")


# ---------------------------
# face_alignment 버전별 LandmarksType(2D) 호환
# ---------------------------
def resolve_landmarks_type_2d():
    """
    face_alignment 버전에 따라 LandmarksType의 2D 명칭이 다를 수 있으므로 안전하게 해석.
    우선순위: enum 멤버명 → 모듈 상수 → Enum값 추정(1)
    """
    try:
        LT = face_alignment.LandmarksType
    except Exception:
        for name in ["_2D", "TWO_D"]:
            if hasattr(face_alignment, name):
                return getattr(face_alignment, name)
        return 1

    for name in ["_2D", "TWO_D", "TwoD", "twoD", "two_d"]:
        if hasattr(LT, name):
            return getattr(LT, name)

    for name in ["_2D", "TWO_D"]:
        if hasattr(face_alignment, name):
            return getattr(face_alignment, name)

    try:
        return LT(1)
    except Exception:
        return 1


# ---------------------------
# 메인
# ---------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="입력 파일(이미지/영상)")
    ap.add_argument("--output", required=True, help="출력 파일 경로")
    ap.add_argument("--mode", choices=["image", "video"], default="video")
    ap.add_argument("--epsilon", type=float, default=8.0, help="L_inf 픽셀 예산 (예: 8)")
    ap.add_argument("--alpha", type=float, default=1.0, help="스텝 크기(픽셀)")
    ap.add_argument("--steps", type=int, default=3, help="최적화 반복 수")
    ap.add_argument("--k", type=int, default=68, help="사용할 랜드마크 점 개수")
    ap.add_argument("--sigma_pix", type=float, default=0.5, help="가우시안 시그마(픽셀)")
    ap.add_argument("--spsa", type=int, default=8, help="SPSA 샘플 수(한 스텝당 2*spsa 모델 호출)")
    ap.add_argument("--face_detector", choices=["sfd", "blazeface"], default="blazeface")
    ap.add_argument("--stride", type=int, default=3, help="비디오에서 매 n프레임마다 최적화")
    ap.add_argument("--debug_dir", type=str, default="", help="중간 저장 디렉토리(공백이면 저장 안함)")
    ap.add_argument("--dump_every", type=int, default=10, help="디버그 프레임 저장 주기")
    ap.add_argument("--device", type=str, default="cuda",
                    help="face_alignment 실행 디바이스: 'cuda' 또는 'cpu' (기본 cuda)")

    args = ap.parse_args()

    # --- GPU 강제 로직 ---
    device = args.device.lower()
    if device == "cuda":
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA 사용을 강제하셨지만 torch.cuda.is_available() == False 입니다.\n"
                "CUDA 드라이버/Toolkit, GPU 빌드의 PyTorch 설치 상태를 확인하세요."
            )
    elif device != "cpu":
        raise ValueError("--device 옵션은 'cuda' 또는 'cpu'만 허용합니다.")

    # face_alignment 초기화 (지정한 device 사용) — LandmarksType 2D 호환 처리
    lmk2d = resolve_landmarks_type_2d()
    fa = face_alignment.FaceAlignment(
        lmk2d,
        device=device,
        face_detector=args.face_detector
    )

    if args.mode == "image":
        process_image(args.input, args.output, args, fa)
    else:
        process_video(args.input, args.output, args, fa)

if __name__ == "__main__":
    main()

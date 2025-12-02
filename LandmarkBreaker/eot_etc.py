#!/usr/bin/env python3
# LMB_DCT_EOT.py
# Black-box Landmark Breaker with Low-Frequency DCT parameterization + EOT + Ensemble loss
# Usage (예):
#   python LMB_DCT_EOT.py --input ../input/testvideo_480p.mp4 --output ../output/dct_eot_lb.avi \
#     --device cuda --epsilon 16 --alpha 3 --steps 8 --spsa 32 --lf 3 --stride 1 --face_detector sfd

import os, io, argparse
import cv2
import numpy as np
from PIL import Image

# 랜드마크: face_alignment (필수)
import face_alignment
HAS_MEDIAPIPE = False
try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except Exception:
    HAS_MEDIAPIPE = False


# -----------------------------
# 유틸
# -----------------------------
def to_uint8(img01):
    return np.clip(img01 * 255.0, 0, 255).astype(np.uint8)

def from_uint8(img):
    return img.astype(np.float32) / 255.0

def gaussian_2d(h, w, cx, cy, sigma):
    yy, xx = np.mgrid[0:h, 0:w]
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma * sigma))

def make_heatmap(points_xy, H, W, sigma):
    if points_xy is None or len(points_xy) == 0:
        return np.zeros((1, H, W), dtype=np.float32)
    pts = np.array(points_xy).reshape(-1, 2)
    hms = [gaussian_2d(H, W, x, y, sigma) for (x, y) in pts]
    return np.stack(hms, axis=0).astype(np.float32)

def cosine_sim(a, b):
    # a,b: [K,H,W]
    a_f = a.reshape(a.shape[0], -1)
    b_f = b.reshape(b.shape[0], -1)
    a_n = a_f / (np.linalg.norm(a_f, axis=1, keepdims=True) + 1e-8)
    b_n = b_f / (np.linalg.norm(b_f, axis=1, keepdims=True) + 1e-8)
    return float((a_n * b_n).sum(axis=1).mean())

def resolve_landmarks_type_2d():
    try:
        LT = face_alignment.LandmarksType
        for name in ["_2D","TWO_D","TwoD","twoD","two_d"]:
            if hasattr(LT, name):
                return getattr(LT, name)
        return LT(1)
    except Exception:
        for name in ["_2D","TWO_D"]:
            if hasattr(face_alignment, name):
                return getattr(face_alignment, name)
        return 1


# -----------------------------
# 검출기 래퍼 (FA + optional MediaPipe)
# -----------------------------
class FAWrapper:
    def __init__(self, device="cuda", fd="sfd"):
        self.fa = face_alignment.FaceAlignment(resolve_landmarks_type_2d(), device=device, face_detector=fd)
    def get_landmarks(self, rgb_uint8):
        try:
            return self.fa.get_landmarks(rgb_uint8)
        except Exception:
            return None

class MPWrapper:
    def __init__(self):
        self.mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
    def get_landmarks(self, rgb_uint8):
        h,w = rgb_uint8.shape[:2]
        res = self.mesh.process(rgb_uint8)
        if not res.multi_face_landmarks:
            return None
        out=[]
        for lm in res.multi_face_landmarks:
            pts=[(p.x*w, p.y*h) for p in lm.landmark]
            out.append(np.array(pts))
        return out


# -----------------------------
# DCT 블록 변환 (8x8), 저주파 계수만 사용
# -----------------------------
def block_dct_2d(block):
    return cv2.dct(block.astype(np.float32))

def block_idct_2d(block_dct):
    return cv2.idct(block_dct.astype(np.float32))

def reconstruct_deltaY_from_coeffs(coeffs, H, W, lf=3, block=8):
    """
    coeffs: (H//block, W//block, lf, lf)  각 8x8 블록의 좌상단 lf×lf 계수
    반환: deltaY (H,W) float32
    """
    out = np.zeros((H, W), dtype=np.float32)
    bh, bw = coeffs.shape[:2]
    for bi in range(bh):
        for bj in range(bw):
            d = np.zeros((block, block), dtype=np.float32)
            d[:lf, :lf] = coeffs[bi, bj, :lf, :lf]
            idct = block_idct_2d(d)
            i0, j0 = bi * block, bj * block
            out[i0:i0+block, j0:j0+block] = idct[:min(block, H-i0), :min(block, W-j0)]
    return out

def coeffs_like(H, W, lf=3, block=8):
    return np.zeros((H // block, W // block, lf, lf), dtype=np.float32)


# -----------------------------
# EOT 변환 (리사이즈/블러/JPEG)
# -----------------------------
def apply_eot_rgb01(img01, p_jpeg=0.9):
    H, W = img01.shape[:2]
    out = img01.copy()
    # scale
    s = np.random.uniform(0.92, 1.06)
    if abs(s - 1.0) > 1e-6:
        out = cv2.resize(out, (max(1, int(W*s)), max(1, int(H*s))), interpolation=cv2.INTER_LINEAR)
        out = cv2.resize(out, (W, H), interpolation=cv2.INTER_LINEAR)
    # blur
    if np.random.rand() < 0.5:
        k = np.random.choice([1,3,5])
        if k > 1:
            out = cv2.GaussianBlur(out, (k, k), 0)
    # jpeg
    if np.random.rand() < p_jpeg:
        pil = Image.fromarray((out*255).astype(np.uint8))
        buf = io.BytesIO()
        q = int(np.random.uniform(60, 95))
        pil.save(buf, format='JPEG', quality=q)
        arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        out = cv2.imdecode(arr, cv2.IMREAD_COLOR)[:, :, ::-1].astype(np.float32) / 255.0
    return out


# -----------------------------
# 앙상블 손실 (히트맵 코사인)
# -----------------------------
def ensemble_cosine(rgb_uint8, baselines, detectors, sigma_pix):
    total = 0.0; cnt = 0
    H, W = rgb_uint8.shape[:2]
    for det, base_hm in zip(detectors, baselines):
        try:
            lm = det.get_landmarks(rgb_uint8)
            if lm is None or len(lm) == 0:
                continue
            pts = lm[0]
            hm = make_heatmap(pts, H, W, sigma_pix)
            total += cosine_sim(hm, base_hm)
            cnt += 1
        except Exception:
            pass
    if cnt == 0:
        # 검출 못하면 합성 실패에 가깝지만, 보수적으로 큰 유사도로 취급하여 더 낮추도록 유도
        return 1.0
    return total / cnt


# -----------------------------
# 한 프레임 공격: DCT 계수 공간 SPSA
# -----------------------------
def attack_frame_dct_spsa(frame_bgr, detectors, baselines, eps_pix, alpha_pix, steps, spsa, lf, block, sigma_pix, eot=True, debug_prefix=None):
    H, W = frame_bgr.shape[:2]
    orig_rgb01 = from_uint8(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    # 최적화 변수: 저주파 DCT 계수 텐서
    C = coeffs_like(H, W, lf=lf, block=block)
    # SPSA 하이퍼
    delta_c = max(1.0, alpha_pix)  # 픽셀 스텝 기준을 DCT 계수로 환산하기 어렵지만, 상대 크기만 맞춰 사용
    # 반복
    for t in range(steps):
        g = np.zeros_like(C, dtype=np.float32)
        for _ in range(spsa):
            U = np.random.choice([-1.0, 1.0], size=C.shape).astype(np.float32)

            # +delta
            C_p = C + delta_c * U
            dY_p = reconstruct_deltaY_from_coeffs(C_p, H, W, lf=lf, block=block)
            adv_p_rgb01 = apply_deltaY_and_project(orig_rgb01, dY_p, eps_pix)
            if eot:
                eval_p = apply_eot_rgb01(adv_p_rgb01)
            else:
                eval_p = adv_p_rgb01
            Lp = ensemble_cosine(to_uint8(eval_p), baselines, detectors, sigma_pix)

            # -delta
            C_m = C - delta_c * U
            dY_m = reconstruct_deltaY_from_coeffs(C_m, H, W, lf=lf, block=block)
            adv_m_rgb01 = apply_deltaY_and_project(orig_rgb01, dY_m, eps_pix)
            if eot:
                eval_m = apply_eot_rgb01(adv_m_rgb01)
            else:
                eval_m = adv_m_rgb01
            Lm = ensemble_cosine(to_uint8(eval_m), baselines, detectors, sigma_pix)

            g += ((Lp - Lm) / (2.0 * delta_c)) * U

        g /= float(max(1, spsa))
        # 목적: 유사도 ↓ → C ← C - α * sign(grad)
        C = C - alpha_pix * np.sign(g)

        if debug_prefix:
            # 중간 결과 저장
            dY = reconstruct_deltaY_from_coeffs(C, H, W, lf=lf, block=block)
            adv = to_uint8(apply_deltaY_and_project(orig_rgb01, dY, eps_pix))
            cv2.imwrite(f"{debug_prefix}_t{t:02d}.png", cv2.cvtColor(adv, cv2.COLOR_RGB2BGR))

    # 최종
    dY = reconstruct_deltaY_from_coeffs(C, H, W, lf=lf, block=block)
    out_rgb01 = apply_deltaY_and_project(orig_rgb01, dY, eps_pix)
    out_bgr = cv2.cvtColor(to_uint8(out_rgb01), cv2.COLOR_RGB2BGR)
    return out_bgr


def apply_deltaY_and_project(orig_rgb01, deltaY, eps_pix):
    """
    YCrCb 공간에서 밝기(Y)에 deltaY를 적용 → RGB로 복귀 → 최종 RGB에서 L_inf(eps_pix) 투영
    """
    bgr = cv2.cvtColor(to_uint8(orig_rgb01), cv2.COLOR_RGB2BGR).astype(np.float32)
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    Y = ycc[:, :, 0]
    Y2 = np.clip(Y + deltaY, 0, 255)
    ycc[:, :, 0] = Y2
    adv_bgr = cv2.cvtColor(ycc.astype(np.uint8), cv2.COLOR_YCrCb2BGR)
    adv_rgb01 = from_uint8(cv2.cvtColor(adv_bgr, cv2.COLOR_BGR2RGB))
    # L_inf 투영 (RGB)
    diff = np.clip(adv_rgb01 - orig_rgb01, -eps_pix/255.0, eps_pix/255.0)
    proj = np.clip(orig_rgb01 + diff, 0.0, 1.0)
    return proj


# -----------------------------
# 베이스라인 히트맵 만들기(검출기 앙상블)
# -----------------------------
def build_baselines(rgb_uint8, detectors, sigma_pix):
    H, W = rgb_uint8.shape[:2]
    outs = []
    for det in detectors:
        try:
            lm = det.get_landmarks(rgb_uint8)
            if lm is None or len(lm) == 0:
                outs.append(np.zeros((1, H, W), dtype=np.float32))
            else:
                pts = lm[0]
                outs.append(make_heatmap(pts, H, W, sigma_pix))
        except Exception:
            outs.append(np.zeros((1, H, W), dtype=np.float32))
    return outs


# -----------------------------
# 비디오 처리
# -----------------------------
def process_video(in_path, out_path, args):
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError(f"can't open input: {in_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[DCT-EOT] opened {in_path} {W}x{H}@{fps:.2f}fps")

    # 코덱
    fourcc = cv2.VideoWriter_fourcc(*args.fourcc)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    writer = cv2.VideoWriter(out_path, fourcc, fps, (W, H))
    if not writer.isOpened():
        raise RuntimeError(f"VideoWriter failed for '{args.fourcc}'. Try --fourcc XVID and .avi")

    # 검출기
    detectors = [FAWrapper(device=args.device, fd=args.face_detector)]
    if HAS_MEDIAPIPE and args.use_mediapipe:
        detectors.append(MPWrapper())
    print(f"[DCT-EOT] detectors: FA + {'MP' if args.use_mediapipe else 'no MP'}")

    f = 0
    noise_cache = None
    while True:
        ok, frame = cap.read()
        if not ok: break

        if (f % max(1, args.stride)) == 0:
            rgb_u8 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            baselines = build_baselines(rgb_u8, detectors, args.sigma_pix)

            adv = attack_frame_dct_spsa(
                frame_bgr=frame, detectors=detectors, baselines=baselines,
                eps_pix=args.epsilon, alpha_pix=args.alpha, steps=args.steps,
                spsa=args.spsa, lf=args.lf, block=args.block, sigma_pix=args.sigma_pix,
                eot=True, debug_prefix=(args.debug_dir and os.path.join(args.debug_dir, f"frame{f:06d}"))
            )
            noise_cache = (adv.astype(np.int16) - frame.astype(np.int16))
        else:
            if noise_cache is None:
                adv = frame.copy()
            else:
                tmp = frame.astype(np.int16) + noise_cache
                adv = np.clip(tmp, 0, 255).astype(np.uint8)

        writer.write(adv)
        if args.log_every > 0 and (f % args.log_every == 0):
            print(f"[DCT-EOT] frame {f}")
        f += 1

    cap.release(); writer.release()
    print("[DCT-EOT] saved:", out_path)


# -----------------------------
# 메인
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--face_detector", choices=["sfd","blazeface"], default="sfd")
    ap.add_argument("--use_mediapipe", action="store_true")

    # 최적화/제약
    ap.add_argument("--epsilon", type=float, default=16.0, help="RGB L_inf pixel budget (e.g., 16)")
    ap.add_argument("--alpha", type=float, default=3.0, help="update step (roughly pixel scale)")
    ap.add_argument("--steps", type=int, default=8, help="iterations per optimized frame")
    ap.add_argument("--spsa", type=int, default=32, help="SPSA samples per step (2*spsa model queries)")
    ap.add_argument("--stride", type=int, default=1, help="optimize every n-th frame")
    ap.add_argument("--sigma_pix", type=float, default=1.0, help="heatmap sigma (pixels)")

    # DCT
    ap.add_argument("--lf", type=int, default=3, help="low-frequency size per 8x8 block (1..8)")
    ap.add_argument("--block", type=int, default=8, help="DCT block size (8 recommended)")

    # IO
    ap.add_argument("--fourcc", type=str, default="XVID")
    ap.add_argument("--debug_dir", type=str, default="")
    ap.add_argument("--log_every", type=int, default=30)

    args = ap.parse_args()

    # GPU 강제 확인
    if args.device == "cuda":
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable. Install GPU PyTorch / check drivers.")

    print("[DCT-EOT] start")
    process_video(args.input, args.output, args)

if __name__ == "__main__":
    main()

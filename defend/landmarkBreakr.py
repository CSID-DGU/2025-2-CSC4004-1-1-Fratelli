# LMB.py
# Black-box LandmarkBreaker (NES) with step-by-step verification.
# 단계별 확인(랜드마크 시각화, 히트맵 그리드, 손실 로그)을 debug_dir 아래 저장합니다.

import os, cv2, math, json, argparse, time
import numpy as np
from tqdm import tqdm
import torch
import torch.nn.functional as F
import face_alignment
from scipy.spatial import ConvexHull

# ----------------------------
# 기본 유틸
# ----------------------------
def ensure_dir(p):
    if p and not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

def to01(img_uint8_bgr):
    return (img_uint8_bgr.astype(np.float32) / 255.0)

def to255(img01_bgr):
    return np.clip(img01_bgr * 255.0, 0, 255).astype(np.uint8)

def tensor01_from_bgr(img_bgr):
    # BGR uint8 -> RGB float(0..1) tensor [1,3,H,W]
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    t = torch.from_numpy(rgb.astype(np.float32)/255.0).permute(2,0,1).unsqueeze(0).contiguous()
    return t

def bgr_from_tensor01(t):
    arr = (t.detach().clamp(0,1).squeeze(0).permute(1,2,0).cpu().numpy()*255.0).astype(np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

# ----------------------------
# 디버깅/시각화
# ----------------------------
def draw_landmarks(img_bgr, landmarks_list, color=(0,255,0)):
    vis = img_bgr.copy()
    if landmarks_list:
        for pts in landmarks_list:
            for (x,y) in pts:
                cv2.circle(vis, (int(x), int(y)), 1, color, -1, lineType=cv2.LINE_AA)
    return vis

def save_heatmap_grid(hmaps, out_path):
    """
    hmaps: torch (1,K,H,W), 0..1 (정규화 가정)
    """
    h = hmaps.detach().cpu().numpy()[0]  # (K,H,W)
    K, Hm, Wm = h.shape
    cols = int(math.ceil(math.sqrt(K)))
    rows = int(math.ceil(K / cols))
    canvas = np.zeros((rows*Hm, cols*Wm), np.float32)
    for i in range(K):
        r = i // cols
        c = i % cols
        tile = h[i]
        m = tile.max()
        if m > 0: tile = tile / m
        canvas[r*Hm:(r+1)*Hm, c*Wm:(c+1)*Wm] = tile
    canvas = (canvas*255).astype(np.uint8)
    cv2.imwrite(out_path, canvas)

def log_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# ----------------------------
# Landmark → 가우시안 히트맵
# ----------------------------
def gaussian_heatmaps_from_points(points_xy, size_hw, sigma=3.0):
    """
    points_xy: (K,2) in (x,y)
    size_hw: (H,W)
    return: torch (1,K,H,W), 각 채널 max=1로 정규화
    """
    H, W = size_hw
    pts = np.asarray(points_xy, dtype=np.float32)
    K = pts.shape[0]
    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    stack = []
    for k in range(K):
        x, y = pts[k]
        g = np.exp(-((xx - x)**2 + (yy - y)**2)/(2*sigma*sigma))
        stack.append(g)
    hmaps = np.stack(stack, 0)  # (K,H,W)
    hmaps = hmaps / (np.max(hmaps, axis=(1,2), keepdims=True) + 1e-8)
    return torch.from_numpy(hmaps).float().unsqueeze(0)  # (1,K,H,W)

def cosine_heatmap_loss(h_ref, h_cur):
    """
    두 히트맵 집합 간 코사인 유사도 평균(값이 작아질수록 ‘덜 닮음’ → 교란 성공).
    """
    N, K, Hm, Wm = h_ref.shape
    a = F.normalize(h_ref.reshape(N, K, -1), dim=-1)
    b = F.normalize(h_cur.reshape(N, K, -1), dim=-1)
    cos = (a*b).sum(dim=-1).mean()
    return cos

# ----------------------------
# 얼굴 마스크 (LB++용, 선택)
# ----------------------------
def build_face_mask(h, w, landmarks_list):
    """
    여러 얼굴의 볼록껍질 합집합(안=1, 밖=0) uint8
    """
    mask = np.zeros((h,w), np.uint8)
    if not landmarks_list:
        return mask
    for pts in landmarks_list:
        pts = np.array(pts, dtype=np.int32)
        if len(pts) >= 3:
            hull = ConvexHull(pts)
            poly = pts[hull.vertices]
            cv2.fillConvexPoly(mask, poly, 255)
    return mask

# ----------------------------
# EOT (강인성용 랜덤 변환)
# ----------------------------
def eot_augment(img_bgr):
    h,w = img_bgr.shape[:2]
    # resize jitter
    scale = np.random.uniform(0.87, 1.10)
    nh, nw = max(8,int(h*scale)), max(8,int(w*scale))
    aug = cv2.resize(img_bgr, (nw,nh), interpolation=cv2.INTER_LINEAR)
    aug = cv2.resize(aug, (w,h), interpolation=cv2.INTER_LINEAR)
    # jpeg
    q = int(np.random.uniform(40,90))
    _, buf = cv2.imencode('.jpg', aug, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    aug = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    # blur
    if np.random.rand() < 0.5:
        k = np.random.choice([3,5])
        aug = cv2.GaussianBlur(aug, (k,k), 0)
    # brightness/contrast
    alpha = np.random.uniform(0.92, 1.08)
    beta  = np.random.uniform(-7, 7)
    aug = np.clip(alpha*aug + beta, 0, 255).astype(np.uint8)
    return aug

# ----------------------------
# 손실(블랙박스): 프레임 BGR → 랜드마크 → 히트맵 → 코사인 손실
# ----------------------------
def compute_loss_for_image(img_bgr, fa, h_ref, face_limit=1):
    lms_list = fa.get_landmarks(img_bgr)
    if (lms_list is None) or (len(lms_list)==0):
        # 얼굴 못 찾으면 이미 크게 교란된 것으로 간주 → 손실 0
        return torch.tensor(0.0)
    if face_limit is not None:
        lms_list = lms_list[:face_limit]
    H, W = img_bgr.shape[:2]
    # 여기서는 첫 얼굴 기준으로 손실 계산(원하시면 평균으로 확장 가능)
    cur = gaussian_heatmaps_from_points(lms_list[0], (H,W), sigma=3.0)
    return cosine_heatmap_loss(h_ref, cur)

# ----------------------------
# NES LandmarkBreaker (핵심 5단계)
# ----------------------------
def landmark_breaker_nes(
    frame_bgr, fa,
    epsilon_pix=8,        # 8/255
    alpha_pix=1,          # 1/255
    steps=20,
    momentum=0.9,
    K=8,                  # 샘플 방향 수
    sigma_pix=0.5,        # 유한차분 스텝(픽셀단위)
    eot_n=0,              # EOT 변환 횟수(0이면 사용 안함)
    lbpp=False,           # 얼굴 내부 보호(배경 위주 교란)
    debug=None            # dict: {dir, frame_idx} 등
):
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    H, W = frame_bgr.shape[:2]

    # 1) 프레임 읽기 (입력 받음)

    # 2) 얼굴+랜드마크 얻기 (기본 시각화 저장)
    lms0 = fa.get_landmarks(frame_bgr)
    if (lms0 is None) or (len(lms0)==0):
        # 얼굴 없음: 그대로 반환
        if debug:
            cv2.imwrite(os.path.join(debug['dir'], f"{debug['prefix']}_step0_no_face.png"), frame_bgr)
        return frame_bgr

    vis0 = draw_landmarks(frame_bgr, [lms0[0]], color=(0,255,0))
    if debug:
        cv2.imwrite(os.path.join(debug['dir'], f"{debug['prefix']}_step2_landmarks_ref.png"), vis0)

    # 3) 기준 히트맵 만들기
    h_ref = gaussian_heatmaps_from_points(lms0[0], (H,W), sigma=3.0)
    if debug:
        save_heatmap_grid(h_ref, os.path.join(debug['dir'], f"{debug['prefix']}_step3_ref_hmaps.png"))

    # 4) 노이즈 반복 업데이트 (NES)
    x0 = tensor01_from_bgr(frame_bgr).to(dev)
    x  = x0.clone().detach()                   # [1,3,H,W], 0..1
    eps  = epsilon_pix / 255.0
    alpha = alpha_pix  / 255.0
    sigma = sigma_pix  / 255.0
    m = torch.zeros_like(x)

    # LB++: 얼굴 내부 보호 마스크
    face_mask = build_face_mask(H,W,[lms0[0]])
    face_mask_t = torch.from_numpy((face_mask>0).astype(np.float32)).unsqueeze(0).unsqueeze(0).to(dev)

    # 진행 로그
    step_log = []

    for t in range(steps):
        grad_est = torch.zeros_like(x)

        # NES 유한차분
        for _ in range(K):
            u = torch.randn_like(x)
            x_pos = (x + sigma*u).clamp(0,1)
            x_neg = (x - sigma*u).clamp(0,1)

            img_pos = bgr_from_tensor01(x_pos)
            img_neg = bgr_from_tensor01(x_neg)

            if eot_n > 0:
                # EOT 평균
                losses_pos, losses_neg = [], []
                for _e in range(eot_n):
                    losses_pos.append(compute_loss_for_image(eot_augment(img_pos), fa, h_ref))
                    losses_neg.append(compute_loss_for_image(eot_augment(img_neg), fa, h_ref))
                Lp = torch.stack(losses_pos).mean()
                Ln = torch.stack(losses_neg).mean()
            else:
                Lp = compute_loss_for_image(img_pos, fa, h_ref)
                Ln = compute_loss_for_image(img_neg, fa, h_ref)

            diff = (Lp - Ln).detach()
            grad_est = grad_est + diff * u

        grad_est = grad_est / (K * sigma)
        m = momentum * m + grad_est / (grad_est.abs().mean() + 1e-12)

        if lbpp:
            # 얼굴 내부 보호: 얼굴 안쪽=1 → 보존(업데이트 억제)
            flat = m.abs().mean(dim=1, keepdim=True)   # (1,1,H,W)
            med  = torch.median(flat)
            keep = (flat > med).float()
            keep = keep * (1.0 - face_mask_t)          # 배경만 유지
            step = alpha * torch.sign(m) * keep
        else:
            step = alpha * torch.sign(m)

        x = (x - step).clamp(x0 - eps, x0 + eps).clamp(0,1).detach()

        # 진행 상황 확인(현재 x에서의 손실, 랜드마크 그림)
        cur_img = bgr_from_tensor01(x)
        L_now = compute_loss_for_image(cur_img, fa, h_ref)
        rec = {'step': int(t+1), 'loss': float(L_now.item())}
        step_log.append(rec)

        if debug and ((t+1) % max(1, debug.get('dump_every', 5)) == 0 or t==0 or (t+1)==steps):
            # 현재 랜드마크 시각화
            lms_now = fa.get_landmarks(cur_img)
            vis_now = draw_landmarks(cur_img, lms_now if lms_now else [], color=(0,0,255))
            cv2.imwrite(os.path.join(debug['dir'], f"{debug['prefix']}_iter{t+1:03d}_image.png"), cur_img)
            cv2.imwrite(os.path.join(debug['dir'], f"{debug['prefix']}_iter{t+1:03d}_landmarks.png"), vis_now)
            # 현재 히트맵
            if lms_now:
                h_cur = gaussian_heatmaps_from_points(lms_now[0], (H,W), sigma=3.0)
                save_heatmap_grid(h_cur, os.path.join(debug['dir'], f"{debug['prefix']}_iter{t+1:03d}_hmaps.png"))
            # 로그 저장(덮어쓰기)
            log_json(step_log, os.path.join(debug['dir'], f"{debug['prefix']}_log.json"))

    # 5) 제한 유지된 최종 결과
    out = bgr_from_tensor01(x)
    if debug:
        cv2.imwrite(os.path.join(debug['dir'], f"{debug['prefix']}_final.png"), out)
        log_json(step_log, os.path.join(debug['dir'], f"{debug['prefix']}_log.json"))
    return out

# ----------------------------
# 메인: 이미지/비디오 모두 지원
# ----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='이미지(.jpg/.png) 또는 비디오(.mp4 등)')
    ap.add_argument('--output', required=True, help='출력 이미지/비디오 경로')
    ap.add_argument('--mode', choices=['auto','image','video'], default='auto', help='입력 타입 자동/강제')
    ap.add_argument('--epsilon', type=float, default=8.0, help='L_inf 허용치(픽셀 단위, 예: 8 → 8/255)')
    ap.add_argument('--alpha', type=float, default=1.0, help='스텝 크기(픽셀 단위, 예: 1 → 1/255)')
    ap.add_argument('--steps', type=int, default=20)
    ap.add_argument('--momentum', type=float, default=0.9)
    ap.add_argument('--k', type=int, default=8, help='NES 샘플 방향 수')
    ap.add_argument('--sigma_pix', type=float, default=0.5, help='유한차분 스텝(픽셀단위)')
    ap.add_argument('--eot', type=int, default=0, help='EOT 변환 반복(0 비활성, 2~4 권장)')
    ap.add_argument('--lbpp', action='store_true', help='얼굴 내부 보호(배경 위주 교란)')
    ap.add_argument('--face_detector', choices=['sfd','blazeface','mediapipe','dlib'], default='blazeface')
    ap.add_argument('--stride', type=int, default=1, help='프레임 간격 처리(>1이면 스킵 복제)')
    ap.add_argument('--max_frames', type=int, default=None, help='최대 처리 프레임 수(디버깅용)')
    ap.add_argument('--debug_dir', type=str, default=None, help='중간 산출물 저장 폴더')
    ap.add_argument('--dump_every', type=int, default=5, help='몇 스텝마다 중간 결과 저장할지')
    args = ap.parse_args()

    ensure_dir(os.path.dirname(args.output) or '.')
    if args.debug_dir:
        ensure_dir(args.debug_dir)

    # face_alignment 초기화 (버전 호환: TWO_D or _2D)
    LT = face_alignment.LandmarksType
    landmarks_2d = LT.TWO_D if hasattr(LT, 'TWO_D') else LT._2D
    fa = face_alignment.FaceAlignment(
        landmarks_2d,
        device='cuda' if torch.cuda.is_available() else 'cpu',
        flip_input=False,
        face_detector=args.face_detector
    )

    # 입력 타입 결정
    mode = args.mode
    if mode == 'auto':
        ext = os.path.splitext(args.input)[1].lower()
        mode = 'image' if ext in ['.jpg','.jpeg','.png','.bmp'] else 'video'

    if mode == 'image':
        img = cv2.imread(args.input, cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError('입력 이미지를 열 수 없습니다.')
        debug = None
        if args.debug_dir:
            prefix = os.path.splitext(os.path.basename(args.input))[0]
            debug = {'dir': args.debug_dir, 'prefix': prefix, 'dump_every': args.dump_every}
            cv2.imwrite(os.path.join(args.debug_dir, f"{prefix}_step1_input.png"), img)
        out = landmark_breaker_nes(
            img, fa,
            epsilon_pix=args.epsilon, alpha_pix=args.alpha, steps=args.steps,
            momentum=args.momentum, K=args.k, sigma_pix=args.sigma_pix,
            eot_n=args.eot, lbpp=args.lbpp, debug=debug
        )
        ok = cv2.imwrite(args.output, out)
        print('✅ Saved:', args.output, 'OK' if ok else 'FAIL')

    else:
        cap = cv2.VideoCapture(args.input)
        if not cap.isOpened():
            raise RuntimeError('입력 비디오를 열 수 없습니다.')
        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        vw = cv2.VideoWriter(args.output, fourcc, fps, (W,H))
        nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        total = nframes if (args.max_frames is None) else min(nframes, args.max_frames)
        pbar = tqdm(total=total if total>0 else None, desc='Processing')

        fidx = 0
        wcount = 0
        last_out = None
        while True:
            ok, frame = cap.read()
            if not ok: break

            if (fidx % args.stride) != 0:
                # stride 스킵: 직전 결과 복제(속도 ↑)
                if last_out is not None:
                    vw.write(last_out)
                    wcount += 1
                    if total: pbar.update(1)
                fidx += 1
                continue

            debug = None
            if args.debug_dir:
                prefix = f"frame{fidx:06d}"
                debug = {'dir': args.debug_dir, 'prefix': prefix, 'dump_every': args.dump_every}
                cv2.imwrite(os.path.join(args.debug_dir, f"{prefix}_step1_input.png"), frame)

            out = landmark_breaker_nes(
                frame, fa,
                epsilon_pix=args.epsilon, alpha_pix=args.alpha, steps=args.steps,
                momentum=args.momentum, K=args.k, sigma_pix=args.sigma_pix,
                eot_n=args.eot, lbpp=args.lbpp, debug=debug
            )
            vw.write(out)
            last_out = out
            fidx += 1
            wcount += 1
            if total: pbar.update(1)
            if args.max_frames is not None and wcount >= args.max_frames:
                break

        pbar.close()
        cap.release()
        vw.release()
        print('✅ Saved:', args.output)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
LMB_StrongHybrid.py
Hybrid proactive DeepFake defense:
 - Landmark heatmap disruption (SPSA, LandmarkBreaker)
 - Optical-flow propagation across frames (VideoFacePoison)
 - Add high-frequency universal watermark (CMUA-style)
 - GPU forced on onnxruntime where possible

Dependencies:
 pip install onnxruntime-gpu face-alignment opencv-python numpy scipy

Usage example:
 python LMB_StrongHybrid.py --input in.mp4 --output out.mp4 --device cuda
"""
import os, sys, time, argparse
import numpy as np
import cv2
import math
import onnxruntime as ort
import face_alignment
from scipy.fftpack import dct, idct

# ---------------- helpers ----------------
def to_uint8(x):
    return np.clip(x*255.0,0,255).astype(np.uint8)

def from_uint8(x):
    return x.astype(np.float32)/255.0

def l2normalize(x, eps=1e-8):
    n = np.linalg.norm(x)
    return x / (n+eps)

# choose k indices helper (same as LMB)
def choose_k_indices(num_points: int, k: int) -> np.ndarray:
    if (k is None) or (k <= 0) or (k >= num_points):
        return np.arange(num_points)
    step = num_points / float(k)
    idx = np.floor(np.arange(k) * step).astype(int)
    idx = np.clip(idx, 0, num_points - 1)
    return np.unique(idx)

def gaussian_2d(h, w, cx, cy, sigma):
    yy, xx = np.mgrid[0:h, 0:w]
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * sigma * sigma))
    return g

def make_heatmap_from_landmarks(landmarks_xy: np.ndarray, H: int, W: int, sigma_pix: float = 1.5, k: int = 68):
    if landmarks_xy is None or len(landmarks_xy) == 0:
        return np.zeros((1,H,W),dtype=np.float32)
    pts = landmarks_xy.reshape(-1,2)
    use_idx = choose_k_indices(len(pts), k)
    pts = pts[use_idx]
    hm = np.zeros((len(pts), H, W), dtype=np.float32)
    for i, (x,y) in enumerate(pts):
        hm[i] = gaussian_2d(H,W,x,y,sigma_pix)
    return hm

def cosine_similarity(a,b):
    a_f = a.reshape(a.shape[0], -1)
    b_f = b.reshape(b.shape[0], -1)
    a_n = a_f / (np.linalg.norm(a_f, axis=1, keepdims=True) + 1e-8)
    b_n = b_f / (np.linalg.norm(b_f, axis=1, keepdims=True) + 1e-8)
    cos = (a_n * b_n).sum(axis=1)
    return float(np.mean(cos))

def largest_face(landmarks_list):
    if (landmarks_list is None) or (len(landmarks_list)==0):
        return None
    if len(landmarks_list)==1:
        return landmarks_list[0]
    def area(pts):
        x1,y1 = pts.min(axis=0); x2,y2 = pts.max(axis=0)
        return (x2-x1)*(y2-y1)
    sizes = [area(p) for p in landmarks_list]
    return landmarks_list[int(np.argmax(sizes))]

# ---------------- optical flow propagation ----------------
def propagate_perturb(prev_frame, cur_frame, prev_noise):
    # prev_frame, cur_frame: BGR uint8
    # prev_noise: float32 noise same shape as frame in [-eps,eps] (value scale 0..1)
    # return estimated noise for cur_frame by warping prev_noise via flow
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    cur_gray = cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(prev_gray, cur_gray,
                                        None, 0.5, 3, 15, 3, 5, 1.2, 0)
    h,w = flow.shape[:2]
    # grid
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (xx + flow[...,0]).astype(np.float32)
    map_y = (yy + flow[...,1]).astype(np.float32)
    warped = cv2.remap(prev_noise, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return warped

# ---------------- universal HF watermark (tile pattern in DCT domain) ----------------
def make_hf_watermark(H, W, strength=0.05, tile=16, seed=1234):
    rng = np.random.RandomState(seed)
    # create small random high-frequency patch in DCT domain
    ph = tile; pw = tile
    base = rng.randn(ph,pw)
    # zero out low frequencies: keep high-frequency ring
    mask = np.ones_like(base)
    cx,cy = ph//2, pw//2
    r = min(ph,pw)//4
    for i in range(ph):
        for j in range(pw):
            # distance from center
            if (i-cx)**2 + (j-cy)**2 < (r*r):
                mask[i,j] = 0.0
    base *= mask
    # upsample tile to full size by tiling plus slight jitter
    tiles_y = int(math.ceil(H/ph)); tiles_x = int(math.ceil(W/pw))
    big = np.tile(base, (tiles_y, tiles_x))
    big = big[:H,:W]
    # inverse DCT to spatial pattern and normalize to [-1,1]
    # approximate via idct rows/cols
    spatial = idct(idct(big.T, norm='ortho').T, norm='ortho')
    spatial = spatial - spatial.mean()
    spatial = spatial / (spatial.std()+1e-8)
    # convert to 3-channel subtle pattern
    pat = np.stack([spatial, spatial, spatial], axis=-1)
    pat = pat * strength
    return pat.astype(np.float32)  # values in approx [-strength, +strength]

# ---------------- SPSA on heatmap loss (stronger) ----------------
def spsa_step_blackbox(img01, baseline_hm, fa_detector, alpha, delta, sigma_pix, k, spsa_samples=32):
    H,W = img01.shape[:2]
    g_hat = np.zeros_like(img01, dtype=np.float32)
    for _ in range(spsa_samples):
        u = np.random.choice([-1.0,1.0], size=img01.shape).astype(np.float32)
        img_p = np.clip(img01 + delta*u, 0.0, 1.0)
        lm_p = fa_detector.get_landmarks(to_uint8(img_p))
        lm_p = largest_face(lm_p)
        hm_p = make_heatmap_from_landmarks(lm_p, H, W, sigma_pix=sigma_pix, k=k)
        Lp = cosine_similarity(hm_p, baseline_hm)

        img_m = np.clip(img01 - delta*u, 0.0, 1.0)
        lm_m = fa_detector.get_landmarks(to_uint8(img_m))
        lm_m = largest_face(lm_m)
        hm_m = make_heatmap_from_landmarks(lm_m, H, W, sigma_pix=sigma_pix, k=k)
        Lm = cosine_similarity(hm_m, baseline_hm)

        g_hat += ((Lp - Lm) / (2.0 * delta)) * u
    g_hat /= float(max(1, spsa_samples))
    step = -alpha * np.sign(g_hat)
    return step

def attack_frame_strong(frame_bgr, fa_detector,
                        steps=8, epsilon=12, alpha=2, k=68, sigma_pix=1.2,
                        spsa_samples=64, eot=3, hf_pat=None, hf_strength=0.04):
    H,W = frame_bgr.shape[:2]
    img01 = from_uint8(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    lm0 = fa_detector.get_landmarks(to_uint8(img01))
    lm0 = largest_face(lm0)
    if lm0 is None:
        return frame_bgr, np.zeros_like(img01, dtype=np.float32)
    baseline_hm = make_heatmap_from_landmarks(lm0, H, W, sigma_pix=sigma_pix, k=k)
    eps01 = epsilon/255.0
    alpha01 = alpha/255.0
    delta01 = max(1.0, alpha)/255.0

    x_adv = img01.copy()
    x_orig = img01.copy()

    # warm-start: add hf_pat if provided (keeps subtle)
    if hf_pat is not None:
        x_adv = np.clip(x_adv + hf_pat*hf_strength, 0.0, 1.0)

    for t in range(steps):
        # SPSA optimizer with EOT
        g = np.zeros_like(x_adv)
        for _e in range(max(1,eot)):
            step_dir = spsa_step_blackbox(x_adv, baseline_hm, fa_detector,
                                         alpha=alpha01, delta=delta01,
                                         sigma_pix=sigma_pix, k=k,
                                         spsa_samples=spsa_samples//max(1,eot))
            g += step_dir
        g /= float(max(1,eot))
        x_adv = np.clip(x_adv + g, 0.0, 1.0)
        # projection L_inf
        diff = np.clip(x_adv - x_orig, -eps01, eps01)
        x_adv = np.clip(x_orig + diff, 0.0, 1.0)

    # blend back using Gaussian mask around face bbox
    # compute bbox from landmarks
    pts = lm0
    x_min = max(0, int(np.floor(pts[:,0].min()))); x_max = min(W-1, int(np.ceil(pts[:,0].max())))
    y_min = max(0, int(np.floor(pts[:,1].min()))); y_max = min(H-1, int(np.ceil(pts[:,1].max())))
    mask = np.zeros((H,W), dtype=np.float32)
    mask[y_min:y_max+1, x_min:x_max+1] = 1.0
    ksz = max(3, min(51, (x_max-x_min+1)//4 | 1))
    mask = cv2.GaussianBlur(mask, (ksz,ksz), sigmaX=ksz/2.0)
    mask = mask[:,:,None]

    warped_adv_bgr = cv2.cvtColor(to_uint8(x_adv), cv2.COLOR_RGB2BGR)
    out = (warped_adv_bgr.astype(np.float32)*mask + frame_bgr.astype(np.float32)*(1.0-mask))
    out = np.clip(out,0,255).astype(np.uint8)
    noise = (from_uint8(out.astype(np.uint8)) - from_uint8(frame_bgr.astype(np.uint8))).astype(np.float32)
    return out, noise

# ---------------- main processing ----------------
def process_video(input_path, output_path, args):
    # face_alignment detector
    LT = None
    if hasattr(face_alignment, "LandmarksType"):
        # safe resolve similar to LMB.py
        try:
            LT = face_alignment.LandmarksType._2D
        except Exception:
            try:
                LT = face_alignment.LandmarksType.TWO_D
            except:
                LT = face_alignment.LandmarksType
    else:
        LT = 1
    fa = face_alignment.FaceAlignment(LT, device=args.face_device, face_detector=args.face_detector)

    # universal HF pattern
    hf_pat = make_hf_watermark(256,256, strength=1.0, tile=args.hf_tile, seed=args.hf_seed)
    # resize hf pattern to frames dynamically later by cropping/tiling
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open input video.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (W,H))
    prev_frame = None
    prev_noise = None
    frame_idx = 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    print("[Hybrid] start video", input_path, "->", output_path)
    start_t = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        # generate hf pattern for this size
        # tile/resize hf_pat to HxW
        hh, ww = hf_pat.shape[0], hf_pat.shape[1]
        tile_y = int(math.ceil(H/hh)); tile_x = int(math.ceil(W/ww))
        big = np.tile(hf_pat, (tile_y, tile_x, 1))[:H,:W,:]
        # if stride skip heavy optimize and reuse propagated or cached noise
        if (frame_idx % max(1,args.stride)) == 0:
            # attempt propagate previous noise via optical flow to warmstart
            propagated = None
            if (prev_frame is not None) and (prev_noise is not None):
                try:
                    propagated = propagate_perturb(prev_frame, frame, prev_noise)
                except Exception as e:
                    propagated = None
            # attack this frame strongly
            out, noise = attack_frame_strong(frame, fa,
                                             steps=args.steps, epsilon=args.eps,
                                             alpha=args.alpha, k=args.k, sigma_pix=args.sigma_pix,
                                             spsa_samples=args.spsa, eot=args.eot,
                                             hf_pat=big, hf_strength=args.hf_strength)
            prev_noise = noise
        else:
            # reuse prev_noise if available (to save time) or propagate
            if prev_noise is None:
                out = frame
            else:
                try:
                    propagated = propagate_perturb(prev_frame, frame, prev_noise)
                    # apply propagated noise with small temporal smoothing
                    blend_noise = 0.85*prev_noise + 0.15*propagated
                    tmp = (from_uint8(frame.astype(np.uint8)) + blend_noise)
                    out = np.clip(to_uint8(tmp)*1.0,0,255).astype(np.uint8)
                    prev_noise = blend_noise
                except Exception as e:
                    out = frame
        writer.write(out)
        prev_frame = frame.copy()
        if frame_idx % args.log_every == 0:
            print(f"[{frame_idx}/{total}] wrote frame")
        frame_idx += 1
    writer.release()
    cap.release()
    print("[done] total time:", time.time()-start_t)

# ---------------- argparse ----------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", default="cuda", choices=["cuda","cpu"])
    p.add_argument("--face_device", default="cuda")
    p.add_argument("--face_detector", default="sfd", choices=["sfd","blazeface"])
    p.add_argument("--eps", type=int, default=12)
    p.add_argument("--alpha", type=float, default=2.0)
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--k", type=int, default=68)
    p.add_argument("--sigma_pix", type=float, default=1.2)
    p.add_argument("--spsa", type=int, default=64)
    p.add_argument("--eot", type=int, default=3)
    p.add_argument("--stride", type=int, default=2)
    p.add_argument("--hf_strength", type=float, default=0.06)
    p.add_argument("--hf_tile", type=int, default=16)
    p.add_argument("--hf_seed", type=int, default=1337)
    p.add_argument("--log_every", type=int, default=30)
    args = p.parse_args()

    # face_alignment device handling already done via args.face_device
    process_video(args.input, args.output, args)

if __name__ == "__main__":
    main()

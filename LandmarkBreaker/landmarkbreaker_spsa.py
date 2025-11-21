
import os, cv2, numpy as np, argparse
from tqdm import tqdm

try:
    import mediapipe as mp
    MP_OK = True
except Exception:
    MP_OK = False

def temporal_smooth(prev_W, W, alpha=0.7):
    if prev_W is None:
        return W
    return (alpha * prev_W + (1.0 - alpha) * W)

def tv_norm(x):
    dx = np.abs(x[:,1:,:] - x[:,:-1,:]).mean()
    dy = np.abs(x[1:,:,:] - x[:-1,:,:]).mean()
    return dx + dy

def face_edge_mask(h, w, cx, cy, r_inner=0.45, r_outer=0.85):
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - cx) / (w*0.5)
    ny = (yy - cy) / (h*0.5)
    rr = np.sqrt(nx*nx + ny*ny)
    mask = np.clip((rr - r_inner) / (r_outer - r_inner + 1e-6), 0, 1)
    mask = cv2.GaussianBlur(mask, (0,0), 5)
    mask = mask[:,:,None]
    return mask

def jpeg_sim(img, q=85):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(q)]
    _, enc = cv2.imencode(".jpg", img, encode_param)
    dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return dec

def detect_landmarks(img_bgr):
    if not MP_OK:
        return None, None
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as fm:
        res = fm.process(img_rgb)
    if not res.multi_face_landmarks:
        return None, None
    pts = res.multi_face_landmarks[0].landmark
    h, w = img_bgr.shape[:2]
    coords = np.array([[p.x*w, p.y*h] for p in pts], dtype=np.float32)
    cx, cy = coords[:,0].mean(), coords[:,1].mean()
    return coords, (cx, cy)

def landmark_instability_loss(img_clean, img_pert):
    lm0, _ = detect_landmarks(img_clean)
    lm1, _ = detect_landmarks(img_pert)
    if lm0 is None or lm1 is None:
        return 0.0, 0.0
    d = np.linalg.norm(lm0 - lm1, axis=1).mean()
    return -d, d

def spsa_step(base, work, loss_fn, step_size=1.0, mask=None, eps=6):
    h, w, c = base.shape
    delta = np.random.choice([-1.0, 1.0], size=(h, w, c)).astype(np.float32)
    if mask is not None:
        delta *= mask
    c_k = 1.0
    x_plus  = np.clip(work.astype(np.float32) + c_k*delta, 0, 255).astype(np.uint8)
    x_minus = np.clip(work.astype(np.float32) - c_k*delta, 0, 255).astype(np.uint8)
    Lp, _ = loss_fn(base, x_plus)
    Lm, _ = loss_fn(base, x_minus)
    g_hat = (Lp - Lm) / (2.0 * c_k + 1e-8) * delta
    g = g_hat / (np.mean(np.abs(g_hat)) + 1e-8)
    x_new = work.astype(np.float32) - step_size * g
    diff = x_new.astype(np.int32) - base.astype(np.int32)
    diff = np.clip(diff, -eps, eps).astype(np.int16)
    x_new = np.clip(base.astype(np.int32) + diff, 0, 255).astype(np.uint8)
    return x_new, float(Lp), float(Lm)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--eps", type=int, default=6)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--iters-per-frame", type=int, default=8)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jpegq", type=int, default=88)
    ap.add_argument("--alpha-temporal", type=float, default=0.7)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        raise SystemExit("Cannot open input video.")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    FPS = args.fps if args.fps>0 else cap.get(cv2.CAP_PROP_FPS)

    outv = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W,H))
    tmp_prev_W = None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT)>0 else None
    pbar = tqdm(total=total_frames, desc="LandmarkBreaker++")

    while True:
        ret, frame = cap.read()
        if not ret: break
        base = frame.copy()

        lm, center = detect_landmarks(base)
        if center is None:
            outv.write(base)
            if pbar: pbar.update(1)
            continue
        cx, cy = center
        mask = face_edge_mask(H, W, cx, cy, r_inner=0.40, r_outer=0.90)

        def loss_on_img(clean, pert):
            sim = jpeg_sim(pert, q=args.jpegq)
            L, raw = landmark_instability_loss(clean, sim)
            tv = tv_norm((sim.astype(np.float32)-clean.astype(np.float32))/255.0)
            return L + 0.05*tv, raw

        work = base.copy()
        for _ in range(args.iters-per-frame if False else args.iters_per_frame):
            for _s in range(args.steps):
                work, Lp, Lm = spsa_step(base, work, loss_on_img, step_size=1.0, mask=mask, eps=args.eps)
            if tmp_prev_W is not None:
                curr_W = (work.astype(np.float32) - base.astype(np.float32))
                sm_W = temporal_smooth(tmp_prev_W, curr_W, alpha=args.alpha_temporal)
                sm_W = np.clip(sm_W, -args.eps, args.eps)
                work = np.clip(base.astype(np.float32)+sm_W, 0, 255).astype(np.uint8)

        tmp_prev_W = (work.astype(np.float32) - base.astype(np.float32))
        outv.write(work)
        if pbar: pbar.update(1)

    cap.release(); outv.release()
    if pbar: pbar.close()
    print("Saved:", args.output)

if __name__ == "__main__":
    if not MP_OK:
        print("[WARN] MediaPipe not found; please `pip install mediapipe`.")
    main()

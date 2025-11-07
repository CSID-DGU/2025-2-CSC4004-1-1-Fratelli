
import os, cv2, numpy as np, argparse
from tqdm import tqdm

try:
    import mediapipe as mp
    MP_OK = True
except Exception:
    MP_OK = False

def jpeg_sim(img, q=85):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(q)]
    _, enc = cv2.imencode(".jpg", img, encode_param)
    dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return dec

def detect_landmarks(img_bgr):
    if not MP_OK: return None
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as fm:
        res = fm.process(img_rgb)
    if not res.multi_face_landmarks:
        return None
    pts = res.multi_face_landmarks[0].landmark
    h, w = img_bgr.shape[:2]
    coords = np.array([[p.x*w, p.y*h] for p in pts], dtype=np.float32)
    return coords

def landmark_var_loss(base_list, pert_list):
    acc = 0.0; count = 0
    for b, p in zip(base_list, pert_list):
        lm0 = detect_landmarks(b); lm1 = detect_landmarks(p)
        if lm0 is None or lm1 is None: 
            acc += 5.0; count += 1
            continue
        d = np.linalg.norm(lm0 - lm1, axis=1).mean()
        acc += d; count += 1
    if count == 0: return 0.0
    return -acc / count

def tv_norm(x):
    dx = np.abs(x[:,1:,:] - x[:,:-1,:]).mean()
    dy = np.abs(x[1:,:,:] - x[:-1,:,:]).mean()
    return dx + dy

def cmua_temporal_opt(frames, eps=5, steps=10, iters=200, jpegq=88, lambda_temporal=2.0, lambda_tv=0.05):
    W = [np.zeros_like(frames[0], dtype=np.float32) for _ in frames]

    for it in tqdm(range(iters), desc="CMUA-temporal"):
        pert = []
        for t in range(len(frames)):
            base = frames[t]
            w = W[t]
            if t>0:
                w = 0.7 * W[t] + 0.3 * W[t-1]
            img = np.clip(base.astype(np.float32) + w, 0, 255).astype(np.uint8)
            img = jpeg_sim(img, q=jpegq)
            pert.append(img)

        L_main = landmark_var_loss(frames, pert)
        L_temp = 0.0
        L_tv = 0.0
        for t in range(1, len(W)):
            L_temp += np.mean(np.abs(W[t] - W[t-1])) / 255.0
        for t in range(len(W)):
            L_tv  += tv_norm(W[t]/255.0)

        # SPSA-like update
        for t in range(len(W)):
            base = frames[t]; w = W[t]
            delta = np.random.choice([-1.0, 1.0], size=w.shape).astype(np.float32)
            wp = np.clip(w + delta, -eps, eps)
            imgp = np.clip(base.astype(np.float32)+wp, 0, 255).astype(np.uint8)
            imgp = jpeg_sim(imgp, q=jpegq)
            wm = np.clip(w - delta, -eps, eps)
            imgm = np.clip(base.astype(np.float32)+wm, 0, 255).astype(np.uint8)
            imgm = jpeg_sim(imgm, q=jpegq)

            lm0 = detect_landmarks(base); lmp = detect_landmarks(imgp); lmm = detect_landmarks(imgm)
            def disp(a,b):
                if a is None or b is None: return 5.0
                return np.linalg.norm(a-b,axis=1).mean()
            Lp = -disp(lm0,lmp); Lm = -disp(lm0,lmm)
            g = (Lp - Lm) / (2.0 + 1e-8) * delta
            g = g / (np.mean(np.abs(g)) + 1e-8)
            W[t] = np.clip(w - 1.0 * g, -eps, eps)

    out = []
    for t in range(len(frames)):
        img = np.clip(frames[t].astype(np.float32) + W[t], 0, 255).astype(np.uint8)
        out.append(img)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--eps", type=int, default=5)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jpegq", type=int, default=88)
    ap.add_argument("--lambda-temporal", type=float, default=2.0)
    ap.add_argument("--lambda-tv", type=float, default=0.05)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened(): raise SystemExit("Cannot open input video.")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    FPS = args.fps if args.fps>0 else cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret: break
        frames.append(f.copy())
    cap.release()
    if len(frames)==0: raise SystemExit("No frames.")

    out_frames = cmua_temporal_opt(
        frames, eps=args.eps, steps=args.steps, iters=args.iters, jpegq=args.jpegq,
        lambda_temporal=args.lambda_temporal, lambda_tv=args.lambda_tv
    )

    outv = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W,H))
    for f in out_frames: outv.write(f)
    outv.release()
    print("Saved:", args.output)

if __name__ == "__main__":
    if not MP_OK:
        print("[WARN] MediaPipe not found; please `pip install mediapipe`.")
    main()

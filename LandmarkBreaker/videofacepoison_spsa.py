
import os, cv2, numpy as np, argparse
from tqdm import tqdm

try:
    import mediapipe as mp
    MP_OK = True
except Exception:
    MP_OK = False

def detect_faces_conf(img_bgr):
    if not MP_OK: return []
    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.3) as fd:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        res = fd.process(img_rgb)
        if not res.detections: return []
        h, w = img_bgr.shape[:2]
        outs = []
        for det in res.detections:
            loc = det.location_data.relative_bounding_box
            x1 = int(loc.xmin * w); y1 = int(loc.ymin * h)
            x2 = int((loc.xmin + loc.width) * w); y2 = int((loc.ymin + loc.height) * h)
            conf = float(det.score[0])
            outs.append((x1,y1,x2,y2,conf))
        return outs

def objective(img_clean, img_work):
    det = detect_faces_conf(img_work)
    if len(det)==0: return 0.0, 0.0, 0
    confs = [d[4] for d in det]
    score = (len(det) + np.mean(confs))
    return score, np.mean(confs), len(det)

def temporal_smooth(prev, cur, alpha=0.8):
    if prev is None: return cur
    return alpha*prev + (1-alpha)*cur

def spsa_update(base, work, step=1.0, eps=6):
    h,w,c = base.shape
    delta = np.random.choice([-1.0,1.0], size=(h,w,c)).astype(np.float32)
    x_plus  = np.clip(work.astype(np.float32)+delta, 0, 255).astype(np.uint8)
    x_minus = np.clip(work.astype(np.float32)-delta, 0, 255).astype(np.uint8)
    Lp,_,_ = objective(base, x_plus)
    Lm,_,_ = objective(base, x_minus)
    g = (Lp - Lm) / (2.0 + 1e-8) * delta
    g = g / (np.mean(np.abs(g))+1e-8)
    new = work.astype(np.float32) - step*g
    diff = new.astype(np.int32) - base.astype(np.int32)
    diff = np.clip(diff, -eps, eps).astype(np.int16)
    new = np.clip(base.astype(np.int32)+diff, 0, 255).astype(np.uint8)
    return new

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--eps", type=int, default=6)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--iters-per-key", type=int, default=10)
    ap.add_argument("--disp-th", type=float, default=12.0)
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened(): raise SystemExit("Cannot open input.")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    FPS = args.fps if args.fps>0 else cap.get(cv2.CAP_PROP_FPS)

    outv = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W,H))

    prev_face_centroid = None
    prev_W = None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT)>0 else None
    pbar = tqdm(total=total_frames, desc="VideoFacePoison")
    while True:
        ret, frame = cap.read()
        if not ret: break
        base = frame.copy()

        det = detect_faces_conf(base)
        if len(det)>0:
            x1,y1,x2,y2,_ = det[0]
            cx = 0.5*(x1+x2); cy = 0.5*(y1+y2)
            centroid = np.array([cx,cy], dtype=np.float32)
        else:
            centroid = None

        if prev_face_centroid is not None and centroid is not None:
            disp = np.linalg.norm(centroid - prev_face_centroid)
        else:
            disp = 1e9

        if prev_W is not None and disp < args.disp_th:
            work = np.clip(base.astype(np.float32)+prev_W, 0, 255).astype(np.uint8)
        else:
            work = base.copy()
            for _ in range(args.iters_per_key):
                for _s in range(args.steps):
                    work = spsa_update(base, work, step=1.0, eps=args.eps)

        prev_W = (work.astype(np.float32)-base.astype(np.float32))
        prev_W = np.clip(prev_W, -args.eps, args.eps)
        prev_face_centroid = centroid

        outv.write(work)
        if pbar: pbar.update(1)

    cap.release(); outv.release()
    if pbar: pbar.close()
    print("Saved:", args.output)

if __name__ == "__main__":
    if not MP_OK:
        print("[WARN] MediaPipe not found; please `pip install mediapipe`.")
    main()

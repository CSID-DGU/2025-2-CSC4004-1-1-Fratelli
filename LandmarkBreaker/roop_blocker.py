import os, cv2, argparse, numpy as np
import face_alignment
import torch

def to_uint8(x): return np.clip(x*255.0,0,255).astype(np.uint8)
def from_uint8(x): return x.astype(np.float32)/255.0

def largest_face(lms_list):
    if not lms_list: return None
    if len(lms_list)==1: return lms_list[0]
    def area(pts):
        x1,y1 = pts.min(axis=0); x2,y2 = pts.max(axis=0)
        return (x2-x1)*(y2-y1)
    sizes=[area(p) for p in lms_list]
    return lms_list[int(np.argmax(sizes))]

# 68점 인덱스 그룹(ibug 기준)
EYE_L = list(range(36,42))
EYE_R = list(range(42,48))
BROW_L = list(range(17,22))
BROW_R = list(range(22,27))
NOSE   = list(range(27,36))
JAW    = list(range(0,17))
MOUTH  = list(range(48,68))
FACE_HULL = JAW + BROW_L + BROW_R + [JAW[0]]

def poly_from_indices(pts, idxs):
    return np.array([pts[i] for i in idxs], dtype=np.int32)

def make_checker(H,W,cell=6,phase=0):
    yy,xx = np.mgrid[0:H,0:W]
    pat = (( (xx+phase)//cell + (yy+phase)//cell ) % 2).astype(np.float32)
    pat = (pat*2-1) # -1..1
    return pat

def apply_soft_noise(rgb, lms, strength=0.12, cell=6, eot_shift=(0,0)):
    H,W = rgb.shape[:2]
    pts = lms.reshape(-1,2).astype(np.int32)
    # 관심영역: 눈/눈썹/코 주변을 큰 폴리곤으로 묶음
    region_idx = sorted(set(EYE_L+EYE_R+BROW_L+BROW_R+NOSE))
    hull = cv2.convexHull(pts[region_idx]).reshape(-1,2)

    mask = np.zeros((H,W), np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)

    # 체크보드 + 위상 지터
    phase = np.random.randint(0,cell*2) + int(eot_shift[0])
    pat = make_checker(H,W,cell=cell,phase=phase)
    # 채널별 위상 살짝 다르게
    pat3 = np.stack([
        pat,
        make_checker(H,W,cell=cell,phase=phase+2),
        make_checker(H,W,cell=cell,phase=phase+4)
    ], axis=2)

    # 마스크 경계 부드럽게
    maskf = cv2.GaussianBlur(mask,(0,0),sigmaX=2,sigmaY=2).astype(np.float32)/255.0
    noise = pat3 * (strength) # [-s..s]
    out = np.clip(rgb + noise*maskf[:,:,None], 0.0, 1.0)
    return out

def apply_hard_blur(bgr, lms, blur_ks=31, mosaic=0):
    H,W = bgr.shape[:2]
    pts = lms.reshape(-1,2).astype(np.int32)
    hull = cv2.convexHull(pts).reshape(-1,2)
    mask = np.zeros((H,W), np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)
    face = cv2.bitwise_and(bgr,bgr,mask=mask)
    if mosaic>0:
        small = cv2.resize(face,(W//mosaic or 1, H//mosaic or 1), interpolation=cv2.INTER_LINEAR)
        face_blur = cv2.resize(small,(W,H), interpolation=cv2.INTER_NEAREST)
    else:
        face_blur = cv2.GaussianBlur(face,(blur_ks,blur_ks),0)
    inv = cv2.bitwise_and(bgr,bgr,mask=255-mask)
    return cv2.add(inv, face_blur)

def process_video(in_path, out_path, args, fa):
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open: {in_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*args.fourcc)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    wr = cv2.VideoWriter(out_path, fourcc, fps, (W,H))
    if not wr.isOpened():
        raise RuntimeError("VideoWriter open failed. Try --fourcc XVID and .avi")

    f=0
    while True:
        ok, frame = cap.read()
        if not ok: break
        # RGB float
        rgb01 = from_uint8(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        lms_list = fa.get_landmarks(to_uint8(rgb01))
        lms = largest_face(lms_list)
        if lms is None:
            out = frame
        else:
            if args.mode=="soft":
                # 프레임별 1~2px 이동/밝기 지터 (EOT)
                shift = (np.random.randint(-2,3), np.random.randint(-2,3))
                rgb01 = np.clip(rgb01*(1.0 + np.random.randn()*0.01), 0.0, 1.0)
                adv01 = apply_soft_noise(rgb01, lms, strength=args.strength, cell=args.cell, eot_shift=shift)
                out = cv2.cvtColor(to_uint8(adv01), cv2.COLOR_RGB2BGR)
            else:
                out = apply_hard_blur(frame, lms, blur_ks=args.blur, mosaic=args.mosaic)

        wr.write(out)
        if args.log_every>0 and (f%args.log_every==0):
            print(f"[ROOP-BLOCK] frame {f}")
        f+=1
    cap.release(); wr.release()
    print(f"[OK] saved: {out_path}")

def process_image(in_path, out_path, args, fa):
    bgr = cv2.imread(in_path, cv2.IMREAD_COLOR)
    if bgr is None: raise RuntimeError(f"Cannot open: {in_path}")
    rgb01 = from_uint8(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    lms_list = fa.get_landmarks(to_uint8(rgb01))
    lms = largest_face(lms_list)
    if lms is None:
        out = bgr
    else:
        if args.mode=="soft":
            rgb01 = np.clip(rgb01*(1.0 + np.random.randn()*0.01), 0.0, 1.0)
            adv01 = apply_soft_noise(rgb01, lms, strength=args.strength, cell=args.cell, eot_shift=(0,0))
            out = cv2.cvtColor(to_uint8(adv01), cv2.COLOR_RGB2BGR)
        else:
            out = apply_hard_blur(bgr, lms, blur_ks=args.blur, mosaic=args.mosaic)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cv2.imwrite(out_path, out)
    print(f"[OK] saved: {out_path}")

def resolve_landmarks_type_2d():
    # face_alignment 버전 호환 (_2D/TWO_D)
    try:
        LT = face_alignment.LandmarksType
        for n in ["_2D","TWO_D","TwoD","twoD","two_d"]:
            if hasattr(LT,n): return getattr(LT,n)
    except: pass
    for n in ["_2D","TWO_D"]:
        if hasattr(face_alignment,n): return getattr(face_alignment,n)
    return 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--mode", choices=["soft","hard"], default="soft")
    ap.add_argument("--strength", type=float, default=0.14, help="soft 노이즈 세기(권장 0.10~0.18)")
    ap.add_argument("--cell", type=int, default=6, help="체크보드 셀 크기(px)")
    ap.add_argument("--blur", type=int, default=31, help="hard 모드 가우시안 커널")
    ap.add_argument("--mosaic", type=int, default=0, help="hard 모자이크 강도(0이면 미사용)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--fourcc", default="mp4v")
    ap.add_argument("--log_every", type=int, default=30)
    ap.add_argument("--type", choices=["image","video"], default="video")
    args = ap.parse_args()

    if args.device=="cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA 강제 지정했지만 사용 불가. PyTorch CUDA/드라이버 확인 필요.")
    lmk2d = resolve_landmarks_type_2d()
    fa = face_alignment.FaceAlignment(lmk2d, device=args.device, face_detector="sfd")

    if args.type=="image":
        process_image(args.input, args.output, args, fa)
    else:
        process_video(args.input, args.output, args, fa)

if __name__=="__main__":
    main()

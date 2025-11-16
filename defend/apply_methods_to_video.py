#!/usr/bin/env python3
"""
apply_methods_to_video.py
- usage examples at bottom of this file (or run: python apply_methods_to_video.py -h)
- Requires: OpenCV, numpy, pywt, face_alignment, torch (for LandmarkBreaker), facenet-pytorch (optional for NullSwap/Face models)
- Uses your existing scripts:
    dwt_lowfreq_perturb.py -> function perturb_dwt_lowfreq(img, alpha, wave)
    landmarkbreaker_pgd.py -> function pgd_maximize_landmark(img, fa, eps, steps, alpha)
    nullswap_arcface_pgd.py  -> function pgd_cloak(img, models, eps, steps, alpha)
    leat_latent_ensemble_pgd.py -> function pgd_leat(x0, encoders, eps, steps, alpha)
    spsa_blackbox.py -> spsa_optimize (requires evaluate_image implement)
"""
import argparse, subprocess, shutil, os, sys, json, uuid
from pathlib import Path
import cv2, numpy as np
import itertools, tqdm

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
INPUT_VIDEO = INPUT_DIR / "short_test.mp4"
TMP_FRAMES = ROOT / f"frames_{uuid.uuid4().hex[:8]}"
TMP_PERT = ROOT / f"pert_{uuid.uuid4().hex[:8]}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_FRAMES.mkdir(parents=True, exist_ok=True)
TMP_PERT.mkdir(parents=True, exist_ok=True)

# import functions from uploaded modules (must be in same folder)
sys.path.append(str(ROOT))
from dwt_lowfreq_perturb import perturb_dwt_lowfreq
from landmarkbreaker_pgd import pgd_maximize_landmark
from nullswap_arcface_pgd import pgd_cloak, InceptionResnetV1
from leat_latent_ensemble_pgd import pgd_leat

# face_alignment single instance for LandmarkBreaker
import face_alignment
FA = face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, flip_input=False)

# NullSwap surrogate model (will try to load; if unavailable, NullSwap will fail)
try:
    from facenet_pytorch import InceptionResnetV1 as FNRes
    NS_MODEL = [FNRes(pretrained='vggface2').eval()]
except Exception as e:
    NS_MODEL = None
    print("WARNING: facenet_pytorch InceptionResnetV1 not available. NULL attack will fail unless you install facenet-pytorch.")

# LEAT: user must provide encoders; we provide a dummy encoder that returns spatial average (weak)
def dummy_encoder(x):
    # expects torch tensor [1,3,H,W], but pgd_leat uses such encoders - this dummy returns simple pooled vector
    import torch
    return torch.nn.functional.adaptive_avg_pool2d(x,1).view(1,-1)

# Helper: ffmpeg extract / combine
def ffmpeg_extract_frames(video_path, out_dir, fps=None):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if fps is None:
        cmd = ["ffmpeg", "-y", "-i", str(video_path), str(out_dir/"frame_%06d.png")]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vf", f"fps={fps}", str(out_dir/"frame_%06d.png")]
    subprocess.run(cmd, check=True)

def ffmpeg_combine_frames(frames_dir, orig_video, out_video, fps=None, crf=18, preset="medium"):
    if fps is None:
        cmd = ["ffmpeg","-y","-i", str(frames_dir/"frame_%06d.png"), "-i", str(orig_video),
               "-map","0:v","-map","1:a?","-c:v","libx264","-crf",str(crf),"-preset",preset,"-c:a","copy", str(out_video)]
    else:
        cmd = ["ffmpeg","-y","-r",str(fps),"-i", str(frames_dir/"frame_%06d.png"), "-i", str(orig_video),
               "-map","0:v","-map","1:a?","-c:v","libx264","-crf",str(crf),"-preset",preset,"-c:a","copy", str(out_video)]
    subprocess.run(cmd, check=True)

def list_frames(frames_dir):
    return sorted(frames_dir.glob("frame_*.png"))

def read_rgb(path):
    im = cv2.imread(str(path))[:,:,::-1].astype(np.float32)/255.0
    return im

def write_rgb(path, rgb):
    path.parent.mkdir(parents=True, exist_ok=True)
    bgr = (np.clip(rgb,0,1)*255).astype('uint8')[:,:,::-1]
    cv2.imwrite(str(path), bgr)

# Attack wrappers: each takes numpy rgb float[0,1] and returns same shape
def attack_dwt(img, params):
    return perturb_dwt_lowfreq(img, alpha=params.get("alpha",0.02), wave=params.get("wave","haar"))

def attack_lmb(img, params):
    # pgd_maximize_landmark(img, fa, eps=..., steps=..., alpha=..., mask_face=True)
    return pgd_maximize_landmark(img, FA, eps=params.get("eps_px",16)/255.0, steps=params.get("steps",20), alpha=params.get("alpha_px",1.0)/255.0)

####

try:
    from facenet_pytorch import InceptionResnetV1 as FNRes
    import torch
    NULL_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    NS_TORCH = FNRes(pretrained='vggface2').eval().to(NULL_DEVICE)
    NS_AVAILABLE = True
    print("[NULL] facenet_pytorch loaded on", NULL_DEVICE)
except Exception as e:
    NS_TORCH = None
    NS_AVAILABLE = False
    print("[NULL][WARN] facenet_pytorch unavailable:", e)

def _to_facenet_tensor(rgb_np):
    """rgb_np: HxWx3 float[0,1] -> torch [1,3,160,160] float in [-1,1] (facenet_pytorch 규약)"""
    import torch, cv2
    H, W = rgb_np.shape[:2]
    # facenet은 160x160 정규화 입력 기대. 간단 resize (정교하게 하려면 얼굴탐지/얼라인 추가)
    img = (rgb_np * 255.0).astype(np.uint8)
    img = cv2.resize(img[:,:,::-1], (160,160))[:,:,::-1]  # keep RGB
    t = torch.from_numpy(img.transpose(2,0,1)).float() / 255.0
    t = (t - 0.5) / 0.5     # [-1,1]
    return t.unsqueeze(0).to(NULL_DEVICE)

def _cosine(a,b,eps=1e-8):
    import torch
    na = a.norm(dim=1, keepdim=True) + eps
    nb = b.norm(dim=1, keepdim=True) + eps
    return (a*b).sum(dim=1, keepdim=True) / (na*nb)

def attack_null(img, params):
    """임베딩 자기-유사도 cos(model(x_adv), model(x_clean))를 최소화하는 PGD."""
    if not NS_AVAILABLE or NS_TORCH is None:
        print("[NULL][WARN] model not available. Passing frame unchanged.")
        return img

    import torch
    steps = params.get("steps", 30)
    eps_px = params.get("eps_px", 8)           # 0~255 스케일
    eps    = eps_px / 255.0                    # [0,1]
    alpha  = max(eps / max(1, steps//2), 1/255.0)  # conservative step

    x_clean = _to_facenet_tensor(img).detach()
    with torch.no_grad():
        emb_clean = NS_TORCH(x_clean)

    # x_adv는 원해상도에서 직접 최적화(간단화 버전: facenet 입력만 resize 후 grad)
    # 실전에서는 원본 해상도에서 perturb → facenet 입력으로 다운샘플/정규화
    x_adv = torch.tensor(img.transpose(2,0,1)[None]).float().to(NULL_DEVICE)
    x0 = x_adv.clone().detach()
    x_adv.requires_grad_(True)

    for _ in range(steps):
        # facenet 입력으로 맞추기
        x_adv_input = torch.nn.functional.interpolate(x_adv, size=(160,160), mode='bilinear', align_corners=False)
        x_adv_input = (x_adv_input - 0.5) / 0.5  # [-1,1]
        emb_adv = NS_TORCH(x_adv_input)

        # cos 유사도 최소화 (self-cloaking)
        cos_sim = _cosine(emb_adv, emb_clean).mean()
        loss = cos_sim  # minimize
        loss.backward()

        with torch.no_grad():
            x_adv = x_adv - alpha * x_adv.grad.sign()
            x_adv = torch.max(torch.min(x_adv, x0 + eps), x0 - eps)
            x_adv = torch.clamp(x_adv, 0.0, 1.0)
        x_adv.requires_grad_(True)

    out = x_adv.detach().cpu().numpy()[0].transpose(1,2,0)
    return np.clip(out, 0, 1)

#####


#####
def attack_leat(img, params):
    # LEAT은 GPU 커널/엔진 문제를 피하기 위해 CPU 강제 + grad 보장
    import torch
    device = torch.device("cpu")  # 안정성 우선. GPU 쓰려면 "cuda"로 바꿔보되 FIND 에러 나면 다시 cpu 권장.
    x0 = torch.tensor(img.transpose(2,0,1)[None]).float().to(device)
    x0.requires_grad_(True)

    # 더미 인코더(순수 torch op만 사용)
    def dummy_encoder(x):
        return torch.nn.functional.adaptive_avg_pool2d(x, 1).view(x.shape[0], -1)

    encs = [dummy_encoder]
    steps = params.get("steps", 30)
    eps   = params.get("eps", 0.05)      # L_inf in [0,1]
    alpha = params.get("alpha", 0.01)    # step size

    # 간단 PGD: 인코더 피처 L2-노름을 최대화(=특징 불안정화) -> 교란 유도
    x = x0.clone().detach().requires_grad_(True)
    for _ in range(steps):
        feats = [e(x) for e in encs]
        loss = sum([(f**2).sum() for f in feats])  # 특징 에너지 ↑
        (-loss).backward()  # maximize => minimize(-loss)

        with torch.no_grad():
            x = x + alpha * x.grad.sign()
            x = torch.max(torch.min(x, x0 + eps), x0 - eps)  # L_inf 프로젝션
            x = torch.clamp(x, 0.0, 1.0)
        x.requires_grad_(True)

    out = x.detach().cpu().numpy()[0].transpose(1,2,0)
    return np.clip(out, 0, 1)

METHOD_FUNCS = {
    "DWT": (attack_dwt, [{"alpha":0.02,"wave":"haar"}, {"alpha":0.015,"wave":"haar"}]),
    "LMB": (attack_lmb, [{"eps_px":12,"steps":15,"alpha_px":1.0}, {"eps_px":16,"steps":20,"alpha_px":1.0}]),
    "NULL": (attack_null, [{"eps_px":8,"steps":30}, {"eps_px":10,"steps":40}]),
    "LEAT": (attack_leat, [{"eps":0.05,"steps":30,"alpha":0.01}]),
    # "SPSA": handled separately if evaluate_image is provided
}
####

def apply_chain(frames, chain, param_combo, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, fp in enumerate(tqdm.tqdm(frames, desc=f"Applying {chain}")):
        rgb = read_rgb(fp)
        out = rgb.copy()
        for name, params in zip(chain, param_combo):
            fn, _ = METHOD_FUNCS[name]
            out = fn(out, params)
        write_rgb(out_dir/fp.name, out)

def generate_chains(methods, max_len):
    chains = []
    for L in range(1, max_len+1):
        for prod in itertools.product(methods, repeat=L):
            chains.append(list(prod))
    return chains

def generate_param_grid(chain):
    grids = [METHOD_FUNCS[name][1] for name in chain]
    combos = list(itertools.product(*grids))
    return [list(c) for c in combos]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(INPUT_VIDEO))
    parser.add_argument("--outputs", default=str(OUTPUT_DIR))
    parser.add_argument("--fps", type=int, default=None)
    parser.add_argument("--max_chain_len", type=int, default=2)
    parser.add_argument("--sample_every", type=int, default=1, help="프레임 샘플링 간격 (1=모두)")
    args = parser.parse_args()

    in_vid = Path(args.input)
    out_root = Path(args.outputs)
    out_root.mkdir(parents=True, exist_ok=True)

    print("Extracting frames...")
    ffmpeg_extract_frames(in_vid, TMP_FRAMES, fps=args.fps)
    frames = list_frames(TMP_FRAMES)
    if args.sample_every > 1:
        frames = [f for i,f in enumerate(frames) if i % args.sample_every == 0]

    methods = list(METHOD_FUNCS.keys())
    chains = generate_chains(methods, args.max_chain_len)
    print(f"Will run {len(chains)} chains (max_len={args.max_chain_len}) on {len(frames)} frames each.")

    for chain in chains:
        param_grid = generate_param_grid(chain)
        for params in param_grid:
            chain_name = "-".join(chain)
            ptag = "__".join("_".join(f"{k}{str(v).replace('.','p')}" for k,v in sorted(p.items())) for p in params)
            run_id = f"{chain_name}__{ptag}"
            out_frames_dir = TMP_PERT / run_id
            try:
                print(f"\n--- Running {run_id} ---")
                apply_chain(frames, chain, params, out_frames_dir)
                out_video = out_root / f"{run_id}.mp4"
                ffmpeg_combine_frames(out_frames_dir, in_vid, out_video, fps=args.fps)
                meta = {"chain":chain, "params":params, "input":str(in_vid), "output":str(out_video)}
                with open(out_root/(run_id+".json"), "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                print(f"Saved {out_video}")
            except Exception as e:
                print(f"ERROR during {run_id}: {e}")
    # cleanup
    print("Cleaning temporary directories...")
    shutil.rmtree(TMP_FRAMES, ignore_errors=True)
    shutil.rmtree(TMP_PERT, ignore_errors=True)
    print("All done.")

if __name__ == "__main__":
    main()

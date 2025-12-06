import os
import cv2
import json
import argparse
import random
import torch
from PIL import Image
from torchvision import transforms
import torchvision.utils as vutils


def load_args():
    with open('./setting.json', 'r') as f:
        cfg = json.load(f)
    class Obj(dict):
        __getattr__ = dict.get
    return Obj(cfg)


def get_transform(size):
    return transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5)),
    ])



def apply_perturbation(img_path, out_path, up, size, eps_scale):
    tf = get_transform(size)
    img = Image.open(img_path).convert("RGB")
    img_t = tf(img).unsqueeze(0)

    # ε 적용 코드: protected = img + eps_scale * up
    protected = img_t + eps_scale * up
    protected = torch.clamp(protected, -1, 1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    vutils.save_image(protected, out_path, normalize=True, range=(-1.,1.))


def is_video(path):
    ext = path.lower().split('.')[-1]
    return ext in ['mp4','avi','mov','mkv']


def process_video(path, output, up, size, eps_scale):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_dir = './tmp_frames'
    out_dir = './tmp_frames_protected'
    os.makedirs(frame_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # 프레임 추출
    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = f"{frame_dir}/{idx:06d}.png"
        cv2.imwrite(frame_path, frame)
        frames.append(frame_path)
        idx += 1
    cap.release()

    # 평가용 랜덤 프레임 선택
    sample_idx = random.randint(0, len(frames)-1)

    # 보호 적용
    for i, f_path in enumerate(frames):
        out_path = f"{out_dir}/{i:06d}.png"
        apply_perturbation(f_path, out_path, up, size, eps_scale)

        if i == sample_idx:
            os.system(f"cp {f_path} ./sample_original_frame.png")
            os.system(f"cp {out_path} ./sample_protected_frame.png")

    # 보호된 프레임 → 영상 합치기
    h, w = cv2.imread(f"{out_dir}/000000.png").shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output, fourcc, fps, (w,h))

    for i in range(len(frames)):
        frame = cv2.imread(f"{out_dir}/{i:06d}.png")
        writer.write(frame)

    writer.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)

    parser.add_argument('--eps', type=float, default=1.0,
                        help="strength scale for CMUA perturbation (1.0 = original strength)")
    args = parser.parse_args()

    cfg = load_args()
    up_path = cfg['global_settings']['universal_perturbation_path']
    size = cfg['global_settings']['img_size']

    # perturbation 로드
    up = torch.load(up_path, map_location='cpu')
    if up.dim() == 4:
        up = up[0]

    print(f"[+] Loaded perturbation: {up_path}")
    print(f"[+] Using eps scale = {args.eps}")

    # 타입 판별
    if not is_video(args.input):
        print("[*] Image detected → protecting…")
        apply_perturbation(args.input, args.output, up, size, args.eps)
        print(f"[+] Saved protected image → {args.output}")
    else:
        print("[*] Video detected → processing frames…")
        process_video(args.input, args.output, up, size, args.eps)
        print(f"[+] Saved protected video → {args.output}")
        print("[+] Sample frames saved: sample_original_frame.png / sample_protected_frame.png")


if __name__ == '__main__':
    main()

    

import os
import cv2
import torch
import argparse
import numpy as np
from tqdm import tqdm
from PIL import Image
from pathlib import Path
import sys
"""
from defend_stargan_pg import (
    Attackmodel,
    load_pg,
    defend_image_tensor,
    build_transform,
    tensor_to_pil
)
"""
"""
영상 전체에 Initiative Defense(AAAI 2021) 노이즈를 적용하는 스크립트.
- 입력 영상의 원본 해상도를 유지.
- 각 프레임을 PG 입력 크기(128/256)에 맞춰 resize하여 노이즈 생성 후,
  다시 원본 해상도로 resize하여 영상에 적용.

[원래 사용 예 - 참고용]

conda activate fomm-gpu
cd ../defense
python defend_video_pg_fin.py \
  --input ../input/bp_178.mp4 \
  --output ../output/bp_178_defended.mp4 \
  --ckpt ../downloads/30000-PG-005.ckpt \
  --eps 0.25\
  --image_size 128 \
  --blend_alpha 0.6 \
  --device cuda

conda activate init_df
cd ../stargan
python main.py \
  --mode test \
  --dataset CelebA \
  --image_size 128 \
  --c_dim 5 \
  --batch_size 1 \
  --selected_attrs Black_Hair Blond_Hair Brown_Hair Male Young \
  --model_save_dir stargan_celeba_128/models \
  --result_dir stargan_celeba_128/results \
  --sample_dir stargan_celeba_128/samples \
  --log_dir stargan_celeba_128/logs
"""


import torch.nn.functional as F


import argparse
import os

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
import numpy as np


# -----------------------------
# 1) Attackmodel (= Perturbation Generator)
#    -> GitHub model.py의 Attackmodel 정의를 그대로 가져온 것
# -----------------------------

def double_conv(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, 3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),

        nn.Conv2d(out_channels, out_channels, 3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True)
    )


class Attackmodel(nn.Module):
    """Backbone of Perturbation Generator (U-Net style)."""

    def __init__(self, out_channel=3):
        super(Attackmodel, self).__init__()

        self.dconv_down1 = double_conv(3, 64)
        self.dconv_down2 = double_conv(64, 128)
        self.dconv_down3 = double_conv(128, 256)
        self.dconv_down4 = double_conv(256, 512)
        self.dconv_down5 = double_conv(512, 1024)

        self.maxpool = nn.AvgPool2d(2)
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear',
                                    align_corners=True)

        self.dconv_up4 = double_conv(512 + 1024, 512)
        self.dconv_up3 = double_conv(256 + 512, 256)
        self.dconv_up2 = double_conv(128 + 256, 128)
        self.dconv_up1 = double_conv(128 + 64, 64)

        self.conv_last = nn.Sequential(
            nn.Conv2d(64, out_channel, 1),
            nn.BatchNorm2d(out_channel),
        )

    def forward(self, x):
        # Encoder
        conv1 = self.dconv_down1(x)
        x = self.maxpool(conv1)

        conv2 = self.dconv_down2(x)
        x = self.maxpool(conv2)

        conv3 = self.dconv_down3(x)
        x = self.maxpool(conv3)

        conv4 = self.dconv_down4(x)
        x = self.maxpool(conv4)

        x = self.dconv_down5(x)

        # Decoder with skip connections
        x = self.upsample(x)
        x = torch.cat([x, conv4], dim=1)
        x = self.dconv_up4(x)

        x = self.upsample(x)
        x = torch.cat([x, conv3], dim=1)
        x = self.dconv_up3(x)

        x = self.upsample(x)
        x = torch.cat([x, conv2], dim=1)
        x = self.dconv_up2(x)

        x = self.upsample(x)
        x = torch.cat([x, conv1], dim=1)
        x = self.dconv_up1(x)

        out = self.conv_last(x)
        out = torch.tanh(out)  # [-1, 1] 범위
        return out


# -----------------------------
# 2) PG 로더 유틸
# -----------------------------

def load_pg(ckpt_path: str, device: torch.device) -> Attackmodel:
    """
    Perturbation Generator(Attackmodel) 가중치를 로드한다.

    ckpt 포맷이 아래 경우들을 모두 커버하도록 작성:
    - torch.save(PG.state_dict())
    - torch.save({'PG': PG.state_dict(), ...})
    - torch.save({'model': PG.state_dict(), ...})
    """

    model = Attackmodel(out_channel=3).to(device)
    model.eval()

    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location=device)

    # 다양한 저장 포맷에 대응
    if isinstance(ckpt, dict):
        if 'PG' in ckpt:
            state_dict = ckpt['PG']
        elif 'model' in ckpt:
            state_dict = ckpt['model']
        elif 'state_dict' in ckpt:
            state_dict = ckpt['state_dict']
        else:
            # 그냥 state_dict로 저장된 경우
            state_dict = ckpt
    else:
        state_dict = ckpt

    # key mismatch를 줄이기 위해 strict=False
    model.load_state_dict(state_dict, strict=False)
    return model


# -----------------------------
# 3) 이미지 전처리 / 후처리
# -----------------------------

def build_transform(image_size: int = 128):
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.5, 0.5, 0.5),
                             std=(0.5, 0.5, 0.5)),
    ])


def tensor_to_pil(x: torch.Tensor) -> Image.Image:
    """
    [-1,1] 텐서 → [0,255] uint8 → PIL Image
    x: (1, 3, H, W)
    """
    x = x.detach().cpu().clone()
    x = (x + 1.0) / 2.0  # [0,1]
    x = torch.clamp(x, 0.0, 1.0)

    x = x.squeeze(0)  # (3,H,W)
    x = x.permute(1, 2, 0).numpy()  # (H,W,3)
    x = (x * 255.0).round().astype(np.uint8)

    return Image.fromarray(x)


# -----------------------------
# 4) 핵심 함수: defend_image_tensor
# -----------------------------

@torch.no_grad()
def defend_image_tensor(x: torch.Tensor,
                        pg: Attackmodel,
                        eps: float,
                        device: torch.device) -> torch.Tensor:
    """
    x       : (1,3,H,W), [-1,1] 범위
    eps     : PG 출력(tanh) 스케일 (ex. 0.03, 0.05 등)
    return  : x_adv, (1,3,H,W), [-1,1]
    """
    x = x.to(device)
    pg = pg.to(device)

    noise = pg(x)            # [-1,1]
    x_adv = x + eps * noise  # [-1-eps, 1+eps] 이지만 곧 clamp
    x_adv = torch.clamp(x_adv, -1.0, 1.0)

    return x_adv


# -----------------------------
# 5) 단일 이미지 처리 함수
# -----------------------------


def defend_single_image(input_path: str,
                        output_path: str,
                        ckpt_path: str,
                        eps: float = 0.15,
                        image_size: int = 128,
                        device_str: str = "cuda"):

    device = torch.device(device_str if torch.cuda.is_available()
                          and device_str.startswith("cuda")
                          else "cpu")

    # 1) PG 로드
    pg = load_pg(ckpt_path, device)
    pg.eval()

    # 2) 이미지 로드 & 전처리
    transform = build_transform(image_size)
    img = Image.open(input_path).convert("RGB")
    x = transform(img).unsqueeze(0)  # (1,3,H,W)

    # 3) 방어 노이즈 추가
    x_adv = defend_image_tensor(x, pg, eps, device)

    # 4) 저장
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_img = tensor_to_pil(x_adv)
    out_img.save(output_path)
    print(f"[INFO] Saved defended image to: {output_path}")


# -----------------------------
# 6) CLI: 단일/배치 통합
# -----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Initiative Defense: add protective noise to face image(s) "
                    "for StarGAN/FOMM source defense."
    )
    parser.add_argument(
        "-i", "--input", type=str, required=True,
        help="입력 경로: 단일 이미지 파일 또는 폴더"
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True,
        help="출력 경로: 파일 또는 폴더"
    )
    parser.add_argument(
        "--ckpt", type=str, required=True,
        help="PG(Attackmodel) 체크포인트 경로"
    )
    parser.add_argument(
        "--eps", type=float, default=0.03,
        help="L_inf 스케일 (PG 출력 스케일링). 기본값=0.03"
    )
    parser.add_argument(
        "--image_size", type=int, default=128,
        help="이미지 해상도 (StarGAN-128 기준). 기본값=128"
    )
    parser.add_argument(
        "--device", type=str, default="cuda",
        help="'cuda' 또는 'cpu'. 기본값='cuda'"
    )
    args = parser.parse_args()

    in_path = args.input
    out_path = args.output

    # 1) 입력이 폴더인지 여부로 단일/배치 자동 분기
    if os.path.isdir(in_path):
        # ---------- 폴더 배치 모드 ----------
        in_dir = in_path
        out_dir = out_path

        os.makedirs(out_dir, exist_ok=True)

        files = sorted(os.listdir(in_dir))
        for fname in files:
            if not fname.lower().endswith((".jpg", ".png", ".jpeg")):
                continue

            src = os.path.join(in_dir, fname)

            # "000001.jpg" → "000001_n.jpg"
            base, ext = os.path.splitext(fname)
            dst_name = f"{base}_n{ext}"
            dst = os.path.join(out_dir, dst_name)

            print(f"[INFO] Defending {fname} → {dst_name}")

            defend_single_image(
                input_path=src,
                output_path=dst,
                ckpt_path=args.ckpt,
                eps=args.eps,
                image_size=args.image_size,
                device_str=args.device
            )

        print("[INFO] All images defended successfully!")

    else:
        # ---------- 단일 파일 모드 ----------
        # 출력이 폴더이면: 입력 파일 이름 + '_n' 붙여서 저장
        if os.path.isdir(out_path):
            base_name = os.path.basename(in_path)
            base, ext = os.path.splitext(base_name)
            dst_name = f"{base}_n{ext}"
            dst = os.path.join(out_path, dst_name)
        else:
            # 출력이 파일 경로이면 그대로 사용
            dst = out_path

        defend_single_image(
            input_path=in_path,
            output_path=dst,
            ckpt_path=args.ckpt,
            eps=args.eps,
            image_size=args.image_size,
            device_str=args.device
        )







# 제출용 고정 실행 명령어 (요구사항 2)
FIXED_CMD = r"""
python defend_video_pg_fin.py \
  --input ./input/bp.mp4 \
  --output ./output/protected.mp4 \
  --ckpt ./models/30000-PG-005.ckpt \
  --eps 0.15\
  --image_size 128 \
  --blend_alpha 0.6 \
  --device cuda
"""

# proj 루트 기준으로 StarGAN 이미지 디렉토리 설정 (원본 기능 유지)
PROJ_ROOT = Path(__file__).resolve().parents[1]
STARGAN_IMAGE_DIR = PROJ_ROOT / "stargan" / "data" / "celeba" / "images"


def frame_to_tensor(frame_bgr, image_size):
    """BGR → RGB PIL → PG transform 텐서로 변환"""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)
    transform = build_transform(image_size)
    tensor = transform(pil_img).unsqueeze(0)  # (1,3,H,W)
    return tensor


def tensor_to_frame(orig_frame_bgr, tensor):
    """PG 출력 텐서를 원본 영상 해상도에 resize하여 BGR 프레임으로 변환"""
    pil_img = tensor_to_pil(tensor)  # PG 출력 해상도
    out_rgb = np.array(pil_img)

    # 다시 원본 해상도(H,W)으로 resize
    h, w = orig_frame_bgr.shape[:2]
    out_rgb = cv2.resize(out_rgb, (w, h), interpolation=cv2.INTER_LINEAR)

    # RGB → BGR
    out_bgr = cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR)
    return out_bgr


def defend_video(input_path, output_path, ckpt_path,
                 eps=0.05, image_size=128, blend_alpha=1.0, device="cuda"):

    # GPU/CPU 설정
    device = torch.device(device if torch.cuda.is_available() else "cpu")

    # 1) PG 로드
    pg = load_pg(ckpt_path, device)
    pg.eval()

    # 2) 비디오 열기
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 출력 디렉토리 생성
    out_dir = os.path.dirname(output_path)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # 랜덤 프레임 하나 선택
    if frame_count > 0:
        target_idx = np.random.randint(0, frame_count)
    else:
        target_idx = 0
    random_frame_saved = False

    # 랜덤 프레임 이미지 저장 경로 (output 쪽)
    base, _ = os.path.splitext(output_path)
    rand_def_path = base + "_debug_def.png"
    rand_clean_path = base + "_debug_clean.png"

    debug_jpg_path = os.path.join(out_dir, "debugging_image.png")

    """
    # debugging_image.jpg (요구사항 4) - mp4 처리 시에만 생성
    debug_jpg_path = os.path.join(out_dir if out_dir != "" else ".", "debugging_image.jpg")
    """
    print(f"[INFO] Start defending video: {input_path}")
    print(f"       Resolution: {w}x{h}, FPS: {fps}, Frames: {frame_count}")
    print(f"       eps={eps}, blend_alpha={blend_alpha}")
    print(f"       Random defended frame will be saved to: {rand_def_path}")
    print(f"       Random clean   frame will be saved to: {rand_clean_path}")
    print(f"       Debugging image (video only): {debug_jpg_path}")
    print(f"       StarGAN images dir: {STARGAN_IMAGE_DIR} (000001.jpg, 000001_n.jpg)")

    frame_idx = 0

    # 3) 프레임 반복
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # (A) PG 입력용 Resized tensor 준비
        x = frame_to_tensor(frame, image_size)

        # (B) PG로 방어 노이즈 생성
        with torch.no_grad():
            x_adv = defend_image_tensor(x, pg, eps, device)

        # (C) 다시 원본 영상 해상도로 resize
        defended_frame_pg = tensor_to_frame(frame, x_adv)

        # (D) 원본과 defended를 blend_alpha 비율로 블렌딩 (최종 프레임)
        if blend_alpha is not None and 0.0 <= blend_alpha < 1.0:
            blended = (
                blend_alpha * defended_frame_pg.astype(np.float32)
                + (1.0 - blend_alpha) * frame.astype(np.float32)
            )
            blended = np.clip(blended, 0, 255).astype(np.uint8)
        else:
            blended = defended_frame_pg

        # 비디오에 쓰는 것은 blended 프레임
        writer.write(blended)
        
        # (E) 무작위로 선택한 프레임 한 장을 이미지로 저장
        if (not random_frame_saved) and (frame_idx == target_idx):
            # 1) output 디렉토리에 clean / defended 한 장씩 저장
            cv2.imwrite(rand_clean_path, frame)    # 원본
            cv2.imwrite(rand_def_path, blended)    # 방어/블렌딩 된 버전

            # 2) StarGAN용 이미지 저장 (000001.jpg / 000001_n.jpg)
#            STARGAN_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
#            stargan_orig_path = STARGAN_IMAGE_DIR / "000001.jpg"
#            stargan_def_path  = STARGAN_IMAGE_DIR / "000001_n.jpg"

#            cv2.imwrite(str(stargan_orig_path), frame)   # 원본
#            cv2.imwrite(str(stargan_def_path), blended)  # 방어/블렌딩 된 프레임

            # 3) 제출용 debugging 이미지(jpg)도 같이 저장
            cv2.imwrite(debug_jpg_path, blended)

            print(f"[INFO] Saved random clean   frame #{frame_idx} to: {rand_clean_path}")
            print(f"[INFO] Saved random defended frame #{frame_idx} to: {rand_def_path}")
#            print(f"[INFO] Saved StarGAN images to: {stargan_orig_path}, {stargan_def_path}")
            print(f"[INFO] Saved debugging image to: {debug_jpg_path}")

            random_frame_saved = True

        frame_idx += 1

    cap.release()
    writer.release()
    print(f"[INFO] Defended video saved to: {output_path}")
    if random_frame_saved:
        print(f"[INFO] Random frames & StarGAN images saved.")
    else:
        print("[WARN] Random frame was not saved (video may be empty).")


# ==== 새로 추가: 이미지 한 장 방어용 (백엔드/분기용) ====
def defend_image(input_path, output_path, ckpt_path,
                 eps=0.25, image_size=128, device="cuda"):

    device = torch.device(device if torch.cuda.is_available() else "cpu")

    # PG 로드 (영상과 동일한 방식)
    pg = load_pg(ckpt_path, device)
    pg.eval()

    img = cv2.imread(input_path)
    if img is None:
        raise RuntimeError(f"Failed to open image: {input_path}")

    x = frame_to_tensor(img, image_size)

    with torch.no_grad():
        x_adv = defend_image_tensor(x, pg, eps, device)

    defended_img = tensor_to_frame(img, x_adv)

    out_dir = os.path.dirname(output_path)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)

    cv2.imwrite(output_path, defended_img)
    print(f"[INFO] Defended image saved to: {output_path}")

def parse_args():
    parser = argparse.ArgumentParser()

    # 수동 실행 시에만 사용되는 옵션들
    parser.add_argument("--input", type=str, default="./input/bp.mp4")
    parser.add_argument("--output", type=str, default="./output/protected.mp4")

    # ⚠ 제출용: 가중치 경로를 ./model 아래로 고정하는 쪽이 자연스러워서 이렇게 맞춤
    #  /submit
    #   ├─ defend_stargan.py
    #   ├─ /model/30000-PG-005.ckpt
    parser.add_argument("--ckpt", type=str, default="./model/30000-PG-005.ckpt")

    parser.add_argument("--eps", type=float, default=0.25)
    ### 가중치 수정
    parser.add_argument("--image_size", type=int, default=128)
    parser.add_argument("--blend_alpha", type=float, default=0.6)
    parser.add_argument("--device", type=str, default="cuda")

    return parser.parse_args()


# -----------------------------
# 8) 자동 실행용 헬퍼 (인자 없이 실행할 때)
# -----------------------------
DEFAULT_CKPT = "./models/30000-PG-005.ckpt"
DEFAULT_INPUT_DIR = "./input"
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_VIDEO_OUT = os.path.join(DEFAULT_OUTPUT_DIR, "protected.mp4")
DEFAULT_IMAGE_OUT = os.path.join(DEFAULT_OUTPUT_DIR, "protected.png")


def auto_run():
    """
    python defend_stargan.py  만 실행했을 때:
    - ./input 폴더에서 파일을 찾아서
      1) 영상(.mp4/.avi/.mov/.mkv)이 있으면 → 그 중 하나 선택해서 방어
      2) 없고 이미지(.jpg/.png/.jpeg)만 있으면 → 그 중 하나 선택해서 방어
    - 가중치는 DEFAULT_CKPT 에서 자동 로드
    """
    print("[AUTO] 인자 없이 실행됨 → 자동 모드로 동작합니다.")

    # 1) input 폴더 확인
    if not os.path.isdir(DEFAULT_INPUT_DIR):
        print(f"[ERROR] 입력 폴더가 없습니다: {DEFAULT_INPUT_DIR}")
        print("        /submit 구조 예시:")
        print("        /submit")
        print("          ├─ defend_stargan.py")
        print("          ├─ /model/30000-PG-005.ckpt")
        print("          └─ /input/bp.mp4 또는 bp.jpg")
        return

    files = sorted(os.listdir(DEFAULT_INPUT_DIR))
    if not files:
        print(f"[ERROR] {DEFAULT_INPUT_DIR} 폴더 안에 파일이 없습니다.")
        return

    video_exts = [".mp4", ".avi", ".mov", ".mkv"]
    image_exts = [".jpg", ".jpeg", ".png", ".bmp"]

    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_exts]
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_exts]

    # 2) 어떤 파일을 쓸지 결정 (영상 우선)
    if video_files:
        fname = video_files[0]
        in_path = os.path.join(DEFAULT_INPUT_DIR, fname)
        is_video = True
        print(f"[AUTO] 영상 파일 선택: {fname}")
    elif image_files:
        fname = image_files[0]
        in_path = os.path.join(DEFAULT_INPUT_DIR, fname)
        is_video = False
        print(f"[AUTO] 이미지 파일 선택: {fname}")
    else:
        print(f"[ERROR] {DEFAULT_INPUT_DIR} 안에 사용 가능한 영상/이미지 파일이 없습니다.")
        return

    # 3) ckpt 경로 확인
    ckpt_path = DEFAULT_CKPT
    if not os.path.exists(ckpt_path):
        print(f"[ERROR] 가중치 파일을 찾을 수 없습니다: {ckpt_path}")
        print("        경로를 확인하거나 파일명을 맞춰 주세요.")
        return

    # 4) output 폴더 생성
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

    # 5) 실제 방어 수행
    if is_video:
        print(f"[AUTO] 영상 방어 시작 → {DEFAULT_VIDEO_OUT}")
        defend_video(
            input_path=in_path,
            output_path=DEFAULT_VIDEO_OUT,
            ckpt_path=ckpt_path,
            eps=0.10, 
            ### 여기서 가중치 세기 수정.
            image_size=128,
            blend_alpha=0.6,
            device="cuda",
        )
    else:
        print(f"[AUTO] 이미지 방어 시작 → {DEFAULT_IMAGE_OUT}")
        defend_image(
            input_path=in_path,
            output_path=DEFAULT_IMAGE_OUT,
            ckpt_path=ckpt_path,
            eps=0.10,
            image_size=128,
            device="cuda",
        )

    print("[AUTO] 완료!")


# -----------------------------
# 9) 엔트리 포인트
# -----------------------------
if __name__ == "__main__":
    # 인자가 하나도 없으면 (sys.argv == ['defend_stargan.py']) → 자동 모드
    if len(sys.argv) == 1:
        auto_run()
    else:
        # 수동 모드: 기존처럼 인자 파싱해서 사용
        args = parse_args()

        # 파일 확장자로 이미지 / 영상 자동 분기
        ext = os.path.splitext(args.input)[1].lower()
        video_exts = [".mp4", ".avi", ".mov", ".mkv"]

        if ext in video_exts:
            defend_video(
                input_path=args.input,
                output_path=args.output,
                ckpt_path=args.ckpt,
                eps=args.eps,
                image_size=args.image_size,
                blend_alpha=args.blend_alpha,
                device=args.device,
            )
        else:
            # 이미지일 경우 output을 protected.jpg로 강제
            out_dir = os.path.dirname(args.output) or "./output"
            os.makedirs(out_dir, exist_ok=True)
            image_out = os.path.join(out_dir, "protected.png")

            defend_image(
                input_path=args.input,
                output_path=image_out,
                ckpt_path=args.ckpt,
                eps=args.eps,
                image_size=args.image_size,
                device=args.device,
            )

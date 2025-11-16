import cv2
import torch
from facenet_pytorch import MTCNN
import pandas as pd
from PIL import Image
import os


def _expand_box(x1, y1, x2, y2, W, H, margin=0.35):
    """
    얼굴 박스를 머리카락까지 포함하도록 위쪽으로 더 확장.
    margin: 전체 크기 확장 비율
    """
    w, h = x2 - x1, y2 - y1
    cx, cy = x1 + w / 2, y1 + h / 2

    # 전체 박스 크기를 늘리되 위쪽으로 조금 더 확장 (머리 포함)
    top_margin = margin * 1.8
    bottom_margin = margin * 0.8
    new_h = h * (1.0 + top_margin + bottom_margin)
    new_w = w * (1.0 + margin * 2)

    nx1 = int(max(0, cx - new_w / 2))
    ny1 = int(max(0, cy - h * (0.5 + top_margin)))
    nx2 = int(min(W, cx + new_w / 2))
    ny2 = int(min(H, ny1 + new_h))
    return nx1, ny1, nx2, ny2


def extract_frames(video_path, output_dir="frame_split"):
    """비디오 프레임 추출"""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(f"{output_dir}/{idx:06d}.jpg", frame)
        idx += 1
    cap.release()
    print(f"[OK] 총 {idx}개의 프레임 추출 완료 → {output_dir}/")


def process_video(video_path, output_csv="face_boxes.csv", margin=0.35, output_faces="face_crops"):
    """
    얼굴 추적 → 얼굴 부분 crop 저장 → CSV 저장
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Device: {device}")
    mtcnn = MTCNN(keep_all=True, device=device)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"비디오를 열 수 없습니다: {video_path}")

    os.makedirs(output_faces, exist_ok=True)
    records = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        boxes, probs = mtcnn.detect(pil_img)

        if boxes is not None and len(boxes) > 0:
            best_idx = probs.argmax()
            x1, y1, x2, y2 = map(int, boxes[best_idx])
            x1, y1, x2, y2 = _expand_box(x1, y1, x2, y2, W, H, margin)
            w, h = x2 - x1, y2 - y1
            records.append({"frame": frame_idx, "x": x1, "y": y1, "w": w, "h": h})

            # 얼굴 crop해서 저장
            face_crop = frame[y1:y2, x1:x2]
            crop_path = os.path.join(output_faces, f"{frame_idx:06d}.jpg")
            cv2.imwrite(crop_path, face_crop)

        else:
            records.append({"frame": frame_idx, "x": -1, "y": -1, "w": -1, "h": -1})

        if frame_idx % max(1, total_frames // 10) == 0:
            print(f"[진행] {frame_idx}/{total_frames} 프레임")

        frame_idx += 1

    cap.release()
    df = pd.DataFrame(records, columns=["frame", "x", "y", "w", "h"])
    df.to_csv(output_csv, index=False)
    print(f"[완료] 얼굴 crop 저장: {output_faces}/")
    print(f"[완료] CSV 저장: {output_csv}")


def make_frame_list(frames_dir, output_txt):
    """StarGAN용 list_attr_celeba_small.txt 자동 생성"""
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    with open(output_txt, 'w') as f:
        f.write(f"{len(frames)}\n")
        f.write("Black_Hair Blond_Hair Brown_Hair Male Young\n")
        for name in frames:
            f.write(f"{name} -1 1 -1 -1 1\n")  # Blond_Hair 강제
    print(f"[OK] list_attr_celeba_small.txt 생성 완료 ({len(frames)} 프레임)")


# ===== 실행부 =====
if __name__ == "__main__":
    video_path = "testvideo.mp4"

    # ① 프레임 추출
    extract_frames(video_path, "frame_split")

    # ② 얼굴 추적 + 얼굴 crop + CSV 생성
    process_video(video_path, margin=0.35, output_faces="faces_cropped")

    # ③ StarGAN용 list 파일 생성
    make_frame_list("faces_cropped", "list_attr_celeba_small.txt")

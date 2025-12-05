## **디렉토리 구조**

```
ex_user/
 ├─ protect.py
 ├─ perturbation.pt
 ├─ setting.json
 │
 ├─ requirements.txt
 ├─ install.sh
 │
 ├─ README.md
 │
 ├─ tmp_frames/                → 영상 프레임 분할 후 순정 버전 저장
 ├─ tmp_frames_protected/      → 영상 프레임 분할 후 노이즈 추가된 버전 저장
 ├─ sample_original_frame.png  → 영상 노이즈 비교 테스트용 샘플 (영상 보호 처리 시 생성됨)
 ├─ sample_protected_frame.png → 영상 노이즈 비교 테스트용 샘플 (영상 보호 처리 시 생성됨)
 │
 ├─ input/   → 중요한 점 : 입력 이미지 및 영상은 256×256 고정
 └─ output/
```

---

## **입력 데이터 사이즈 변경 (터미널에서 실행)**

### **영상 256×256 고정 + 고화질 유지**

```bash
ffmpeg -i input.mp4 \
  -vf "scale=256:256:flags=lanczos:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -crf 10 -preset slow -pix_fmt yuv420p \
  -c:a copy \
  origin_video.mp4
```

### **이미지 256×256 고정 + 고화질 유지**

```bash
ffmpeg -i input.jpg \
  -vf "scale=256:256:flags=lanczos:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2" \
  -qscale:v 1 \
  origin_input.png
```

---

## **실행 순서**

### **1) 설치**

설치하려는 디렉토리로 이동 후 다음 실행:

```bash
chmod +x install.sh
./install.sh
```

> 환경 이름 = **deepflect**

---

### **2) 환경 활성화**

```bash
conda activate deepflect
```

---

### **3) 보호 실행 코드**

* `eps` 로 노이즈 세기 조절 (기본값: 1.0)

```bash
python protect.py \
  --input ./input/origin_video.mp4 \
  --output ./output/protected_video.mp4 \
  --eps 1.0
```


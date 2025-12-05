#!/usr/bin/env bash
set -e

ENV_NAME="deepflect"

echo "========================================"
echo "              TEAM fratelli            "
echo "    DeepFlect Environment Installer    "
echo "========================================"

# 1) conda 확인
if ! command -v conda &> /dev/null; then
  echo "[!] conda 명령을 찾을 수 없습니다."
  echo "    Miniconda 또는 Anaconda를 먼저 설치한 뒤 다시 실행하세요."
  exit 1
fi

# 2) conda base 경로 로드
CONDA_BASE=$(conda info --base)
# shellcheck disable=SC1090
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 3) 기존에 같은 이름의 환경이 있으면 안내
if conda env list | grep -q "^$ENV_NAME "; then
  echo "[*] 이미 '$ENV_NAME' 환경이 존재합니다."
  echo "    이 환경을 그대로 사용하거나, 삭제 후 다시 설치할 수 있습니다."
  echo "    삭제하려면: conda remove -n $ENV_NAME --all"
  echo
else
  echo "[*] 새 conda 환경 생성: $ENV_NAME (python=3.6)"
  conda create -y -n "$ENV_NAME" python=3.6
fi

# 4) 환경 활성화
echo "[*] 환경 활성화: $ENV_NAME"
conda activate "$ENV_NAME"

# 5) requirements.txt 설치
if [ ! -f "requirements.txt" ]; then
  echo "[!] requirements.txt 파일을 찾을 수 없습니다."
  echo "    이 스크립트와 같은 폴더에 requirements.txt를 두고 실행하세요."
  exit 1
fi

echo "[*] pip 패키지 설치 (requirements.txt)"
pip install -r requirements.txt

echo
echo "======================================="
echo "  DeepFlect Environment is Installed  "
echo "======================================="
echo

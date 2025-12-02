import os

# 업로드/저장 디렉토리
UPLOAD_FOLDER = "temp/uploads"
OUTPUT_FOLDER = "temp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
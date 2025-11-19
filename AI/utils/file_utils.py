import uuid
import os
from config import UPLOAD_FOLDER, OUTPUT_FOLDER

def save_upload_file(upload_file, prefix="file"):
    ext = upload_file.filename.split(".")[-1]
    save_path = os.path.join(UPLOAD_FOLDER, f"{prefix}_{uuid.uuid4()}.{ext}")

    with open(save_path, "wb") as f:
        f.write(upload_file.file.read())

    return save_path


def generate_output_path():
    return os.path.join(OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.mp4")

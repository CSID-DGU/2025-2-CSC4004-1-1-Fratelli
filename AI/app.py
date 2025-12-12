"""
FastAPI 메인 애플리케이션 - AI Video Protection Server
"""
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import uuid
import traceback
import requests
from pathlib import Path
import shutil
import uvicorn
import logging
import sys

# 로컬 모듈
from deepfake.defend_stargan import generate_video_thumbnail
from deepvoice.extract_audio import extract_audio
from deepvoice.protect_audio import protect_audio
from deepvoice.merge_video import merge_video
from config import UPLOAD_FOLDER, OUTPUT_FOLDER

# 딥페이크 방어 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), 'deepfake'))
from deepfake.defend_stargan import defend_image, defend_video
from deepfake.protect_wrapper import protect_image, protect_video
import random

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="AI Video Protection Server",
    description="이미지 및 동영상 보호 처리 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 protector (한 번만 초기화)
protector = None

# 취소된 작업 추적
cancelled_tasks = set()

def init_protector():
    """오디오 보호 시스템 초기화"""
    global protector
    if protector is None:
        print("Initializing HighQualityVoiceProtection...")
        from deepvoice.protect_audio import HighQualityVoiceProtection
        protector = HighQualityVoiceProtection(
            epsilon=0.008,
            alpha=0.0003,
            iterations=1500,
            lambda_psycho=0.2,
            lambda_smooth=0.15,
            lambda_spectral=0.1,
            augmentation_prob=0.7,
            attack_mode="quality",
            use_pretrained=True,
        )
    return protector


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("=" * 60)
    logger.info("AI Image/Video Protection Server 시작")
    logger.info("=" * 60)
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    
    # GPU 확인
    import torch
    if torch.cuda.is_available():
        logger.info(f"✅ GPU 사용 가능: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("⚠️ CPU 모드로 실행")
        
    # Torchaudio backend 설정
    import torchaudio
    try:
        torchaudio.set_audio_backend("soundfile")  # <- 추가
        logger.info(f"Torchaudio backend set to: {torchaudio.get_audio_backend()}")
    except Exception as e:
        logger.warning(f"⚠️ Torchaudio backend 설정 실패: {e}")
        
    # Protector 초기화 (미리 로드)
    try:
        logger.info("오디오 보호 시스템 초기화 중...")
        init_protector()
        logger.info("✅ 오디오 보호 시스템 초기화 완료")
    except Exception as e:
        logger.warning(f"⚠️ 오디오 보호 시스템 초기화 실패: {e}")
    
    logger.info("🚀 서버 준비 완료")


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info("서버 종료 중...")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "status": "ok",
        "message": "AI Video Protection Server is running",
        "version": "1.0.0"
    }


@app.get('/health')
async def health():
    """헬스 체크"""
    import torch
    gpu_available = torch.cuda.is_available()
    
    # 컴포넌트 상태 확인
    status = {
        "api": "ok",
        "gpu_available": gpu_available,
        "device": "cuda" if gpu_available else "cpu",
        "protector": "unknown"
    }
    
    # Protector 상태
    try:
        global protector
        if protector is not None:
            status["protector"] = "initialized"
        else:
            status["protector"] = "not_initialized"
    except Exception as e:
        status["protector"] = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "components": status
    }

class ProcessingStopped(Exception):
    """사용자가 업로드 파일을 삭제하면 처리 중단"""
    pass

def _background_image_processing(task_id: str, image_path: str):
    """
    백그라운드에서 이미지 처리:
    1. defend_stargan으로 이미지 보호
    """
    print(f"[{task_id}] Background image processing started for {image_path}")
    
    try:
        # 취소 확인
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task was cancelled")
        
        # 파일 존재 확인
        if not os.path.exists(image_path):
            raise ProcessingStopped(f"[{task_id}] Uploaded file was deleted: {image_path}")
        
        # 진행률 0%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 0, 'progressStatus': '시작'},
                timeout=2
            )
        except Exception:
            pass
        
        # 랜덤으로 보호 방법 선택 (defend_stargan or protect)
        # use_defend_stargan = random.choice([True, False])
        method_name = "protect (CMUA)"
        
        print(f"[{task_id}] Step 1: Protecting image with {method_name}...")
        
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task cancelled before image protection")
        
        # 출력 파일 경로 결정 (확장자 유지)
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            ext = '.png'
        output_image = os.path.join(OUTPUT_FOLDER, f"{task_id}_protected{ext}")
        
        # if use_defend_stargan:
        #     # defend_stargan 사용
        #     ckpt_path = os.path.join(os.path.dirname(__file__), 'deepfake', 'models', '30000-PG-005.ckpt')
        #     if not os.path.exists(ckpt_path):
        #         raise Exception(f"Checkpoint file not found: {ckpt_path}")
            
        #     defend_image(
        #         input_path=image_path,
        #         output_path=output_image,
        #         ckpt_path=ckpt_path,
        #         eps=0.10,
        #         image_size=128,
        #         device="cuda"
        #     )
            # protect (CMUA) 사용
        perturbation_path = os.path.join(os.path.dirname(__file__), 'deepfake', 'models', 'perturbation.pt')
        if not os.path.exists(perturbation_path):
            raise Exception(f"Perturbation file not found: {perturbation_path}")
        
        protect_image(
            input_path=image_path,
            output_path=output_image,
            perturbation_path=perturbation_path,
            eps=1.0,
            image_size=224
        )
        
        print(f"[{task_id}] Image protected with {method_name}: {output_image}")
        
        # 진행률 100%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 100, 'progressStatus': '완료'},
                timeout=2
            )
        except Exception:
            pass
        
        # 완료 콜백
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_finished',
                json={
                    'taskId': task_id,
                    'progress': 100,
                    'downloadUrl': f'http://localhost:8080/api/v1/files/download-protected/{task_id}',
                    'progressStatus': '완료'
                },
                timeout=2
            )
            print(f"[{task_id}] Finished callback sent")
        except Exception as e:
            print(f"[{task_id}] Failed to send finished callback: {e}")
    
    except ProcessingStopped as ps:
        print(ps)
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_failed',
                json={'taskId': task_id, 'message': str(ps)},
                timeout=2
            )
        except Exception:
            pass
    
    except Exception as e:
        print(f"[{task_id}] Error in image processing: {e}")
        print(traceback.format_exc())
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_failed',
                json={'taskId': task_id, 'message': str(e)},
                timeout=2
            )
        except Exception:
            pass
    
    finally:
        if task_id in cancelled_tasks:
            cancelled_tasks.discard(task_id)
            logger.info(f"[{task_id}] Removed from cancelled tasks")
    
    print(f"[{task_id}] Background image processing completed")


def _background_video_processing(task_id: str, video_path: str):
    """
    백그라운드에서 비디오 처리:
    1. 오디오 추출 (extract_audio)
    2. 오디오 보호 (protect_audio)
    3. 비디오와 보호된 오디오 병합 (merge_video)
    """
    print(f"[{task_id}] Background processing started for {video_path}")

    try:
        # 취소 확인
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task was cancelled")
        
        # 0. 파일 존재 확인
        if not os.path.exists(video_path):
            raise ProcessingStopped(f"[{task_id}] Uploaded file was deleted: {video_path}")

        # 진행률 0%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 0, 'progressStatus': '시작'},
                timeout=2
            )
        except Exception:
            pass

        # 1. 오디오 추출
        print(f"[{task_id}] Step 1: Extracting audio...")
        
        # 취소 확인
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task cancelled before audio extraction")
        
        extracted_audio = os.path.join(UPLOAD_FOLDER, f"{task_id}_extracted.wav")
        
        # 추출 전 파일 존재 확인
        if not os.path.exists(video_path):
            raise ProcessingStopped(f"[{task_id}] Uploaded file deleted before audio extraction")
        
        extract_audio(video_path, extracted_audio)
        print(f"[{task_id}] Audio extracted: {extracted_audio}")

        # 진행률 30% (노이즈 삽입 중)
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 30, 'progressStatus': '오디오 노이즈 삽입 중'},
                timeout=2
            )
        except Exception:
            pass

        # 2. 오디오 보호
        print(f"[{task_id}] Step 2: Protecting audio...")
        
        # 취소 확인 (보호 작업은 시간이 오래 걸리므로 중요)
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task cancelled before audio protection")
        
        protected_audio = os.path.join(UPLOAD_FOLDER, f"{task_id}_protected.wav")

        # 보호 함수 내부에서도 파일 존재 체크
        if not os.path.exists(extracted_audio):
            raise ProcessingStopped(f"[{task_id}] Extracted audio deleted before protection")
        
        # task_id와 cancelled_tasks를 전달하여 반복 중 취소 체크
        protect_audio(extracted_audio, protected_audio, task_id, cancelled_tasks)
        print(f"[{task_id}] Audio protected: {protected_audio}")

        # 진행률 70%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 70, 'progressStatus': '오디오 완료'},
                timeout=2
            )
        except Exception:
            pass

        # 3. 비디오 딥페이크 방어 (랜덤: defend_stargan or protect)
        # use_defend_stargan = random.choice([True, False])
        method_name = "protect (CMUA)"
        
        print(f"[{task_id}] Step 3: Protecting video with {method_name}...")
        
        # 취소 확인
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task cancelled before video deepfake defense")
        
        # 임시 방어된 비디오 경로
        defended_video = os.path.join(UPLOAD_FOLDER, f"{task_id}_defended.mp4")
        
        # protect (CMUA) 사용
        perturbation_path = os.path.join(os.path.dirname(__file__), 'deepfake', 'models', 'perturbation.pt')
        if not os.path.exists(perturbation_path):
            raise Exception(f"Perturbation file not found: {perturbation_path}")
        
        protect_video(
            input_path=video_path,
            output_path=defended_video,
            perturbation_path=perturbation_path,
            eps=1.0,
            image_size=224
        )
        
        print(f"[{task_id}] Video defended with {method_name}: {defended_video}")
        
        # 진행률 80%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 80, 'progressStatus': '영상 노이즈 삽입 완료'},
                timeout=2
            )
        except Exception:
            pass
        
        # 4. 방어된 비디오와 보호된 오디오 병합
        print(f"[{task_id}] Step 4: Merging defended video and protected audio...")
        
        # 취소 확인
        if task_id in cancelled_tasks:
            raise ProcessingStopped(f"[{task_id}] Task cancelled before final merge")
        
        output_video = os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.mp4")

        if not os.path.exists(defended_video) or not os.path.exists(protected_audio):
            raise ProcessingStopped(f"[{task_id}] Defended video or protected audio missing before merge")
        
        merge_video(defended_video, protected_audio, output_video)
        print(f"[{task_id}] Final video merged: {output_video}")
        
        # ---  썸네일 생성 로직 추가 ---
        print(f"[{task_id}] Generating thumbnail...")
        # output_video가 ".../uuid_protected.mp4" 이므로 
        # 썸네일은 ".../uuid_protected_thumbnail.jpg"로 생성됨
        generate_video_thumbnail(output_video, OUTPUT_FOLDER)

        # 진행률 100%
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_progress',
                json={'taskId': task_id, 'progress': 100, 'progressStatus': '완료'},
                timeout=2
            )
        except Exception:
            pass

        # 완료 콜백
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_finished',
                json={
                    'taskId': task_id,
                    'progress': 100,
                    'downloadUrl': f'http://localhost:8080/api/v1/files/download-protected/{task_id}',
                    'progressStatus': '완료'
                },
                timeout=2
            )
            print(f"[{task_id}] Finished callback sent")
        except Exception as e:
            print(f"[{task_id}] Failed to send finished callback: {e}")

    except ProcessingStopped as ps:
        print(ps)
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_failed',
                json={'taskId': task_id, 'message': str(ps)},
                timeout=2
            )
        except Exception:
            pass

    except Exception as e:
        print(f"[{task_id}] Error in processing: {e}")
        print(traceback.format_exc())
        try:
            requests.post(
                'http://localhost:8080/api/v1/callback/ai_failed',
                json={'taskId': task_id, 'message': str(e)},
                timeout=2
            )
        except Exception:
            pass
    
    finally:
        # 처리 완료 후 취소 목록에서 제거
        if task_id in cancelled_tasks:
            cancelled_tasks.discard(task_id)
            logger.info(f"[{task_id}] Removed from cancelled tasks")

    print(f"[{task_id}] Background processing completed")



@app.post('/api/v1/files/progress-file')
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    taskId: Optional[str] = Form(None),
    fileType: Optional[str] = Form(None)
):
    """
    통합 파일 처리 API (백엔드 호환)
    
    Request:
    - file: 업로드 파일 (비디오/이미지/오디오)
    - taskId: 백엔드에서 제공하는 작업 ID
    - fileType: 파일 타입 ('video', 'image', 'audio')
    
    Response:
    - task_id: 작업 ID
    - status: 'queued'
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail='No selected file')
        
        # 작업 ID 생성 또는 사용 (백엔드에서 제공)
        task_id = taskId or str(uuid.uuid4())
        
        # 파일 저장
        filename = file.filename.replace('/', '_').replace('\\', '_')
        saved_name = f"{task_id}_{filename}"
        saved_path = os.path.join(UPLOAD_FOLDER, saved_name)
        
        with open(saved_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[{task_id}] File saved: {saved_path}")
        
        # 파일 타입 추론 (백엔드가 제공하지 않으면)
        if not fileType:
            lower = filename.lower()
            if lower.endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
                fileType = 'video'
            elif lower.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')):
                fileType = 'image'
            else:
                fileType = 'other'
        
        logger.info(f"[{task_id}] File type: {fileType}")
        
        # 파일 타입에 따라 처리
        if fileType == 'video':
            # 백그라운드 비디오 처리 (딥보이스 + 딥페이크)
            background_tasks.add_task(_background_video_processing, task_id, saved_path)
            logger.info(f"[{task_id}] Background video processing scheduled")
        elif fileType == 'image':
            # 백그라운드 이미지 처리 (딥페이크만)
            background_tasks.add_task(_background_image_processing, task_id, saved_path)
            logger.info(f"[{task_id}] Background image processing scheduled")
        else:
            # 오디오는 아직 미지원
            logger.warning(f"[{task_id}] Unsupported file type: {fileType}")
            raise HTTPException(
                status_code=400,
                detail=f"File type '{fileType}' is not supported yet. Only video and image files are supported."
            )
        
        return {
            'task_id': task_id,
            'status': 'uploading'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_file: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/files/thumbnail/{task_id}')
async def get_thumbnail(task_id: str):
    """썸네일 이미지 다운로드"""
    # 생성 규칙: {task_id}_protected_thumbnail.jpg
    # (generate_video_thumbnail 함수가 파일명_thumbnail.jpg 로 저장하기 때문)
    thumbnail_filename = f"{task_id}_protected_thumbnail.jpg"
    thumbnail_path = os.path.join(OUTPUT_FOLDER, thumbnail_filename)
    
    if not os.path.exists(thumbnail_path):
        # 혹시 protected가 안 붙은 경우를 대비한 예외 처리 (선택사항)
        fallback_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_thumbnail.jpg")
        if os.path.exists(fallback_path):
            thumbnail_path = fallback_path
            thumbnail_filename = f"{task_id}_thumbnail.jpg"
        else:
            raise HTTPException(status_code=404, detail="Thumbnail not found")
            
    return FileResponse(
        thumbnail_path, 
        media_type="image/jpeg", 
        filename=thumbnail_filename
    )
    
@app.get('/api/v1/download/{task_id}')
async def download_file(task_id: str):
    """보호된 파일 다운로드 (비디오/이미지/오디오)"""
    try:
        # outputs 폴더에서 파일 찾기 (확장자 우선순위: 이미지 -> 비디오 -> 오디오)
        possible_files = [
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.png"), "image/png", ".png"),
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.jpg"), "image/jpeg", ".jpg"),
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.jpeg"), "image/jpeg", ".jpeg"),
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.webp"), "image/webp", ".webp"),
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.mp4"), "video/mp4", ".mp4"),
            (os.path.join(OUTPUT_FOLDER, f"{task_id}_protected.wav"), "audio/wav", ".wav"),
        ]
        
        protected_file = None
        media_type = None
        extension = None
        
        for file_path, mime_type, ext in possible_files:
            if os.path.exists(file_path):
                protected_file = file_path
                media_type = mime_type
                extension = ext
                logger.info(f"[{task_id}] Found protected file: {file_path}")
                break
        
        if protected_file is None:
            logger.warning(f"[{task_id}] No protected file found")
            raise HTTPException(status_code=404, detail='Protected file not found')
        
        return FileResponse(
            protected_file,
            media_type=media_type,
            filename=f'{task_id}_protected{extension}'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v1/status/{task_id}')
async def get_status(task_id: str):
    """작업 상태 조회"""
    try:
        # outputs 폴더에서 보호된 파일 존재 여부 확인
        possible_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.mp4', '.wav']
        
        for ext in possible_extensions:
            output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_protected{ext}")
            if os.path.exists(output_path):
                return {
                    'task_id': task_id,
                    'status': 'success'
                }
        
        # 파일이 없으면 처리 중
        return {
            'task_id': task_id,
            'status': 'uploading'
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            'task_id': task_id,
            'status': 'unknown'
        }


@app.delete('/api/v1/cancel/{task_id}')
async def cancel_processing(task_id: str):
    """
    업로드 취소 - 처리 중인 파일 삭제 및 작업 중단
    백엔드에서 DELETE /api/v1/files/uploads/{taskId} 호출 시 실행
    """
    try:
        logger.info(f"[{task_id}] Cancelling processing...")
        
        # 취소 플래그 설정 (백그라운드 작업이 이를 감지하고 중단)
        cancelled_tasks.add(task_id)
        logger.info(f"[{task_id}] Added to cancelled tasks set")
        
        # 업로드된 원본 파일 삭제
        deleted_files = []
        
        # uploads 폴더에서 taskId로 시작하는 파일 찾아서 삭제
        upload_pattern = f"{task_id}_*"
        for file in Path(UPLOAD_FOLDER).glob(upload_pattern):
            if file.is_file():
                file.unlink()
                deleted_files.append(str(file))
                logger.info(f"[{task_id}] Deleted upload file: {file}")
        
        # outputs 폴더에서 보호된 파일 삭제
        output_pattern = f"{task_id}_protected.*"
        for file in Path(OUTPUT_FOLDER).glob(output_pattern):
            if file.is_file():
                file.unlink()
                deleted_files.append(str(file))
                logger.info(f"[{task_id}] Deleted output file: {file}")
        
        return {
            'task_id': task_id,
            'status': 'cancelled',
            'deleted_files': deleted_files,
            'message': f'Processing cancelled, {len(deleted_files)} files deleted. Background task will stop at next checkpoint.'
        }
            
    except Exception as e:
        logger.error(f"[{task_id}] Error cancelling: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=8000,
        reload=True  # 프로덕션에서는 False
    )
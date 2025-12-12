# 2025-2-CSC4004-1-1-Fratelli
팀장 : 김현정 
팀원 : 박서연, 유호준, 정세연

# 본 프로젝트는 최근 급격히 발전한 딥보이스(Voice Cloning) 및 딥페이크(Deepfake) 기술이 가지는 실제적 위협에 대응하는 것을 핵심 목표로 합니다.

1️⃣ DeepVoice (Voice Cloning) 위협

딥보이스 기술은 짧은 음성 샘플만으로도 특정 화자의 음색·억양·발화 습관을 학습하여, 마치 실제 화자가 말한 것처럼 고품질 음성을 생성할 수 있습니다.
이로 인해 다음과 같은 문제가 발생합니다.

> 1. 유명인·지인의 음성을 이용한 사기 전화 및 음성 스푸핑
>
> 2. 음성 인증 시스템(콜센터, 금융 ARS)의 신뢰성 붕괴
>
> 3. AI 음성 합성 기반 허위 발언 생성

본 프로젝트에서는 단순히 **귀로 들었을 때 다른 음성**을 만드는 것이 아니라,

**사람에게는 거의 구별되지 않지만,
딥보이스 모델이 화자 특징을 정확히 추출하지 못하도록 방해하는 것** 을 목표로 합니다.

### 🔐 DeepVoice 방어 접근 방식

ECAPA-TDNN 기반 Speaker Embedding 공격

Waveform 레벨에서 지각 불가능한 adversarial perturbation 추가

음질(SNR, PESQ)을 최대한 유지하면서
화자 임베딩 공간(feature space)에서 유사도 붕괴 유도

다양한 음성 변환(랜덤 증강)을 포함한 Robust Optimization

이를 통해,

사람 귀 기준: 거의 동일한 음성

AI 모델 기준: “다른 화자”로 인식

하는 비대칭 방어 효과를 지향합니다.

### ✨ What’s inside

AI(음성/영상) 방어 모듈: 음성 보호(perturbation), 얼굴/랜드마크 기반 방어 등 다양한 실험 모듈 포함

Backend: 클라이언트(앱/확장) 요청을 받아 AI 모듈을 오케스트레이션

Front App (Flutter): 사용자 UI/워크플로우 제공

Front Extension (Browser Extension): 웹 환경에서 빠른 보호 적용/업로드 지원

### 🧱 Repository Structure

아래는 현재 저장소 루트에 존재하는 주요 폴더들입니다. 
GitHub

.
├─ AI/                 # AI 관련 실험/유틸(프로젝트 구성에 따라 사용)
├─ AI_DeepVoice/        # 음성 보호/딥보이스 방어 중심 모듈
├─ Backend/             # 서버(API) 및 오케스트레이션
├─ DeepFlect/           # 통합/핵심 모듈(프로젝트 구성에 따라 사용)
├─ LandmarkBreaker/     # 얼굴 랜드마크 기반 방어/교란 실험
├─ defend/              # 방어 관련 실험/스크립트
├─ facetrack/           # 얼굴 추적/전처리 관련
├─ front_app/           # Flutter 앱
├─ front_extension/     # 브라우저 확장
├─ submit/              # 제출용 산출물/패키징
└─ README.md

### 🚀 Quick Start (개발 환경)

프로젝트가 멀티 모듈 구조라서, 보통 아래처럼 “모듈별로” 실행합니다.

1) Backend 실행

2) AI 모듈 실행 (예: 음성 보호)

3) Front App (Flutter)


4) Front Extension (Browser Extension)


### 🧩 How it works (권장 흐름)

사용자(앱/확장)가 음성/영상 파일 업로드 또는 링크 입력

Backend가 요청 수신 → 파일 저장/전처리

Backend가 AI 모듈(음성 보호, 얼굴/랜드마크 방어 등) 호출

결과물(Protected media) 반환 및 다운로드/재생 제공

### 🛠️ Development Notes



👥 Team

팀장: 김현정

팀원: 박서연, 유호준, 정세연 

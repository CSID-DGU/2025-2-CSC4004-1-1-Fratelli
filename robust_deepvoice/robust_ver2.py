"""
Robust Voice Protection System (Production Version)
====================================================
Feature-space attack using pre-trained ECAPA-TDNN + Robust optimization

핵심 원리:
1. 실제 TTS 시스템이 사용하는 ECAPA-TDNN 스피커 인코더 공격
2. 다양한 변환(압축, 리샘플, 노이즈제거)에 강건한 perturbation
3. Psychoacoustic masking으로 사람 귀에는 안 들리게

Requirements:
pip install torch torchaudio speechbrain
"""

import torch
import torchaudio
import torch.nn.functional as F
import numpy as np
import random
import sys
import os


class DataAugmentation:
    """
    강건성을 위한 데이터 증강
    MP3 압축, 리샘플, 노이즈, 리버브 등을 시뮬레이션
    """
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def random_resample(self, waveform):
        """무작위 리샘플 (8k/12k/16k/24k)"""
        target_rates = [8000, 12000, 16000, 24000]
        target_sr = random.choice(target_rates)
        
        if target_sr == self.sample_rate:
            return waveform
        
        # 리샘플 후 다시 원래 샘플레이트로
        resampler_down = torchaudio.transforms.Resample(
            self.sample_rate, target_sr
        ).to(self.device)
        resampler_up = torchaudio.transforms.Resample(
            target_sr, self.sample_rate
        ).to(self.device)
        
        resampled = resampler_down(waveform)
        restored = resampler_up(resampled)
        
        # 길이 맞춤
        if restored.shape[-1] > waveform.shape[-1]:
            restored = restored[..., :waveform.shape[-1]]
        elif restored.shape[-1] < waveform.shape[-1]:
            padding = waveform.shape[-1] - restored.shape[-1]
            restored = F.pad(restored, (0, padding))
        
        return restored
    
    def random_gain(self, waveform):
        """무작위 게인 조정 (±3dB)"""
        gain_db = random.uniform(-3, 3)
        gain_linear = 10 ** (gain_db / 20)
        return waveform * gain_linear
    
    def add_background_noise(self, waveform):
        """배경 노이즈 추가 (SNR 20-40dB)"""
        snr_db = random.uniform(20, 40)
        signal_power = torch.mean(waveform ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        
        noise = torch.randn_like(waveform) * torch.sqrt(noise_power)
        return waveform + noise
    
    def mp3_compression_simulation(self, waveform):
        """
        MP3 압축 시뮬레이션 (더 강하게)
        """
        # 더 공격적인 압축 시뮬레이션
        cutoff = random.uniform(3000, 7000)  # 더 낮은 주파수
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        
        # Lowpass filter
        kernel_size = 101
        kernel = torch.sinc(
            2 * normalized_cutoff * (torch.arange(kernel_size, dtype=torch.float32) - kernel_size // 2)
        )
        kernel = kernel / kernel.sum()
        kernel = kernel.view(1, 1, -1).to(self.device)
        
        # Convolution
        padded = F.pad(waveform, (kernel_size // 2, kernel_size // 2), mode='reflect')
        filtered = F.conv1d(padded, kernel)
        
        # 추가: 비트 양자화 시뮬레이션 (MP3 효과)
        bits = random.choice([8, 12, 16])
        scale = 2 ** bits
        quantized = torch.round(filtered * scale) / scale
        
        return quantized
    
    def apply_random_augmentation(self, waveform):
        """무작위로 증강 기법 하나 또는 여러 개 적용"""
        augmentations = [
            self.random_resample,
            self.random_gain,
            self.add_background_noise,
            self.mp3_compression_simulation,
        ]
        
        # 50% 확률로 2개 연속 적용 (더 강건하게)
        if random.random() < 0.5:
            aug_func1 = random.choice(augmentations)
            aug_func2 = random.choice(augmentations)
            waveform = aug_func1(waveform)
            waveform = aug_func2(waveform)
        else:
            aug_func = random.choice(augmentations)
            waveform = aug_func(waveform)
        
        return waveform


class RobustVoiceProtection:
    """
    강건한 음성 보호 시스템
    Feature-space attack + Robust optimization with ECAPA-TDNN
    """
    def __init__(
        self,
        epsilon=0.02,           # 더 강하게! (0.01 → 0.02)
        alpha=0.0005,           # Step size 증가
        iterations=800,         # 더 많은 최적화 (400 → 800)
        lambda_psycho=0.05,     # Psycho 완화 (더 공격적)
        augmentation_prob=0.8,  # 증강 확률 증가 (강건성 UP)
        use_pretrained=True,    # ECAPA-TDNN 사용 여부
    ):
        self.epsilon = epsilon
        self.alpha = alpha
        self.iterations = iterations
        self.lambda_psycho = lambda_psycho
        self.augmentation_prob = augmentation_prob
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Speaker Encoder 초기화
        if use_pretrained:
            print("Loading pre-trained ECAPA-TDNN from SpeechBrain...")
            try:
                # SpeechBrain 1.0+ uses inference module
                try:
                    from speechbrain.inference.speaker import EncoderClassifier
                except ImportError:
                    from speechbrain.pretrained import EncoderClassifier
                
                self.encoder = EncoderClassifier.from_hparams(
                    source="speechbrain/spkrec-ecapa-voxceleb",
                    savedir="pretrained_models/spkrec-ecapa-voxceleb",
                    run_opts={"device": str(self.device)}
                )
                self.use_pretrained = True
                print("✓ ECAPA-TDNN loaded successfully!")
            except Exception as e:
                print(f"Warning: Could not load ECAPA-TDNN: {e}")
                print("Falling back to simple encoder (for testing only)")
                self.encoder = self._create_simple_encoder()
                self.use_pretrained = False
        else:
            print("Using simple encoder (for testing only)")
            self.encoder = self._create_simple_encoder()
            self.use_pretrained = False
        
        # Data Augmentation 초기화
        self.augmentor = DataAugmentation()
        
        print(f"Device: {self.device}")
        print(f"Parameters: epsilon={epsilon}, alpha={alpha}, iterations={iterations}")
    
    def _create_simple_encoder(self):
        """간단한 테스트용 인코더 (실전 사용 X)"""
        class SimpleEncoder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = torch.nn.Conv1d(1, 64, kernel_size=80, stride=16)
                self.conv2 = torch.nn.Conv1d(64, 128, kernel_size=5, stride=2)
                self.conv3 = torch.nn.Conv1d(128, 256, kernel_size=3, stride=2)
                self.pool = torch.nn.AdaptiveAvgPool1d(1)
                self.fc = torch.nn.Linear(256, 192)
                
            def forward(self, waveform):
                x = F.relu(self.conv1(waveform))
                x = F.relu(self.conv2(x))
                x = F.relu(self.conv3(x))
                x = self.pool(x).squeeze(-1)
                embedding = F.normalize(self.fc(x), p=2, dim=-1)
                return embedding
        
        encoder = SimpleEncoder().to(self.device)
        encoder.eval()
        return encoder
    
    def load_audio(self, audio_path):
        """오디오 로드 및 전처리"""
        waveform, sr = torchaudio.load(audio_path)
        
        # 16kHz로 리샘플
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        # 모노로 변환
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        return waveform.unsqueeze(0).to(self.device)  # [1, 1, time]
    
    def extract_embedding(self, waveform):
        """스피커 임베딩 추출"""
        with torch.no_grad():
            if self.use_pretrained:
                # ECAPA-TDNN: [batch, time] 형식 필요
                embedding = self.encoder.encode_batch(waveform.squeeze(1))
                # tuple이면 첫 번째 요소 추출
                if isinstance(embedding, tuple):
                    embedding = embedding[0]
                # 정규화
                embedding = F.normalize(embedding, p=2, dim=-1)
            else:
                # Simple encoder: [batch, 1, time]
                embedding = self.encoder(waveform)
        
        return embedding
    
    def psychoacoustic_penalty(self, perturbation):
        """
        Psychoacoustic 페널티
        고주파에 더 많은 에너지 할당 (사람 귀에 덜 민감)
        """
        # FFT로 주파수 분석
        fft = torch.fft.rfft(perturbation, dim=-1)
        magnitude = torch.abs(fft)
        
        # 저주파 페널티 (0-2kHz는 사람이 민감)
        n_freqs = magnitude.shape[-1]
        low_freq_ratio = int(0.125 * n_freqs)  # 2kHz at 16kHz SR
        
        low_freq_penalty = magnitude[..., :low_freq_ratio].pow(2).mean()
        high_freq_penalty = magnitude[..., low_freq_ratio:].pow(2).mean()
        
        # 저주파는 억제, 고주파는 허용
        return low_freq_penalty - 0.5 * high_freq_penalty
    
    def generate_perturbation(self, original_waveform):
        """
        강건한 perturbation 생성
        Feature-space attack + Robust optimization
        """
        # 원본 임베딩 추출
        print("\nExtracting original speaker embedding...")
        original_embedding = self.extract_embedding(original_waveform)
        print(f"Original embedding shape: {original_embedding.shape}")
        print(f"Original embedding norm: {original_embedding.norm().item():.4f}")
        
        # Perturbation 초기화 (작은 노이즈로 시작)
        perturbation = torch.zeros_like(original_waveform).uniform_(
            -self.epsilon/10, self.epsilon/10
        )
        perturbation.requires_grad = True
        
        # Optimizer 설정 (Adam 사용)
        optimizer = torch.optim.Adam([perturbation], lr=self.alpha)
        
        print(f"\nStarting robust optimization ({self.iterations} iterations)...")
        print("This will take a few minutes...")
        
        best_loss = -float('inf')
        best_perturbation = perturbation.clone()
        
        for iteration in range(self.iterations):
            optimizer.zero_grad()
            
            # Perturbation 적용
            perturbed_waveform = original_waveform + perturbation
            perturbed_waveform = torch.clamp(perturbed_waveform, -1.0, 1.0)
            
            # 무작위 증강 적용 (강건성)
            if random.random() < self.augmentation_prob:
                augmented = self.augmentor.apply_random_augmentation(perturbed_waveform)
            else:
                augmented = perturbed_waveform
            
            # 증강된 오디오의 임베딩 추출
            if self.use_pretrained:
                # ECAPA-TDNN: encode_batch 사용
                perturbed_embedding = self.encoder.encode_batch(augmented.squeeze(1))
                # tuple이면 첫 번째 요소 추출
                if isinstance(perturbed_embedding, tuple):
                    perturbed_embedding = perturbed_embedding[0]
                perturbed_embedding = F.normalize(perturbed_embedding, p=2, dim=-1)
            else:
                perturbed_embedding = self.encoder(augmented)
            
            # Loss 계산
            # 목표: 원본과 변조된 임베딩의 코사인 유사도를 낮춤
            cosine_similarity = F.cosine_similarity(
                original_embedding, 
                perturbed_embedding, 
                dim=-1
            ).mean()
            
            # L2 distance도 최대화 (더 강력)
            l2_distance = torch.norm(original_embedding - perturbed_embedding, p=2, dim=-1).mean()
            
            # Embedding distance 최대화 (유사도 최소화)
            embedding_loss = cosine_similarity - 0.3 * l2_distance  # L2도 고려
            
            # Psychoacoustic 페널티
            psycho_penalty = self.psychoacoustic_penalty(perturbation)
            
            # 총 손실
            total_loss = embedding_loss + self.lambda_psycho * psycho_penalty
            
            # Backpropagation
            total_loss.backward()
            optimizer.step()
            
            # Epsilon ball 제약 (L_inf)
            with torch.no_grad():
                perturbation.clamp_(-self.epsilon, self.epsilon)
            
            # Best perturbation 저장
            if -total_loss.item() > best_loss:
                best_loss = -total_loss.item()
                best_perturbation = perturbation.clone().detach()
            
            # 진행 상황 출력
            if (iteration + 1) % 50 == 0:
                print(f"Iter {iteration+1}/{self.iterations}: "
                      f"Cosine Sim={cosine_similarity.item():.4f}, "
                      f"Total Loss={total_loss.item():.4f}")
        
        print(f"\nOptimization complete!")
        print(f"Final cosine similarity: {cosine_similarity.item():.4f}")
        print(f"(Lower is better - original similarity was ~1.0)")
        
        return best_perturbation.detach()
    
    def analyze_protection(self, original_waveform, perturbation):
        """보호 효과 분석"""
        perturbed_waveform = original_waveform + perturbation
        perturbed_waveform = torch.clamp(perturbed_waveform, -1.0, 1.0)
        
        # 임베딩 비교
        original_emb = self.extract_embedding(original_waveform)
        perturbed_emb = self.extract_embedding(perturbed_waveform)
        
        cosine_sim = F.cosine_similarity(original_emb, perturbed_emb, dim=-1).mean().item()
        
        # SNR 계산
        signal_power = torch.mean(original_waveform ** 2)
        noise_power = torch.mean(perturbation ** 2)
        snr_db = 10 * torch.log10(signal_power / noise_power).item()
        
        # Perturbation 통계
        max_pert = perturbation.abs().max().item()
        mean_pert = perturbation.abs().mean().item()
        
        print("\n" + "="*60)
        print("PROTECTION ANALYSIS")
        print("="*60)
        print(f"Speaker Encoder: {'ECAPA-TDNN (Real)' if self.use_pretrained else 'Simple (Test only)'}")
        print(f"\nEmbedding Cosine Similarity: {cosine_sim:.4f}")
        print(f"  Original: 1.0 (same speaker)")
        print(f"  Target: < 0.3 (very different speaker)")
        print(f"  Status: {'✓✓ STRONG' if cosine_sim < 0.3 else '✓ PROTECTED' if cosine_sim < 0.5 else '⚠ WEAK'}")
        print(f"\nSignal-to-Noise Ratio: {snr_db:.2f} dB")
        print(f"  Target: > 30dB (inaudible)")
        print(f"  Status: {'✓ INAUDIBLE' if snr_db > 30 else '⚠ AUDIBLE'}")
        print(f"\nPerturbation Statistics:")
        print(f"  Max: {max_pert:.6f} (Limit: {self.epsilon})")
        print(f"  Mean: {mean_pert:.6f}")
        print("="*60)
        
        return {
            'cosine_similarity': cosine_sim,
            'snr_db': snr_db,
            'max_perturbation': max_pert,
            'mean_perturbation': mean_pert
        }
    
    def save_protected_audio(self, waveform, perturbation, output_path):
        """보호된 오디오 저장"""
        protected = waveform + perturbation
        protected = torch.clamp(protected, -1.0, 1.0)
        
        # 정규화
        max_val = protected.abs().max()
        if max_val > 0:
            protected = protected / max_val * 0.95
        
        torchaudio.save(output_path, protected.squeeze(0).cpu(), 16000)
        print(f"\n✓ Protected audio saved: {output_path}")


def main():
    # 기본 설정
    input_file = "original_audio.wav"
    output_file = "protected_audio.wav"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    print("="*60)
    print("ROBUST VOICE PROTECTION SYSTEM")
    print("="*60)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)
    
    # 시스템 초기화
    protector = RobustVoiceProtection(
        epsilon=0.02,           # 더 강한 보호 (0.01 → 0.02)
        alpha=0.0005,           # 더 큰 step
        iterations=800,         # 더 많은 최적화 (400 → 800)
        lambda_psycho=0.05,     # Psycho 완화 (더 공격적)
        augmentation_prob=0.8,  # 80% 확률로 증강
        use_pretrained=True,    # ECAPA-TDNN 사용
    )
    
    # 오디오 로드
    print("\nLoading audio...")
    waveform = protector.load_audio(input_file)
    duration = waveform.shape[-1] / 16000
    print(f"Duration: {duration:.2f} seconds")
    
    # Perturbation 생성
    perturbation = protector.generate_perturbation(waveform)
    
    # 분석
    analysis = protector.analyze_protection(waveform, perturbation)
    
    # 저장
    protector.save_protected_audio(waveform, perturbation, output_file)
    
    print("\n" + "="*60)
    print("PROTECTION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Listen to the protected audio - should sound natural")
    print("2. Test with voice cloning tools (e.g., SV2TTS, RVC)")
    print("3. Try uploading to YouTube and re-downloading")
    print("4. Verify protection still works after compression")
    print("\nIf protection is weak, try:")
    print("  - Increase epsilon (e.g., 0.02)")
    print("  - Increase iterations (e.g., 800)")
    print("="*60)


if __name__ == "__main__":
    main()
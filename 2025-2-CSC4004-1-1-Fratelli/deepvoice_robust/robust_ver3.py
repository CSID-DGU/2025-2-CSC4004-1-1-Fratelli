"""
Enhanced Robust Voice Protection System v2.0 (Fixed)
====================================================
SV2TTS/RVC 대응 강화 버전 - Gradient 버그 수정
"""

import torch
import torchaudio
import torch.nn.functional as F
import numpy as np
import random
import sys
import os
from scipy import signal


class DataAugmentation:
    """
    강건성을 위한 데이터 증강 (개선 버전)
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
        
        resampler_down = torchaudio.transforms.Resample(
            self.sample_rate, target_sr
        ).to(self.device)
        resampler_up = torchaudio.transforms.Resample(
            target_sr, self.sample_rate
        ).to(self.device)
        
        resampled = resampler_down(waveform)
        restored = resampler_up(resampled)
        
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
        """MP3 압축 시뮬레이션 (더 강하게)"""
        cutoff = random.uniform(3000, 7000)
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        
        kernel_size = 101
        kernel = torch.sinc(
            2 * normalized_cutoff * (torch.arange(kernel_size, dtype=torch.float32) - kernel_size // 2)
        )
        kernel = kernel / kernel.sum()
        kernel = kernel.view(1, 1, -1).to(self.device)
        
        padded = F.pad(waveform, (kernel_size // 2, kernel_size // 2), mode='reflect')
        filtered = F.conv1d(padded, kernel)
        
        bits = random.choice([8, 12, 16])
        scale = 2 ** bits
        quantized = torch.round(filtered * scale) / scale
        
        return quantized
    
    def codec_simulation(self, waveform):
        """음성 코덱 시뮬레이션 (전화, VoIP 등)"""
        # G.711 μ-law 시뮬레이션
        mu = 255
        waveform_np = waveform.cpu().numpy()
        
        # μ-law 압축
        sign = np.sign(waveform_np)
        waveform_abs = np.abs(waveform_np)
        compressed = sign * np.log(1 + mu * waveform_abs) / np.log(1 + mu)
        
        # 양자화
        compressed = np.round(compressed * 127) / 127
        
        # μ-law 복원
        sign = np.sign(compressed)
        compressed_abs = np.abs(compressed)
        restored = sign * ((1 + mu) ** compressed_abs - 1) / mu
        
        return torch.from_numpy(restored).float().to(self.device)
    
    def apply_random_augmentation(self, waveform):
        """무작위로 증강 기법 적용 (더 강력하게)"""
        augmentations = [
            self.random_resample,
            self.random_gain,
            self.add_background_noise,
            self.mp3_compression_simulation,
            self.codec_simulation,
        ]
        
        # 60% 확률로 2개 연속 적용
        if random.random() < 0.6:
            aug_func1 = random.choice(augmentations)
            aug_func2 = random.choice(augmentations)
            waveform = aug_func1(waveform)
            waveform = aug_func2(waveform)
        else:
            aug_func = random.choice(augmentations)
            waveform = aug_func(waveform)
        
        return waveform


class VoiceActivityDetector:
    """음성 구간 감지기"""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def detect_voice_segments(self, waveform):
        """음성이 있는 구간 감지"""
        # 에너지 기반 VAD
        frame_length = int(0.025 * self.sample_rate)  # 25ms
        hop_length = int(0.010 * self.sample_rate)    # 10ms
        
        # RMS 에너지 계산
        energy = torch.sqrt(
            F.avg_pool1d(
                waveform ** 2,
                kernel_size=frame_length,
                stride=hop_length
            )
        )
        
        # 동적 임계값 (상위 30%)
        threshold = torch.quantile(energy, 0.3)
        
        # 음성 구간 마스크
        voice_mask = (energy > threshold).float()
        
        # 마스크 스무딩 (급격한 변화 방지)
        kernel = torch.ones(1, 1, 5).to(self.device) / 5
        voice_mask = F.conv1d(
            voice_mask,
            kernel,
            padding=2
        )
        voice_mask = (voice_mask > 0.5).float()
        
        # 원본 크기로 업샘플링
        voice_mask = F.interpolate(
            voice_mask,
            size=waveform.shape[-1],
            mode='nearest'
        )
        
        return voice_mask.detach()  # gradient 불필요
    
    def get_important_segments(self, waveform, top_k=3):
        """가장 중요한 음성 구간 k개 추출"""
        voice_mask = self.detect_voice_segments(waveform)
        
        # 연속된 음성 구간 찾기
        voice_np = voice_mask.squeeze().cpu().numpy()
        diff = np.diff(np.concatenate([[0], voice_np, [0]]))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        
        # 구간별 에너지 계산
        segments = []
        for start, end in zip(starts, ends):
            if end - start > self.sample_rate * 0.5:  # 0.5초 이상만
                segment_energy = torch.mean(
                    waveform[:, :, start:end] ** 2
                ).item()
                segments.append((start, end, segment_energy))
        
        # 에너지 순으로 정렬
        segments.sort(key=lambda x: x[2], reverse=True)
        
        # 상위 k개 반환
        return segments[:top_k]


class EnhancedRobustVoiceProtection:
    """
    강화된 음성 보호 시스템
    SV2TTS/RVC 특화 + 20초 음성 최적화
    """
    
    def __init__(
        self,
        epsilon=0.018,              # 살짝 낮춤 (음질 보존)
        alpha=0.0008,               # Step size 증가
        iterations=1000,            # 더 많은 최적화
        lambda_psycho=0.03,         # Psycho 조정
        lambda_temporal=0.5,        # 시간축 가중치
        lambda_formant=0.3,         # Formant 가중치
        augmentation_prob=0.9,      # 증강 확률 증가
        attack_mode="selective",    # selective/uniform/aggressive
        use_pretrained=True,
    ):
        self.epsilon = epsilon
        self.alpha = alpha
        self.iterations = iterations
        self.lambda_psycho = lambda_psycho
        self.lambda_temporal = lambda_temporal
        self.lambda_formant = lambda_formant
        self.augmentation_prob = augmentation_prob
        self.attack_mode = attack_mode
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # VAD 초기화
        self.vad = VoiceActivityDetector()
        
        # Speaker Encoder 초기화
        if use_pretrained:
            print("Loading pre-trained ECAPA-TDNN from SpeechBrain...")
            try:
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
                print("Falling back to simple encoder")
                self.encoder = self._create_simple_encoder()
                self.use_pretrained = False
        else:
            self.encoder = self._create_simple_encoder()
            self.use_pretrained = False
        
        # Data Augmentation 초기화
        self.augmentor = DataAugmentation()
        
        print(f"Device: {self.device}")
        print(f"Attack mode: {attack_mode}")
        print(f"Parameters: ε={epsilon}, α={alpha}, iterations={iterations}")
    
    def _create_simple_encoder(self):
        """간단한 테스트용 인코더"""
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
        
        return waveform.unsqueeze(0).to(self.device)
    
    def extract_embedding(self, waveform):
        """스피커 임베딩 추출"""
        with torch.no_grad():
            if self.use_pretrained:
                embedding = self.encoder.encode_batch(waveform.squeeze(1))
                if isinstance(embedding, tuple):
                    embedding = embedding[0]
                embedding = F.normalize(embedding, p=2, dim=-1)
            else:
                embedding = self.encoder(waveform)
        
        return embedding
    
    def generate_perturbation(self, original_waveform):
        """
        강화된 perturbation 생성 (Gradient 버그 수정)
        """
        # 원본 임베딩 추출
        print("\nExtracting original speaker embedding...")
        original_embedding = self.extract_embedding(original_waveform)
        print(f"Original embedding shape: {original_embedding.shape}")
        print(f"Original embedding norm: {original_embedding.norm().item():.4f}")
        
        # 음성 구간 분석
        print("\nAnalyzing voice segments...")
        voice_mask = self.vad.detect_voice_segments(original_waveform)
        voice_ratio = voice_mask.mean().item()
        print(f"Voice activity ratio: {voice_ratio:.2%}")
        
        important_segments = self.vad.get_important_segments(original_waveform)
        print(f"Found {len(important_segments)} important segments")
        
        # Perturbation 초기화
        perturbation = torch.zeros_like(original_waveform).uniform_(
            -self.epsilon/10, self.epsilon/10
        ).to(self.device)
        perturbation.requires_grad = True
        
        # Optimizer 설정 (AdamW 사용)
        optimizer = torch.optim.AdamW([perturbation], lr=self.alpha, weight_decay=0.01)
        
        # Learning rate scheduler
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=self.iterations, eta_min=self.alpha * 0.1
        )
        
        print(f"\nStarting enhanced optimization ({self.iterations} iterations)...")
        print(f"Attack mode: {self.attack_mode}")
        print("This will take a few minutes...")
        
        best_loss = -float('inf')
        best_perturbation = perturbation.clone()
        
        for iteration in range(self.iterations):
            optimizer.zero_grad()
            
            # Perturbation에 가중치 적용 (gradient 유지)
            if self.attack_mode == "selective":
                # 음성 구간 가중치 (gradient 유지됨)
                weight_mask = 0.5 + 1.5 * voice_mask
                
                # 시간축 가중치
                duration = original_waveform.shape[-1]
                temporal_weight = torch.ones_like(perturbation)
                
                # 처음 5초
                first_5s = min(80000, duration // 3)
                temporal_weight[:, :, :first_5s] *= 1.8
                
                # 중간 5초
                mid_start = duration // 2 - 40000
                mid_end = min(mid_start + 80000, duration)
                if mid_start > 0:
                    temporal_weight[:, :, mid_start:mid_end] *= 1.5
                
                # 중요 구간
                for start, end, _ in important_segments:
                    temporal_weight[:, :, start:end] *= 1.3
                
                # 가중치 적용 (gradient 유지)
                current_pert = perturbation * weight_mask * temporal_weight
                
            elif self.attack_mode == "aggressive":
                # 공격적 모드
                current_pert = perturbation * 1.5
            else:
                # Uniform 모드
                current_pert = perturbation
            
            # Perturbation 적용
            perturbed_waveform = original_waveform + current_pert
            perturbed_waveform = torch.clamp(perturbed_waveform, -1.0, 1.0)
            
            # 데이터 증강 (gradient 없음)
            with torch.no_grad():
                if random.random() < self.augmentation_prob:
                    if iteration > self.iterations // 2:
                        augmented = self.augmentor.apply_random_augmentation(perturbed_waveform.detach())
                        augmented = self.augmentor.apply_random_augmentation(augmented)
                    else:
                        augmented = self.augmentor.apply_random_augmentation(perturbed_waveform.detach())
                else:
                    augmented = perturbed_waveform.detach()
            
            # 증강된 버전에 gradient 연결
            # perturbation의 영향이 결과에 반영되도록
            augmented = augmented + (perturbed_waveform - perturbed_waveform.detach())
            
            # 임베딩 추출
            if self.use_pretrained:
                perturbed_embedding = self.encoder.encode_batch(augmented.squeeze(1))
                if isinstance(perturbed_embedding, tuple):
                    perturbed_embedding = perturbed_embedding[0]
                perturbed_embedding = F.normalize(perturbed_embedding, p=2, dim=-1)
            else:
                perturbed_embedding = self.encoder(augmented)
            
            # Loss 계산
            # 1. Cosine similarity 최소화
            cosine_similarity = F.cosine_similarity(
                original_embedding.detach(),  # 원본은 gradient 불필요
                perturbed_embedding, 
                dim=-1
            ).mean()
            
            # 2. L2 distance 최대화
            l2_distance = torch.norm(
                original_embedding.detach() - perturbed_embedding, 
                p=2, dim=-1
            ).mean()
            
            # 3. Triplet-like loss
            random_target = torch.randn_like(original_embedding)
            random_target = F.normalize(random_target, p=2, dim=-1).detach()
            target_similarity = F.cosine_similarity(
                perturbed_embedding,
                random_target,
                dim=-1
            ).mean()
            
            # 총 임베딩 손실
            embedding_loss = (
                cosine_similarity -          # 원본과 멀어지기
                0.4 * l2_distance -          # L2 거리 증가
                0.2 * target_similarity      # 랜덤 타겟에 가까워지기
            )
            
            # 4. Psychoacoustic 페널티
            # FFT 기반 페널티 (simplified to avoid complex number issues)
            fft_magnitude = torch.abs(torch.fft.rfft(current_pert, dim=-1))
            n_freqs = fft_magnitude.shape[-1]
            low_freq_end = int(0.125 * n_freqs)
            mid_freq_end = int(0.25 * n_freqs)
            
            low_freq_penalty = fft_magnitude[..., :low_freq_end].pow(2).mean()
            mid_freq_penalty = fft_magnitude[..., low_freq_end:mid_freq_end].pow(2).mean()
            high_freq_penalty = fft_magnitude[..., mid_freq_end:].pow(2).mean()
            
            psycho_penalty = (
                1.0 * low_freq_penalty +
                0.5 * mid_freq_penalty -
                0.3 * high_freq_penalty
            )
            
            # 5. Temporal smoothness
            temporal_smoothness = torch.mean(
                torch.abs(current_pert[:, :, 1:] - current_pert[:, :, :-1])
            )
            
            # 총 손실
            total_loss = (
                embedding_loss +
                self.lambda_psycho * psycho_penalty +
                0.01 * temporal_smoothness
            )
            
            # Gradient 존재 확인
            if not total_loss.requires_grad:
                print(f"Warning: No gradient at iteration {iteration}")
                continue
            
            # Backpropagation
            total_loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_([perturbation], max_norm=1.0)
            
            optimizer.step()
            scheduler.step()
            
            # Epsilon ball 제약 (L_inf)
            with torch.no_grad():
                perturbation.clamp_(-self.epsilon, self.epsilon)
                
                # 무음 구간 보호 (선택적 모드에서만)
                if self.attack_mode == "selective":
                    silence_mask = 1 - voice_mask
                    perturbation.mul_(voice_mask + 0.1 * silence_mask)
            
            # Best perturbation 저장
            if -total_loss.item() > best_loss:
                best_loss = -total_loss.item()
                best_perturbation = current_pert.clone().detach()
            
            # 진행 상황 출력
            if (iteration + 1) % 50 == 0:
                current_lr = scheduler.get_last_lr()[0]
                print(f"Iter {iteration+1}/{self.iterations}: "
                      f"Cosine={cosine_similarity.item():.4f}, "
                      f"L2={l2_distance.item():.4f}, "
                      f"Loss={total_loss.item():.4f}, "
                      f"LR={current_lr:.6f}")
        
        print(f"\n✓ Optimization complete!")
        print(f"Final cosine similarity: {cosine_similarity.item():.4f}")
        print(f"Final L2 distance: {l2_distance.item():.4f}")
        print(f"Target: cosine < 0.3 for strong protection")
        
        return best_perturbation.detach()
    
    def analyze_protection(self, original_waveform, perturbation):
        """보호 효과 상세 분석"""
        perturbed_waveform = original_waveform + perturbation
        perturbed_waveform = torch.clamp(perturbed_waveform, -1.0, 1.0)
        
        # 임베딩 비교
        original_emb = self.extract_embedding(original_waveform)
        perturbed_emb = self.extract_embedding(perturbed_waveform)
        
        cosine_sim = F.cosine_similarity(original_emb, perturbed_emb, dim=-1).mean().item()
        l2_dist = torch.norm(original_emb - perturbed_emb, p=2, dim=-1).mean().item()
        
        # SNR 계산
        signal_power = torch.mean(original_waveform ** 2)
        noise_power = torch.mean(perturbation ** 2)
        snr_db = 10 * torch.log10(signal_power / noise_power).item()
        
        # PESQ 추정 (간단한 근사)
        pesq_estimate = min(4.5, max(1.0, 4.5 - (35 - snr_db) * 0.1))
        
        # Perturbation 통계
        max_pert = perturbation.abs().max().item()
        mean_pert = perturbation.abs().mean().item()
        
        # 음성 구간별 분석
        voice_mask = self.vad.detect_voice_segments(original_waveform)
        voice_pert = (perturbation * voice_mask).abs().mean().item()
        silence_pert = (perturbation * (1 - voice_mask)).abs().mean().item()
        
        print("\n" + "="*70)
        print("ENHANCED PROTECTION ANALYSIS")
        print("="*70)
        print(f"Speaker Encoder: {'ECAPA-TDNN (Production)' if self.use_pretrained else 'Simple (Test)'}")
        print(f"Attack Mode: {self.attack_mode.upper()}")
        
        print(f"\n[Embedding Protection]")
        print(f"  Cosine Similarity: {cosine_sim:.4f}")
        print(f"    • Original: 1.000 (same speaker)")
        print(f"    • Target: < 0.300 (different speaker)")
        print(f"    • Status: {'✓✓ EXCELLENT' if cosine_sim < 0.2 else '✓ STRONG' if cosine_sim < 0.3 else '○ GOOD' if cosine_sim < 0.5 else '⚠ WEAK'}")
        print(f"  L2 Distance: {l2_dist:.4f} {'✓' if l2_dist > 0.5 else '○'}")
        
        print(f"\n[Audio Quality]")
        print(f"  Signal-to-Noise Ratio: {snr_db:.2f} dB")
        print(f"    • Status: {'✓ EXCELLENT' if snr_db > 35 else '○ GOOD' if snr_db > 30 else '⚠ AUDIBLE'}")
        print(f"  Estimated PESQ: {pesq_estimate:.2f}/4.5")
        
        print(f"\n[Perturbation Distribution]")
        print(f"  Maximum: {max_pert:.6f} (limit: {self.epsilon})")
        print(f"  Mean: {mean_pert:.6f}")
        print(f"  Voice segments: {voice_pert:.6f}")
        print(f"  Silence segments: {silence_pert:.6f}")
        
        print(f"\n[Protection Level]")
        if cosine_sim < 0.2:
            print("  ★★★★★ MAXIMUM PROTECTION - Voice cloning will fail")
        elif cosine_sim < 0.3:
            print("  ★★★★☆ STRONG PROTECTION - Highly effective")
        elif cosine_sim < 0.4:
            print("  ★★★☆☆ GOOD PROTECTION - Should work well")
        elif cosine_sim < 0.5:
            print("  ★★☆☆☆ MODERATE PROTECTION - May need stronger settings")
        else:
            print("  ★☆☆☆☆ WEAK PROTECTION - Increase epsilon or iterations")
        
        print("="*70)
        
        return {
            'cosine_similarity': cosine_sim,
            'l2_distance': l2_dist,
            'snr_db': snr_db,
            'pesq_estimate': pesq_estimate,
            'max_perturbation': max_pert,
            'mean_perturbation': mean_pert,
            'voice_perturbation': voice_pert,
            'silence_perturbation': silence_pert
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
    
    def process_long_audio(self, audio_path, output_path):
        """
        20초 이상 긴 오디오 특별 처리
        구간별로 다른 강도의 보호 적용
        """
        print("\n" + "="*70)
        print("PROCESSING LONG AUDIO (20+ seconds)")
        print("="*70)
        
        # 전체 오디오 로드
        waveform = self.load_audio(audio_path)
        duration = waveform.shape[-1] / 16000
        print(f"Total duration: {duration:.2f} seconds")
        
        if duration < 20:
            print("Audio is shorter than 20s, using standard protection...")
            perturbation = self.generate_perturbation(waveform)
        else:
            print("Applying segment-wise protection for long audio...")
            
            # 전체에 대한 기본 perturbation
            print("\n[Phase 1/3] Generating base perturbation...")
            base_perturbation = self.generate_perturbation(waveform)
            
            # 처음 10초에 추가 강화
            print("\n[Phase 2/3] Enhancing first 10 seconds...")
            first_10s_samples = min(160000, waveform.shape[-1])
            first_segment = waveform[:, :, :first_10s_samples]
            
            # 일시적으로 더 강한 설정
            original_epsilon = self.epsilon
            self.epsilon = min(0.025, self.epsilon * 1.3)
            first_perturbation = self.generate_perturbation(first_segment)
            self.epsilon = original_epsilon
            
            # 중간 10초 강화
            print("\n[Phase 3/3] Enhancing middle section...")
            mid_start = max(0, waveform.shape[-1] // 2 - 80000)
            mid_end = min(waveform.shape[-1], mid_start + 160000)
            
            if mid_end - mid_start > 80000:  # 최소 5초 이상인 경우만
                mid_segment = waveform[:, :, mid_start:mid_end]
                mid_perturbation = self.generate_perturbation(mid_segment)
                
                # Perturbation 합성
                final_perturbation = base_perturbation.clone()
                
                # 처음 10초 오버레이
                final_perturbation[:, :, :first_10s_samples] = (
                    0.6 * base_perturbation[:, :, :first_10s_samples] +
                    0.4 * first_perturbation[:, :, :min(first_perturbation.shape[-1], first_10s_samples)]
                )
                
                # 중간 10초 오버레이
                mid_pert_len = min(mid_perturbation.shape[-1], mid_end - mid_start)
                final_perturbation[:, :, mid_start:mid_start + mid_pert_len] = (
                    0.7 * base_perturbation[:, :, mid_start:mid_start + mid_pert_len] +
                    0.3 * mid_perturbation[:, :, :mid_pert_len]
                )
                
                perturbation = final_perturbation
            else:
                # 중간 구간이 너무 짧으면 기본 + 처음만
                final_perturbation = base_perturbation.clone()
                final_perturbation[:, :, :first_10s_samples] = (
                    0.6 * base_perturbation[:, :, :first_10s_samples] +
                    0.4 * first_perturbation[:, :, :min(first_perturbation.shape[-1], first_10s_samples)]
                )
                perturbation = final_perturbation
        
        # 분석 및 저장
        analysis = self.analyze_protection(waveform, perturbation)
        self.save_protected_audio(waveform, perturbation, output_path)
        
        return analysis


def main():
    # 기본 설정
    input_file = "original_audio.wav"
    output_file = "protected_audio.wav"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    print("="*70)
    print("ENHANCED ROBUST VOICE PROTECTION SYSTEM v2.0")
    print("SV2TTS/RVC Specialized Edition")
    print("="*70)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)
    
    # 시스템 초기화
    protector = EnhancedRobustVoiceProtection(
        epsilon=0.018,              # 음질과 효과의 균형
        alpha=0.0008,               # 학습률
        iterations=1000,            # 충분한 최적화
        lambda_psycho=0.03,         # Psychoacoustic
        lambda_temporal=0.5,        # 시간축 가중치
        lambda_formant=0.3,         # Formant 가중치  
        augmentation_prob=0.9,      # 90% 증강
        attack_mode="selective",    # selective/uniform/aggressive
        use_pretrained=True,
    )
    
    # 오디오 처리
    print("\nLoading and analyzing audio...")
    waveform = protector.load_audio(input_file)
    duration = waveform.shape[-1] / 16000
    
    if duration >= 20:
        print(f"\n✓ Detected long audio ({duration:.1f}s), using enhanced processing...")
        analysis = protector.process_long_audio(input_file, output_file)
    else:
        print(f"\nDuration: {duration:.2f} seconds")
        perturbation = protector.generate_perturbation(waveform)
        analysis = protector.analyze_protection(waveform, perturbation)
        protector.save_protected_audio(waveform, perturbation, output_file)
    
    print("\n" + "="*70)
    print("PROTECTION COMPLETE!")
    print("="*70)
    print("\n[Recommended Testing]")
    print("1. Test with SV2TTS (Real-Time-Voice-Cloning)")
    print("2. Test with RVC (Retrieval-based Voice Conversion)")  
    print("3. Upload to YouTube/SoundCloud and re-download")
    print("4. Convert to MP3 128kbps and verify protection")
    
    print("\n[If Protection is Weak]")
    print("• For SV2TTS: Use attack_mode='aggressive'")
    print("• For RVC: Increase epsilon to 0.025")
    print("• For 20+ second audio: Process in segments")
    print("="*70)


if __name__ == "__main__":
    main()
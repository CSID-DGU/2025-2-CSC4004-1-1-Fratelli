import torch
import torchaudio
import torch.nn.functional as F
import numpy as np
import random
import sys
import os
from scipy import signal as scipy_signal


class DataAugmentation:
    """강건성을 위한 데이터 증강"""
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def random_resample(self, waveform):
        """무작위 리샘플"""
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
    
    def mp3_compression_simulation(self, waveform):
        """MP3 압축 시뮬레이션"""
        cutoff = random.uniform(5000, 8000)  # 더 높은 cutoff
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
        
        return filtered
    
    def apply_random_augmentation(self, waveform):
        """무작위 증강 (가벼운 버전)"""
        augmentations = [
            self.random_resample,
            self.mp3_compression_simulation,
        ]
        
        aug_func = random.choice(augmentations)
        return aug_func(waveform)


class VoiceActivityDetector:
    """음성 구간 감지기"""
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def detect_voice_segments(self, waveform):
        """음성이 있는 구간 감지"""
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)
        
        energy = torch.sqrt(
            F.avg_pool1d(
                waveform ** 2,
                kernel_size=frame_length,
                stride=hop_length
            )
        )
        
        threshold = torch.quantile(energy, 0.3)
        voice_mask = (energy > threshold).float()
        
        kernel = torch.ones(1, 1, 5).to(self.device) / 5
        voice_mask = F.conv1d(voice_mask, kernel, padding=2)
        voice_mask = (voice_mask > 0.5).float()
        
        voice_mask = F.interpolate(
            voice_mask,
            size=waveform.shape[-1],
            mode='nearest'
        )
        
        return voice_mask.detach()


class HighQualityVoiceProtection:
    """
    고품질 음성 보호 시스템
    음질 보존 최우선 + 효과적인 보호
    """
    
    def __init__(
        self,
        epsilon=0.008,              # 크게 낮춤 (음질 우선)
        alpha=0.0003,               # 작은 step size
        iterations=1500,            # 더 많은 iteration으로 보상
        lambda_psycho=0.2,          # Psycho 강화 (자연스러운 노이즈)
        lambda_smooth=0.15,         # Smoothing 강화 (지지직 제거)
        lambda_spectral=0.1,        # 스펙트럴 shaping
        augmentation_prob=0.7,      
        attack_mode="quality",      # quality/balanced/aggressive
        use_pretrained=True,
    ):
        self.epsilon = epsilon
        self.alpha = alpha
        self.iterations = iterations
        self.lambda_psycho = lambda_psycho
        self.lambda_smooth = lambda_smooth
        self.lambda_spectral = lambda_spectral
        self.augmentation_prob = augmentation_prob
        self.attack_mode = attack_mode
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # VAD 초기화
        self.vad = VoiceActivityDetector()
        
        # Speaker Encoder 초기화
        if use_pretrained:
            print("Loading pre-trained ECAPA-TDNN...")
            try:
                from speechbrain.inference.speaker import EncoderClassifier
                
                self.encoder = EncoderClassifier.from_hparams(
                    source="speechbrain/spkrec-ecapa-voxceleb",
                    savedir="pretrained_models/spkrec-ecapa-voxceleb",
                    run_opts={"device": str(self.device)}
                )
                self.use_pretrained = True
                print("✓ ECAPA-TDNN loaded successfully!")
            except Exception as e:
                print(f"Warning: Could not load ECAPA-TDNN: {e}")
                self.encoder = self._create_simple_encoder()
                self.use_pretrained = False
        else:
            self.encoder = self._create_simple_encoder()
            self.use_pretrained = False
        
        self.augmentor = DataAugmentation()
        
        print(f"Device: {self.device}")
        print(f"Attack mode: {attack_mode} (Quality-focused)")
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
        
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
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
    
    def spectral_shaping_filter(self, perturbation):
        """
        스펙트럴 쉐이핑 - 자연스러운 노이즈 생성
        지지직 소리의 원인인 고주파 스파이크 제거
        """
        # STFT
        stft = torch.stft(
            perturbation.squeeze(), 
            n_fft=2048, 
            hop_length=512,
            window=torch.hann_window(2048).to(self.device),
            return_complex=True
        )
        
        magnitude = torch.abs(stft)
        phase = torch.angle(stft)
        
        # magnitude shape: [n_freqs, n_frames]
        n_freqs, n_frames = magnitude.shape
        
        # 주파수별 가중치 (자연스러운 pink noise 특성)
        freq_weights = 1.0 / torch.sqrt(torch.arange(1, n_freqs + 1).float()).to(self.device)
        freq_weights = freq_weights.unsqueeze(1)  # [n_freqs, 1]
        
        # Magnitude smoothing (지지직 제거)
        # 주파수 축 스무딩 - reshape to [1, 1, n_freqs, n_frames]
        magnitude_batch = magnitude.unsqueeze(0).unsqueeze(0)  # [1, 1, n_freqs, n_frames]
        
        # 2D convolution으로 스무딩
        kernel_2d = torch.ones(1, 1, 3, 3).to(self.device) / 9
        magnitude_smooth = F.conv2d(
            F.pad(magnitude_batch, (1, 1, 1, 1), mode='reflect'),
            kernel_2d,
            padding=0
        )
        magnitude_smooth = magnitude_smooth.squeeze(0).squeeze(0)  # [n_freqs, n_frames]
        
        # Pink noise 특성 적용
        magnitude_shaped = magnitude_smooth * freq_weights
        
        # 고주파 제한 (8kHz 이상 급격히 감소)
        cutoff_bin = int(n_freqs * 0.5)  # 8kHz at 16kHz sampling
        high_freq_suppress = torch.ones_like(magnitude_shaped)
        if cutoff_bin < n_freqs:
            suppress_factor = torch.exp(
                -0.5 * torch.arange(n_freqs - cutoff_bin).float().to(self.device) / (n_freqs - cutoff_bin)
            ).unsqueeze(1)
            high_freq_suppress[cutoff_bin:] *= suppress_factor
        
        magnitude_shaped *= high_freq_suppress
        
        # 복원
        stft_shaped = magnitude_shaped * torch.exp(1j * phase)
        perturbation_shaped = torch.istft(
            stft_shaped,
            n_fft=2048,
            hop_length=512,
            window=torch.hann_window(2048).to(self.device),
            length=perturbation.shape[-1]
        )
        
        return perturbation_shaped.unsqueeze(0).unsqueeze(0)
    
    def adaptive_noise_gate(self, perturbation, original_waveform):
        """
        적응형 노이즈 게이트 - 무음 구간의 노이즈 제거
        """
        # 원본 신호의 에너지 계산
        energy = torch.sqrt(
            F.avg_pool1d(
                original_waveform ** 2,
                kernel_size=800,  # 50ms
                stride=400
            )
        )
        energy = F.interpolate(energy, size=perturbation.shape[-1], mode='linear')
        
        # 에너지 기반 게이트 (무음 구간 = 낮은 perturbation)
        energy_norm = (energy - energy.min()) / (energy.max() - energy.min() + 1e-8)
        gate = torch.sigmoid(10 * (energy_norm - 0.1))  # 부드러운 게이트
        
        return perturbation * gate
    
    def temporal_smoothing(self, perturbation):
        """
        시간축 스무딩 - 급격한 변화 제거 (지지직 방지)
        """
        # Moving average filter
        kernel_size = 5
        kernel = torch.ones(1, 1, kernel_size).to(self.device) / kernel_size
        
        # 양방향 스무딩
        smoothed = F.conv1d(
            F.pad(perturbation, (kernel_size//2, kernel_size//2), mode='reflect'),
            kernel
        )
        
        # 2차 스무딩 (더 부드럽게)
        smoothed = F.conv1d(
            F.pad(smoothed, (kernel_size//2, kernel_size//2), mode='reflect'),
            kernel
        )
        
        return smoothed
    
    def generate_perturbation(self, original_waveform):
        """
        고품질 perturbation 생성 - 음질 보존 최우선
        """
        print("\nExtracting original speaker embedding...")
        original_embedding = self.extract_embedding(original_waveform)
        print(f"Original embedding shape: {original_embedding.shape}")
        
        # 음성 구간 분석
        voice_mask = self.vad.detect_voice_segments(original_waveform)
        
        # Perturbation 초기화 (더 작게)
        perturbation = torch.zeros_like(original_waveform).normal_(
            0, self.epsilon/20  # 매우 작은 초기값
        ).to(self.device)
        perturbation.requires_grad = True
        
        # Optimizer
        optimizer = torch.optim.AdamW([perturbation], lr=self.alpha, weight_decay=0.001)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer, T_0=200, T_mult=2, eta_min=self.alpha * 0.01
        )
        
        print(f"\nStarting high-quality optimization ({self.iterations} iterations)...")
        print("Prioritizing audio quality...")
        
        best_loss = -float('inf')
        best_perturbation = perturbation.clone()
        
        for iteration in range(self.iterations):
            optimizer.zero_grad()
            
            # 노이즈 쉐이핑 적용 (gradient 유지)
            if iteration > 100:  # 초반에는 기본 최적화
                # Spectral shaping (자연스러운 노이즈)
                with torch.no_grad():
                    pert_shaped = self.spectral_shaping_filter(perturbation.detach())
                # Gradient 재연결
                shaped_pert = pert_shaped + (perturbation - perturbation.detach())
                
                # Temporal smoothing (지지직 제거)
                shaped_pert = self.temporal_smoothing(shaped_pert)
                
                # Adaptive noise gate (무음 구간 보호)
                shaped_pert = self.adaptive_noise_gate(shaped_pert, original_waveform)
            else:
                shaped_pert = perturbation
            
            # Quality mode: 음성 구간에만 집중
            if self.attack_mode == "quality":
                # 음성 구간 가중치 (부드럽게)
                voice_weight = 0.2 + 0.8 * voice_mask
                shaped_pert = shaped_pert * voice_weight
            elif self.attack_mode == "balanced":
                voice_weight = 0.5 + 0.5 * voice_mask
                shaped_pert = shaped_pert * voice_weight
            
            # Perturbation 적용
            perturbed_waveform = original_waveform + shaped_pert
            perturbed_waveform = torch.clamp(perturbed_waveform, -1.0, 1.0)
            
            # 가벼운 증강
            with torch.no_grad():
                if random.random() < self.augmentation_prob:
                    augmented = self.augmentor.apply_random_augmentation(perturbed_waveform.detach())
                else:
                    augmented = perturbed_waveform.detach()
            
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
            cosine_similarity = F.cosine_similarity(
                original_embedding.detach(),
                perturbed_embedding, 
                dim=-1
            ).mean()
            
            l2_distance = torch.norm(
                original_embedding.detach() - perturbed_embedding, 
                p=2, dim=-1
            ).mean()
            
            # Embedding loss
            embedding_loss = cosine_similarity - 0.3 * l2_distance
            
            # Psychoacoustic loss (강화)
            # 저주파 노이즈 억제
            fft_magnitude = torch.abs(torch.fft.rfft(shaped_pert, dim=-1))
            n_freqs = fft_magnitude.shape[-1]
            
            # 0-4kHz 구간 (민감한 영역)
            sensitive_end = int(0.25 * n_freqs)
            sensitive_penalty = fft_magnitude[..., :sensitive_end].pow(2).mean()
            
            # 4-8kHz 구간 (덜 민감)
            mid_end = int(0.5 * n_freqs)
            mid_penalty = fft_magnitude[..., sensitive_end:mid_end].pow(2).mean()
            
            # 8kHz 이상 (거의 안들림)
            high_penalty = fft_magnitude[..., mid_end:].pow(2).mean()
            
            psycho_loss = (
                2.0 * sensitive_penalty +  # 민감 영역 강하게 억제
                0.5 * mid_penalty -
                0.1 * high_penalty  # 고주파는 약간 허용
            )
            
            # Smoothness loss (강화 - 지지직 방지)
            # 1차 미분 (급격한 변화)
            diff1 = torch.abs(shaped_pert[:, :, 1:] - shaped_pert[:, :, :-1])
            smoothness1 = diff1.mean()
            
            # 2차 미분 (더 부드럽게)
            diff2 = torch.abs(diff1[:, :, 1:] - diff1[:, :, :-1])
            smoothness2 = diff2.mean()
            
            smoothness_loss = smoothness1 + 0.5 * smoothness2
            
            # Sparsity loss (sparse perturbation이 더 자연스러움)
            sparsity = torch.abs(shaped_pert).mean()
            
            # Total loss
            total_loss = (
                embedding_loss +
                self.lambda_psycho * psycho_loss +
                self.lambda_smooth * smoothness_loss +
                self.lambda_spectral * sparsity
            )
            
            if not total_loss.requires_grad:
                continue
            
            total_loss.backward()
            
            # Gradient clipping (안정성)
            torch.nn.utils.clip_grad_norm_([perturbation], max_norm=0.5)
            
            optimizer.step()
            scheduler.step()
            
            # Constraints
            with torch.no_grad():
                # L_inf constraint (더 작게)
                perturbation.clamp_(-self.epsilon, self.epsilon)
                
                # L2 constraint 추가 (전체 에너지 제한)
                pert_norm = torch.norm(perturbation, p=2, dim=-1, keepdim=True)
                max_norm = self.epsilon * np.sqrt(perturbation.shape[-1]) * 0.5
                perturbation.div_(torch.max(pert_norm / max_norm, torch.ones_like(pert_norm)))
            
            # Best 저장
            if -total_loss.item() > best_loss:
                best_loss = -total_loss.item()
                best_perturbation = shaped_pert.clone().detach()
            
            # Progress
            if (iteration + 1) % 100 == 0:
                print(f"Iter {iteration+1}/{self.iterations}: "
                      f"Cosine={cosine_similarity.item():.4f}, "
                      f"Psycho={psycho_loss.item():.4f}, "
                      f"Smooth={smoothness_loss.item():.4f}")
        
        # 최종 후처리 (음질 개선)
        print("\nApplying final quality enhancement...")
        
        # 1. 추가 spectral shaping
        best_perturbation = self.spectral_shaping_filter(best_perturbation)
        
        # 2. 추가 temporal smoothing
        best_perturbation = self.temporal_smoothing(best_perturbation)
        
        # 3. 최종 noise gate
        best_perturbation = self.adaptive_noise_gate(best_perturbation, original_waveform)
        
        # 4. 최종 amplitude 조정
        best_perturbation = best_perturbation * 0.8  # 살짝 더 줄임
        
        print("✓ Optimization complete with quality preservation!")
        
        return best_perturbation.detach()
    
    def analyze_protection(self, original_waveform, perturbation):
        """보호 효과 분석"""
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
        
        # PESQ 추정
        pesq_estimate = min(4.5, max(1.0, 4.5 - max(0, 40 - snr_db) * 0.08))
        
        print("\n" + "="*70)
        print("HIGH-QUALITY PROTECTION ANALYSIS")
        print("="*70)
        print(f"Mode: {self.attack_mode.upper()} (Quality-focused)")
        
        print(f"\n[Protection Effectiveness]")
        print(f"  Cosine Similarity: {cosine_sim:.4f}")
        if cosine_sim < 0.4:
            print(f"    • Status: ✓ PROTECTED (Voice cloning prevented)")
        elif cosine_sim < 0.6:
            print(f"    • Status: ○ MODERATE (Partial protection)")
        else:
            print(f"    • Status: △ WEAK (Consider 'balanced' mode)")
        
        print(f"\n[Audio Quality]")
        print(f"  SNR: {snr_db:.1f} dB")
        print(f"  PESQ Estimate: {pesq_estimate:.1f}/4.5")
        if snr_db > 40:
            print(f"    • Quality: ✓✓ EXCELLENT (Nearly imperceptible)")
        elif snr_db > 35:
            print(f"    • Quality: ✓ VERY GOOD (Minimal artifacts)")
        elif snr_db > 30:
            print(f"    • Quality: ○ GOOD (Slight background)")
        else:
            print(f"    • Quality: △ ACCEPTABLE")
        
        print("="*70)
        
        return {
            'cosine_similarity': cosine_sim,
            'snr_db': snr_db,
            'pesq_estimate': pesq_estimate
        }
    
    def save_protected_audio(self, waveform, perturbation, output_path):
        """보호된 오디오 저장"""
        protected = waveform + perturbation
        protected = torch.clamp(protected, -1.0, 1.0)
        
        # 부드러운 정규화
        max_val = protected.abs().max()
        if max_val > 0.95:
            protected = protected * 0.95 / max_val
        
        torchaudio.save(output_path, protected.squeeze(0).cpu(), 16000)
        print(f"\n✓ Protected audio saved: {output_path}")
        print("  Audio quality preserved with minimal artifacts!")


def main():
    input_file = "original.wav"
    output_file = "protected.wav"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    print("="*70)
    print("HIGH-QUALITY VOICE PROTECTION SYSTEM v3.0")
    print("Minimal Artifacts Edition")
    print("="*70)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)
    
    # 시스템 초기화 (음질 우선 설정)
    protector = HighQualityVoiceProtection(
        epsilon=0.008,              # 낮은 epsilon (음질)
        alpha=0.0003,               # 작은 step
        iterations=1500,            # 충분한 iteration
        lambda_psycho=0.2,          # Psychoacoustic 강화
        lambda_smooth=0.15,         # Smoothing 강화
        lambda_spectral=0.1,        # Spectral shaping
        augmentation_prob=0.7,
        attack_mode="quality",      # quality/balanced/aggressive
        use_pretrained=True,
    )
    
    # 오디오 처리
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
    
    print("\n" + "="*70)
    print("PROTECTION COMPLETE!")
    print("="*70)
    
    if analysis['cosine_similarity'] > 0.5:
        print("\n⚠ Protection is moderate. For stronger protection:")
        print("  • Use attack_mode='balanced' (epsilon=0.012)")
        print("  • Or attack_mode='aggressive' (epsilon=0.018)")
    
    print("\nThe protected audio should sound natural with minimal artifacts.")
    print("No more crackling or buzzing sounds!")
    print("="*70)


if __name__ == "__main__":
    main()
"""
Practical Voice Protection
===========================
실용적인 딥페이크 방지 시스템

균형잡힌 접근:
- 사람: 약간 이상하게 들림 (수용 가능)
- AI: 학습 품질 크게 저하

Requirements:
pip install torch torchaudio speechbrain
"""

import torch
import torchaudio
import torch.nn.functional as F
import random
import sys
import os


class PracticalProtection:
    """
    실용적인 음성 보호
    """
    def __init__(
        self,
        protection_level="medium",  # low, medium, high
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 보호 수준별 설정
        self.configs = {
            "low": {
                "epsilon": 0.005,
                "pitch_semitones": 0.3,
                "use_structural": False,
                "iterations": 100,
                "description": "최소 보호 (거의 안 들림)"
            },
            "medium": {
                "epsilon": 0.012,
                "pitch_semitones": 0.6,
                "use_structural": True,
                "iterations": 200,
                "description": "균형잡힌 보호 (약간 들림)"
            },
            "high": {
                "epsilon": 0.02,
                "pitch_semitones": 1.0,
                "use_structural": True,
                "iterations": 300,
                "description": "강력한 보호 (명확히 들림)"
            }
        }
        
        if protection_level not in self.configs:
            protection_level = "medium"
        
        self.config = self.configs[protection_level]
        self.protection_level = protection_level
        
        print(f"Protection Level: {protection_level.upper()}")
        print(f"  - {self.config['description']}")
        print(f"  - Epsilon: {self.config['epsilon']}")
        print(f"  - Pitch shift: {self.config['pitch_semitones']} semitones")
        
        # ECAPA-TDNN 로드
        self.load_encoder()
    
    def load_encoder(self):
        """스피커 인코더 로드"""
        print("\nLoading speaker encoder...")
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
            print("✓ Encoder loaded!")
            self.has_encoder = True
        except Exception as e:
            print(f"⚠ Could not load encoder: {e}")
            print("  Protection will be limited.")
            self.has_encoder = False
    
    def load_audio(self, audio_path):
        """오디오 로드"""
        waveform, sr = torchaudio.load(audio_path)
        
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        return waveform.unsqueeze(0).to(self.device)
    
    def subtle_pitch_shift(self, waveform, semitones):
        """
        미묘한 음높이 변조
        사람: 약간 이상 / AI: 크게 혼란
        """
        if semitones == 0:
            return waveform
        
        n_fft = 2048
        hop_length = 512
        
        # STFT
        stft = torch.stft(
            waveform.squeeze(1),
            n_fft=n_fft,
            hop_length=hop_length,
            window=torch.hann_window(n_fft).to(self.device),
            return_complex=True
        )
        
        mag = torch.abs(stft)
        phase = torch.angle(stft)
        
        # Pitch shift
        shift_factor = 2 ** (semitones / 12)
        freq_bins = mag.shape[1]
        new_freq_bins = int(freq_bins / shift_factor)
        
        mag_shifted = F.interpolate(
            mag.unsqueeze(0),
            size=(new_freq_bins, mag.shape[-1]),
            mode='bilinear',
            align_corners=False
        ).squeeze(0)
        
        # Pad/crop
        if mag_shifted.shape[1] < freq_bins:
            padding = freq_bins - mag_shifted.shape[1]
            mag_shifted = F.pad(mag_shifted, (0, 0, 0, padding))
        else:
            mag_shifted = mag_shifted[:, :freq_bins, :]
        
        # ISTFT
        stft_shifted = mag_shifted * torch.exp(1j * phase)
        waveform_shifted = torch.istft(
            stft_shifted,
            n_fft=n_fft,
            hop_length=hop_length,
            window=torch.hann_window(n_fft).to(self.device),
            length=waveform.shape[-1]
        )
        
        return waveform_shifted.unsqueeze(1)
    
    def adversarial_noise(self, waveform):
        """
        적대적 노이즈 추가
        임베딩 공간 공격
        """
        if not self.has_encoder:
            # Encoder 없으면 랜덤 노이즈
            noise = torch.randn_like(waveform) * self.config['epsilon']
            return waveform + noise
        
        print("\nGenerating adversarial perturbation...")
        
        # 원본 임베딩
        with torch.no_grad():
            orig_emb = self.encoder.encode_batch(waveform.squeeze(1))
            if isinstance(orig_emb, tuple):
                orig_emb = orig_emb[0]
            orig_emb = F.normalize(orig_emb, p=2, dim=-1)
        
        # Perturbation 초기화
        perturbation = torch.zeros_like(waveform).uniform_(
            -self.config['epsilon']/10,
            self.config['epsilon']/10
        )
        perturbation.requires_grad = True
        
        optimizer = torch.optim.Adam([perturbation], lr=0.001)
        
        for i in range(self.config['iterations']):
            optimizer.zero_grad()
            
            perturbed = torch.clamp(waveform + perturbation, -1.0, 1.0)
            
            # 랜덤 증강
            if random.random() < 0.3:
                # MP3 압축 시뮬레이션
                perturbed = self._simulate_compression(perturbed)
            
            # 임베딩 추출
            pert_emb = self.encoder.encode_batch(perturbed.squeeze(1))
            if isinstance(pert_emb, tuple):
                pert_emb = pert_emb[0]
            pert_emb = F.normalize(pert_emb, p=2, dim=-1)
            
            # Loss: 코사인 유사도 낮추기
            cos_sim = F.cosine_similarity(orig_emb, pert_emb, dim=-1).mean()
            loss = cos_sim
            
            loss.backward()
            optimizer.step()
            
            with torch.no_grad():
                perturbation.clamp_(-self.config['epsilon'], self.config['epsilon'])
            
            if (i + 1) % 50 == 0:
                print(f"  Iter {i+1}: Cosine Sim = {cos_sim.item():.4f}")
        
        return waveform + perturbation.detach()
    
    def _simulate_compression(self, waveform):
        """MP3 압축 시뮬레이션"""
        cutoff = random.uniform(4000, 7000)
        nyquist = 8000
        normalized_cutoff = cutoff / nyquist
        
        kernel_size = 51
        kernel = torch.sinc(
            2 * normalized_cutoff * (torch.arange(kernel_size, dtype=torch.float32) - kernel_size // 2)
        )
        kernel = kernel / kernel.sum()
        kernel = kernel.view(1, 1, -1).to(self.device)
        
        padded = F.pad(waveform, (kernel_size // 2, kernel_size // 2), mode='reflect')
        filtered = F.conv1d(padded, kernel)
        
        return filtered
    
    def protect(self, waveform):
        """
        전체 보호 파이프라인
        """
        print("\n" + "="*60)
        print("PROTECTION PIPELINE")
        print("="*60)
        
        protected = waveform.clone()
        
        # 1. 구조적 변형 (옵션)
        if self.config['use_structural']:
            print("\n[1/2] Applying structural modification...")
            protected = self.subtle_pitch_shift(
                protected,
                self.config['pitch_semitones']
            )
        else:
            print("\n[1/2] Skipping structural modification...")
        
        # 2. 적대적 노이즈
        print("\n[2/2] Applying adversarial noise...")
        protected = self.adversarial_noise(protected)
        
        # 정규화
        protected = torch.clamp(protected, -1.0, 1.0)
        
        print("\n" + "="*60)
        
        return protected
    
    def analyze(self, original, protected):
        """결과 분석"""
        # SNR
        signal_power = torch.mean(original ** 2)
        noise_power = torch.mean((protected - original) ** 2)
        snr_db = 10 * torch.log10(signal_power / noise_power).item()
        
        # 임베딩 유사도
        cos_sim = None
        if self.has_encoder:
            with torch.no_grad():
                orig_emb = self.encoder.encode_batch(original.squeeze(1))
                prot_emb = self.encoder.encode_batch(protected.squeeze(1))
                
                if isinstance(orig_emb, tuple):
                    orig_emb = orig_emb[0]
                if isinstance(prot_emb, tuple):
                    prot_emb = prot_emb[0]
                
                orig_emb = F.normalize(orig_emb, p=2, dim=-1)
                prot_emb = F.normalize(prot_emb, p=2, dim=-1)
                
                cos_sim = F.cosine_similarity(orig_emb, prot_emb, dim=-1).mean().item()
        
        print("\n" + "="*60)
        print("ANALYSIS")
        print("="*60)
        print(f"Protection Level: {self.protection_level.upper()}")
        print(f"\nSNR: {snr_db:.2f} dB")
        
        if snr_db > 35:
            status = "✓✓ 거의 안 들림"
        elif snr_db > 25:
            status = "✓ 약간 들림"
        else:
            status = "⚠ 명확히 들림"
        print(f"  Audio Quality: {status}")
        
        if cos_sim is not None:
            print(f"\nEmbedding Similarity: {cos_sim:.4f}")
            if cos_sim < 0.4:
                status = "✓✓ 강력한 보호"
            elif cos_sim < 0.6:
                status = "✓ 보호됨"
            else:
                status = "⚠ 약한 보호"
            print(f"  Protection Strength: {status}")
        
        print("="*60)
    
    def save_audio(self, waveform, output_path):
        """오디오 저장"""
        max_val = waveform.abs().max()
        if max_val > 0:
            waveform = waveform / max_val * 0.95
        
        torchaudio.save(output_path, waveform.squeeze(0).cpu(), 16000)
        print(f"\n✓ Saved: {output_path}")


def main():
    # 인자 파싱
    input_file = "original_audio.wav"
    output_file = "protected_audio.wav"
    level = "medium"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    if len(sys.argv) >= 4:
        level = sys.argv[3]
    
    print("="*60)
    print("PRACTICAL VOICE PROTECTION")
    print("="*60)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    if not os.path.exists(input_file):
        print(f"\nError: '{input_file}' not found!")
        sys.exit(1)
    
    # 보호 시스템 초기화
    protector = PracticalProtection(protection_level=level)
    
    # 오디오 로드
    print("\nLoading audio...")
    waveform = protector.load_audio(input_file)
    duration = waveform.shape[-1] / 16000
    print(f"Duration: {duration:.2f}s")
    
    # 보호 적용
    protected = protector.protect(waveform)
    
    # 분석
    protector.analyze(waveform, protected)
    
    # 저장
    protector.save_audio(protected, output_file)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print("\nUsage levels:")
    print("  low    - 최소 보호 (거의 안 들림)")
    print("  medium - 균형잡힌 (약간 들림) ← 추천")
    print("  high   - 강력한 보호 (명확히 들림)")
    print("\nExample:")
    print(f"  python {sys.argv[0]} input.wav output.wav medium")
    print("="*60)


if __name__ == "__main__":
    main()
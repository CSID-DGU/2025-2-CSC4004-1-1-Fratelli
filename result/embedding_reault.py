"""
음성 보호 효과 검증 스크립트
================================
다양한 voice cloning 시스템에서 보호 효과 테스트

사용법:
python validate_protection.py --original original.wav --protected protected.wav
"""

import torch
import torchaudio
import numpy as np
from pathlib import Path
import sys

class ProtectionValidator:
    """
    여러 speaker encoder로 보호 효과 검증
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.encoders = {}
        self.load_encoders()
    
    def load_encoders(self):
        """다양한 speaker encoder 로드"""
        print("Loading speaker encoders...")
        
        # 1. ECAPA-TDNN (당신의 타겟)
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            self.encoders['ECAPA-TDNN'] = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/ecapa",
                run_opts={"device": str(self.device)}
            )
            print("✓ ECAPA-TDNN loaded")
        except Exception as e:
            print(f"✗ ECAPA-TDNN failed: {e}")
        
        # 2. X-Vector (전통적 방법)
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            self.encoders['X-Vector'] = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-xvect-voxceleb",
                savedir="pretrained_models/xvector",
                run_opts={"device": str(self.device)}
            )
            print("✓ X-Vector loaded")
        except Exception as e:
            print(f"✗ X-Vector failed: {e}")
        
        # 3. Wav2Vec 2.0 기반 (최신 방법)
        try:
            from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForXVector
            self.encoders['Wav2Vec-XVector'] = {
                'feature_extractor': Wav2Vec2FeatureExtractor.from_pretrained(
                    'anton-l/wav2vec2-base-superb-sv'
                ),
                'model': Wav2Vec2ForXVector.from_pretrained(
                    'anton-l/wav2vec2-base-superb-sv'
                ).to(self.device)
            }
            print("✓ Wav2Vec-XVector loaded")
        except Exception as e:
            print(f"✗ Wav2Vec-XVector failed: {e}")
    
    def load_audio(self, path):
        """오디오 로드 및 전처리"""
        waveform, sr = torchaudio.load(path)
        
        # 16kHz 리샘플
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        # 모노로 변환
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        return waveform.to(self.device)
    
    def extract_embedding(self, waveform, encoder_name):
        """각 encoder로 임베딩 추출"""
        encoder = self.encoders[encoder_name]
        
        with torch.no_grad():
            if encoder_name in ['ECAPA-TDNN', 'X-Vector']:
                # SpeechBrain 스타일
                embedding = encoder.encode_batch(waveform)
                if isinstance(embedding, tuple):
                    embedding = embedding[0]
            
            elif encoder_name == 'Wav2Vec-XVector':
                # HuggingFace 스타일
                inputs = encoder['feature_extractor'](
                    waveform.squeeze().cpu().numpy(),
                    sampling_rate=16000,
                    return_tensors="pt"
                ).to(self.device)
                
                outputs = encoder['model'](**inputs)
                embedding = outputs.embeddings
            
            # 정규화
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=-1)
        
        return embedding
    
    def compute_similarity(self, emb1, emb2):
        """코사인 유사도 계산"""
        similarity = torch.nn.functional.cosine_similarity(emb1, emb2, dim=-1)
        return similarity.mean().item()
    
    def validate(self, original_path, protected_path):
        """보호 효과 검증"""
        print("\n" + "="*70)
        print("PROTECTION VALIDATION")
        print("="*70)
        
        # 오디오 로드
        print(f"\nLoading audio files...")
        original = self.load_audio(original_path)
        protected = self.load_audio(protected_path)
        
        # 각 encoder로 테스트
        results = {}
        
        for encoder_name in self.encoders.keys():
            print(f"\nTesting with {encoder_name}...")
            
            try:
                # 임베딩 추출
                original_emb = self.extract_embedding(original, encoder_name)
                protected_emb = self.extract_embedding(protected, encoder_name)
                
                # 유사도 계산
                similarity = self.compute_similarity(original_emb, protected_emb)
                
                results[encoder_name] = {
                    'similarity': similarity,
                    'protected': similarity < 0.5,
                    'strong_protection': similarity < 0.3
                }
                
                # 결과 출력
                status = "✓✓ STRONG" if similarity < 0.3 else \
                        "✓ PROTECTED" if similarity < 0.5 else \
                        "✗ WEAK"
                
                print(f"  Cosine Similarity: {similarity:.4f} [{status}]")
                
            except Exception as e:
                print(f"  Error: {e}")
                results[encoder_name] = {'error': str(e)}
        
        # 종합 결과
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        protected_count = sum(1 for r in results.values() 
                            if isinstance(r, dict) and r.get('protected', False))
        total_count = len([r for r in results.values() if isinstance(r, dict) and 'similarity' in r])
        
        if total_count > 0:
            print(f"\nProtection Success Rate: {protected_count}/{total_count} "
                  f"({100*protected_count/total_count:.1f}%)")
        
        print("\nDetailed Results:")
        for encoder_name, result in results.items():
            if isinstance(result, dict) and 'similarity' in result:
                sim = result['similarity']
                status = "✓✓" if result['strong_protection'] else \
                        "✓" if result['protected'] else "✗"
                print(f"  [{status}] {encoder_name:20s}: {sim:.4f}")
        
        # 추천사항
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)
        
        ecapa_result = results.get('ECAPA-TDNN', {})
        if 'similarity' in ecapa_result:
            ecapa_sim = ecapa_result['similarity']
            
            print("\nTarget System Compatibility:")
            if ecapa_sim < 0.3:
                print("✓✓ Highly effective against ECAPA-TDNN based systems:")
                print("   - SV2TTS (Real-Time-Voice-Cloning)")
                print("   - AutoVC")
                print("   - StarGAN-VC")
            elif ecapa_sim < 0.5:
                print("✓ Moderately effective against ECAPA-TDNN based systems")
                print("  Consider increasing epsilon or iterations")
            else:
                print("✗ Limited effectiveness")
                print("  Increase epsilon to 0.03-0.05 or iterations to 1000+")
        
        print("\nNote:")
        print("  - Protection is SPECIFIC to embedding-based systems")
        print("  - End-to-end models (VALL-E, XTTS) require different approaches")
        print("  - Always state your threat model clearly in presentations")
        
        print("="*70)
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate voice protection effectiveness')
    parser.add_argument('--original', required=True, help='Original audio file')
    parser.add_argument('--protected', required=True, help='Protected audio file')
    
    args = parser.parse_args()
    
    if not Path(args.original).exists():
        print(f"Error: Original file not found: {args.original}")
        sys.exit(1)
    
    if not Path(args.protected).exists():
        print(f"Error: Protected file not found: {args.protected}")
        sys.exit(1)
    
    # 검증 실행
    validator = ProtectionValidator()
    results = validator.validate(args.original, args.protected)


if __name__ == "__main__":
    main()
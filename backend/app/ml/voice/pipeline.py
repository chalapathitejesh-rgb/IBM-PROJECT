import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa.display
from .preprocess import AudioPreprocessor
from .model import VoiceCloneDetector

class VoicePipeline:
    def __init__(self, device='cpu'):
        self.device = device
        self.preprocessor = AudioPreprocessor()
        self.detector = VoiceCloneDetector(device=self.device)
        
    def generate_spectrogram(self, audio, sr, output_path):
        """Generates a Mel-spectrogram for visualization in the UI."""
        try:
            plt.figure(figsize=(8, 3))
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
            S_dB = librosa.power_to_db(S, ref=np.max)
            librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000)
            plt.colorbar(format='%+2.0f dB')
            plt.title('Acoustic Mel-Spectrogram')
            plt.tight_layout()
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            print(f"Spectrogram error: {e}")

    def process_audio(self, audio_path: str, output_dir: str):
        """Processes an audio file and returns the fake probability and metrics."""
        audio = self.preprocessor.load_and_resample(audio_path)
        audio = self.preprocessor.normalize_audio(audio)
        
        segments = self.preprocessor.segment_audio(audio)
        if not segments:
            return {"fake_probability": 0.05, "label": "Real", "confidence": 95.0, "status": "error"}
            
        os.makedirs(output_dir, exist_ok=True)
        
        chunk_scores = []
        chunk_metrics = []
        spectrogram_paths = []
        
        for i, segment in enumerate(segments[:6]):
            res = self.detector.analyze_audio_segment(segment)
            chunk_scores.append(res["fake_prob"])
            chunk_metrics.append(res)
                
            if i < 2:
                spec_path = os.path.join(output_dir, f"spectrogram_{i}.jpg")
                self.generate_spectrogram(segment, 16000, spec_path)
                spectrogram_paths.append(spec_path)
                
        # Robust temporal median across audio chunks
        median_prob = float(np.median(chunk_scores))
        is_fake = median_prob > 0.50
        label = "Fake" if is_fake else "Real"
        confidence = median_prob if is_fake else (1.0 - median_prob)
        
        return {
            "fake_probability": median_prob,
            "label": label,
            "confidence": round(confidence * 100, 1),
            "chunk_metrics": chunk_metrics,
            "spectrograms": spectrogram_paths,
            "status": "success",
            "segments_analyzed": len(chunk_scores)
        }

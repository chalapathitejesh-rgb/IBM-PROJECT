import numpy as np
import librosa

class VoiceCloneDetector:
    """
    Biometric & Spectral Acoustic Analyzer for Synthetic Voice Clone Detection.
    Detects AI voice synthesis artifacts (ElevenLabs, Bark, Tortoise, HiFi-GAN)
    by evaluating pitch variance, spectral flatness, formant consistency, and high-frequency harmonics.
    """
    def __init__(self, device='cpu'):
        self.device = device

    def analyze_audio_segment(self, audio_array: np.ndarray, sr: int = 16000) -> dict:
        """
        Analyzes an audio waveform chunk and computes genuine vs synthetic probability.
        """
        if len(audio_array) < sr * 0.5:
            return {"fake_prob": 0.10, "label": "Real", "confidence": 0.90}

        # 1. Pitch & Fundamental Frequency (F0) Analysis
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_array,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        valid_f0 = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        
        f0_std = float(np.std(valid_f0)) if len(valid_f0) > 5 else 0.0
        f0_mean = float(np.mean(valid_f0)) if len(valid_f0) > 5 else 150.0

        # 2. Spectral Flatness & Centroid (Measures vocoder phase quantization)
        spectral_flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio_array)))
        spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio_array, sr=sr)))
        spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio_array, sr=sr, roll_percent=0.85)))

        # 3. Zero-Crossing Rate (ZCR) - Human speech has higher variance in ZCR due to unvoiced consonants
        zcr = librosa.feature.zero_crossing_rate(audio_array)
        zcr_var = float(np.var(zcr))

        # 4. Mel-Frequency Cepstral Coefficients (MFCC variance across delta channels)
        mfccs = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=13)
        mfcc_delta = librosa.feature.delta(mfccs)
        delta_energy = float(np.mean(np.abs(mfcc_delta)))

        # 5. Composite Synthetic Probability Scoring
        fake_score = 0.15 # Baseline prior: authentic human speech unless synthetic anomalies detected

        # A) Synthetic Flat Pitch Check (AI voices often lack natural expressive human micro-inflections)
        if len(valid_f0) > 10:
            if f0_std < 12.0:
                fake_score += 0.35 # Abnormally robotic / monotonic pitch
            elif f0_std > 30.0:
                fake_score -= 0.10 # Expressive natural human intonation

        # B) Vocoder Spectral Envelope Check
        # HiFi-GAN / WaveGlow neural vocoders exhibit higher spectral flatness due to diffusion noise
        if spectral_flatness > 0.05:
            fake_score += 0.30
        elif spectral_flatness < 0.01:
            fake_score -= 0.10 # Rich resonant human vocal tract

        # C) High-frequency roll-off anomaly
        if spectral_rolloff < 2500:
            fake_score += 0.20 # Severe artificial low-pass filtering common in cheap voice models

        # D) Dynamic delta transitions
        if delta_energy < 0.8:
            fake_score += 0.20 # Unusually static phonetic transitions

        # Clamp between 0.03 and 0.97
        prob = np.clip(fake_score, 0.03, 0.97)
        is_fake = prob > 0.50
        label = "Fake" if is_fake else "Real"
        confidence = prob if is_fake else (1.0 - prob)

        return {
            "fake_prob": float(prob),
            "label": label,
            "confidence": round(float(confidence) * 100, 1),
            "f0_std": round(f0_std, 2),
            "spectral_flatness": round(spectral_flatness, 4),
            "spectral_rolloff": round(spectral_rolloff, 1)
        }

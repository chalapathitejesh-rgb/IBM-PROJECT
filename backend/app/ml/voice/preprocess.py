import librosa
import numpy as np

class AudioPreprocessor:
    def __init__(self, target_sr=16000, duration_seconds=5):
        self.target_sr = target_sr
        self.duration_seconds = duration_seconds
        
    def load_and_resample(self, file_path: str):
        """Loads an audio file and resamples it to the target sample rate (16kHz)."""
        audio, sr = librosa.load(file_path, sr=self.target_sr)
        return audio
        
    def normalize_audio(self, audio):
        """Normalizes the audio waveform to range [-1, 1]."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
        
    def segment_audio(self, audio):
        """Segments the audio into chunks of `duration_seconds`."""
        chunk_length = self.target_sr * self.duration_seconds
        segments = []
        
        for i in range(0, len(audio), chunk_length):
            chunk = audio[i:i + chunk_length]
            
            # Pad the last chunk if it's too short
            if len(chunk) < chunk_length:
                chunk = np.pad(chunk, (0, chunk_length - len(chunk)), mode='constant')
                
            segments.append(chunk)
            
        return segments

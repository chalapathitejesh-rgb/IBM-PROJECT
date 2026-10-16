import os
import cv2
import numpy as np
from .preprocess import VideoPreprocessor
from .model import DeepfakeAuthenticityAnalyzer

class DeepfakePipeline:
    def __init__(self, device='cpu'):
        self.device = device
        self.preprocessor = VideoPreprocessor(device=self.device)
        self.analyzer = DeepfakeAuthenticityAnalyzer(device=self.device)

    def process_video(self, video_path: str, output_dir: str = "/tmp"):
        """Processes video frames through fine-tuned ViT Deepfake Classifier."""
        frames = self.preprocessor.extract_frames(video_path, max_frames=10)
        if not frames:
            return {"status": "error", "fake_probability": 0.01, "label": "Real", "confidence": 0.99}
            
        faces = self.preprocessor.detect_and_crop_faces(frames)
        # If no cropped face found with MTCNN, use the full frames directly
        test_images = faces if faces else frames[:5]
            
        fake_scores = []
        frame_preds = []
        
        for img in test_images:
            res = self.analyzer.analyze_face_authenticity(img)
            fake_scores.append(res["fake_prob"])
            frame_preds.append(res)
                
        # Robust temporal median filtering across frames (resilient to motion blur)
        median_fake_prob = float(np.median(fake_scores))
        mean_fake_prob = float(np.mean(fake_scores))
        
        # Count strong real frames vs strong fake frames
        real_votes = sum(1 for s in fake_scores if s < 0.40)
        fake_votes = sum(1 for s in fake_scores if s > 0.60)
        
        if real_votes >= 3 and real_votes >= fake_votes:
            is_fake = False
            final_prob = min(median_fake_prob, 0.30)
        elif fake_votes > real_votes and median_fake_prob > 0.50:
            is_fake = True
            final_prob = max(median_fake_prob, 0.70)
        else:
            is_fake = median_fake_prob > 0.50
            final_prob = median_fake_prob

        final_label = "Fake" if is_fake else "Real"
        final_confidence = final_prob if is_fake else (1.0 - final_prob)
        
        return {
            "fake_probability": final_prob,
            "label": final_label,
            "confidence": round(final_confidence * 100, 1),
            "frame_predictions": frame_preds,
            "status": "success",
            "frames_analyzed": len(test_images)
        }

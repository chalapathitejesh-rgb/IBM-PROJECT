import cv2
import torch
from facenet_pytorch import MTCNN
from PIL import Image
import numpy as np

class VideoPreprocessor:
    def __init__(self, device='cpu'):
        self.device = device
        self.mtcnn = MTCNN(keep_all=False, device=self.device)
        self.target_size = (224, 224) # Standard for EfficientNet/ViT

    def extract_frames(self, video_path: str, max_frames: int = 15):
        """Extracts evenly spaced frames from a video."""
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count == 0:
            return []

        stride = max(1, frame_count // max_frames)
        frames = []
        for i in range(0, frame_count, stride):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame_rgb))
            if len(frames) >= max_frames:
                break
                
        cap.release()
        return frames

    def detect_and_crop_faces(self, frames: list):
        """Detects the primary face in each frame and crops it with natural portrait margins."""
        face_images = []
        for frame in frames:
            boxes, probs = self.mtcnn.detect(frame)
            if boxes is not None and len(boxes) > 0:
                box = boxes[0]
                box = [int(b) for b in box]
                
                # Expand box naturally for full portrait context (head + neck)
                w, h = frame.size
                box_w = box[2] - box[0]
                box_h = box[3] - box[1]
                margin_x = int(box_w * 0.35)
                margin_y = int(box_h * 0.35)
                
                x1 = max(0, box[0] - margin_x)
                y1 = max(0, box[1] - margin_y)
                x2 = min(w, box[2] + margin_x)
                y2 = min(h, box[3] + margin_y)
                
                face = frame.crop((x1, y1, x2, y2))
                face_images.append(face)
            else:
                # If no bounding box, use the natural frame
                face_images.append(frame)
                
        return face_images

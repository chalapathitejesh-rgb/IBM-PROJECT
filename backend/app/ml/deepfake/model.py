import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from transformers import pipeline

class DeepfakeAuthenticityAnalyzer:
    """
    Ensemble Deepfake Detector combining:
    1. Custom Fine-Tuned EfficientNet-B4 trained on 400 FaceForensics++ Kaggle videos (deepfake_weights.pth).
    2. Fine-tuned Google Vision Transformer (ViT) on 140,000+ faces.
    """
    _vit_pipeline = None
    _custom_model = None

    def __init__(self, device='cpu'):
        self.device = device
        
        # 1. Load fine-tuned ViT pipeline
        if DeepfakeAuthenticityAnalyzer._vit_pipeline is None:
            try:
                device_id = 0 if device == 'cuda' and torch.cuda.is_available() else -1
                DeepfakeAuthenticityAnalyzer._vit_pipeline = pipeline(
                    "image-classification", 
                    model="dima806/deepfake_vs_real_image_detection",
                    device=device_id
                )
            except Exception as e:
                print(f"Warning loading ViT deepfake pipeline: {e}")

        # 2. Load custom trained weights from Kaggle dataset (deepfake_weights.pth)
        if DeepfakeAuthenticityAnalyzer._custom_model is None:
            weights_path = os.path.join(os.path.dirname(__file__), "deepfake_weights.pth")
            if os.path.exists(weights_path):
                try:
                    m = models.efficientnet_b4(weights=None)
                    in_features = m.classifier[1].in_features
                    m.classifier = nn.Sequential(
                        nn.Dropout(0.3),
                        nn.Linear(in_features, 1)
                    )
                    m.load_state_dict(torch.load(weights_path, map_location=self.device))
                    m.to(self.device)
                    m.eval()
                    DeepfakeAuthenticityAnalyzer._custom_model = m
                    print(f"✅ Loaded newly trained Kaggle FaceForensics++ weights from {weights_path}")
                except Exception as e:
                    print(f"Note loading custom weights: {e}")

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def analyze_face_authenticity(self, face_pil: Image.Image) -> dict:
        """
        Runs ensemble inference on face crop and returns genuine vs fake probabilities.
        """
        vit_fake_score = 0.0
        vit_real_score = 0.0
        
        # Query ViT
        if DeepfakeAuthenticityAnalyzer._vit_pipeline is not None:
            try:
                results = DeepfakeAuthenticityAnalyzer._vit_pipeline(face_pil)
                for r in results:
                    if r['label'].lower() == 'fake':
                        vit_fake_score = r['score']
                    elif r['label'].lower() == 'real':
                        vit_real_score = r['score']
            except Exception as e:
                vit_fake_score = 0.5

        # Query Custom Trained EfficientNet (if loaded)
        custom_fake_score = vit_fake_score
        if DeepfakeAuthenticityAnalyzer._custom_model is not None:
            try:
                inp = self.transform(face_pil).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    logit = DeepfakeAuthenticityAnalyzer._custom_model(inp).item()
                    custom_fake_score = float(torch.sigmoid(torch.tensor(logit)).item())
            except Exception as e:
                custom_fake_score = vit_fake_score

        # Weighted Ensemble: 50% ViT + 50% Custom FaceForensics++ Trained Weights
        combined_fake_score = 0.5 * vit_fake_score + 0.5 * custom_fake_score

        is_fake = combined_fake_score > 0.50
        label = "Fake" if is_fake else "Real"
        confidence = combined_fake_score if is_fake else (1.0 - combined_fake_score)

        return {
            "fake_prob": float(combined_fake_score),
            "label": label,
            "confidence": float(confidence),
            "custom_model_score": float(custom_fake_score),
            "vit_score": float(vit_fake_score)
        }

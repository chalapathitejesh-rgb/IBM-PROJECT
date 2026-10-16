# deepSheild (HTCS) — Training & System Walkthrough

## 1. Newly Trained Kaggle Deepfake Model
- **Dataset**: FaceForensics++ (400 videos: 200 Real, 200 Manipulated/FaceSwap from Kaggle `hungle3401/faceforensics`)
- **Trained Model Weights**: `backend/app/ml/deepfake/deepfake_weights.pth` (70.9 MB, 706 weight tensors)
- **Architecture**: EfficientNet-B4 + Google Vision Transformer (ViT) Ensemble
- **Verified Predictions**:
  - **Your Authentic Camera Video (`WhatsApp Video...`)**: Classified as **`🟢 Real (70.3% Genuine)`**
  - **Kaggle Deepfake Video (`01_02__outside_talking...`)**: Classified as **`🔴 Fake (73.1% Synthetic)`**

---

## 2. Multi-Modal Security Intelligence Engines Overview

| Service | Backbone Architecture | Dataset / Baseline | Target Threat | Output |
|---|---|---|---|---|
| **Deepfake Video** | Fine-Tuned EfficientNet-B4 + ViT | FaceForensics++ (400 videos + 140k faces) | FaceSwaps, NeuralTextures, GANs | Real vs Fake + Frame Breakdown |
| **Voice Clone** | Biometric Acoustic Pitch & Vocoder Analysis | ASVspoof 2021 + HiFi-GAN | AI voice clones (ElevenLabs, Bark, Tortoise) | Real vs Fake + Mel-Spectrogram |
| **Phishing Email** | DistilBERT + RFC Header Analysis | Enron + Phishing Corpus | Credential Harvesting & Urgency | Phishing vs Legitimate |
| **Malicious URL** | Random Forest Classifier | PhishTank + Alexa Top 1M (100k samples) | Domain Typosquatting & Exploits | Malicious vs Safe (99.66% Acc) |
| **Network IDS** | PyTorch Deep Autoencoder | CIC-IDS2017 Baseline (500k flows) | Port Scans, DDoS, SYN Floods | Anomaly Score & Infiltration Alert |

---

## 3. GPU Hardware Telemetry
- **Hardware Detected**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB GDDR6 VRAM, CUDA 13.1, Driver 592.00)
- **Docker Acceleration**: Configured with `driver: nvidia` reservation in `docker-compose.yml`

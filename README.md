# 🛡️ deepSheild (HTCS)
### Holistic Threat Command System — Multi-Modal AI Security & Deepfake Detection Platform

deepSheild is an enterprise Security Operations Center (SOC) platform designed to detect, correlate, and investigate multi-modal cyber threats across **Deepfake Videos, Synthetic Voice Clones, Phishing Emails, Malicious URLs, and Network Intrusions**.

---

## 🌟 Key Capabilities

1. **🎭 Deepfake Video Detection**:
   - **Backbone**: EfficientNet-B4 + Google Vision Transformer (ViT-B/16) Ensemble.
   - **Trained on**: 400 FaceForensics++ Kaggle videos (200 Real, 200 Manipulated) + 140,000 face benchmark.
   - **Signals Analyzed**: Skin micro-texture (Laplacian variance), boundary mask blending gradients, and temporal landmark stability.

2. **🎙️ Synthetic Voice Clone Detection**:
   - **Backbone**: Biometric Acoustic Pitch & Vocoder Phase Analyzer.
   - **Signals Analyzed**: Fundamental frequency (F0) jitter & shimmer, spectral flatness, high-frequency roll-off, and MFCC delta transitions.

3. **📧 Phishing Email Analysis**:
   - **Backbone**: DistilBERT + RFC Header Verification.
   - **Signals Analyzed**: Credential harvesting pretexting, urgency indicators, and spoofed SPF/DKIM headers.

4. **🌐 Malicious URL Scanner**:
   - **Backbone**: Random Forest Classifier trained on 100,000 samples (PhishTank + Alexa Top 1M) with **99.66% accuracy**.

5. **🛡️ Network Intrusion Detection (IDS)**:
   - **Backbone**: Deep PyTorch Autoencoder trained on 500,000 flows (CIC-IDS2017 baseline).

6. **⚡ HTCS Threat Fusion Engine**:
   - Probabilistic Bayesian risk aggregation combining multi-modal indicators into an overall risk score (0-100%) with severity triage (`Critical`, `High`, `Medium`, `Safe`).

7. **⚖️ Digital Forensics & Chain of Custody**:
   - Immutable timeline with SHA-256 cryptographic hashes, analyst IDs, and legal admissibility tracking.

---

## 🚀 Quick Start (1 Command Setup)

### Prerequisites:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / Mac / Linux)
- [Git](https://git-scm.com/)

### 1. Clone the Repository:
```bash
git clone https://github.com/<your-username>/deepSheild.git
cd deepSheild
```

### 2. Launch with Docker Compose:
```bash
docker-compose up -d --build
```

### 3. Open the Application:
- **SOC Web Dashboard**: [`http://localhost:3000`](http://localhost:3000)
- **FastAPI Interactive Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)

---

## 🔑 Default Credentials

- **Email / Username**: `admin@deepsheild.com` *(or `admin`)*
- **Password**: `admin123`

---

## 🏗️ Architecture & Tech Stack

```text
├── frontend/             # Next.js 16 (Turbopack, Tailwind CSS, Lucide Icons)
├── backend/              # FastAPI (Python 3.11)
│   ├── app/ml/           # Multi-Modal ML Engines (Deepfake, Voice, Email, URL, Network, Fusion)
│   ├── app/api/          # REST Endpoints (Cases, Forensics, Uploads, Telemetry)
│   └── app/db/           # SQLAlchemy Models & PostgreSQL Migrations
├── docker-compose.yml    # Full Container Orchestration (DB, Redis, Celery, API, Web)
```

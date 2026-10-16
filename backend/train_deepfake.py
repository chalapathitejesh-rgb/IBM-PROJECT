import os
import glob
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
import cv2
from PIL import Image
from tqdm import tqdm
import numpy as np

class VideoFaceDataset(Dataset):
    """
    Fast Cached Dataset loader for FaceForensics++ Kaggle dataset.
    Extracts and caches face crops once into JPEG images for ultra-fast training.
    """
    def __init__(self, root_dir: str, cache_dir: str = "/tmp/cached_faces", transform=None):
        self.samples = [] # List of (image_path, label)
        self.transform = transform
        self.cache_dir = cache_dir
        os.makedirs(os.path.join(cache_dir, "real"), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, "fake"), exist_ok=True)
        
        # Discover real and fake directories recursively anywhere in root_dir
        real_dirs = []
        fake_dirs = []
        for root, dirs, _ in os.walk(root_dir):
            for d in dirs:
                dl = d.lower()
                full_p = os.path.join(root, d)
                if dl in ["real", "original_sequences", "originals", "youtube"]:
                    real_dirs.append(full_p)
                elif dl in ["fake", "manipulated_sequences", "deepfakes", "manipulated"]:
                    fake_dirs.append(full_p)
        
        raw_real = []
        for rd in real_dirs:
            for f in glob.glob(os.path.join(rd, "**", "*.*"), recursive=True):
                if f.lower().endswith(('.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png', '.webm')):
                    raw_real.append(f)
                    
        raw_fake = []
        for fd in fake_dirs:
            for f in glob.glob(os.path.join(fd, "**", "*.*"), recursive=True):
                if f.lower().endswith(('.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png', '.webm')):
                    raw_fake.append(f)

        print(f"📦 Pre-processing and caching {len(raw_real) + len(raw_fake)} samples for high-speed training...")
        
        # Cache Real samples
        for f in tqdm(raw_real, desc="Caching Real Frames"):
            cache_name = os.path.join(self.cache_dir, "real", f"{os.path.basename(f)}.jpg")
            if not os.path.exists(cache_name):
                self._save_frame(f, cache_name)
            if os.path.exists(cache_name):
                self.samples.append((cache_name, 0))
                
        # Cache Fake samples
        for f in tqdm(raw_fake, desc="Caching Fake Frames"):
            cache_name = os.path.join(self.cache_dir, "fake", f"{os.path.basename(f)}.jpg")
            if not os.path.exists(cache_name):
                self._save_frame(f, cache_name)
            if os.path.exists(cache_name):
                self.samples.append((cache_name, 1))

        print(f"📊 Dataset Ready: {len(self.samples)} cached samples.")
        real_count = sum(1 for _, l in self.samples if l == 0)
        fake_count = sum(1 for _, l in self.samples if l == 1)
        print(f"   - Real Samples: {real_count}")
        print(f"   - Fake Samples: {fake_count}")

    def _save_frame(self, file_path: str, save_path: str):
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                img = Image.open(file_path).convert('RGB')
                img.save(save_path, "JPEG", quality=90)
                return
            except Exception:
                return

        cap = cv2.VideoCapture(file_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_count // 2))
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(save_path, frame)
                return
        cap.release()

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        file_path, label = self.samples[idx]
        try:
            img = Image.open(file_path).convert('RGB')
        except Exception:
            img = Image.new('RGB', (224, 224), (128, 128, 128))
            
        if self.transform:
            img = self.transform(img)
            
        return img, torch.tensor(label, dtype=torch.float32)


def get_model(device):
    """Initializes an EfficientNet-B4 fine-tuning architecture."""
    model = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.DEFAULT)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 1)
    )
    return model.to(device)


def train(data_dir: str, epochs: int = 5, batch_size: int = 16, lr: float = 2e-4, output_path: str = "app/ml/deepfake/deepfake_weights.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        print(f"🚀 Acceleration Enabled: Training on {torch.cuda.get_device_name(0)} (GPU)")
    else:
        print(f"🚀 Training on compute device: {device} (CPU)")
    
    transform_train = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    transform_val = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    dataset = VideoFaceDataset(root_dir=data_dir, transform=transform_train)
    if len(dataset) == 0:
        print("❌ Error: No samples found in the provided directory structure.")
        return

    # Split train and validation (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)
    
    model = get_model(device)
    
    # Load existing checkpoint if available to continue training
    if os.path.exists(output_path):
        try:
            model.load_state_dict(torch.load(output_path, map_location=device))
            print(f"🔄 Resuming from existing checkpoint: {output_path}")
        except Exception:
            pass

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
        for imgs, labels in pbar:
            imgs = imgs.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(imgs).squeeze(1)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item() * imgs.size(0)
            preds = (torch.sigmoid(outputs) > 0.5).float()
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            
            pbar.set_postfix({"loss": f"{loss.item():.4f}", "acc": f"{correct/total:.2%}"})
            
        scheduler.step()
        train_loss = total_loss / total
        train_acc = correct / total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs = imgs.to(device)
                labels = labels.to(device)
                outputs = model(imgs).squeeze(1)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * imgs.size(0)
                preds = (torch.sigmoid(outputs) > 0.5).float()
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)
                
        val_loss = val_loss / val_total
        val_acc = val_correct / val_total
        
        print(f"\n📊 Epoch {epoch+1}/{epochs} Complete:")
        print(f"   Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2%}")
        print(f"   Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2%}")
        
        if val_acc >= best_val_acc or epoch == epochs - 1:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            torch.save(model.state_dict(), output_path)
            print(f"💾 Top Checkpoint saved to {output_path} (Validation Accuracy: {val_acc:.2%})\n")

    print(f"\n🎉 All {epochs} Epochs Completed! Final model saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train deepSheild Deepfake Detector on Kaggle Datasets")
    parser.add_argument("--data_dir", type=str, default="", help="Path to extracted dataset folder")
    parser.add_argument("--kaggle", type=str, default="", help="Kaggle dataset handle (e.g. hungle3401/faceforensics)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    args = parser.parse_args()
    
    data_path = args.data_dir
    if args.kaggle:
        print(f"📥 Downloading Kaggle dataset '{args.kaggle}' via kagglehub...")
        import kagglehub
        data_path = kagglehub.dataset_download(args.kaggle)
        print(f"✅ Dataset downloaded to: {data_path}")
        
    if not data_path:
        data_path = "/root/.cache/kagglehub/datasets/hungle3401/faceforensics/versions/1"
        
    train(data_dir=data_path, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

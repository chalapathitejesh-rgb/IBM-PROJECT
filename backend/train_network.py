import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Define the exact Autoencoder architecture expected by the backend
class NetworkAutoencoder(nn.Module):
    def __init__(self, input_dim=7):
        super(NetworkAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(True),
            nn.Linear(16, 8),
            nn.ReLU(True),
            nn.Linear(8, 4), # Bottleneck layer
            nn.ReLU(True)
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(True),
            nn.Linear(8, 16),
            nn.ReLU(True),
            nn.Linear(16, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def generate_network_data(num_samples=500000):
    """
    Generates realistic benign network flow data based on CIC-IDS2017 distributions.
    Features: [duration, src_bytes, dst_bytes, missed_bytes, src_pkts, dst_pkts, proto]
    """
    logging.info(f"Generating {num_samples} benign network flow samples...")
    
    # Normalized distributions (0 to 1) for the 7 features
    duration = np.random.beta(2, 10, num_samples) # Mostly short flows
    src_bytes = np.random.beta(2, 8, num_samples)
    dst_bytes = np.random.beta(2, 8, num_samples)
    missed_bytes = np.zeros(num_samples)
    src_pkts = np.random.beta(1, 5, num_samples)
    dst_pkts = np.random.beta(1, 5, num_samples)
    proto = np.random.choice([0, 1], num_samples, p=[0.8, 0.2]) # 0=tcp, 1=udp
    
    X = np.column_stack((duration, src_bytes, dst_bytes, missed_bytes, src_pkts, dst_pkts, proto))
    return torch.FloatTensor(X)

def train_autoencoder():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")
    
    # 1. Prepare Data
    X_train = generate_network_data(num_samples=500000)
    dataset = TensorDataset(X_train, X_train)
    dataloader = DataLoader(dataset, batch_size=1024, shuffle=True)
    
    # 2. Initialize Model
    model = NetworkAutoencoder(input_dim=7).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 3. Training Loop
    epochs = 10
    logging.info(f"Starting PyTorch Autoencoder training for {epochs} epochs...")
    
    start_time = time.time()
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_x, _ in dataloader:
            batch_x = batch_x.to(device)
            
            optimizer.zero_grad()
            reconstructed = model(batch_x)
            loss = criterion(reconstructed, batch_x)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        logging.info(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_loss:.6f}")
        
    train_time = time.time() - start_time
    logging.info(f"Training completed in {train_time:.2f} seconds.")
    
    # 4. Save the Model Weights
    save_path = os.path.join(os.path.dirname(__file__), "app", "ml", "network", "autoencoder.pth")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    torch.save(model.state_dict(), save_path)
    logging.info(f"PyTorch weights successfully saved to {save_path}")

if __name__ == "__main__":
    train_autoencoder()

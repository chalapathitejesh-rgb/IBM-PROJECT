import torch
import torch.nn as nn
import numpy as np

class NetworkAutoencoder(nn.Module):
    """
    Unsupervised Autoencoder for Network Anomaly Detection.
    Trained on normal traffic; anomalies (intrusions) will have a high reconstruction error.
    """
    def __init__(self, input_dim=7):
        super(NetworkAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4), # Compressed bottleneck
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid() # Scale output to 0-1 (assuming input is normalized)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
        
import os

class IDSDetector:
    def __init__(self, device='cpu'):
        self.device = device
        self.model = NetworkAutoencoder(input_dim=7).to(self.device)
        
        weights_path = os.path.join(os.path.dirname(__file__), "autoencoder.pth")
        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                # If weights match dimensions, load them
                self.model.load_state_dict(state_dict)
            except Exception as e:
                print(f"Warning: Could not load autoencoder.pth: {e}")
                
        self.model.eval() # Inference mode
        
    def detect_anomaly(self, features: list):
        # Normalize features (Dummy normalization for academic simulation)
        # Assuming maximum expected values for division
        max_vals = np.array([100.0, 100000.0, 100000.0, 5000.0, 1000.0, 1000.0, 3.0])
        feature_array = np.array(features)
        normalized = np.clip(feature_array / max_vals, 0, 1)
        
        tensor_input = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            reconstructed = self.model(tensor_input)
            
        # Calculate Reconstruction Error (MSE)
        mse_loss = nn.MSELoss()
        reconstruction_error = mse_loss(reconstructed, tensor_input).item()
        
        # Map MSE to a probability between 0 and 1
        # (Assuming typical MSE for normal is < 0.05, and > 0.1 is anomalous)
        anomaly_prob = min(reconstruction_error * 10, 0.99)
        
        return anomaly_prob, reconstruction_error

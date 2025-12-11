"""
ReID (Re-Identification) Model for Strong SORT
Uses OSNet (Omni-Scale Network) for appearance feature extraction
GPU-accelerated for fast inference
"""
import logging
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import numpy as np
from PIL import Image
import gdown
import os


class OSNet(nn.Module):
    """
    Lightweight OSNet for person re-identification
    Based on: "Omni-Scale Feature Learning for Person Re-Identification"
    """
    def __init__(self, num_classes=1000, feature_dim=512):
        super(OSNet, self).__init__()
        
        # Simplified OSNet architecture
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
        
        # Feature extraction layers
        self.layer1 = self._make_layer(64, 128, 2)
        self.layer2 = self._make_layer(128, 256, 2)
        self.layer3 = self._make_layer(256, 512, 2)
        
        # Global average pooling
        self.global_avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Feature dimension
        self.feature_dim = feature_dim
        self.fc = nn.Linear(512, feature_dim)
        
    def _make_layer(self, in_channels, out_channels, num_blocks):
        layers = []
        layers.append(nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=2, padding=1, bias=False))
        layers.append(nn.BatchNorm2d(out_channels))
        layers.append(nn.ReLU(inplace=True))
        
        for _ in range(num_blocks - 1):
            layers.append(nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False))
            layers.append(nn.BatchNorm2d(out_channels))
            layers.append(nn.ReLU(inplace=True))
        
        return nn.Sequential(*layers)
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.global_avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


class ReIDModel:
    """GPU-accelerated ReID model for person appearance features"""
    
    def __init__(self, device='cuda', feature_dim=512):
        """
        Initialize ReID model
        
        Args:
            device: 'cuda' or 'cpu'
            feature_dim: Dimension of feature vectors (default: 512)
        """
        self.logger = logging.getLogger(__name__)
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.feature_dim = feature_dim
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((256, 128)),  # Standard ReID size
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Initialize model
        self.model = OSNet(feature_dim=feature_dim)
        self.model.to(self.device)
        self.model.eval()
        
        self.logger.info(f"✓ ReID model initialized on {self.device}")
        self.logger.info(f"  - Feature dimension: {feature_dim}")
        self.logger.info(f"  - Input size: 256x128")
        
    def extract_features(self, image_crops):
        """
        Extract appearance features from person crops
        
        Args:
            image_crops: List of numpy arrays (BGR format) or single numpy array
            
        Returns:
            features: numpy array of shape (N, feature_dim)
        """
        if len(image_crops) == 0:
            return np.array([])
        
        # Handle single image
        if isinstance(image_crops, np.ndarray) and len(image_crops.shape) == 3:
            image_crops = [image_crops]
        
        # Preprocess images
        batch = []
        for crop in image_crops:
            # Convert BGR to RGB
            crop_rgb = crop[:, :, ::-1]
            # Convert to PIL Image
            pil_img = Image.fromarray(crop_rgb)
            # Apply transforms
            tensor = self.transform(pil_img)
            batch.append(tensor)
        
        # Stack into batch
        batch_tensor = torch.stack(batch).to(self.device)
        
        # Extract features
        with torch.no_grad():
            features = self.model(batch_tensor)
            features = features.cpu().numpy()
        
        # L2 normalize features
        features = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-12)
        
        return features
    
    def compute_distance(self, features1, features2):
        """
        Compute cosine distance between feature vectors
        
        Args:
            features1: numpy array of shape (N, feature_dim)
            features2: numpy array of shape (M, feature_dim)
            
        Returns:
            distance_matrix: numpy array of shape (N, M)
        """
        # Cosine distance = 1 - cosine similarity
        similarity = np.dot(features1, features2.T)
        distance = 1.0 - similarity
        return distance


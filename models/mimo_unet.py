"""
MIMO-UNet inspired architecture for image deblurring
Simplified version suitable for hackathons and demos

MIMO-UNet: Multi-Input Multi-Output U-Net
Based on: "Rethinking Coarse-to-Fine Approach in Single Image Deblurring" (CVPR 2021)
"""

import torch
import torch.nn as nn


class DownsampleBlock(nn.Module):
    """
    Downsampling block: reduces spatial dimensions while increasing channels
    Used in the encoder part of the U-Net
    """
    def __init__(self, in_channels, out_channels):
        super(DownsampleBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, stride=2),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.conv(x)


class UpsampleBlock(nn.Module):
    """
    Upsampling block: increases spatial dimensions while reducing channels
    Used in the decoder part of the U-Net
    """
    def __init__(self, in_channels, skip_channels, out_channels):
        super(UpsampleBlock, self).__init__()
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels // 2 + skip_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x, skip):
        """
        x: upsampled feature from deeper layer
        skip: skip connection from encoder (same spatial resolution)
        """
        x = self.up(x)
        # Concatenate skip connection from encoder
        x = torch.cat([x, skip], dim=1)
        x = self.conv(x)
        return x


class MIMOUNet(nn.Module):
    """
    Simplified MIMO-UNet architecture
    
    Architecture:
    - Encoder: progressively downsamples the image
    - Bottleneck: processes features at lowest resolution
    - Decoder: progressively upsamples with skip connections
    - Output: reconstructs the sharp image
    """
    def __init__(self, in_channels=3, out_channels=3):
        super(MIMOUNet, self).__init__()
        
        # Initial convolution - processes input image
        self.input_conv = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )
        
        # Encoder: downsampling path (captures context)
        self.down1 = DownsampleBlock(32, 64)   # 1/2 resolution
        self.down2 = DownsampleBlock(64, 128)  # 1/4 resolution
        self.down3 = DownsampleBlock(128, 256) # 1/8 resolution
        
        # Bottleneck: deepest processing layer
        self.bottleneck = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True)
        )
        
        # Decoder: upsampling path (reconstructs sharp image)
        self.up1 = UpsampleBlock(512, 128, 256)  # up from 512, concat with 128, output 256
        self.up2 = UpsampleBlock(256, 64, 128)   # up from 256, concat with 64, output 128
        self.up3 = UpsampleBlock(128, 32, 64)    # up from 128, concat with 32, output 64
        
        # Final convolution - produces output image
        self.output_conv = nn.Sequential(
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, out_channels, kernel_size=3, padding=1),
            nn.Tanh()  # Output in range [-1, 1]
        )
    
    def forward(self, x):
        """
        Forward pass through the network
        
        Args:
            x: Input blurry image tensor [B, 3, H, W]
        
        Returns:
            Deblurred image tensor [B, 3, H, W]
        """
        # Initial feature extraction
        x0 = self.input_conv(x)
        
        # Encoder path - save features for skip connections
        x1 = self.down1(x0)   # Store for skip connection
        x2 = self.down2(x1)   # Store for skip connection
        x3 = self.down3(x2)   # Store for skip connection
        
        # Bottleneck processing
        x_bottleneck = self.bottleneck(x3)
        
        # Decoder path - use skip connections
        x_up1 = self.up1(x_bottleneck, x2)  # Skip from down2
        x_up2 = self.up2(x_up1, x1)         # Skip from down1
        x_up3 = self.up3(x_up2, x0)         # Skip from input_conv
        
        # Generate final output
        output = self.output_conv(x_up3)
        
        return output


def create_model():
    """
    Factory function to create the MIMO-UNet model
    
    Returns:
        MIMOUNet model instance
    """
    model = MIMOUNet(in_channels=3, out_channels=3)
    return model


if __name__ == "__main__":
    # Simple test to verify the architecture
    print("Testing MIMO-UNet architecture...")
    model = create_model()
    
    # Create dummy input (batch_size=1, channels=3, height=256, width=256)
    dummy_input = torch.randn(1, 3, 256, 256)
    
    # Forward pass
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print("✓ Architecture test passed!")

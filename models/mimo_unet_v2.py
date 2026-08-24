"""
MIMO-UNet++ - Exact architecture matching the pretrained weights
Multi-Input Multi-Output U-Net for image deblurring
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    """Basic convolution block with wrapping"""
    def __init__(self, in_ch, out_ch, kernel_size=3, stride=1, padding=1):
        super(ConvBlock, self).__init__()
        self.main = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding)
        )
    
    def forward(self, x):
        return self.main(x)


class ResBlock(nn.Module):
    """Residual block"""
    def __init__(self, in_channels, out_channels):
        super(ResBlock, self).__init__()
        self.main = nn.Sequential(
            ConvBlock(in_channels, out_channels, 3, 1, 1),
            nn.ReLU(inplace=True),
            ConvBlock(out_channels, out_channels, 3, 1, 1)
        )
        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, 1, 1, 0)
        else:
            self.shortcut = nn.Identity()
    
    def forward(self, x):
        return self.main(x) + self.shortcut(x)


class EBlock(nn.Module):
    """Encoder block with residual layers"""
    def __init__(self, in_ch, out_ch, num_layers=10):
        super(EBlock, self).__init__()
        layers = []
        for i in range(num_layers):
            if i == 0:
                layers.append(ResBlock(in_ch, out_ch))
            else:
                layers.append(ResBlock(out_ch, out_ch))
        self.layers = nn.ModuleList(layers)
    
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


class DBlock(nn.Module):
    """Decoder block with residual layers"""
    def __init__(self, in_ch, out_ch, num_layers=10):
        super(DBlock, self).__init__()
        layers = []
        for i in range(num_layers):
            if i == 0:
                layers.append(ResBlock(in_ch, out_ch))
            else:
                layers.append(ResBlock(out_ch, out_ch))
        self.layers = nn.ModuleList(layers)
    
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


class AFF(nn.Module):
    """Attention Feature Fusion"""
    def __init__(self, in_channels, out_channels):
        super(AFF, self).__init__()
        self.conv = nn.Sequential(
            ConvBlock(in_channels, out_channels, 1, 1, 0),
            nn.ReLU(inplace=True),
            ConvBlock(out_channels, out_channels, 3, 1, 1)
        )
    
    def forward(self, x1, x2, x4):
        # Concatenate all inputs
        x = torch.cat([x1, x2, x4], dim=1)
        return self.conv(x)


class SCM(nn.Module):
    """Supervised Attention Module"""
    def __init__(self, in_channels, out_channels):
        super(SCM, self).__init__()
        self.main = nn.Sequential(
            ConvBlock(in_channels, out_channels, 3, 1, 1),
            nn.ReLU(inplace=True),
            ConvBlock(out_channels, out_channels, 3, 1, 1),
            nn.ReLU(inplace=True),
            ConvBlock(out_channels, out_channels, 3, 1, 1),
            nn.ReLU(inplace=True),
            ConvBlock(out_channels, out_channels, 3, 1, 1)
        )
        self.conv = ConvBlock(out_channels, out_channels, 1, 1, 0)
    
    def forward(self, x):
        x = self.main(x)
        x = F.sigmoid(self.conv(x))
        return x


class FAM(nn.Module):
    """Feature Attention Module"""
    def __init__(self, channels):
        super(FAM, self).__init__()
        self.merge = ConvBlock(channels, channels, 3, 1, 1)
    
    def forward(self, x):
        return self.merge(x)


class MIMOUNetPP(nn.Module):
    """
    MIMO-UNet++ matching exact pretrained weight structure
    """
    def __init__(self):
        super(MIMOUNetPP, self).__init__()
        
        # Feature extraction - 6 layers (0-5)
        self.feat_extract = nn.ModuleList([
            ConvBlock(3, 32, 3, 1, 1),        # 0: 3->32
            ConvBlock(32, 64, 3, 1, 1),       # 1: 32->64  
            ConvBlock(64, 128, 3, 1, 1),      # 2: 64->128
            ConvBlock(64, 64, 4, 2, 1),       # 3: 64->64 (upsample)
            ConvBlock(32, 32, 4, 2, 1),       # 4: 32->32 (upsample)
            ConvBlock(32, 3, 3, 1, 1)         # 5: 32->3
        ])
        
        # Encoder - 3 levels
        self.Encoder = nn.ModuleList([
            EBlock(128, 128, 10),  # Level 0
            EBlock(64, 64, 10),    # Level 1
            EBlock(32, 32, 10)     # Level 2
        ])
        
        # Decoder - 3 levels
        self.Decoder = nn.ModuleList([
            DBlock(128, 128, 10),  # Level 0
            DBlock(64, 64, 10),    # Level 1
            DBlock(32, 32, 10)     # Level 2
        ])
        
        # Convs - channel reduction
        self.Convs = nn.ModuleList([
            ConvBlock(128, 64, 1, 1, 0),  # 0: 128->64
            ConvBlock(64, 32, 1, 1, 0)    # 1: 64->32
        ])
        
        # Output convs
        self.ConvsOut = nn.ModuleList([
            ConvBlock(128, 3, 3, 1, 1),  # 0: 128->3
            ConvBlock(64, 3, 3, 1, 1)    # 1: 64->3
        ])
        
        # Attention Feature Fusion
        self.AFFs = nn.ModuleList([
            AFF(32 + 64 + 128, 32),   # AFF0
            AFF(32 + 64 + 128, 64)    # AFF1
        ])
        
        # Supervised Attention Modules
        self.SCM1 = SCM(128, 128)
        self.SCM2 = SCM(64, 64)
        
        # Feature Attention Modules
        self.FAM1 = FAM(128)
        self.FAM2 = FAM(64)
    
    def forward(self, x):
        # Multi-scale inputs
        x_2 = F.interpolate(x, scale_factor=0.5, mode='bilinear', align_corners=False)
        x_4 = F.interpolate(x_2, scale_factor=0.5, mode='bilinear', align_corners=False)
        
        # Initial feature extraction
        z2 = self.feat_extract[0](x_2)       # 32 channels
        z4 = self.feat_extract[1](z2)        # 64 channels  
        z8 = self.feat_extract[2](z4)        # 128 channels
        
        # === Encoder path ===
        # Encoder level 0 (finest scale - 128 ch)
        e0 = self.Encoder[0](z8)
        e0_out = self.Convs[0](e0)           # 128 -> 64
        
        # Encoder level 1 (64 ch)
        z4_down = F.interpolate(z4, scale_factor=0.5, mode='bilinear', align_corners=False)
        e1 = self.Encoder[1](z4_down)
        e1_out = self.Convs[1](e1)           # 64 -> 32
        
        # Encoder level 2 (32 ch)
        z2_down = F.interpolate(z2, scale_factor=0.25, mode='bilinear', align_corners=False)
        e2 = self.Encoder[2](z2_down)
        
        # === Decoder path ===
        # Decoder level 0 (128 ch) - coarsest
        d0 = self.Decoder[0](e0)
        d0 = self.FAM1(d0)
        scm1 = self.SCM1(d0)
        d0 = d0 * scm1
        out_0 = self.ConvsOut[0](d0)
        out_0 = torch.tanh(out_0)
        
        # Decoder level 1 (64 ch)
        d0_up = self.Convs[0](d0)  # 128 -> 64
        d0_up = F.interpolate(d0_up, scale_factor=2, mode='bilinear', align_corners=False)
        
        # Fuse with encoder output
        d1_in = d0_up + e1
        d1 = self.Decoder[1](d1_in)
        d1 = self.FAM2(d1)
        scm2 = self.SCM2(d1)
        d1 = d1 * scm2
        out_1 = self.ConvsOut[1](d1)
        out_1 = torch.tanh(out_1)
        
        # Decoder level 2 (32 ch) - finest
        d1_up = self.Convs[1](d1)  # 64 -> 32
        d1_up = F.interpolate(d1_up, scale_factor=2, mode='bilinear', align_corners=False)
        
        # Final output
        d2_in = d1_up + e2
        d2 = self.Decoder[2](d2_in)
        
        # Upsample to final resolution
        out_final = self.feat_extract[4](d2)  # 32 -> 32 (upsample)
        out_final = self.feat_extract[5](out_final)  # 32 -> 3
        out_final = torch.tanh(out_final)
        
        # Upsample intermediate outputs to match input size
        out_0_up = F.interpolate(out_0, size=x.shape[2:], mode='bilinear', align_corners=False)
        out_1_up = F.interpolate(out_1, size=x.shape[2:], mode='bilinear', align_corners=False)
        
        return [out_final, out_1_up, out_0_up]


def create_model():
    """Create MIMO-UNet++ model"""
    return MIMOUNetPP()


if __name__ == "__main__":
    print("Testing MIMO-UNet++ architecture...")
    model = create_model()
    x = torch.randn(1, 3, 256, 256)
    
    with torch.no_grad():
        outputs = model(x)
    
    print(f"Input shape: {x.shape}")
    for i, out in enumerate(outputs):
        print(f"Output {i} shape: {out.shape}")
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    
    # Try loading weights
    try:
        checkpoint = torch.load('weights/mimo_unet.pkl', map_location='cpu')
        state_dict = checkpoint['model']
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        print(f"\nWeight loading:")
        print(f"Missing keys: {len(missing)}")
        print(f"Unexpected keys: {len(unexpected)}")
        if len(missing) > 0:
            print(f"First few missing: {missing[:5]}")
    except Exception as e:
        print(f"\nCouldn't load weights: {e}")

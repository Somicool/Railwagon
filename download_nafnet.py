"""
Download NAFNet pretrained weights for GoPro deblurring
"""
import os
import requests
from tqdm import tqdm

def download_file(url, dest_path):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    with open(dest_path, 'wb') as file, tqdm(
        desc=os.path.basename(dest_path),
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def main():
    print("Downloading NAFNet pretrained weights for GoPro deblurring...")
    print("This model achieves ~33 dB PSNR on GoPro dataset (much better than 25 dB)")
    print()
    
    # NAFNet GoPro weights URL (from official repository)
    url = "https://github.com/megvii-research/NAFNet/releases/download/v1.0/NAFNet-GoPro-width32.pth"
    dest = "weights/nafnet_gopro.pth"
    
    if os.path.exists(dest):
        print(f"✓ {dest} already exists")
        return
    
    try:
        download_file(url, dest)
        print(f"\n✓ Downloaded successfully to {dest}")
        print(f"✓ File size: {os.path.getsize(dest) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        print("\nAlternative: Download manually from:")
        print("https://github.com/megvii-research/NAFNet/releases/download/v1.0/NAFNet-GoPro-width32.pth")
        print(f"Save to: {os.path.abspath(dest)}")

if __name__ == '__main__':
    main()

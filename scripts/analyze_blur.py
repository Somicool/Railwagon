import cv2
import numpy as np
from pathlib import Path

blur_img = cv2.imread('train/train/blur/3821852741-preview_frame_00001.jpg')
sharp_img = cv2.imread('train/train/sharp/3821852741-preview_frame_00001.jpg')

print(f"Image size: {blur_img.shape}")
diff = cv2.absdiff(blur_img, sharp_img)
print(f"Average pixel difference: {diff.mean():.2f}")

# Check blur severity using Laplacian variance
lap_blur = cv2.Laplacian(blur_img, cv2.CV_64F).var()
lap_sharp = cv2.Laplacian(sharp_img, cv2.CV_64F).var()
print(f"Blur sharpness: {lap_blur:.2f}")
print(f"Sharp sharpness: {lap_sharp:.2f}")
print(f"Sharpness loss: {((lap_sharp - lap_blur) / lap_sharp * 100):.1f}%")

if lap_blur > 500:
    print("\n✓ Images are already quite sharp - deblurring has limited room for improvement")
elif lap_blur > 200:
    print("\n⚠ Moderate blur detected - deblurring can help but gains are limited")
else:
    print("\n✗ Severe blur detected - deblurring has high potential for improvement")

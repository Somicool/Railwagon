import cv2
from pathlib import Path

# Find wagon images
sessions_path = Path("railway_dashboard/backend/sessions")
wagon_images = list(sessions_path.rglob("wagon_*.jpg"))

if wagon_images:
    print(f"Found {len(wagon_images)} wagon images\n")
    
    for img_path in wagon_images[:5]:  # Check first 5
        img = cv2.imread(str(img_path))
        if img is not None:
            h, w = img.shape[:2]
            print(f"{img_path.name}: {w}x{h} pixels")
            if w > 1000:
                print("  ⚠️  This is a FULL FRAME (not zoomed)")
            else:
                print("  ✓ This is a ZOOMED region")
else:
    print("No wagon images found")

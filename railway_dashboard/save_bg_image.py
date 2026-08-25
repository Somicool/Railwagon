"""
Save the train background image for the dashboard.
Place your train.jpg image in this folder and run this script.
"""
import os
from pathlib import Path

# This script expects you to manually place the train image here
# You can download it from the chat attachment and save it as 'train_source.jpg'
# then this will copy it to background.jpg

source = Path(__file__).parent / 'train_source.jpg'
dest = Path(__file__).parent / 'background.jpg'

if source.exists():
    import shutil
    shutil.copy(source, dest)
    print(f"✓ Background image saved to {dest}")
else:
    print(f"✗ Please save your train image as: {source}")
    print("  Then run this script again.")

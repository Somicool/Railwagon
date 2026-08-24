"""
Create a test video from test_sequence frames for pipeline testing.
"""
import cv2
from pathlib import Path

# Configuration
input_dir = Path("test_sequence")
output_video = "test_video.mp4"
fps = 10  # Frames per second

# Get frame paths
frame_paths = sorted(input_dir.glob("frame_*.png"))

if not frame_paths:
    print("No frames found in test_sequence/")
    exit(1)

print(f"Found {len(frame_paths)} frames")

# Read first frame to get dimensions
first_frame = cv2.imread(str(frame_paths[0]))
height, width = first_frame.shape[:2]

print(f"Frame size: {width}x{height}")

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

# Write frames (repeat each frame multiple times to make video longer)
repeats = 3  # Repeat each frame 3 times for better temporal fusion testing

for frame_path in frame_paths:
    frame = cv2.imread(str(frame_path))
    for _ in range(repeats):
        out.write(frame)
    print(f"Added {frame_path.name}")

out.release()

total_frames = len(frame_paths) * repeats
duration = total_frames / fps

print(f"\n✓ Video created: {output_video}")
print(f"  - Total frames: {total_frames}")
print(f"  - Duration: {duration:.2f} seconds")
print(f"  - FPS: {fps}")

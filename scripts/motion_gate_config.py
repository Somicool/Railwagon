# Motion Gate Configuration File
# ================================

# DroidCam Settings
# -----------------
# Change this to your DroidCam IP address
# You can find it in the DroidCam app on your phone
DROIDCAM_URL = "http://192.168.1.6:4747/video"

# Alternative: Use local webcam
# DROIDCAM_URL = 0  # Use local webcam index 0

# Motion Detection Sensitivity
# -----------------------------
# Higher values = less sensitive (fewer false positives)
# Lower values = more sensitive (may trigger on small movements)

MOTION_THRESHOLD = 25.0  
# Recommended range: 15-35
# 15 = Very sensitive (detects small movements)
# 25 = Balanced (default)
# 35 = Very conservative (only large movements)

MIN_CONTOUR_AREA = 8000
# Minimum size of moving object to be considered
# Recommended range: 5000-15000
# 5000 = Small objects trigger motion
# 8000 = Balanced (default)
# 15000 = Only very large objects

FRAMES_TO_CONFIRM_TRAIN = 15
# How many consecutive motion frames needed to activate
# Recommended range: 10-25
# 10 = Quick response
# 15 = Balanced (default)
# 25 = Very conservative

FRAMES_NO_MOTION_TO_STOP = 60
# How many frames with no motion before stopping
# Recommended range: 30-120
# 30 = Quick stop
# 60 = Balanced (default)
# 120 = Long trains with gaps

# Background Learning
# -------------------
LEARNING_FRAMES = 30
# How many frames to learn background before detecting
# Recommended: 20-50

BG_HISTORY = 200
# Number of frames for background model
# Higher = more stable but slower adaptation

BG_VAR_THRESHOLD = 50
# Sensitivity of background subtraction
# Higher = less sensitive
# Recommended range: 30-80

BG_LEARNING_RATE = 0.001
# How fast background adapts to changes
# Lower = more stable (recommended for static scenes)
# Higher = adapts faster (for changing environments)

# Output Settings
# ---------------
SAVE_FRAMES = True  # Set to False to just detect without saving
OUTPUT_FOLDER = "motion_gate_output"

# Display Settings
# ----------------
SHOW_PREVIEW = True  # Show live video window
SHOW_MOTION_MASK = True  # Show motion detection visualization

# ================================
# TUNING GUIDE
# ================================
#
# Problem: Too many false positives (capturing when no train)
# Solution: 
#   - Increase MOTION_THRESHOLD (25 -> 30)
#   - Increase MIN_CONTOUR_AREA (8000 -> 12000)
#   - Increase FRAMES_TO_CONFIRM_TRAIN (15 -> 20)
#   - Increase BG_VAR_THRESHOLD (50 -> 70)
#
# Problem: Missing trains (not detecting)
# Solution:
#   - Decrease MOTION_THRESHOLD (25 -> 18)
#   - Decrease MIN_CONTOUR_AREA (8000 -> 5000)
#   - Decrease FRAMES_TO_CONFIRM_TRAIN (15 -> 10)
#   - Decrease BG_VAR_THRESHOLD (50 -> 35)
#
# Problem: Recording stops too early (during train)
# Solution:
#   - Increase FRAMES_NO_MOTION_TO_STOP (60 -> 90)
#   - Decrease MOTION_THRESHOLD (25 -> 20)
#
# Problem: Recording doesn't stop after train passes
# Solution:
#   - Decrease FRAMES_NO_MOTION_TO_STOP (60 -> 45)
#   - Increase MOTION_THRESHOLD (25 -> 28)

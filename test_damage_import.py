"""
Test damage detector import in live processor context
"""
import sys
from pathlib import Path

print("="*60)
print("Testing Damage Detector Import")
print("="*60)

# Simulate the import exactly as in live processors
try:
    current_file = Path(__file__).resolve()
    backend_path = current_file.parent / 'railway_dashboard' / 'backend'
    print(f"Looking for damage_detector at: {backend_path}")
    print(f"Path exists: {backend_path.exists()}")
    
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
        print(f"Added to sys.path: {backend_path}")
    
    from damage_detector import WagonDamageDetector
    DAMAGE_DETECTION_AVAILABLE = True
    print("✓ WagonDamageDetector imported successfully")
    
    # Try to initialize it
    print("\nInitializing damage detector...")
    detector = WagonDamageDetector(device='cpu')
    print("✓ Damage detector initialized successfully")
    
    # Test with a dummy image
    import cv2
    import numpy as np
    print("\nTesting with dummy image...")
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.detect_damage(test_img)
    print(f"✓ Damage detection ran successfully")
    print(f"  Result keys: {result.keys()}")
    print(f"  has_damage: {result['has_damage']}")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    
except ImportError as e:
    print(f"✗ ImportError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

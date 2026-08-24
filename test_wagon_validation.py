"""
Test updated wagon number validation rules:
- 8 digits = NO letters (pure numeric)
- 6-7 digits = can have 1-3 letter prefix
"""
import sys
sys.path.append('.')
from ocr_pipeline import OCRPipeline

# Initialize OCR
ocr = OCRPipeline(output_dir='test_output')

# Test cases
test_cases = [
    # 8 digits - should be PURE NUMERIC (no letters)
    ("12345678", True, "✓ Valid: 8 pure digits"),
    ("A12345678", False, "✗ Invalid: 8 digits cannot have letters"),
    ("AB12345678", False, "✗ Invalid: 8 digits cannot have letters"),
    
    # 6-7 digits with letters - ALLOWED
    ("A123456", True, "✓ Valid: 1 letter + 6 digits"),
    ("AB123456", True, "✓ Valid: 2 letters + 6 digits"),
    ("ABC123456", True, "✓ Valid: 3 letters + 6 digits"),
    ("A1234567", True, "✓ Valid: 1 letter + 7 digits"),
    ("AB1234567", True, "✓ Valid: 2 letters + 7 digits"),
    
    # Invalid cases
    ("123456", False, "✗ Invalid: 6 pure digits (need letters OR 8 digits)"),
    ("1234567", False, "✗ Invalid: 7 pure digits (need letters OR 8 digits)"),
    ("ABCD123456", False, "✗ Invalid: too many letters"),
    ("A12345", False, "✗ Invalid: too short"),
]

print("=" * 80)
print("WAGON NUMBER VALIDATION TEST")
print("=" * 80)
print("\nRULES:")
print("  • 8 digits = PURE NUMERIC (NO letters)")
print("  • 6-7 digits = CAN have 1-3 letter prefix")
print("\n" + "=" * 80)

passed = 0
failed = 0

for text, expected, description in test_cases:
    result = ocr._is_valid_wagon_number(text)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status} | {text:15s} → {result:5} | {description}")

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 80)

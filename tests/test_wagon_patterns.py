"""
Wagon Number Pattern Validation Test
Shows which formats are now recognized.
"""

import re

def is_valid_wagon_number(text):
    """
    Check if text matches valid wagon number patterns.
    
    Valid patterns:
    - 8 digits: 12345678
    - 7 digits: 1234567
    - 6 digits: 123456
    - 1 letter + 6 digits: A123456
    - 2 letters + 5-6 digits: AB12345
    - Multiple letters + digits (4-12 chars total)
    """
    if not text or len(text) < 4 or len(text) > 12:
        return False
    
    # Pattern 1: All digits (6-8 digits common)
    if text.isdigit() and len(text) >= 6:
        return True
    
    # Pattern 2: Starts with 1-3 letters, rest digits
    letter_match = re.match(r'^([A-Z]{1,3})([0-9]{4,9})$', text)
    if letter_match:
        return True
    
    # Pattern 3: Mixed alphanumeric (must have at least 3 digits)
    digit_count = sum(c.isdigit() for c in text)
    letter_count = sum(c.isalpha() for c in text)
    
    if digit_count >= 3 and (letter_count >= 1 or digit_count >= 6):
        return True
    
    return False


# Test cases
test_cases = [
    # 8-digit numbers
    ("12345678", True, "8 digits"),
    ("87654321", True, "8 digits"),
    
    # 7-digit numbers
    ("1234567", True, "7 digits"),
    
    # 6-digit numbers
    ("123456", True, "6 digits"),
    ("740512", True, "6 digits"),
    
    # Letter + digits
    ("A123456", True, "1 letter + 6 digits"),
    ("B654321", True, "1 letter + 6 digits"),
    ("AB12345", True, "2 letters + 5 digits"),
    ("ABC1234", True, "3 letters + 4 digits"),
    
    # With hyphens (after cleaning)
    ("7405012", True, "7 digits"),
    ("034230", True, "6 digits"),
    
    # Invalid cases
    ("12345", False, "Only 5 digits"),
    ("ABC", False, "Only 3 letters"),
    ("12", False, "Only 2 digits"),
    ("ABCD", False, "Only 4 letters"),
    
    # Edge cases
    ("A12345678", True, "1 letter + 8 digits"),
    ("AB123456", True, "2 letters + 6 digits"),
]

print("="*70)
print("WAGON NUMBER PATTERN VALIDATION TEST")
print("="*70)

passed = 0
failed = 0

for text, expected, description in test_cases:
    result = is_valid_wagon_number(text)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | {text:12} | Expected: {str(expected):5} | Got: {str(result):5} | {description}")

print("="*70)
print(f"Results: {passed} passed, {failed} failed")
print("="*70)

print("\n" + "="*70)
print("SUPPORTED WAGON NUMBER FORMATS")
print("="*70)
print("\n✓ Numeric formats:")
print("  • 6 digits: 123456, 740512")
print("  • 7 digits: 1234567, 7405012")
print("  • 8 digits: 12345678, 87654321")
print("\n✓ Alphanumeric formats:")
print("  • 1 letter + 6 digits: A123456, B654321")
print("  • 2 letters + 5 digits: AB12345, CD67890")
print("  • 3 letters + 4 digits: ABC1234, XYZ9876")
print("  • Mixed (4-12 chars with 3+ digits)")
print("\n✓ With separators:")
print("  • Hyphens: 12-3456, A-123456 (cleaned to: 123456, A123456)")
print("  • Spaces: 12 3456, A 123456 (cleaned to: 123456, A123456)")
print("\n✓ Text merging:")
print("  • Splits auto-merged: '12' + '3456' → '123456'")
print("  • Close detections combined automatically")
print("="*70)

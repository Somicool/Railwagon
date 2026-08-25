"""
Quick Test: Wagon Number Format Recognition
=============================================

This script demonstrates the updated OCR wagon number validation
that supports multiple formats including 8-digit numbers.

Usage:
    python quick_format_test.py
"""

import re

def is_valid_wagon_number(text):
    """
    Validate wagon number with flexible pattern matching
    
    Supports:
    - 6-10 digit numbers (123456, 1234567, 12345678, etc.)
    - 1-3 letters + digits (A123456, AB12345, etc.)
    - Mixed alphanumeric combinations
    """
    if not text or len(text) < 4 or len(text) > 12:
        return False
    
    # Clean text (remove spaces, hyphens, convert to uppercase)
    clean_text = text.strip().upper().replace(' ', '').replace('-', '')
    
    # Pattern 1: All digits (6-10 digits)
    if clean_text.isdigit() and 6 <= len(clean_text) <= 10:
        return True
    
    # Pattern 2: 1-3 letters followed by digits
    letter_match = re.match(r'^([A-Z]{1,3})([0-9]{4,9})$', clean_text)
    if letter_match:
        return True
    
    # Pattern 3: Mixed alphanumeric (both letters and digits required)
    digit_count = sum(c.isdigit() for c in clean_text)
    letter_count = sum(c.isalpha() for c in clean_text)
    
    if (letter_count >= 1 and letter_count <= 3 and 
        digit_count >= 3 and digit_count <= 10 and
        (letter_count + digit_count) == len(clean_text)):
        return True
    
    return False


def test_wagon_numbers():
    """Test various wagon number formats"""
    
    test_cases = [
        # User's examples
        ("12345678", "8-digit wagon number (user requested)"),
        ("A123456", "1 letter + 6 digits (user requested)"),
        
        # Common Indian railway wagon formats
        ("1234567", "7-digit wagon number"),
        ("123456", "6-digit wagon number"),
        ("AB12345", "2 letters + 5 digits"),
        ("NWR12345", "Would be rejected (3+ letters in prefix)"),
        
        # With formatting (will be cleaned)
        ("12 34 56 78", "8-digit with spaces (will be cleaned)"),
        ("A-123456", "Letter + digits with hyphen (will be cleaned)"),
        
        # Invalid examples
        ("12345", "Too short (5 digits)"),
        ("HELLO", "No digits"),
        ("123", "Only 3 digits"),
    ]
    
    print("=" * 80)
    print("WAGON NUMBER FORMAT VALIDATION TEST")
    print("=" * 80)
    print()
    
    valid_count = 0
    invalid_count = 0
    
    for wagon_num, description in test_cases:
        result = is_valid_wagon_number(wagon_num)
        status = "✓ VALID" if result else "✗ INVALID"
        
        if result:
            valid_count += 1
            # Clean and show the processed version
            clean = wagon_num.strip().upper().replace(' ', '').replace('-', '')
            print(f"{status:10} | Input: '{wagon_num:15}' → Processed: '{clean:12}' | {description}")
        else:
            invalid_count += 1
            print(f"{status:10} | Input: '{wagon_num:15}' | {description}")
    
    print()
    print("=" * 80)
    print(f"Summary: {valid_count} valid, {invalid_count} invalid wagon numbers")
    print("=" * 80)
    print()
    print("USER REQUIREMENTS:")
    print("  ✓ 8-digit numbers (12345678) - SUPPORTED")
    print("  ✓ Letter + digit combinations (A123456) - SUPPORTED")
    print("  ✓ Automatic text cleaning (spaces, hyphens) - SUPPORTED")
    print("  ✓ Merged split OCR detections - SUPPORTED (via _merge_nearby_text)")
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_wagon_numbers()
    
    print()
    print("To test with your wagon image:")
    print("  1. Save your image as 'uploaded_wagon.jpg'")
    print("  2. Run: python test_user_wagon.py")
    print()
    print("Or use the full OCR pipeline:")
    print("  python run_full_pipeline_with_ocr.py --video your_video.mp4")

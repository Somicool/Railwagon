# Wagon Damage Detection - Testing Guide

## Prerequisites
- Railway dashboard backend running
- Frontend accessible via browser
- Sample wagon images/videos (with and without damage)

## Test Scenarios

### Test 1: Single Image Processing (No Damage)

**Steps:**
1. Navigate to **IMAGE INSPECTION** page
2. Upload a clear wagon image (no visible damage)
3. Click "PROCESS IMAGE"
4. Wait for processing to complete

**Expected Result:**
```
✓ NO DAMAGE DETECTED
[Green indicator displayed below comparison section]
```

---

### Test 2: Single Image Processing (With Damage)

**Steps:**
1. Navigate to **IMAGE INSPECTION** page
2. Upload a wagon image with visible cracks/broken glass
3. Click "PROCESS IMAGE"
4. Wait for processing to complete

**Expected Result:**
```
⚠ DAMAGE DETECTED - [CRACK/BROKEN_GLASS/STRUCTURAL]
[Red pulsing indicator displayed]

Damage Details:
- Damage Count: [Number]
- Damage Type: [Type]
- Confidence: [Percentage]
- Clickable preview of annotated damage image
```

---

### Test 3: Live Video Inspection

**Steps:**
1. Navigate to **LIVE VIDEO INSPECTION** page
2. Click "START VIDEO FEED"
3. Once video appears, click "START INSPECTION"
4. Point camera at wagons (with or without damage)
5. Observe damage detection panel in real-time

**Expected Result:**
- Panel updates in real-time as frames are processed
- Shows "NO DAMAGE" for clean wagons
- Shows "DAMAGE DETECTED" when damage appears
- Statistics update automatically (total damages, types, confidence)
- Recent detections list updates with new finds

---

### Test 4: Recorded Video Processing

**Steps:**
1. Navigate to **RECORDED VIDEO INSPECTION** page
2. Upload a video file containing wagon footage
3. Click "START INSPECTION"
4. Monitor progress

**Expected Result:**
- Damage detection panel updates as video processes
- Shows cumulative damage statistics
- Lists all detected damages with frame numbers
- Updates in real-time during processing

---

### Test 5: Historical Records Review

**Steps:**
1. Complete Test 2, 3, or 4 (ensure some damage was detected)
2. Navigate to **RECORDS** page
3. Find the session you just completed
4. Click on the session card

**Expected Result:**
- Session details modal opens
- If damage was detected, shows "⚠ DAMAGE DETECTIONS (X FOUND)" section
- Displays:
  - Total damages count
  - Number of damage types
  - Average confidence percentage
  - List of all detected damages with frame numbers and confidence
  - Ability to scroll through all damage detections

---

### Test 6: No Damage Session in Records

**Steps:**
1. Complete an inspection where no damage is detected
2. Navigate to **RECORDS** page
3. Click on the clean session

**Expected Result:**
- Session details modal opens
- No "DAMAGE DETECTIONS" section appears (only shown when damage exists)
- All other session info displays normally

---

## Verification Checklist

### Backend Integration
- [ ] Damage detector loads without errors
- [ ] Detections saved to session data
- [ ] Damage images saved to wagon_detections folder
- [ ] API returns damage_detections array
- [ ] API returns damage metadata for images

### Frontend Display
- [ ] Damage section appears on Live page
- [ ] Damage section appears on Recorded page
- [ ] Damage section appears on Image page
- [ ] "No damage" shows green indicator
- [ ] "Has damage" shows red pulsing indicator
- [ ] Statistics display correctly
- [ ] Recent detections list updates
- [ ] Damage info grid shows correct data

### Records Integration
- [ ] Damage count shown in session summary (if > 0)
- [ ] Damage section appears in session details (if > 0)
- [ ] All damage detections listed correctly
- [ ] Frame numbers match detections
- [ ] Confidence percentages display correctly

### Edge Cases
- [ ] Handles no camera gracefully
- [ ] Handles corrupted images
- [ ] Handles very low confidence detections
- [ ] Handles multiple damage types in one frame
- [ ] Handles sessions with 0 damage
- [ ] Handles sessions with many damages (50+)

---

## Sample Test Images

### Recommended Test Cases:

1. **Wagon with cracked window**
   - Should detect: CRACK type
   - Expected confidence: 60-90%

2. **Wagon with shattered glass**
   - Should detect: BROKEN_GLASS type
   - Expected confidence: 50-85%

3. **Wagon with damaged door frame**
   - Should detect: STRUCTURAL type
   - Expected confidence: 40-75%

4. **Clean wagon (no damage)**
   - Should detect: Nothing
   - Display: "NO DAMAGE DETECTED"

5. **Poor quality/blurry image**
   - May have lower confidence
   - Should still attempt detection

---

## Common Issues & Solutions

### Issue: Damage not detected on obviously damaged wagon
**Solution:**
- Check image quality (resolution, blur)
- Try processing as single image for better accuracy
- Verify deblurring is working correctly
- Check confidence threshold (may need adjustment)

### Issue: False positives (detecting damage when none exists)
**Solutions:**
- Check if detecting shadows as cracks
- Verify image is properly deblurred
- Look at confidence score (ignore <40%)
- Review annotated image to see what was detected

### Issue: Damage section not appearing
**Solutions:**
- Hard refresh browser (Ctrl+F5)
- Check browser console for JavaScript errors
- Verify backend is running and returning damage data
- Check API response includes damage_detections field

### Issue: Performance slow with damage detection
**Expected:**
- Adds ~50-100ms per frame
- If slower, check:
  - CPU usage
  - Image resolution (large images take longer)
  - Multiple detections per frame (complex damage)

---

## Performance Benchmarks

### Expected Processing Times:
- **Single Image:** +50-100ms (including damage detection)
- **Live Video:** 3-5 FPS with damage detection enabled
- **Recorded Video:** Similar to live, depends on frame skip rate

### Memory Usage:
- Minimal increase (<100MB additional RAM)
- One detector instance shared across all modes

---

## Debug Mode

To see detailed detection logs:

1. Open browser developer console (F12)
2. Look for messages like:
   ```
   [DAMAGE] Detected 2 damage(s): crack
   [DAMAGE] Confidence: 78%
   ```

3. Backend logs will show:
   ```
   Loading Wagon Damage Detector...
   Damage Detector loaded successfully
   ```

---

## Report Issues

If you encounter problems:

1. **Check Browser Console** - Look for JavaScript errors
2. **Check Backend Logs** - Look for Python exceptions
3. **Verify API Response** - Use Network tab to see if damage_detections is returned
4. **Check File Paths** - Ensure damage images are being saved correctly

---

## Success Criteria

All tests pass if:
- ✅ All three inspection modes show damage section
- ✅ Damage correctly detected and displayed
- ✅ No damage shows green indicator
- ✅ Damage shows red pulsing indicator with details
- ✅ Records properly display damage information
- ✅ No errors in browser console
- ✅ No errors in backend logs
- ✅ Performance acceptable (< 200ms additional per frame)

---

## Next Steps After Testing

1. Gather sample wagon images with various damage types
2. Test with real-world video footage
3. Calibrate confidence thresholds based on results
4. Fine-tune detection parameters if needed
5. Train team on interpreting damage reports
6. Integrate into regular inspection workflow

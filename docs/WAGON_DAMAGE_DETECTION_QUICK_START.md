# Wagon Damage Detection - Quick Start Guide

## What It Does
Automatically detects and reports visible damage (cracks, broken glass, structural issues) on wagon windows and doors in real-time during inspections.

## Where to See It

### 1. Live Video Inspection
- Navigate to **LIVE VIDEO INSPECTION** page
- Start inspection (with or without auto mode)
- Look below the "BEFORE / AFTER COMPARISON" section
- See "WAGON DAMAGE DETECTION" panel

### 2. Recorded Video Inspection
- Navigate to **RECORDED VIDEO INSPECTION** page
- Upload and process a video
- Look below the "BEFORE / AFTER COMPARISON" section
- See "WAGON DAMAGE DETECTION" panel

### 3. Image Inspection
- Navigate to **IMAGE INSPECTION** page
- Upload an image and process it
- Look below the wagon number detection
- See "WAGON DAMAGE DETECTION" panel

### 4. Historical Records
- Navigate to **RECORDS** page
- Click any session to view details
- If damage was detected, see "⚠ DAMAGE DETECTIONS" section
- View complete list of all damages found

## What You'll See

### When NO Damage:
```
┌────────────────────────────────────┐
│  ✓ NO DAMAGE DETECTED              │
│  [Green indicator]                 │
└────────────────────────────────────┘
```

### When Damage IS Detected:
```
┌────────────────────────────────────┐
│  ⚠ DAMAGE DETECTED - CRACK         │
│  [Red pulsing indicator]           │
├────────────────────────────────────┤
│  Total Damages:     5              │
│  Damage Types:      2              │
│  Avg Confidence:    78%            │
│  Latest Frame:      #127           │
├────────────────────────────────────┤
│  Recent Detections:                │
│  • CRACK (Frame 127) - 85%         │
│  • BROKEN GLASS (Frame 115) - 72%  │
│  • CRACK (Frame 98) - 80%          │
└────────────────────────────────────┘
```

## Damage Types Detected

| Type | Description | Visual Indicator |
|------|-------------|------------------|
| **CRACK** | Linear fractures, thin elongated patterns | Red bounding box |
| **BROKEN GLASS** | Shattered glass, high texture variance | Orange bounding box |
| **STRUCTURAL** | Damaged frames, irregular shapes | Yellow bounding box |

## How to Use

### Automatic Mode (Recommended)
1. Start any inspection (live, recorded, or image)
2. System automatically checks every frame
3. Damage appears in real-time below comparison section
4. No user action required

### Manual Review
1. After inspection completes, go to **RECORDS**
2. Click on the session
3. Scroll to "DAMAGE DETECTIONS" section
4. View all detected damages with frame numbers
5. Click damage images to view annotated versions

## Saved Files

For each detected damage, the system saves:
- `damage_XXXXXX.jpg` - Annotated image with bounding boxes
- Located in: `sessions/{session_id}/wagon_detections/`

## Tips

1. **Better Detection:** 
   - Ensure good lighting
   - Use deblurred frames for analysis
   - Higher resolution = better accuracy

2. **False Positives:**
   - May detect shadows or reflections as damage
   - Check confidence score (>70% is reliable)
   - Verify with annotated image

3. **Performance:**
   - Damage detection adds ~50-100ms per frame
   - Minimal impact on overall processing
   - Runs in parallel with OCR

## Troubleshooting

**Q: Damage section not showing?**
- Refresh the page
- Check browser console for errors
- Ensure backend is running

**Q: "NO DAMAGE DETECTED" but damage visible?**
- Damage may be too subtle
- Check if frame is properly deblurred
- Try processing the frame as a single image

**Q: Too many false positives?**
- Lower confidence threshold in code
- Adjust detection sensitivity
- Use better quality video/images

## Example Workflow

1. **Start Live Inspection:**
   ```
   Dashboard → Live Video → Start Inspection
   ```

2. **Monitor in Real-Time:**
   ```
   Watch "WAGON DAMAGE DETECTION" section
   Green = All Clear
   Red = Damage Found!
   ```

3. **Review After Inspection:**
   ```
   Stop Inspection → Go to Records
   Click session → View "DAMAGE DETECTIONS"
   ```

4. **View Details:**
   ```
   See all frames with damage
   Check confidence scores
   Click to enlarge annotated images
   ```

## Integration with Existing Features

- ✅ Works with Live Video
- ✅ Works with Recorded Video  
- ✅ Works with Single Images
- ✅ Stored in Historical Records
- ✅ Appears in Session Details
- ✅ Real-time updates during inspection

## API Response Structure

```javascript
{
    "damage_detections": [
        {
            "frame": 127,
            "damage_type": "crack",
            "damage_types": ["crack"],
            "confidence": 0.85,
            "damage_count": 2
        },
        // ... more detections
    ]
}
```

## Color Coding

| Status | Color | Meaning |
|--------|-------|---------|
| ✓ No Damage | Green (#4caf50) | Wagon is in good condition |
| ⚠ Damage | Red (#d32f2f) | Damage detected, needs attention |

## Questions?

Check the main implementation summary: `WAGON_DAMAGE_DETECTION_SUMMARY.md`

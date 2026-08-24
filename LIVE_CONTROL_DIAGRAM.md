# Live Control Flow Diagram

## Terminal Control Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   PROGRAM STARTS                             │
│                                                              │
│  python live_simple_control.py                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              PRINT WELCOME MESSAGE                           │
│                                                              │
│  "Type 'start' to begin live processing"                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 WAIT FOR INPUT                               │
│                                                              │
│  while True:                                                 │
│      cmd = input("Command: ")                                │
│      if cmd == 'start':                                      │
│          break                                               │
│                                                              │
│  USER TYPES HERE ───────────────────────────────────┐       │
│                                                      │       │
│  Valid: "start" ─────────────────────────────► CONTINUE     │
│  Invalid: "xyz" ──────────────────────────► ASK AGAIN       │
│  Exit: "quit" ─────────────────────────────► EXIT           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            INITIALIZE PROCESSOR                              │
│                                                              │
│  processor = SimpleLiveProcessor(                            │
│      model_path='weights/gopro_best.pth',                    │
│      buffer_size=3,                                          │
│      save_interval=30                                        │
│  )                                                           │
│                                                              │
│  - Load deblurring model                                     │
│  - Create output directories                                 │
│  - Setup frame buffer                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 OPEN DROIDCAM                                │
│                                                              │
│  cap = cv2.VideoCapture(0)                                   │
│                                                              │
│  if not cap.isOpened():                                      │
│      print("ERROR: Could not open camera!")                  │
│      return                                                  │
│                                                              │
│  ✓ SUCCESS → Continue                                       │
│  ✗ FAILED  → Exit with error message                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            MAIN PROCESSING LOOP                              │
│                                                              │
│  while True:                                                 │
│      ┌────────────────────────────────────┐                 │
│      │ 1. Read frame                      │                 │
│      │    ret, frame = cap.read()         │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 2. Deblur frame                    │                 │
│      │    deblurred = model(frame)        │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 3. Add to buffer                   │                 │
│      │    buffer.append(deblurred)        │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 4. Temporal fusion                 │                 │
│      │    fused = median(buffer)          │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 5. Text enhancement                │                 │
│      │    enhanced = CLAHE(fused)         │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 6. Display video window            │                 │
│      │    cv2.imshow('Live', enhanced)    │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 7. Save at intervals               │                 │
│      │    if count % 30 == 0:             │                 │
│      │        save_frame(...)             │                 │
│      └──────────────┬─────────────────────┘                 │
│                     │                                        │
│      ┌─────────────▼──────────────────────┐                 │
│      │ 8. Check for 'q' key               │                 │
│      │    key = cv2.waitKey(1)            │                 │
│      │    if key == ord('q'):             │                 │
│      │        break ──────────────┐       │                 │
│      └────────────────────────────┼───────┘                 │
│                                   │                          │
│      NO STOP ─────────────────────┘                         │
│      (loop continues)              ▼                         │
└────────────────────────────────────┼─────────────────────────┘
                                     │
                        STOP REQUESTED
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   CLEANUP                                    │
│                                                              │
│  finally:                                                    │
│      cap.release()                                           │
│      cv2.destroyAllWindows()                                 │
│                                                              │
│  This ALWAYS runs, even if:                                  │
│    - Error occurs                                            │
│    - Ctrl+C pressed                                          │
│    - Script crashes                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  PRINT SUMMARY                               │
│                                                              │
│  "LIVE PROCESSING STOPPED SUCCESSFULLY"                      │
│  "Total frames processed: 150"                               │
│  "Frame sets saved: 5"                                       │
│  "Results saved in: live_simple_output"                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  PROGRAM ENDS                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Stop Conditions - Two Paths

### Path 1: Press 'q' in Video Window (Recommended)

```
                    [Video Window Open]
                            │
                            │ User sees live feed
                            │
                            ▼
                   ┌─────────────────┐
                   │  User presses   │
                   │     'q' key     │
                   └────────┬────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │  cv2.waitKey(1) detects  │
              │  key == ord('q')         │
              └────────┬─────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │  break from loop         │
              └────────┬─────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │  Run cleanup (finally)   │
              │  - cap.release()         │
              │  - cv2.destroyAllWindows │
              └────────┬─────────────────┘
                       │
                       ▼
                   [STOPPED]
```

### Path 2: Type 'stop' in Terminal (Threaded Version Only)

```
                [Processing Running]
                        │
                        │ Separate thread listening
                        │
                        ▼
               ┌─────────────────┐
               │  User types     │
               │    'stop'       │
               └────────┬────────┘
                        │
                        ▼
          ┌──────────────────────────┐
          │ Thread detects 'stop'    │
          │ Sets running = False     │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │ Main loop checks flag    │
          │ Sees running == False    │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │  break from loop         │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │  Run cleanup (finally)   │
          └────────┬─────────────────┘
                   │
                   ▼
               [STOPPED]
```

---

## Frame Processing Pipeline - Detailed

```
┌────────────────────────────────────────────────────────────┐
│                     RAW FRAME                               │
│  DroidCam captures 1920x1080 BGR image                     │
│                                                             │
│  frame = cap.read()                                         │
│  Shape: (1080, 1920, 3)                                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│                 PREPROCESSING                               │
│                                                             │
│  1. BGR → RGB:     frame_rgb = cv2.cvtColor(...)           │
│  2. Normalize:     frame_norm = frame / 255.0              │
│  3. To tensor:     tensor = torch.from_numpy(...)          │
│  4. Reshape:       (H,W,C) → (1,C,H,W)                     │
│  5. To device:     tensor.to('cuda')                       │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│                   DEBLURRING                                │
│                                                             │
│  with torch.no_grad():                                      │
│      output = model(input_tensor)                           │
│                                                             │
│  MIMO-UNet+ Model:                                          │
│    - Multi-scale processing                                 │
│    - Encoder-decoder architecture                           │
│    - Skip connections                                       │
│    - Output: sharp image tensor                             │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│                POSTPROCESSING                               │
│                                                             │
│  1. To CPU:        output.cpu()                             │
│  2. Reshape:       (1,C,H,W) → (H,W,C)                     │
│  3. Denormalize:   output * 255                             │
│  4. Clip:          np.clip(0, 255)                          │
│  5. To uint8:      .astype(np.uint8)                        │
│  6. RGB → BGR:     cv2.cvtColor(...)                       │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│              FRAME BUFFER (FIFO)                            │
│                                                             │
│  deque(maxlen=3):                                           │
│  ┌──────┬──────┬──────┐                                    │
│  │Frame │Frame │Frame │                                    │
│  │ t-2  │ t-1  │  t   │                                    │
│  └──────┴──────┴──────┘                                    │
│                                                             │
│  When new frame arrives:                                    │
│  ┌──────┬──────┬──────┐                                    │
│  │Frame │Frame │Frame │← New                               │
│  │ t-1  │  t   │ t+1  │                                    │
│  └──────┴──────┴──────┘                                    │
│   Oldest dropped automatically                              │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│             TEMPORAL FUSION                                 │
│                                                             │
│  Stack frames:                                              │
│  frames_array = np.array([frame1, frame2, frame3])          │
│  Shape: (3, H, W, 3)                                        │
│                                                             │
│  Compute median:                                            │
│  fused = np.median(frames_array, axis=0)                    │
│                                                             │
│  Effect:                                                    │
│    - Reduces temporal noise                                 │
│    - Sharpens consistent features                           │
│    - Smooths out inconsistencies                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│           TEXT ENHANCEMENT                                  │
│                                                             │
│  Step 1: Convert to LAB color space                         │
│    lab = cv2.cvtColor(frame, COLOR_BGR2LAB)                 │
│    l, a, b = cv2.split(lab)                                 │
│                                                             │
│  Step 2: Apply CLAHE to L channel                           │
│    clahe = cv2.createCLAHE(clipLimit=3.0)                   │
│    l_enhanced = clahe.apply(l)                              │
│                                                             │
│  Step 3: Merge back                                         │
│    enhanced = cv2.merge([l_enhanced, a, b])                 │
│    enhanced = cv2.cvtColor(enhanced, COLOR_LAB2BGR)         │
│                                                             │
│  Step 4: Sharpen                                            │
│    kernel = [[-1,-1,-1],                                    │
│              [-1, 9,-1],                                    │
│              [-1,-1,-1]]                                    │
│    sharpened = cv2.filter2D(enhanced, kernel)               │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│              DISPLAY & SAVE                                 │
│                                                             │
│  Display:                                                   │
│    - Resize to 960x540 for screen                           │
│    - Add text overlay (frame count, instructions)           │
│    - cv2.imshow('Live Processing', display)                 │
│                                                             │
│  Save (every 30 frames):                                    │
│    - raw_00001_timestamp.jpg                                │
│    - deblurred_00001_timestamp.jpg                          │
│    - enhanced_00001_timestamp.jpg                           │
└────────────────────────────────────────────────────────────┘
```

---

## Camera Safety - Why It Never Locks

```
┌──────────────────────────────────────────────┐
│  try:                                         │
│      cap = cv2.VideoCapture(0)                │
│      while True:                              │
│          ret, frame = cap.read()              │
│          # Process...                         │
│                                               │
│          if cv2.waitKey(1) == ord('q'):       │
│              break                            │
│                                               │
├──────────────────────────────────────────────┤
│  except KeyboardInterrupt:                    │
│      print("Ctrl+C detected")                 │
│                                               │
├──────────────────────────────────────────────┤
│  except Exception as e:                       │
│      print(f"Error: {e}")                     │
│                                               │
├──────────────────────────────────────────────┤
│  finally:                                     │
│      # ⭐ THIS ALWAYS RUNS ⭐                │
│      cap.release()                            │
│      cv2.destroyAllWindows()                  │
│                                               │
│  # Camera is released no matter what!         │
└──────────────────────────────────────────────┘

Guaranteed execution paths:

  Normal exit (press 'q')  ──────┐
                                  │
  Ctrl+C (KeyboardInterrupt) ────┤
                                  ├──► finally: cap.release()
  Exception (any error) ─────────┤
                                  │
  Power loss... ✗ (only case) ───┘
```

---

## Comparison: With vs Without Threading

### Without Threading (Simple Version)

```
┌────────────────────────────────────┐
│  Main Thread                        │
│                                     │
│  ┌──────────────────┐               │
│  │ Wait for 'start' │               │
│  │ (blocking input) │               │
│  └────────┬─────────┘               │
│           │                         │
│           ▼                         │
│  ┌──────────────────┐               │
│  │ Initialize       │               │
│  └────────┬─────────┘               │
│           │                         │
│           ▼                         │
│  ┌──────────────────┐               │
│  │ Open camera      │               │
│  └────────┬─────────┘               │
│           │                         │
│           ▼                         │
│  ┌──────────────────┐               │
│  │ Process frames   │               │
│  │ (can't accept    │               │
│  │  terminal input) │               │
│  └────────┬─────────┘               │
│           │                         │
│           ▼                         │
│  ┌──────────────────┐               │
│  │ Check 'q' key    │               │
│  │ (cv2.waitKey)    │               │
│  └────────┬─────────┘               │
│           │                         │
│           ▼                         │
│  ┌──────────────────┐               │
│  │ Cleanup          │               │
│  └──────────────────┘               │
│                                     │
└────────────────────────────────────┘

STOP: Press 'q' only ✅
```

### With Threading (Advanced Version)

```
┌────────────────────┐  ┌────────────────────┐
│  Main Thread       │  │  Input Thread      │
│                    │  │                    │
│  ┌──────────────┐ │  │                    │
│  │ Initialize   │ │  │                    │
│  └──────┬───────┘ │  │                    │
│         │         │  │                    │
│         ▼         │  │                    │
│  ┌──────────────┐ │  │ ┌──────────────┐  │
│  │ Start thread ├─┼──┼►│ Listen for   │  │
│  └──────┬───────┘ │  │ │ 'stop' input │  │
│         │         │  │ └──────┬───────┘  │
│         ▼         │  │        │          │
│  ┌──────────────┐ │  │        ▼          │
│  │ Process      │ │  │ ┌──────────────┐  │
│  │ frames       │ │  │ │ if 'stop':   │  │
│  │              │ │  │ │   running =  │  │
│  │ Check:       │◄┼──┼─┤   False      │  │
│  │ - 'q' key    │ │  │ └──────────────┘  │
│  │ - running    │ │  │                    │
│  │   flag       │ │  │                    │
│  └──────┬───────┘ │  │                    │
│         │         │  │                    │
│         ▼         │  │                    │
│  ┌──────────────┐ │  │                    │
│  │ Cleanup      │ │  │                    │
│  └──────────────┘ │  │                    │
│                    │  │                    │
└────────────────────┘  └────────────────────┘

STOP: Press 'q' OR type 'stop' ✅
```

---

This diagram shows the complete control flow!

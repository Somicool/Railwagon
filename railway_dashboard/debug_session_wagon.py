"""
Debug script to check wagon numbers in session metadata
"""
import json
from pathlib import Path

# Find the sessions folder
sessions_folder = Path(__file__).parent / 'backend' / 'sessions'

print("=" * 60)
print("WAGON NUMBER DEBUG SCRIPT")
print("=" * 60)

if not sessions_folder.exists():
    print(f"ERROR: Sessions folder not found at {sessions_folder}")
    exit(1)

# Get all sessions
sessions = [d for d in sessions_folder.iterdir() if d.is_dir()]

if not sessions:
    print("No sessions found!")
    exit(0)

print(f"\nFound {len(sessions)} session(s)\n")

for session_dir in sorted(sessions):
    session_id = session_dir.name
    metadata_file = session_dir / 'metadata.json'
    
    if not metadata_file.exists():
        print(f"[{session_id}] No metadata.json found")
        continue
    
    print(f"\n{'='*60}")
    print(f"SESSION: {session_id}")
    print(f"{'='*60}")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Check wagon_detections folder and ALL files
    wagon_det_dir = session_dir / 'wagon_detections'
    if wagon_det_dir.exists():
        all_files = list(wagon_det_dir.glob('*'))
        jpg_files = list(wagon_det_dir.glob('*.jpg'))
        json_files = list(wagon_det_dir.glob('*.json'))
        wagon_files = list(wagon_det_dir.glob('wagon_*.jpg'))
        
        print(f"\n📁 wagon_detections folder:")
        print(f"   Total files: {len(all_files)}")
        print(f"   JPG files: {len(jpg_files)}")
        print(f"   Wagon JPG files (wagon_*.jpg): {len(wagon_files)}")
        print(f"   JSON files: {len(json_files)}")
        
        if wagon_files:
            print(f"\n   🎯 WAGON IMAGE FILES:")
            for wf in sorted(wagon_files)[:10]:
                print(f"      - {wf.name}")
                # Try to parse the filename
                try:
                    parts = wf.stem.split('_')
                    if len(parts) >= 3:
                        wagon_num = parts[1]
                        frame_num = int(parts[2])
                        print(f"        → Wagon: {wagon_num}, Frame: {frame_num:06d}")
                except:
                    pass
            if len(wagon_files) > 10:
                print(f"      ... and {len(wagon_files) - 10} more")
        
        if jpg_files and not wagon_files:
            print(f"\n   📋 OTHER JPG FILES:")
            for jf in sorted(jpg_files)[:5]:
                print(f"      - {jf.name}")
    else:
        print(f"\n📁 wagon_detections folder: ❌ Not found")
    
    # Check wagon_numbers array
    wagon_numbers = metadata.get('wagon_numbers', [])
    print(f"\n📊 wagon_numbers in metadata.json: {len(wagon_numbers)} entries")
    if wagon_numbers:
        for i, wn in enumerate(wagon_numbers[:3], 1):  # Show first 3
            print(f"  {i}. {json.dumps(wn, indent=4)}")
        if len(wagon_numbers) > 3:
            print(f"  ... and {len(wagon_numbers) - 3} more")
    else:
        print("  ❌ No wagon_numbers array in metadata")
    
    # Check deblurred frames
    deblurred_dir = session_dir / 'deblurred'
    if deblurred_dir.exists():
        deblurred_frames = list(deblurred_dir.glob('deblurred_*.jpg'))
        print(f"\n🖼️  Deblurred frames: {len(deblurred_frames)} files")
        if deblurred_frames:
            print(f"   First few: {', '.join([f.name for f in sorted(deblurred_frames)[:5]])}")
    else:
        print(f"\n🖼️  Deblurred frames: ❌ Folder not found")

print(f"\n{'='*60}")
print("DEBUG COMPLETE")
print(f"{'='*60}\n")

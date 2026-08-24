"""
rAIlwagon Inspection System - Flask Backend API
================================================

REST API server for railway wagon inspection system.
Integrates with existing deblurring and OCR pipelines.

Endpoints:
- POST /api/live/start - Start live video feed
- POST /api/live/stop - Stop live video feed
- POST /api/inspection/start - Start inspection (live or recorded)
- POST /api/inspection/stop - Stop inspection
- POST /api/image/process - Process single image
- GET /api/sessions - Get all inspection sessions
- GET /api/session/<id> - Get specific session details
- GET /api/analytics - Get aggregated analytics
- GET /api/stream - Live video stream (Server-Sent Events)

Author: Railway Wagon Inspection System
Date: December 25, 2025
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
import base64
import cv2
import numpy as np

# Add parent directories to path to import existing modules
# Go up two levels: backend -> railway_dashboard -> blur (where models/ is located)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from inspection_processor import InspectionProcessor

# Import AI Incident Manager
try:
    from incident_manager import (
        IncidentAIAgent,
        Incident,
        IncidentSeverity,
        IncidentStatus,
        IncidentType,
        create_incident_from_damage_detection
    )
    INCIDENT_AI_ENABLED = True
    print("✓ AI Incident Response Agent loaded")
except ImportError as e:
    INCIDENT_AI_ENABLED = False
    print(f"⚠ AI Incident Agent not available: {e}")

# Try to import DroidCam configuration
try:
    from droidcam_config import DROIDCAM_URL
    DEFAULT_VIDEO_SOURCE = DROIDCAM_URL
    print(f"✓ Using DroidCam: {DROIDCAM_URL}")
except ImportError:
    DEFAULT_VIDEO_SOURCE = 0
    print("⚠ DroidCam config not found, using camera 0")

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('uploads')
SESSIONS_FOLDER = Path('sessions')
DELETED_SESSIONS_FOLDER = Path('sessions_deleted')
UPLOAD_FOLDER.mkdir(exist_ok=True)
SESSIONS_FOLDER.mkdir(exist_ok=True)
DELETED_SESSIONS_FOLDER.mkdir(exist_ok=True)

# Global state
processor = InspectionProcessor()
active_sessions = {}

# Initialize AI Incident Agent
if INCIDENT_AI_ENABLED:
    incident_ai = IncidentAIAgent(db_path="incidents_db")
    print(f"✓ AI Agent initialized with {len(incident_ai.incidents)} historical incidents")
else:
    incident_ai = None


# ====================================================
# SERVE FRONTEND
# ====================================================

@app.route('/api/sessions/<path:filepath>')
def serve_session_file(filepath):
    """Serve session files (images, etc.)."""
    try:
        print(f"[INFO] Serving session file: {filepath}")
        file_path = SESSIONS_FOLDER / filepath
        print(f"[INFO] Full path: {file_path}")
        print(f"[INFO] File exists: {file_path.exists()}, Is file: {file_path.is_file() if file_path.exists() else 'N/A'}")
        
        if file_path.exists() and file_path.is_file():
            return send_from_directory(SESSIONS_FOLDER, filepath)
        else:
            print(f"[ERROR] File not found: {file_path}")
            return jsonify({'status': 'error', 'message': f'File not found: {filepath}'}), 404
    except Exception as e:
        print(f"[ERROR] serve_session_file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def serve_frontend():
    """Serve the main HTML page."""
    return send_from_directory('..', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('..', path)


# ====================================================
# LIVE VIDEO ENDPOINTS
# ====================================================

@app.route('/api/live/start', methods=['POST'])
def start_live_video():
    """Start live video feed from camera."""
    try:
        data = request.get_json() or {}
        # Use DroidCam URL by default, or device_id if provided
        video_source = data.get('video_source', DEFAULT_VIDEO_SOURCE)
        
        success = processor.start_live_video(video_source)
        
        if success:
            source_type = 'DroidCam' if isinstance(video_source, str) else f'Camera {video_source}'
            return jsonify({
                'status': 'success',
                'message': f'Live video started ({source_type})',
                'video_source': str(video_source)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to start video'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/live/stop', methods=['POST'])
def stop_live_video():
    """Stop live video feed."""
    try:
        processor.stop_live_video()
        return jsonify({
            'status': 'success',
            'message': 'Live video stopped'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/live/stream')
def video_stream():
    """Stream live video feed as MJPEG."""
    print(f"[STREAM] Client connected to video stream", flush=True)
    print(f"[STREAM] Camera active: {processor.live_video_active}", flush=True)
    print(f"[STREAM] Camera object: {processor.camera}", flush=True)
    
    def generate():
        """Generate video frames in MJPEG format."""
        try:
            frame_count = 0
            failed_reads = 0
            max_failed_reads = 10
            
            while True:
                frame = processor.get_live_frame()
                if frame is None:
                    # No frame available, wait a bit and try again
                    failed_reads += 1
                    if frame_count == 0:
                        print(f"[STREAM] Waiting for first frame... (attempt {failed_reads})", flush=True)
                    
                    if failed_reads > max_failed_reads and frame_count == 0:
                        print(f"[STREAM ERROR] Failed to get first frame after {max_failed_reads} attempts", flush=True)
                        print(f"[STREAM ERROR] Camera status: active={processor.live_video_active}, obj={processor.camera is not None}", flush=True)
                        break
                    
                    time.sleep(0.033)  # ~30fps
                    continue
                
                if frame_count == 0:
                    print(f"[STREAM] First frame captured! Shape: {frame.shape}", flush=True)
                
                failed_reads = 0  # Reset failed counter on successful read
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not ret:
                    print(f"[STREAM] Failed to encode frame", flush=True)
                    continue
                
                frame_bytes = buffer.tobytes()
                frame_count += 1
                
                if frame_count % 30 == 0:
                    print(f"[STREAM] Streamed {frame_count} frames", flush=True)
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except GeneratorExit:
            print(f"[STREAM] Client disconnected (streamed {frame_count} frames)", flush=True)
        except Exception as e:
            print(f"[STREAM] Error in video stream: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ====================================================
# INSPECTION ENDPOINTS
# ====================================================

@app.route('/api/inspection/start', methods=['POST'])
def start_inspection():
    """Start inspection process (live or recorded)."""
    try:
        data = request.get_json() or {}
        inspection_type = data.get('type', 'live')  # 'live' or 'recorded'
        operator = data.get('operator', 'Unknown')
        use_motion_detection = data.get('use_motion_detection', False)  # Auto mode flag
        
        print(f"\n{'='*60}", flush=True)
        print(f"[API] /api/inspection/start called", flush=True)
        print(f"[API] Type: {inspection_type}", flush=True)
        print(f"[API] Operator: {operator}", flush=True)
        print(f"[API] Auto Mode: {use_motion_detection}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        # Create session
        session_id = str(int(time.time() * 1000))
        session_dir = SESSIONS_FOLDER / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[API] Created session: {session_id}", flush=True)
        print(f"[API] Starting thread...", flush=True)
        
        # Start inspection in background thread
        if inspection_type == 'live':
            thread = threading.Thread(
                target=processor.run_live_inspection,
                args=(session_id, session_dir, operator, use_motion_detection)
            )
        else:
            video_path = data.get('video_path')
            if not video_path:
                return jsonify({
                    'status': 'error',
                    'message': 'No video path provided'
                }), 400
            
            thread = threading.Thread(
                target=processor.run_recorded_inspection,
                args=(session_id, session_dir, video_path, operator)
            )
        
        thread.daemon = True
        thread.start()
        
        print(f"[API] Thread started successfully!", flush=True)
        
        active_sessions[session_id] = {
            'id': session_id,
            'type': inspection_type,
            'operator': operator,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'thread': thread
        }
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Inspection started'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/inspection/stop', methods=['POST'])
def stop_inspection():
    """Stop running inspection."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid session ID'
            }), 400
        
        # Stop inspection
        processor.stop_inspection(session_id)
        
        # Update session status
        active_sessions[session_id]['status'] = 'stopped'
        active_sessions[session_id]['end_time'] = datetime.now().isoformat()
        
        # Save session metadata
        session_dir = SESSIONS_FOLDER / session_id
        metadata = {
            'id': session_id,
            'type': active_sessions[session_id]['type'],
            'operator': active_sessions[session_id]['operator'],
            'start_time': active_sessions[session_id]['start_time'],
            'end_time': active_sessions[session_id]['end_time'],
            'status': 'completed',
            'results': processor.get_session_results(session_id)
        }
        
        with open(session_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Inspection stopped',
            'results': metadata['results']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/inspection/status/<session_id>', methods=['GET'])
def get_inspection_status(session_id):
    """Get current status of inspection."""
    try:
        if session_id in active_sessions:
            status = processor.get_inspection_status(session_id, SESSIONS_FOLDER)
            return jsonify({
                'status': 'success',
                'data': status
            })
        else:
            # Check if session exists in history
            session_dir = SESSIONS_FOLDER / session_id
            metadata_file = session_dir / 'metadata.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                return jsonify({
                    'status': 'success',
                    'data': metadata
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Session not found'
                }), 404
                
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/motion/settings', methods=['GET', 'POST'])
def motion_settings():
    """Get or update motion detection settings."""
    try:
        if request.method == 'GET':
            # Return current settings
            return jsonify({
                'status': 'success',
                'settings': {
                    'method': processor.motion_detection_method,
                    'threshold': processor.motion_threshold,
                    'frames_to_confirm': processor.motion_frames_to_confirm,
                    'no_motion_frames_to_stop': processor.no_motion_frames_to_stop,
                    'available_methods': ['mog2', 'knn', 'frame_diff', 'combined']
                }
            })
        
        elif request.method == 'POST':
            # Update settings
            data = request.get_json() or {}
            
            if 'method' in data:
                if data['method'] in ['mog2', 'knn', 'frame_diff', 'combined']:
                    processor.motion_detection_method = data['method']
                    print(f"[CONFIG] Motion detection method changed to: {data['method'].upper()}")
            
            if 'threshold' in data:
                processor.motion_threshold = float(data['threshold'])
                print(f"[CONFIG] Motion threshold changed to: {data['threshold']}%")
            
            if 'frames_to_confirm' in data:
                processor.motion_frames_to_confirm = int(data['frames_to_confirm'])
                print(f"[CONFIG] Frames to confirm changed to: {data['frames_to_confirm']}")
            
            if 'no_motion_frames_to_stop' in data:
                processor.no_motion_frames_to_stop = int(data['no_motion_frames_to_stop'])
                print(f"[CONFIG] No-motion frames to stop changed to: {data['no_motion_frames_to_stop']}")
            
            return jsonify({
                'status': 'success',
                'message': 'Settings updated',
                'settings': {
                    'method': processor.motion_detection_method,
                    'threshold': processor.motion_threshold,
                    'frames_to_confirm': processor.motion_frames_to_confirm,
                    'no_motion_frames_to_stop': processor.no_motion_frames_to_stop
                }
            })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ====================================================
# IMAGE PROCESSING ENDPOINT
# ====================================================

@app.route('/api/image/process', methods=['POST'])
def process_image():
    """Process single image for deblurring."""
    try:
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Save uploaded file
        timestamp = int(time.time() * 1000)
        filename = f"image_{timestamp}_{file.filename}"
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))
        
        # Process image
        result = processor.process_single_image(str(filepath))
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """Upload video file for processing."""
    try:
        if 'video' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No video file provided'
            }), 400
        
        file = request.files['video']
        
        # Save uploaded file
        timestamp = int(time.time() * 1000)
        filename = f"video_{timestamp}_{file.filename}"
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))
        
        return jsonify({
            'status': 'success',
            'path': str(filepath),
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ====================================================
# SESSION MANAGEMENT
# ====================================================

@app.route('/api/session/<session_id>/archive', methods=['POST'])
def archive_session(session_id):
    """Archive a session and prepare for new inspection."""
    try:
        session_dir = SESSIONS_FOLDER / session_id
        
        if not session_dir.exists():
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
        
        # Session is already in sessions folder which serves as records
        # Just mark it as archived in metadata
        metadata_file = session_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata['archived'] = True
            metadata['archived_at'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Session archived successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all inspection sessions."""
    try:
        sessions = []
        
        # Get all session directories
        for session_dir in SESSIONS_FOLDER.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        sessions.append(metadata)
        
        # Sort by start time (newest first)
        sessions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        return jsonify({
            'status': 'success',
            'sessions': sessions
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>', methods=['GET', 'DELETE'])
def handle_session(session_id):
    """Get or delete session."""
    if request.method == 'DELETE':
        return delete_session(session_id)
    else:
        return get_session_detail(session_id)

def get_session_detail(session_id):
    """Get detailed information for a specific session."""
    try:
        session_dir = SESSIONS_FOLDER / session_id
        metadata_file = session_dir / 'metadata.json'
        
        if not metadata_file.exists():
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Try to get inspection status from active session first
        status_data = processor.get_inspection_status(session_id, SESSIONS_FOLDER)
        
        if status_data:
            # Active session - use live data
            metadata['wagon_numbers'] = status_data.get('wagon_numbers', [])
            metadata['damage_detections'] = status_data.get('damage_detections', [])
            metadata['deblurred_thumbnails'] = status_data.get('deblurred_thumbnails', [])
            metadata['original_thumbnails'] = status_data.get('original_thumbnails', [])
            metadata['deblurred_frames'] = status_data.get('deblurred_frames', [])
        else:
            # Completed session - load from disk and generate base64
            import cv2
            import base64
            
            # Generate wagon detection base64 images
            wagon_numbers = []
            wagon_dir = session_dir / 'wagon_detections'
            if wagon_dir.exists():
                wagon_files = sorted(wagon_dir.glob('wagon_*.jpg'))
                for wagon_file in wagon_files:
                    # Extract wagon number and frame from filename: wagon_NR-12345_123.jpg
                    parts = wagon_file.stem.split('_')
                    if len(parts) >= 3:
                        wagon_num = parts[1]
                        frame_num = int(parts[2])
                        
                        # Load and encode to base64
                        img = cv2.imread(str(wagon_file))
                        if img is not None:
                            # Resize to thumbnail
                            h, w = img.shape[:2]
                            new_w = 320
                            new_h = int(h * (new_w / w))
                            thumbnail = cv2.resize(img, (new_w, new_h))
                            
                            success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            if success:
                                wagon_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                                wagon_numbers.append({
                                    'number': wagon_num,
                                    'frame': frame_num,
                                    'wagon_base64': wagon_base64
                                })
            
            # Generate damage detection base64 images
            damage_detections = []
            wagon_dir = session_dir / 'wagon_detections'
            print(f"[DAMAGE LOAD] Checking for damage files in completed session {session_id}")
            print(f"[DAMAGE LOAD] Wagon dir path: {wagon_dir}")
            print(f"[DAMAGE LOAD] Wagon dir exists: {wagon_dir.exists()}")
            if wagon_dir.exists():
                damage_files = sorted(wagon_dir.glob('damage_*.jpg'))
                print(f"[DAMAGE LOAD] Found {len(damage_files)} damage files: {[f.name for f in damage_files]}")
                for damage_file in damage_files:
                    # Extract frame number: damage_123.jpg
                    try:
                        frame_num = int(damage_file.stem.split('_')[1])
                        
                        # Load and encode to base64
                        img = cv2.imread(str(damage_file))
                        if img is not None:
                            # Resize to thumbnail
                            h, w = img.shape[:2]
                            new_w = 320
                            new_h = int(h * (new_w / w))
                            thumbnail = cv2.resize(img, (new_w, new_h))
                            
                            success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            if success:
                                damage_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                                damage_detections.append({
                                    'frame': frame_num,
                                    'damage_type': 'detected',
                                    'confidence': 0.85,
                                    'damage_base64': damage_base64
                                })
                                print(f"[DAMAGE LOAD] Successfully encoded damage image for frame {frame_num}")
                    except Exception as e:
                        print(f"[DAMAGE LOAD] Error processing damage file {damage_file}: {e}")
            
            print(f"[DAMAGE LOAD] Total damage detections loaded: {len(damage_detections)}")
            metadata['damage_detections'] = damage_detections
            
            # Generate deblurred frame thumbnails
            deblurred_thumbnails = []
            original_thumbnails = []
            deblurred_dir = session_dir / 'deblurred'
            frames_dir = session_dir / 'frames'
            
            if deblurred_dir.exists():
                deblurred_files = sorted(deblurred_dir.glob('*.jpg'))  # Get all frames
                for img_file in deblurred_files:
                    # Load deblurred
                    img = cv2.imread(str(img_file))
                    if img is not None:
                        h, w = img.shape[:2]
                        new_w = 320
                        new_h = int(h * (new_w / w))
                        thumbnail = cv2.resize(img, (new_w, new_h))
                        
                        success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if success:
                            deblurred_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                            deblurred_thumbnails.append(deblurred_b64)
                        
                        # Load corresponding original
                        frame_name = img_file.name.replace('deblurred_', 'frame_')
                        original_path = frames_dir / frame_name
                        if original_path.exists():
                            orig_img = cv2.imread(str(original_path))
                            if orig_img is not None:
                                orig_thumbnail = cv2.resize(orig_img, (new_w, new_h))
                                success, orig_buffer = cv2.imencode('.jpg', orig_thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                if success:
                                    orig_b64 = f"data:image/jpeg;base64,{base64.b64encode(orig_buffer).decode('utf-8')}"
                                    original_thumbnails.append(orig_b64)
            
            metadata['wagon_numbers'] = wagon_numbers
            metadata['damage_detections'] = damage_detections
            metadata['deblurred_thumbnails'] = deblurred_thumbnails
            metadata['original_thumbnails'] = original_thumbnails
        
        return jsonify({
            'status': 'success',
            'data': metadata
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def delete_session(session_id):
    """Soft delete a session by moving it to deleted folder."""
    try:
        import shutil
        
        session_dir = SESSIONS_FOLDER / session_id
        
        if not session_dir.exists():
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
        
        # Read metadata to add deletion timestamp
        metadata_file = session_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Add deletion info
            metadata['deleted_at'] = datetime.now().isoformat()
            
            # Write back
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        # Move to deleted folder
        deleted_dir = DELETED_SESSIONS_FOLDER / session_id
        shutil.move(str(session_dir), str(deleted_dir))
        
        print(f"Soft deleted session: {session_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Session {session_id} moved to recently deleted'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/deleted-sessions', methods=['GET'])
def get_deleted_sessions():
    """Get all recently deleted sessions (within 7 days)."""
    try:
        from datetime import timedelta
        deleted_sessions = []
        current_time = datetime.now()
        
        # Get all deleted session directories
        for session_dir in DELETED_SESSIONS_FOLDER.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        
                        # Check if deleted within last 7 days
                        deleted_at = metadata.get('deleted_at')
                        if deleted_at:
                            deleted_date = datetime.fromisoformat(deleted_at)
                            days_since_deletion = (current_time - deleted_date).days
                            
                            if days_since_deletion <= 7:
                                metadata['days_until_permanent_delete'] = 7 - days_since_deletion
                                deleted_sessions.append(metadata)
        
        # Sort by deletion time (newest first)
        deleted_sessions.sort(key=lambda x: x.get('deleted_at', ''), reverse=True)
        
        return jsonify({
            'status': 'success',
            'sessions': deleted_sessions
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/restore', methods=['POST'])
def restore_session(session_id):
    """Restore a deleted session."""
    try:
        import shutil
        
        deleted_dir = DELETED_SESSIONS_FOLDER / session_id
        
        if not deleted_dir.exists():
            return jsonify({
                'status': 'error',
                'message': 'Deleted session not found'
            }), 404
        
        # Move back to sessions folder
        restored_dir = SESSIONS_FOLDER / session_id
        shutil.move(str(deleted_dir), str(restored_dir))
        
        # Remove deletion timestamp from metadata
        metadata_file = restored_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Remove deletion info
            if 'deleted_at' in metadata:
                del metadata['deleted_at']
            
            # Write back
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        print(f"Restored session: {session_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Session {session_id} restored successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_session(session_id):
    """Permanently delete a session from recently deleted."""
    try:
        import shutil
        
        deleted_dir = DELETED_SESSIONS_FOLDER / session_id
        
        if not deleted_dir.exists():
            return jsonify({
                'status': 'error',
                'message': 'Deleted session not found'
            }), 404
        
        # Permanently remove the entire session directory
        shutil.rmtree(deleted_dir)
        
        print(f"Permanently deleted session: {session_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Session {session_id} permanently deleted'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/cleanup-old-deletions', methods=['POST'])
def cleanup_old_deletions():
    """Automatically clean up sessions deleted more than 7 days ago."""
    try:
        from datetime import timedelta
        import shutil
        
        current_time = datetime.now()
        deleted_count = 0
        
        for session_dir in DELETED_SESSIONS_FOLDER.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        
                        deleted_at = metadata.get('deleted_at')
                        if deleted_at:
                            deleted_date = datetime.fromisoformat(deleted_at)
                            days_since_deletion = (current_time - deleted_date).days
                            
                            if days_since_deletion > 7:
                                shutil.rmtree(session_dir)
                                deleted_count += 1
                                print(f"Auto-deleted old session: {session_dir.name}")
        
        return jsonify({
            'status': 'success',
            'message': f'Cleaned up {deleted_count} old deleted sessions'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/image/<filename>', methods=['GET'])
def get_session_image(session_id, filename):
    """Get specific image from session."""
    try:
        # Try different folders
        folders = ['wagon_detections', 'deblurred', 'frames']
        
        for folder in folders:
            session_dir = SESSIONS_FOLDER / session_id / folder
            filepath = session_dir / filename
            if filepath.exists():
                response = send_from_directory(session_dir, filename)
                # Add CORS headers
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Cache-Control'] = 'no-cache'
                return response
        
        # If not found, log the attempted paths for debugging
        print(f"[404] Image not found: {session_id}/{filename}")
        print(f"     Checked folders: {folders}")
        print(f"     Session dir exists: {(SESSIONS_FOLDER / session_id).exists()}")
        
        # If not found, return 404
        return jsonify({
            'status': 'error',
            'message': 'Image not found'
        }), 404
        
    except Exception as e:
        print(f"[ERROR] get_session_image: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404


@app.route('/uploads/<filename>', methods=['GET'])
def get_upload_file(filename):
    """Get uploaded file."""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404


# ====================================================
# ANALYTICS ENDPOINT
# ====================================================

@app.route('/api/sessions/list', methods=['GET'])
def get_sessions_list():
    """Get list of all recorded inspection sessions."""
    try:
        sessions = []
        
        for session_dir in SESSIONS_FOLDER.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        
                        # Get timestamp - use start_time if timestamp not available
                        timestamp = metadata.get('timestamp') or metadata.get('start_time', '')
                        
                        sessions.append({
                            'id': session_dir.name,
                            'timestamp': timestamp,
                            'type': metadata.get('type', 'unknown'),
                            'video_source': metadata.get('video_source', ''),
                            'wagons_detected': metadata.get('results', {}).get('wagons_detected', 0),
                            'readable': metadata.get('results', {}).get('readable', 0),
                            'unreadable': metadata.get('results', {}).get('unreadable', 0),
                            'duration': metadata.get('results', {}).get('duration', 0),
                            'status': metadata.get('status', 'unknown')
                        })
        
        # Sort by timestamp (newest first)
        sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        print(f"[ERROR] get_sessions_list: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/top-frames', methods=['GET'])
def get_top_frames(session_id):
    """Get top 10 frames from a session sorted by deblur quality."""
    try:
        print(f"[INFO] Getting top frames for session: {session_id}")
        session_dir = SESSIONS_FOLDER / session_id
        
        if not session_dir.exists():
            print(f"[ERROR] Session directory not found: {session_dir}")
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
        
        # Load metadata
        metadata_file = session_dir / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'status': 'error',
                'message': 'Session metadata not found'
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Get deblurred frames directory
        deblurred_dir = session_dir / 'deblurred'
        if not deblurred_dir.exists():
            return jsonify({
                'status': 'error',
                'message': 'No deblurred frames found'
            }), 404
        
        # Get all deblurred frames and calculate quality metrics
        frames_data = []
        
        print(f"[DEBUG] Starting to process frames from {deblurred_dir}")
        deblurred_files = sorted(deblurred_dir.glob('deblurred_*.jpg'))
        print(f"[DEBUG] Found {len(deblurred_files)} deblurred frames to process")
        
        for frame_file in deblurred_files:
            # Extract frame number
            import re
            match = re.match(r'deblurred_(\d+)', frame_file.stem)
            if match:
                frame_num = int(match.group(1))
                
                # Read image and calculate sharpness/quality
                try:
                    import cv2
                    import numpy as np
                    
                    img = cv2.imread(str(frame_file))
                    if img is not None:
                        # Calculate Laplacian variance (sharpness metric)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                        
                        # Calculate edge strength
                        edges = cv2.Canny(gray, 100, 200)
                        edge_density = np.sum(edges > 0) / edges.size
                        
                        # Combined quality score (normalized to 0-100 scale, more realistic)
                        # Typical laplacian values: blurry=10-50, sharp=100-500+
                        # Edge density: 0.01-0.10
                        laplacian_score = min(100, (laplacian_var / 500) * 100)
                        edge_score = min(100, edge_density * 1000)
                        quality_score = (laplacian_score * 0.7) + (edge_score * 0.3)
                        
                        # Get corresponding original frame for before/after comparison
                        original_frame = session_dir / 'frames' / f'frame_{frame_num:06d}.jpg'
                        original_quality = 0
                        
                        if original_frame.exists():
                            orig_img = cv2.imread(str(original_frame))
                            if orig_img is not None:
                                orig_gray = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
                                orig_lap_var = cv2.Laplacian(orig_gray, cv2.CV_64F).var()
                                orig_edges = cv2.Canny(orig_gray, 100, 200)
                                orig_edge_density = np.sum(orig_edges > 0) / orig_edges.size
                                orig_lap_score = min(100, (orig_lap_var / 500) * 100)
                                orig_edge_score = min(100, orig_edge_density * 1000)
                                original_quality = (orig_lap_score * 0.7) + (orig_edge_score * 0.3)
                        
                        # Calculate improvement percentage
                        improvement = quality_score - original_quality
                        improvement_pct = (improvement / (original_quality + 0.1)) * 100
                        
                        # Try to get wagon number from wagon_detections folder
                        wagon_number = None
                        wagon_det_dir = session_dir / 'wagon_detections'
                        if wagon_det_dir.exists():
                            # Get ALL wagon files and look for EXACT match or very close match (±2 frames for timing)
                            all_wagon_files = list(wagon_det_dir.glob('wagon_*.jpg'))
                            
                            for wagon_file in all_wagon_files:
                                try:
                                    # Parse filename: wagon_07-242_10.jpg
                                    parts = wagon_file.stem.split('_')
                                    if len(parts) >= 3:
                                        # parts[0] = 'wagon', parts[1] = wagon_number, parts[2] = frame_num
                                        file_wagon_num = parts[1]
                                        file_frame_num = int(parts[2])
                                        
                                        # Only match if EXACT frame number (no fuzzy matching)
                                        if file_frame_num == frame_num:
                                            wagon_number = file_wagon_num
                                            print(f"[DEBUG] ✓ Found wagon {wagon_number} for frame {frame_num}")
                                            break
                                except Exception as e:
                                    print(f"[DEBUG] Error parsing wagon file {wagon_file.name}: {e}")
                                    continue
                            
                            if not wagon_number:
                                print(f"[DEBUG] ✗ No wagon detected in frame {frame_num}")
                        
                        # Try from metadata wagon_numbers array (new format)
                        if not wagon_number:
                            wagon_numbers = metadata.get('wagon_numbers', [])
                            if wagon_numbers:
                                for wn in wagon_numbers:
                                    # Check if it's an object with frame number
                                    wn_frame_num = wn.get('frame')
                                    if isinstance(wn_frame_num, int) and wn_frame_num == frame_num:
                                        wagon_number = wn.get('number', wn.get('wagon_number', wn.get('text', None)))
                                        if wagon_number:
                                            print(f"[DEBUG] ✓ Found wagon {wagon_number} for frame {frame_num} from metadata")
                                            break
                        
                        if not wagon_number:
                            print(f"[DEBUG] ✗ No wagon number found for frame {frame_num}")
                        
                        frames_data.append({
                            'frame_number': frame_num,
                            'frame_id': f'frame_{frame_num:06d}',
                            'quality_score': round(quality_score, 2),
                            'original_quality': round(original_quality, 2),
                            'improvement': round(improvement, 2),
                            'improvement_pct': round(improvement_pct, 2),
                            'wagon_number': wagon_number if wagon_number else 'N/A',
                            'deblurred_path': f'sessions/{session_id}/deblurred/deblurred_{frame_num:06d}.jpg',
                            'original_path': f'sessions/{session_id}/frames/frame_{frame_num:06d}.jpg'
                        })
                        
                except Exception as e:
                    print(f"[ERROR] Processing frame {frame_file}: {e}")
                    continue
        
        # Sort by DEBLURRED quality score (highest quality frames first), not improvement
        print(f"[DEBUG] Before sorting: Total frames = {len(frames_data)}")
        if frames_data:
            print(f"[DEBUG] Quality scores range: {min(f['quality_score'] for f in frames_data):.2f} to {max(f['quality_score'] for f in frames_data):.2f}")
            print(f"[DEBUG] Sample frames before sort:")
            for i, f in enumerate(frames_data[:5], 1):
                print(f"  Frame {f['frame_number']}: quality={f['quality_score']:.2f}")
        
        frames_data.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"[DEBUG] After sorting by quality_score (highest first):")
        for i, f in enumerate(frames_data[:10], 1):
            print(f"  #{i}: Frame {f['frame_number']} - Quality: {f['quality_score']:.2f}")
        
        top_10 = frames_data[:10]
        
        print(f"[INFO] Processed {len(frames_data)} frames, returning top {len(top_10)}")
        if top_10:
            print(f"[INFO] Top 10 frames by quality:")
            for i, frame in enumerate(top_10, 1):
                print(f"  #{i}: Frame {frame.get('frame_number')} - Quality: {frame.get('quality_score'):.2f}, Improvement: {frame.get('improvement_pct'):.1f}%, Wagon: {frame.get('wagon_number', 'N/A')}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'session_info': {
                'timestamp': metadata.get('timestamp') or metadata.get('start_time', ''),
                'type': metadata.get('type', ''),
                'wagons_detected': metadata.get('results', {}).get('wagons_detected', 0)
            },
            'top_frames': top_10,
            'total_frames': len(frames_data)
        })
        
    except Exception as e:
        print(f"[ERROR] get_top_frames: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get aggregated analytics from all sessions."""
    try:
        total_wagons = 0
        total_readable = 0
        total_unreadable = 0
        total_duration = 0
        session_count = 0
        top_frames = []
        
        # Aggregate data from all sessions
        for session_dir in SESSIONS_FOLDER.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        results = metadata.get('results', {})
                        
                        total_wagons += results.get('wagons_detected', 0)
                        total_readable += results.get('readable', 0)
                        total_unreadable += results.get('unreadable', 0)
                        total_duration += results.get('duration', 0)
                        session_count += 1
        
        avg_confidence = (total_readable / total_wagons * 100) if total_wagons > 0 else 0
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'total_wagons': total_wagons,
                'readable': total_readable,
                'unreadable': total_unreadable,
                'avg_confidence': round(avg_confidence, 2),
                'total_duration': total_duration,
                'session_count': session_count,
                'top_frames': top_frames
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ====================================================
# HEALTH CHECK
# ====================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'rAIlwagon API is running',
        'timestamp': datetime.now().isoformat()
    })


# ====================================================
# ERROR HANDLERS
# ====================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


# ====================================================
# AI INCIDENT RESPONSE ENDPOINTS
# ====================================================

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    """Get all incidents with optional filtering."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        severity = request.args.get('severity')
        status = request.args.get('status')
        incident_type = request.args.get('type')
        
        incidents = incident_ai.incidents
        
        # Apply filters
        if severity:
            incidents = [inc for inc in incidents if inc.severity == severity]
        if status:
            incidents = [inc for inc in incidents if inc.status == status]
        if incident_type:
            incidents = [inc for inc in incidents if inc.type == incident_type]
        
        # Sort by detected_at (most recent first)
        from dataclasses import asdict
        incidents = sorted(incidents, key=lambda x: x.detected_at, reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(incidents),
            'incidents': [asdict(inc) for inc in incidents]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incident/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Get specific incident details."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        incident = incident_ai.get_incident_by_id(incident_id)
        if not incident:
            return jsonify({'success': False, 'error': 'Incident not found'}), 404
        
        from dataclasses import asdict
        return jsonify({
            'success': True,
            'incident': asdict(incident)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incident/<incident_id>/similar', methods=['GET'])
def get_similar_incidents(incident_id):
    """Get similar past incidents for learning."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        incident = incident_ai.get_incident_by_id(incident_id)
        if not incident:
            return jsonify({'success': False, 'error': 'Incident not found'}), 404
        
        similar = incident_ai.find_similar_incidents(incident, top_k=5)
        
        return jsonify({
            'success': True,
            'incident_id': incident_id,
            'similar_incidents': similar
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incident/<incident_id>/recommendations', methods=['GET'])
def get_incident_recommendations(incident_id):
    """Get AI-powered action recommendations."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        incident = incident_ai.get_incident_by_id(incident_id)
        if not incident:
            return jsonify({'success': False, 'error': 'Incident not found'}), 404
        
        recommendations = incident_ai.recommend_actions(incident)
        similar = incident_ai.find_similar_incidents(incident, top_k=3)
        
        return jsonify({
            'success': True,
            'incident_id': incident_id,
            'recommended_actions': recommendations,
            'based_on_similar_incidents': len(similar),
            'similar_incidents': similar
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incident', methods=['POST'])
def create_incident():
    """Create new incident (manual or automated)."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        data = request.json
        
        incident = Incident(
            id="",
            type=data['type'],
            severity=data['severity'],
            status='detected',
            title=data['title'],
            description=data['description'],
            detected_at=datetime.now().isoformat(),
            session_id=data.get('session_id', ''),
            wagon_number=data.get('wagon_number'),
            frame_number=data.get('frame_number'),
            damage_type=data.get('damage_type'),
            confidence=data.get('confidence', 0.0)
        )
        
        incident_id = incident_ai.add_incident(incident)
        
        # Get AI recommendations
        recommendations = incident_ai.recommend_actions(incident)
        incident_ai.update_incident(incident_id, {
            'recommended_actions': recommendations,
            'recommended_by_ai': True
        })
        
        return jsonify({
            'success': True,
            'incident_id': incident_id,
            'recommended_actions': recommendations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incident/<incident_id>', methods=['PUT'])
def update_incident(incident_id):
    """Update incident (acknowledge, resolve, add notes)."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        data = request.json
        
        updates = {}
        if 'status' in data:
            updates['status'] = data['status']
            
            # Set timestamps
            if updates['status'] == 'acknowledged' and 'acknowledged_at' not in data:
                updates['acknowledged_at'] = datetime.now().isoformat()
            elif updates['status'] == 'resolved' and 'resolved_at' not in data:
                updates['resolved_at'] = datetime.now().isoformat()
        
        if 'assigned_to' in data:
            updates['assigned_to'] = data['assigned_to']
        if 'root_cause' in data:
            updates['root_cause'] = data['root_cause']
        if 'resolution_steps' in data:
            updates['resolution_steps'] = data['resolution_steps']
        if 'notes' in data:
            incident = incident_ai.get_incident_by_id(incident_id)
            if incident:
                notes = incident.notes or []
                notes.append(data['notes'])
                updates['notes'] = notes
        
        success = incident_ai.update_incident(incident_id, updates)
        
        if success:
            return jsonify({'success': True, 'incident_id': incident_id})
        else:
            return jsonify({'success': False, 'error': 'Incident not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/incidents/stats', methods=['GET'])
def get_incident_stats():
    """Get incident statistics and response time metrics."""
    if not INCIDENT_AI_ENABLED or incident_ai is None:
        return jsonify({'success': False, 'error': 'AI Incident Agent not available'}), 503
    
    try:
        incidents = incident_ai.incidents
        
        # Count by status
        status_counts = {
            'detected': 0,
            'acknowledged': 0,
            'in_progress': 0,
            'resolved': 0,
            'escalated': 0
        }
        for inc in incidents:
            if inc.status in status_counts:
                status_counts[inc.status] += 1
        
        # Count by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        for inc in incidents:
            if inc.severity in severity_counts:
                severity_counts[inc.severity] += 1
        
        # Response time stats
        response_time_stats = incident_ai.get_response_time_stats()
        
        # Recent incidents (last 10)
        from dataclasses import asdict
        recent = sorted(incidents, key=lambda x: x.detected_at, reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'total_incidents': len(incidents),
            'status_breakdown': status_counts,
            'severity_breakdown': severity_counts,
            'response_time_stats': response_time_stats,
            'recent_incidents': [asdict(inc) for inc in recent]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ====================================================
# MAIN
# ====================================================

if __name__ == '__main__':
    print("=" * 60)
    print("rAIlwagon Inspection System - Backend API")
    print("=" * 60)
    print(f"Starting server...")
    print(f"Upload folder: {UPLOAD_FOLDER.absolute()}")
    print(f"Sessions folder: {SESSIONS_FOLDER.absolute()}")
    print(f"\nAPI will be available at: http://localhost:5000")
    print(f"Frontend will be available at: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

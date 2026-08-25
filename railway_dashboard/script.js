// ====================================================
// rAIlwagon Inspection System - Main Application Logic
// ====================================================

// ====================================================
// STATE MANAGEMENT
// ====================================================

const AppState = {
    currentUser: null,
    currentPage: null,
    currentSessionId: null,  // Track current inspection session
    inspectionSessions: [],
    deletedSessions: [],  // Track deleted sessions
    currentRecordsTab: 'active',  // Track which tab is active
    analysisEnabled: false,
    liveVideoActive: false,
    liveInspectionActive: false,
    recordedInspectionActive: false,
    
    // Motion Detection State
    motionDetection: {
        autoMode: true,  // Changed to ON by default - only process when train detected
        currentState: 'IDLE',  // IDLE, MOTION_DETECTED, TRAIN_CONFIRMED, INSPECTION_RUNNING
        motionFrameCount: 0,
        noMotionFrameCount: 0,
        totalFramesAnalyzed: 0,
        currentMotionLevel: 0,
        detectionTimer: null,
        
        // Simulation control
        simulatingTrain: false,
        trainSimulationFrame: 0,
        
        // Thresholds
        MOTION_CONFIRM_FRAMES: 10,  // Frames with motion to confirm train
        NO_MOTION_STOP_FRAMES: 60,  // Frames without motion to auto-stop (2 seconds at 30fps)
        MOTION_THRESHOLD: 15  // Percentage of change to consider motion
    }
};

// ====================================================
// INITIALIZATION
// ====================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Check for saved login session
    const savedUser = localStorage.getItem('railwayInspectionUser');
    if (savedUser) {
        try {
            AppState.currentUser = JSON.parse(savedUser);
            // Auto-login with saved credentials
            document.getElementById('loginScreen').classList.remove('active');
            document.getElementById('mainDashboard').classList.add('active');
            document.getElementById('loggedOperator').textContent = AppState.currentUser.name;
        } catch (e) {
            console.error('Error loading saved user:', e);
            localStorage.removeItem('railwayInspectionUser');
        }
    }
    
    // Login form handler
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', handleLogin);

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    logoutBtn.addEventListener('click', handleLogout);

    // Selection screen cards
    const selectionCards = document.querySelectorAll('.selection-card');
    selectionCards.forEach(card => {
        card.addEventListener('click', handleSelectionCard);
    });

    // Sidebar navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // Live Video Page Controls
    initializeLiveVideoPage();

    // Recorded Video Page Controls
    initializeRecordedVideoPage();

    // Image Inspection Page Controls
    initializeImageInspectionPage();

    // Records Page
    initializeRecordsPage();

    // Initially disable analysis
    updateAnalysisState();
    
    // Load existing sessions from backend on startup
    loadSessionsFromBackend();
}

// ====================================================
// LOGIN / LOGOUT HANDLERS
// ====================================================

function handleLogin(e) {
    e.preventDefault();
    
    const name = document.getElementById('operatorName').value;
    const email = document.getElementById('operatorEmail').value;
    
    AppState.currentUser = { name, email };
    
    // Save to localStorage for persistence across page refreshes
    localStorage.setItem('railwayInspectionUser', JSON.stringify(AppState.currentUser));
    
    // Show dashboard, hide login
    document.getElementById('loginScreen').classList.remove('active');
    document.getElementById('mainDashboard').classList.add('active');
    
    // Update header with operator info
    document.getElementById('loggedOperator').textContent = name;
}

function handleLogout() {
    AppState.currentUser = null;
    AppState.currentPage = null;
    
    // Clear saved login session
    localStorage.removeItem('railwayInspectionUser');
    
    // Reset to login screen
    document.getElementById('mainDashboard').classList.remove('active');
    document.getElementById('loginScreen').classList.add('active');
    
    // Hide sidebar and show selection screen
    document.getElementById('sidebar').classList.remove('active');
    const selectionScreen = document.getElementById('selectionScreen');
    selectionScreen.classList.remove('hidden');
    
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active state from nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Clear form
    document.getElementById('loginForm').reset();
}

// ====================================================
// NAVIGATION HANDLERS
// ====================================================

function handleSelectionCard(e) {
    const card = e.currentTarget;
    const page = card.dataset.page;
    
    // Check if analysis is disabled
    if (page === 'analysis' && !AppState.analysisEnabled) {
        return;
    }
    
    // Animate selection screen out
    const selectionScreen = document.getElementById('selectionScreen');
    selectionScreen.classList.add('hidden');
    
    // Show sidebar with delay for smooth transition
    setTimeout(() => {
        document.getElementById('sidebar').classList.add('active');
    }, 300);
    
    // Navigate to page
    setTimeout(() => {
        navigateToPage(page);
    }, 400);
}

function handleNavigation(e) {
    const item = e.currentTarget;
    const page = item.dataset.page;
    
    // Check if item is disabled
    if (item.classList.contains('disabled')) {
        return;
    }
    
    navigateToPage(page);
}

function navigateToPage(page) {
    AppState.currentPage = page;
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.dataset.page === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Show correct page content
    document.querySelectorAll('.page-content').forEach(pageContent => {
        pageContent.classList.remove('active');
    });
    
    const pageElement = document.getElementById(page + 'Page');
    if (pageElement) {
        pageElement.classList.add('active');
    }
    
    // Load page-specific data
    if (page === 'analysis') {
        loadAnalysisSessions();
    } else if (page === 'records') {
        loadAllSessions();
    } else if (page === 'incidents') {
        onIncidentsPageShown();
    }
}

// ====================================================
// LIVE VIDEO INSPECTION PAGE
// ====================================================

function initializeLiveVideoPage() {
    const startLiveBtn = document.getElementById('startLiveBtn');
    const startInspectionBtn = document.getElementById('startLiveInspectionBtn');
    const stopInspectionBtn = document.getElementById('stopLiveInspectionBtn');
    const restartLiveBtn = document.getElementById('restartLiveBtn');
    
    startLiveBtn.addEventListener('click', handleStartLiveVideo);
    startInspectionBtn.addEventListener('click', handleStartLiveInspection);
    stopInspectionBtn.addEventListener('click', handleStopLiveInspection);
    restartLiveBtn.addEventListener('click', handleRestartLiveVideo);
    
    // Motion Detection Controls
    initializeMotionDetection();
}

function handleStartLiveVideo() {
    AppState.liveVideoActive = true;
    
    console.log('[VIDEO] Starting live video...');
    
    // Call backend to start live video
    apiStartLiveVideo().then(response => {
        console.log('[VIDEO] Backend response:', response);
        
        if (response.status === 'success') {
            console.log('[VIDEO] Backend started successfully, waiting for camera initialization...');
            
            // Wait a moment for camera to fully initialize before starting stream
            setTimeout(() => {
                // Use IMG tag for MJPEG stream (more reliable than video tag)
                const imgElement = document.getElementById('liveVideoFeed');
                const streamUrl = '/api/live/stream?t=' + Date.now();
                
                console.log('[VIDEO] Setting image source to:', streamUrl);
                
                imgElement.onload = function() {
                    console.log('[VIDEO] Stream loaded successfully!');
                    imgElement.style.display = 'block';
                    document.getElementById('liveVideoOverlay').classList.add('hidden');
                };
                
                imgElement.onerror = function(e) {
                    console.error('[VIDEO] Stream error:', e);
                    console.error('[VIDEO] Failed to load stream from:', streamUrl);
                    document.getElementById('liveVideoOverlay').classList.remove('hidden');
                    document.getElementById('liveStatusText').textContent = 'VIDEO STREAM ERROR';
                    
                    // Try to get more error details
                    fetch(streamUrl, { method: 'HEAD' })
                        .then(response => {
                            console.error('[VIDEO] Stream endpoint status:', response.status);
                            console.error('[VIDEO] Stream endpoint headers:', response.headers);
                        })
                        .catch(err => {
                            console.error('[VIDEO] Cannot reach stream endpoint:', err);
                        });
                    
                    alert('Video stream failed to load. Check console for details.');
                };
                
                imgElement.src = streamUrl;
            }, 500); // Wait 500ms for camera to initialize
            
            // Update UI immediately
            document.getElementById('liveStatus').classList.add('active');
            document.getElementById('liveStatusText').textContent = 'LIVE FEED ACTIVE';
            
            // Enable inspection button
            document.getElementById('startLiveInspectionBtn').disabled = false;
            if (AppState.motionDetection.autoMode) {
                document.getElementById('startLiveInspectionBtn').title = 'Start inspection with automatic train detection';
            } else {
                document.getElementById('startLiveInspectionBtn').title = 'Start inspection and capture all frames';
            }
            
            // Disable start live button
            document.getElementById('startLiveBtn').disabled = true;
            
            console.log('[VIDEO] Video element setup complete');
        } else {
            console.error('[VIDEO] Backend failed to start:', response.message);
            alert('Failed to start live video: ' + response.message);
            AppState.liveVideoActive = false;
        }
    }).catch(error => {
        console.error('[VIDEO] Error starting live video:', error);
        alert('Error starting live video. Is the backend running?');
        AppState.liveVideoActive = false;
    });
}

function handleStartLiveInspection() {
    // Note: AUTO mode flag will be sent to backend, which handles motion detection
    // Frontend no longer blocks inspection start when auto mode is on
    
    // Call backend to start inspection
    apiStartInspection('live').then(response => {
        if (response.status === 'success') {
            AppState.liveInspectionActive = true;
            AppState.currentSessionId = response.session_id;
            
            // Update UI
            document.getElementById('liveStatusText').textContent = 'INSPECTION RUNNING';
            
            // Enable stop button, disable start
            document.getElementById('startLiveInspectionBtn').disabled = true;
            document.getElementById('stopLiveInspectionBtn').disabled = false;
            
            // Start polling for status updates
            startLiveInspectionPolling();
            
            console.log('Live inspection started:', response.session_id);
        } else {
            alert('Failed to start inspection: ' + response.message);
        }
    }).catch(error => {
        console.error('Error starting inspection:', error);
        alert('Error starting inspection. Is the backend running?');
    });
}

function handleStopLiveInspection() {
    // Call backend to stop inspection
    apiStopInspection(AppState.currentSessionId).then(response => {
        if (response.status === 'success') {
            AppState.liveInspectionActive = false;
            
            // Update UI
            document.getElementById('liveStatusText').textContent = 'INSPECTION STOPPED';
            
            // If auto mode is still on, log completion and reset
            if (AppState.motionDetection.autoMode) {
                logMotionEvent('Inspection completed - monitoring resumed', 'idle');
                updateMotionState('IDLE');
                AppState.motionDetection.motionFrameCount = 0;
                AppState.motionDetection.noMotionFrameCount = 0;
            }
            
            // Hide inspection buttons, show restart button
            document.getElementById('startLiveInspectionBtn').style.display = 'none';
            document.getElementById('stopLiveInspectionBtn').style.display = 'none';
            document.getElementById('restartLiveBtn').style.display = 'inline-block';
            
            // Stop polling
            stopLiveInspectionPolling();
            
            // Save session and enable analysis
            saveInspectionSession('live', response.results);
            
            console.log('Live inspection stopped. Session saved to records.');
        } else {
            alert('Failed to stop inspection: ' + response.message);
        }
    }).catch(error => {
        console.error('Error stopping inspection:', error);
        alert('Error stopping inspection');
    });
}

function handleRestartLiveVideo() {
    // Stop motion detection
    stopMotionDetection();
    
    // Stop the video stream
    const imgElement = document.getElementById('liveVideoFeed');
    imgElement.src = '';
    imgElement.style.display = 'none';
    
    // Clear all data from the live video page
    clearLiveVideoPageData();
    
    // Reset buttons
    document.getElementById('startLiveBtn').disabled = false;
    document.getElementById('startLiveBtn').style.display = 'inline-block';
    document.getElementById('startLiveInspectionBtn').disabled = true;
    document.getElementById('startLiveInspectionBtn').style.display = 'inline-block';
    document.getElementById('stopLiveInspectionBtn').disabled = true;
    document.getElementById('stopLiveInspectionBtn').style.display = 'inline-block';
    document.getElementById('restartLiveBtn').style.display = 'none';
    
    // Reset status
    document.getElementById('liveVideoOverlay').classList.remove('hidden');
    document.getElementById('liveStatus').classList.remove('active');
    document.getElementById('liveStatusText').textContent = 'STANDBY';
    
    // Reset state
    AppState.liveVideoActive = false;
    AppState.liveInspectionActive = false;
    AppState.currentSessionId = null;
    
    // Reset motion detection state
    if (AppState.motionDetection.autoMode) {
        resetMotionState();
        logMotionEvent('System reset - ready for new session', 'idle');
    }
    
    console.log('Live video page reset. Previous session saved in records.');
}

function clearLiveVideoPageData() {
    // Clear system stats
    document.getElementById('liveFps').textContent = '0';
    document.getElementById('liveLatency').textContent = '0';
    document.getElementById('liveFramesProcessed').textContent = '0';
    document.getElementById('liveDetections').textContent = '0';
    
    // Clear blur quality
    document.getElementById('blurQuality').style.width = '0%';
    document.getElementById('blurQualityText').textContent = '0%';
    
    // Clear OCR status
    const ocrIndicator = document.getElementById('ocrStatus');
    ocrIndicator.textContent = 'PENDING';
    ocrIndicator.className = 'ocr-indicator';
    
    // Clear damage detection
    const damageStatus = document.getElementById('liveDamageStatus');
    damageStatus.innerHTML = `
        <div class="damage-indicator no-damage">
            <span class="damage-icon">✓</span>
            <span class="damage-text">NO DAMAGE DETECTED</span>
        </div>
    `;
    const damageDetails = document.getElementById('liveDamageDetails');
    damageDetails.style.display = 'none';
    damageDetails.innerHTML = '';
    
    // Clear wagon detections
    const wagonDetections = document.getElementById('wagonDetections');
    wagonDetections.innerHTML = '<div class="frame-placeholder">NO DETECTIONS</div>';
    
    // Clear deblurred frames
    const deblurredFrames = document.getElementById('deblurredFrames');
    deblurredFrames.innerHTML = '<div class="frame-placeholder">NO FRAMES</div>';
    
    // Clear comparison images
    const beforeImage = document.getElementById('beforeImage');
    const afterImage = document.getElementById('afterImage');
    beforeImage.innerHTML = '<div class="frame-placeholder">NO DATA</div>';
    afterImage.innerHTML = '<div class="frame-placeholder">NO DATA</div>';
}

function simulateLiveVideoFeed() {
    // Placeholder: In real implementation, this would access camera via getUserMedia
    // For now, just show that video is active
    console.log('Live video feed started (placeholder)');
}

let liveInspectionInterval;

function startLiveInspectionPolling() {
    // Poll backend for status updates every 500ms
    liveInspectionInterval = setInterval(() => {
        if (!AppState.liveInspectionActive || !AppState.currentSessionId) {
            return;
        }
        
        apiGetInspectionStatus(AppState.currentSessionId).then(response => {
            if (response.status === 'success' && response.data) {
                const data = response.data;
                
                // Update system stats
                document.getElementById('liveFps').textContent = data.fps || 0;
                document.getElementById('liveLatency').textContent = data.latency || 0;
                document.getElementById('liveFramesProcessed').textContent = data.frames_processed || 0;
                document.getElementById('liveDetections').textContent = data.detections || 0;
                
                // Update real motion data from backend if available
                if (AppState.motionDetection.autoMode && data.motion_level !== undefined) {
                    document.getElementById('motionLevel').textContent = data.motion_level.toFixed(1) + '%';
                    
                    // Update motion state from backend
                    if (data.motion_state) {
                        const stateMap = {
                            'IDLE': 'IDLE',
                            'LEARNING': 'LEARNING',
                            'MOTION_CANDIDATE': 'MOTION DETECTED',
                            'TRAIN_CONFIRMED': '✓ TRAIN CONFIRMED',
                            'INSPECTION_RUNNING': 'INSPECTION RUNNING'
                        };
                        const displayState = stateMap[data.motion_state] || data.motion_state;
                        document.getElementById('motionStateText').textContent = displayState;
                        
                        // Update train confirmed status
                        const trainStatus = document.getElementById('trainConfirmedStatus');
                        if (data.train_confirmed) {
                            trainStatus.textContent = 'YES';
                            trainStatus.className = 'train-status confirmed';
                        } else {
                            trainStatus.textContent = 'NO';
                            trainStatus.className = 'train-status';
                        }
                        
                        // Update indicator class
                        const indicator = document.getElementById('motionIndicator');
                        indicator.classList.remove('idle', 'detected', 'confirmed', 'recording');
                        
                        if (data.motion_state === 'IDLE' || data.motion_state === 'LEARNING') {
                            indicator.classList.add('idle');
                        } else if (data.motion_state === 'MOTION_CANDIDATE') {
                            indicator.classList.add('detected');
                        } else if (data.motion_state === 'TRAIN_CONFIRMED') {
                            indicator.classList.add('confirmed');
                        } else if (data.motion_state === 'INSPECTION_RUNNING') {
                            indicator.classList.add('recording');
                        }
                    }
                }
                
                // Update blur quality (simulate based on processing)
                const blurQuality = Math.min(95, 60 + (data.frames_processed || 0) * 0.5);
                document.getElementById('blurQuality').style.width = blurQuality + '%';
                document.getElementById('blurQualityText').textContent = Math.floor(blurQuality) + '%';
                
                // Update OCR status
                const ocrIndicator = document.getElementById('ocrStatus');
                if (data.detections > 0) {
                    ocrIndicator.textContent = 'SUCCESS';
                    ocrIndicator.className = 'ocr-indicator success';
                } else {
                    ocrIndicator.textContent = 'PENDING';
                    ocrIndicator.className = 'ocr-indicator';
                }
                
                // Add ALL wagon detections (process all new ones)
                if (data.wagon_numbers && data.wagon_numbers.length > 0) {
                    data.wagon_numbers.forEach(detection => {
                        addWagonDetection('wagonDetections', detection);
                    });
                    
                    // Update comparison with latest
                    const latest = data.wagon_numbers[data.wagon_numbers.length - 1];
                    updateComparison('beforeImage', 'afterImage', latest.frame);
                }
                
                // Update damage detection display
                updateDamageDisplay('live', data.damage_detections || []);
                
                // Add deblurred frames using base64 thumbnails
                if (data.deblurred_thumbnails && data.deblurred_thumbnails.length > 0) {
                    data.deblurred_thumbnails.forEach((thumbnail, index) => {
                        const originalThumb = data.original_thumbnails && data.original_thumbnails[index] 
                            ? data.original_thumbnails[index] 
                            : thumbnail;
                        addDeblurredFrameFromBase64('deblurredFrames', originalThumb, thumbnail, index);
                    });
                }
            }
        }).catch(error => {
            console.error('Error polling inspection status:', error);
        });
    }, 500);
}

function stopLiveInspectionPolling() {
    if (liveInspectionInterval) {
        clearInterval(liveInspectionInterval);
        liveInspectionInterval = null;
    }
}

// ====================================================
// MOTION DETECTION AUTO MODE
// ====================================================

function initializeMotionDetection() {
    const autoModeToggle = document.getElementById('autoModeToggle');
    const autoModeLabel = document.getElementById('autoModeLabel');
    const liveModeDisplay = document.getElementById('liveMode');
    const simulateTrainBtn = document.getElementById('simulateTrainBtn');
    
    autoModeToggle.addEventListener('change', (e) => {
        AppState.motionDetection.autoMode = e.target.checked;
        
        // Update UI labels
        autoModeLabel.textContent = e.target.checked ? 'ON' : 'OFF';
        liveModeDisplay.textContent = e.target.checked ? 'AUTO' : 'MANUAL';
        
        if (e.target.checked) {
            // Auto mode enabled - backend will handle motion detection
            logMotionEvent('Auto mode ENABLED - Backend motion detection will activate', 'recording');
            
            // Update button title to inform user
            const startInspectionBtn = document.getElementById('startLiveInspectionBtn');
            if (startInspectionBtn && !AppState.liveInspectionActive) {
                startInspectionBtn.title = 'Start inspection with automatic train detection';
            }
        } else {
            // Auto mode disabled - manual capture mode
            logMotionEvent('Auto mode DISABLED - Manual capture mode', 'idle');
            
            // Update button title
            const startInspectionBtn = document.getElementById('startLiveInspectionBtn');
            if (startInspectionBtn && AppState.liveVideoActive && !AppState.liveInspectionActive) {
                startInspectionBtn.title = 'Start inspection and capture all frames';
            }
        }
    });
    
    // Simulate Train Button
    simulateTrainBtn.addEventListener('click', () => {
        if (AppState.motionDetection.autoMode && AppState.liveVideoActive) {
            AppState.motionDetection.simulatingTrain = true;
            AppState.motionDetection.trainSimulationFrame = 0;
            logMotionEvent('Manual trigger: Simulating train approach', 'motion');
            simulateTrainBtn.disabled = true;
            simulateTrainBtn.textContent = 'TRAIN SIMULATING...';
        }
    });
}

function startMotionDetection() {
    // Reset counters
    AppState.motionDetection.motionFrameCount = 0;
    AppState.motionDetection.noMotionFrameCount = 0;
    AppState.motionDetection.totalFramesAnalyzed = 0;
    
    logMotionEvent('Motion detection started', 'motion');
    updateMotionState('IDLE');
    
    // Start detection loop (placeholder simulation)
    AppState.motionDetection.detectionTimer = setInterval(() => {
        simulateMotionDetection();
    }, 100); // Check every 100ms
}

function stopMotionDetection() {
    if (AppState.motionDetection.detectionTimer) {
        clearInterval(AppState.motionDetection.detectionTimer);
        AppState.motionDetection.detectionTimer = null;
    }
}

function resetMotionState() {
    updateMotionState('IDLE');
    AppState.motionDetection.motionFrameCount = 0;
    AppState.motionDetection.noMotionFrameCount = 0;
    AppState.motionDetection.totalFramesAnalyzed = 0;
    AppState.motionDetection.currentMotionLevel = 0;
    
    // Clear event log
    const eventLog = document.getElementById('eventLogContent');
    eventLog.innerHTML = '<div class="event-placeholder">AUTO MODE DISABLED</div>';
    
    // Reset metrics display
    document.getElementById('motionFrames').textContent = '0';
    document.getElementById('motionLevel').textContent = '0%';
}

function simulateMotionDetection() {
    // Frontend motion simulation - only active when NOT inspecting
    // During inspection, backend provides real motion data
    
    if (!AppState.liveVideoActive || !AppState.motionDetection.autoMode) {
        return;
    }
    
    // If inspection is running, backend handles motion detection
    if (AppState.liveInspectionActive) {
        return;
    }
    
    const md = AppState.motionDetection;
    md.totalFramesAnalyzed++;
    
    // Update frames counter
    document.getElementById('motionFrames').textContent = md.totalFramesAnalyzed;
    
    let motionIntensity = 0;
    
    // REALISTIC SIMULATION: No motion by default (static camera watching track)
    // Motion only occurs when user clicks "SIMULATE TRAIN" button
    
    if (md.simulatingTrain) {
        md.trainSimulationFrame++;
        
        // Simulate realistic train passing sequence
        if (md.trainSimulationFrame < 15) {
            // Train approaching (increasing motion)
            motionIntensity = Math.floor(10 + (md.trainSimulationFrame * 1.5));
        } else if (md.trainSimulationFrame < 120) {
            // Train passing (sustained high motion)
            motionIntensity = Math.floor(20 + Math.random() * 15);
        } else if (md.trainSimulationFrame < 135) {
            // Train leaving (decreasing motion)
            motionIntensity = Math.floor(25 - ((md.trainSimulationFrame - 120) * 1.5));
        } else {
            // Train gone (no motion)
            motionIntensity = Math.floor(Math.random() * 5);
            md.simulatingTrain = false;
            
            // Re-enable simulate button after train passes
            const simulateBtn = document.getElementById('simulateTrainBtn');
            if (simulateBtn && md.currentState === 'IDLE') {
                simulateBtn.disabled = false;
                simulateBtn.textContent = 'SIMULATE TRAIN';
            }
        }
    } else {
        // No train - static scene (wall/track with minimal noise)
        // Real cameras have sensor noise ~0-5% variation
        motionIntensity = Math.floor(Math.random() * 3);
    }
    
    md.currentMotionLevel = motionIntensity;
    document.getElementById('motionLevel').textContent = motionIntensity + '%';
    
    // State machine logic
    switch (md.currentState) {
        case 'IDLE':
            if (motionIntensity >= md.MOTION_THRESHOLD) {
                md.motionFrameCount++;
                md.noMotionFrameCount = 0;
                
                if (md.motionFrameCount >= 3) {
                    updateMotionState('MOTION_DETECTED');
                    logMotionEvent('Motion detected in frame stream', 'motion');
                }
            } else {
                md.motionFrameCount = 0;
            }
            break;
            
        case 'MOTION_DETECTED':
            if (motionIntensity >= md.MOTION_THRESHOLD) {
                md.motionFrameCount++;
                md.noMotionFrameCount = 0;
                
                if (md.motionFrameCount >= md.MOTION_CONFIRM_FRAMES) {
                    updateMotionState('TRAIN_CONFIRMED');
                    logMotionEvent('Train confirmed - initiating inspection', 'train');
                    
                    // Auto-start inspection
                    setTimeout(() => {
                        if (md.currentState === 'TRAIN_CONFIRMED' && !AppState.liveInspectionActive) {
                            autoStartInspection();
                        }
                    }, 500);
                }
            } else {
                md.noMotionFrameCount++;
                
                if (md.noMotionFrameCount >= 20) {
                    updateMotionState('IDLE');
                    logMotionEvent('False alarm - returning to idle', 'idle');
                    md.motionFrameCount = 0;
                }
            }
            break;
            
        case 'TRAIN_CONFIRMED':
            // Waiting for inspection to start
            if (AppState.liveInspectionActive) {
                updateMotionState('INSPECTION_RUNNING');
            }
            break;
            
        case 'INSPECTION_RUNNING':
            // Backend handles motion detection during inspection
            // This state is just for UI consistency
            break;
    }
}

function updateMotionState(newState) {
    AppState.motionDetection.currentState = newState;
    
    const stateText = document.getElementById('motionStateText');
    const indicator = document.getElementById('motionIndicator');
    
    // Remove all state classes
    indicator.classList.remove('idle', 'detected', 'confirmed', 'recording');
    
    switch (newState) {
        case 'IDLE':
            stateText.textContent = 'IDLE';
            indicator.classList.add('idle');
            break;
        case 'MOTION_DETECTED':
            stateText.textContent = 'TRAIN DETECTED';
            indicator.classList.add('detected');
            break;
        case 'TRAIN_CONFIRMED':
            stateText.textContent = 'TRAIN CONFIRMED';
            indicator.classList.add('confirmed');
            break;
        case 'INSPECTION_RUNNING':
            stateText.textContent = 'RECORDING';
            indicator.classList.add('recording');
            break;
    }
}

function logMotionEvent(message, type = 'idle') {
    const eventLog = document.getElementById('eventLogContent');
    
    // Remove placeholder if it exists
    const placeholder = eventLog.querySelector('.event-placeholder');
    if (placeholder) {
        eventLog.innerHTML = '';
    }
    
    // Create event entry
    const eventEntry = document.createElement('div');
    eventEntry.className = 'event-entry';
    
    const timestamp = document.createElement('span');
    timestamp.className = 'event-timestamp';
    const now = new Date();
    timestamp.textContent = now.toLocaleTimeString('en-US', { hour12: false });
    
    const eventMessage = document.createElement('span');
    eventMessage.className = `event-message ${type}`;
    eventMessage.textContent = message;
    
    eventEntry.appendChild(timestamp);
    eventEntry.appendChild(eventMessage);
    
    // Add to top of log
    eventLog.insertBefore(eventEntry, eventLog.firstChild);
    
    // Limit to 20 entries
    while (eventLog.children.length > 20) {
        eventLog.removeChild(eventLog.lastChild);
    }
}

function autoStartInspection() {
    logMotionEvent('AUTO START: Train confirmed - Starting inspection', 'recording');
    
    // Temporarily allow auto start even though auto mode is on
    const wasAutoMode = AppState.motionDetection.autoMode;
    AppState.motionDetection.autoMode = false;
    
    // Call the start inspection handler
    apiStartInspection('live').then(response => {
        if (response.status === 'success') {
            AppState.liveInspectionActive = true;
            AppState.currentSessionId = response.session_id;
            
            // Re-enable auto mode
            AppState.motionDetection.autoMode = wasAutoMode;
            
            // Update UI
            document.getElementById('liveStatusText').textContent = 'INSPECTION RUNNING (AUTO)';
            
            // Enable stop button, keep start disabled
            document.getElementById('startLiveInspectionBtn').disabled = true;
            document.getElementById('stopLiveInspectionBtn').disabled = false;
            
            // Start polling for status updates
            startLiveInspectionPolling();
            
            logMotionEvent('Inspection started successfully', 'recording');
            console.log('Auto inspection started:', response.session_id);
        } else {
            AppState.motionDetection.autoMode = wasAutoMode;
            logMotionEvent('AUTO START FAILED: ' + response.message, 'stopped');
        }
    }).catch(error => {
        AppState.motionDetection.autoMode = wasAutoMode;
        console.error('Error in auto-start inspection:', error);
        logMotionEvent('AUTO START ERROR: ' + error.message, 'stopped');
    });
}

function autoStopInspection() {
    logMotionEvent('AUTO STOP: Inspection completed', 'stopped');
    
    // Programmatically trigger inspection stop
    handleStopLiveInspection();
}

// ====================================================
// RECORDED VIDEO INSPECTION PAGE
// ====================================================

function initializeRecordedVideoPage() {
    const videoFileInput = document.getElementById('videoFileInput');
    const startInspectionBtn = document.getElementById('startRecordedInspectionBtn');
    const stopInspectionBtn = document.getElementById('stopRecordedInspectionBtn');
    const uploadAnotherBtn = document.getElementById('uploadAnotherVideoBtn');
    
    videoFileInput.addEventListener('change', handleVideoFileSelect);
    startInspectionBtn.addEventListener('click', handleStartRecordedInspection);
    stopInspectionBtn.addEventListener('click', handleStopRecordedInspection);
    uploadAnotherBtn.addEventListener('click', handleUploadAnotherVideo);
}

function handleVideoFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('videoFileName').textContent = file.name;
        
        // Load video
        const video = document.getElementById('recordedVideoFeed');
        video.src = URL.createObjectURL(file);
        
        // Hide overlay
        document.getElementById('recordedVideoOverlay').classList.add('hidden');
        
        // Enable inspection button
        document.getElementById('startRecordedInspectionBtn').disabled = false;
    }
}

function handleStartRecordedInspection() {
    const videoFileInput = document.getElementById('videoFileInput');
    const file = videoFileInput.files[0];
    
    if (!file) {
        alert('Please select a video file first');
        return;
    }
    
    // Save file to backend first
    const formData = new FormData();
    formData.append('video', file);
    
    // Upload video file
    fetch(`${API_BASE_URL}/api/upload/video`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(uploadResponse => {
        if (uploadResponse.status === 'success') {
            const videoPath = uploadResponse.path;
            
            // Start inspection with uploaded video path
            return apiStartInspection('recorded', videoPath);
        } else {
            throw new Error('Failed to upload video');
        }
    })
    .then(response => {
        if (response.status === 'success') {
            AppState.recordedInspectionActive = true;
            AppState.currentSessionId = response.session_id;
            
            // Update UI
            document.getElementById('recordedStatus').classList.add('active');
            document.getElementById('recordedStatusText').textContent = 'INSPECTION RUNNING';
            
            // Enable stop button, disable start
            document.getElementById('startRecordedInspectionBtn').disabled = true;
            document.getElementById('stopRecordedInspectionBtn').disabled = false;
            
            // Start polling for status updates
            startRecordedInspectionPolling();
            
            console.log('Recorded inspection started:', response.session_id);
        } else {
            alert('Failed to start inspection: ' + response.message);
        }
    })
    .catch(error => {
        console.error('Error starting inspection:', error);
        alert('Error starting inspection: ' + error.message);
    });
}

function handleStopRecordedInspection() {
    // Call backend to stop inspection
    apiStopInspection(AppState.currentSessionId).then(response => {
        if (response.status === 'success') {
            AppState.recordedInspectionActive = false;
            
            // Update UI
            document.getElementById('recordedStatusText').textContent = 'COMPLETED';
            document.getElementById('recordedStatus').classList.remove('active');
            
            // Disable stop button, show upload another button
            document.getElementById('startRecordedInspectionBtn').disabled = true;
            document.getElementById('stopRecordedInspectionBtn').disabled = true;
            document.getElementById('uploadAnotherVideoBtn').style.display = 'inline-block';
            
            // Stop polling
            stopRecordedInspectionPolling();
            
            // Save session and enable analysis
            saveInspectionSession('recorded', response.results);
            
            console.log('Recorded inspection stopped - results saved to records');
        } else {
            alert('Failed to stop inspection: ' + response.message);
        }
    }).catch(error => {
        console.error('Error stopping inspection:', error);
        alert('Error stopping inspection');
    });
}

function handleUploadAnotherVideo() {
    // Archive current session
    if (AppState.currentSessionId) {
        apiArchiveSession(AppState.currentSessionId).then(() => {
            console.log('Session archived successfully');
        }).catch(error => {
            console.error('Error archiving session:', error);
        });
    }
    
    // Clear all results from UI
    clearRecordedVideoResults();
    
    // Reset state
    AppState.currentSessionId = null;
    AppState.recordedInspectionActive = false;
    
    // Reset UI to initial state
    document.getElementById('recordedStatusText').textContent = 'STANDBY';
    document.getElementById('recordedStatus').classList.remove('active');
    
    // Reset buttons
    document.getElementById('videoFileInput').value = '';
    document.getElementById('videoFileName').textContent = 'NO FILE SELECTED';
    document.getElementById('startRecordedInspectionBtn').disabled = true;
    document.getElementById('stopRecordedInspectionBtn').disabled = true;
    document.getElementById('uploadAnotherVideoBtn').style.display = 'none';
    
    // Clear video
    const video = document.getElementById('recordedVideoFeed');
    video.src = '';
    video.load();
    document.getElementById('recordedVideoOverlay').classList.remove('hidden');
    
    console.log('Ready for new video upload');
}

function clearRecordedVideoResults() {
    // Clear stats
    document.getElementById('recordedFps').textContent = '0';
    document.getElementById('recordedLatency').textContent = '0';
    document.getElementById('recordedFramesProcessed').textContent = '0';
    document.getElementById('recordedDetections').textContent = '0';
    
    // Reset blur quality
    document.getElementById('recordedBlurQuality').style.width = '0%';
    document.getElementById('recordedBlurQualityText').textContent = '0%';
    
    // Reset OCR status
    const ocrIndicator = document.getElementById('recordedOcrStatus');
    ocrIndicator.textContent = 'PENDING';
    ocrIndicator.className = 'ocr-indicator';
    
    // Clear damage detection
    const damageStatus = document.getElementById('recordedDamageStatus');
    damageStatus.innerHTML = `
        <div class="damage-indicator no-damage">
            <span class="damage-icon">✓</span>
            <span class="damage-text">NO DAMAGE DETECTED</span>
        </div>
    `;
    const damageDetails = document.getElementById('recordedDamageDetails');
    damageDetails.style.display = 'none';
    damageDetails.innerHTML = '';
    
    // Clear deblurred frames
    const deblurredContainer = document.getElementById('recordedDeblurredFrames');
    deblurredContainer.innerHTML = '<div class="frame-placeholder">AWAITING DATA</div>';
    
    // Clear wagon detections
    const wagonContainer = document.getElementById('recordedWagonDetections');
    wagonContainer.innerHTML = '<div class="frame-placeholder">NO DETECTIONS</div>';
    
    // Clear comparison images
    const beforeImage = document.getElementById('recordedBeforeImage');
    const afterImage = document.getElementById('recordedAfterImage');
    beforeImage.innerHTML = '<div class="comparison-placeholder">NO DATA</div>';
    afterImage.innerHTML = '<div class="comparison-placeholder">NO DATA</div>';
}

let recordedInspectionInterval;

function startRecordedInspectionPolling() {
    // Poll backend for status updates every 500ms
    recordedInspectionInterval = setInterval(() => {
        if (!AppState.recordedInspectionActive || !AppState.currentSessionId) {
            return;
        }
        
        apiGetInspectionStatus(AppState.currentSessionId).then(response => {
            if (response.status === 'success' && response.data) {
                const data = response.data;
                
                // Check if inspection completed automatically
                if (data.completed) {
                    console.log('Recorded inspection completed automatically');
                    handleRecordedInspectionComplete();
                    return;
                }
                
                // Update system stats
                document.getElementById('recordedFps').textContent = data.fps || 0;
                document.getElementById('recordedLatency').textContent = data.latency || 0;
                document.getElementById('recordedFramesProcessed').textContent = data.frames_processed || 0;
                document.getElementById('recordedDetections').textContent = data.detections || 0;
                
                // Update blur quality (simulate based on processing)
                const blurQuality = Math.min(95, 60 + (data.frames_processed || 0) * 0.5);
                document.getElementById('recordedBlurQuality').style.width = blurQuality + '%';
                document.getElementById('recordedBlurQualityText').textContent = Math.floor(blurQuality) + '%';
                
                // Update OCR status
                const ocrIndicator = document.getElementById('recordedOcrStatus');
                if (data.detections > 0) {
                    ocrIndicator.textContent = 'SUCCESS';
                    ocrIndicator.className = 'ocr-indicator success';
                } else {
                    ocrIndicator.textContent = 'PENDING';
                    ocrIndicator.className = 'ocr-indicator';
                }
                
                // Add ALL wagon detections (process all new ones)
                if (data.wagon_numbers && data.wagon_numbers.length > 0) {
                    data.wagon_numbers.forEach(detection => {
                        addWagonDetection('recordedWagonDetections', detection);
                    });
                    
                    // Update comparison with latest
                    const latest = data.wagon_numbers[data.wagon_numbers.length - 1];
                    updateComparison('recordedBeforeImage', 'recordedAfterImage', latest.frame);
                }
                
                // Update damage detection display
                updateDamageDisplay('recorded', data.damage_detections || []);
                
                // Add deblurred frames using base64 thumbnails
                if (data.deblurred_thumbnails && data.deblurred_thumbnails.length > 0) {
                    data.deblurred_thumbnails.forEach((thumbnail, index) => {
                        const originalThumb = data.original_thumbnails && data.original_thumbnails[index] 
                            ? data.original_thumbnails[index] 
                            : thumbnail;
                        addDeblurredFrameFromBase64('recordedDeblurredFrames', originalThumb, thumbnail, index);
                    });
                }
            }
        }).catch(error => {
            console.error('Error polling inspection status:', error);
        });
    }, 500);
}

function stopRecordedInspectionPolling() {
    if (recordedInspectionInterval) {
        clearInterval(recordedInspectionInterval);
        recordedInspectionInterval = null;
    }
}

function handleRecordedInspectionComplete() {
    // Auto-stop when video ends
    AppState.recordedInspectionActive = false;
    
    // Update UI
    document.getElementById('recordedStatusText').textContent = 'COMPLETED';
    document.getElementById('recordedStatus').classList.remove('active');
    
    // Enable start button, disable stop
    document.getElementById('startRecordedInspectionBtn').disabled = false;
    document.getElementById('stopRecordedInspectionBtn').disabled = true;
    
    // Stop polling
    stopRecordedInspectionPolling();
    
    // Get final results and save session
    if (AppState.currentSessionId) {
        apiStopInspection(AppState.currentSessionId).then(response => {
            if (response.status === 'success') {
                saveInspectionSession('recorded', response.results);
                console.log('Recorded inspection session saved');
            }
        }).catch(error => {
            console.error('Error saving inspection results:', error);
        });
    }
}

// ====================================================
// IMAGE INSPECTION PAGE
// ====================================================

function initializeImageInspectionPage() {
    const imageFileInput = document.getElementById('imageFileInput');
    const processBtn = document.getElementById('processImageBtn');
    
    imageFileInput.addEventListener('change', handleImageFileSelect);
    processBtn.addEventListener('click', handleProcessImage);
}

function handleImageFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('imageFileName').textContent = file.name;
        
        // Load image
        const reader = new FileReader();
        reader.onload = function(event) {
            const originalContainer = document.getElementById('originalImage');
            originalContainer.innerHTML = `<img src="${event.target.result}" alt="Original">`;
            
            // Update image size
            const img = new Image();
            img.onload = function() {
                document.getElementById('imageSize').textContent = `${this.width}x${this.height}`;
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
        
        // Enable process button
        document.getElementById('processImageBtn').disabled = false;
    }
}

function handleProcessImage() {
    const fileInput = document.getElementById('imageFileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select an image first');
        return;
    }
    
    // Update status
    document.getElementById('imageStatus').classList.add('active');
    document.getElementById('imageStatusText').textContent = 'PROCESSING';
    
    // Disable button during processing
    document.getElementById('processImageBtn').disabled = true;
    
    const startTime = Date.now();
    
    // Call backend API
    apiProcessImage(file).then(response => {
        if (response.status === 'success' && response.data) {
            const data = response.data;
            
            // Display deblurred image
            const deblurredContainer = document.getElementById('deblurredImage');
            const img = new Image();
            img.onload = function() {
                deblurredContainer.innerHTML = '';
                deblurredContainer.appendChild(img);
            };
            // Use base64 image if available, otherwise fall back to file path
            img.src = data.deblurred_base64 || `${API_BASE_URL}/${data.deblurred_path}`;
            
            // Update processing time
            document.getElementById('imageProcessTime').textContent = data.processing_time + ' ms';
            
            // Display wagon detection if available
            if (data.wagon_number && data.wagon_base64) {
                const wagonSection = document.getElementById('imageWagonSection');
                const wagonContainer = document.getElementById('imageWagonDetection');
                
                wagonSection.style.display = 'block';
                wagonContainer.innerHTML = `
                    <div class="frame-item">
                        <img src="${data.wagon_base64}" loading="lazy" 
                             onclick="viewImage('${data.wagon_base64}', '${data.wagon_number}')">
                        <div class="frame-label">${data.wagon_number}</div>
                    </div>
                `;
                console.log('Wagon number detected:', data.wagon_number);
            } else {
                // Hide wagon section if no detection
                document.getElementById('imageWagonSection').style.display = 'none';
            }
            
            // Update damage detection display
            updateDamageDisplayForImage(data);
            
            // Update status
            document.getElementById('imageStatusText').textContent = 'COMPLETE';
            document.getElementById('imageStatus').classList.remove('active');
            
            console.log('Image processed successfully');
        } else {
            alert('Failed to process image: ' + (response.message || 'Unknown error'));
            document.getElementById('imageStatusText').textContent = 'ERROR';
            document.getElementById('imageStatus').classList.remove('active');
        }
        
        // Re-enable button
        document.getElementById('processImageBtn').disabled = false;
    }).catch(error => {
        console.error('Error processing image:', error);
        alert('Error processing image. Is the backend running?');
        
        document.getElementById('imageStatusText').textContent = 'ERROR';
        document.getElementById('imageStatus').classList.remove('active');
        document.getElementById('processImageBtn').disabled = false;
    });
}

// ====================================================
// HELPER FUNCTIONS - FRAME DISPLAY
// ====================================================

function addDeblurredFrame(containerId, frameNumber) {
    const container = document.getElementById(containerId);
    
    // Remove placeholder if exists
    const placeholder = container.querySelector('.frame-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Check if frame already exists
    const existingFrame = container.querySelector(`[data-frame="${frameNumber}"]`);
    if (existingFrame) {
        return; // Don't add duplicates
    }
    
    // Add new frame with image if available
    const frameDiv = document.createElement('div');
    frameDiv.className = 'frame-item';
    frameDiv.setAttribute('data-frame', frameNumber);
    
    // Try to load actual deblurred image from session
    if (AppState.currentSessionId) {
        const imgPath = `${API_BASE_URL}/api/session/${AppState.currentSessionId}/image/deblurred_${String(frameNumber).padStart(6, '0')}.jpg`;
        frameDiv.innerHTML = `
            <img src="${imgPath}" onerror="this.style.display='none'" loading="lazy">
            <div class="frame-label">FRAME ${frameNumber}</div>
        `;
    } else {
        frameDiv.innerHTML = `<div class="frame-label">FRAME ${frameNumber}</div>`;
    }
    
    container.appendChild(frameDiv);
}

function addDeblurredFrameFromPath(containerId, framePath) {
    const container = document.getElementById(containerId);
    
    // Remove placeholder if exists
    const placeholder = container.querySelector('.frame-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Extract filename to use as unique identifier
    const filename = framePath.split('/').pop();
    
    // Check if frame already exists
    const existingFrame = container.querySelector(`[data-frame="${filename}"]`);
    if (existingFrame) {
        return; // Don't add duplicates
    }
    
    // Extract frame number from filename (e.g., deblurred_000015.jpg -> 15)
    const frameMatch = filename.match(/deblurred_(\d+)/);
    const frameNumber = frameMatch ? parseInt(frameMatch[1]) : 0;
    
    // Add new frame
    const frameDiv = document.createElement('div');
    frameDiv.className = 'frame-item';
    frameDiv.setAttribute('data-frame', filename);
    frameDiv.innerHTML = `
        <img src="${API_BASE_URL}${framePath}" onerror="this.style.display='none'" loading="lazy">
        <div class="frame-label">FRAME ${frameNumber}</div>
    `;
    
    container.appendChild(frameDiv);
}

function addDeblurredFrameFromBase64(containerId, originalBase64, deblurredBase64, index) {
    const container = document.getElementById(containerId);
    
    // Remove placeholder if exists
    const placeholder = container.querySelector('.frame-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Check if frame already exists
    const existingFrame = container.querySelector(`[data-frame="frame_${index}"]`);
    if (existingFrame) {
        return; // Don't add duplicates
    }
    
    // Add new frame with before/after comparison
    const frameDiv = document.createElement('div');
    frameDiv.className = 'frame-item';
    frameDiv.setAttribute('data-frame', `frame_${index}`);
    frameDiv.innerHTML = `
        <img src="${deblurredBase64}" loading="lazy" 
             onclick="viewComparisonImages('${originalBase64}', '${deblurredBase64}', 'Frame ${index}')">
        <div class="frame-label">FRAME ${index}</div>
    `;
    
    container.appendChild(frameDiv);
}

function addWagonDetection(containerId, detection) {
    const container = document.getElementById(containerId);
    
    // Remove placeholder if exists
    const placeholder = container.querySelector('.frame-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const wagonNumber = detection.number;
    const frameNumber = detection.frame;
    const wagonBase64 = detection.wagon_base64;
    
    // Check if detection already exists
    const existingDetection = container.querySelector(`[data-wagon="${wagonNumber}-${frameNumber}"]`);
    if (existingDetection) {
        return; // Don't add duplicates
    }
    
    // Add new detection with image if available
    const frameDiv = document.createElement('div');
    frameDiv.className = 'frame-item';
    frameDiv.setAttribute('data-wagon', `${wagonNumber}-${frameNumber}`);
    
    // Use base64 image if available, otherwise show placeholder
    if (wagonBase64) {
        frameDiv.innerHTML = `
            <img src="${wagonBase64}" loading="lazy" onclick="viewImage('${wagonBase64}', '${wagonNumber}')">
            <div class="frame-label">${wagonNumber}</div>
        `;
    } else {
        frameDiv.innerHTML = `<div class="frame-label">${wagonNumber}</div>`;
    }
    
    container.appendChild(frameDiv);
}

function updateComparison(beforeId, afterId, frameNumber) {
    const beforeContainer = document.getElementById(beforeId);
    const afterContainer = document.getElementById(afterId);
    
    // Try to load actual images if session is active
    if (AppState.currentSessionId) {
        const originalPath = `${API_BASE_URL}/api/session/${AppState.currentSessionId}/image/frame_${String(frameNumber).padStart(6, '0')}.jpg`;
        const deblurredPath = `${API_BASE_URL}/api/session/${AppState.currentSessionId}/image/deblurred_${String(frameNumber).padStart(6, '0')}.jpg`;
        
        beforeContainer.innerHTML = `
            <img src="${originalPath}" onerror="this.parentElement.innerHTML='<div class=\\'frame-placeholder\\'>FRAME ${frameNumber}<br>ORIGINAL</div>'">
        `;
        afterContainer.innerHTML = `
            <img src="${deblurredPath}" onerror="this.parentElement.innerHTML='<div class=\\'frame-placeholder\\'>FRAME ${frameNumber}<br>DEBLURRED</div>'">
        `;
    } else {
        // Fallback to placeholder
        beforeContainer.innerHTML = `<div class="frame-placeholder">FRAME ${frameNumber}<br>ORIGINAL</div>`;
        afterContainer.innerHTML = `<div class="frame-placeholder">FRAME ${frameNumber}<br>DEBLURRED</div>`;
    }
}

function generateRandomWagonNumber() {
    const prefix = ['NR', 'ER', 'WR', 'SR', 'CR'];
    const randomPrefix = prefix[Math.floor(Math.random() * prefix.length)];
    const randomNumber = Math.floor(10000 + Math.random() * 90000);
    return `${randomPrefix}-${randomNumber}`;
}

// ====================================================
// LOAD DATA FROM BACKEND
// ====================================================

function loadSessionsFromBackend() {
    apiGetSessions().then(response => {
        if (response.status === 'success' && response.sessions) {
            // Convert backend format to frontend format
            AppState.inspectionSessions = response.sessions.map(s => ({
                id: s.id,
                type: s.type,
                date: s.start_time,
                operator: s.operator,
                wagonsDetected: s.results?.wagons_detected || 0,
                readable: s.results?.readable || 0,
                unreadable: s.results?.unreadable || 0,
                duration: s.results?.duration || 0
            }));
            
            // Update records page
            updateRecordsPage();
            
            // Enable analysis if we have sessions
            if (AppState.inspectionSessions.length > 0) {
                AppState.analysisEnabled = true;
                updateAnalysisState();
                updateAnalysisPage();
            }
        }
    }).catch(error => {
        console.error('Error loading sessions:', error);
    });
}

function loadAnalyticsFromBackend() {
    apiGetAnalytics().then(response => {
        if (response.status === 'success' && response.analytics) {
            const analytics = response.analytics;
            
            // Update analysis page
            document.getElementById('totalWagons').textContent = analytics.total_wagons || 0;
            document.getElementById('readableCount').textContent = analytics.readable || 0;
            document.getElementById('unreadableCount').textContent = analytics.unreadable || 0;
            document.getElementById('avgConfidence').textContent = (analytics.avg_confidence || 0) + '%';
            document.getElementById('inspectionDuration').textContent = (analytics.total_duration || 0) + 's';
        }
    }).catch(error => {
        console.error('Error loading analytics:', error);
    });
}

// ====================================================
// INSPECTION SESSION MANAGEMENT
// ====================================================

function saveInspectionSession(type, results) {
    if (!results) {
        results = {
            wagons_detected: 0,
            readable: 0,
            unreadable: 0,
            duration: 0
        };
    }
    
    const session = {
        id: AppState.currentSessionId || Date.now(),
        type: type,
        date: new Date().toISOString(),
        operator: AppState.currentUser.name,
        wagonsDetected: results.wagons_detected || 0,
        readable: results.readable || 0,
        unreadable: results.unreadable || 0,
        duration: results.duration || 0
    };
    
    AppState.inspectionSessions.push(session);
    
    // Enable analysis
    AppState.analysisEnabled = true;
    updateAnalysisState();
    
    // Reload sessions from backend
    loadSessionsFromBackend();
    
    // Update analysis page with latest data
    updateAnalysisPage();
}

// ====================================================
// ANALYSIS PAGE
// ====================================================

function updateAnalysisState() {
    const analysisNavItem = document.querySelector('.nav-item[data-page="analysis"]');
    const analysisCard = document.querySelector('.selection-card[data-page="analysis"]');
    const analysisContent = document.getElementById('analysisContent');
    const analysisDisabledMsg = document.getElementById('analysisDisabledMsg');
    
    if (AppState.analysisEnabled) {
        analysisNavItem.classList.remove('disabled');
        analysisCard.classList.remove('disabled');
        analysisContent.classList.add('enabled');
        analysisDisabledMsg.style.display = 'none';
    } else {
        analysisNavItem.classList.add('disabled');
        analysisCard.classList.add('disabled');
        analysisContent.classList.remove('enabled');
        analysisDisabledMsg.style.display = 'flex';
    }
}

function updateAnalysisPage() {
    if (AppState.inspectionSessions.length === 0) return;
    
    // Load sessions for selection
    loadAnalysisSessions();
}

// ====================================================
// RECORDS PAGE
// ====================================================

function initializeRecordsPage() {
    // Modal close button for active sessions
    const closeModal = document.getElementById('closeSessionModal');
    closeModal.addEventListener('click', () => {
        document.getElementById('sessionModal').classList.remove('active');
    });
    
    // Modal close button for deleted sessions
    const closeDeletedModal = document.getElementById('closeDeletedSessionModal');
    closeDeletedModal.addEventListener('click', () => {
        document.getElementById('deletedSessionModal').classList.remove('active');
    });
    
    // Close modal on background click
    document.getElementById('sessionModal').addEventListener('click', (e) => {
        if (e.target.id === 'sessionModal') {
            document.getElementById('sessionModal').classList.remove('active');
        }
    });
    
    // Close deleted modal on background click
    document.getElementById('deletedSessionModal').addEventListener('click', (e) => {
        if (e.target.id === 'deletedSessionModal') {
            document.getElementById('deletedSessionModal').classList.remove('active');
        }
    });
    
    // Close image viewer modal on background click
    const imageViewerModal = document.getElementById('imageViewerModal');
    if (imageViewerModal) {
        imageViewerModal.addEventListener('click', (e) => {
            if (e.target.id === 'imageViewerModal') {
                closeImageViewer();
            }
        });
    }
    
    // Load deleted sessions on init
    loadDeletedSessions();
}

// ====================================================
// CUSTOM CONFIRMATION MODAL
// ====================================================

function showConfirmModal(title, message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleElement = document.getElementById('confirmModalTitle');
        const messageElement = document.getElementById('confirmModalMessage');
        const confirmBtn = document.getElementById('confirmModalConfirm');
        const cancelBtn = document.getElementById('confirmModalCancel');
        
        titleElement.textContent = title;
        messageElement.textContent = message;
        
        modal.classList.add('active');
        
        const handleConfirm = () => {
            modal.classList.remove('active');
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            resolve(true);
        };
        
        const handleCancel = () => {
            modal.classList.remove('active');
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            resolve(false);
        };
        
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'confirmModal') {
                handleCancel();
            }
        });
    });
}

function updateRecordsPage() {
    const sessionsList = document.getElementById('sessionsList');
    
    if (AppState.inspectionSessions.length === 0) {
        sessionsList.innerHTML = '<div class="no-sessions">NO INSPECTION SESSIONS RECORDED</div>';
        return;
    }
    
    sessionsList.innerHTML = '';
    
    // Sort sessions by date (newest first)
    const sortedSessions = [...AppState.inspectionSessions].sort((a, b) => b.id - a.id);
    
    sortedSessions.forEach(session => {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = 'session-item';
        
        const date = new Date(session.date);
        const formattedDate = date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        sessionDiv.innerHTML = `
            <div class="session-header">
                <div class="session-title">${session.type.toUpperCase()} INSPECTION #${session.id}</div>
                <div class="session-date">${formattedDate}</div>
            </div>
            <div class="session-info">
                <span>OPERATOR: ${session.operator}</span>
                <span>WAGONS: ${session.wagonsDetected}</span>
                <span class="text-success">READABLE: ${session.readable}</span>
                <span class="text-danger">UNREADABLE: ${session.unreadable}</span>
                <span>DURATION: ${session.duration}s</span>
            </div>
        `;
        
        sessionDiv.addEventListener('click', () => openSessionDetail(session));
        
        sessionsList.appendChild(sessionDiv);
    });
}

function openSessionDetail(session) {
    const modal = document.getElementById('sessionModal');
    const modalTitle = document.getElementById('sessionModalTitle');
    const modalBody = document.getElementById('sessionModalBody');
    
    // Store session ID for deletion
    currentSessionIdForDelete = session.id;
    console.log('Session opened, ID stored for deletion:', currentSessionIdForDelete, 'Full session:', session);
    
    modalTitle.textContent = `${session.type.toUpperCase()} INSPECTION #${session.id}`;
    
    const date = new Date(session.date);
    const formattedDate = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Load full session details from backend
    apiGetSessionDetail(session.id).then(response => {
        if (response.status === 'success' && response.data) {
            const sessionData = response.data;
            
            modalBody.innerHTML = `
                <div class="analysis-section">
                    <h3 class="section-title">SESSION METADATA</h3>
                    <div class="summary-grid">
                        <div class="summary-card">
                            <div class="summary-label">DATE & TIME</div>
                            <div class="summary-value" style="font-size: 16px;">${formattedDate}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">OPERATOR</div>
                            <div class="summary-value" style="font-size: 16px;">${session.operator}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">TYPE</div>
                            <div class="summary-value" style="font-size: 16px;">${session.type.toUpperCase()}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">DURATION</div>
                            <div class="summary-value">${session.duration}s</div>
                        </div>
                    </div>
                </div>
                
                <div class="analysis-section">
                    <h3 class="section-title">DETECTION RESULTS</h3>
                    <div class="summary-grid">
                        <div class="summary-card">
                            <div class="summary-label">TOTAL WAGONS</div>
                            <div class="summary-value">${session.wagonsDetected}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">READABLE</div>
                            <div class="summary-value success">${session.readable}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">UNREADABLE</div>
                            <div class="summary-value error">${session.unreadable}</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-label">SUCCESS RATE</div>
                            <div class="summary-value">${session.wagonsDetected > 0 ? Math.floor((session.readable / session.wagonsDetected) * 100) : 0}%</div>
                        </div>
                    </div>
                </div>
                
                <!-- Section Tabs -->
                <div class="session-detail-tabs">
                    <button class="session-tab active" onclick="switchSessionTab('wagons', '${session.id}')">
                        <span class="tab-icon">🚂</span>
                        <span>WAGON NUMBERS</span>
                        <span class="tab-count">${sessionData.wagon_numbers ? sessionData.wagon_numbers.length : 0}</span>
                    </button>
                    <button class="session-tab" onclick="switchSessionTab('comparison', '${session.id}')">
                        <span class="tab-icon">🔄</span>
                        <span>BEFORE/AFTER</span>
                        <span class="tab-count">${sessionData.deblurred_thumbnails ? sessionData.deblurred_thumbnails.length : 0}</span>
                    </button>
                    <button class="session-tab" onclick="switchSessionTab('damage', '${session.id}')">
                        <span class="tab-icon">⚠️</span>
                        <span>DAMAGE DETECTION</span>
                        <span class="tab-count">${sessionData.damage_detections ? sessionData.damage_detections.length : 0}</span>
                    </button>
                </div>
                
                <!-- Tab Content -->
                <div id="sessionTabContent">
                    <!-- Wagon Numbers Tab -->
                    <div class="session-tab-panel active" data-tab="wagons">
                        <div class="wagon-grid">
                            ${generateWagonImagesGrid(sessionData.wagon_numbers || [])}
                        </div>
                    </div>
                    
                    <!-- Comparison Tab -->
                    <div class="session-tab-panel" data-tab="comparison">
                        <div class="comparison-grid">
                            ${generateComparisonFramesGrid(sessionData.original_thumbnails || [], sessionData.deblurred_thumbnails || [])}
                        </div>
                    </div>
                    
                    <!-- Damage Tab -->
                    <div class="session-tab-panel" data-tab="damage">
                        ${sessionData.damage_detections && sessionData.damage_detections.length > 0 
                            ? generateDamageDetectionsSection(sessionData.damage_detections || [])
                            : '<div class="no-data-message"><span class="success-icon">✓</span><p>NO DAMAGE DETECTED</p></div>'
                        }
                    </div>
                </div>
            `;
        }
    }).catch(error => {
        console.error('Error loading session details:', error);
        modalBody.innerHTML = `
            <div class="analysis-section">
                <p class="text-danger">Error loading session details</p>
            </div>
        `;
    });
    
    modal.classList.add('active');
}

function generateWagonImagesGrid(wagonDetections) {
    if (!wagonDetections || wagonDetections.length === 0) {
        return '<div class="frame-placeholder">NO WAGON DETECTIONS</div>';
    }
    
    return wagonDetections.map(detection => {
        // Check if it's a detection object (has 'number' field) or just an image path string
        if (typeof detection === 'object' && detection.number) {
            const wagonNum = detection.number;
            const imgSrc = detection.wagon_base64 || 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
            return `
                <div class="frame-item">
                    <img src="${imgSrc}" loading="lazy" onerror="this.parentElement.style.display='none'" onclick="viewImage('${imgSrc.replace(/'/g, "\\'")}', '${wagonNum}')">
                    <div class="frame-label">${wagonNum}</div>
                </div>
            `;
        } else {
            // Fallback for old format (just paths)
            const imgPath = detection;
            const fullPath = `${API_BASE_URL}${imgPath}`;
            const wagonNum = extractWagonNumber(imgPath);
            return `
                <div class="frame-item">
                    <img src="${fullPath}" loading="lazy" onerror="this.parentElement.style.display='none'" onclick="viewImage('${fullPath.replace(/'/g, "\\'")}', '${wagonNum}')">
                    <div class="frame-label">${wagonNum}</div>
                </div>
            `;
        }
    }).join('');
}

function generateDeblurredFramesGrid(deblurredFrames) {
    if (!deblurredFrames || deblurredFrames.length === 0) {
        return '<div class="frame-placeholder">NO DEBLURRED FRAMES</div>';
    }
    
    return deblurredFrames.map((imgPath, index) => {
        const frameMatch = imgPath.match(/deblurred_(\d+)/);
        const frameNumber = frameMatch ? parseInt(frameMatch[1]) : (index + 1) * 5;
        const fullPath = `${API_BASE_URL}${imgPath}`;
        return `
            <div class="frame-item">
                <img src="${fullPath}" loading="lazy" onerror="this.parentElement.style.display='none'" onclick="viewImage('${fullPath.replace(/'/g, "\\'")}', 'Frame ${frameNumber}')">
                <div class="frame-label">FRAME ${frameNumber}</div>
            </div>
        `;
    }).join('');
}

function generateComparisonFramesGrid(originalFrames, deblurredFrames) {
    if ((!deblurredFrames || deblurredFrames.length === 0) && (!originalFrames || originalFrames.length === 0)) {
        return '<div class="frame-placeholder">NO FRAMES AVAILABLE</div>';
    }
    
    // Check if frames are base64 or paths
    const isBase64 = deblurredFrames.length > 0 && deblurredFrames[0].startsWith('data:image');
    
    if (isBase64) {
        // Base64 thumbnails - pair them by index
        const comparisons = [];
        const maxFrames = Math.max(deblurredFrames.length, originalFrames.length);
        
        for (let i = 0; i < maxFrames; i++) {
            comparisons.push({
                frameNumber: (i + 1) * 5,
                original: originalFrames[i],
                deblurred: deblurredFrames[i]
            });
        }
        
        const comparisonItems = comparisons.map(comp => {
            const originalSrc = comp.original || 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
            const deblurredSrc = comp.deblurred || 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
            
            return `
                <div class="comparison-item" style="border: 1px solid #333; padding: 8px; background: #1a1a1a; cursor: pointer;" onclick="viewComparison('${originalSrc.replace(/'/g, "\\'").replace(/"/g, '&quot;')}', '${deblurredSrc.replace(/'/g, "\\'").replace(/"/g, '&quot;')}', ${comp.frameNumber})">
                    <div class="comparison-label" style="text-align: center; color: #00ff00; margin-bottom: 8px; font-weight: bold; font-size: 11px;">FRAME ${comp.frameNumber} - CLICK TO VIEW</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                        <div style="text-align: center;">
                            <div style="color: #888; margin-bottom: 3px; font-size: 10px;">ORIGINAL</div>
                            ${comp.original ? 
                                `<img src="${originalSrc}" style="width: 100%; border: 1px solid #444; pointer-events: none;" loading="lazy" onerror="this.style.display='none'">` :
                                '<div class="frame-placeholder" style="padding: 20px; font-size: 10px;">NO ORIGINAL</div>'
                            }
                        </div>
                        <div style="text-align: center;">
                            <div style="color: #888; margin-bottom: 3px; font-size: 10px;">DEBLURRED</div>
                            ${comp.deblurred ?
                                `<img src="${deblurredSrc}" style="width: 100%; border: 1px solid #00ff00; pointer-events: none;" loading="lazy" onerror="this.style.display='none'">` :
                                '<div class="frame-placeholder" style="padding: 20px; font-size: 10px;">NO DEBLURRED</div>'
                            }
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        return `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">${comparisonItems}</div>`;
    }
    
    // Old format: Match original and deblurred frames by frame number
    const comparisons = [];
    
    deblurredFrames.forEach(deblurredPath => {
        const frameMatch = deblurredPath.match(/deblurred_(\d+)/);
        if (frameMatch) {
            const frameNumber = frameMatch[1];
            const originalPath = originalFrames.find(p => p.includes(`frame_${frameNumber}`));
            comparisons.push({
                frameNumber: parseInt(frameNumber),
                original: originalPath,
                deblurred: deblurredPath
            });
        }
    });
    
    if (comparisons.length === 0) {
        return '<div class="frame-placeholder">NO MATCHED FRAMES</div>';
    }
    
    const comparisonItems = comparisons.map(comp => {
        const originalFullPath = comp.original ? `${API_BASE_URL}${comp.original}` : '';
        const deblurredFullPath = `${API_BASE_URL}${comp.deblurred}`;
        
        return `
            <div class="comparison-item" style="border: 1px solid #333; padding: 8px; background: #1a1a1a;">
                <div class="comparison-label" style="text-align: center; color: #00ff00; margin-bottom: 8px; font-weight: bold; font-size: 11px;">FRAME ${comp.frameNumber}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                    <div style="text-align: center;">
                        <div style="color: #888; margin-bottom: 3px; font-size: 10px;">ORIGINAL</div>
                        ${comp.original ? 
                            `<img src="${originalFullPath}" style="width: 100%; cursor: pointer; border: 1px solid #444;" loading="lazy" onerror="this.style.display='none'" onclick="viewImage('${originalFullPath.replace(/'/g, "\\'")}', 'Original Frame ${comp.frameNumber}')">` :
                            '<div class="frame-placeholder" style="padding: 20px; font-size: 10px;">NO ORIGINAL</div>'
                        }
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #888; margin-bottom: 3px; font-size: 10px;">DEBLURRED</div>
                        <img src="${deblurredFullPath}" style="width: 100%; cursor: pointer; border: 1px solid #00ff00;" loading="lazy" onerror="this.style.display='none'" onclick="viewImage('${deblurredFullPath.replace(/'/g, "\\'")}', 'Deblurred Frame ${comp.frameNumber}')">
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    return `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">${comparisonItems}</div>`;
}

function generateDamageDetectionsSection(damageDetections) {
    if (!damageDetections || damageDetections.length === 0) {
        return '<div class="frame-placeholder">NO DAMAGE DETECTIONS</div>';
    }
    
    const uniqueDamageTypes = [...new Set(damageDetections.map(d => d.damage_type))];
    const avgConfidence = (damageDetections.reduce((sum, d) => sum + (d.confidence || 0), 0) / damageDetections.length * 100).toFixed(0);
    
    return `
        <div class="damage-info-grid">
            <div class="damage-info-item">
                <div class="damage-info-label">Total Damages</div>
                <div class="damage-info-value critical">${damageDetections.length}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Damage Types</div>
                <div class="damage-info-value">${uniqueDamageTypes.length}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Average Confidence</div>
                <div class="damage-info-value">${avgConfidence}%</div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4 style="color: var(--text-secondary); font-size: 12px; margin-bottom: 12px;">DAMAGE IMAGES WITH ANNOTATIONS</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; max-height: 600px; overflow-y: auto;">
                ${damageDetections.map(damage => {
                    const damageImg = damage.damage_base64 || 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
                    const damageType = damage.damage_type ? damage.damage_type.replace('_', ' ').toUpperCase() : 'UNKNOWN';
                    const confidence = damage.confidence ? (damage.confidence * 100).toFixed(0) : 'N/A';
                    const frame = damage.frame || 'N/A';
                    
                    return `
                        <div style="border: 2px solid #ff4444; padding: 10px; background: #1a1a1a; border-radius: 4px;">
                            <div style="text-align: center; margin-bottom: 8px;">
                                <div style="color: #ff4444; font-weight: bold; font-size: 11px; margin-bottom: 4px;">⚠ ${damageType}</div>
                                <div style="color: #888; font-size: 10px;">Frame ${frame} • ${confidence}% Confidence</div>
                            </div>
                            ${damage.damage_base64 ? 
                                `<img src="${damageImg}" style="width: 100%; cursor: pointer; border: 1px solid #ff4444; border-radius: 3px;" loading="lazy" onerror="this.style.display='none'" onclick="viewImage('${damageImg.replace(/'/g, "\\'")}', 'Damage: ${damageType} - Frame ${frame}')">` :
                                '<div class="frame-placeholder" style="padding: 40px; font-size: 10px;">NO IMAGE</div>'
                            }
                            <div style="margin-top: 8px; font-size: 10px; color: #888;">
                                ${damage.damage_count ? `${damage.damage_count} regions detected` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
        
        <div class="damage-list" style="max-height: 300px; overflow-y: auto; margin-top: 20px;">
            <div class="damage-list-title">Damage Details List</div>
            ${damageDetections.map(damage => `
                <div class="damage-item">
                    <div>
                        <span class="damage-item-type">${damage.damage_type ? damage.damage_type.replace('_', ' ').toUpperCase() : 'UNKNOWN'}</span>
                        <span style="color: var(--text-secondary); font-size: 10px; margin-left: 8px;">Frame ${damage.frame || 'N/A'}</span>
                    </div>
                    <span class="damage-item-confidence">${damage.confidence ? (damage.confidence * 100).toFixed(0) + '%' : 'N/A'}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function extractWagonNumber(imagePath) {
    // Match wagon numbers in format: wagon_NUMBER_framecount.jpg
    // Supports: 77-474, NR-12345, ER-67890, 08-711, etc.
    const match = imagePath.match(/wagon_([A-Z0-9]{2}-\d{3,6})_/);
    return match ? match[1] : 'UNKNOWN';
}

function viewImage(imageSrc, title) {
    console.log('[viewImage] Opening image:', imageSrc, 'Title:', title);
    const modal = document.getElementById('imageViewerModal');
    const img = document.getElementById('imageViewerImg');
    const titleElement = document.getElementById('imageViewerTitle');
    const comparisonContainer = document.getElementById('comparisonViewContainer');
    
    if (!modal || !img || !titleElement) {
        console.error('[viewImage] Modal elements not found!', {modal, img, titleElement});
        return;
    }
    
    // Show single image, hide comparison
    img.style.display = 'block';
    comparisonContainer.style.display = 'none';
    
    img.src = imageSrc;
    titleElement.textContent = title || 'IMAGE VIEWER';
    modal.classList.add('active');
    console.log('[viewImage] Modal opened successfully');
}

function viewComparison(originalSrc, deblurredSrc, frameNumber) {
    console.log('[viewComparison] Opening comparison:', frameNumber);
    const modal = document.getElementById('imageViewerModal');
    const img = document.getElementById('imageViewerImg');
    const titleElement = document.getElementById('imageViewerTitle');
    const comparisonContainer = document.getElementById('comparisonViewContainer');
    const originalImg = document.getElementById('comparisonOriginal');
    const deblurredImg = document.getElementById('comparisonDeblurred');
    
    if (!modal || !comparisonContainer) {
        console.error('[viewComparison] Modal elements not found!');
        return;
    }
    
    // Show comparison, hide single image
    img.style.display = 'none';
    comparisonContainer.style.display = 'flex';
    
    originalImg.src = originalSrc;
    deblurredImg.src = deblurredSrc;
    titleElement.textContent = `FRAME ${frameNumber} - BEFORE/AFTER COMPARISON`;
    modal.classList.add('active');
    console.log('[viewComparison] Comparison modal opened successfully');
}

// Make viewImage and viewComparison globally accessible
window.viewImage = viewImage;
window.viewComparison = viewComparison;

function openFrameFromAnalysis(frameNumber, frameId, sessionId) {
    // Use the provided session ID from the analysis table
    const sessionIdToUse = sessionId;
    
    if (sessionIdToUse) {
        const modal = document.getElementById('imageViewerModal');
        const img = document.getElementById('imageViewerImg');
        const titleElement = document.getElementById('imageViewerTitle');
        
        // Try to load deblurred frame first
        const deblurredPath = `${API_BASE_URL}/api/session/${sessionIdToUse}/image/deblurred_${String(frameNumber).padStart(6, '0')}.jpg`;
        
        img.src = deblurredPath;
        titleElement.textContent = `${frameId} - DEBLURRED`;
        modal.classList.add('active');
        
        // If deblurred doesn't exist, try original frame
        img.onerror = function() {
            const originalPath = `${API_BASE_URL}/api/session/${sessionIdToUse}/image/frame_${String(frameNumber).padStart(6, '0')}.jpg`;
            img.src = originalPath;
            titleElement.textContent = `${frameId} - ORIGINAL`;
            
            // If neither exists, show error
            img.onerror = function() {
                titleElement.textContent = `${frameId} - NOT FOUND`;
            };
        };
    } else {
        alert('No session ID provided');
    }
}

function closeImageViewer() {
    const modal = document.getElementById('imageViewerModal');
    modal.classList.remove('active');
}

// Make closeImageViewer globally accessible
window.closeImageViewer = closeImageViewer;

let currentSessionIdForDelete = null;

function switchRecordsTab(tab) {
    AppState.currentRecordsTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.records-tab').forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Show/hide content
    if (tab === 'active') {
        document.getElementById('activeRecordsContent').style.display = 'block';
        document.getElementById('deletedRecordsContent').style.display = 'none';
    } else {
        document.getElementById('activeRecordsContent').style.display = 'none';
        document.getElementById('deletedRecordsContent').style.display = 'block';
        // Refresh deleted sessions when switching to this tab
        loadDeletedSessions();
    }
}

function loadDeletedSessions() {
    apiGetDeletedSessions()
        .then(response => {
            if (response.status === 'success') {
                AppState.deletedSessions = response.sessions || [];
                updateDeletedRecordsPage();
                
                // Update badge count
                const badge = document.getElementById('deletedCountBadge');
                if (AppState.deletedSessions.length > 0) {
                    badge.textContent = AppState.deletedSessions.length;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error loading deleted sessions:', error);
        });
}

function updateDeletedRecordsPage() {
    const deletedList = document.getElementById('deletedSessionsList');
    
    if (AppState.deletedSessions.length === 0) {
        deletedList.innerHTML = '<div class="no-sessions">NO RECENTLY DELETED SESSIONS</div>';
        return;
    }
    
    deletedList.innerHTML = '';
    
    // Sort sessions by deletion date (newest first)
    const sortedSessions = [...AppState.deletedSessions].sort((a, b) => {
        const dateA = new Date(a.deleted_at);
        const dateB = new Date(b.deleted_at);
        return dateB - dateA;
    });
    
    sortedSessions.forEach(session => {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = 'session-item deleted-session-item';
        
        const date = new Date(session.date);
        const deletedDate = new Date(session.deleted_at);
        const formattedDate = date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        const formattedDeletedDate = deletedDate.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const daysRemaining = session.days_until_permanent_delete || 0;
        
        sessionDiv.innerHTML = `
            <div class="session-header">
                <div class="session-title">${session.type.toUpperCase()} INSPECTION #${session.id}</div>
                <div class="session-date">${formattedDate}</div>
            </div>
            <div class="session-info">
                <span>OPERATOR: ${session.operator}</span>
                <span>WAGONS: ${session.wagonsDetected}</span>
                <span class="text-success">READABLE: ${session.readable}</span>
                <span class="text-danger">UNREADABLE: ${session.unreadable}</span>
                <span>DURATION: ${session.duration}s</span>
            </div>
            <div class="deleted-info">
                <span class="deleted-time">🗑️ Deleted: ${formattedDeletedDate}</span>
                <span class="auto-delete-warning">⚠️ Auto-deletes in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}</span>
            </div>
        `;
        
        sessionDiv.addEventListener('click', () => openDeletedSessionDetail(session));
        
        deletedList.appendChild(sessionDiv);
    });
}

function openDeletedSessionDetail(session) {
    const modal = document.getElementById('deletedSessionModal');
    const modalTitle = document.getElementById('deletedSessionModalTitle');
    const modalBody = document.getElementById('deletedSessionModalBody');
    
    // Store session ID for restore/permanent delete
    currentSessionIdForDelete = session.id;
    console.log('Deleted session opened, ID stored:', currentSessionIdForDelete);
    
    modalTitle.textContent = `${session.type.toUpperCase()} INSPECTION #${session.id} (DELETED)`;
    
    const date = new Date(session.date);
    const deletedDate = new Date(session.deleted_at);
    const formattedDate = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const formattedDeletedDate = deletedDate.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const daysRemaining = session.days_until_permanent_delete || 0;
    
    modalBody.innerHTML = `
        <div class="deleted-warning-banner">
            <span class="warning-icon">⚠️</span>
            <div>
                <strong>This session was deleted and will be permanently removed in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}.</strong>
                <p>You can restore it now or permanently delete it immediately.</p>
            </div>
        </div>
        
        <div class="analysis-section">
            <h3 class="section-title">SESSION METADATA</h3>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-label">ORIGINAL DATE</div>
                    <div class="summary-value" style="font-size: 16px;">${formattedDate}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">DELETED DATE</div>
                    <div class="summary-value text-danger" style="font-size: 16px;">${formattedDeletedDate}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">OPERATOR</div>
                    <div class="summary-value" style="font-size: 16px;">${session.operator}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">TYPE</div>
                    <div class="summary-value" style="font-size: 16px;">${session.type.toUpperCase()}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">DURATION</div>
                    <div class="summary-value">${session.duration}s</div>
                </div>
            </div>
        </div>
        
        <div class="analysis-section">
            <h3 class="section-title">DETECTION RESULTS</h3>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-label">TOTAL WAGONS</div>
                    <div class="summary-value">${session.wagonsDetected}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">READABLE</div>
                    <div class="summary-value success">${session.readable}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">UNREADABLE</div>
                    <div class="summary-value error">${session.unreadable}</div>
                </div>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

// Make functions globally accessible
window.switchRecordsTab = switchRecordsTab;
window.restoreCurrentSession = restoreCurrentSession;
window.permanentDeleteCurrentSession = permanentDeleteCurrentSession;
window.switchSessionTab = switchSessionTab;

function switchSessionTab(tab, sessionId) {
    // Update tab buttons
    document.querySelectorAll('.session-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.session-tab').classList.add('active');
    
    // Update tab panels
    document.querySelectorAll('.session-tab-panel').forEach(panel => {
        if (panel.dataset.tab === tab) {
            panel.classList.add('active');
        } else {
            panel.classList.remove('active');
        }
    });
}

async function deleteCurrentSession() {
    if (!currentSessionIdForDelete) {
        await showConfirmModal('ERROR', 'No session selected');
        console.error('Delete failed: No session ID');
        return;
    }
    
    const confirmed = await showConfirmModal(
        'MOVE TO RECENTLY DELETED',
        'Are you sure you want to move this session to recently deleted? You can restore it within 7 days.'
    );
    
    if (!confirmed) {
        return;
    }
    
    console.log('Attempting to delete session:', currentSessionIdForDelete);
    
    try {
        const response = await apiDeleteSession(currentSessionIdForDelete);
        console.log('Delete response:', response);
        
        if (response.status === 'success') {
            document.getElementById('sessionModal').classList.remove('active');
            
            // Reload both active and deleted sessions
            await loadSessionsFromBackend();
            await loadDeletedSessions();
            
            // Update the current view
            updateRecordsPage();
        } else {
            await showConfirmModal('DELETE FAILED', response.message || 'Failed to delete session');
            console.error('Delete failed:', response);
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        await showConfirmModal('ERROR', 'Error deleting session: ' + error.message);
    }
}

async function restoreCurrentSession() {
    if (!currentSessionIdForDelete) {
        await showConfirmModal('ERROR', 'No session selected');
        return;
    }
    
    console.log('Attempting to restore session:', currentSessionIdForDelete);
    
    try {
        const response = await apiRestoreSession(currentSessionIdForDelete);
        console.log('Restore response:', response);
        
        if (response.status === 'success') {
            document.getElementById('deletedSessionModal').classList.remove('active');
            
            // Reload both active and deleted sessions
            await loadSessionsFromBackend();
            await loadDeletedSessions();
            
            // Switch to active tab to show the restored session
            switchRecordsTab('active');
            
            // Update the view
            updateRecordsPage();
        } else {
            await showConfirmModal('RESTORE FAILED', response.message || 'Failed to restore session');
            console.error('Restore failed:', response);
        }
    } catch (error) {
        console.error('Error restoring session:', error);
        await showConfirmModal('ERROR', 'Error restoring session: ' + error.message);
    }
}

async function permanentDeleteCurrentSession() {
    if (!currentSessionIdForDelete) {
        await showConfirmModal('ERROR', 'No session selected');
        return;
    }
    
    const confirmed = await showConfirmModal(
        '⚠️ PERMANENT DELETE WARNING',
        'This will PERMANENTLY delete this session. This action cannot be undone. Are you absolutely sure?'
    );
    
    if (!confirmed) {
        return;
    }
    
    console.log('Attempting to permanently delete session:', currentSessionIdForDelete);
    
    try {
        const response = await apiPermanentDeleteSession(currentSessionIdForDelete);
        console.log('Permanent delete response:', response);
        
        if (response.status === 'success') {
            document.getElementById('deletedSessionModal').classList.remove('active');
            
            // Reload deleted sessions
            await loadDeletedSessions();
            
            // Update the deleted records view
            updateDeletedRecordsPage();
        } else {
            await showConfirmModal('DELETE FAILED', response.message || 'Failed to permanently delete session');
            console.error('Permanent delete failed:', response);
        }
    } catch (error) {
        console.error('Error permanently deleting session:', error);
        await showConfirmModal('ERROR', 'Error permanently deleting session: ' + error.message);
    }
}

// ====================================================
// API CONFIGURATION
// ====================================================

const API_BASE_URL = window.location.origin;

// ====================================================
// API CALLS
// ====================================================

async function apiStartLiveVideo(deviceId = 0) {
    const response = await fetch(`${API_BASE_URL}/api/live/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ device_id: deviceId })
    });
    return await response.json();
}

async function apiStopLiveVideo() {
    const response = await fetch(`${API_BASE_URL}/api/live/stop`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function apiStartInspection(type, videoPath = null) {
    const body = {
        type: type,
        operator: AppState.currentUser ? AppState.currentUser.name : 'Unknown'
    };
    
    if (videoPath) {
        body.video_path = videoPath;
    }
    
    // Add motion detection flag for live inspections
    if (type === 'live') {
        body.use_motion_detection = AppState.motionDetection.autoMode;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/inspection/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    return await response.json();
}

async function apiStopInspection(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/inspection/stop`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
    });
    return await response.json();
}

async function apiGetInspectionStatus(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/inspection/status/${sessionId}`);
    return await response.json();
}

async function apiProcessImage(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    const response = await fetch(`${API_BASE_URL}/api/image/process`, {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

async function apiGetSessions() {
    const response = await fetch(`${API_BASE_URL}/api/sessions`);
    return await response.json();
}

async function apiGetSessionDetail(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`);
    return await response.json();
}

async function apiArchiveSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/archive`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function apiDeleteSession(sessionId) {
    console.log('apiDeleteSession called with:', sessionId);
    const url = `${API_BASE_URL}/api/session/${sessionId}`;
    console.log('DELETE URL:', url);
    
    const response = await fetch(url, {
        method: 'DELETE'
    });
    
    const data = await response.json();
    console.log('DELETE response:', data);
    
    return data;
}

async function apiGetDeletedSessions() {
    const response = await fetch(`${API_BASE_URL}/api/deleted-sessions`);
    return await response.json();
}

async function apiRestoreSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/restore`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function apiPermanentDeleteSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/permanent-delete`, {
        method: 'DELETE'
    });
    return await response.json();
}

async function apiGetAnalytics() {
    const response = await fetch(`${API_BASE_URL}/api/analytics`);
    return await response.json();
}

// ====================================================
// DAMAGE DETECTION DISPLAY FUNCTIONS
// ====================================================

function updateDamageDisplay(mode, damageDetections) {
    // mode can be 'live' or 'recorded'
    const prefix = mode === 'live' ? 'live' : 'recorded';
    const statusContainer = document.getElementById(`${prefix}DamageStatus`);
    const detailsContainer = document.getElementById(`${prefix}DamageDetails`);
    
    if (!damageDetections || damageDetections.length === 0) {
        // No damage detected
        statusContainer.innerHTML = `
            <div class="damage-indicator no-damage">
                <span class="damage-icon">✓</span>
                <span class="damage-text">NO DAMAGE DETECTED</span>
            </div>
        `;
        detailsContainer.style.display = 'none';
        return;
    }
    
    // Damage detected - show latest damage
    const latestDamage = damageDetections[damageDetections.length - 1];
    const totalDamages = damageDetections.length;
    
    statusContainer.innerHTML = `
        <div class="damage-indicator has-damage">
            <span class="damage-icon">⚠</span>
            <span class="damage-text">DAMAGE DETECTED - ${latestDamage.damage_type.toUpperCase().replace('_', ' ')}</span>
        </div>
    `;
    
    // Show damage details
    detailsContainer.style.display = 'block';
    
    const uniqueDamageTypes = [...new Set(damageDetections.map(d => d.damage_type))];
    const avgConfidence = (damageDetections.reduce((sum, d) => sum + (d.confidence || 0), 0) / damageDetections.length * 100).toFixed(0);
    
    detailsContainer.innerHTML = `
        <div class="damage-info-grid">
            <div class="damage-info-item">
                <div class="damage-info-label">Total Damages</div>
                <div class="damage-info-value critical">${totalDamages}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Damage Types</div>
                <div class="damage-info-value">${uniqueDamageTypes.length}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Avg Confidence</div>
                <div class="damage-info-value">${avgConfidence}%</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Latest Frame</div>
                <div class="damage-info-value">#${latestDamage.frame}</div>
            </div>
        </div>
        ${latestDamage.damage_base64 ? `
        <div class="damage-image-container">
            <div class="damage-list-title">Latest Damage Image</div>
            <img src="${latestDamage.damage_base64}" style="max-width: 100%; border-radius: 4px; margin-bottom: 12px;" 
                 onclick="viewImage('${latestDamage.damage_base64}', 'Damage Detection')" loading="lazy">
        </div>` : ''}
        <div class="damage-list">
            <div class="damage-list-title">Recent Detections</div>
            ${damageDetections.slice(-5).reverse().map(damage => `
                <div class="damage-item">
                    <div>
                        <span class="damage-item-type">${damage.damage_type.replace('_', ' ')}</span>
                        <span style="color: var(--text-secondary); font-size: 10px; margin-left: 8px;">Frame ${damage.frame}</span>
                    </div>
                    <span class="damage-item-confidence">${(damage.confidence * 100).toFixed(0)}%</span>
                </div>
            `).join('')}
        </div>
    `;
}

function updateDamageDisplayForImage(imageData) {
    const statusContainer = document.getElementById('imageDamageStatus');
    const detailsContainer = document.getElementById('imageDamageDetails');
    
    if (!imageData.damage_detected || imageData.damage_count === 0) {
        // No damage detected
        statusContainer.innerHTML = `
            <div class="damage-indicator no-damage">
                <span class="damage-icon">✓</span>
                <span class="damage-text">NO DAMAGE DETECTED</span>
            </div>
        `;
        detailsContainer.style.display = 'none';
        return;
    }
    
    // Damage detected
    statusContainer.innerHTML = `
        <div class="damage-indicator has-damage">
            <span class="damage-icon">⚠</span>
            <span class="damage-text">DAMAGE DETECTED - ${imageData.damage_type.toUpperCase().replace('_', ' ')}</span>
        </div>
    `;
    
    // Show damage details
    detailsContainer.style.display = 'block';
    
    let damageImageHtml = '';
    if (imageData.damage_base64) {
        damageImageHtml = `
            <div class="damage-preview-grid">
                <div class="damage-preview-item" onclick="viewImage('${imageData.damage_base64}', 'Damage Detection')">
                    <img src="${imageData.damage_base64}" loading="lazy">
                    <div class="damage-preview-label">View Annotated Damage</div>
                </div>
            </div>
        `;
    }
    
    detailsContainer.innerHTML = `
        <div class="damage-info-grid">
            <div class="damage-info-item">
                <div class="damage-info-label">Damage Count</div>
                <div class="damage-info-value critical">${imageData.damage_count}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Damage Type</div>
                <div class="damage-info-value">${imageData.damage_type.replace('_', ' ').toUpperCase()}</div>
            </div>
            <div class="damage-info-item">
                <div class="damage-info-label">Confidence</div>
                <div class="damage-info-value">${(imageData.damage_confidence * 100).toFixed(0)}%</div>
            </div>
        </div>
        ${damageImageHtml}
    `;
}

// ====================================================
// CONSOLE LOGGING FOR DEVELOPMENT
// ====================================================

console.log('%c rAIlwagon Inspection System ', 'background: #ffcc00; color: #000; font-weight: bold; padding: 4px 8px;');
console.log('System initialized and ready for operation.');
console.log('Backend API calls are currently placeholder functions.');
console.log('Replace apiXXX() functions with real fetch() calls for production deployment.');


// ====================================================
// ANALYSIS PAGE - Session Selection & Top Frames
// ====================================================

function loadAnalysisSessions() {
    console.log('Loading analysis sessions...');
    fetch(`${API_BASE_URL}/api/sessions/list`)
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Sessions data:', data);
            if (data.status === 'success' && data.sessions) {
                console.log('Found', data.sessions.length, 'sessions');
                displaySessionSelection(data.sessions);
            } else {
                console.error('Failed to load sessions:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading sessions:', error);
        });
}

function displaySessionSelection(sessions) {
    const grid = document.getElementById('sessionSelectionGrid');
    
    if (!sessions || sessions.length === 0) {
        grid.innerHTML = `
            <div class="no-data" style="grid-column: 1/-1; text-align: center; padding: 40px;">
                NO RECORDED INSPECTIONS FOUND
            </div>
        `;
        return;
    }
    
    grid.innerHTML = sessions.map(session => {
        const timestamp = session.timestamp ? new Date(session.timestamp) : null;
        const formattedTime = timestamp ? timestamp.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }) : 'N/A';
        
        return `
            <div class="session-card" onclick="loadSessionTopFrames('${session.id}')">
                <div class="session-card-header">
                    <div class="session-id">${session.id}</div>
                    <div class="session-type">${session.type.toUpperCase()}</div>
                </div>
                <div class="session-info-row">
                    <span class="session-label">Wagons Detected:</span>
                    <span class="session-value">${session.wagons_detected}</span>
                </div>
                <div class="session-info-row">
                    <span class="session-label">Readable:</span>
                    <span class="session-value" style="color: var(--accent-success)">${session.readable}</span>
                </div>
                <div class="session-info-row">
                    <span class="session-label">Unreadable:</span>
                    <span class="session-value" style="color: var(--accent-danger)">${session.unreadable}</span>
                </div>
                <div class="session-info-row">
                    <span class="session-label">Duration:</span>
                    <span class="session-value">${session.duration}s</span>
                </div>
                <div class="session-timestamp">${formattedTime}</div>
            </div>
        `;
    }).join('');
}

function loadSessionTopFrames(sessionId) {
    // Hide session selection, show top frames section
    document.getElementById('sessionSelectionSection').style.display = 'none';
    document.getElementById('topFramesSection').style.display = 'block';
    
    // Show loading state
    const tableBody = document.getElementById('topFramesTable');
    tableBody.innerHTML = '<tr><td colspan="7" class="loading">LOADING TOP FRAMES...</td></tr>';
    
    // Fetch top frames from backend
    fetch(`${API_BASE_URL}/api/session/${sessionId}/top-frames`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayTopFrames(data);
            } else {
                tableBody.innerHTML = `<tr><td colspan="7" class="error">ERROR: ${data.message}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('Error loading top frames:', error);
            tableBody.innerHTML = '<tr><td colspan="7" class="error">FAILED TO LOAD FRAMES</td></tr>';
        });
}

// Store frames globally for click handlers
let currentTopFrames = [];

function displayTopFrames(data) {
    const { session_id, session_info, top_frames, total_frames } = data;
    
    // Store frames globally
    currentTopFrames = top_frames || [];
    
    // Update session info bar
    const infoBar = document.getElementById('selectedSessionInfo');
    const timestamp = new Date(session_info.timestamp);
    const formattedTime = timestamp.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    infoBar.innerHTML = `
        <div class="info-item">
            <span class="info-label">SESSION:</span>
            <span class="info-value">${session_id}</span>
        </div>
        <div class="info-item">
            <span class="info-label">TYPE:</span>
            <span class="info-value">${session_info.type}</span>
        </div>
        <div class="info-item">
            <span class="info-label">TIMESTAMP:</span>
            <span class="info-value">${formattedTime}</span>
        </div>
        <div class="info-item">
            <span class="info-label">TOTAL FRAMES:</span>
            <span class="info-value">${total_frames}</span>
        </div>
        <div class="info-item">
            <span class="info-label">WAGONS:</span>
            <span class="info-value">${session_info.wagons_detected}</span>
        </div>
    `;
    
    // Populate table
    const tableBody = document.getElementById('topFramesTable');
    
    if (!top_frames || top_frames.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="no-data">NO FRAMES AVAILABLE</td></tr>';
        return;
    }
    
    console.log('========================================');
    console.log('[displayTopFrames] Top frames data received:');
    console.log('[displayTopFrames] Number of frames:', top_frames?.length);
    if (top_frames && top_frames.length > 0) {
        console.log('[displayTopFrames] First frame sample:', top_frames[0]);
        console.log('[displayTopFrames] Wagon numbers in first 3 frames:');
        top_frames.slice(0, 3).forEach((f, i) => {
            console.log(`  Frame ${i}: wagon_number = "${f.wagon_number}"`);
        });
    }
    console.log('========================================');
    
    tableBody.innerHTML = top_frames.map((frame, index) => {
        const improvement = frame.improvement_pct >= 0 ? 
            `<span style="color: var(--accent-success)">+${frame.improvement_pct.toFixed(1)}%</span>` :
            `<span style="color: var(--accent-danger)">${frame.improvement_pct.toFixed(1)}%</span>`;
        
        // Build correct image URL
        const imageUrl = `${API_BASE_URL}/api/${frame.deblurred_path}`;
        
        return `
            <tr>
                <td>${index + 1}</td>
                <td>${frame.frame_id}</td>
                <td>${frame.original_quality.toFixed(2)}</td>
                <td><strong style="color: var(--accent-primary)">${frame.quality_score.toFixed(2)}</strong></td>
                <td>${improvement}</td>
                <td><strong style="color: var(--accent-warning)">${frame.wagon_number || 'N/A'}</strong></td>
                <td>
                    <img src="${imageUrl}" 
                         onclick="openFrameImage(${index})"
                         style="width: 100px; height: 100px; object-fit: cover; cursor: pointer; border: 2px solid var(--accent-primary); border-radius: 4px;" 
                         onerror="this.style.display='none'"
                         loading="lazy" 
                         alt="Frame preview" />
                </td>
            </tr>
        `;
    }).join('');
}

function openFrameImage(index) {
    console.log('========================================');
    console.log('[openFrameImage] Called with index:', index);
    console.log('[openFrameImage] currentTopFrames exists:', !!currentTopFrames);
    console.log('[openFrameImage] currentTopFrames length:', currentTopFrames?.length);
    
    if (currentTopFrames && currentTopFrames[index]) {
        const frame = currentTopFrames[index];
        console.log('[openFrameImage] Frame data:', frame);
        
        const imageUrl = `${API_BASE_URL}/api/${frame.deblurred_path}`;
        const title = `${frame.frame_id} - Quality: ${frame.quality_score.toFixed(2)}`;
        
        console.log('[openFrameImage] Image URL:', imageUrl);
        console.log('[openFrameImage] Title:', title);
        console.log('[openFrameImage] Calling viewImage...');
        
        viewImage(imageUrl, title);
    } else {
        console.error('[openFrameImage] ERROR: Frame not found at index:', index);
        console.error('[openFrameImage] currentTopFrames:', currentTopFrames);
    }
    console.log('========================================');
}

// Make it globally accessible
window.openFrameImage = openFrameImage;

function backToSessionSelection() {
    document.getElementById('sessionSelectionSection').style.display = 'block';
    document.getElementById('topFramesSection').style.display = 'none';
}

function viewFrameDetail(sessionId, frameId, frameNumber) {
    // You can implement a modal or detailed view here
    console.log('View frame detail:', sessionId, frameId, frameNumber);
    // For now, just log it - you can expand this later
}



// ====================================================
// AI CHAT ASSISTANT
// ====================================================

let chatHistory = [];

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    // Process the message
    await processChatMessage(message);
    
    // Remove typing indicator
    removeTypingIndicator(typingId);
}

function askQuickQuestion(question) {
    document.getElementById('chatInput').value = question;
    sendChatMessage();
}

function addChatMessage(message, sender) {
    const container = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    if (sender === 'user') {
        messageDiv.style.cssText = `
            background: linear-gradient(135deg, #2196F3, #1976D2);
            padding: 15px 20px;
            border-radius: 12px;
            max-width: 70%;
            align-self: flex-end;
            margin-left: auto;
        `;
        messageDiv.innerHTML = `
            <div style="color: white; line-height: 1.6;">${message}</div>
        `;
    } else {
        messageDiv.style.cssText = `
            background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,200,100,0.15));
            border-left: 4px solid var(--accent-primary);
            padding: 15px 20px;
            border-radius: 12px;
            max-width: 80%;
            align-self: flex-start;
        `;
        messageDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 20px;">🤖</span>
                <span style="font-weight: 600; color: var(--accent-primary);">AI Assistant</span>
            </div>
            <div style="color: var(--text-primary); line-height: 1.6;">${message}</div>
        `;
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    chatHistory.push({ sender, message, timestamp: new Date().toISOString() });
}

function addTypingIndicator() {
    const container = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    const id = 'typing-' + Date.now();
    typingDiv.id = id;
    typingDiv.style.cssText = `
        background: rgba(0,255,136,0.1);
        padding: 15px 20px;
        border-radius: 12px;
        max-width: 150px;
        align-self: flex-start;
    `;
    typingDiv.innerHTML = `
        <div style="display: flex; gap: 6px; align-items: center;">
            <span style="color: var(--accent-primary);">🤖</span>
            <span style="color: var(--text-secondary); font-size: 14px;">Thinking</span>
            <span class="typing-dots" style="color: var(--accent-primary);">...</span>
        </div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

async function processChatMessage(message) {
    const lowerMessage = message.toLowerCase();
    
    try {
        // Fetch all data we might need
        const [sessionsResp, incidentsResp, statsResp] = await Promise.all([
            fetch('/api/sessions'),
            fetch('/api/incidents'),
            fetch('/api/incidents/stats')
        ]);
        
        const sessionsData = await sessionsResp.json();
        const incidentsData = await incidentsResp.json();
        const statsData = await statsResp.json();
        
        const sessions = sessionsData.sessions || [];
        const incidents = incidentsData.incidents || [];
        const stats = statsData;
        
        // Question routing based on keywords
        if (lowerMessage.includes('how many') && (lowerMessage.includes('wagon') || lowerMessage.includes('inspect'))) {
            handleWagonCountQuestion(sessions, message);
        }
        else if (lowerMessage.includes('damage') || lowerMessage.includes('incident')) {
            if (lowerMessage.includes('structural')) {
                handleStructuralDamageQuestion(incidents);
            } else {
                handleGeneralIncidentsQuestion(incidents);
            }
        }
        else if (lowerMessage.includes('response time') || lowerMessage.includes('statistic')) {
            handleResponseTimeQuestion(stats);
        }
        else if (lowerMessage.includes('today') || lowerMessage.includes('recent')) {
            handleRecentInspectionsQuestion(sessions);
        }
        else if (lowerMessage.includes('critical') || lowerMessage.includes('urgent')) {
            handleCriticalIncidentsQuestion(incidents);
        }
        else if (lowerMessage.includes('show') || lowerMessage.includes('list')) {
            if (lowerMessage.includes('all')) {
                handleShowAllQuestion(sessions, incidents);
            } else {
                handleGeneralShowQuestion(message, sessions, incidents);
            }
        }
        else {
            // General help or unclear question
            handleGeneralQuestion(sessions, incidents, stats);
        }
        
    } catch (error) {
        console.error('Error processing message:', error);
        addChatMessage('Sorry, I encountered an error processing your request. Please try again.', 'ai');
    }
}

function handleWagonCountQuestion(sessions, message) {
    const today = new Date().toDateString();
    const todaySessions = sessions.filter(s => new Date(s.start_time).toDateString() === today);
    
    let totalWagons = 0;
    todaySessions.forEach(session => {
        if (session.results && session.results.wagons_detected) {
            totalWagons += session.results.wagons_detected;
        }
    });
    
    const response = `
        📊 <strong>Wagon Inspection Statistics</strong><br><br>
        Today: <strong>${totalWagons} wagons</strong> inspected across <strong>${todaySessions.length} session${todaySessions.length !== 1 ? 's' : ''}</strong><br><br>
        Total all-time: <strong>${sessions.reduce((sum, s) => sum + (s.results?.wagons_detected || 0), 0)} wagons</strong> across <strong>${sessions.length} sessions</strong>
    `;
    addChatMessage(response, 'ai');
}

function handleStructuralDamageQuestion(incidents) {
    const structural = incidents.filter(i => i.damage_type === 'structural');
    
    if (structural.length === 0) {
        addChatMessage('No structural damage incidents found in the database.', 'ai');
        return;
    }
    
    const critical = structural.filter(i => i.severity === 'critical').length;
    const resolved = structural.filter(i => i.status === 'resolved').length;
    
    let response = `
        🚨 <strong>Structural Damage Incidents</strong><br><br>
        Total: <strong>${structural.length} incidents</strong><br>
        Critical: <strong>${critical}</strong><br>
        Resolved: <strong>${resolved}</strong> (${((resolved/structural.length)*100).toFixed(0)}%)<br><br>
        <strong>Recent structural damage incidents:</strong><br>
    `;
    
    structural.slice(0, 3).forEach(inc => {
        response += `<br>• ${inc.title} - ${inc.status.replace('_', ' ').toUpperCase()} (${new Date(inc.detected_at).toLocaleDateString()})`;
    });
    
    addChatMessage(response, 'ai');
    showIncidentsSection(structural);
}

function handleGeneralIncidentsQuestion(incidents) {
    const total = incidents.length;
    const bySeverity = {
        critical: incidents.filter(i => i.severity === 'critical').length,
        high: incidents.filter(i => i.severity === 'high').length,
        medium: incidents.filter(i => i.severity === 'medium').length,
        low: incidents.filter(i => i.severity === 'low').length
    };
    const resolved = incidents.filter(i => i.status === 'resolved').length;
    
    const response = `
        📋 <strong>Incident Overview</strong><br><br>
        Total Incidents: <strong>${total}</strong><br><br>
        By Severity:<br>
        • Critical: <strong>${bySeverity.critical}</strong><br>
        • High: <strong>${bySeverity.high}</strong><br>
        • Medium: <strong>${bySeverity.medium}</strong><br>
        • Low: <strong>${bySeverity.low}</strong><br><br>
        Resolved: <strong>${resolved}</strong> (${total > 0 ? ((resolved/total)*100).toFixed(0) : 0}%)
    `;
    addChatMessage(response, 'ai');
}

function handleResponseTimeQuestion(stats) {
    if (!stats.success || !stats.response_time_stats) {
        addChatMessage('No response time statistics available yet.', 'ai');
        return;
    }
    
    const timeStats = stats.response_time_stats;
    let response = '⏱️ <strong>Response Time Statistics</strong><br><br>';
    
    Object.entries(timeStats).forEach(([type, data]) => {
        response += `<strong>${type.replace('_', ' ').toUpperCase()}:</strong><br>`;
        response += `• Average: ${data.avg_response_time.toFixed(1)} minutes<br>`;
        response += `• Best: ${data.min_response_time.toFixed(1)} minutes<br>`;
        response += `• Cases: ${data.count}<br><br>`;
    });
    
    addChatMessage(response, 'ai');
}

function handleRecentInspectionsQuestion(sessions) {
    const recent = sessions.slice(0, 5);
    
    let response = '🕐 <strong>Recent Inspections</strong><br><br>';
    
    recent.forEach(session => {
        const date = new Date(session.start_time).toLocaleString();
        const wagons = session.results?.wagons_detected || 0;
        response += `• ${date}: <strong>${wagons} wagon${wagons !== 1 ? 's' : ''}</strong> inspected by ${session.operator}<br>`;
    });
    
    addChatMessage(response, 'ai');
}

function handleCriticalIncidentsQuestion(incidents) {
    const critical = incidents.filter(i => i.severity === 'critical');
    
    if (critical.length === 0) {
        addChatMessage('✅ Great news! No critical incidents found.', 'ai');
        return;
    }
    
    const unresolved = critical.filter(i => i.status !== 'resolved');
    
    let response = `
        ⚠️ <strong>Critical Incidents</strong><br><br>
        Total: <strong>${critical.length}</strong><br>
        Unresolved: <strong>${unresolved.length}</strong><br><br>
    `;
    
    if (unresolved.length > 0) {
        response += '<strong>⚠️ URGENT - Unresolved Critical Incidents:</strong><br>';
        unresolved.forEach(inc => {
            response += `<br>• ${inc.title} (${new Date(inc.detected_at).toLocaleDateString()})`;
        });
    }
    
    addChatMessage(response, 'ai');
    showIncidentsSection(critical);
}

function handleShowAllQuestion(sessions, incidents) {
    const response = `
        📊 <strong>Complete Overview</strong><br><br>
        <strong>Inspections:</strong> ${sessions.length} total sessions<br>
        <strong>Wagons:</strong> ${sessions.reduce((sum, s) => sum + (s.results?.wagons_detected || 0), 0)} total inspected<br>
        <strong>Incidents:</strong> ${incidents.length} total recorded<br><br>
        I've displayed the detailed incident list below. You can click on any incident for more details!
    `;
    addChatMessage(response, 'ai');
    showIncidentsSection(incidents);
}

function handleGeneralShowQuestion(message, sessions, incidents) {
    addChatMessage(`I can show you information about inspections and incidents. Try asking: "Show me all incidents" or "Show me recent inspections"`, 'ai');
}

function handleGeneralQuestion(sessions, incidents, stats) {
    const response = `
        I can help you with:<br><br>
        📊 <strong>Statistics:</strong> "How many wagons were inspected?"<br>
        🚨 <strong>Incidents:</strong> "Show me structural damage incidents"<br>
        ⏱️ <strong>Performance:</strong> "What are the response times?"<br>
        🕐 <strong>Recent Activity:</strong> "Show me today's inspections"<br>
        ⚠️ <strong>Urgent Items:</strong> "Any critical incidents?"<br><br>
        Current overview:<br>
        • ${sessions.length} inspection sessions<br>
        • ${incidents.length} total incidents<br>
        • ${incidents.filter(i => i.status === 'resolved').length} resolved
    `;
    addChatMessage(response, 'ai');
}

function showIncidentsSection(incidentsToShow) {
    const section = document.getElementById('incidentsListSection');
    if (section) {
        section.style.display = 'block';
        displayIncidents(incidentsToShow);
        updateIncidentStats(incidentsToShow);
    }
}

// Auto-load on page show
function onIncidentsPageShown() {
    // Clear chat and show welcome message
    const container = document.getElementById('chatMessages');
    // Welcome message is already in HTML, just scroll to top
    if (container) {
        container.scrollTop = 0;
    }
}


function displayIncidents(incidents) {
    const container = document.getElementById('incidentsList');
    if (!container) return;
    
    if (incidents.length === 0) {
        container.innerHTML = '<div class="no-data">No incidents found</div>';
        return;
    }
    
    container.innerHTML = incidents.map(incident => `
        <div class="incident-card ${incident.severity}" onclick="viewIncidentDetail('${incident.id}')" style="
            background: var(--card-bg);
            border: 2px solid ${getSeverityColor(incident.severity)};
            border-radius: 8px;
            padding: 20px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,255,136,0.2)'" onmouseout="this.style.transform=''; this.style.boxShadow=''">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">${incident.id}</div>
                    <div style="font-size: 18px; font-weight: 600; color: var(--text-primary);">${incident.title}</div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <span style="background: ${getSeverityColor(incident.severity)}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        ${incident.severity.toUpperCase()}
                    </span>
                    <span style="background: ${getStatusColor(incident.status)}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        ${incident.status.replace('_', ' ').toUpperCase()}
                    </span>
                </div>
            </div>
            
            <div style="color: var(--text-secondary); font-size: 13px; margin-bottom: 15px; line-height: 1.6;">
                ${incident.description.substring(0, 150)}${incident.description.length > 150 ? '...' : ''}
            </div>
            
            <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 12px; color: var(--text-secondary);">
                <div>📅 ${new Date(incident.detected_at).toLocaleString()}</div>
                ${incident.wagon_number ? `<div>🚂 Wagon ${incident.wagon_number}</div>` : ''}
                ${incident.confidence ? `<div>🎯 ${(incident.confidence * 100).toFixed(1)}% confidence</div>` : ''}
            </div>
            
            ${incident.recommended_by_ai ? '<div style="margin-top: 12px; padding: 8px 12px; background: rgba(0,255,136,0.1); border-left: 3px solid var(--accent-primary); font-size: 12px; color: var(--accent-primary);">🤖 AI Recommendations Available</div>' : ''}
        </div>
    `).join('');
}

function getSeverityColor(severity) {
    const colors = {
        'critical': '#ff4444',
        'high': '#ff9800',
        'medium': '#ffc107',
        'low': '#4caf50'
    };
    return colors[severity] || '#666';
}

function getStatusColor(status) {
    const colors = {
        'detected': '#2196F3',
        'acknowledged': '#9C27B0',
        'in_progress': '#FF9800',
        'resolved': '#4CAF50',
        'escalated': '#F44336'
    };
    return colors[status] || '#666';
}

function updateIncidentStats(incidents) {
    const critical = incidents.filter(i => i.severity === 'critical').length;
    const high = incidents.filter(i => i.severity === 'high').length;
    const medium = incidents.filter(i => i.severity === 'medium').length;
    const resolved = incidents.filter(i => i.status === 'resolved').length;
    
    document.getElementById('criticalCount').textContent = critical;
    document.getElementById('highCount').textContent = high;
    document.getElementById('mediumCount').textContent = medium;
    document.getElementById('resolvedCount').textContent = resolved;
}

async function viewIncidentDetail(incidentId) {
    try {
        const [incidentResp, recommendResp, similarResp] = await Promise.all([
            fetch(`/api/incident/${incidentId}`),
            fetch(`/api/incident/${incidentId}/recommendations`),
            fetch(`/api/incident/${incidentId}/similar`)
        ]);
        
        const incidentData = await incidentResp.json();
        const recommendData = await recommendResp.json();
        const similarData = await similarResp.json();
        
        if (!incidentData.success) {
            showNotification('Failed to load incident details', 'error');
            return;
        }
        
        const incident = incidentData.incident;
        const recommendations = recommendData.recommended_actions || [];
        const similar = similarData.similar_incidents || [];
        
        const detailHTML = `
            <div style="display: flex; flex-direction: column; gap: 25px;">
                
                <!-- Header -->
                <div>
                    <h2 style="color: var(--text-primary); margin-bottom: 10px;">${incident.title}</h2>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <span style="background: ${getSeverityColor(incident.severity)}; color: white; padding: 6px 14px; border-radius: 4px; font-size: 13px; font-weight: 600;">
                            ${incident.severity.toUpperCase()}
                        </span>
                        <span style="background: ${getStatusColor(incident.status)}; color: white; padding: 6px 14px; border-radius: 4px; font-size: 13px; font-weight: 600;">
                            ${incident.status.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 14px; line-height: 1.6;">
                        ${incident.description}
                    </div>
                </div>
                
                <!-- Details Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">INCIDENT ID</div>
                        <div style="font-size: 14px; color: var(--text-primary); font-weight: 600;">${incident.id}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">DETECTED AT</div>
                        <div style="font-size: 14px; color: var(--text-primary); font-weight: 600;">${new Date(incident.detected_at).toLocaleString()}</div>
                    </div>
                    ${incident.wagon_number ? `
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">WAGON NUMBER</div>
                        <div style="font-size: 14px; color: var(--text-primary); font-weight: 600;">${incident.wagon_number}</div>
                    </div>
                    ` : ''}
                    ${incident.confidence ? `
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">CONFIDENCE</div>
                        <div style="font-size: 14px; color: var(--text-primary); font-weight: 600;">${(incident.confidence * 100).toFixed(1)}%</div>
                    </div>
                    ` : ''}
                </div>
                
                <!-- AI Recommendations -->
                ${recommendations.length > 0 ? `
                <div style="background: linear-gradient(135deg, rgba(0,255,136,0.1) 0%, rgba(0,200,100,0.1) 100%); border: 2px solid var(--accent-primary); border-radius: 8px; padding: 20px;">
                    <h3 style="color: var(--accent-primary); margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                        <span>🤖</span>
                        <span>AI-POWERED RECOMMENDATIONS</span>
                    </h3>
                    <div style="color: var(--text-secondary); font-size: 13px; margin-bottom: 15px;">
                        Based on ${similar.length} similar past incident${similar.length !== 1 ? 's' : ''}
                    </div>
                    <ol style="margin: 0; padding-left: 20px; color: var(--text-primary); font-size: 14px; line-height: 2;">
                        ${recommendations.map(action => `<li>${action}</li>`).join('')}
                    </ol>
                </div>
                ` : ''}
                
                <!-- Similar Incidents -->
                ${similar.length > 0 ? `
                <div>
                    <h3 style="color: var(--text-primary); margin-bottom: 15px;">Similar Past Incidents (${similar.length})</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${similar.slice(0, 3).map(item => `
                            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px; border-left: 3px solid var(--accent-primary);">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <div style="font-size: 14px; font-weight: 600; color: var(--text-primary);">${item.incident.title}</div>
                                    <div style="font-size: 13px; color: var(--accent-primary); font-weight: 600;">${(item.similarity_score * 100).toFixed(0)}% similar</div>
                                </div>
                                <div style="font-size: 12px; color: var(--text-secondary);">
                                    ${item.incident.status === 'resolved' ? '✓ Resolved' : 'Pending'} • 
                                    ${new Date(item.incident.detected_at).toLocaleDateString()}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- Actions -->
                <div style="display: flex; gap: 12px; padding-top: 15px; border-top: 1px solid var(--border-color);">
                    ${incident.status !== 'resolved' ? `
                    <button onclick="updateIncidentStatus('${incident.id}', 'acknowledged')" class="btn-primary" style="padding: 10px 20px;">
                        ACKNOWLEDGE
                    </button>
                    <button onclick="updateIncidentStatus('${incident.id}', 'resolved')" class="btn-success" style="padding: 10px 20px; background: #4CAF50;">
                        MARK RESOLVED
                    </button>
                    ` : ''}
                    <button onclick="closeIncidentModal()" class="btn-secondary" style="padding: 10px 20px; margin-left: auto;">
                        CLOSE
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('incidentDetailContent').innerHTML = detailHTML;
        document.getElementById('incidentModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading incident details:', error);
        showNotification('Error loading incident details', 'error');
    }
}

async function updateIncidentStatus(incidentId, newStatus) {
    try {
        const response = await fetch(`/api/incident/${incidentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: newStatus
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Incident ${newStatus}!`, 'success');
            closeIncidentModal();
            loadIncidents(); // Refresh the list
        } else {
            showNotification('Failed to update incident', 'error');
        }
    } catch (error) {
        console.error('Error updating incident:', error);
        showNotification('Error updating incident', 'error');
    }
}

function closeIncidentModal() {
    document.getElementById('incidentModal').style.display = 'none';
}

// Auto-load incidents when page is shown
function onIncidentsPageShown() {
    loadIncidents();
}

import streamlit as st
import cv2
import numpy as np
import time
from datetime import datetime
import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'))

# Import our organized modules
from utils.detection import HumanDetector
from utils.motion import MotionAnalyzer
from utils.alerts import AlertSystem
from assets.config import APP_CONFIG, CAMERA_CONFIG, DETECTION_CONFIG, UI_CONFIG

# Page configuration
st.set_page_config(
    page_title=APP_CONFIG["name"],
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Frame rotation function - MOVED TO TOP
def rotate_frame(frame, angle):
    """Rotate frame by specified angle"""
    if angle == 0:
        return frame
    
    height, width = frame.shape[:2]
    center = (width // 2, height // 2)
    
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated_frame = cv2.warpAffine(frame, rotation_matrix, (width, height))
    
    return rotated_frame

# Camera initialization with rotation support
def init_camera(camera_type, url=None):
    try:
        if camera_type == "Webcam":
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG["frame_width"])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG["frame_height"])
            return cap, "Webcam Connected"
        else:
            cap = cv2.VideoCapture(url)
            time.sleep(2)
            if cap.isOpened():
                return cap, f"IP Camera Connected: {url}"
            return None, "Failed to connect to IP camera"
    except Exception as e:
        return None, f"Camera error: {str(e)}"

# Load CSS
def load_css():
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# ADD THIS JAVASCRIPT FIX FOR SELECTBOX AND INPUT TEXT COLOR
st.markdown("""
<script>
// Force selectbox text to be white
function fixSelectboxText() {
    const selectboxes = document.querySelectorAll('div[data-baseweb="select"]');
    selectboxes.forEach(selectbox => {
        const valueDiv = selectbox.querySelector('div > div');
        if (valueDiv) {
            valueDiv.style.color = 'white';
            valueDiv.style.fontWeight = '500';
        }
    });
}

// Force input text to be white
function fixInputText() {
    // Fix number inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.style.color = 'white';
        input.style.caretColor = 'white';
    });
    
    // Fix text inputs  
    const textInputs = document.querySelectorAll('input[type="text"]');
    textInputs.forEach(input => {
        input.style.color = 'white';
        input.style.caretColor = 'white';
    });
    
    // Fix all other inputs
    const allInputs = document.querySelectorAll('input');
    allInputs.forEach(input => {
        if (input.type !== 'range' && input.type !== 'checkbox' && input.type !== 'radio') {
            input.style.color = 'white';
            input.style.caretColor = 'white';
        }
    });
}

function fixAllTextColors() {
    fixSelectboxText();
    fixInputText();
}

// Run on page load
document.addEventListener('DOMContentLoaded', fixAllTextColors);

// Run after any Streamlit update
const observer = new MutationObserver(fixAllTextColors);
observer.observe(document.body, { childList: true, subtree: true });

// Also fix when dropdown closes or inputs change
document.addEventListener('click', function(e) {
    setTimeout(fixAllTextColors, 100);
});

// Fix when typing in inputs
document.addEventListener('input', function(e) {
    if (e.target.tagName === 'INPUT') {
        e.target.style.color = 'white';
        e.target.style.caretColor = 'white';
    }
});
</script>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'detector' not in st.session_state:
        st.session_state.detector = HumanDetector()
    if 'motion_analyzer' not in st.session_state:
        st.session_state.motion_analyzer = MotionAnalyzer()
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = AlertSystem()
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
    if 'camera' not in st.session_state:
        st.session_state.camera = None
    if 'frame_count' not in st.session_state:
        st.session_state.frame_count = 0
    if 'selected_camera' not in st.session_state:
        st.session_state.selected_camera = "Webcam"
    if 'frame_rotation' not in st.session_state:
        st.session_state.frame_rotation = 0
    if 'last_frame' not in st.session_state:
        st.session_state.last_frame = None

initialize_session_state()

# Header Section
st.markdown("""
<div class="dashboard-header fade-in">
    <h1 class="header-title">🎥 AI CCTV Surveillance System</h1>
    <p class="header-subtitle">Advanced Human Behavior Monitoring & Threat Detection</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - CLEAN VERSION WITHOUT HEADLINES
with st.sidebar:
    # SYSTEM STATUS CARD (without headline)
    if st.session_state.monitoring:
        status_html = f"""
        <div style="background: rgba(16, 185, 129, 0.15); padding: 1rem; border-radius: 10px; border: 1px solid var(--success); margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div style="width: 8px; height: 8px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite;"></div>
                <div style="font-size: 0.9rem; color: var(--success); font-weight: 600;">ACTIVE MONITORING</div>
            </div>
            <div style="font-size: 0.8rem; color: var(--gray);">
                🎯 Frames: <strong>{st.session_state.frame_count}</strong><br>
                🚨 Alerts: <strong>{len(st.session_state.alert_system.alerts)}</strong><br>
                ⏱️ Uptime: <strong>{st.session_state.frame_count // 10}s</strong>
            </div>
        </div>
        """
    else:
        status_html = """
        <div style="background: rgba(100, 116, 139, 0.15); padding: 1rem; border-radius: 10px; border: 1px solid var(--gray); margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div style="width: 8px; height: 8px; background: var(--gray); border-radius: 50%;"></div>
                <div style="font-size: 0.9rem; color: var(--gray); font-weight: 600;">SYSTEM READY</div>
            </div>
            <div style="font-size: 0.8rem; color: var(--gray);">
                Click START to begin monitoring
            </div>
        </div>
        """
    
    st.markdown(status_html, unsafe_allow_html=True)
    
    # CAMERA CONFIGURATION (without headline)
    camera_type = st.radio(
        "Camera Source",
        ["Webcam", "IP Camera"],
        index=0,
        horizontal=True,
        key="camera_source_radio"
    )
    
    ip_url = None
    if camera_type == "IP Camera":
        ip_url = st.text_input(
            "IP Camera URL",
            value="http://10.191.172.173:8080/video",
            placeholder="http://your-ip:port/video",
            help="Enter your IP camera stream URL",
            key="ip_url_input"
        )
    
    # Camera Orientation with fixed text color
    st.session_state.frame_rotation = st.selectbox(
        "🔄 Camera Orientation",
        options=[0, 90, 180, 270],
        format_func=lambda x: {
            0: "0° - Normal", 
            90: "90° - Right", 
            180: "180° - Upside Down", 
            270: "270° - Left"
        }[x],
        index=3,
        help="Adjust if your camera feed is rotated",
        key="orientation_select"
    )
    
    # DETECTION SETTINGS (without headline)
    st.markdown("<div style='margin-bottom: 0.5rem; font-weight: 600;'>Detection Settings</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        alert_cooldown = st.number_input(
            "Cooldown (s)",
            min_value=10,
            max_value=300,
            value=60,
            step=10,
            help="Seconds between alerts",
            key="cooldown_input"
        )
    
    with col2:
        confidence_threshold = st.number_input(
            "Confidence",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.1,
            help="Detection confidence",
            key="confidence_input"
        )
    
    # Motion sensitivity
    motion_sensitivity = st.slider(
        "Motion Sensitivity",
        min_value=1,
        max_value=10,
        value=5,
        help="Adjust motion detection sensitivity",
        key="sensitivity_slider"
    )
    
    # SYSTEM CONTROLS (without headline)
    st.markdown("<div style='margin: 1.5rem 0 0.5rem 0; font-weight: 600;'>System Controls</div>", unsafe_allow_html=True)
    
    # Control buttons in a nice grid
    control_col1, control_col2 = st.columns(2)
    
    with control_col1:
        start_btn = st.button(
            "▶️ START", 
            use_container_width=True, 
            type="primary",
            disabled=st.session_state.monitoring,
            key="start_button"
        )
    
    with control_col2:
        stop_btn = st.button(
            "⏹️ STOP", 
            use_container_width=True, 
            type="secondary",
            disabled=not st.session_state.monitoring,
            key="stop_button"
        )
    
    # Quick actions
    test_btn = st.button("🔄 TEST CAMERA", use_container_width=True, key="test_button")
    
    # Handle button actions
    if start_btn:
        st.session_state.monitoring = True
        st.session_state.alert_system.alerts = []
        st.session_state.frame_count = 0
        st.session_state.camera = None  # Reset camera to force reinitialization
        st.rerun()
    
    if stop_btn:
        st.session_state.monitoring = False
        if st.session_state.camera:
            st.session_state.camera.release()
            st.session_state.camera = None
        st.rerun()
    
    if test_btn:
        # Test camera connection - ACTUAL TEST
        test_camera_placeholder = st.empty()
        test_camera_placeholder.info("🔍 Testing camera connection...")
        
        try:
            # Get the URL based on camera type
            if camera_type == "IP Camera":
                test_url = ip_url if ip_url else "http://10.191.172.173:8080/video"
            else:
                test_url = 0  # Webcam
            
            # Try to connect to camera
            test_cap = cv2.VideoCapture(test_url)
            time.sleep(2)  # Give time for connection
            
            if test_cap.isOpened():
                # Try to read a frame
                ret, test_frame = test_cap.read()
                
                if ret and test_frame is not None:
                    # SUCCESS: Camera is working
                    test_camera_placeholder.success("✅ Camera test completed! Connection successful.")
                    
                    # Show camera preview in sidebar
                    st.markdown("**📸 Camera Preview:**")
                    
                    # Apply rotation if needed
                    if st.session_state.frame_rotation != 0:
                        test_frame = rotate_frame(test_frame, st.session_state.frame_rotation)
                    
                    # Resize for sidebar display
                    preview_frame = cv2.resize(test_frame, (320, 240))
                    preview_frame_rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
                    
                    # Display the preview
                    st.image(preview_frame_rgb, channels="RGB", use_container_width=True, 
                            caption="Live Camera Preview")
                    
                    # Show camera info
                    st.info(f"📏 Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    
                else:
                    # Camera connected but no frame
                    test_camera_placeholder.error("❌ Camera connected but no video frame received. Check camera permissions.")
            else:
                # Camera not connected
                if camera_type == "IP Camera":
                    test_camera_placeholder.error(f"❌ Cannot connect to IP camera: {test_url}")
                else:
                    test_camera_placeholder.error("❌ Cannot access webcam. Check if it's being used by another app.")
            
            # Always release the test camera
            test_cap.release()
            
        except Exception as e:
            # Error during testing
            test_camera_placeholder.error(f"❌ Camera test failed: {str(e)}")
        
        # Keep the message visible for a while
        time.sleep(3)

# Main Dashboard Layout
col1, col2 = st.columns([2, 1])

with col1:
    # Video Feed Card
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-header">
            <span class="card-icon">📹</span>
            <span class="card-title">Live Camera Feed</span>
            <div style="margin-left: auto; display: flex; gap: 0.5rem; align-items: center;">
                <div style="font-size: 0.8rem; color: var(--gray);">
                    Orientation: {0}° • Sensitivity: {1}/10
                </div>
            </div>
        </div>
    </div>
    """.format(st.session_state.frame_rotation, motion_sensitivity), unsafe_allow_html=True)
    
    # Use a persistent container to prevent reloading
    video_container = st.container()
    
    # Activity Analysis Card
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-header">
            <span class="card-icon">🔍</span>
            <span class="card-title">Real-time Analysis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    activity_container = st.container()

with col2:
    # System Status Card
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-header">
            <span class="card-icon">📊</span>
            <span class="card-title">Live Status</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    status_container = st.container()
    
    # Alerts Card
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-header">
            <span class="card-icon">🚨</span>
            <span class="card-title">Alert History</span>
            <div style="margin-left: auto;">
                <span style="background: var(--danger); color: white; padding: 0.25rem 0.5rem; border-radius: 20px; font-size: 0.8rem;">
                    {0}
                </span>
            </div>
        </div>
    </div>
    """.format(len(st.session_state.alert_system.alerts)), unsafe_allow_html=True)
    
    alerts_container = st.container()

# Stats Grid
st.markdown("""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number" id="frame-count">0</div>
        <div class="stat-label">Frames Processed</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="human-count">0</div>
        <div class="stat-label">Humans Detected</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="alert-count">0</div>
        <div class="stat-label">Total Alerts</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="uptime">0s</div>
        <div class="stat-label">System Uptime</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main monitoring loop - FIXED to prevent reloading
def main_monitoring_loop():
    # Initialize camera if needed
    if st.session_state.camera is None:
        if camera_type == "IP Camera":
            url = ip_url if ip_url else "http://10.191.172.173:8080/video"
        else:
            url = None  # Webcam
        
        st.session_state.camera, status = init_camera(camera_type, url)
    
    cap = st.session_state.camera
    
    if cap is None or not cap.isOpened():
        st.error("❌ Cannot access camera. Please check connection.")
        return
    
    # Read frame
    ret, frame = cap.read()
    
    if not ret:
        st.warning("⚠️ No frame received from camera")
        return
    
    # Apply rotation if needed
    if st.session_state.frame_rotation != 0:
        frame = rotate_frame(frame, st.session_state.frame_rotation)
    
    # Process frame for display
    display_frame = cv2.resize(frame, (640, 480))
    
    # Detect humans
    human_present, human_confidence, human_bboxes = st.session_state.detector.detect_humans(frame)
    
    # Draw bounding boxes
    for (x, y, w, h) in human_bboxes:
        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
        cv2.putText(display_frame, "HUMAN", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Add overlay info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(display_frame, timestamp, (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    info_text = f"Humans: {len(human_bboxes)} | Frame: {st.session_state.frame_count}"
    cv2.putText(display_frame, info_text, (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add orientation indicator
    if st.session_state.frame_rotation != 0:
        rotation_text = f"Rotated: {st.session_state.frame_rotation}°"
        cv2.putText(display_frame, rotation_text, (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Convert for display
    display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    
    # FIX: Update video container without reloading
    with video_container:
        st.image(display_frame_rgb, use_container_width=True, channels="RGB")
    
    # Analyze motion if humans detected
    if human_present and len(human_bboxes) > 0:
        activity, motion_level, confidence = st.session_state.motion_analyzer.analyze_motion(frame, human_bboxes)
        
        # Check for alerts
        if st.session_state.alert_system.should_alert(activity, motion_level, alert_cooldown):
            alert_data = st.session_state.alert_system.add_alert(activity, motion_level, confidence)
    else:
        activity = "no_humans"
        motion_level = 0.0
        confidence = "no_confidence"
    
    # Update activity display - FIXED: Use container to prevent reloading
    with activity_container:
        if activity == "no_humans":
            activity_html = f"""
            <div class="alert-box alert-info">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span>🚫</span>
                    <span>NO HUMANS DETECTED</span>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">
                    Monitoring background activity
                </div>
            </div>
            """
        elif activity == "running":
            activity_html = f"""
            <div class="alert-box alert-danger">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span>🚨</span>
                    <span>RUNNING DETECTED!</span>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                    Motion: {motion_level:.1%} | Confidence: {confidence.upper()}
                </div>
            </div>
            """
        else:
            activity_html = f"""
            <div class="alert-box alert-success">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span>✅</span>
                    <span>{activity.upper()}</span>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                    Motion: {motion_level:.1%} | Confidence: {confidence.upper()}
                </div>
            </div>
            """
        
        st.markdown(activity_html, unsafe_allow_html=True)
    
    # Update status - FIXED: Use container
    with status_container:
        status_html = f"""
        <div style="margin: 1rem 0;">
            <div class="status-indicator {'status-active' if st.session_state.monitoring else 'status-inactive'}" style="margin-bottom: 1rem;">
                {'✅ ACTIVE MONITORING' if st.session_state.monitoring else '❌ SYSTEM READY'}
            </div>
            
            <div style="background: rgba(30, 41, 59, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                    <div style="color: var(--gray);">Camera:</div>
                    <div style="font-weight: 600;">{camera_type}</div>
                    
                    <div style="color: var(--gray);">Humans:</div>
                    <div style="font-weight: 600; color: {'var(--success)' if len(human_bboxes) > 0 else 'var(--gray)'};">
                        {len(human_bboxes)}
                    </div>
                    
                    <div style="color: var(--gray);">Confidence:</div>
                    <div style="font-weight: 600;">{human_confidence:.1%}</div>
                    
                    <div style="color: var(--gray);">Activity:</div>
                    <div style="font-weight: 600; color: {'var(--danger)' if activity == 'running' else 'var(--success)'};">
                        {activity}
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 1rem; font-size: 0.8rem; color: var(--gray); text-align: center;">
                Last update: {datetime.now().strftime("%H:%M:%S")}
            </div>
        </div>
        """
        
        st.markdown(status_html, unsafe_allow_html=True)
    
    # Update alerts - FIXED: Use container
    with alerts_container:
        recent_alerts = st.session_state.alert_system.get_recent_alerts(5)
        if recent_alerts:
            alerts_html = "<div style='max-height: 300px; overflow-y: auto;'>"
            for alert in recent_alerts:
                alert_type = "alert-danger" if alert["type"] == "danger" else "alert-warning"
                time_ago = "Just now"  # You can calculate actual time difference here
                alerts_html += f"""
                <div class="alert-box {alert_type}" style="margin: 0.5rem 0; padding: 0.75rem; font-size: 0.9rem;">
                    <div style="display: flex; justify-content: between; align-items: start;">
                        <div style="flex: 1;">
                            <strong>{alert['activity'].upper()}</strong><br>
                            <span style="font-size: 0.8rem; opacity: 0.8;">
                                Motion: {alert['motion_level']:.1%} • {alert['timestamp']}
                            </span>
                        </div>
                    </div>
                </div>
                """
            alerts_html += "</div>"
        else:
            alerts_html = """
            <div class="alert-box alert-info">
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
                    <div>No alerts yet</div>
                    <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem;">
                        System monitoring normally
                    </div>
                </div>
            </div>
            """
        
        st.markdown(alerts_html, unsafe_allow_html=True)
    
    # Update stats
    st.session_state.frame_count += 1
    
    # Update JavaScript for real-time stats
    st.markdown(f"""
    <script>
        document.getElementById('frame-count').innerText = '{st.session_state.frame_count}';
        document.getElementById('human-count').innerText = '{len(human_bboxes)}';
        document.getElementById('alert-count').innerText = '{len(st.session_state.alert_system.alerts)}';
        document.getElementById('uptime').innerText = '{st.session_state.frame_count // 10}s';
    </script>
    """, unsafe_allow_html=True)

# Run monitoring if active
if st.session_state.monitoring:
    main_monitoring_loop()
    time.sleep(UI_CONFIG["refresh_rate"])
    st.rerun()
else:
    # Welcome screen when not monitoring
    st.markdown("""
    <div class="dashboard-card fade-in">
        <div class="card-header">
            <span class="card-icon">👋</span>
            <span class="card-title">Welcome to AI Surveillance System</span>
        </div>
        <div style="padding: 2rem; text-align: center;">
            <h3 style="color: var(--primary); margin-bottom: 1rem;">Ready to Start Monitoring?</h3>
            <p style="color: var(--gray); margin-bottom: 2rem;">
                Configure your camera settings in the sidebar and click <strong>START</strong> to begin.<br>
                The system will automatically detect humans and monitor their activities in real-time.
            </p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 2rem 0;">
                <div style="background: rgba(37, 99, 235, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--primary);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                    <strong>Smart Detection</strong>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem; color: var(--gray);">
                    Advanced YOLO-based human detection
                    </p>
                </div>
                
                <div style="background: rgba(16, 185, 129, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--success);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                    <strong>Real-time Analysis</strong>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem; color: var(--gray);">
                    Live motion analysis and activity tracking
                    </p>
                </div>
                
                <div style="background: rgba(239, 68, 68, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--danger);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚨</div>
                    <strong>Instant Alerts</strong>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem; color: var(--gray);">
                    Smart alert system for suspicious activities
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

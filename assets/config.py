# Configuration settings
import os
from dotenv import load_dotenv

load_dotenv()

# App Configuration
APP_CONFIG = {
    "name": "AI CCTV Surveillance System",
    "version": "2.0.0",
    "description": "Advanced Human Behavior Monitoring"
}

# Camera Configuration
CAMERA_CONFIG = {
    "webcam_index": 0,
    "ip_camera_timeout": 5,
    "frame_width": 640,
    "frame_height": 480,
    "rotation_angles": [0, 90, 180, 270]
}

# Detection Configuration
DETECTION_CONFIG = {
    "min_human_confidence": 0.5,
    "motion_thresholds": {
        "standing": 0.001,
        "walking": 0.015,
        "running": 0.03
    },
    "alert_cooldown": 60
}

# Alert Configuration
ALERT_CONFIG = {
    "suspicious_activities": ["running", "fighting", "falling"],
    "email_enabled": False,
    "sound_enabled": True
}

# UI Configuration
UI_CONFIG = {
    "theme": "dark",
    "refresh_rate": 0.1,
    "max_alerts_display": 10
}

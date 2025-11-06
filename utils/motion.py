import cv2
import numpy as np

class MotionAnalyzer:
    def __init__(self):
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
        self.motion_history = []
        
    def analyze_motion(self, frame, human_bboxes):
        """Analyze motion in human regions"""
        if frame is None or len(human_bboxes) == 0:
            return "no_humans", 0.0, "no_confidence"
        
        # Apply background subtraction
        fg_mask = self.backSub.apply(frame)
        
        # Create mask for human regions only
        human_mask = np.zeros_like(fg_mask)
        for (x, y, w, h) in human_bboxes:
            human_mask[y:y+h, x:x+w] = fg_mask[y:y+h, x:x+w]
        
        # Calculate motion percentage
        total_human_pixels = np.sum(human_mask > 0)
        total_frame_pixels = frame.shape[0] * frame.shape[1]
        motion_level = total_human_pixels / total_frame_pixels if total_frame_pixels > 0 else 0
        
        # Determine activity
        if motion_level < 0.001:
            activity = "standing"
            confidence = "high"
        elif motion_level < 0.005:
            activity = "talking"
            confidence = "medium"
        elif motion_level < 0.015:
            activity = "walking"
            confidence = "medium"
        elif motion_level < 0.03:
            activity = "walking_fast"
            confidence = "medium"
        elif motion_level < 0.06:
            activity = "possible_running"
            confidence = "low"
        else:
            activity = "running"
            confidence = "high"
        
        return activity, motion_level, confidence

import cv2
import numpy as np
from ultralytics import YOLO

class HumanDetector:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.detection_history = []
        
    def detect_humans(self, frame):
        """Detect humans in frame using YOLO"""
        if frame is None:
            return False, 0, []
        
        try:
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            human_bboxes = []
            max_confidence = 0
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # class 0 is 'person' in COCO dataset
                    if int(box.cls) == 0 and box.conf > 0.5:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        human_bboxes.append([x1, y1, x2-x1, y2-y1])
                        max_confidence = max(max_confidence, float(box.conf))
            
            human_present = len(human_bboxes) > 0
            
            # Store detection history for confidence
            self.detection_history.append(human_present)
            if len(self.detection_history) > 10:
                self.detection_history.pop(0)
            
            presence_confidence = (sum(self.detection_history) / len(self.detection_history) 
                                if self.detection_history else 0)
            
            return human_present, presence_confidence, human_bboxes
            
        except Exception as e:
            print(f"Detection error: {e}")
            return False, 0, []

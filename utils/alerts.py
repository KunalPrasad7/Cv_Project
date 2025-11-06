import time
from datetime import datetime

class AlertSystem:
    def __init__(self):
        self.alerts = []
        self.last_alert_time = 0
        
    def add_alert(self, activity, motion_level, confidence):
        """Add a new alert"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        alert_data = {
            "timestamp": timestamp,
            "activity": activity,
            "motion_level": motion_level,
            "confidence": confidence,
            "type": "danger" if activity == "running" else "warning"
        }
        
        self.alerts.insert(0, alert_data)
        
        # Keep only last 20 alerts
        if len(self.alerts) > 20:
            self.alerts.pop()
            
        return alert_data
    
    def should_alert(self, activity, motion_level, cooldown=60):
        """Check if alert should be triggered"""
        current_time = time.time()
        
        if activity == "running" and motion_level > 0.03:
            if current_time - self.last_alert_time > cooldown:
                self.last_alert_time = current_time
                return True
                
        return False
    
    def get_recent_alerts(self, count=10):
        """Get recent alerts"""
        return self.alerts[:count]

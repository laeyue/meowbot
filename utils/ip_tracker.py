import json
import os
from datetime import datetime, timedelta

class IPTracker:
    def __init__(self):
        self.data_file = 'data/whitelisted_users/ip_tracker.json'
        self.max_requests = 3
        self.cooldown_hours = 24
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """Load tracking data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
        except Exception as e:
            print(f"Error loading IP tracker data: {e}")
            self.data = {}
    
    def save_data(self):
        """Save tracking data to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Error saving IP tracker data: {e}")
    
    def can_whitelist(self, ip, username):
        """Check if an IP can make a whitelist request."""
        now = datetime.now()
        
        # Clean up old entries
        self.cleanup_old_entries(now)
        
        # Check if username is already whitelisted
        if username in self.data.get('whitelisted', []):
            return False, "This username is already whitelisted."
        
        # Get IP data
        ip_data = self.data.get(ip, {
            'requests': [],
            'whitelisted': []
        })
        
        # Check if IP has reached max requests
        recent_requests = [
            req for req in ip_data['requests']
            if now - datetime.fromisoformat(req) < timedelta(hours=self.cooldown_hours)
        ]
        
        if len(recent_requests) >= self.max_requests:
            return False, f"You have reached the maximum number of whitelist requests ({self.max_requests}). Please try again later."
        
        # Add new request
        ip_data['requests'].append(now.isoformat())
        self.data[ip] = ip_data
        self.save_data()
        
        return True, "You can proceed with the whitelist process."
    
    def cleanup_old_entries(self, now):
        """Remove entries older than cooldown period."""
        for ip, data in list(self.data.items()):
            # Clean up old requests
            data['requests'] = [
                req for req in data['requests']
                if now - datetime.fromisoformat(req) < timedelta(hours=self.cooldown_hours)
            ]
            
            # Remove IP if no recent requests
            if not data['requests'] and not data['whitelisted']:
                del self.data[ip]
        
        self.save_data()
    
    def mark_whitelisted(self, ip, username):
        """Mark a username as whitelisted for an IP."""
        if ip not in self.data:
            self.data[ip] = {'requests': [], 'whitelisted': []}
        
        if username not in self.data[ip]['whitelisted']:
            self.data[ip]['whitelisted'].append(username)
            self.save_data() 
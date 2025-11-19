"""
People Counting Module with Line Crossing Detection
"""
import logging
import numpy as np
from collections import defaultdict, deque
from datetime import datetime
from src.utils import line_intersection, get_direction


class PeopleCounter:
    """People counter using line crossing detection"""
    
    def __init__(self, config, line_coords):
        """
        Initialize people counter
        
        Args:
            config: Configuration dictionary
            line_coords: Tuple of (x1, y1, x2, y2) for counting line
        """
        self.logger = logging.getLogger(__name__)
        self.config = config['counting_line']
        
        # Counting line coordinates
        self.line_start = (line_coords[0], line_coords[1])
        self.line_end = (line_coords[2], line_coords[3])
        
        # Direction configuration
        self.in_direction = self.config['in_direction']
        
        # Counters
        self.count_in = 0
        self.count_out = 0
        
        # Track history for each ID
        self.track_history = defaultdict(lambda: deque(maxlen=30))
        
        # Set of IDs that have been counted (to prevent double counting)
        self.counted_ids = set()
        
        # Cooldown for counted IDs (frames)
        self.cooldown = defaultdict(int)
        self.cooldown_frames = 30
        
        # Event log
        self.events = []
        
        self.logger.info(f"Counter initialized - Line: {self.line_start} to {self.line_end}")
        self.logger.info(f"IN direction: {self.in_direction}")
    
    def update(self, tracks, frame_number):
        """
        Update counter with new tracks
        
        Args:
            tracks: Array of tracks [[x1,y1,x2,y2,track_id], ...]
            frame_number: Current frame number
            
        Returns:
            events: List of new counting events
        """
        new_events = []
        
        # Update cooldowns
        for track_id in list(self.cooldown.keys()):
            self.cooldown[track_id] -= 1
            if self.cooldown[track_id] <= 0:
                del self.cooldown[track_id]
                if track_id in self.counted_ids:
                    self.counted_ids.remove(track_id)
        
        # Process each track
        for track in tracks:
            x1, y1, x2, y2, track_id = track
            track_id = int(track_id)
            
            # Calculate centroid
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centroid = (cx, cy)
            
            # Add to history
            self.track_history[track_id].append(centroid)
            
            # Need at least 2 points to check for crossing
            if len(self.track_history[track_id]) < 2:
                continue
            
            # Check if already counted recently
            if track_id in self.counted_ids:
                continue
            
            # Get previous and current position
            prev_pos = self.track_history[track_id][-2]
            curr_pos = self.track_history[track_id][-1]
            
            # Check for line crossing
            if line_intersection(prev_pos, curr_pos, self.line_start, self.line_end):
                # Determine direction
                direction = get_direction(prev_pos, curr_pos, self.line_start, self.line_end)
                
                if direction:
                    # Determine if IN or OUT
                    if direction == self.in_direction:
                        self.count_in += 1
                        event_type = "IN"
                        self.logger.info(f"Person IN - ID: {track_id}, Total IN: {self.count_in}")
                    else:
                        self.count_out += 1
                        event_type = "OUT"
                        self.logger.info(f"Person OUT - ID: {track_id}, Total OUT: {self.count_out}")
                    
                    # Mark as counted
                    self.counted_ids.add(track_id)
                    self.cooldown[track_id] = self.cooldown_frames
                    
                    # Create event
                    event = {
                        'timestamp': datetime.now(),
                        'frame': frame_number,
                        'track_id': track_id,
                        'type': event_type,
                        'position': curr_pos,
                        'count_in': self.count_in,
                        'count_out': self.count_out,
                        'occupancy': self.count_in - self.count_out
                    }
                    
                    self.events.append(event)
                    new_events.append(event)
        
        return new_events
    
    def get_counts(self):
        """Get current counts"""
        return {
            'in': self.count_in,
            'out': self.count_out,
            'occupancy': self.count_in - self.count_out
        }
    
    def get_track_history(self, track_id):
        """Get history for a specific track"""
        return list(self.track_history.get(track_id, []))
    
    def reset(self):
        """Reset all counters"""
        self.count_in = 0
        self.count_out = 0
        self.counted_ids.clear()
        self.cooldown.clear()
        self.track_history.clear()
        self.events.clear()
        self.logger.info("Counter reset")


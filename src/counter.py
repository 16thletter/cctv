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

        # Calculate door region (center 50% of the line to avoid lateral movements at edges)
        # This prevents counting people who move laterally inside the room
        line_length_x = self.line_end[0] - self.line_start[0]
        line_length_y = self.line_end[1] - self.line_start[1]
        margin = 0.25  # 25% margin on each side = center 50%

        self.door_start = (
            self.line_start[0] + line_length_x * margin,
            self.line_start[1] + line_length_y * margin
        )
        self.door_end = (
            self.line_start[0] + line_length_x * (1 - margin),
            self.line_start[1] + line_length_y * (1 - margin)
        )

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
        self.cooldown_frames = 50  # Increased to prevent double counting in groups

        # Pending crossings that need confirmation
        # Format: {track_id: {'type': 'IN'/'OUT', 'direction': 'up'/'down', 'frames': count, 'required_zone': 'inside'/'outside'}}
        self.pending_crossings = defaultdict(lambda: None)
        self.confirmation_frames = 5  # Number of frames to confirm crossing (reduced for groups)

        # Track cancellation counts to prevent infinite oscillation
        self.cancellation_counts = defaultdict(int)
        self.max_cancellations = 3  # Maximum times a pending crossing can be canceled before giving up

        # Recently counted positions to prevent ID swap double counting
        # Format: [(position, timestamp, type), ...]
        self.recent_counts = deque(maxlen=20)  # Keep last 20 counts
        self.position_threshold = 100  # Pixels - if new track is within this distance, might be ID swap

        # Event log
        self.events = []

        self.logger.info(f"Counter initialized - Line: {self.line_start} to {self.line_end}")
        self.logger.info(f"Door region (center 50%): {self.door_start} to {self.door_end}")
        self.logger.info(f"IN direction: {self.in_direction}")

    def _get_zone(self, point):
        """
        Determine which zone a point is in relative to the counting line.
        Returns 'inside' if point is on the inside zone, 'outside' if on outside zone.

        For horizontal line with IN=down:
        - Points above line (smaller Y) = outside
        - Points below line (larger Y) = inside
        """
        # Calculate cross product to determine which side of line
        line_vec = np.array([self.line_end[0] - self.line_start[0],
                            self.line_end[1] - self.line_start[1]])
        point_vec = np.array([point[0] - self.line_start[0],
                             point[1] - self.line_start[1]])
        cross = np.cross(line_vec, point_vec)

        # For horizontal line (most common case)
        if abs(line_vec[0]) > abs(line_vec[1]):
            # Horizontal line: cross < 0 means above, cross > 0 means below
            if self.in_direction == 'down':
                # IN is down, so above=outside, below=inside
                return 'outside' if cross < 0 else 'inside'
            else:  # IN is up
                return 'inside' if cross < 0 else 'outside'
        else:
            # Vertical line: cross < 0 means left, cross > 0 means right
            if self.in_direction == 'right':
                return 'outside' if cross < 0 else 'inside'
            else:  # IN is left
                return 'inside' if cross < 0 else 'outside'

    def _is_near_recent_count(self, position, event_type, frame_number):
        """
        Check if this position is too close to a recently counted person.
        This helps prevent double counting due to ID swaps in groups.

        Args:
            position: (x, y) tuple
            event_type: 'IN' or 'OUT'
            frame_number: Current frame number

        Returns:
            True if position is near a recent count (likely ID swap)
        """
        for recent_pos, recent_frame, recent_type in self.recent_counts:
            # Only check same type (IN or OUT)
            if recent_type != event_type:
                continue

            # Only check recent counts (within last 25 frames = 1 second)
            if frame_number - recent_frame > 25:
                continue

            # Calculate distance
            distance = np.sqrt((position[0] - recent_pos[0])**2 + (position[1] - recent_pos[1])**2)

            if distance < self.position_threshold:
                return True

        return False

    def _is_in_door_region(self, point):
        """
        Check if a point is within the door region (center 50% of counting line).
        This prevents counting lateral movements at the edges of the line.

        Args:
            point: (x, y) tuple - intersection point on the line

        Returns:
            True if point is within door region
        """
        # For horizontal line, check X coordinate
        if abs(self.line_end[0] - self.line_start[0]) > abs(self.line_end[1] - self.line_start[1]):
            return self.door_start[0] <= point[0] <= self.door_end[0]
        # For vertical line, check Y coordinate
        else:
            return self.door_start[1] <= point[1] <= self.door_end[1]

    def _get_overall_movement_direction(self, track_id):
        """
        Analyze the overall movement direction of a track over its history.
        This helps determine if someone is truly going IN or OUT, even if they
        oscillate near the line.

        Returns:
            'IN', 'OUT', or None if unclear
        """
        history = self.track_history[track_id]
        if len(history) < 5:
            return None

        # Look at first and last few positions
        start_positions = list(history)[:3]
        end_positions = list(history)[-3:]

        # Get average zones
        start_zones = [self._get_zone(pos) for pos in start_positions]
        end_zones = [self._get_zone(pos) for pos in end_positions]

        # Count zone occurrences
        start_outside = start_zones.count('outside')
        start_inside = start_zones.count('inside')
        end_outside = end_zones.count('outside')
        end_inside = end_zones.count('inside')

        # Determine overall movement
        # If started mostly outside and ended mostly inside = IN
        if start_outside > start_inside and end_inside > end_outside:
            return 'IN'
        # If started mostly inside and ended mostly outside = OUT
        elif start_inside > start_outside and end_outside > end_inside:
            return 'OUT'

        return None

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
        
        # Get current active track IDs
        active_track_ids = set([int(track[4]) for track in tracks])

        # Update cooldowns
        for track_id in list(self.cooldown.keys()):
            self.cooldown[track_id] -= 1
            if self.cooldown[track_id] <= 0:
                del self.cooldown[track_id]
                if track_id in self.counted_ids:
                    self.counted_ids.remove(track_id)

        # Clean up pending crossings for inactive tracks
        for track_id in list(self.pending_crossings.keys()):
            if track_id not in active_track_ids:
                if self.pending_crossings[track_id] is not None:
                    self.logger.debug(f"Track {track_id} lost, canceling pending crossing")
                    self.pending_crossings[track_id] = None
                if track_id in self.cancellation_counts:
                    del self.cancellation_counts[track_id]

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

            # Get current zone
            current_zone = self._get_zone(centroid)

            # Check if there's a pending crossing for this track
            if self.pending_crossings[track_id] is not None:
                pending = self.pending_crossings[track_id]

                # Check if person is still in the required zone
                if current_zone == pending['required_zone']:
                    # Still in correct zone, increment confirmation frames
                    pending['frames'] += 1
                    self.logger.debug(f"Track {track_id} in {current_zone} zone, pending {pending['type']} confirmation: {pending['frames']}/{self.confirmation_frames}")

                    # Check if we have enough confirmation frames
                    if pending['frames'] >= self.confirmation_frames:
                        # Validate with overall movement direction
                        overall_direction = self._get_overall_movement_direction(track_id)

                        # If overall direction contradicts the pending type, cancel it
                        if overall_direction is not None and overall_direction != pending['type']:
                            self.logger.info(f"Track {track_id} pending {pending['type']} contradicts overall movement {overall_direction}, canceling")
                            self.pending_crossings[track_id] = None
                            self.counted_ids.add(track_id)  # Mark as counted to prevent retry
                            self.cooldown[track_id] = self.cooldown_frames
                        # Check if this position is too close to a recent count (ID swap detection)
                        elif self._is_near_recent_count(centroid, pending['type'], frame_number):
                            self.logger.info(f"Track {track_id} near recent {pending['type']} count - likely ID swap, ignoring")
                            self.pending_crossings[track_id] = None
                            self.counted_ids.add(track_id)  # Mark as counted to prevent retry
                            self.cooldown[track_id] = self.cooldown_frames
                        else:
                            # Confirmed! Count the crossing
                            if pending['type'] == 'IN':
                                self.count_in += 1
                                self.logger.info(f"Person IN (confirmed) - ID: {track_id}, Direction: {pending['direction']}, Total IN: {self.count_in}")
                            else:
                                self.count_out += 1
                                self.logger.info(f"Person OUT (confirmed) - ID: {track_id}, Direction: {pending['direction']}, Total OUT: {self.count_out}")

                            # Mark as counted
                            self.counted_ids.add(track_id)
                            self.cooldown[track_id] = self.cooldown_frames
                            self.cancellation_counts[track_id] = 0  # Reset cancellation count

                            # Record this count position
                            self.recent_counts.append((centroid, frame_number, pending['type']))

                            # Create event
                            event = {
                                'timestamp': datetime.now(),
                                'track_id': track_id,
                                'type': pending['type'],
                                'frame': frame_number,
                                'position': centroid,
                                'count_in': self.count_in,
                                'count_out': self.count_out,
                                'occupancy': self.count_in - self.count_out
                            }
                            new_events.append(event)
                            self.events.append(event)

                            # Clear pending
                            self.pending_crossings[track_id] = None
                else:
                    # Person moved back to wrong zone - cancel the crossing
                    self.cancellation_counts[track_id] += 1
                    self.logger.info(f"Track {track_id} moved back to {current_zone}, canceling {pending['type']} crossing (was in {pending['required_zone']} zone, centroid: {centroid}, cancellations: {self.cancellation_counts[track_id]})")

                    # If canceled too many times, mark as counted to prevent infinite oscillation
                    if self.cancellation_counts[track_id] >= self.max_cancellations:
                        self.logger.info(f"Track {track_id} canceled {self.cancellation_counts[track_id]} times, marking as counted to prevent oscillation")
                        self.counted_ids.add(track_id)
                        self.cooldown[track_id] = self.cooldown_frames
                        self.cancellation_counts[track_id] = 0

                    self.pending_crossings[track_id] = None

                # Skip further processing for this track
                continue

            # Need at least 2 points to check for crossing
            if len(self.track_history[track_id]) < 2:
                continue

            # Check if already counted recently
            if track_id in self.counted_ids:
                continue

            # Get previous and current position
            prev_pos = self.track_history[track_id][-2]
            curr_pos = self.track_history[track_id][-1]

            # Check for line crossing and get intersection point
            intersects, intersection_point = line_intersection(
                prev_pos, curr_pos, self.line_start, self.line_end, return_point=True
            )

            if intersects:
                # Check if crossing is within door region (not lateral movement at edges)
                if not self._is_in_door_region(intersection_point):
                    self.logger.debug(f"Track {track_id} crossed line outside door region at {intersection_point}, ignoring")
                    continue

                # Determine direction
                direction = get_direction(prev_pos, curr_pos, self.line_start, self.line_end)

                if direction:
                    # Get zones for debugging
                    from_zone = self._get_zone(prev_pos)
                    to_zone = self._get_zone(curr_pos)

                    # IMPORTANT: Use zone transition to determine IN/OUT, not just direction!
                    # This handles lateral movements correctly
                    if from_zone == 'outside' and to_zone == 'inside':
                        # Moving from outside to inside = IN
                        event_type = "IN"
                        required_zone = "inside"
                    elif from_zone == 'inside' and to_zone == 'outside':
                        # Moving from inside to outside = OUT
                        event_type = "OUT"
                        required_zone = "outside"
                    else:
                        # Same zone to same zone - shouldn't happen, but ignore
                        self.logger.debug(f"Track {track_id} crossed line but stayed in same zone ({from_zone}->{to_zone}), ignoring")
                        continue

                    # Create pending crossing - needs confirmation
                    self.pending_crossings[track_id] = {
                        'type': event_type,
                        'direction': direction,
                        'frames': 1,  # Start with 1 frame
                        'required_zone': required_zone
                    }
                    self.logger.info(f"Track {track_id} crossed line {direction} ({from_zone}->{to_zone}), pending {event_type} (needs {self.confirmation_frames} frames in {required_zone} zone) - prev_pos: {prev_pos}, curr_pos: {curr_pos}")
        
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
        self.pending_crossings.clear()
        self.cancellation_counts.clear()
        self.events.clear()
        self.logger.info("Counter reset")


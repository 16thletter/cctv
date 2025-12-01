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
    
    def __init__(self, config, line_coords, outside_line_coords=None, inside_line_coords=None):
        """
        Initialize people counter with TWO-LINE zone system

        Args:
            config: Configuration dictionary
            line_coords: Tuple of (x1, y1, x2, y2) for counting line (legacy single-line mode)
            outside_line_coords: Tuple of (x1, y1, x2, y2) for outside zone line (two-line mode)
            inside_line_coords: Tuple of (x1, y1, x2, y2) for inside zone line (two-line mode)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config['counting_line']

        # TWO-LINE ZONE SYSTEM
        # If both outside and inside lines are provided, use two-line mode
        if outside_line_coords is not None and inside_line_coords is not None:
            self.two_line_mode = True
            self.outside_line_start = (outside_line_coords[0], outside_line_coords[1])
            self.outside_line_end = (outside_line_coords[2], outside_line_coords[3])
            self.inside_line_start = (inside_line_coords[0], inside_line_coords[1])
            self.inside_line_end = (inside_line_coords[2], inside_line_coords[3])

            # For compatibility, set line_start/end to outside line
            self.line_start = self.outside_line_start
            self.line_end = self.outside_line_end

            self.logger.info("✓ Using TWO-LINE zone system for enhanced accuracy")
        else:
            # Single line mode (legacy)
            self.two_line_mode = False
            self.line_start = (line_coords[0], line_coords[1])
            self.line_end = (line_coords[2], line_coords[3])

            # Set both lines to same position for compatibility
            self.outside_line_start = self.line_start
            self.outside_line_end = self.line_end
            self.inside_line_start = self.line_start
            self.inside_line_end = self.line_end

            self.logger.info("Using SINGLE-LINE zone system (legacy mode)")

        # Calculate door region (center 50% of the outside line to avoid lateral movements at edges)
        line_length_x = self.outside_line_end[0] - self.outside_line_start[0]
        line_length_y = self.outside_line_end[1] - self.outside_line_start[1]
        margin = 0.25  # 25% margin on each side = center 50%

        self.door_start = (
            self.outside_line_start[0] + line_length_x * margin,
            self.outside_line_start[1] + line_length_y * margin
        )
        self.door_end = (
            self.outside_line_start[0] + line_length_x * (1 - margin),
            self.outside_line_start[1] + line_length_y * (1 - margin)
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

        # Zone-based tracking state machine
        # Format: {track_id: {'state': 'outside'/'transition'/'inside',
        #                     'zone_frames': count,
        #                     'entry_time': frame_number,
        #                     'direction': 'entering'/'exiting',
        #                     'origin_zone': 'outside'/'inside' - where the journey started,
        #                     'zone_history': deque of recent zones for smoothing}}
        self.track_states = defaultdict(lambda: {
            'state': None,
            'zone_frames': 0,
            'entry_time': 0,
            'origin_zone': None,
            'zone_history': deque(maxlen=5)  # Keep last 5 zone detections for smoothing
        })

        # Minimum frames required in each zone before transitioning
        # CRITICAL: Lower values = more responsive but more noise-sensitive
        # For multiple people, we need to be more lenient to avoid missing fast movements
        self.min_zone_frames = 2  # Must be in a zone for 2 frames (0.067s at 30fps)

        # Minimum frames required in transition state before counting
        self.min_transition_frames = 1  # Must be transitioning for 1 frame (very responsive)

        # For zone skipping (fast movement), use even lower threshold
        self.min_zone_frames_for_skip = 1  # Only 1 frame needed for zone skip detection

        # Recently counted positions to prevent ID swap double counting
        # Format: [(position, timestamp, type), ...]
        self.recent_counts = deque(maxlen=20)  # Keep last 20 counts

        # SPATIAL SEPARATION THRESHOLDS for multi-person handling
        # Vertical threshold (Y-axis) - perpendicular to door line
        self.vertical_threshold = 40  # Pixels - distance along crossing direction
        # Horizontal threshold (X-axis) - parallel to door line
        self.horizontal_threshold = 80  # Pixels - distance along the door width
        # This allows multiple people to cross simultaneously at different positions along the door

        # Event log
        self.events = []

        self.logger.info(f"Counter initialized - Line: {self.line_start} to {self.line_end}")
        self.logger.info(f"Door region (center 50%): {self.door_start} to {self.door_end}")
        self.logger.info(f"IN direction: {self.in_direction}")
        self.logger.info(f"Using ZONE-BASED tracking: min_zone_frames={self.min_zone_frames}, min_transition_frames={self.min_transition_frames}")
        self.logger.info(f"SPATIAL SEPARATION enabled: vertical_threshold={self.vertical_threshold}px, horizontal_threshold={self.horizontal_threshold}px")

        # Log zone interpretation
        if self.in_direction == 'down':
            self.logger.info(f"Zone mapping: ABOVE line (y < {self.line_start[1]}) = OUTSIDE, BELOW line (y > {self.line_start[1]}) = INSIDE")
        elif self.in_direction == 'up':
            self.logger.info(f"Zone mapping: ABOVE line (y < {self.line_start[1]}) = INSIDE, BELOW line (y > {self.line_start[1]}) = OUTSIDE")

    def _get_zone(self, point):
        """
        Determine which zone a point is in using TWO-LINE system.

        Returns:
            'outside' - person is in outside zone (beyond outside line)
            'inside' - person is in inside zone (beyond inside line)
            'transition' - person is between the two lines (in transition zone)

        For horizontal lines with IN=down:
        - Above outside line = 'outside'
        - Between lines = 'transition'
        - Below inside line = 'inside'
        """
        if self.two_line_mode:
            # TWO-LINE MODE: More accurate zone detection
            # For horizontal lines (most common case)
            if abs(self.outside_line_end[0] - self.outside_line_start[0]) > abs(self.outside_line_end[1] - self.outside_line_start[1]):
                # Horizontal lines - use Y coordinate
                outside_y = self.outside_line_start[1]
                inside_y = self.inside_line_start[1]
                point_y = point[1]

                if self.in_direction == 'down':
                    # IN is down, so: outside (top) → transition → inside (bottom)
                    if point_y < outside_y:
                        return 'outside'
                    elif point_y > inside_y:
                        return 'inside'
                    else:
                        return 'transition'
                else:  # IN is up
                    # IN is up, so: inside (top) → transition → outside (bottom)
                    if point_y < inside_y:
                        return 'inside'
                    elif point_y > outside_y:
                        return 'outside'
                    else:
                        return 'transition'
            else:
                # Vertical lines - use X coordinate
                outside_x = self.outside_line_start[0]
                inside_x = self.inside_line_start[0]
                point_x = point[0]

                if self.in_direction == 'right':
                    if point_x < outside_x:
                        return 'outside'
                    elif point_x > inside_x:
                        return 'inside'
                    else:
                        return 'transition'
                else:  # IN is left
                    if point_x < inside_x:
                        return 'inside'
                    elif point_x > outside_x:
                        return 'outside'
                    else:
                        return 'transition'
        else:
            # SINGLE-LINE MODE (legacy): Use buffer zones
            # For horizontal line (most common case)
            if abs(self.line_end[0] - self.line_start[0]) > abs(self.line_end[1] - self.line_start[1]):
                # Horizontal line - use Y coordinate
                line_y = self.line_start[1]
                point_y = point[1]

                # Add buffer zone (30 pixels) to prevent oscillation
                buffer = 30

                if self.in_direction == 'down':
                    # IN is down, so above=outside, below=inside
                    if point_y < line_y - buffer:
                        return 'outside'
                    elif point_y > line_y + buffer:
                        return 'inside'
                    else:
                        # In buffer zone - treat as transition
                        return 'transition'
                else:  # IN is up
                    if point_y < line_y - buffer:
                        return 'inside'
                    elif point_y > line_y + buffer:
                        return 'outside'
                    else:
                        return 'transition'
            else:
                # Vertical line - use X coordinate
                line_x = self.line_start[0]
                point_x = point[0]

                buffer = 30

                if self.in_direction == 'right':
                    if point_x < line_x - buffer:
                        return 'outside'
                    elif point_x > line_x + buffer:
                        return 'inside'
                    else:
                        return 'transition'
                else:  # IN is left
                    if point_x < line_x - buffer:
                        return 'inside'
                    elif point_x > line_x + buffer:
                        return 'outside'
                    else:
                        return 'transition'

    def _get_smoothed_zone(self, track_id, raw_zone):
        """
        Get smoothed zone using recent history to reduce oscillation.
        Uses majority voting from recent zone detections.

        CRITICAL for multiple people: Reduces false transitions when people
        are near zone boundaries or when detection is noisy.

        Args:
            track_id: Track ID
            raw_zone: Current detected zone

        Returns:
            Smoothed zone ('outside', 'transition', or 'inside')
        """
        state_info = self.track_states[track_id]
        zone_history = state_info['zone_history']

        # Add current zone to history
        zone_history.append(raw_zone)

        # If we don't have enough history, use raw zone
        if len(zone_history) < 3:
            return raw_zone

        # Use majority voting from recent history (last 3-5 frames)
        from collections import Counter
        zone_counts = Counter(zone_history)
        most_common_zone, count = zone_counts.most_common(1)[0]

        # Only use smoothed zone if it has clear majority (at least 60%)
        if count >= len(zone_history) * 0.6:
            return most_common_zone
        else:
            # No clear majority, use current zone
            return raw_zone

    def _is_near_recent_count(self, position, event_type, frame_number):
        """
        Check if this position is too close to a recently counted person using SPATIAL SEPARATION.
        This helps prevent double counting due to ID swaps while allowing simultaneous crossings.

        SPATIAL SEPARATION LOGIC:
        - Checks both VERTICAL (Y) and HORIZONTAL (X) distances separately
        - For horizontal door lines: Y = crossing direction, X = position along door
        - Allows multiple people to cross simultaneously at different horizontal positions
        - Only blocks if BOTH vertical AND horizontal distances are too close

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

            # Only check VERY recent counts (within last 10 frames = 0.33 seconds)
            # REDUCED from 25 frames to allow multiple people in quick succession
            if frame_number - recent_frame > 10:
                continue

            # SPATIAL SEPARATION: Calculate vertical and horizontal distances separately
            # For horizontal lines (most common):
            # - vertical_distance (Y) = distance in crossing direction (perpendicular to line)
            # - horizontal_distance (X) = distance along the door (parallel to line)

            vertical_distance = abs(position[1] - recent_pos[1])  # Y-axis distance
            horizontal_distance = abs(position[0] - recent_pos[0])  # X-axis distance

            # Check if this is likely an ID swap (close in BOTH dimensions)
            # If people are far apart horizontally, they're different people even if close vertically
            is_too_close_vertically = vertical_distance < self.vertical_threshold
            is_too_close_horizontally = horizontal_distance < self.horizontal_threshold

            if is_too_close_vertically and is_too_close_horizontally:
                # Both distances are small - likely ID swap
                self.logger.debug(
                    f"ID swap detected: position={position}, recent={recent_pos}, "
                    f"vertical_dist={vertical_distance:.1f}px (thresh={self.vertical_threshold}), "
                    f"horizontal_dist={horizontal_distance:.1f}px (thresh={self.horizontal_threshold})"
                )
                return True
            elif is_too_close_vertically and not is_too_close_horizontally:
                # Close vertically but far horizontally - different people crossing simultaneously
                self.logger.debug(
                    f"Simultaneous crossing allowed: position={position}, recent={recent_pos}, "
                    f"vertical_dist={vertical_distance:.1f}px, horizontal_dist={horizontal_distance:.1f}px "
                    f"(far apart horizontally - different person)"
                )
                # Continue checking other recent counts

        return False

    def _validate_movement_direction(self, track_id, expected_direction):
        """
        Validate that the track's movement matches the expected direction.
        Uses trajectory history to calculate actual movement direction.

        Args:
            track_id: Track ID
            expected_direction: 'IN' or 'OUT'

        Returns:
            True if movement direction is valid, False otherwise
        """
        history = self.track_history[track_id]

        # Need at least 5 points for reliable direction calculation
        if len(history) < 5:
            return True  # Not enough data, allow the count

        # Get first and last few positions
        start_positions = list(history)[:3]
        end_positions = list(history)[-3:]

        # Calculate average start and end positions
        start_y = sum(pos[1] for pos in start_positions) / len(start_positions)
        end_y = sum(pos[1] for pos in end_positions) / len(end_positions)

        # Calculate movement in Y direction
        y_movement = end_y - start_y

        # Determine actual direction based on movement
        # For horizontal lines: positive Y = moving down, negative Y = moving up
        if self.in_direction == 'down':
            # IN = moving down (positive Y), OUT = moving up (negative Y)
            if expected_direction == 'IN':
                is_valid = y_movement > 5  # Moved down at least 5 pixels
            else:  # OUT
                is_valid = y_movement < -5  # Moved up at least 5 pixels
        else:  # in_direction == 'up'
            # IN = moving up (negative Y), OUT = moving down (positive Y)
            if expected_direction == 'IN':
                is_valid = y_movement < -5  # Moved up at least 5 pixels
            else:  # OUT
                is_valid = y_movement > 5  # Moved down at least 5 pixels

        if not is_valid:
            self.logger.info(
                f"Track {track_id}: Movement direction mismatch! "
                f"Expected={expected_direction}, y_movement={y_movement:.1f}px, "
                f"in_direction={self.in_direction}"
            )

        return is_valid

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

    def _calculate_perpendicular_distance(self, point, line_start, line_end):
        """
        Calculate the perpendicular distance from a point to a line.

        Args:
            point: (x, y) tuple
            line_start: (x, y) tuple
            line_end: (x, y) tuple

        Returns:
            Distance in pixels
        """
        # Convert to numpy arrays
        p = np.array(point)
        l1 = np.array(line_start)
        l2 = np.array(line_end)

        # Calculate perpendicular distance using cross product formula
        # distance = |cross(line_vec, point_vec)| / |line_vec|
        line_vec = l2 - l1
        point_vec = p - l1

        cross = np.cross(line_vec, point_vec)
        line_length = np.linalg.norm(line_vec)

        if line_length < 1:
            return 0

        distance = abs(cross) / line_length
        return distance

    def _is_perpendicular_movement(self, track_id, min_perpendicular_ratio=0.5, min_perpendicular_distance=50):
        """
        Check if the track's movement is perpendicular to the counting line.
        This prevents counting people who are moving parallel to the line (lateral movement).

        Args:
            track_id: Track ID to check
            min_perpendicular_ratio: Minimum ratio of perpendicular to parallel movement (default 0.5)
            min_perpendicular_distance: Minimum distance traveled perpendicular to line in pixels (default 50)

        Returns:
            True if movement is sufficiently perpendicular to the line
        """
        history = self.track_history[track_id]
        if len(history) < 5:
            return True  # Not enough data, allow it

        # Get first and last positions
        start_pos = np.array(history[0])
        end_pos = np.array(history[-1])

        # Calculate movement vector
        movement_vec = end_pos - start_pos
        movement_magnitude = np.linalg.norm(movement_vec)

        if movement_magnitude < 10:  # Very small movement, ignore
            return False

        # Calculate perpendicular distances from line for start and end positions
        start_dist = self._calculate_perpendicular_distance(start_pos, self.line_start, self.line_end)
        end_dist = self._calculate_perpendicular_distance(end_pos, self.line_start, self.line_end)

        # Calculate how much they moved perpendicular to the line
        perpendicular_distance_traveled = abs(end_dist - start_dist)

        # Check if they traveled enough perpendicular distance
        if perpendicular_distance_traveled < min_perpendicular_distance:
            self.logger.debug(f"Track {track_id} only traveled {perpendicular_distance_traveled:.1f}px perpendicular to line (min: {min_perpendicular_distance})")
            return False

        # Calculate line vector (normalized)
        line_vec = np.array([self.line_end[0] - self.line_start[0],
                            self.line_end[1] - self.line_start[1]])
        line_magnitude = np.linalg.norm(line_vec)

        if line_magnitude < 1:
            return True

        line_vec_normalized = line_vec / line_magnitude
        movement_vec_normalized = movement_vec / movement_magnitude

        # Calculate dot product to get parallel component
        # dot product = cos(angle) * magnitudes
        # If angle is 0° (parallel), dot = 1
        # If angle is 90° (perpendicular), dot = 0
        dot_product = abs(np.dot(line_vec_normalized, movement_vec_normalized))

        # Calculate perpendicular component
        # If dot_product is close to 1, movement is parallel (bad)
        # If dot_product is close to 0, movement is perpendicular (good)
        perpendicular_component = 1 - dot_product

        # Check if movement is sufficiently perpendicular
        is_perpendicular = perpendicular_component >= min_perpendicular_ratio

        self.logger.debug(f"Track {track_id} movement analysis: parallel={dot_product:.2f}, perpendicular={perpendicular_component:.2f}, perp_dist={perpendicular_distance_traveled:.1f}px, is_perpendicular={is_perpendicular}")

        return is_perpendicular

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

    def _update_zone_state(self, track_id, raw_zone, centroid, frame_number):
        """
        Update the zone-based state machine for a track using TWO-LINE system.

        State transitions (TWO-LINE MODE):
        - outside → transition → inside (entering)
        - inside → transition → outside (exiting)

        The 'transition' zone is the physical space between the two lines.

        Returns:
            event: {'type': 'IN'/'OUT', ...} if a count should be made, None otherwise
        """
        # Use smoothed zone to reduce oscillation (CRITICAL for multiple people)
        current_zone = self._get_smoothed_zone(track_id, raw_zone)

        state_info = self.track_states[track_id]
        current_state = state_info['state']
        zone_frames = state_info['zone_frames']

        # Check if centroid is in door region (center 50% of line)
        in_door_region = self._is_in_door_region(centroid)

        # Initialize state if this is a new track
        if current_state is None:
            # Initialize in any zone (including transition)
            state_info['state'] = current_zone
            state_info['zone_frames'] = 1
            state_info['entry_time'] = frame_number

            # If starting in transition, try to infer direction from next frames
            if current_zone == 'transition':
                self.logger.debug(f"Track {track_id} initialized in TRANSITION zone - will infer direction")
            else:
                self.logger.debug(f"Track {track_id} initialized in {current_zone} zone")
            return None

        # Same zone - increment counter
        if current_zone == current_state:
            state_info['zone_frames'] += 1
            return None

        # Zone changed - handle transitions

        # Handle tracks that started in transition zone
        if current_state == 'transition' and state_info.get('direction') is None:
            # Track started in transition, now moved to a clear zone
            if current_zone == 'inside':
                # Moved to inside - was entering
                state_info['state'] = 'transition'
                state_info['direction'] = 'entering'
                state_info['zone_frames'] = 1
                self.logger.info(f"🟢 Track {track_id}: transition (unknown) → inferred ENTERING direction")
                print(f"🟢 Track {track_id} inferred ENTERING (transition → inside)")
                return None
            elif current_zone == 'outside':
                # Moved to outside - was exiting
                state_info['state'] = 'transition'
                state_info['direction'] = 'exiting'
                state_info['zone_frames'] = 1
                self.logger.info(f"🔴 Track {track_id}: transition (unknown) → inferred EXITING direction")
                print(f"🔴 Track {track_id} inferred EXITING (transition → outside)")
                return None

        # ENTERING: outside → transition → inside
        if current_state == 'outside' and current_zone == 'transition':
            # Entering transition zone from outside
            if zone_frames >= self.min_zone_frames:
                state_info['state'] = 'transition'
                state_info['zone_frames'] = 1
                state_info['direction'] = 'entering'
                state_info['origin_zone'] = 'outside'  # Mark where journey started
                self.logger.info(f"🟢 Track {track_id}: outside ({zone_frames}f) → transition (entering) [origin=outside]")
                print(f"🟢 Track {track_id} started ENTERING (outside → transition) - must reach inside to count")
            else:
                self.logger.debug(f"Track {track_id}: unstable outside ({zone_frames}f < {self.min_zone_frames}), waiting")
                state_info['zone_frames'] += 1
            return None

        elif current_state == 'transition' and current_zone == 'inside':
            # Completed entry: transition → inside
            origin = state_info.get('origin_zone')
            direction = state_info.get('direction')

            # ONLY count if direction is 'entering' AND origin was 'outside'
            if direction == 'entering' and origin == 'outside':
                # Validate movement direction using trajectory
                if not self._validate_movement_direction(track_id, 'IN'):
                    self.logger.info(f"Track {track_id} movement direction invalid for IN - ignoring")
                    state_info['state'] = 'inside'
                    state_info['zone_frames'] = 1
                    state_info['origin_zone'] = None
                    self.counted_ids.add(track_id)
                    return None

                # Check for ID swap using spatial separation
                if self._is_near_recent_count(centroid, 'IN', frame_number):
                    self.logger.info(f"Track {track_id} near recent IN count - likely ID swap, ignoring")
                    state_info['state'] = 'inside'
                    state_info['zone_frames'] = 1
                    state_info['origin_zone'] = None
                    self.counted_ids.add(track_id)
                    return None

                # Count as IN - complete journey from outside → transition → inside
                self.count_in += 1
                self.logger.info(f"🟢 ✓ Person IN - ID: {track_id}, Total IN: {self.count_in} 🟢")
                print(f"\n{'='*60}")
                print(f"🟢 IN COUNT INCREMENTED! Track {track_id}")
                print(f"🟢 Journey: outside → transition → inside ✓")
                print(f"🟢 Total IN: {self.count_in}")
                print(f"🟢 Total OUT: {self.count_out}")
                print(f"🟢 Occupancy: {self.count_in - self.count_out}")
                print(f"{'='*60}\n")

                # Mark as counted
                self.counted_ids.add(track_id)
                self.recent_counts.append((centroid, frame_number, 'IN'))

                # Update state
                state_info['state'] = 'inside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None  # Clear origin

                # Create event
                event = {
                    'timestamp': datetime.now(),
                    'track_id': track_id,
                    'type': 'IN',
                    'frame': frame_number,
                    'position': centroid,
                    'count_in': self.count_in,
                    'count_out': self.count_out,
                    'occupancy': self.count_in - self.count_out
                }
                return event
            else:
                # Either wrong direction or wrong origin - don't count
                if direction != 'entering':
                    self.logger.info(f"❌ Track {track_id}: transition→inside but direction={direction}, NOT counting")
                elif origin != 'outside':
                    self.logger.info(f"❌ Track {track_id}: transition→inside but origin={origin} (not outside), NOT counting")
                    print(f"❌ Track {track_id} moved inside→transition→inside (hovering), NOT counted")

                state_info['state'] = 'inside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None
                return None

        # EXITING: inside → transition → outside
        elif current_state == 'inside' and current_zone == 'transition':
            # Entering transition zone from inside
            self.logger.debug(f"Track {track_id}: inside→transition, zone_frames={zone_frames}, min={self.min_zone_frames}, centroid={centroid}")

            # Be more lenient for exits - don't require door region check
            if zone_frames >= self.min_zone_frames:
                state_info['state'] = 'transition'
                state_info['zone_frames'] = 1
                state_info['direction'] = 'exiting'
                state_info['origin_zone'] = 'inside'  # Mark where journey started
                self.logger.info(f"🔴 Track {track_id}: inside ({zone_frames}f) → transition (exiting) [origin=inside], centroid={centroid}")
                print(f"🔴 Track {track_id} started EXITING (inside → transition) - must reach outside to count")
            else:
                self.logger.debug(f"Track {track_id}: unstable inside ({zone_frames}f < {self.min_zone_frames}), waiting")
                state_info['zone_frames'] += 1
            return None

        elif current_state == 'transition' and current_zone == 'outside':
            # Completed exit: transition → outside
            origin = state_info.get('origin_zone')
            direction = state_info.get('direction')
            self.logger.debug(f"Track {track_id}: transition→outside, direction={direction}, origin={origin}")

            # ONLY count if direction is 'exiting' AND origin was 'inside'
            if direction == 'exiting' and origin == 'inside':
                # Validate movement direction using trajectory
                if not self._validate_movement_direction(track_id, 'OUT'):
                    self.logger.info(f"Track {track_id} movement direction invalid for OUT - ignoring")
                    state_info['state'] = 'outside'
                    state_info['zone_frames'] = 1
                    state_info['origin_zone'] = None
                    self.counted_ids.add(track_id)
                    return None

                # Check for ID swap using spatial separation
                if self._is_near_recent_count(centroid, 'OUT', frame_number):
                    self.logger.info(f"Track {track_id} near recent OUT count - likely ID swap, ignoring")
                    state_info['state'] = 'outside'
                    state_info['zone_frames'] = 1
                    state_info['origin_zone'] = None
                    self.counted_ids.add(track_id)
                    return None

                # Count as OUT - complete journey from inside → transition → outside
                self.count_out += 1
                self.logger.info(f"🔴 ✓ Person OUT - ID: {track_id}, Total OUT: {self.count_out} 🔴")
                print(f"\n{'='*60}")
                print(f"🔴 OUT COUNT INCREMENTED! Track {track_id}")
                print(f"🔴 Journey: inside → transition → outside ✓")
                print(f"🔴 Total OUT: {self.count_out}")
                print(f"🔴 Total IN: {self.count_in}")
                print(f"🔴 Occupancy: {self.count_in - self.count_out}")
                print(f"{'='*60}\n")

                # Mark as counted
                self.counted_ids.add(track_id)
                self.recent_counts.append((centroid, frame_number, 'OUT'))

                # Update state
                state_info['state'] = 'outside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None  # Clear origin

                # Create event
                event = {
                    'timestamp': datetime.now(),
                    'track_id': track_id,
                    'type': 'OUT',
                    'frame': frame_number,
                    'position': centroid,
                    'count_in': self.count_in,
                    'count_out': self.count_out,
                    'occupancy': self.count_in - self.count_out
                }
                return event
            else:
                # Either wrong direction or wrong origin - don't count
                if direction != 'exiting':
                    self.logger.info(f"❌ Track {track_id}: transition→outside but direction={direction}, NOT counting")
                elif origin != 'inside':
                    self.logger.info(f"❌ Track {track_id}: transition→outside but origin={origin} (not inside), NOT counting")
                    print(f"❌ Track {track_id} moved outside→transition→outside (hovering), NOT counted")

                state_info['state'] = 'outside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None
                return None

        # Handle backward movement (person changed their mind)
        elif current_state == 'transition' and current_zone == 'inside':
            if state_info.get('direction') == 'exiting':
                # Person was exiting but moved back inside - cancel the exit
                self.logger.info(f"❌ Track {track_id}: transition (exiting) → inside (moved back, EXIT CANCELED)")
                print(f"❌ Track {track_id} was exiting but moved back inside - EXIT CANCELED")
                state_info['state'] = 'inside'
                state_info['zone_frames'] = 1
                state_info['direction'] = None  # Clear direction
                state_info['origin_zone'] = None  # Clear origin
                return None
            else:
                # This is handled above in the entering logic
                self.logger.debug(f"Track {track_id}: transition→inside (unexpected state)")
                state_info['state'] = 'inside'
                state_info['zone_frames'] = 1
                return None

        # Handle backward movement for exiting (transition → outside when was entering)
        elif current_state == 'transition' and current_zone == 'outside':
            if state_info.get('direction') == 'entering':
                # Person was entering but moved back outside - cancel the entry
                self.logger.info(f"❌ Track {track_id}: transition (entering) → outside (moved back, ENTRY CANCELED)")
                print(f"❌ Track {track_id} was entering but moved back outside - ENTRY CANCELED")
                state_info['state'] = 'outside'
                state_info['zone_frames'] = 1
                state_info['direction'] = None  # Clear direction
                state_info['origin_zone'] = None  # Clear origin
                return None

        # ZONE SKIPPING: Handle missed frames (person jumped zones)
        # This is CRITICAL for not losing counts when frames are dropped

        # Case 1: outside → inside (skipped transition) = ENTERING
        elif current_state == 'outside' and current_zone == 'inside':
            # Person jumped from outside to inside (missed transition zone)
            # This happens when frames are dropped or person moves very fast
            # Use lower threshold for zone skips to catch fast movements
            if zone_frames >= self.min_zone_frames_for_skip:
                # Validate movement direction using trajectory
                if not self._validate_movement_direction(track_id, 'IN'):
                    self.logger.info(f"Track {track_id} movement direction invalid for IN (zone skip) - ignoring")
                    state_info['state'] = 'inside'
                    state_info['zone_frames'] = 1
                    self.counted_ids.add(track_id)
                    return None

                # Check for ID swap using spatial separation
                if self._is_near_recent_count(centroid, 'IN', frame_number):
                    self.logger.info(f"Track {track_id} near recent IN count - likely ID swap, ignoring")
                    state_info['state'] = 'inside'
                    state_info['zone_frames'] = 1
                    self.counted_ids.add(track_id)
                    return None

                # Count as IN - person clearly entered
                self.count_in += 1
                self.logger.info(f"🟢 ✓ Person IN (FAST) - ID: {track_id}, Total IN: {self.count_in} 🟢")
                print(f"\n{'='*60}")
                print(f"🟢 IN COUNT INCREMENTED! Track {track_id} (ZONE SKIP)")
                print(f"🟢 Journey: outside → inside (skipped transition - fast movement)")
                print(f"🟢 Total IN: {self.count_in}")
                print(f"🟢 Total OUT: {self.count_out}")
                print(f"🟢 Occupancy: {self.count_in - self.count_out}")
                print(f"{'='*60}\n")

                # Mark as counted
                self.counted_ids.add(track_id)
                self.recent_counts.append((centroid, frame_number, 'IN'))

                # Update state
                state_info['state'] = 'inside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None

                # Create event
                event = {
                    'timestamp': datetime.now(),
                    'track_id': track_id,
                    'type': 'IN',
                    'frame': frame_number,
                    'position': centroid,
                    'count_in': self.count_in,
                    'count_out': self.count_out,
                    'occupancy': self.count_in - self.count_out,
                    'zone_skip': True  # Flag for debugging
                }
                return event
            else:
                self.logger.debug(f"Track {track_id}: unstable outside ({zone_frames}f < {self.min_zone_frames}), waiting")
                state_info['zone_frames'] += 1
                return None

        # Case 2: inside → outside (skipped transition) = EXITING
        elif current_state == 'inside' and current_zone == 'outside':
            # Person jumped from inside to outside (missed transition zone)
            # Use lower threshold for zone skips to catch fast movements
            if zone_frames >= self.min_zone_frames_for_skip:
                # Validate movement direction using trajectory
                if not self._validate_movement_direction(track_id, 'OUT'):
                    self.logger.info(f"Track {track_id} movement direction invalid for OUT (zone skip) - ignoring")
                    state_info['state'] = 'outside'
                    state_info['zone_frames'] = 1
                    self.counted_ids.add(track_id)
                    return None

                # Check for ID swap using spatial separation
                if self._is_near_recent_count(centroid, 'OUT', frame_number):
                    self.logger.info(f"Track {track_id} near recent OUT count - likely ID swap, ignoring")
                    state_info['state'] = 'outside'
                    state_info['zone_frames'] = 1
                    self.counted_ids.add(track_id)
                    return None

                # Count as OUT - person clearly exited
                self.count_out += 1
                self.logger.info(f"🔴 ✓ Person OUT (FAST) - ID: {track_id}, Total OUT: {self.count_out} 🔴")
                print(f"\n{'='*60}")
                print(f"🔴 OUT COUNT INCREMENTED! Track {track_id} (ZONE SKIP)")
                print(f"🔴 Journey: inside → outside (skipped transition - fast movement)")
                print(f"🔴 Total OUT: {self.count_out}")
                print(f"🔴 Total IN: {self.count_in}")
                print(f"🔴 Occupancy: {self.count_in - self.count_out}")
                print(f"{'='*60}\n")

                # Mark as counted
                self.counted_ids.add(track_id)
                self.recent_counts.append((centroid, frame_number, 'OUT'))

                # Update state
                state_info['state'] = 'outside'
                state_info['zone_frames'] = 1
                state_info['origin_zone'] = None

                # Create event
                event = {
                    'timestamp': datetime.now(),
                    'track_id': track_id,
                    'type': 'OUT',
                    'frame': frame_number,
                    'position': centroid,
                    'count_in': self.count_in,
                    'count_out': self.count_out,
                    'occupancy': self.count_in - self.count_out,
                    'zone_skip': True  # Flag for debugging
                }
                return event
            else:
                self.logger.debug(f"Track {track_id}: unstable inside ({zone_frames}f < {self.min_zone_frames}), waiting")
                state_info['zone_frames'] += 1
                return None

        # Other transitions - reset
        else:
            self.logger.debug(f"Track {track_id}: {current_state} → {current_zone} (unexpected, resetting)")
            state_info['state'] = current_zone if current_zone != 'transition' else current_state
            state_info['zone_frames'] = 1
            return None

    def update(self, tracks, frame_number):
        """
        Update counter with new tracks using ZONE-BASED state machine.

        Args:
            tracks: Array of tracks [[x1,y1,x2,y2,track_id], ...]
            frame_number: Current frame number

        Returns:
            events: List of new counting events
        """
        new_events = []

        # Get current active track IDs
        active_track_ids = set([int(track[4]) for track in tracks])

        # Log when multiple people are being tracked
        if len(active_track_ids) > 1:
            self.logger.debug(f"📊 Tracking {len(active_track_ids)} people simultaneously: {sorted(active_track_ids)}")
            print(f"\n{'='*70}")
            print(f"📊 MULTIPLE PEOPLE: Tracking {len(active_track_ids)} people: {sorted(active_track_ids)}")
            print(f"{'='*70}")

        # Clean up state for inactive tracks (with grace period)
        # CRITICAL: Don't immediately delete state when track is lost!
        # Keep state for grace period to allow track recovery
        for track_id in list(self.track_states.keys()):
            if track_id not in active_track_ids:
                state_info = self.track_states[track_id]

                # Initialize lost_frames counter if not present
                if 'lost_frames' not in state_info:
                    state_info['lost_frames'] = 0

                state_info['lost_frames'] += 1

                # Only delete state after grace period (90 frames = 3 seconds)
                # This matches max_age in tracker config
                if state_info['lost_frames'] > 90:
                    self.logger.debug(f"Track {track_id} lost for {state_info['lost_frames']} frames, cleaning up state")
                    del self.track_states[track_id]
                else:
                    self.logger.debug(f"Track {track_id} temporarily lost ({state_info['lost_frames']} frames), keeping state for recovery")
            else:
                # Track is active, reset lost_frames counter
                if 'lost_frames' in self.track_states[track_id]:
                    if self.track_states[track_id]['lost_frames'] > 0:
                        self.logger.info(f"✅ Track {track_id} RECOVERED after {self.track_states[track_id]['lost_frames']} frames - continuing from state={self.track_states[track_id].get('state')}")
                    self.track_states[track_id]['lost_frames'] = 0

        # Process each track using zone-based state machine
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

            # Log current state for debugging
            state_info = self.track_states[track_id]
            current_state = state_info.get('state') or 'none'
            direction = state_info.get('direction') or 'none'
            origin = state_info.get('origin_zone') or 'none'
            zone_frames = state_info.get('zone_frames', 0)

            # Show detailed info for ALL tracks (for debugging)
            print(f"  👤 Track {track_id}: zone={current_zone:10s} | state={current_state:10s} | dir={direction:8s} | origin={origin:7s} | frames={zone_frames}")

            self.logger.debug(f"Track {track_id}: zone={current_zone}, state={current_state}, dir={direction}, origin={origin}, frames={zone_frames}, pos=({cx},{cy})")

            # Update zone-based state machine
            event = self._update_zone_state(track_id, current_zone, centroid, frame_number)

            if event:
                new_events.append(event)
                self.events.append(event)
                print(f"📊 Event created: {event['type']} for track {track_id}")

        # Log summary if multiple people or events occurred
        if len(active_track_ids) > 1 or new_events:
            states_summary = []
            for tid in sorted(active_track_ids):
                state = self.track_states[tid].get('state', 'unknown')
                direction = self.track_states[tid].get('direction', '')
                if direction:
                    states_summary.append(f"{tid}:{state}({direction})")
                else:
                    states_summary.append(f"{tid}:{state}")
            self.logger.debug(f"Frame {frame_number} summary: {', '.join(states_summary)} | IN:{self.count_in} OUT:{self.count_out}")

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
        self.track_history.clear()
        self.track_states.clear()
        self.events.clear()
        self.logger.info("Counter reset")


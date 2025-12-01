"""
Object Tracking Module using ByteTrack
ByteTrack: Multi-Object Tracking by Associating Every Detection Box
Paper: https://arxiv.org/abs/2110.06864

ByteTrack improves upon SORT by:
1. Using both high and low confidence detections
2. Better handling of occlusions and missed frames
3. More stable track IDs in crowded scenes
4. Two-stage association (high-conf first, then low-conf)
"""
import logging
import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment


class KalmanBoxTracker:
    """Kalman Filter based tracker for bounding boxes"""
    
    count = 0
    
    def __init__(self, bbox):
        """Initialize tracker with initial bounding box"""
        # Define constant velocity model
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        self.kf.R[2:, 2:] *= 10.
        self.kf.P[4:, 4:] *= 1000.
        self.kf.P *= 10.
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0

        # ByteTrack specific attributes
        self.state = 'new'  # 'new', 'tracked', 'lost', 'removed'
        self.is_activated = False
        self.frame_id = 0
        self.start_frame = 0
        
    def update(self, bbox):
        """Update tracker with new detection"""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
        
    def predict(self):
        """Predict next state"""
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]
        
    def get_state(self):
        """Return current bounding box estimate"""
        return self._convert_x_to_bbox(self.kf.x)

    def activate(self, frame_id):
        """Activate a new track (ByteTrack)"""
        self.is_activated = True
        self.state = 'tracked'
        self.frame_id = frame_id
        self.start_frame = frame_id

    def reactivate(self, new_det):
        """Reactivate a lost track (ByteTrack)"""
        if new_det is not None:
            self.kf.update(self._convert_bbox_to_z(new_det))
        self.state = 'tracked'
        self.is_activated = True
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1

    def mark_lost(self):
        """Mark track as lost (ByteTrack)"""
        self.state = 'lost'
        
    @staticmethod
    def _convert_bbox_to_z(bbox):
        """Convert [x1,y1,x2,y2] to [cx,cy,s,r]"""
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.
        y = bbox[1] + h / 2.
        s = w * h
        r = w / float(h) if h != 0 else 1
        return np.array([x, y, s, r]).reshape((4, 1))
        
    @staticmethod
    def _convert_x_to_bbox(x):
        """Convert [cx,cy,s,r] to [x1,y1,x2,y2]"""
        # Extract values, handling both scalar and array types
        cx = float(x[0])
        cy = float(x[1])
        s = float(x[2])
        r = float(x[3])

        # Ensure positive values
        s = max(s, 1.0)
        r = max(min(r, 10.0), 0.1)

        w = np.sqrt(s * r)
        h = s / w if w > 0 else 1.0

        return np.array([
            cx - w / 2., cy - h / 2.,
            cx + w / 2., cy + h / 2.
        ]).reshape((1, 4))[0]


class ByteTracker:
    """
    ByteTrack: Multi-Object Tracking with Two-Stage Association

    Improvements over SORT:
    - Uses both high and low confidence detections
    - Two-stage matching: high-conf first, then low-conf for recovery
    - Better handling of occlusions and missed frames
    - More stable track IDs in crowded scenes
    """

    def __init__(self, config):
        """Initialize ByteTrack tracker"""
        self.logger = logging.getLogger(__name__)
        self.config = config['tracking']

        # Core tracking parameters
        self.max_age = self.config.get('max_age', 60)
        self.min_hits = self.config.get('min_hits', 1)
        self.iou_threshold = self.config.get('iou_threshold', 0.2)

        # ByteTrack specific parameters
        self.track_high_thresh = self.config.get('track_high_thresh', 0.6)  # High confidence threshold
        self.track_low_thresh = self.config.get('track_low_thresh', 0.1)   # Low confidence threshold
        self.new_track_thresh = self.config.get('new_track_thresh', 0.7)   # New track creation threshold
        self.track_buffer = self.config.get('track_buffer', 30)            # Track buffer frames

        self.tracked_tracks = []  # Active tracks (high confidence)
        self.lost_tracks = []     # Lost tracks (low confidence, being recovered)
        self.removed_tracks = []  # Removed tracks (dead)

        self.frame_count = 0

        self.logger.info(f"🚀 ByteTrack initialized - Max age: {self.max_age}, Min hits: {self.min_hits}")
        self.logger.info(f"   High thresh: {self.track_high_thresh}, Low thresh: {self.track_low_thresh}, New track: {self.new_track_thresh}")
        self.logger.info(f"   Track buffer: {self.track_buffer}, IOU threshold: {self.iou_threshold}")
        
    def update(self, detections):
        """
        Update tracker with new detections using ByteTrack's two-stage association

        Args:
            detections: Array of detections [[x1,y1,x2,y2,score], ...]

        Returns:
            tracks: Array of active tracks [[x1,y1,x2,y2,track_id], ...]
        """
        self.frame_count += 1

        # Separate detections by confidence
        if len(detections) > 0:
            high_det_idx = detections[:, 4] >= self.track_high_thresh
            low_det_idx = (detections[:, 4] >= self.track_low_thresh) & (detections[:, 4] < self.track_high_thresh)

            detections_high = detections[high_det_idx]
            detections_low = detections[low_det_idx]

            # Log detection confidence distribution
            if len(detections) > 1:
                self.logger.debug(f"📊 {len(detections)} detections: {len(detections_high)} high-conf (≥{self.track_high_thresh}), {len(detections_low)} low-conf ({self.track_low_thresh}-{self.track_high_thresh})")
                if len(detections_low) > 0:
                    self.logger.debug(f"   Low-conf scores: {[f'{d[4]:.2f}' for d in detections_low]}")
        else:
            detections_high = np.empty((0, 5))
            detections_low = np.empty((0, 5))

        # Predict all tracks
        for track in self.tracked_tracks + self.lost_tracks:
            track.predict()

        # STAGE 1: Associate high-confidence detections with tracked tracks
        matched_high, unmatched_tracks_high, unmatched_dets_high = self._associate(
            detections_high, self.tracked_tracks, self.iou_threshold
        )

        # Update matched tracks
        for track_idx, det_idx in matched_high:
            self.tracked_tracks[track_idx].update(detections_high[det_idx, :])

        # STAGE 2: Associate remaining tracks with low-confidence detections
        # This is the key innovation of ByteTrack - recover lost tracks with low-conf detections
        unmatched_tracks = [self.tracked_tracks[i] for i in unmatched_tracks_high]

        matched_low, unmatched_tracks_low, unmatched_dets_low = self._associate(
            detections_low, unmatched_tracks, self.iou_threshold
        )

        # Update tracks matched with low-confidence detections
        for track_idx, det_idx in matched_low:
            unmatched_tracks[track_idx].update(detections_low[det_idx, :])

        # Mark remaining unmatched tracks as lost
        for track_idx in unmatched_tracks_low:
            track = unmatched_tracks[track_idx]
            if track.state != 'lost':
                track.mark_lost()

        # STAGE 3: Associate lost tracks with remaining high-confidence detections
        unmatched_dets_high_idx = [detections_high[i] for i in unmatched_dets_high]

        matched_lost, unmatched_lost, unmatched_dets_final = self._associate(
            np.array(unmatched_dets_high_idx) if len(unmatched_dets_high_idx) > 0 else np.empty((0, 5)),
            self.lost_tracks,
            self.iou_threshold
        )

        # Reactivate lost tracks that were matched
        for track_idx, det_idx in matched_lost:
            self.lost_tracks[track_idx].reactivate(
                unmatched_dets_high_idx[det_idx] if len(unmatched_dets_high_idx) > 0 else None
            )
            self.tracked_tracks.append(self.lost_tracks[track_idx])

        # Create new tracks from remaining high-confidence detections
        for det_idx in unmatched_dets_final:
            if len(unmatched_dets_high_idx) > 0:
                det = unmatched_dets_high_idx[det_idx]
                if det[4] >= self.new_track_thresh:  # Only create track if above new track threshold
                    new_track = KalmanBoxTracker(det)
                    new_track.activate(self.frame_count)
                    self.tracked_tracks.append(new_track)

        # Remove lost tracks from lost_tracks list if they were reactivated
        self.lost_tracks = [t for i, t in enumerate(self.lost_tracks) if i not in [m[0] for m in matched_lost]]

        # Move tracks from tracked to lost if they've been lost
        tracked_tracks_new = []
        for track in self.tracked_tracks:
            if track.state == 'tracked':
                tracked_tracks_new.append(track)
            else:
                self.lost_tracks.append(track)
        self.tracked_tracks = tracked_tracks_new

        # Remove dead tracks
        # Log tracks being removed
        removed_lost = [t for t in self.lost_tracks if t.time_since_update > self.max_age]
        removed_tracked = [t for t in self.tracked_tracks if t.time_since_update > self.max_age]

        if len(removed_lost) > 0:
            self.logger.warning(f"⚠️ Removing {len(removed_lost)} lost tracks (exceeded max_age={self.max_age}): {[t.id for t in removed_lost]}")
        if len(removed_tracked) > 0:
            self.logger.warning(f"⚠️ Removing {len(removed_tracked)} tracked tracks (exceeded max_age={self.max_age}): {[t.id for t in removed_tracked]}")

        self.lost_tracks = [t for t in self.lost_tracks if t.time_since_update <= self.max_age]
        self.tracked_tracks = [t for t in self.tracked_tracks if t.time_since_update <= self.max_age]

        # Return active tracks
        output_tracks = []
        for track in self.tracked_tracks:
            if track.is_activated and track.time_since_update < 1:
                d = track.get_state()
                output_tracks.append(np.concatenate((d, [track.id])).reshape(1, -1))

        if len(output_tracks) > 0:
            return np.concatenate(output_tracks)
        return np.empty((0, 5))

    def _associate(self, detections, tracks, iou_threshold):
        """
        Associate detections to tracks using IoU matching

        Args:
            detections: Array of detections [[x1,y1,x2,y2,score], ...]
            tracks: List of track objects
            iou_threshold: IoU threshold for matching

        Returns:
            matches: List of (track_idx, det_idx) pairs
            unmatched_tracks: List of unmatched track indices
            unmatched_dets: List of unmatched detection indices
        """
        if len(tracks) == 0:
            return [], [], list(range(len(detections)))

        if len(detections) == 0:
            return [], list(range(len(tracks))), []

        # Build IoU matrix
        iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)

        for d, det in enumerate(detections):
            for t, track in enumerate(tracks):
                track_bbox = track.get_state()
                iou_matrix[d, t] = self._iou(det[:4], track_bbox)

        # Use Hungarian algorithm for optimal assignment
        if min(iou_matrix.shape) > 0:
            # Try greedy assignment first (faster)
            a = (iou_matrix > iou_threshold).astype(np.int32)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = np.stack(np.where(a), axis=1)
            else:
                # Use Hungarian algorithm
                matched_indices = self._linear_assignment(-iou_matrix)
        else:
            matched_indices = np.empty(shape=(0, 2))

        # Find unmatched detections and tracks
        unmatched_dets = []
        for d in range(len(detections)):
            if len(matched_indices) == 0 or d not in matched_indices[:, 0]:
                unmatched_dets.append(d)

        unmatched_tracks = []
        for t in range(len(tracks)):
            if len(matched_indices) == 0 or t not in matched_indices[:, 1]:
                unmatched_tracks.append(t)

        # Filter out matched with low IOU
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < iou_threshold:
                unmatched_dets.append(m[0])
                unmatched_tracks.append(m[1])
            else:
                matches.append((m[1], m[0]))  # (track_idx, det_idx)

        return matches, unmatched_tracks, unmatched_dets

    def _associate_detections_to_trackers(self, detections, trackers):
        """Associate detections to tracked objects using IOU"""
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)

        iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)

        for d, det in enumerate(detections):
            for t, trk in enumerate(trackers):
                iou_matrix[d, t] = self._iou(det, trk)

        if min(iou_matrix.shape) > 0:
            a = (iou_matrix > self.iou_threshold).astype(np.int32)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = np.stack(np.where(a), axis=1)
            else:
                matched_indices = self._linear_assignment(-iou_matrix)
        else:
            matched_indices = np.empty(shape=(0, 2))

        unmatched_detections = []
        for d, det in enumerate(detections):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)

        unmatched_trackers = []
        for t, trk in enumerate(trackers):
            if t not in matched_indices[:, 1]:
                unmatched_trackers.append(t)

        # Filter out matched with low IOU
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < self.iou_threshold:
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))

        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)

        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)

    @staticmethod
    def _iou(bb_test, bb_gt):
        """Calculate IOU between two bounding boxes"""
        xx1 = np.maximum(bb_test[0], bb_gt[0])
        yy1 = np.maximum(bb_test[1], bb_gt[1])
        xx2 = np.minimum(bb_test[2], bb_gt[2])
        yy2 = np.minimum(bb_test[3], bb_gt[3])
        w = np.maximum(0., xx2 - xx1)
        h = np.maximum(0., yy2 - yy1)
        wh = w * h
        o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
                  + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
        return o

    @staticmethod
    def _linear_assignment(cost_matrix):
        """Linear assignment using Hungarian algorithm"""
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))


# Backward compatibility alias
SORTTracker = ByteTracker


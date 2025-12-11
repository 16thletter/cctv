"""
Strong SORT: Multi-Object Tracking with Appearance Features
Combines SORT/ByteTrack with ReID (Re-Identification) for robust tracking
Paper: "StrongSORT: Make DeepSORT Great Again"

Key improvements over ByteTrack:
1. Appearance features using ReID model (GPU-accelerated)
2. Better handling of occlusions and ID switches
3. Appearance-motion fusion for association
4. EMA (Exponential Moving Average) for feature smoothing
"""
import logging
import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment
import lap  # Linear Assignment Problem solver (faster than scipy)
from cctv.core.reid_model import ReIDModel


class KalmanBoxTracker:
    """Kalman Filter based tracker with appearance features"""
    
    count = 0
    
    def __init__(self, bbox, feature=None):
        """Initialize tracker with initial bounding box and appearance feature"""
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
        
        # Strong SORT specific attributes
        self.state = 'new'
        self.is_activated = False
        self.frame_id = 0
        self.start_frame = 0
        
        # Appearance features
        self.smooth_feature = feature  # EMA smoothed feature
        self.curr_feature = feature    # Current frame feature
        self.features = []             # Feature history
        self.alpha = 0.9               # EMA smoothing factor
        
    def update(self, bbox, feature=None):
        """Update tracker with new detection and appearance feature"""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
        
        # Update appearance feature with EMA
        if feature is not None:
            self.curr_feature = feature
            if self.smooth_feature is None:
                self.smooth_feature = feature
            else:
                self.smooth_feature = self.alpha * self.smooth_feature + (1 - self.alpha) * feature
            
            # Keep feature history (max 100 frames)
            self.features.append(feature)
            if len(self.features) > 100:
                self.features.pop(0)
        
        self.state = 'tracked'
        self.is_activated = True
        
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
    
    def _convert_bbox_to_z(self, bbox):
        """Convert [x1,y1,x2,y2] to [cx,cy,s,r]"""
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.
        y = bbox[1] + h / 2.
        s = w * h
        r = w / float(h + 1e-6)
        return np.array([x, y, s, r]).reshape((4, 1))
    
    def _convert_x_to_bbox(self, x, score=None):
        """Convert [cx,cy,s,r] to [x1,y1,x2,y2]"""
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w
        if score is None:
            return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2.]).reshape((1, 4))
        else:
            return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2., score]).reshape((1, 5))


def iou_batch(bb_test, bb_gt):
    """Compute IoU between two sets of boxes"""
    bb_gt = np.expand_dims(bb_gt, 0)
    bb_test = np.expand_dims(bb_test, 1)

    xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
    yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
    xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
    yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    wh = w * h
    o = wh / ((bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1])
              + (bb_gt[..., 2] - bb_gt[..., 0]) * (bb_gt[..., 3] - bb_gt[..., 1]) - wh + 1e-6)
    return o


class StrongSORT:
    """
    Strong SORT tracker with appearance features
    Combines motion (Kalman) and appearance (ReID) for robust tracking
    """

    def __init__(self, config):
        """Initialize Strong SORT tracker"""
        self.logger = logging.getLogger(__name__)
        self.config = config['tracking']

        # Core tracking parameters
        self.max_age = self.config.get('max_age', 90)
        self.min_hits = self.config.get('min_hits', 1)
        self.iou_threshold = self.config.get('iou_threshold', 0.3)

        # Strong SORT specific parameters
        self.track_high_thresh = self.config.get('track_high_thresh', 0.4)
        self.track_low_thresh = self.config.get('track_low_thresh', 0.05)
        self.new_track_thresh = self.config.get('new_track_thresh', 0.4)
        self.track_buffer = self.config.get('track_buffer', 45)

        # Appearance feature parameters
        self.lambda_iou = self.config.get('lambda_iou', 0.98)  # Weight for IoU
        self.lambda_app = self.config.get('lambda_app', 0.02)  # Weight for appearance
        self.appearance_thresh = self.config.get('appearance_thresh', 0.25)

        # Initialize ReID model
        device = config.get('detection', {}).get('device', 'cuda')
        self.reid_model = ReIDModel(device=device)

        self.tracked_tracks = []
        self.lost_tracks = []
        self.removed_tracks = []
        self.frame_count = 0

        self.logger.info(f"🚀 Strong SORT initialized - Max age: {self.max_age}, Min hits: {self.min_hits}")
        self.logger.info(f"   High thresh: {self.track_high_thresh}, Low thresh: {self.track_low_thresh}")
        self.logger.info(f"   IoU weight: {self.lambda_iou}, Appearance weight: {self.lambda_app}")
        self.logger.info(f"   ReID model: GPU-accelerated OSNet")

    def update(self, detections, frame=None):
        """
        Update tracker with new detections

        Args:
            detections: Array of detections [[x1,y1,x2,y2,score], ...]
            frame: Current frame (numpy array) for extracting appearance features

        Returns:
            tracks: Array of active tracks [[x1,y1,x2,y2,track_id], ...]
        """
        self.frame_count += 1

        # Extract appearance features if frame is provided
        features = None
        if frame is not None and len(detections) > 0:
            crops = []
            for det in detections:
                x1, y1, x2, y2 = int(det[0]), int(det[1]), int(det[2]), int(det[3])
                # Ensure valid crop
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    crop = frame[y1:y2, x1:x2]
                    crops.append(crop)
                else:
                    crops.append(np.zeros((64, 32, 3), dtype=np.uint8))

            if len(crops) > 0:
                features = self.reid_model.extract_features(crops)

        # Split detections by confidence
        if len(detections) > 0:
            scores = detections[:, 4]
            high_idx = scores >= self.track_high_thresh
            low_idx = (scores >= self.track_low_thresh) & (scores < self.track_high_thresh)

            detections_high = detections[high_idx]
            detections_low = detections[low_idx]

            features_high = features[high_idx] if features is not None else None
            features_low = features[low_idx] if features is not None else None
        else:
            detections_high = np.empty((0, 5))
            detections_low = np.empty((0, 5))
            features_high = None
            features_low = None

        # Predict all tracks
        for track in self.tracked_tracks + self.lost_tracks:
            track.predict()

        # STAGE 1: Associate high-confidence detections with tracked tracks
        matched_high, unmatched_tracks_high, unmatched_dets_high = self._associate(
            detections_high, self.tracked_tracks, self.iou_threshold, features_high
        )

        # Update matched tracks
        for track_idx, det_idx in matched_high:
            feat = features_high[det_idx] if features_high is not None else None
            self.tracked_tracks[track_idx].update(detections_high[det_idx, :4], feat)

        # STAGE 2: Associate remaining high-conf detections with lost tracks
        unmatched_tracked = [self.tracked_tracks[i] for i in unmatched_tracks_high]
        matched_lost, unmatched_tracks_lost, unmatched_dets_high2 = self._associate(
            detections_high[unmatched_dets_high], self.lost_tracks, self.iou_threshold,
            features_high[unmatched_dets_high] if features_high is not None else None
        )

        # Recover lost tracks
        for track_idx, det_idx in matched_lost:
            feat = features_high[unmatched_dets_high[det_idx]] if features_high is not None else None
            self.lost_tracks[track_idx].update(detections_high[unmatched_dets_high[det_idx], :4], feat)
            self.tracked_tracks.append(self.lost_tracks[track_idx])

        # Remove matched lost tracks
        self.lost_tracks = [self.lost_tracks[i] for i in unmatched_tracks_lost]

        # STAGE 3: Associate low-confidence detections with unmatched tracks
        unmatched_dets_high_final = [unmatched_dets_high[i] for i in unmatched_dets_high2]
        unmatched_tracked_final = [t for t in unmatched_tracked]

        if len(detections_low) > 0:
            matched_low, unmatched_tracks_low, _ = self._associate(
                detections_low, unmatched_tracked_final, 0.5,  # Lower IoU threshold
                features_low
            )

            for track_idx, det_idx in matched_low:
                feat = features_low[det_idx] if features_low is not None else None
                unmatched_tracked_final[track_idx].update(detections_low[det_idx, :4], feat)

        # Create new tracks from unmatched high-confidence detections
        for det_idx in unmatched_dets_high_final:
            if detections_high[det_idx, 4] >= self.new_track_thresh:
                feat = features_high[det_idx] if features_high is not None else None
                new_track = KalmanBoxTracker(detections_high[det_idx, :4], feat)
                new_track.is_activated = True
                new_track.state = 'tracked'
                self.tracked_tracks.append(new_track)

        # Move lost tracks
        lost_tracks_temp = []
        for track in self.tracked_tracks:
            if track.time_since_update > self.max_age:
                self.removed_tracks.append(track)
            elif track.time_since_update > 1:
                track.state = 'lost'
                lost_tracks_temp.append(track)

        self.tracked_tracks = [t for t in self.tracked_tracks if t.time_since_update <= 1]
        self.lost_tracks.extend(lost_tracks_temp)

        # Remove old lost tracks
        self.lost_tracks = [t for t in self.lost_tracks if t.time_since_update <= self.track_buffer]

        # Return active tracks
        output_tracks = []
        for track in self.tracked_tracks:
            if track.is_activated and track.hits >= self.min_hits:
                bbox = track.get_state()[0]
                output_tracks.append([bbox[0], bbox[1], bbox[2], bbox[3], track.id])

        return np.array(output_tracks) if len(output_tracks) > 0 else np.empty((0, 5))

    def _associate(self, detections, tracks, iou_threshold, features=None):
        """Associate detections with tracks using IoU and appearance"""
        if len(tracks) == 0:
            return [], [], list(range(len(detections)))

        if len(detections) == 0:
            return [], list(range(len(tracks))), []

        # Compute IoU cost matrix
        track_boxes = np.array([t.get_state()[0] for t in tracks])
        det_boxes = detections[:, :4]
        iou_matrix = iou_batch(det_boxes, track_boxes)

        # Compute appearance cost matrix if features available
        if features is not None and len(features) > 0:
            track_features = []
            for t in tracks:
                if t.smooth_feature is not None:
                    track_features.append(t.smooth_feature)
                else:
                    track_features.append(np.zeros(512))  # Dummy feature

            track_features = np.array(track_features)
            app_matrix = self.reid_model.compute_distance(features, track_features)

            # Fuse IoU and appearance
            cost_matrix = self.lambda_iou * (1 - iou_matrix) + self.lambda_app * app_matrix
        else:
            cost_matrix = 1 - iou_matrix

        # Linear assignment
        if cost_matrix.size > 0:
            matched_indices = lap.lapjv(cost_matrix, extend_cost=True, cost_limit=1.0)[1]

            matches = []
            unmatched_dets = []
            unmatched_tracks = []

            for det_idx, track_idx in enumerate(matched_indices):
                if track_idx < 0:
                    unmatched_dets.append(det_idx)
                elif iou_matrix[det_idx, track_idx] < iou_threshold:
                    unmatched_dets.append(det_idx)
                    unmatched_tracks.append(track_idx)
                else:
                    matches.append([track_idx, det_idx])

            # Find unmatched tracks
            matched_track_indices = set([m[0] for m in matches])
            for track_idx in range(len(tracks)):
                if track_idx not in matched_track_indices:
                    unmatched_tracks.append(track_idx)

            return matches, unmatched_tracks, unmatched_dets
        else:
            return [], list(range(len(tracks))), list(range(len(detections)))


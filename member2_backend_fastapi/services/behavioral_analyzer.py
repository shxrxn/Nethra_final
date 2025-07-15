"""
Behavioral Analyzer Service for NETHRA
Analyzes user behavioral patterns and detects anomalies
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import defaultdict, deque
import statistics

from services.ai_interface import AIModelInterface
from models.behavioral_models import (
    BehavioralSession, TouchPattern, SwipePattern, DeviceMotion,
    NavigationPattern, TransactionPattern, TypingPattern,
    BehaviorType, AnomalyDetection, create_behavioral_features
)

logger = logging.getLogger(__name__)

@dataclass
class BehavioralBaseline:
    """Baseline behavioral metrics for a user"""
    touch_pressure_mean: float = 0.0
    touch_pressure_std: float = 0.0
    touch_duration_mean: float = 0.0
    touch_duration_std: float = 0.0
    
    swipe_velocity_mean: float = 0.0
    swipe_velocity_std: float = 0.0
    swipe_acceleration_mean: float = 0.0
    swipe_acceleration_std: float = 0.0
    
    motion_stability_mean: float = 0.0
    motion_stability_std: float = 0.0
    
    navigation_speed_mean: float = 0.0
    navigation_speed_std: float = 0.0
    
    sample_count: int = 0
    last_updated: datetime = datetime.now()

class BehavioralAnalyzer:
    """Advanced behavioral pattern analysis service"""
    
    def __init__(self, ai_interface: AIModelInterface):
        self.ai_interface = ai_interface
        self.baselines: Dict[str, BehavioralBaseline] = {}
        self.pattern_cache: Dict[str, Dict] = {}
        self.anomaly_history: Dict[str, List[AnomalyDetection]] = {}
        
        # Analysis parameters
        self.min_samples_for_baseline = 20
        self.baseline_update_threshold = 0.1
        self.anomaly_threshold = 2.0  # Standard deviations
        self.pattern_window_size = 100
        
        # Real-time analysis
        self.real_time_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Performance metrics
        self.analysis_count = 0
        self.anomaly_detection_count = 0
        self.false_positive_count = 0
        
        logger.info("Behavioral Analyzer initialized")
    
    async def analyze_session(self, session: BehavioralSession) -> Dict[str, Any]:
        """Comprehensive behavioral analysis of a session"""
        user_key = f"{session.user_id}_{session.device_id}"
        
        try:
            # Update real-time buffers
            self._update_real_time_buffers(session)
            
            # Get or create baseline
            baseline = await self._get_or_create_baseline(user_key, session)
            
            # Analyze different behavioral aspects
            touch_analysis = await self._analyze_touch_patterns(session.touch_patterns, baseline)
            swipe_analysis = await self._analyze_swipe_patterns(session.swipe_patterns, baseline)
            motion_analysis = await self._analyze_device_motion(session.device_motions, baseline)
            navigation_analysis = await self._analyze_navigation_patterns(session.navigation_patterns, baseline)
            
            # Detect temporal patterns
            temporal_analysis = await self._analyze_temporal_patterns(session)
            
            # Detect contextual anomalies
            contextual_analysis = await self._analyze_contextual_patterns(session)
            
            # Combine all analyses
            combined_analysis = {
                "touch_analysis": touch_analysis,
                "swipe_analysis": swipe_analysis,
                "motion_analysis": motion_analysis,
                "navigation_analysis": navigation_analysis,
                "temporal_analysis": temporal_analysis,
                "contextual_analysis": contextual_analysis,
                "overall_consistency": self._calculate_overall_consistency(
                    touch_analysis, swipe_analysis, motion_analysis, navigation_analysis
                ),
                "behavioral_entropy": self._calculate_behavioral_entropy(session),
                "session_metadata": {
                    "duration": (session.end_time - session.start_time).total_seconds() if session.end_time else 0,
                    "interaction_count": len(session.touch_patterns) + len(session.swipe_patterns),
                    "pattern_diversity": self._calculate_pattern_diversity(session)
                }
            }
            
            # Update baseline
            await self._update_baseline(user_key, session, combined_analysis)
            
            # Update metrics
            self.analysis_count += 1
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {str(e)}")
            return self._get_fallback_analysis()
    
    def _update_real_time_buffers(self, session: BehavioralSession):
        """Update real-time analysis buffers"""
        user_key = f"{session.user_id}_{session.device_id}"
        
        # Add touch data
        for touch in session.touch_patterns:
            self.real_time_buffers[f"{user_key}_touch"].append({
                "pressure": touch.pressure,
                "duration": touch.duration,
                "timestamp": touch.timestamp
            })
        
        # Add swipe data
        for swipe in session.swipe_patterns:
            self.real_time_buffers[f"{user_key}_swipe"].append({
                "velocity": swipe.velocity,
                "acceleration": swipe.acceleration,
                "timestamp": swipe.timestamp
            })
    
    async def _get_or_create_baseline(self, user_key: str, session: BehavioralSession) -> BehavioralBaseline:
        """Get existing baseline or create new one"""
        if user_key not in self.baselines:
            self.baselines[user_key] = BehavioralBaseline()
        
        baseline = self.baselines[user_key]
        
        # Initialize baseline if we have enough samples
        if (baseline.sample_count < self.min_samples_for_baseline and 
            len(session.touch_patterns) > 0):
            await self._initialize_baseline(baseline, session)
        
        return baseline
    
    async def _initialize_baseline(self, baseline: BehavioralBaseline, session: BehavioralSession):
        """Initialize baseline with session data"""
        # Touch baseline
        if session.touch_patterns:
            pressures = [t.pressure for t in session.touch_patterns]
            durations = [t.duration for t in session.touch_patterns]
            
            baseline.touch_pressure_mean = statistics.mean(pressures)
            baseline.touch_pressure_std = statistics.stdev(pressures) if len(pressures) > 1 else 0.1
            baseline.touch_duration_mean = statistics.mean(durations)
            baseline.touch_duration_std = statistics.stdev(durations) if len(durations) > 1 else 0.1
        
        # Swipe baseline
        if session.swipe_patterns:
            velocities = [s.velocity for s in session.swipe_patterns]
            accelerations = [s.acceleration for s in session.swipe_patterns]
            
            baseline.swipe_velocity_mean = statistics.mean(velocities)
            baseline.swipe_velocity_std = statistics.stdev(velocities) if len(velocities) > 1 else 0.1
            baseline.swipe_acceleration_mean = statistics.mean(accelerations)
            baseline.swipe_acceleration_std = statistics.stdev(accelerations) if len(accelerations) > 1 else 0.1
        
        # Motion baseline
        if session.device_motions:
            stabilities = [self._calculate_motion_stability(m) for m in session.device_motions]
            baseline.motion_stability_mean = statistics.mean(stabilities)
            baseline.motion_stability_std = statistics.stdev(stabilities) if len(stabilities) > 1 else 0.1
        
        # Navigation baseline
        if session.navigation_patterns:
            speeds = [self._calculate_navigation_speed_single(n) for n in session.navigation_patterns]
            baseline.navigation_speed_mean = statistics.mean(speeds)
            baseline.navigation_speed_std = statistics.stdev(speeds) if len(speeds) > 1 else 0.1
        
        baseline.sample_count += 1
        baseline.last_updated = datetime.now()
    
    async def _analyze_touch_patterns(self, patterns: List[TouchPattern], baseline: BehavioralBaseline) -> Dict[str, Any]:
        """Analyze touch patterns for anomalies"""
        if not patterns:
            return {"anomaly_score": 0.0, "patterns": [], "consistency": 1.0}
        
        pressures = [p.pressure for p in patterns]
        durations = [p.duration for p in patterns]
        
        # Calculate z-scores
        pressure_z_scores = self._calculate_z_scores(pressures, baseline.touch_pressure_mean, baseline.touch_pressure_std)
        duration_z_scores = self._calculate_z_scores(durations, baseline.touch_duration_mean, baseline.touch_duration_std)
        
        # Detect anomalies
        pressure_anomalies = [abs(z) > self.anomaly_threshold for z in pressure_z_scores]
        duration_anomalies = [abs(z) > self.anomaly_threshold for z in duration_z_scores]
        
        # Calculate consistency metrics
        pressure_consistency = 1.0 - (statistics.stdev(pressures) / max(statistics.mean(pressures), 0.1))
        duration_consistency = 1.0 - (statistics.stdev(durations) / max(statistics.mean(durations), 0.1))
        
        # Calculate rhythm analysis
        rhythm_score = self._analyze_touch_rhythm(patterns)
        
        # Detect pressure patterns
        pressure_patterns = self._detect_pressure_patterns(patterns)
        
        return {
            "anomaly_score": (sum(pressure_anomalies) + sum(duration_anomalies)) / (2 * len(patterns)),
            "pressure_consistency": max(0.0, min(1.0, pressure_consistency)),
            "duration_consistency": max(0.0, min(1.0, duration_consistency)),
            "rhythm_score": rhythm_score,
            "pressure_patterns": pressure_patterns,
            "total_touches": len(patterns),
            "anomalous_touches": sum(pressure_anomalies) + sum(duration_anomalies),
            "average_pressure": statistics.mean(pressures),
            "average_duration": statistics.mean(durations)
        }
    
    async def _analyze_swipe_patterns(self, patterns: List[SwipePattern], baseline: BehavioralBaseline) -> Dict[str, Any]:
        """Analyze swipe patterns for anomalies"""
        if not patterns:
            return {"anomaly_score": 0.0, "patterns": [], "consistency": 1.0}
        
        velocities = [p.velocity for p in patterns]
        accelerations = [p.acceleration for p in patterns]
        directions = [p.direction for p in patterns]
        
        # Calculate z-scores
        velocity_z_scores = self._calculate_z_scores(velocities, baseline.swipe_velocity_mean, baseline.swipe_velocity_std)
        acceleration_z_scores = self._calculate_z_scores(accelerations, baseline.swipe_acceleration_mean, baseline.swipe_acceleration_std)
        
        # Detect anomalies
        velocity_anomalies = [abs(z) > self.anomaly_threshold for z in velocity_z_scores]
        acceleration_anomalies = [abs(z) > self.anomaly_threshold for z in acceleration_z_scores]
        
        # Direction analysis
        direction_consistency = self._calculate_direction_consistency(directions)
        
        # Gesture fluidity
        fluidity_score = self._calculate_gesture_fluidity(patterns)
        
        # Swipe rhythm
        rhythm_score = self._analyze_swipe_rhythm(patterns)
        
        return {
            "anomaly_score": (sum(velocity_anomalies) + sum(acceleration_anomalies)) / (2 * len(patterns)),
            "velocity_consistency": 1.0 - (statistics.stdev(velocities) / max(statistics.mean(velocities), 0.1)),
            "acceleration_consistency": 1.0 - (statistics.stdev(accelerations) / max(statistics.mean(accelerations), 0.1)),
            "direction_consistency": direction_consistency,
            "fluidity_score": fluidity_score,
            "rhythm_score": rhythm_score,
            "total_swipes": len(patterns),
            "anomalous_swipes": sum(velocity_anomalies) + sum(acceleration_anomalies),
            "average_velocity": statistics.mean(velocities),
            "average_acceleration": statistics.mean(accelerations),
            "dominant_direction": max(set(directions), key=directions.count) if directions else "none"
        }
    
    async def _analyze_device_motion(self, motions: List[DeviceMotion], baseline: BehavioralBaseline) -> Dict[str, Any]:
        """Analyze device motion patterns"""
        if not motions:
            return {"anomaly_score": 0.0, "stability": 1.0, "patterns": []}
        
        # Calculate stability for each motion
        stabilities = [self._calculate_motion_stability(m) for m in motions]
        
        # Calculate z-scores
        stability_z_scores = self._calculate_z_scores(stabilities, baseline.motion_stability_mean, baseline.motion_stability_std)
        
        # Detect anomalies
        stability_anomalies = [abs(z) > self.anomaly_threshold for z in stability_z_scores]
        
        # Analyze motion patterns
        shake_intensity = self._calculate_shake_intensity(motions)
        tilt_patterns = self._analyze_tilt_patterns(motions)
        orientation_changes = self._detect_orientation_changes(motions)
        
        return {
            "anomaly_score": sum(stability_anomalies) / len(motions),
            "stability_score": statistics.mean(stabilities),
            "shake_intensity": shake_intensity,
            "tilt_patterns": tilt_patterns,
            "orientation_changes": orientation_changes,
            "total_motions": len(motions),
            "anomalous_motions": sum(stability_anomalies)
        }
    
    async def _analyze_navigation_patterns(self, patterns: List[NavigationPattern], baseline: BehavioralBaseline) -> Dict[str, Any]:
        """Analyze navigation patterns"""
        if not patterns:
            return {"anomaly_score": 0.0, "consistency": 1.0, "patterns": []}
        
        # Calculate navigation speeds
        speeds = [self._calculate_navigation_speed_single(p) for p in patterns]
        
        # Calculate z-scores
        speed_z_scores = self._calculate_z_scores(speeds, baseline.navigation_speed_mean, baseline.navigation_speed_std)
        
        # Detect anomalies
        speed_anomalies = [abs(z) > self.anomaly_threshold for z in speed_z_scores]
        
        # Analyze navigation flow
        flow_consistency = self._analyze_navigation_flow(patterns)
        
        # Detect hesitation patterns
        hesitation_score = self._detect_hesitation_patterns(patterns)
        
        # Screen transition analysis
        transition_patterns = self._analyze_screen_transitions(patterns)
        
        return {
            "anomaly_score": sum(speed_anomalies) / len(patterns),
            "flow_consistency": flow_consistency,
            "hesitation_score": hesitation_score,
            "transition_patterns": transition_patterns,
            "total_navigations": len(patterns),
            "anomalous_navigations": sum(speed_anomalies),
            "average_speed": statistics.mean(speeds)
        }
    
    async def _analyze_temporal_patterns(self, session: BehavioralSession) -> Dict[str, Any]:
        """Analyze temporal patterns in user behavior"""
        all_timestamps = []
        
        # Collect all timestamps
        for touch in session.touch_patterns:
            all_timestamps.append(touch.timestamp)
        for swipe in session.swipe_patterns:
            all_timestamps.append(swipe.timestamp)
        for motion in session.device_motions:
            all_timestamps.append(motion.timestamp)
        
        all_timestamps.sort()
        
        if len(all_timestamps) < 2:
            return {"rhythm_score": 1.0, "burst_patterns": [], "pause_patterns": []}
        
        # Calculate inter-action intervals
        intervals = []
        for i in range(1, len(all_timestamps)):
            interval = (all_timestamps[i] - all_timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        # Analyze rhythm
        rhythm_score = self._calculate_temporal_rhythm(intervals)
        
        # Detect burst patterns
        burst_patterns = self._detect_burst_patterns(intervals)
        
        # Detect pause patterns
        pause_patterns = self._detect_pause_patterns(intervals)
        
        return {
            "rhythm_score": rhythm_score,
            "burst_patterns": burst_patterns,
            "pause_patterns": pause_patterns,
            "average_interval": statistics.mean(intervals),
            "interval_variability": statistics.stdev(intervals) if len(intervals) > 1 else 0.0
        }
    
    async def _analyze_contextual_patterns(self, session: BehavioralSession) -> Dict[str, Any]:
        """Analyze contextual behavioral patterns"""
        # Time-based analysis
        session_hour = session.start_time.hour
        time_context = self._get_time_context(session_hour)
        
        # Location-based analysis (if available)
        location_consistency = self._analyze_location_consistency(session.location_context)
        
        # Network-based analysis
        network_consistency = self._analyze_network_consistency(session.network_context)
        
        # App usage patterns
        app_usage_pattern = self._analyze_app_usage_pattern(session)
        
        return {
            "time_context": time_context,
            "location_consistency": location_consistency,
            "network_consistency": network_consistency,
            "app_usage_pattern": app_usage_pattern,
            "context_anomaly_score": self._calculate_context_anomaly_score(session)
        }
    
    def _calculate_z_scores(self, values: List[float], mean: float, std: float) -> List[float]:
        """Calculate z-scores for a list of values"""
        if std == 0:
            return [0.0] * len(values)
        
        return [(v - mean) / std for v in values]
    
    def _calculate_motion_stability(self, motion: DeviceMotion) -> float:
        """Calculate stability score for a single motion reading"""
        acc_magnitude = (motion.accelerometer_x**2 + motion.accelerometer_y**2 + motion.accelerometer_z**2)**0.5
        gyro_magnitude = (motion.gyroscope_x**2 + motion.gyroscope_y**2 + motion.gyroscope_z**2)**0.5
        
        # Lower magnitude = higher stability
        stability = 1.0 / (1.0 + acc_magnitude + gyro_magnitude)
        return stability
    
    def _calculate_navigation_speed_single(self, pattern: NavigationPattern) -> float:
        """Calculate navigation speed for a single pattern"""
        return 1.0 / max(pattern.duration, 0.1)  # Avoid division by zero
    
    def _analyze_touch_rhythm(self, patterns: List[TouchPattern]) -> float:
        """Analyze rhythm in touch patterns"""
        if len(patterns) < 2:
            return 1.0
        
        timestamps = [p.timestamp for p in patterns]
        intervals = []
        
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        # Calculate rhythm consistency
        if len(intervals) > 1:
            rhythm_consistency = 1.0 - (statistics.stdev(intervals) / max(statistics.mean(intervals), 0.1))
            return max(0.0, min(1.0, rhythm_consistency))
        
        return 1.0
    
    def _detect_pressure_patterns(self, patterns: List[TouchPattern]) -> List[str]:
        """Detect pressure patterns in touch data"""
        if not patterns:
            return []
        
        pressures = [p.pressure for p in patterns]
        detected_patterns = []
        
        # Detect increasing pressure trend
        if len(pressures) > 3:
            trend = np.polyfit(range(len(pressures)), pressures, 1)[0]
            if trend > 0.1:
                detected_patterns.append("increasing_pressure")
            elif trend < -0.1:
                detected_patterns.append("decreasing_pressure")
        
        # Detect pressure spikes
        if len(pressures) > 1:
            mean_pressure = statistics.mean(pressures)
            std_pressure = statistics.stdev(pressures)
            
            spikes = [p for p in pressures if p > mean_pressure + 2 * std_pressure]
            if len(spikes) > len(pressures) * 0.2:
                detected_patterns.append("pressure_spikes")
        
        return detected_patterns
    
    def _calculate_direction_consistency(self, directions: List[str]) -> float:
        """Calculate consistency in swipe directions"""
        if not directions:
            return 1.0
        
        # Count direction frequencies
        direction_counts = {}
        for direction in directions:
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        # Calculate entropy
        total = len(directions)
        entropy = 0.0
        
        for count in direction_counts.values():
            prob = count / total
            entropy -= prob * np.log2(prob)
        
        # Normalize entropy (lower entropy = higher consistency)
        max_entropy = np.log2(len(direction_counts))
        consistency = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0
        
        return consistency
    
    def _calculate_gesture_fluidity(self, patterns: List[SwipePattern]) -> float:
        """Calculate fluidity of swipe gestures"""
        if not patterns:
            return 1.0
        
        fluidity_scores = []
        
        for pattern in patterns:
            # Calculate fluidity based on acceleration consistency
            if pattern.duration > 0:
                fluidity = 1.0 / (1.0 + abs(pattern.acceleration) / pattern.duration)
                fluidity_scores.append(fluidity)
        
        return statistics.mean(fluidity_scores) if fluidity_scores else 1.0
    
    def _analyze_swipe_rhythm(self, patterns: List[SwipePattern]) -> float:
        """Analyze rhythm in swipe patterns"""
        if len(patterns) < 2:
            return 1.0
        
        timestamps = [p.timestamp for p in patterns]
        intervals = []
        
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        # Calculate rhythm consistency
        if len(intervals) > 1:
            rhythm_consistency = 1.0 - (statistics.stdev(intervals) / max(statistics.mean(intervals), 0.1))
            return max(0.0, min(1.0, rhythm_consistency))
        
        return 1.0
    
    def _calculate_shake_intensity(self, motions: List[DeviceMotion]) -> float:
        """Calculate shake intensity from motion data"""
        if not motions:
            return 0.0
        
        shake_scores = []
        
        for motion in motions:
            # Calculate total acceleration magnitude
            acc_magnitude = (motion.accelerometer_x**2 + motion.accelerometer_y**2 + motion.accelerometer_z**2)**0.5
            shake_scores.append(acc_magnitude)
        
        return statistics.mean(shake_scores)
    
    def _analyze_tilt_patterns(self, motions: List[DeviceMotion]) -> Dict[str, float]:
        """Analyze device tilt patterns"""
        if not motions:
            return {"average_tilt": 0.0, "tilt_variability": 0.0}
        
        # Calculate tilt angles (simplified)
        tilt_angles = []
        
        for motion in motions:
            # Calculate tilt based on accelerometer
            tilt_x = np.arctan2(motion.accelerometer_y, motion.accelerometer_z)
            tilt_y = np.arctan2(-motion.accelerometer_x, np.sqrt(motion.accelerometer_y**2 + motion.accelerometer_z**2))
            
            tilt_magnitude = np.sqrt(tilt_x**2 + tilt_y**2)
            tilt_angles.append(tilt_magnitude)
        
        return {
            "average_tilt": statistics.mean(tilt_angles),
            "tilt_variability": statistics.stdev(tilt_angles) if len(tilt_angles) > 1 else 0.0
        }
    
    def _detect_orientation_changes(self, motions: List[DeviceMotion]) -> int:
        """Detect device orientation changes"""
        if len(motions) < 2:
            return 0
        
        orientation_changes = 0
        previous_orientation = None
        
        for motion in motions:
            # Simple orientation detection
            if abs(motion.accelerometer_y) > abs(motion.accelerometer_x):
                current_orientation = "portrait"
            else:
                current_orientation = "landscape"
            
            if previous_orientation and previous_orientation != current_orientation:
                orientation_changes += 1
            
            previous_orientation = current_orientation
        
        return orientation_changes
    
    def _analyze_navigation_flow(self, patterns: List[NavigationPattern]) -> float:
        """Analyze navigation flow consistency"""
        if not patterns:
            return 1.0
        
        # Check sequence consistency
        sequence_consistency = 0.0
        expected_sequence = 1
        
        for pattern in patterns:
            if pattern.sequence_number == expected_sequence:
                sequence_consistency += 1.0
            expected_sequence += 1
        
        return sequence_consistency / len(patterns)
    
    def _detect_hesitation_patterns(self, patterns: List[NavigationPattern]) -> float:
        """Detect hesitation in navigation patterns"""
        if not patterns:
            return 0.0
        
        durations = [p.duration for p in patterns]
        mean_duration = statistics.mean(durations)
        
        # Count long pauses (hesitations)
        hesitations = [d for d in durations if d > mean_duration * 2]
        
        return len(hesitations) / len(patterns)
    
    def _analyze_screen_transitions(self, patterns: List[NavigationPattern]) -> Dict[str, Any]:
        """Analyze screen transition patterns"""
        if not patterns:
            return {"transition_count": 0, "unique_screens": 0}
        
        screens = [p.screen_id for p in patterns]
        unique_screens = len(set(screens))
        
        # Count transitions
        transitions = 0
        for i in range(1, len(screens)):
            if screens[i] != screens[i-1]:
                transitions += 1
        
        return {
            "transition_count": transitions,
            "unique_screens": unique_screens,
            "navigation_efficiency": transitions / max(len(patterns), 1)
        }
    
    def _calculate_temporal_rhythm(self, intervals: List[float]) -> float:
        """Calculate temporal rhythm consistency"""
        if len(intervals) < 2:
            return 1.0
        
        # Calculate rhythm consistency
        rhythm_consistency = 1.0 - (statistics.stdev(intervals) / max(statistics.mean(intervals), 0.1))
        return max(0.0, min(1.0, rhythm_consistency))
    
    def _detect_burst_patterns(self, intervals: List[float]) -> List[Dict[str, Any]]:
        """Detect burst patterns in intervals"""
        if not intervals:
            return []
        
        mean_interval = statistics.mean(intervals)
        burst_threshold = mean_interval * 0.3  # 30% of mean interval
        
        bursts = []
        current_burst = []
        
        for i, interval in enumerate(intervals):
            if interval < burst_threshold:
                current_burst.append(i)
            else:
                if len(current_burst) > 2:  # Minimum 3 actions for a burst
                    bursts.append({
                        "start_index": current_burst[0],
                        "end_index": current_burst[-1],
                        "action_count": len(current_burst),
                        "duration": sum(intervals[current_burst[0]:current_burst[-1]+1])
                    })
                current_burst = []
        
        # Check final burst
        if len(current_burst) > 2:
            bursts.append({
                "start_index": current_burst[0],
                "end_index": current_burst[-1],
                "action_count": len(current_burst),
                "duration": sum(intervals[current_burst[0]:current_burst[-1]+1])
            })
        
        return bursts
    
    def _detect_pause_patterns(self, intervals: List[float]) -> List[Dict[str, Any]]:
        """Detect pause patterns in intervals"""
        if not intervals:
            return []
        
        mean_interval = statistics.mean(intervals)
        pause_threshold = mean_interval * 3.0  # 3x mean interval
        
        pauses = []
        
        for i, interval in enumerate(intervals):
            if interval > pause_threshold:
                pauses.append({
                    "index": i,
                    "duration": interval,
                    "relative_duration": interval / mean_interval
                })
        
        return pauses
    
    def _get_time_context(self, hour: int) -> str:
        """Get time context for behavioral analysis"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _analyze_location_consistency(self, location_context: Optional[str]) -> float:
        """Analyze location consistency"""
        if not location_context:
            return 0.5  # Neutral score
        
        # Simple location consistency scoring
        location_scores = {
            "home": 1.0,
            "work": 0.8,
            "familiar": 0.6,
            "unknown": 0.2
        }
        
        return location_scores.get(location_context, 0.5)
    
    def _analyze_network_consistency(self, network_context: Optional[str]) -> float:
        """Analyze network consistency"""
        if not network_context:
            return 0.5  # Neutral score
        
        # Simple network consistency scoring
        network_scores = {
            "wifi": 1.0,
            "cellular": 0.7,
            "public_wifi": 0.3,
            "unknown": 0.2
        }
        
        return network_scores.get(network_context, 0.5)
    
    def _analyze_app_usage_pattern(self, session: BehavioralSession) -> Dict[str, Any]:
        """Analyze app usage patterns"""
        # Calculate interaction density
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()
            total_interactions = len(session.touch_patterns) + len(session.swipe_patterns)
            
            interaction_density = total_interactions / max(duration, 1)
        else:
            interaction_density = 0.0
        
        # Analyze transaction patterns
        transaction_count = len(session.transaction_patterns)
        transaction_complexity = sum(1 for t in session.transaction_patterns if t.hesitation_count > 0)
        
        return {
            "interaction_density": interaction_density,
            "transaction_count": transaction_count,
            "transaction_complexity": transaction_complexity,
            "session_depth": len(session.navigation_patterns)
        }
    
    def _calculate_context_anomaly_score(self, session: BehavioralSession) -> float:
        """Calculate anomaly score based on context"""
        anomaly_score = 0.0
        
        # Time-based anomaly
        session_hour = session.start_time.hour
        if session_hour < 6 or session_hour > 22:
            anomaly_score += 0.3
        
        # Location-based anomaly
        if session.location_context == "unknown":
            anomaly_score += 0.4
        
        # Network-based anomaly
        if session.network_context == "public_wifi":
            anomaly_score += 0.2
        
        return min(anomaly_score, 1.0)
    
    def _calculate_overall_consistency(self, touch_analysis: Dict, swipe_analysis: Dict, 
                                     motion_analysis: Dict, navigation_analysis: Dict) -> float:
        """Calculate overall behavioral consistency"""
        consistency_scores = []
        
        # Touch consistency
        if touch_analysis.get("pressure_consistency"):
            consistency_scores.append(touch_analysis["pressure_consistency"])
        
        # Swipe consistency
        if swipe_analysis.get("velocity_consistency"):
            consistency_scores.append(swipe_analysis["velocity_consistency"])
        
        # Motion consistency
        if motion_analysis.get("stability_score"):
            consistency_scores.append(motion_analysis["stability_score"])
        
        # Navigation consistency
        if navigation_analysis.get("flow_consistency"):
            consistency_scores.append(navigation_analysis["flow_consistency"])
        
        return statistics.mean(consistency_scores) if consistency_scores else 0.5
    
    def _calculate_behavioral_entropy(self, session: BehavioralSession) -> float:
        """Calculate behavioral entropy"""
        # Collect all behavioral features
        features = create_behavioral_features(session)
        
        if not features:
            return 0.0
        
        # Calculate entropy based on feature diversity
        feature_values = list(features.values())
        
        # Normalize values
        normalized_values = []
        for value in feature_values:
            if isinstance(value, (int, float)):
                normalized_values.append(float(value))
        
        if not normalized_values:
            return 0.0
        
        # Calculate entropy
        entropy = 0.0
        for value in normalized_values:
            if value > 0:
                entropy -= value * np.log2(value)
        
        return entropy / len(normalized_values)
    
    def _calculate_pattern_diversity(self, session: BehavioralSession) -> float:
        """Calculate diversity of behavioral patterns"""
        pattern_types = 0
        
        if session.touch_patterns:
            pattern_types += 1
        if session.swipe_patterns:
            pattern_types += 1
        if session.device_motions:
            pattern_types += 1
        if session.navigation_patterns:
            pattern_types += 1
        if session.transaction_patterns:
            pattern_types += 1
        if session.typing_patterns:
            pattern_types += 1
        
        return pattern_types / 6.0  # Normalize to 0-1
    
    async def _update_baseline(self, user_key: str, session: BehavioralSession, analysis: Dict[str, Any]):
        """Update baseline with new session data"""
        baseline = self.baselines.get(user_key)
        if not baseline:
            return
        
        # Update with exponential moving average
        alpha = 0.1  # Learning rate
        
        # Update touch baseline
        touch_analysis = analysis.get("touch_analysis", {})
        if "average_pressure" in touch_analysis:
            baseline.touch_pressure_mean = (
                alpha * touch_analysis["average_pressure"] + 
                (1 - alpha) * baseline.touch_pressure_mean
            )
        
        # Update swipe baseline
        swipe_analysis = analysis.get("swipe_analysis", {})
        if "average_velocity" in swipe_analysis:
            baseline.swipe_velocity_mean = (
                alpha * swipe_analysis["average_velocity"] + 
                (1 - alpha) * baseline.swipe_velocity_mean
            )
        
        # Update motion baseline
        motion_analysis = analysis.get("motion_analysis", {})
        if "stability_score" in motion_analysis:
            baseline.motion_stability_mean = (
                alpha * motion_analysis["stability_score"] + 
                (1 - alpha) * baseline.motion_stability_mean
            )
        
        # Update navigation baseline
        navigation_analysis = analysis.get("navigation_analysis", {})
        if "average_speed" in navigation_analysis:
            baseline.navigation_speed_mean = (
                alpha * navigation_analysis["average_speed"] + 
                (1 - alpha) * baseline.navigation_speed_mean
            )
        
        baseline.sample_count += 1
        baseline.last_updated = datetime.now()
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Get fallback analysis when processing fails"""
        return {
            "touch_analysis": {"anomaly_score": 0.0, "consistency": 0.5},
            "swipe_analysis": {"anomaly_score": 0.0, "consistency": 0.5},
            "motion_analysis": {"anomaly_score": 0.0, "stability": 0.5},
            "navigation_analysis": {"anomaly_score": 0.0, "consistency": 0.5},
            "temporal_analysis": {"rhythm_score": 0.5},
            "contextual_analysis": {"context_anomaly_score": 0.0},
            "overall_consistency": 0.5,
            "behavioral_entropy": 0.0,
            "session_metadata": {"duration": 0, "interaction_count": 0, "pattern_diversity": 0},
            "error": "Analysis failed"
        }
    
    async def get_real_time_analysis(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Get real-time behavioral analysis"""
        user_key = f"{user_id}_{device_id}"
        
        # Get recent data from buffers
        touch_buffer = list(self.real_time_buffers.get(f"{user_key}_touch", []))
        swipe_buffer = list(self.real_time_buffers.get(f"{user_key}_swipe", []))
        
        if not touch_buffer and not swipe_buffer:
            return {"status": "no_data", "analysis": {}}
        
        # Analyze recent patterns
        recent_analysis = {}
        
        if touch_buffer:
            recent_pressures = [t["pressure"] for t in touch_buffer[-10:]]  # Last 10 touches
            recent_analysis["touch_trend"] = {
                "average_pressure": statistics.mean(recent_pressures),
                "pressure_variability": statistics.stdev(recent_pressures) if len(recent_pressures) > 1 else 0.0,
                "sample_count": len(recent_pressures)
            }
        
        if swipe_buffer:
            recent_velocities = [s["velocity"] for s in swipe_buffer[-10:]]  # Last 10 swipes
            recent_analysis["swipe_trend"] = {
                "average_velocity": statistics.mean(recent_velocities),
                "velocity_variability": statistics.stdev(recent_velocities) if len(recent_velocities) > 1 else 0.0,
                "sample_count": len(recent_velocities)
            }
        
        return {
            "status": "active",
            "analysis": recent_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get behavioral analyzer service metrics"""
        return {
            "analysis_count": self.analysis_count,
            "anomaly_detection_count": self.anomaly_detection_count,
            "false_positive_count": self.false_positive_count,
            "active_baselines": len(self.baselines),
            "active_buffers": len(self.real_time_buffers),
            "accuracy_rate": 1.0 - (self.false_positive_count / max(self.analysis_count, 1))
        }
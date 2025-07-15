"""
Behavioral Models for NETHRA System
Defines data structures for behavioral analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import json

class BehaviorType(str, Enum):
    """Types of behavioral patterns"""
    TOUCH = "touch"
    SWIPE = "swipe"
    TAP = "tap"
    DEVICE_MOTION = "device_motion"
    NAVIGATION = "navigation"
    TRANSACTION = "transaction"
    TYPING = "typing"

class TouchPattern(BaseModel):
    """Touch pattern data structure"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    pressure: float = Field(..., description="Touch pressure")
    duration: float = Field(..., description="Touch duration in ms")
    timestamp: datetime = Field(default_factory=datetime.now)

class SwipePattern(BaseModel):
    """Swipe gesture pattern"""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    velocity: float
    acceleration: float
    duration: float
    direction: str
    timestamp: datetime = Field(default_factory=datetime.now)

class DeviceMotion(BaseModel):
    """Device motion sensor data"""
    accelerometer_x: float
    accelerometer_y: float
    accelerometer_z: float
    gyroscope_x: float
    gyroscope_y: float
    gyroscope_z: float
    magnetometer_x: Optional[float] = None
    magnetometer_y: Optional[float] = None
    magnetometer_z: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class NavigationPattern(BaseModel):
    """User navigation behavior"""
    screen_id: str
    action: str
    duration: float
    sequence_number: int
    timestamp: datetime = Field(default_factory=datetime.now)

class TransactionPattern(BaseModel):
    """Transaction behavior pattern"""
    transaction_type: str
    amount: Optional[float] = None
    recipient_type: str
    time_to_complete: float
    hesitation_count: int
    timestamp: datetime = Field(default_factory=datetime.now)

class TypingPattern(BaseModel):
    """Typing behavior pattern"""
    key_intervals: List[float]
    dwell_times: List[float]
    pressure_variations: List[float]
    accuracy_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)

class BehavioralSession(BaseModel):
    """Complete behavioral session data"""
    session_id: str
    user_id: str
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Behavioral patterns
    touch_patterns: List[TouchPattern] = []
    swipe_patterns: List[SwipePattern] = []
    device_motions: List[DeviceMotion] = []
    navigation_patterns: List[NavigationPattern] = []
    transaction_patterns: List[TransactionPattern] = []
    typing_patterns: List[TypingPattern] = []
    
    # Computed features
    behavioral_features: Dict[str, Any] = {}
    anomaly_scores: Dict[str, float] = {}
    trust_score: float = 100.0
    
    # Context
    app_version: str
    device_model: str
    os_version: str
    location_context: Optional[str] = None
    network_context: Optional[str] = None

class TrustProfile(BaseModel):
    """User's trust profile"""
    user_id: str
    device_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Baseline behavioral patterns
    baseline_features: Dict[str, Any] = {}
    
    # Adaptive thresholds
    touch_threshold: float = 0.15
    swipe_threshold: float = 0.20
    motion_threshold: float = 0.25
    navigation_threshold: float = 0.10
    transaction_threshold: float = 0.30
    
    # Trust scoring parameters
    base_trust: float = 100.0
    decay_rate: float = 0.95
    recovery_rate: float = 1.02
    
    # Learning parameters
    adaptation_rate: float = 0.1
    min_samples: int = 50
    max_samples: int = 1000
    
    # Historical data
    session_count: int = 0
    total_interactions: int = 0
    anomaly_count: int = 0
    false_positive_count: int = 0

class AnomalyDetection(BaseModel):
    """Anomaly detection result"""
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Anomaly details
    anomaly_type: BehaviorType
    anomaly_score: float
    threshold: float
    is_anomaly: bool
    
    # Context
    feature_deviations: Dict[str, float] = {}
    confidence_level: float
    
    # Response
    recommended_action: str
    risk_level: str  # low, medium, high, critical

class MirageSession(BaseModel):
    """Mirage interface session"""
    session_id: str
    user_id: str
    device_id: str
    activated_at: datetime = Field(default_factory=datetime.now)
    deactivated_at: Optional[datetime] = None
    
    # Mirage configuration
    mirage_type: str
    deception_level: int  # 1-5
    cognitive_challenges: List[str] = []
    
    # Interaction tracking
    attacker_actions: List[Dict[str, Any]] = []
    challenge_responses: List[Dict[str, Any]] = []
    
    # Outcome
    attack_defeated: bool = False
    legitimate_user_recovered: bool = False
    duration: Optional[float] = None

class TamperAttempt(BaseModel):
    """Tamper detection event"""
    session_id: str
    user_id: str
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Tamper details
    tamper_type: str
    severity: str  # low, medium, high, critical
    indicators: List[str] = []
    
    # System response
    action_taken: str
    auto_lock_triggered: bool = False
    
    # Context
    app_integrity: bool = True
    device_rooted: bool = False
    suspicious_processes: List[str] = []

class CognitiveChallenge(BaseModel):
    """Cognitive challenge for user verification"""
    challenge_id: str
    challenge_type: str
    difficulty: int  # 1-5
    question: str
    options: Optional[List[str]] = None
    expected_pattern: Optional[str] = None
    timeout: int = 30  # seconds
    
    # Response tracking
    response_time: Optional[float] = None
    response_accuracy: Optional[float] = None
    behavioral_consistency: Optional[float] = None
    
    # Result
    passed: bool = False
    confidence: float = 0.0

class PrivacyMetrics(BaseModel):
    """Privacy compliance metrics"""
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Data minimization
    data_collected: Dict[str, int] = {}
    data_processed: Dict[str, int] = {}
    data_retained: Dict[str, int] = {}
    
    # Processing location
    on_device_processing: float = 100.0  # percentage
    cloud_processing: float = 0.0  # percentage
    
    # Anonymization
    anonymized_data: Dict[str, int] = {}
    pseudonymized_data: Dict[str, int] = {}
    
    # Compliance
    gdpr_compliant: bool = True
    dpdp_compliant: bool = True
    consent_recorded: bool = True
    
    # Performance
    processing_time: float
    memory_usage: float
    battery_impact: float

# Utility functions
def create_behavioral_features(session: BehavioralSession) -> Dict[str, Any]:
    """Extract behavioral features from session data"""
    features = {}
    
    # Touch features
    if session.touch_patterns:
        touches = session.touch_patterns
        features.update({
            "avg_touch_pressure": sum(t.pressure for t in touches) / len(touches),
            "avg_touch_duration": sum(t.duration for t in touches) / len(touches),
            "touch_variability": calculate_variability([t.pressure for t in touches]),
            "touch_frequency": len(touches) / (session.end_time - session.start_time).total_seconds() if session.end_time else 0
        })
    
    # Swipe features
    if session.swipe_patterns:
        swipes = session.swipe_patterns
        features.update({
            "avg_swipe_velocity": sum(s.velocity for s in swipes) / len(swipes),
            "avg_swipe_acceleration": sum(s.acceleration for s in swipes) / len(swipes),
            "swipe_direction_consistency": calculate_direction_consistency(swipes),
            "swipe_rhythm": calculate_rhythm([s.timestamp for s in swipes])
        })
    
    # Device motion features
    if session.device_motions:
        motions = session.device_motions
        features.update({
            "device_stability": calculate_stability(motions),
            "motion_intensity": calculate_motion_intensity(motions),
            "orientation_preference": calculate_orientation_preference(motions)
        })
    
    # Navigation features
    if session.navigation_patterns:
        nav = session.navigation_patterns
        features.update({
            "navigation_speed": calculate_navigation_speed(nav),
            "screen_dwell_time": calculate_dwell_time(nav),
            "navigation_pattern": calculate_navigation_pattern(nav)
        })
    
    return features

def calculate_variability(values: List[float]) -> float:
    """Calculate coefficient of variation"""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    return std_dev / mean if mean > 0 else 0.0

def calculate_direction_consistency(swipes: List[SwipePattern]) -> float:
    """Calculate consistency of swipe directions"""
    if not swipes:
        return 1.0
    
    directions = [s.direction for s in swipes]
    unique_directions = set(directions)
    
    # Calculate entropy
    entropy = 0.0
    for direction in unique_directions:
        prob = directions.count(direction) / len(directions)
        entropy -= prob * (prob.bit_length() - 1) if prob > 0 else 0
    
    return 1.0 - (entropy / 4.0)  # Normalize to 0-1

def calculate_rhythm(timestamps: List[datetime]) -> float:
    """Calculate rhythm consistency"""
    if len(timestamps) < 2:
        return 1.0
    
    intervals = []
    for i in range(1, len(timestamps)):
        interval = (timestamps[i] - timestamps[i-1]).total_seconds()
        intervals.append(interval)
    
    return 1.0 - calculate_variability(intervals)

def calculate_stability(motions: List[DeviceMotion]) -> float:
    """Calculate device stability score"""
    if not motions:
        return 1.0
    
    # Calculate average acceleration magnitude
    acc_magnitudes = []
    for motion in motions:
        magnitude = (motion.accelerometer_x**2 + motion.accelerometer_y**2 + motion.accelerometer_z**2)**0.5
        acc_magnitudes.append(magnitude)
    
    # Lower variability = higher stability
    return 1.0 - min(calculate_variability(acc_magnitudes), 1.0)

def calculate_motion_intensity(motions: List[DeviceMotion]) -> float:
    """Calculate motion intensity"""
    if not motions:
        return 0.0
    
    total_intensity = 0.0
    for motion in motions:
        acc_intensity = (motion.accelerometer_x**2 + motion.accelerometer_y**2 + motion.accelerometer_z**2)**0.5
        gyro_intensity = (motion.gyroscope_x**2 + motion.gyroscope_y**2 + motion.gyroscope_z**2)**0.5
        total_intensity += acc_intensity + gyro_intensity
    
    return total_intensity / len(motions)

def calculate_orientation_preference(motions: List[DeviceMotion]) -> str:
    """Calculate preferred device orientation"""
    if not motions:
        return "unknown"
    
    # Simple orientation detection based on accelerometer
    portrait_count = sum(1 for m in motions if abs(m.accelerometer_y) > abs(m.accelerometer_x))
    landscape_count = len(motions) - portrait_count
    
    return "portrait" if portrait_count > landscape_count else "landscape"

def calculate_navigation_speed(nav_patterns: List[NavigationPattern]) -> float:
    """Calculate navigation speed"""
    if len(nav_patterns) < 2:
        return 0.0
    
    total_duration = sum(p.duration for p in nav_patterns)
    return len(nav_patterns) / total_duration if total_duration > 0 else 0.0

def calculate_dwell_time(nav_patterns: List[NavigationPattern]) -> float:
    """Calculate average screen dwell time"""
    if not nav_patterns:
        return 0.0
    
    return sum(p.duration for p in nav_patterns) / len(nav_patterns)

def calculate_navigation_pattern(nav_patterns: List[NavigationPattern]) -> str:
    """Calculate navigation pattern type"""
    if not nav_patterns:
        return "unknown"
    
    # Simple pattern detection
    sequential_count = 0
    for i in range(1, len(nav_patterns)):
        if nav_patterns[i].sequence_number == nav_patterns[i-1].sequence_number + 1:
            sequential_count += 1
    
    sequential_ratio = sequential_count / max(len(nav_patterns) - 1, 1)
    
    if sequential_ratio > 0.8:
        return "sequential"
    elif sequential_ratio > 0.4:
        return "mixed"
    else:
        return "random"
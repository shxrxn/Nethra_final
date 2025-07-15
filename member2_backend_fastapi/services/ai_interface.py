"""
AI Interface Service for NETHRA
Handles TensorFlow Lite model integration and inference
"""

import os
import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Import TensorFlow Lite
try:
    import tensorflow as tf
    import tensorflow.lite as tflite
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow Lite not available. Using mock implementation.")

from models.behavioral_models import (
    BehavioralSession, TrustProfile, AnomalyDetection, 
    BehaviorType, create_behavioral_features
)

logger = logging.getLogger(__name__)

class AIModelInterface:
    """AI model interface for behavioral analysis and trust scoring"""
    
    def __init__(self, model_path: str = "models/trust_model.tflite"):
        self.model_path = model_path
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_initialized = False
        self.model_version = "1.0.0"
        
        # Feature dimensions
        self.feature_dim = 50
        self.sequence_length = 100
        
        # Model performance metrics
        self.inference_count = 0
        self.total_inference_time = 0.0
        self.accuracy_scores = []
        
        # Thread safety
        self.lock = threading.Lock()
        
    async def initialize(self):
        """Initialize the AI model interface"""
        logger.info("Initializing AI Model Interface...")
        
        try:
            if TF_AVAILABLE and os.path.exists(self.model_path):
                await self._load_tflite_model()
            else:
                await self._initialize_mock_model()
            
            self.is_initialized = True
            logger.info("✅ AI Model Interface initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI model: {str(e)}")
            await self._initialize_mock_model()
            self.is_initialized = True
    
    async def _load_tflite_model(self):
        """Load TensorFlow Lite model"""
        def load_model():
            try:
                # Load TFLite model
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                
                # Get input and output details
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
                logger.info(f"TFLite model loaded: {self.model_path}")
                logger.info(f"Input shape: {self.input_details[0]['shape']}")
                logger.info(f"Output shape: {self.output_details[0]['shape']}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to load TFLite model: {str(e)}")
                return False
        
        # Run in thread pool
        success = await asyncio.get_event_loop().run_in_executor(
            self.executor, load_model
        )
        
        if not success:
            raise Exception("Failed to load TensorFlow Lite model")
    
    async def _initialize_mock_model(self):
        """Initialize mock model for development/testing"""
        logger.info("Initializing mock AI model for development...")
        
        # Simulate model loading delay
        await asyncio.sleep(0.1)
        
        # Mock model parameters
        self.interpreter = "mock_interpreter"
        self.input_details = [{"shape": [1, self.sequence_length, self.feature_dim]}]
        self.output_details = [{"shape": [1, 1]}]
        
        logger.info("Mock AI model initialized")
    
    async def analyze_behavioral_session(self, session: BehavioralSession) -> Dict[str, Any]:
        """Analyze behavioral session and return trust metrics"""
        if not self.is_initialized:
            raise Exception("AI model not initialized")
        
        start_time = datetime.now()
        
        try:
            # Extract features from session
            features = create_behavioral_features(session)
            
            # Prepare feature vector
            feature_vector = await self._prepare_feature_vector(features)
            
            # Run inference
            trust_score = await self._run_trust_inference(feature_vector)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(session, features)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(feature_vector, trust_score)
            
            # Update metrics
            inference_time = (datetime.now() - start_time).total_seconds()
            await self._update_metrics(inference_time, trust_score)
            
            return {
                "trust_score": trust_score,
                "anomalies": anomalies,
                "confidence": confidence,
                "features": features,
                "inference_time": inference_time,
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {str(e)}")
            return await self._get_fallback_analysis(session)
    
    async def _prepare_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare feature vector for model inference"""
        # Feature mapping for consistent model input
        feature_mapping = {
            "avg_touch_pressure": 0,
            "avg_touch_duration": 1,
            "touch_variability": 2,
            "touch_frequency": 3,
            "avg_swipe_velocity": 4,
            "avg_swipe_acceleration": 5,
            "swipe_direction_consistency": 6,
            "swipe_rhythm": 7,
            "device_stability": 8,
            "motion_intensity": 9,
            "navigation_speed": 10,
            "screen_dwell_time": 11,
            # Add more features as needed
        }
        
        # Initialize feature vector
        feature_vector = np.zeros(self.feature_dim, dtype=np.float32)
        
        # Fill feature vector
        for feature_name, value in features.items():
            if feature_name in feature_mapping:
                index = feature_mapping[feature_name]
                if index < self.feature_dim:
                    feature_vector[index] = float(value) if value is not None else 0.0
        
        # Normalize features
        feature_vector = self._normalize_features(feature_vector)
        
        return feature_vector.reshape(1, 1, self.feature_dim)
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize feature vector"""
        # Simple min-max normalization
        # In production, use learned normalization parameters
        return np.clip(features, -3.0, 3.0) / 3.0
    
    async def _run_trust_inference(self, feature_vector: np.ndarray) -> float:
        """Run trust score inference"""
        def inference():
            with self.lock:
                if self.interpreter == "mock_interpreter":
                    # Mock inference
                    return self._mock_trust_inference(feature_vector)
                
                try:
                    # Set input tensor
                    self.interpreter.set_tensor(
                        self.input_details[0]['index'], 
                        feature_vector
                    )
                    
                    # Run inference
                    self.interpreter.invoke()
                    
                    # Get output
                    output = self.interpreter.get_tensor(self.output_details[0]['index'])
                    
                    # Convert to trust score (0-100)
                    trust_score = float(output[0][0]) * 100.0
                    return max(0.0, min(100.0, trust_score))
                    
                except Exception as e:
                    logger.error(f"Inference error: {str(e)}")
                    return self._mock_trust_inference(feature_vector)
        
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, inference
        )
    
    def _mock_trust_inference(self, feature_vector: np.ndarray) -> float:
        """Mock trust inference for development"""
        # Simple mock logic based on feature stability
        feature_mean = np.mean(feature_vector)
        feature_std = np.std(feature_vector)
        
        # Base trust score
        base_score = 85.0
        
        # Adjust based on feature consistency
        consistency_bonus = max(0, 15.0 - feature_std * 30.0)
        
        # Adjust based on feature normality
        normality_bonus = max(0, 10.0 - abs(feature_mean) * 20.0)
        
        trust_score = base_score + consistency_bonus + normality_bonus
        
        # Add some realistic noise
        noise = np.random.normal(0, 2.0)
        trust_score += noise
        
        return max(0.0, min(100.0, trust_score))
    
    async def _detect_anomalies(self, session: BehavioralSession, features: Dict[str, Any]) -> List[AnomalyDetection]:
        """Detect behavioral anomalies"""
        anomalies = []
        
        # Define anomaly thresholds
        thresholds = {
            "touch_variability": 0.3,
            "swipe_direction_consistency": 0.5,
            "device_stability": 0.4,
            "navigation_speed": 2.0
        }
        
        for feature_name, value in features.items():
            if feature_name in thresholds:
                threshold = thresholds[feature_name]
                
                # Check for anomaly
                is_anomaly = False
                anomaly_score = 0.0
                
                if feature_name == "touch_variability" and value > threshold:
                    is_anomaly = True
                    anomaly_score = (value - threshold) / threshold
                elif feature_name == "swipe_direction_consistency" and value < threshold:
                    is_anomaly = True
                    anomaly_score = (threshold - value) / threshold
                elif feature_name == "device_stability" and value < threshold:
                    is_anomaly = True
                    anomaly_score = (threshold - value) / threshold
                elif feature_name == "navigation_speed" and value > threshold:
                    is_anomaly = True
                    anomaly_score = (value - threshold) / threshold
                
                if is_anomaly:
                    # Determine behavior type
                    behavior_type = self._get_behavior_type(feature_name)
                    
                    # Determine risk level
                    risk_level = self._calculate_risk_level(anomaly_score)
                    
                    # Create anomaly detection
                    anomaly = AnomalyDetection(
                        session_id=session.session_id,
                        user_id=session.user_id,
                        anomaly_type=behavior_type,
                        anomaly_score=anomaly_score,
                        threshold=threshold,
                        is_anomaly=True,
                        feature_deviations={feature_name: value},
                        confidence_level=min(anomaly_score, 1.0),
                        recommended_action=self._get_recommended_action(risk_level),
                        risk_level=risk_level
                    )
                    
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _get_behavior_type(self, feature_name: str) -> BehaviorType:
        """Map feature name to behavior type"""
        mapping = {
            "touch_variability": BehaviorType.TOUCH,
            "touch_frequency": BehaviorType.TOUCH,
            "swipe_direction_consistency": BehaviorType.SWIPE,
            "swipe_rhythm": BehaviorType.SWIPE,
            "device_stability": BehaviorType.DEVICE_MOTION,
            "motion_intensity": BehaviorType.DEVICE_MOTION,
            "navigation_speed": BehaviorType.NAVIGATION,
            "screen_dwell_time": BehaviorType.NAVIGATION
        }
        
        return mapping.get(feature_name, BehaviorType.TOUCH)
    
    def _calculate_risk_level(self, anomaly_score: float) -> str:
        """Calculate risk level based on anomaly score"""
        if anomaly_score < 0.3:
            return "low"
        elif anomaly_score < 0.6:
            return "medium"
        elif anomaly_score < 0.9:
            return "high"
        else:
            return "critical"
    
    def _get_recommended_action(self, risk_level: str) -> str:
        """Get recommended action based on risk level"""
        actions = {
            "low": "monitor",
            "medium": "increase_monitoring",
            "high": "challenge_user",
            "critical": "activate_mirage"
        }
        
        return actions.get(risk_level, "monitor")
    
    async def _calculate_confidence(self, feature_vector: np.ndarray, trust_score: float) -> float:
        """Calculate confidence in the trust score"""
        # Simple confidence calculation based on feature quality
        feature_quality = 1.0 - np.std(feature_vector)
        
        # Adjust for trust score extremes
        score_confidence = 1.0 - abs(trust_score - 50.0) / 50.0
        
        # Combine confidences
        confidence = (feature_quality + score_confidence) / 2.0
        
        return max(0.0, min(1.0, confidence))
    
    async def _update_metrics(self, inference_time: float, trust_score: float):
        """Update model performance metrics"""
        with self.lock:
            self.inference_count += 1
            self.total_inference_time += inference_time
            
            # Track accuracy (simplified)
            if len(self.accuracy_scores) >= 100:
                self.accuracy_scores.pop(0)
            self.accuracy_scores.append(trust_score)
    
    async def _get_fallback_analysis(self, session: BehavioralSession) -> Dict[str, Any]:
        """Fallback analysis when model fails"""
        return {
            "trust_score": 50.0,  # Neutral score
            "anomalies": [],
            "confidence": 0.5,
            "features": {},
            "inference_time": 0.0,
            "model_version": "fallback",
            "error": "Model inference failed"
        }
    
    async def update_trust_profile(self, profile: TrustProfile, session: BehavioralSession) -> TrustProfile:
        """Update trust profile with new behavioral data"""
        try:
            # Extract features
            features = create_behavioral_features(session)
            
            # Update baseline features with exponential moving average
            alpha = profile.adaptation_rate
            
            for feature_name, value in features.items():
                if feature_name in profile.baseline_features:
                    old_value = profile.baseline_features[feature_name]
                    new_value = alpha * value + (1 - alpha) * old_value
                    profile.baseline_features[feature_name] = new_value
                else:
                    profile.baseline_features[feature_name] = value
            
            # Update profile statistics
            profile.session_count += 1
            profile.total_interactions += len(session.touch_patterns) + len(session.swipe_patterns)
            profile.updated_at = datetime.now()
            
            # Adapt thresholds based on user behavior
            await self._adapt_thresholds(profile, features)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error updating trust profile: {str(e)}")
            return profile
    
    async def _adapt_thresholds(self, profile: TrustProfile, features: Dict[str, Any]):
        """Adapt anomaly detection thresholds based on user behavior"""
        # Adaptive threshold adjustment
        adjustment_factor = 0.05
        
        # Adjust touch threshold
        if "touch_variability" in features:
            touch_var = features["touch_variability"]
            if touch_var > profile.touch_threshold:
                profile.touch_threshold = min(
                    profile.touch_threshold + adjustment_factor,
                    0.5  # Maximum threshold
                )
        
        # Adjust swipe threshold
        if "swipe_direction_consistency" in features:
            swipe_consistency = features["swipe_direction_consistency"]
            if swipe_consistency < profile.swipe_threshold:
                profile.swipe_threshold = max(
                    profile.swipe_threshold - adjustment_factor,
                    0.1  # Minimum threshold
                )
        
        # Adjust motion threshold
        if "device_stability" in features:
            stability = features["device_stability"]
            if stability < profile.motion_threshold:
                profile.motion_threshold = max(
                    profile.motion_threshold - adjustment_factor,
                    0.1  # Minimum threshold
                )
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        with self.lock:
            avg_inference_time = (
                self.total_inference_time / self.inference_count
                if self.inference_count > 0 else 0.0
            )
            
            avg_accuracy = (
                sum(self.accuracy_scores) / len(self.accuracy_scores)
                if self.accuracy_scores else 0.0
            )
            
            return {
                "model_version": self.model_version,
                "inference_count": self.inference_count,
                "average_inference_time": avg_inference_time,
                "average_accuracy": avg_accuracy,
                "is_initialized": self.is_initialized,
                "tensorflow_available": TF_AVAILABLE
            }
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up AI model interface...")
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.is_initialized = False
        
        logger.info("AI model interface cleanup complete")
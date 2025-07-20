"""
AI Interface Service - Manages TensorFlow Lite model interactions
"""

import numpy as np
import tensorflow as tf
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AIInterface:
    """Interface for AI model operations"""
    
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize TensorFlow Lite interpreter"""
        try:
            if not self.model_path.exists():
                # Create a dummy model for demo purposes
                self._create_dummy_model()
            
            self.interpreter = tf.lite.Interpreter(model_path=str(self.model_path))
            self.interpreter.allocate_tensors()
            
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            logger.info(f"AI model initialized successfully from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {str(e)}")
            self._create_dummy_model()
    
    def _create_dummy_model(self):
        """Create a dummy model for demonstration"""
        try:
            # Import and create sample model
            import sys
            import os
            
            # Add the project root to Python path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            try:
                from models.create_sample_model import create_sample_trust_model
                
                logger.info("Creating sample AI model...")
                model_path = create_sample_trust_model()
                
                if model_path:
                    self.model_path = Path(model_path)
                    logger.info("Sample AI model created successfully")
                    # Re-initialize with the new model
                    self._initialize_model()
                else:
                    logger.error("Failed to create sample model")
            except ImportError as e:
                logger.error(f"Could not import sample model creator: {str(e)}")
                # Create a minimal dummy model file
                self._create_minimal_dummy()
            
        except Exception as e:
            logger.error(f"Failed to create dummy model: {str(e)}")
            self._create_minimal_dummy()
    
    def _create_minimal_dummy(self):
        """Create minimal dummy model if TensorFlow is not available"""
        try:
            # Create a dummy model file (just for testing)
            dummy_model = b'\x00' * 1024  # 1KB dummy data
            
            model_dir = self.model_path.parent
            model_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                f.write(dummy_model)
            
            logger.info(f"Created minimal dummy model at {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to create minimal dummy model: {str(e)}")
    async def predict_trust_score(self, behavioral_features: np.ndarray) -> float:
        """Predict trust score from behavioral features"""
        try:
            # Run inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            trust_score = await loop.run_in_executor(
                self.executor,
                self._run_inference,
                behavioral_features
            )
            
            return float(trust_score)
            
        except Exception as e:
            logger.error(f"Trust score prediction failed: {str(e)}")
            # Return default medium trust score
            return 75.0
    
    def _run_inference(self, features: np.ndarray) -> float:
        """Run model inference"""
        try:
            # Ensure features are in correct shape
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Pad or truncate features to match model input
            expected_shape = self.input_details[0]['shape']
            if features.shape[1] < expected_shape[1]:
                # Pad with zeros
                padding = np.zeros((features.shape[0], expected_shape[1] - features.shape[1]))
                features = np.concatenate([features, padding], axis=1)
            elif features.shape[1] > expected_shape[1]:
                # Truncate
                features = features[:, :expected_shape[1]]
            
            # Set input tensor
            self.interpreter.set_tensor(
                self.input_details[0]['index'],
                features.astype(np.float32)
            )
            
            # Run inference
            self.interpreter.invoke()
            
            # Get output
            output = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            # Convert to trust score (0-100)
            trust_score = float(output[0][0]) * 100
            
            return max(0.0, min(100.0, trust_score))
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            return 75.0
    
    async def detect_anomalies(self, behavioral_features: np.ndarray) -> List[str]:
        """Detect behavioral anomalies"""
        try:
            # Simplified anomaly detection logic
            anomalies = []
            
            # Check for statistical anomalies
            if np.std(behavioral_features) > 2.0:
                anomalies.append("HIGH_VARIANCE_BEHAVIOR")
            
            if np.mean(behavioral_features) < 0.3:
                anomalies.append("UNUSUAL_INTERACTION_PATTERN")
            
            # Check for specific behavioral patterns
            if len(behavioral_features) > 10:
                recent_behavior = behavioral_features[-10:]
                if np.all(recent_behavior < 0.5):
                    anomalies.append("CONSISTENTLY_UNUSUAL_BEHAVIOR")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []
    
    async def extract_behavioral_features(self, behavioral_data: Dict) -> np.ndarray:
        """Extract features from behavioral data"""
        try:
            features = []
            
            # Touch pattern features
            touch_patterns = behavioral_data.get('touch_patterns', [])
            if touch_patterns:
                # Extract timing features
                touch_times = [p.get('timestamp', 0) for p in touch_patterns]
                if len(touch_times) > 1:
                    time_intervals = np.diff(touch_times)
                    features.extend([
                        np.mean(time_intervals),
                        np.std(time_intervals),
                        np.max(time_intervals),
                        np.min(time_intervals)
                    ])
                else:
                    features.extend([0.0, 0.0, 0.0, 0.0])
                
                # Extract pressure features
                pressures = [p.get('pressure', 0.5) for p in touch_patterns]
                features.extend([
                    np.mean(pressures),
                    np.std(pressures),
                    np.max(pressures),
                    np.min(pressures)
                ])
                
                # Extract coordinate features
                x_coords = [p.get('x', 0) for p in touch_patterns]
                y_coords = [p.get('y', 0) for p in touch_patterns]
                features.extend([
                    np.mean(x_coords),
                    np.std(x_coords),
                    np.mean(y_coords),
                    np.std(y_coords)
                ])
            else:
                features.extend([0.0] * 12)
            
            # Swipe pattern features
            swipe_patterns = behavioral_data.get('swipe_patterns', [])
            if swipe_patterns:
                # Extract velocity features
                velocities = [s.get('velocity', 0) for s in swipe_patterns]
                features.extend([
                    np.mean(velocities),
                    np.std(velocities),
                    np.max(velocities),
                    np.min(velocities)
                ])
                
                # Extract direction features
                directions = [s.get('direction', 0) for s in swipe_patterns]
                features.extend([
                    np.mean(directions),
                    np.std(directions)
                ])
            else:
                features.extend([0.0] * 6)
            
            # Device motion features
            device_motion = behavioral_data.get('device_motion', {})
            features.extend([
                device_motion.get('accelerometer_x', 0),
                device_motion.get('accelerometer_y', 0),
                device_motion.get('accelerometer_z', 0),
                device_motion.get('gyroscope_x', 0),
                device_motion.get('gyroscope_y', 0),
                device_motion.get('gyroscope_z', 0)
            ])
            
            # App usage features
            app_usage = behavioral_data.get('app_usage', {})
            features.extend([
                app_usage.get('session_duration', 0),
                app_usage.get('screen_transitions', 0),
                app_usage.get('button_clicks', 0),
                app_usage.get('scroll_events', 0)
            ])
            
            # Network and location features
            network_info = behavioral_data.get('network_info', {})
            features.extend([
                1.0 if network_info.get('wifi_connected', False) else 0.0,
                network_info.get('signal_strength', 0),
                network_info.get('network_type', 0)
            ])
            
            location_context = behavioral_data.get('location_context', {})
            features.extend([
                location_context.get('is_home_location', 0),
                location_context.get('is_work_location', 0),
                location_context.get('location_confidence', 0)
            ])
            
            # Pad features to ensure we have exactly 50 features
            while len(features) < 50:
                features.append(0.0)
            
            return np.array(features[:50])
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return np.zeros(50)
    
    async def calculate_risk_level(self, trust_score: float, anomalies: List[str]) -> str:
        """Calculate risk level based on trust score and anomalies"""
        try:
            if trust_score >= 80 and len(anomalies) == 0:
                return "LOW"
            elif trust_score >= 60 and len(anomalies) <= 1:
                return "MEDIUM"
            elif trust_score >= 40 and len(anomalies) <= 2:
                return "HIGH"
            else:
                return "CRITICAL"
                
        except Exception as e:
            logger.error(f"Risk level calculation failed: {str(e)}")
            return "MEDIUM"
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        try:
            return {
                "model_path": str(self.model_path),
                "input_shape": self.input_details[0]['shape'] if self.input_details else None,
                "output_shape": self.output_details[0]['shape'] if self.output_details else None,
                "model_size": self.model_path.stat().st_size if self.model_path.exists() else 0
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {str(e)}")
            return {}
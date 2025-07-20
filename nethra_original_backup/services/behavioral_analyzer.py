"""
Behavioral Analyzer Service - Analyzes user behavior patterns
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from services.ai_interface import AIInterface

logger = logging.getLogger(__name__)

class BehavioralAnalyzer:
    """Service for analyzing user behavioral patterns"""
    
    def __init__(self, ai_interface: AIInterface, db_manager, cache_service):
        self.ai_interface = ai_interface
        self.db_manager = db_manager
        self.cache_service = cache_service
        self.baseline_window = timedelta(hours=24)
        self.anomaly_threshold = 0.3
        self.learning_rate = 0.1
        self.memory_store = {}
    
    async def analyze_behavior(self, behavioral_data) -> object:
        """Analyze behavioral data and return trust assessment"""
        try:
            # Extract features from behavioral data
            features = await self.ai_interface.extract_behavioral_features(
                behavioral_data.dict()
            )
            
            # Get or create user baseline
            user_baseline = await self._get_user_baseline(behavioral_data.user_id)
            
            # Calculate deviation from baseline
            deviation_score = await self._calculate_deviation(features, user_baseline)
            
            # Get AI prediction
            ai_trust_score = await self.ai_interface.predict_trust_score(features)
            
            # Detect anomalies
            anomalies = await self._detect_behavioral_anomalies(
                behavioral_data.dict(),
                user_baseline
            )
            
            # Calculate final trust score
            final_trust_score = await self._calculate_final_trust_score(
                ai_trust_score,
                deviation_score,
                anomalies
            )
            
            # Determine risk level
            risk_level = await self.ai_interface.calculate_risk_level(
                final_trust_score,
                anomalies
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                final_trust_score,
                anomalies,
                risk_level
            )
            
            # Update user baseline
            await self._update_user_baseline(
                behavioral_data.user_id,
                features,
                final_trust_score
            )
            
            # Store behavioral analysis
            await self._store_behavioral_analysis(
                behavioral_data.user_id,
                behavioral_data.session_id,
                {
                    "trust_score": final_trust_score,
                    "deviation_score": deviation_score,
                    "anomalies": anomalies,
                    "features": features.tolist()
                }
            )
            
            # Create response object
            from main import TrustScoreResponse
            return TrustScoreResponse(
                trust_index=final_trust_score,
                risk_level=risk_level,
                behavioral_anomalies=anomalies,
                recommended_actions=recommendations,
                session_valid=final_trust_score > 40,
                mirage_active=False
            )
            
        except Exception as e:
            logger.error(f"Behavioral analysis failed: {str(e)}")
            # Return default response
            from main import TrustScoreResponse
            return TrustScoreResponse(
                trust_index=50.0,
                risk_level="MEDIUM",
                behavioral_anomalies=["ANALYSIS_ERROR"],
                recommended_actions=["RETRY_ANALYSIS"],
                session_valid=True,
                mirage_active=False
            )
    
    async def _get_user_baseline(self, user_id: str) -> Dict:
        """Get user's behavioral baseline"""
        try:
            baseline_key = f"user_baseline_{user_id}"
            
            if baseline_key not in self.memory_store:
                # Create default baseline
                baseline_data = {
                    "touch_speed_avg": 0.5,
                    "touch_pressure_avg": 0.5,
                    "swipe_velocity_avg": 0.5,
                    "device_tilt_avg": 0.0,
                    "session_duration_avg": 300,
                    "transaction_frequency_avg": 0.1,
                    "created_at": datetime.utcnow().isoformat(),
                    "update_count": 0
                }
                
                self.memory_store[baseline_key] = baseline_data
            
            return self.memory_store[baseline_key]
            
        except Exception as e:
            logger.error(f"Failed to get user baseline: {str(e)}")
            return {}
    
    async def _calculate_deviation(self, features: np.ndarray, baseline: Dict) -> float:
        """Calculate deviation from user baseline"""
        try:
            if not baseline:
                return 0.0
            
            # Calculate deviations for key metrics
            deviations = []
            
            # Touch speed deviation (assuming first 4 features are touch timing)
            if len(features) >= 4:
                touch_speed = np.mean(features[:4])
                baseline_touch_speed = float(baseline.get('touch_speed_avg', 0.5))
                touch_deviation = abs(touch_speed - baseline_touch_speed) / (baseline_touch_speed + 0.001)
                deviations.append(touch_deviation)
            
            # Touch pressure deviation (assuming features 4-8 are pressure)
            if len(features) >= 8:
                touch_pressure = np.mean(features[4:8])
                baseline_pressure = float(baseline.get('touch_pressure_avg', 0.5))
                pressure_deviation = abs(touch_pressure - baseline_pressure) / (baseline_pressure + 0.001)
                deviations.append(pressure_deviation)
            
            # Swipe velocity deviation
            if len(features) >= 18:
                swipe_velocity = np.mean(features[12:18])
                baseline_velocity = float(baseline.get('swipe_velocity_avg', 0.5))
                velocity_deviation = abs(swipe_velocity - baseline_velocity) / (baseline_velocity + 0.001)
                deviations.append(velocity_deviation)
            
            # Calculate overall deviation score
            if deviations:
                avg_deviation = np.mean(deviations)
                # Convert to 0-100 scale (lower deviation = higher trust)
                deviation_score = max(0, 100 - (avg_deviation * 100))
                return deviation_score
            
            return 75.0  # Default if no deviations calculated
            
        except Exception as e:
            logger.error(f"Deviation calculation failed: {str(e)}")
            return 75.0
    
    async def _detect_behavioral_anomalies(self, behavioral_data: Dict, baseline: Dict) -> List[str]:
        """Detect specific behavioral anomalies"""
        try:
            anomalies = []
            
            # Check touch patterns
            touch_patterns = behavioral_data.get('touch_patterns', [])
            if touch_patterns:
                # Rapid successive touches (potential bot behavior)
                touch_intervals = []
                for i in range(1, len(touch_patterns)):
                    if 'timestamp' in touch_patterns[i] and 'timestamp' in touch_patterns[i-1]:
                        interval = touch_patterns[i]['timestamp'] - touch_patterns[i-1]['timestamp']
                        touch_intervals.append(interval)
                
                if touch_intervals and np.mean(touch_intervals) < 0.05:  # Less than 50ms
                    anomalies.append("RAPID_TOUCH_PATTERN")
                
                # Unusual pressure patterns
                pressures = [p.get('pressure', 0.5) for p in touch_patterns]
                if pressures and (np.std(pressures) > 0.3 or np.mean(pressures) > 0.9):
                    anomalies.append("UNUSUAL_PRESSURE_PATTERN")
            
            # Check swipe patterns
            swipe_patterns = behavioral_data.get('swipe_patterns', [])
            if swipe_patterns:
                # Mechanical/robotic swipe patterns
                velocities = [s.get('velocity', 0) for s in swipe_patterns]
                if velocities and np.std(velocities) < 0.1:  # Too consistent
                    anomalies.append("MECHANICAL_SWIPE_PATTERN")
                
                # Unusual swipe directions
                directions = [s.get('direction', 0) for s in swipe_patterns]
                if directions and len(set(directions)) == 1 and len(directions) > 5:
                    anomalies.append("REPETITIVE_SWIPE_DIRECTION")
            
            # Check device motion
            device_motion = behavioral_data.get('device_motion', {})
            if device_motion:
                # Check for unusual device stability (potential emulator)
                accel_variance = (
                    device_motion.get('accelerometer_x', 0) ** 2 +
                    device_motion.get('accelerometer_y', 0) ** 2 +
                    device_motion.get('accelerometer_z', 0) ** 2
                )
                if accel_variance < 0.01:  # Too stable
                    anomalies.append("UNUSUAL_DEVICE_STABILITY")
            
            # Check app usage patterns
            app_usage = behavioral_data.get('app_usage', {})
            if app_usage:
                # Unusual navigation patterns
                screen_transitions = app_usage.get('screen_transitions', 0)
                session_duration = app_usage.get('session_duration', 0)
                
                if session_duration > 0:
                    transition_rate = screen_transitions / session_duration
                    if transition_rate > 0.1:  # More than 1 transition per 10 seconds
                        anomalies.append("RAPID_NAVIGATION")
                    elif transition_rate < 0.01:  # Less than 1 transition per 100 seconds
                        anomalies.append("STATIC_BEHAVIOR")
            
            # Check network patterns
            network_info = behavioral_data.get('network_info', {})
            if network_info:
                # Check for VPN or proxy usage
                if network_info.get('network_type', 0) == 'proxy':
                    anomalies.append("PROXY_USAGE")
                
                # Unusual signal strength patterns
                signal_strength = network_info.get('signal_strength', 0)
                if signal_strength == 1.0:  # Perfect signal (suspicious)
                    anomalies.append("PERFECT_SIGNAL_STRENGTH")
            
            # Time-based anomalies
            current_hour = datetime.utcnow().hour
            if 2 <= current_hour <= 5:  # Very early morning activity
                anomalies.append("UNUSUAL_TIME_ACTIVITY")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []
    
    async def _calculate_final_trust_score(self, ai_score: float, deviation_score: float, anomalies: List[str]) -> float:
        """Calculate final trust score combining all factors"""
        try:
            # Weight different components
            ai_weight = 0.5
            deviation_weight = 0.3
            anomaly_weight = 0.2
            
            # Calculate anomaly penalty
            anomaly_penalty = len(anomalies) * 10  # 10 points per anomaly
            
            # Combine scores
            final_score = (
                (ai_weight * ai_score) +
                (deviation_weight * deviation_score) -
                (anomaly_weight * anomaly_penalty)
            )
            
            # Apply additional penalties for critical anomalies
            critical_anomalies = [
                "RAPID_TOUCH_PATTERN",
                "MECHANICAL_SWIPE_PATTERN",
                "UNUSUAL_DEVICE_STABILITY",
                "PROXY_USAGE"
            ]
            
            for anomaly in anomalies:
                if anomaly in critical_anomalies:
                    final_score -= 20  # Additional penalty for critical anomalies
            
            return max(0.0, min(100.0, final_score))
            
        except Exception as e:
            logger.error(f"Final trust score calculation failed: {str(e)}")
            return 50.0
    
    async def _generate_recommendations(self, trust_score: float, anomalies: List[str], risk_level: str) -> List[str]:
        """Generate recommendations based on analysis"""
        try:
            recommendations = []
            
            if trust_score < 30:
                recommendations.append("IMMEDIATE_LOCKDOWN")
            elif trust_score < 50:
                recommendations.append("ACTIVATE_MIRAGE")
                recommendations.append("INCREASE_MONITORING")
            elif trust_score < 70:
                recommendations.append("REQUEST_ADDITIONAL_VERIFICATION")
                recommendations.append("LIMIT_TRANSACTION_AMOUNT")
            
            # Specific recommendations based on anomalies
            if "RAPID_TOUCH_PATTERN" in anomalies:
                recommendations.append("COGNITIVE_CHALLENGE")
            
            if "MECHANICAL_SWIPE_PATTERN" in anomalies:
                recommendations.append("PATTERN_VERIFICATION")
            
            if "UNUSUAL_DEVICE_STABILITY" in anomalies:
                recommendations.append("DEVICE_VERIFICATION")
            
            if "PROXY_USAGE" in anomalies:
                recommendations.append("NETWORK_VERIFICATION")
            
            if "UNUSUAL_TIME_ACTIVITY" in anomalies:
                recommendations.append("TIME_BASED_VERIFICATION")
            
            if not recommendations:
                recommendations.append("CONTINUE_MONITORING")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            return ["CONTINUE_MONITORING"]
    
    async def _update_user_baseline(self, user_id: str, features: np.ndarray, trust_score: float):
        """Update user's behavioral baseline"""
        try:
            # Only update baseline if trust score is reasonably high
            if trust_score < 60:
                return
            
            baseline_key = f"user_baseline_{user_id}"
            current_baseline = self.memory_store.get(baseline_key, {})
            
            if not current_baseline:
                return
            
            # Update with exponential moving average
            alpha = self.learning_rate
            
            # Update touch speed
            if len(features) >= 4:
                current_touch_speed = np.mean(features[:4])
                old_touch_speed = float(current_baseline.get('touch_speed_avg', 0.5))
                new_touch_speed = alpha * current_touch_speed + (1 - alpha) * old_touch_speed
                current_baseline['touch_speed_avg'] = new_touch_speed
            
            # Update touch pressure
            if len(features) >= 8:
                current_pressure = np.mean(features[4:8])
                old_pressure = float(current_baseline.get('touch_pressure_avg', 0.5))
                new_pressure = alpha * current_pressure + (1 - alpha) * old_pressure
                current_baseline['touch_pressure_avg'] = new_pressure
            
            # Update swipe velocity
            if len(features) >= 18:
                current_velocity = np.mean(features[12:18])
                old_velocity = float(current_baseline.get('swipe_velocity_avg', 0.5))
                new_velocity = alpha * current_velocity + (1 - alpha) * old_velocity
                current_baseline['swipe_velocity_avg'] = new_velocity
            
            # Update metadata
            current_baseline['update_count'] = current_baseline.get('update_count', 0) + 1
            current_baseline['last_updated'] = datetime.utcnow().isoformat()
            
            # Save updated baseline
            self.memory_store[baseline_key] = current_baseline
            
        except Exception as e:
            logger.error(f"Baseline update failed: {str(e)}")
    
    async def _store_behavioral_analysis(self, user_id: str, session_id: str, analysis_data: Dict):
        """Store behavioral analysis results"""
        try:
            analysis_key = f"behavioral_analysis_{session_id}"
            
            analysis_record = {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_data": analysis_data
            }
            
            # Store analysis
            self.memory_store[analysis_key] = analysis_record
            
            # Add to session analysis history
            history_key = f"session_analysis_history_{session_id}"
            if history_key not in self.memory_store:
                self.memory_store[history_key] = []
            
            self.memory_store[history_key].append(analysis_record)
            
            # Keep last 100 entries
            if len(self.memory_store[history_key]) > 100:
                self.memory_store[history_key] = self.memory_store[history_key][-100:]
            
        except Exception as e:
            logger.error(f"Failed to store behavioral analysis: {str(e)}")
    
    async def get_behavioral_insights(self, user_id: str, session_id: str) -> Dict:
        """Get behavioral insights for a user session"""
        try:
            # Get recent analysis history
            history_key = f"session_analysis_history_{session_id}"
            history_data = self.memory_store.get(history_key, [])
            
            if not history_data:
                return {"insights": [], "trend": "STABLE", "risk_factors": []}
            
            # Calculate insights
            insights = []
            trust_scores = []
            
            for analysis in history_data:
                analysis_data = analysis['analysis_data']
                trust_scores.append(analysis_data['trust_score'])
                
                if analysis_data['anomalies']:
                    insights.append({
                        "timestamp": analysis['timestamp'],
                        "anomalies": analysis_data['anomalies'],
                        "trust_score": analysis_data['trust_score']
                    })
            
            # Calculate trend
            trend = "STABLE"
            if len(trust_scores) >= 3:
                recent_avg = np.mean(trust_scores[-3:])
                overall_avg = np.mean(trust_scores)
                
                if recent_avg > overall_avg + 10:
                    trend = "IMPROVING"
                elif recent_avg < overall_avg - 10:
                    trend = "DECLINING"
            
            # Identify risk factors
            risk_factors = []
            if trust_scores and np.mean(trust_scores) < 60:
                risk_factors.append("LOW_AVERAGE_TRUST")
            
            if len(trust_scores) >= 5:
                volatility = np.std(trust_scores)
                if volatility > 15:
                    risk_factors.append("HIGH_VOLATILITY")
            
            return {
                "insights": insights,
                "trend": trend,
                "risk_factors": risk_factors,
                "average_trust": np.mean(trust_scores) if trust_scores else 0,
                "analysis_count": len(history_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get behavioral insights: {str(e)}")
            return {"insights": [], "trend": "STABLE", "risk_factors": []}
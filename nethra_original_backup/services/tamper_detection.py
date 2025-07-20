"""
Tamper Detection Service - Detects app tampering and security threats
"""

import asyncio
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class TamperDetector:
    """Service for detecting app tampering and security threats"""
    
    def __init__(self, memory_store: Dict):
        self.memory_store = memory_store
        self.integrity_keys = {
            "app_signature": "NETHRA_APP_SIGNATURE_KEY",
            "device_fingerprint": "NETHRA_DEVICE_FINGERPRINT_KEY",
            "session_token": "NETHRA_SESSION_TOKEN_KEY"
        }
        self.max_tamper_score = 100
        self.critical_tamper_threshold = 70
    
    async def detect_tampering(self, behavioral_data) -> bool:
        """Detect if app has been tampered with"""
        try:
            tamper_score = 0
            tamper_indicators = []
            
            # Check app integrity
            app_integrity_score = await self._check_app_integrity(behavioral_data)
            tamper_score += app_integrity_score
            if app_integrity_score > 20:
                tamper_indicators.append("APP_INTEGRITY_COMPROMISED")
            
            # Check device integrity
            device_integrity_score = await self._check_device_integrity(behavioral_data)
            tamper_score += device_integrity_score
            if device_integrity_score > 20:
                tamper_indicators.append("DEVICE_INTEGRITY_COMPROMISED")
            
            # Check runtime tampering
            runtime_score = await self._check_runtime_tampering(behavioral_data)
            tamper_score += runtime_score
            if runtime_score > 15:
                tamper_indicators.append("RUNTIME_TAMPERING_DETECTED")
            
            # Check for debugging/emulation
            debug_score = await self._check_debug_environment(behavioral_data)
            tamper_score += debug_score
            if debug_score > 15:
                tamper_indicators.append("DEBUG_ENVIRONMENT_DETECTED")
            
            # Check network tampering
            network_score = await self._check_network_tampering(behavioral_data)
            tamper_score += network_score
            if network_score > 10:
                tamper_indicators.append("NETWORK_TAMPERING_DETECTED")
            
            # Store tamper analysis
            await self._store_tamper_analysis(
                behavioral_data.user_id,
                behavioral_data.session_id,
                tamper_score,
                tamper_indicators
            )
            
            # Log critical tampering
            if tamper_score >= self.critical_tamper_threshold:
                await self._log_critical_tampering(
                    behavioral_data.user_id,
                    behavioral_data.session_id,
                    tamper_score,
                    tamper_indicators
                )
            
            return tamper_score >= self.critical_tamper_threshold
            
        except Exception as e:
            logger.error(f"Tamper detection failed: {str(e)}")
            return False
    
    async def _check_app_integrity(self, behavioral_data) -> int:
        """Check app integrity and signature"""
        try:
            score = 0
            
            # Check app signature (simulated)
            app_usage = behavioral_data.app_usage
            if app_usage:
                # Check for modified app behavior
                if app_usage.get('debug_mode', False):
                    score += 25
                
                # Check for unusual app version
                app_version = app_usage.get('app_version', '')
                if not app_version or 'debug' in app_version.lower():
                    score += 20
                
                # Check for root/jailbreak indicators
                if app_usage.get('root_detected', False):
                    score += 30
                
                # Check for hooking frameworks
                if app_usage.get('hooking_detected', False):
                    score += 35
            
            return min(score, 50)
            
        except Exception as e:
            logger.error(f"App integrity check failed: {str(e)}")
            return 0
    
    async def _check_device_integrity(self, behavioral_data) -> int:
        """Check device integrity and fingerprint"""
        try:
            score = 0
            
            # Check device motion consistency
            device_motion = behavioral_data.device_motion
            if device_motion:
                # Check for emulator indicators
                accel_x = device_motion.get('accelerometer_x', 0)
                accel_y = device_motion.get('accelerometer_y', 0)
                accel_z = device_motion.get('accelerometer_z', 0)
                
                # Perfect zeros indicate emulator
                if accel_x == 0 and accel_y == 0 and accel_z == 0:
                    score += 25
                
                # Check for unrealistic sensor values
                if abs(accel_x) > 20 or abs(accel_y) > 20 or abs(accel_z) > 20:
                    score += 15
                
                # Check gyroscope consistency
                gyro_x = device_motion.get('gyroscope_x', 0)
                gyro_y = device_motion.get('gyroscope_y', 0)
                gyro_z = device_motion.get('gyroscope_z', 0)
                
                if gyro_x == 0 and gyro_y == 0 and gyro_z == 0:
                    score += 20
            
            # Check touch patterns for automation
            touch_patterns = behavioral_data.touch_patterns
            if touch_patterns and len(touch_patterns) > 5:
                # Check for perfect timing (bot behavior)
                timestamps = [p.get('timestamp', 0) for p in touch_patterns]
                if len(set(timestamps)) == len(timestamps):  # All unique
                    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                    if len(set(intervals)) == 1:  # Perfect intervals
                        score += 30
            
            return min(score, 40)
            
        except Exception as e:
            logger.error(f"Device integrity check failed: {str(e)}")
            return 0
    
    async def _check_runtime_tampering(self, behavioral_data) -> int:
        """Check for runtime tampering"""
        try:
            score = 0
            
            # Check for memory tampering indicators
            app_usage = behavioral_data.app_usage
            if app_usage:
                # Check for unusual memory usage patterns
                memory_usage = app_usage.get('memory_usage', 0)
                if memory_usage > 1000:  # Unrealistic memory usage
                    score += 20
                
                # Check for code injection indicators
                if app_usage.get('code_injection_detected', False):
                    score += 40
                
                # Check for dynamic analysis tools
                if app_usage.get('analysis_tools_detected', False):
                    score += 30
            
            # Check session consistency
            session_duration = behavioral_data.app_usage.get('session_duration', 0)
            if session_duration < 5:  # Too short session
                score += 10
            elif session_duration > 7200:  # Too long session (2 hours)
                score += 15
            
            return min(score, 35)
            
        except Exception as e:
            logger.error(f"Runtime tampering check failed: {str(e)}")
            return 0
    
    async def _check_debug_environment(self, behavioral_data) -> int:
        """Check for debug/emulation environment"""
        try:
            score = 0
            
            # Check network info for emulator indicators
            network_info = behavioral_data.network_info
            if network_info:
                # Check for emulator network patterns
                network_type = network_info.get('network_type', '')
                if network_type == 'emulator' or 'android' in network_type.lower():
                    score += 25
                
                # Check for localhost connections
                if network_info.get('localhost_detected', False):
                    score += 20
                
                # Check for proxy/VPN indicators
                if network_info.get('proxy_detected', False):
                    score += 15
            
            # Check for debugging tools
            app_usage = behavioral_data.app_usage
            if app_usage:
                if app_usage.get('debugger_detected', False):
                    score += 30
                
                if app_usage.get('emulator_detected', False):
                    score += 35
            
            return min(score, 30)
            
        except Exception as e:
            logger.error(f"Debug environment check failed: {str(e)}")
            return 0
    
    async def _check_network_tampering(self, behavioral_data) -> int:
        """Check for network-level tampering"""
        try:
            score = 0
            
            network_info = behavioral_data.network_info
            if network_info:
                # Check for SSL/TLS tampering
                if network_info.get('ssl_tampering_detected', False):
                    score += 25
                
                # Check for man-in-the-middle indicators
                if network_info.get('mitm_detected', False):
                    score += 30
                
                # Check for unusual DNS responses
                if network_info.get('dns_tampering_detected', False):
                    score += 20
                
                # Check for traffic analysis tools
                if network_info.get('traffic_analysis_detected', False):
                    score += 15
            
            return min(score, 25)
            
        except Exception as e:
            logger.error(f"Network tampering check failed: {str(e)}")
            return 0
    
    async def _store_tamper_analysis(self, user_id: str, session_id: str, tamper_score: int, indicators: List[str]):
        """Store tamper analysis results"""
        try:
            analysis_key = f"tamper_analysis_{session_id}"
            
            analysis_data = {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tamper_score": tamper_score,
                "indicators": indicators,
                "severity": self._get_severity_level(tamper_score)
            }
            
            # Store analysis
            self.memory_store[analysis_key] = analysis_data
            
            # Add to tamper history
            history_key = f"tamper_history_{user_id}"
            if history_key not in self.memory_store:
                self.memory_store[history_key] = []
            
            self.memory_store[history_key].append(analysis_data)
            
            # Keep last 100 entries
            if len(self.memory_store[history_key]) > 100:
                self.memory_store[history_key] = self.memory_store[history_key][-100:]
            
        except Exception as e:
            logger.error(f"Failed to store tamper analysis: {str(e)}")
    
    async def _log_critical_tampering(self, user_id: str, session_id: str, tamper_score: int, indicators: List[str]):
        """Log critical tampering events"""
        try:
            critical_log = {
                "event_type": "CRITICAL_TAMPERING",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tamper_score": tamper_score,
                "indicators": indicators,
                "severity": "CRITICAL"
            }
            
            # Store in critical events log
            if "critical_events" not in self.memory_store:
                self.memory_store["critical_events"] = []
            
            self.memory_store["critical_events"].append(critical_log)
            
            # Keep last 1000 critical events
            if len(self.memory_store["critical_events"]) > 1000:
                self.memory_store["critical_events"] = self.memory_store["critical_events"][-1000:]
            
            # Send alert (placeholder for actual alerting system)
            await self._send_tamper_alert(critical_log)
            
        except Exception as e:
            logger.error(f"Failed to log critical tampering: {str(e)}")
    
    async def _send_tamper_alert(self, critical_log: Dict):
        """Send tamper alert to security team"""
        try:
            # Placeholder for actual alerting system
            # This could integrate with email, Slack, SMS, etc.
            logger.warning(f"CRITICAL TAMPERING DETECTED: {critical_log}")
            
            # Store alert for demo purposes
            if "tamper_alerts" not in self.memory_store:
                self.memory_store["tamper_alerts"] = []
            
            self.memory_store["tamper_alerts"].append(critical_log)
            
        except Exception as e:
            logger.error(f"Failed to send tamper alert: {str(e)}")
    
    def _get_severity_level(self, tamper_score: int) -> str:
        """Get severity level based on tamper score"""
        if tamper_score >= 70:
            return "CRITICAL"
        elif tamper_score >= 50:
            return "HIGH"
        elif tamper_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def get_tamper_report(self, user_id: str, session_id: str) -> Dict:
        """Get tamper detection report"""
        try:
            analysis_key = f"tamper_analysis_{session_id}"
            analysis_data = self.memory_store.get(analysis_key)
            
            if not analysis_data:
                return {"status": "NO_ANALYSIS", "tamper_score": 0}
            
            return {
                "status": "ANALYZED",
                "tamper_score": analysis_data.get('tamper_score', 0),
                "severity": analysis_data.get('severity', 'LOW'),
                "indicators": analysis_data.get('indicators', []),
                "timestamp": analysis_data.get('timestamp', ''),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get tamper report: {str(e)}")
            return {"status": "ERROR", "tamper_score": 0}
    
    async def get_tamper_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get tamper detection history for user"""
        try:
            history_key = f"tamper_history_{user_id}"
            history_data = self.memory_store.get(history_key, [])
            
            return history_data[-limit:] if len(history_data) > limit else history_data
            
        except Exception as e:
            logger.error(f"Failed to get tamper history: {str(e)}")
            return []
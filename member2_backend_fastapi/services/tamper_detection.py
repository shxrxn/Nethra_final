"""
Tamper Detection Service for NETHRA
Detects system tampering and security threats
"""

import asyncio
import logging
import hashlib
import os
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from models.behavioral_models import TamperAttempt

logger = logging.getLogger(__name__)

@dataclass
class SecurityCheck:
    """Security check result"""
    check_type: str
    passed: bool
    details: Dict[str, Any]
    timestamp: datetime

class TamperDetector:
    """Service for detecting system tampering and security threats"""
    
    def __init__(self):
        self.security_checks: Dict[str, SecurityCheck] = {}
        self.tamper_attempts: List[TamperAttempt] = []
        self.app_integrity_hash = None
        self.suspicious_processes = []
        
        # Security thresholds
        self.max_failed_checks = 3
        self.check_interval = 30  # seconds
        self.integrity_check_enabled = True
        
        logger.info("Tamper Detector initialized")
    
    async def initialize(self):
        """Initialize tamper detection"""
        try:
            # Calculate app integrity hash
            await self._calculate_app_integrity()
            
            # Start monitoring
            asyncio.create_task(self._continuous_monitoring())
            
            logger.info("✅ Tamper detection initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize tamper detection: {str(e)}")
    
    async def perform_security_check(self, user_id: str, device_id: str, session_id: str) -> Dict[str, Any]:
        """Perform comprehensive security check"""
        try:
            checks = {}
            
            # App integrity check
            checks["app_integrity"] = await self._check_app_integrity()
            
            # Root/jailbreak detection
            checks["device_security"] = await self._check_device_security()
            
            # Process monitoring
            checks["process_security"] = await self._check_suspicious_processes()
            
            # Network security
            checks["network_security"] = await self._check_network_security()
            
            # Memory protection
            checks["memory_security"] = await self._check_memory_protection()
            
            # Calculate overall security score
            security_score = self._calculate_security_score(checks)
            
            # Detect tampering
            tamper_detected = security_score < 0.7
            
            if tamper_detected:
                await self._handle_tamper_detection(user_id, device_id, session_id, checks)
            
            return {
                "security_score": security_score,
                "tamper_detected": tamper_detected,
                "checks": checks,
                "timestamp": datetime.now().isoformat(),
                "recommended_action": "lock_session" if tamper_detected else "continue"
            }
            
        except Exception as e:
            logger.error(f"Security check failed: {str(e)}")
            return self._get_fallback_security_check()
    
    async def _calculate_app_integrity(self):
        """Calculate application integrity hash"""
        try:
            # In a real implementation, this would hash critical app files
            # For demo purposes, we'll create a mock hash
            app_files = ["main.py", "models/behavioral_models.py"]
            
            hasher = hashlib.sha256()
            for file_path in app_files:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        hasher.update(f.read())
            
            self.app_integrity_hash = hasher.hexdigest()
            logger.info("App integrity hash calculated")
            
        except Exception as e:
            logger.error(f"Failed to calculate app integrity: {str(e)}")
            self.app_integrity_hash = "mock_hash_for_demo"
    
    async def _check_app_integrity(self) -> SecurityCheck:
        """Check application integrity"""
        try:
            # Recalculate hash and compare
            current_hash = hashlib.sha256()
            
            # Mock integrity check for demo
            integrity_intact = True  # In real implementation, compare hashes
            
            return SecurityCheck(
                check_type="app_integrity",
                passed=integrity_intact,
                details={
                    "expected_hash": self.app_integrity_hash[:16] + "...",
                    "current_hash": self.app_integrity_hash[:16] + "...",
                    "files_checked": 2
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"App integrity check failed: {str(e)}")
            return SecurityCheck(
                check_type="app_integrity",
                passed=False,
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _check_device_security(self) -> SecurityCheck:
        """Check for device rooting/jailbreaking"""
        try:
            # Mock device security check
            # In real implementation, check for:
            # - Root access indicators
            # - Jailbreak indicators
            # - Developer options enabled
            # - USB debugging enabled
            
            security_indicators = {
                "root_detected": False,
                "jailbreak_detected": False,
                "developer_mode": False,
                "usb_debugging": False,
                "unknown_sources": False
            }
            
            device_secure = not any(security_indicators.values())
            
            return SecurityCheck(
                check_type="device_security",
                passed=device_secure,
                details=security_indicators,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Device security check failed: {str(e)}")
            return SecurityCheck(
                check_type="device_security",
                passed=False,
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _check_suspicious_processes(self) -> SecurityCheck:
        """Check for suspicious running processes"""
        try:
            suspicious_keywords = [
                "frida", "xposed", "substrate", "cydia",
                "supersu", "magisk", "busybox", "debugger"
            ]
            
            suspicious_found = []
            
            # Check running processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    for keyword in suspicious_keywords:
                        if keyword in proc_name:
                            suspicious_found.append(proc_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.suspicious_processes = suspicious_found
            
            return SecurityCheck(
                check_type="process_security",
                passed=len(suspicious_found) == 0,
                details={
                    "suspicious_processes": suspicious_found,
                    "total_processes": len(list(psutil.process_iter())),
                    "check_keywords": len(suspicious_keywords)
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Process security check failed: {str(e)}")
            return SecurityCheck(
                check_type="process_security",
                passed=True,  # Assume safe on error
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _check_network_security(self) -> SecurityCheck:
        """Check network security"""
        try:
            # Mock network security check
            # In real implementation, check for:
            # - Proxy detection
            # - VPN detection
            # - Man-in-the-middle attacks
            # - SSL pinning bypass
            
            network_indicators = {
                "proxy_detected": False,
                "vpn_detected": False,
                "mitm_detected": False,
                "ssl_bypass_detected": False,
                "suspicious_dns": False
            }
            
            network_secure = not any(network_indicators.values())
            
            return SecurityCheck(
                check_type="network_security",
                passed=network_secure,
                details=network_indicators,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Network security check failed: {str(e)}")
            return SecurityCheck(
                check_type="network_security",
                passed=True,  # Assume safe on error
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _check_memory_protection(self) -> SecurityCheck:
        """Check memory protection"""
        try:
            # Mock memory protection check
            # In real implementation, check for:
            # - Memory dumps
            # - Code injection
            # - Runtime manipulation
            
            memory_indicators = {
                "memory_dump_detected": False,
                "code_injection_detected": False,
                "runtime_manipulation": False,
                "heap_protection": True,
                "stack_protection": True
            }
            
            memory_secure = (
                not memory_indicators["memory_dump_detected"] and
                not memory_indicators["code_injection_detected"] and
                not memory_indicators["runtime_manipulation"] and
                memory_indicators["heap_protection"] and
                memory_indicators["stack_protection"]
            )
            
            return SecurityCheck(
                check_type="memory_security",
                passed=memory_secure,
                details=memory_indicators,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Memory security check failed: {str(e)}")
            return SecurityCheck(
                check_type="memory_security",
                passed=True,  # Assume safe on error
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _calculate_security_score(self, checks: Dict[str, SecurityCheck]) -> float:
        """Calculate overall security score"""
        if not checks:
            return 0.5
        
        # Weight different security checks
        weights = {
            "app_integrity": 0.3,
            "device_security": 0.25,
            "process_security": 0.2,
            "network_security": 0.15,
            "memory_security": 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for check_type, check in checks.items():
            weight = weights.get(check_type, 0.1)
            score = 1.0 if check.passed else 0.0
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    async def _handle_tamper_detection(self, user_id: str, device_id: str, session_id: str, checks: Dict[str, SecurityCheck]):
        """Handle detected tampering"""
        try:
            # Determine tamper type and severity
            tamper_type = self._determine_tamper_type(checks)
            severity = self._determine_severity(checks)
            
            # Create tamper attempt record
            tamper_attempt = TamperAttempt(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                tamper_type=tamper_type,
                severity=severity,
                indicators=self._extract_indicators(checks),
                action_taken="session_lock",
                auto_lock_triggered=True,
                app_integrity=checks.get("app_integrity", SecurityCheck("", False, {}, datetime.now())).passed,
                device_rooted=not checks.get("device_security", SecurityCheck("", True, {}, datetime.now())).passed,
                suspicious_processes=self.suspicious_processes
            )
            
            self.tamper_attempts.append(tamper_attempt)
            
            logger.warning(f"🚨 Tamper detected: {tamper_type} (severity: {severity})")
            
        except Exception as e:
            logger.error(f"Failed to handle tamper detection: {str(e)}")
    
    def _determine_tamper_type(self, checks: Dict[str, SecurityCheck]) -> str:
        """Determine type of tampering"""
        failed_checks = [name for name, check in checks.items() if not check.passed]
        
        if "app_integrity" in failed_checks:
            return "app_modification"
        elif "device_security" in failed_checks:
            return "device_compromise"
        elif "process_security" in failed_checks:
            return "malicious_process"
        elif "network_security" in failed_checks:
            return "network_attack"
        elif "memory_security" in failed_checks:
            return "memory_manipulation"
        else:
            return "unknown_tamper"
    
    def _determine_severity(self, checks: Dict[str, SecurityCheck]) -> str:
        """Determine severity of tampering"""
        failed_count = sum(1 for check in checks.values() if not check.passed)
        
        if failed_count >= 3:
            return "critical"
        elif failed_count == 2:
            return "high"
        elif failed_count == 1:
            return "medium"
        else:
            return "low"
    
    def _extract_indicators(self, checks: Dict[str, SecurityCheck]) -> List[str]:
        """Extract tamper indicators"""
        indicators = []
        
        for check_type, check in checks.items():
            if not check.passed:
                indicators.append(f"{check_type}_failed")
                
                # Add specific details
                if check_type == "process_security" and self.suspicious_processes:
                    indicators.extend([f"suspicious_process_{proc}" for proc in self.suspicious_processes[:3]])
        
        return indicators
    
    async def _continuous_monitoring(self):
        """Continuous security monitoring"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Perform lightweight security checks
                await self._lightweight_security_check()
                
            except Exception as e:
                logger.error(f"Continuous monitoring error: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _lightweight_security_check(self):
        """Lightweight security check for continuous monitoring"""
        try:
            # Check for new suspicious processes
            current_processes = []
            for proc in psutil.process_iter(['name']):
                try:
                    current_processes.append(proc.info['name'].lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Look for new suspicious processes
            suspicious_keywords = ["frida", "xposed", "debugger"]
            new_suspicious = []
            
            for proc_name in current_processes:
                for keyword in suspicious_keywords:
                    if keyword in proc_name and proc_name not in self.suspicious_processes:
                        new_suspicious.append(proc_name)
            
            if new_suspicious:
                logger.warning(f"🚨 New suspicious processes detected: {new_suspicious}")
                self.suspicious_processes.extend(new_suspicious)
            
        except Exception as e:
            logger.error(f"Lightweight security check failed: {str(e)}")
    
    def _get_fallback_security_check(self) -> Dict[str, Any]:
        """Fallback security check result"""
        return {
            "security_score": 0.5,
            "tamper_detected": False,
            "checks": {},
            "timestamp": datetime.now().isoformat(),
            "recommended_action": "continue",
            "error": "Security check failed"
        }
    
    async def get_tamper_history(self, user_id: str, device_id: str) -> List[Dict[str, Any]]:
        """Get tamper attempt history"""
        user_attempts = [
            {
                "timestamp": attempt.timestamp.isoformat(),
                "tamper_type": attempt.tamper_type,
                "severity": attempt.severity,
                "indicators": attempt.indicators,
                "action_taken": attempt.action_taken
            }
            for attempt in self.tamper_attempts
            if attempt.user_id == user_id and attempt.device_id == device_id
        ]
        
        return user_attempts[-10:]  # Return last 10 attempts
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        return {
            "total_tamper_attempts": len(self.tamper_attempts),
            "integrity_checks_enabled": self.integrity_check_enabled,
            "monitoring_interval": self.check_interval,
            "suspicious_processes_detected": len(self.suspicious_processes),
            "app_integrity_hash": self.app_integrity_hash[:16] + "..." if self.app_integrity_hash else None
        }
"""
Trust Service for NETHRA
Manages trust scoring and profile management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid

from services.ai_interface import AIModelInterface
from models.behavioral_models import (
    BehavioralSession, TrustProfile, AnomalyDetection, 
    PrivacyMetrics, create_behavioral_features
)

logger = logging.getLogger(__name__)

@dataclass
class TrustDecision:
    """Trust decision result"""
    trust_score: float
    risk_level: str
    recommended_action: str
    confidence: float
    factors: Dict[str, Any]
    timestamp: datetime

class TrustService:
    """Service for managing trust profiles and scoring"""
    
    def __init__(self, ai_interface: AIModelInterface):
        self.ai_interface = ai_interface
        self.trust_profiles: Dict[str, TrustProfile] = {}
        self.session_cache: Dict[str, BehavioralSession] = {}
        self.trust_history: Dict[str, List[TrustDecision]] = {}
        
        # Trust scoring parameters
        self.min_trust_score = 0.0
        self.max_trust_score = 100.0
        self.default_trust_score = 85.0
        self.critical_threshold = 30.0
        self.warning_threshold = 50.0
        self.safe_threshold = 70.0
        
        # Session management
        self.session_timeout = timedelta(minutes=30)
        self.max_sessions = 1000
        
        # Performance metrics
        self.total_evaluations = 0
        self.false_positive_rate = 0.0
        self.false_negative_rate = 0.0
        
        logger.info("Trust Service initialized")
    
    async def create_trust_profile(self, user_id: str, device_id: str) -> TrustProfile:
        """Create a new trust profile for a user"""
        profile_key = f"{user_id}_{device_id}"
        
        if profile_key in self.trust_profiles:
            return self.trust_profiles[profile_key]
        
        profile = TrustProfile(
            user_id=user_id,
            device_id=device_id,
            baseline_features={},
            base_trust=self.default_trust_score
        )
        
        self.trust_profiles[profile_key] = profile
        self.trust_history[profile_key] = []
        
        logger.info(f"Created trust profile for user {user_id} on device {device_id}")
        return profile
    
    async def get_trust_profile(self, user_id: str, device_id: str) -> Optional[TrustProfile]:
        """Get trust profile for a user-device combination"""
        profile_key = f"{user_id}_{device_id}"
        return self.trust_profiles.get(profile_key)
    
    async def evaluate_trust(self, session: BehavioralSession) -> TrustDecision:
        """Evaluate trust score for a behavioral session"""
        try:
            # Get or create trust profile
            profile = await self.get_trust_profile(session.user_id, session.device_id)
            if not profile:
                profile = await self.create_trust_profile(session.user_id, session.device_id)
            
            # Analyze session with AI
            analysis = await self.ai_interface.analyze_behavioral_session(session)
            
            # Calculate trust score
            trust_score = await self._calculate_trust_score(session, profile, analysis)
            
            # Determine risk level
            risk_level = self._determine_risk_level(trust_score)
            
            # Get recommended action
            recommended_action = await self._get_recommended_action(
                trust_score, risk_level, analysis["anomalies"]
            )
            
            # Calculate confidence
            confidence = analysis.get("confidence", 0.5)
            
            # Create trust decision
            decision = TrustDecision(
                trust_score=trust_score,
                risk_level=risk_level,
                recommended_action=recommended_action,
                confidence=confidence,
                factors=self._extract_trust_factors(analysis),
                timestamp=datetime.now()
            )
            
            # Update profile
            await self._update_trust_profile(profile, session, decision)
            
            # Store in history
            await self._store_trust_decision(session.user_id, session.device_id, decision)
            
            # Update metrics
            self.total_evaluations += 1
            
            return decision
            
        except Exception as e:
            logger.error(f"Error evaluating trust: {str(e)}")
            return self._get_fallback_decision()
    
    async def _calculate_trust_score(self, session: BehavioralSession, profile: TrustProfile, analysis: Dict[str, Any]) -> float:
        """Calculate trust score based on behavioral analysis"""
        # Base trust score from AI model
        base_score = analysis.get("trust_score", self.default_trust_score)
        
        # Adjust based on anomalies
        anomaly_penalty = 0.0
        for anomaly in analysis.get("anomalies", []):
            penalty = self._calculate_anomaly_penalty(anomaly)
            anomaly_penalty += penalty
        
        # Adjust based on historical trust
        history_bonus = await self._calculate_history_bonus(session.user_id, session.device_id)
        
        # Adjust based on session context
        context_adjustment = self._calculate_context_adjustment(session)
        
        # Adjust based on device familiarity
        device_bonus = self._calculate_device_familiarity_bonus(profile)
        
        # Calculate final trust score
        trust_score = base_score - anomaly_penalty + history_bonus + context_adjustment + device_bonus
        
        # Apply trust decay for extended sessions
        trust_score = await self._apply_trust_decay(trust_score, session)
        
        # Clamp to valid range
        trust_score = max(self.min_trust_score, min(self.max_trust_score, trust_score))
        
        return trust_score
    
    def _calculate_anomaly_penalty(self, anomaly: AnomalyDetection) -> float:
        """Calculate penalty for detected anomaly"""
        base_penalty = 10.0
        
        # Scale by anomaly score
        severity_multiplier = anomaly.anomaly_score
        
        # Scale by risk level
        risk_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        
        risk_multiplier = risk_multipliers.get(anomaly.risk_level, 1.0)
        
        # Scale by confidence
        confidence_multiplier = anomaly.confidence_level
        
        penalty = base_penalty * severity_multiplier * risk_multiplier * confidence_multiplier
        
        return min(penalty, 30.0)  # Cap penalty
    
    async def _calculate_history_bonus(self, user_id: str, device_id: str) -> float:
        """Calculate bonus based on trust history"""
        profile_key = f"{user_id}_{device_id}"
        history = self.trust_history.get(profile_key, [])
        
        if not history:
            return 0.0
        
        # Calculate average trust over recent history
        recent_history = [d for d in history if (datetime.now() - d.timestamp).days <= 7]
        
        if not recent_history:
            return 0.0
        
        avg_trust = sum(d.trust_score for d in recent_history) / len(recent_history)
        
        # Bonus for consistently high trust
        if avg_trust > self.safe_threshold:
            return min((avg_trust - self.safe_threshold) * 0.1, 5.0)
        
        return 0.0
    
    def _calculate_context_adjustment(self, session: BehavioralSession) -> float:
        """Calculate adjustment based on session context"""
        adjustment = 0.0
        
        # Time-based adjustment
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            adjustment += 2.0
        elif 22 <= current_hour or current_hour <= 6:  # Night hours
            adjustment -= 3.0
        
        # Location context (if available)
        if session.location_context:
            if session.location_context == "home":
                adjustment += 3.0
            elif session.location_context == "work":
                adjustment += 2.0
            elif session.location_context == "unknown":
                adjustment -= 5.0
        
        # Network context
        if session.network_context:
            if session.network_context == "wifi":
                adjustment += 1.0
            elif session.network_context == "cellular":
                adjustment += 0.5
            elif session.network_context == "public_wifi":
                adjustment -= 3.0
        
        return adjustment
    
    def _calculate_device_familiarity_bonus(self, profile: TrustProfile) -> float:
        """Calculate bonus for device familiarity"""
        # Bonus based on session count
        session_bonus = min(profile.session_count * 0.1, 5.0)
        
        # Bonus for low false positives
        if profile.session_count > 10:
            false_positive_rate = profile.false_positive_count / profile.session_count
            if false_positive_rate < 0.05:
                session_bonus += 2.0
        
        return session_bonus
    
    async def _apply_trust_decay(self, trust_score: float, session: BehavioralSession) -> float:
        """Apply trust decay for extended sessions"""
        if not session.end_time:
            return trust_score
        
        session_duration = (session.end_time - session.start_time).total_seconds()
        
        # Apply decay after 30 minutes
        if session_duration > 1800:  # 30 minutes
            decay_factor = 0.95 ** ((session_duration - 1800) / 300)  # Decay every 5 minutes
            trust_score *= decay_factor
        
        return trust_score
    
    def _determine_risk_level(self, trust_score: float) -> str:
        """Determine risk level based on trust score"""
        if trust_score >= self.safe_threshold:
            return "low"
        elif trust_score >= self.warning_threshold:
            return "medium"
        elif trust_score >= self.critical_threshold:
            return "high"
        else:
            return "critical"
    
    async def _get_recommended_action(self, trust_score: float, risk_level: str, anomalies: List[AnomalyDetection]) -> str:
        """Get recommended action based on trust assessment"""
        # Check for critical anomalies
        critical_anomalies = [a for a in anomalies if a.risk_level == "critical"]
        if critical_anomalies:
            return "activate_mirage"
        
        # Check for high anomalies
        high_anomalies = [a for a in anomalies if a.risk_level == "high"]
        if high_anomalies or risk_level == "critical":
            return "challenge_user"
        
        # Check for medium risk
        if risk_level == "high":
            return "increase_monitoring"
        elif risk_level == "medium":
            return "passive_monitoring"
        else:
            return "continue_session"
    
    def _extract_trust_factors(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trust factors from analysis"""
        factors = {}
        
        # Add key behavioral features
        features = analysis.get("features", {})
        factors["behavioral_consistency"] = features.get("touch_variability", 0.0)
        factors["navigation_pattern"] = features.get("navigation_speed", 0.0)
        factors["device_handling"] = features.get("device_stability", 0.0)
        
        # Add anomaly information
        anomalies = analysis.get("anomalies", [])
        factors["anomaly_count"] = len(anomalies)
        factors["highest_anomaly_score"] = max([a.anomaly_score for a in anomalies], default=0.0)
        
        # Add model confidence
        factors["model_confidence"] = analysis.get("confidence", 0.5)
        
        return factors
    
    async def _update_trust_profile(self, profile: TrustProfile, session: BehavioralSession, decision: TrustDecision):
        """Update trust profile with new decision"""
        # Update profile with AI interface
        await self.ai_interface.update_trust_profile(profile, session)
        
        # Update trust scoring parameters
        if decision.trust_score < self.warning_threshold:
            profile.base_trust = max(profile.base_trust * 0.98, 50.0)
        elif decision.trust_score > self.safe_threshold:
            profile.base_trust = min(profile.base_trust * 1.01, 95.0)
        
        # Update anomaly count
        if decision.risk_level in ["high", "critical"]:
            profile.anomaly_count += 1
        
        # Update false positive tracking (simplified)
        if decision.risk_level == "high" and decision.confidence < 0.7:
            profile.false_positive_count += 1
    
    async def _store_trust_decision(self, user_id: str, device_id: str, decision: TrustDecision):
        """Store trust decision in history"""
        profile_key = f"{user_id}_{device_id}"
        
        if profile_key not in self.trust_history:
            self.trust_history[profile_key] = []
        
        # Add decision to history
        self.trust_history[profile_key].append(decision)
        
        # Limit history size
        if len(self.trust_history[profile_key]) > 100:
            self.trust_history[profile_key] = self.trust_history[profile_key][-100:]
    
    def _get_fallback_decision(self) -> TrustDecision:
        """Get fallback decision when evaluation fails"""
        return TrustDecision(
            trust_score=self.default_trust_score,
            risk_level="medium",
            recommended_action="passive_monitoring",
            confidence=0.5,
            factors={"error": "evaluation_failed"},
            timestamp=datetime.now()
        )
    
    async def get_trust_trends(self, user_id: str, device_id: str, days: int = 7) -> Dict[str, Any]:
        """Get trust trends for a user over specified days"""
        profile_key = f"{user_id}_{device_id}"
        history = self.trust_history.get(profile_key, [])
        
        # Filter by time period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [d for d in history if d.timestamp >= cutoff_date]
        
        if not recent_history:
            return {"error": "No trust history found"}
        
        # Calculate trends
        trust_scores = [d.trust_score for d in recent_history]
        risk_levels = [d.risk_level for d in recent_history]
        
        # Calculate statistics
        avg_trust = sum(trust_scores) / len(trust_scores)
        min_trust = min(trust_scores)
        max_trust = max(trust_scores)
        
        # Calculate risk distribution
        risk_distribution = {}
        for level in risk_levels:
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        # Calculate trend direction
        if len(trust_scores) >= 2:
            recent_avg = sum(trust_scores[-5:]) / min(5, len(trust_scores))
            older_avg = sum(trust_scores[:-5]) / max(1, len(trust_scores) - 5)
            trend = "improving" if recent_avg > older_avg else "declining"
        else:
            trend = "stable"
        
        return {
            "period_days": days,
            "total_evaluations": len(recent_history),
            "average_trust": avg_trust,
            "min_trust": min_trust,
            "max_trust": max_trust,
            "risk_distribution": risk_distribution,
            "trend": trend,
            "trust_scores": trust_scores[-20:],  # Last 20 scores
            "timestamps": [d.timestamp.isoformat() for d in recent_history[-20:]]
        }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get trust service performance metrics"""
        return {
            "total_evaluations": self.total_evaluations,
            "active_profiles": len(self.trust_profiles),
            "active_sessions": len(self.session_cache),
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
            "trust_thresholds": {
                "critical": self.critical_threshold,
                "warning": self.warning_threshold,
                "safe": self.safe_threshold
            }
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.session_cache.items():
            if session.end_time and (current_time - session.end_time) > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_cache[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
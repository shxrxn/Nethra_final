"""
Trust Service - Enhanced with caching, encryption, and lockout functionality
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.ai_interface import AIInterface

logger = logging.getLogger(__name__)

class TrustService:
    """Enhanced service for managing trust scores and session validation"""
    
    def __init__(self, ai_interface: AIInterface, db_manager, cache_service, encryption_service):
        self.ai_interface = ai_interface
        self.db_manager = db_manager
        self.cache_service = cache_service
        self.encryption_service = encryption_service
        self.session_timeout = timedelta(minutes=30)
        self.trust_threshold_low = 40.0
        self.trust_threshold_medium = 60.0
        self.trust_threshold_high = 80.0
        self.locked_sessions = set()
        self.lockout_timers = {}
    
    async def create_session(self, user_id: str, device_info: Dict) -> str:
        """Create a new session with enhanced security"""
        try:
            session_id = f"session_{user_id}_{datetime.utcnow().timestamp()}"
            
            # Check if user exists
            user_data = await self.db_manager.execute_query(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            
            is_new_user = not user_data
            initial_trust = 95.0 if is_new_user else 85.0  # Higher trust for new users
            
            # Create session in database
            from database.models import SessionModel
            await SessionModel.create_session(session_id, user_id, json.dumps(device_info))
            
            # Cache session data
            session_data = {
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "trust_index": initial_trust,
                "risk_level": "LOW",
                "is_active": True,
                "is_new_user": is_new_user
            }
            
            await self.cache_service.cache_session_data(session_id, session_data)
            
            logger.info(f"Created session {session_id} for user {user_id} (new_user: {is_new_user})")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def update_session_trust(self, session_id: str, trust_score: float, risk_level: str):
        """Update session trust score with caching"""
        try:
            # Update in database
            from database.models import SessionModel
            await SessionModel.update_session_trust(session_id, trust_score, risk_level)
            
            # Update cache
            cached_session = await self.cache_service.get_session_data(session_id)
            if cached_session:
                cached_session["trust_index"] = trust_score
                cached_session["risk_level"] = risk_level
                cached_session["last_activity"] = datetime.utcnow().isoformat()
                await self.cache_service.cache_session_data(session_id, cached_session)
            
            # Store encrypted trust history
            trust_data = {
                "trust_score": trust_score,
                "risk_level": risk_level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            encrypted_data = self.encryption_service.encrypt_data(trust_data)
            
            logger.info(f"Updated trust score for session {session_id}: {trust_score}")
            
        except Exception as e:
            logger.error(f"Failed to update session trust: {str(e)}")
            raise
    
    async def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get session status with caching"""
        try:
            # Try cache first
            cached_session = await self.cache_service.get_session_data(session_id)
            if cached_session:
                return cached_session
            
            # Fallback to database
            from database.models import SessionModel
            session_data = await SessionModel.get_session(session_id)
            
            if session_data:
                # Cache for future requests
                await self.cache_service.cache_session_data(session_id, session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session status: {str(e)}")
            return None
    
    async def validate_session(self, session_id: str) -> bool:
        """Enhanced session validation"""
        try:
            # Check if session is locked
            if session_id in self.locked_sessions:
                return False
            
            session_data = await self.get_session_status(session_id)
            
            if not session_data:
                return False
            
            # Check if session is active
            if not session_data.get('is_active', False):
                return False
            
            # Check if session has expired
            last_activity = datetime.fromisoformat(session_data.get('last_activity', datetime.utcnow().isoformat()))
            if datetime.utcnow() - last_activity > self.session_timeout:
                await self.terminate_session(session_id)
                return False
            
            # Check trust level
            trust_score = session_data.get('trust_index', 0)
            if trust_score < self.trust_threshold_low:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}")
            return False
    
    async def lock_session(self, session_id: str) -> bool:
        """Lock session immediately"""
        try:
            self.locked_sessions.add(session_id)
            
            # Update database
            await self.db_manager.execute_update(
                "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
                (session_id,)
            )
            
            # Clear cache
            await self.cache_service.delete(f"session_{session_id}")
            
            # Log security incident
            from database.models import SecurityModel
            await SecurityModel.log_security_incident(
                session_id,
                "SESSION_LOCKED",
                "HIGH",
                {"reason": "Trust score below threshold", "timestamp": datetime.utcnow().isoformat()}
            )
            
            logger.warning(f"Session {session_id} locked due to low trust score")
            return True
            
        except Exception as e:
            logger.error(f"Failed to lock session: {str(e)}")
            return False
    
    async def is_session_locked(self, session_id: str) -> bool:
        """Check if session is locked"""
        return session_id in self.locked_sessions
    
    async def schedule_lockout(self, session_id: str, delay_seconds: int):
        """Schedule automatic session lockout"""
        try:
            async def lockout_task():
                await asyncio.sleep(delay_seconds)
                await self.lock_session(session_id)
                
                # Remove from timer tracking
                if session_id in self.lockout_timers:
                    del self.lockout_timers[session_id]
            
            # Cancel existing timer if any
            if session_id in self.lockout_timers:
                self.lockout_timers[session_id].cancel()
            
            # Schedule new lockout
            task = asyncio.create_task(lockout_task())
            self.lockout_timers[session_id] = task
            
            logger.info(f"Scheduled lockout for session {session_id} in {delay_seconds} seconds")
            
        except Exception as e:
            logger.error(f"Failed to schedule lockout: {str(e)}")
    
    async def terminate_session(self, session_id: str):
        """Terminate a session"""
        try:
            # Cancel any pending lockout
            if session_id in self.lockout_timers:
                self.lockout_timers[session_id].cancel()
                del self.lockout_timers[session_id]
            
            # Remove from locked sessions
            self.locked_sessions.discard(session_id)
            
            # Update database
            from database.models import SessionModel
            await SessionModel.terminate_session(session_id)
            
            # Clear cache
            await self.cache_service.delete(f"session_{session_id}")
            
            logger.info(f"Terminated session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to terminate session: {str(e)}")
            raise
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        try:
            from database.models import SessionModel
            return await SessionModel.get_user_sessions(user_id)
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return []
    
    async def get_trust_analytics(self, session_id: str) -> Dict:
        """Get trust analytics for a session"""
        try:
            from database.models import TrustScoreModel
            trust_history = await TrustScoreModel.get_trust_history(session_id)
            
            if not trust_history:
                return {"average_trust": 0, "trust_trend": "STABLE", "data_points": 0}
            
            scores = [entry["trust_score"] for entry in trust_history]
            
            analytics = {
                "average_trust": sum(scores) / len(scores),
                "min_trust": min(scores),
                "max_trust": max(scores),
                "data_points": len(scores),
                "trust_trend": self._calculate_trend(scores),
                "risk_assessment": self._assess_risk_level(scores)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get trust analytics: {str(e)}")
            return {}
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trust trend"""
        if len(scores) < 3:
            return "STABLE"
        
        recent_avg = sum(scores[-3:]) / 3
        earlier_avg = sum(scores[:-3]) / len(scores[:-3]) if len(scores) > 3 else recent_avg
        
        if recent_avg > earlier_avg + 5:
            return "INCREASING"
        elif recent_avg < earlier_avg - 5:
            return "DECREASING"
        else:
            return "STABLE"
    
    def _assess_risk_level(self, scores: List[float]) -> str:
        """Assess overall risk level"""
        if not scores:
            return "UNKNOWN"
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 80:
            return "LOW"
        elif avg_score >= 60:
            return "MEDIUM"
        elif avg_score >= 40:
            return "HIGH"
        else:
            return "CRITICAL"
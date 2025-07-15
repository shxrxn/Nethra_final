"""
Main API Endpoints for NETHRA Backend
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from services.ai_interface import AIModelInterface
from services.trust_service import TrustService
from services.behavioral_analyzer import BehavioralAnalyzer
from services.tamper_detection import TamperDetector
from services.mirage_controller import MirageController
from models.behavioral_models import (
    BehavioralSession, TouchPattern, SwipePattern, DeviceMotion,
    NavigationPattern, TransactionPattern, TypingPattern
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class BehavioralDataRequest(BaseModel):
    user_id: str
    device_id: str
    session_id: str
    touch_patterns: List[TouchPattern] = []
    swipe_patterns: List[SwipePattern] = []
    device_motions: List[DeviceMotion] = []
    navigation_patterns: List[NavigationPattern] = []
    transaction_patterns: List[TransactionPattern] = []
    typing_patterns: List[TypingPattern] = []
    app_version: str = "1.0.0"
    device_model: str = "unknown"
    os_version: str = "unknown"
    location_context: Optional[str] = None
    network_context: Optional[str] = None

class TrustEvaluationResponse(BaseModel):
    trust_score: float
    risk_level: str
    recommended_action: str
    confidence: float
    anomalies: List[Dict[str, Any]]
    mirage_activated: bool = False
    mirage_data: Optional[Dict[str, Any]] = None
    timestamp: str

class ChallengeResponseRequest(BaseModel):
    session_id: str
    challenge_id: str
    response: str
    response_time: float
    behavioral_data: Optional[Dict[str, Any]] = None

# Dependency injection
async def get_ai_interface() -> AIModelInterface:
    from main import app
    return app.state.ai_interface

async def get_trust_service() -> TrustService:
    from main import app
    return app.state.trust_service

async def get_behavioral_analyzer() -> BehavioralAnalyzer:
    from main import app
    return app.state.behavioral_analyzer

async def get_tamper_detector() -> TamperDetector:
    from main import app
    return app.state.tamper_detector

async def get_mirage_controller() -> MirageController:
    from main import app
    return app.state.mirage_controller

@router.post("/analyze-behavior", response_model=TrustEvaluationResponse)
async def analyze_behavior(
    request: BehavioralDataRequest,
    background_tasks: BackgroundTasks,
    trust_service: TrustService = Depends(get_trust_service),
    behavioral_analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer),
    tamper_detector: TamperDetector = Depends(get_tamper_detector),
    mirage_controller: MirageController = Depends(get_mirage_controller)
):
    """
    Analyze behavioral data and return trust evaluation
    """
    try:
        # Create behavioral session
        session = BehavioralSession(
            session_id=request.session_id,
            user_id=request.user_id,
            device_id=request.device_id,
            start_time=datetime.now(),
            touch_patterns=request.touch_patterns,
            swipe_patterns=request.swipe_patterns,
            device_motions=request.device_motions,
            navigation_patterns=request.navigation_patterns,
            transaction_patterns=request.transaction_patterns,
            typing_patterns=request.typing_patterns,
            app_version=request.app_version,
            device_model=request.device_model,
            os_version=request.os_version,
            location_context=request.location_context,
            network_context=request.network_context
        )
        
        # Perform security check
        security_check = await tamper_detector.perform_security_check(
            request.user_id, request.device_id, request.session_id
        )
        
        # If tampering detected, activate mirage immediately
        if security_check["tamper_detected"]:
            mirage_response = await mirage_controller.activate_mirage(
                request.user_id, request.device_id, 0.0, "critical", []
            )
            
            return TrustEvaluationResponse(
                trust_score=0.0,
                risk_level="critical",
                recommended_action="activate_mirage",
                confidence=1.0,
                anomalies=[{
                    "type": "tamper_detection",
                    "severity": "critical",
                    "details": security_check["checks"]
                }],
                mirage_activated=True,
                mirage_data=mirage_response.get("mirage_data"),
                timestamp=datetime.now().isoformat()
            )
        
        # Evaluate trust
        trust_decision = await trust_service.evaluate_trust(session)
        
        # Perform detailed behavioral analysis
        behavioral_analysis = await behavioral_analyzer.analyze_session(session)
        
        # Check if mirage should be activated
        mirage_activated = False
        mirage_data = None
        
        if trust_decision.recommended_action == "activate_mirage":
            mirage_response = await mirage_controller.activate_mirage(
                request.user_id,
                request.device_id,
                trust_decision.trust_score,
                trust_decision.risk_level,
                []  # Pass anomalies if available
            )
            
            mirage_activated = mirage_response.get("mirage_activated", False)
            mirage_data = mirage_response.get("mirage_data")
        
        # Schedule background tasks
        background_tasks.add_task(
            _update_behavioral_profile,
            request.user_id,
            request.device_id,
            session,
            behavioral_analysis
        )
        
        return TrustEvaluationResponse(
            trust_score=trust_decision.trust_score,
            risk_level=trust_decision.risk_level,
            recommended_action=trust_decision.recommended_action,
            confidence=trust_decision.confidence,
            anomalies=[{
                "type": "behavioral",
                "score": behavioral_analysis.get("overall_consistency", 0.5),
                "details": behavioral_analysis
            }],
            mirage_activated=mirage_activated,
            mirage_data=mirage_data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in behavior analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Behavior analysis failed")

@router.post("/challenge-response")
async def process_challenge_response(
    request: ChallengeResponseRequest,
    mirage_controller: MirageController = Depends(get_mirage_controller)
):
    """
    Process cognitive challenge response
    """
    try:
        result = await mirage_controller.process_challenge_response(
            request.session_id,
            request.challenge_id,
            request.response,
            request.response_time
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing challenge response: {str(e)}")
        raise HTTPException(status_code=500, detail="Challenge processing failed")

@router.get("/trust-profile/{user_id}/{device_id}")
async def get_trust_profile(
    user_id: str,
    device_id: str,
    trust_service: TrustService = Depends(get_trust_service)
):
    """
    Get trust profile for user-device combination
    """
    try:
        profile = await trust_service.get_trust_profile(user_id, device_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Trust profile not found")
        
        return {
            "user_id": profile.user_id,
            "device_id": profile.device_id,
            "base_trust": profile.base_trust,
            "session_count": profile.session_count,
            "total_interactions": profile.total_interactions,
            "anomaly_count": profile.anomaly_count,
            "false_positive_count": profile.false_positive_count,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trust profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trust profile")

@router.get("/trust-trends/{user_id}/{device_id}")
async def get_trust_trends(
    user_id: str,
    device_id: str,
    days: int = 7,
    trust_service: TrustService = Depends(get_trust_service)
):
    """
    Get trust trends for user over specified days
    """
    try:
        trends = await trust_service.get_trust_trends(user_id, device_id, days)
        return trends
        
    except Exception as e:
        logger.error(f"Error getting trust trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trust trends")

@router.get("/real-time-analysis/{user_id}/{device_id}")
async def get_real_time_analysis(
    user_id: str,
    device_id: str,
    behavioral_analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
):
    """
    Get real-time behavioral analysis
    """
    try:
        analysis = await behavioral_analyzer.get_real_time_analysis(user_id, device_id)
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting real-time analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get real-time analysis")

@router.get("/security-status/{user_id}/{device_id}")
async def get_security_status(
    user_id: str,
    device_id: str,
    tamper_detector: TamperDetector = Depends(get_tamper_detector)
):
    """
    Get current security status
    """
    try:
        # Perform quick security check
        security_check = await tamper_detector.perform_security_check(
            user_id, device_id, f"status_check_{int(datetime.now().timestamp())}"
        )
        
        return security_check
        
    except Exception as e:
        logger.error(f"Error getting security status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get security status")

@router.get("/mirage-sessions")
async def get_active_mirage_sessions(
    mirage_controller: MirageController = Depends(get_mirage_controller)
):
    """
    Get all active mirage sessions
    """
    try:
        sessions = await mirage_controller.get_active_sessions()
        return {"active_sessions": sessions}
        
    except Exception as e:
        logger.error(f"Error getting mirage sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get mirage sessions")

@router.post("/deactivate-mirage/{session_id}")
async def deactivate_mirage_session(
    session_id: str,
    reason: str = "manual",
    mirage_controller: MirageController = Depends(get_mirage_controller)
):
    """
    Deactivate mirage session
    """
    try:
        result = await mirage_controller.deactivate_mirage(session_id, reason)
        return result
        
    except Exception as e:
        logger.error(f"Error deactivating mirage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to deactivate mirage")

@router.get("/system-metrics")
async def get_system_metrics(
    ai_interface: AIModelInterface = Depends(get_ai_interface),
    trust_service: TrustService = Depends(get_trust_service),
    behavioral_analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer),
    tamper_detector: TamperDetector = Depends(get_tamper_detector),
    mirage_controller: MirageController = Depends(get_mirage_controller)
):
    """
    Get comprehensive system metrics
    """
    try:
        metrics = {
            "ai_model": await ai_interface.get_model_performance(),
            "trust_service": await trust_service.get_service_metrics(),
            "behavioral_analyzer": await behavioral_analyzer.get_service_metrics(),
            "tamper_detector": await tamper_detector.get_security_metrics(),
            "mirage_controller": await mirage_controller.get_mirage_metrics(),
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

# Background task functions
async def _update_behavioral_profile(
    user_id: str,
    device_id: str,
    session: BehavioralSession,
    analysis: Dict[str, Any]
):
    """Background task to update behavioral profile"""
    try:
        # This would typically update the user's behavioral profile
        # For now, we'll just log the update
        logger.info(f"Updated behavioral profile for user {user_id} on device {device_id}")
        
    except Exception as e:
        logger.error(f"Failed to update behavioral profile: {str(e)}")
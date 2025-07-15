"""
Authentication Endpoints for NETHRA Backend
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from services.trust_service import TrustService
from services.tamper_detection import TamperDetector

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class LoginRequest(BaseModel):
    user_id: str
    device_id: str
    credentials: Dict[str, str]  # e.g. {"password": "value"}
    device_info: Dict[str, str]
    biometric_data: Optional[Dict[str, Any]] = None

class LoginResponse(BaseModel):
    success: bool
    session_token: str
    trust_score: float
    requires_additional_auth: bool
    message: str
    timestamp: str

class SessionValidationRequest(BaseModel):
    session_token: str
    user_id: str
    device_id: str

class SessionValidationResponse(BaseModel):
    valid: bool
    trust_score: float
    remaining_time: int  # in seconds
    requires_reauth: bool
    message: str

# Mock database (replace with actual DB in production)
MOCK_USERS = {
    "user123": {
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "device_ids": ["device456", "device789"],
        "created_at": datetime.now() - timedelta(days=30)
    },
    "testuser": {
        "password_hash": hashlib.sha256("testpass".encode()).hexdigest(),
        "device_ids": ["testdevice"],
        "created_at": datetime.now() - timedelta(days=10)
    }
}

ACTIVE_SESSIONS = {}  # Replace with Redis or DB in production

# Dependency injections
async def get_trust_service() -> TrustService:
    from main import app
    return app.state.trust_service

async def get_tamper_detector() -> TamperDetector:
    from main import app
    return app.state.tamper_detector

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    trust_service: TrustService = Depends(get_trust_service),
    tamper_detector: TamperDetector = Depends(get_tamper_detector)
):
    try:
        user_data = MOCK_USERS.get(request.user_id)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        provided_password = request.credentials.get("password", "")
        password_hash = hashlib.sha256(provided_password.encode()).hexdigest()
        if password_hash != user_data["password_hash"]:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if request.device_id not in user_data["device_ids"]:
            logger.warning(f"Unregistered device login: {request.device_id}")

        security_check = await tamper_detector.perform_security_check(
            request.user_id, request.device_id, f"login_{int(datetime.now().timestamp())}"
        )

        if security_check["tamper_detected"]:
            raise HTTPException(status_code=403, detail="Security threat detected")

        trust_profile = await trust_service.get_trust_profile(request.user_id, request.device_id)
        if not trust_profile:
            trust_profile = await trust_service.create_trust_profile(request.user_id, request.device_id)

        initial_trust_score = trust_profile.base_trust
        initial_trust_score += 5.0 if request.device_id in user_data["device_ids"] else -10.0
        initial_trust_score *= security_check["security_score"]
        initial_trust_score = max(0.0, min(100.0, initial_trust_score))

        session_token = secrets.token_urlsafe(32)
        ACTIVE_SESSIONS[session_token] = {
            "user_id": request.user_id,
            "device_id": request.device_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "trust_score": initial_trust_score,
            "device_info": request.device_info,
            "security_score": security_check["security_score"]
        }

        requires_additional_auth = initial_trust_score < 70.0

        return LoginResponse(
            success=True,
            session_token=session_token,
            trust_score=initial_trust_score,
            requires_additional_auth=requires_additional_auth,
            message="Login successful" if not requires_additional_auth else "Additional authentication required",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/validate-session", response_model=SessionValidationResponse)
async def validate_session(
    request: SessionValidationRequest,
    trust_service: TrustService = Depends(get_trust_service)
):
    try:
        session_data = ACTIVE_SESSIONS.get(request.session_token)
        if not session_data:
            return SessionValidationResponse(valid=False, trust_score=0.0, remaining_time=0, requires_reauth=True, message="Session not found")

        if session_data["user_id"] != request.user_id or session_data["device_id"] != request.device_id:
            return SessionValidationResponse(valid=False, trust_score=0.0, remaining_time=0, requires_reauth=True, message="Session mismatch")

        session_age = datetime.now() - session_data["created_at"]
        if session_age > timedelta(hours=24):
            del ACTIVE_SESSIONS[request.session_token]
            return SessionValidationResponse(valid=False, trust_score=0.0, remaining_time=0, requires_reauth=True, message="Session expired")

        if datetime.now() - session_data["last_activity"] > timedelta(hours=2):
            del ACTIVE_SESSIONS[request.session_token]
            return SessionValidationResponse(valid=False, trust_score=0.0, remaining_time=0, requires_reauth=True, message="Session inactive")

        session_data["last_activity"] = datetime.now()
        trust_profile = await trust_service.get_trust_profile(request.user_id, request.device_id)
        trust_score = trust_profile.base_trust if trust_profile else session_data["trust_score"]

        remaining = int((timedelta(hours=24) - session_age).total_seconds())
        return SessionValidationResponse(
            valid=True,
            trust_score=trust_score,
            remaining_time=remaining,
            requires_reauth=trust_score < 50.0,
            message="Session valid"
        )
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Session validation failed")

@router.post("/logout")
async def logout(session_token: str):
    try:
        session_data = ACTIVE_SESSIONS.pop(session_token, None)
        if session_data:
            logger.info(f"User {session_data['user_id']} logged out")
        return {"success": True, "message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.post("/register-device")
async def register_device(user_id: str, device_id: str, device_info: Dict[str, str], verification_code: str):
    try:
        if verification_code != "123456":
            raise HTTPException(status_code=400, detail="Invalid verification code")

        user_data = MOCK_USERS.get(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        if device_id not in user_data["device_ids"]:
            user_data["device_ids"].append(device_id)

        logger.info(f"Device {device_id} registered for user {user_id}")
        return {"success": True, "message": "Device registered", "device_id": device_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Device registration failed")

@router.get("/session-info/{session_token}")
async def get_session_info(session_token: str):
    try:
        session_data = ACTIVE_SESSIONS.get(session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "user_id": session_data["user_id"],
            "device_id": session_data["device_id"],
            "created_at": session_data["created_at"].isoformat(),
            "last_activity": session_data["last_activity"].isoformat(),
            "trust_score": session_data["trust_score"],
            "device_info": session_data["device_info"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session info error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session info")

@router.get("/active-sessions/{user_id}")
async def get_active_sessions(user_id: str):
    try:
        sessions = [
            {
                "session_token": token[:16] + "...",
                "device_id": data["device_id"],
                "created_at": data["created_at"].isoformat(),
                "last_activity": data["last_activity"].isoformat(),
                "trust_score": data["trust_score"]
            }
            for token, data in ACTIVE_SESSIONS.items()
            if data["user_id"] == user_id
        ]
        return {"active_sessions": sessions}
    except Exception as e:
        logger.error(f"Active sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active sessions")

@router.post("/terminate-session")
async def terminate_session(session_token: str, user_id: str):
    try:
        session_data = ACTIVE_SESSIONS.get(session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        if session_data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        del ACTIVE_SESSIONS[session_token]
        logger.info(f"Session terminated for user {user_id}")
        return {"success": True, "message": "Session terminated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Terminate session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to terminate session")

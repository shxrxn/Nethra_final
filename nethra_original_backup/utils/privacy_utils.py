"""
Privacy Utilities - Privacy-related helper functions
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class PrivacyUtils:
    """Privacy utility functions for GDPR/DPDP compliance"""
    
    @staticmethod
    async def get_compliance_info() -> Dict[str, Any]:
        """Get privacy compliance information"""
        try:
            return {
                "compliance_standards": ["GDPR", "DPDP", "CCPA"],
                "data_processing_principles": [
                    "On-device processing",
                    "Minimal data collection",
                    "Purpose limitation",
                    "Data minimization",
                    "Accuracy",
                    "Storage limitation",
                    "Integrity and confidentiality"
                ],
                "user_rights": [
                    "Right to access",
                    "Right to rectification",
                    "Right to erasure",
                    "Right to restrict processing",
                    "Right to data portability",
                    "Right to object"
                ],
                "data_retention": {
                    "behavioral_data": "On-device only, not transmitted",
                    "session_data": "1 hour",
                    "trust_scores": "24 hours",
                    "security_logs": "7 days",
                    "mirage_logs": "24 hours"
                },
                "encryption": {
                    "data_at_rest": "AES-256",
                    "data_in_transit": "TLS 1.3",
                    "key_management": "Hardware security modules"
                },
                "privacy_by_design": True,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance info: {str(e)}")
            raise
    
    @staticmethod
    def anonymize_data(data: Dict) -> Dict:
        """Anonymize sensitive data"""
        try:
            anonymized = data.copy()
            
            # Fields to anonymize
            sensitive_fields = [
                "user_id", "email", "phone", "name", "address",
                "ip_address", "device_id", "session_id"
            ]
            
            for field in sensitive_fields:
                if field in anonymized:
                    # Generate consistent hash for anonymization
                    original_value = str(anonymized[field])
                    anonymized[field] = PrivacyUtils._generate_anonymous_id(original_value)
            
            # Remove timestamp precision for privacy
            if "timestamp" in anonymized:
                timestamp = datetime.fromisoformat(anonymized["timestamp"])
                # Round to nearest hour for privacy
                rounded_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
                anonymized["timestamp"] = rounded_timestamp.isoformat()
            
            return anonymized
            
        except Exception as e:
            logger.error(f"Data anonymization failed: {str(e)}")
            return data
    
    @staticmethod
    def _generate_anonymous_id(original_value: str) -> str:
        """Generate anonymous ID from original value"""
        try:
            # Use consistent hashing for anonymization
            hash_value = hashlib.sha256(original_value.encode()).hexdigest()
            return f"anon_{hash_value[:8]}"
            
        except Exception as e:
            logger.error(f"Anonymous ID generation failed: {str(e)}")
            return "anon_unknown"
    
    @staticmethod
    def mask_personal_data(data: Dict) -> Dict:
        """Mask personal data for logging"""
        try:
            masked = data.copy()
            
            # Fields to mask
            mask_fields = {
                "user_id": lambda x: f"user_{x[:4]}****",
                "email": lambda x: f"{x[:3]}****@{x.split('@')[1]}" if '@' in x else "****",
                "phone": lambda x: f"****{x[-4:]}" if len(x) > 4 else "****",
                "ip_address": lambda x: f"{x.split('.')[0]}.*.*.{x.split('.')[-1]}" if '.' in x else "****",
                "device_id": lambda x: f"device_{x[:6]}****",
                "session_id": lambda x: f"session_{x[:8]}****"
            }
            
            for field, mask_func in mask_fields.items():
                if field in masked and masked[field]:
                    masked[field] = mask_func(str(masked[field]))
            
            return masked
            
        except Exception as e:
            logger.error(f"Data masking failed: {str(e)}")
            return data
    
    @staticmethod
    def validate_data_retention(data_type: str, timestamp: datetime) -> bool:
        """Validate if data should be retained based on retention policy"""
        try:
            retention_periods = {
                "session_data": timedelta(hours=1),
                "trust_scores": timedelta(days=1),
                "security_logs": timedelta(days=7),
                "mirage_logs": timedelta(days=1),
                "behavioral_data": timedelta(seconds=0),  # Not retained
                "user_profile": timedelta(days=30),
                "analytics": timedelta(days=90)
            }
            
            if data_type not in retention_periods:
                return False
            
            retention_period = retention_periods[data_type]
            return datetime.utcnow() - timestamp <= retention_period
            
        except Exception as e:
            logger.error(f"Data retention validation failed: {str(e)}")
            return False
    
    @staticmethod
    def generate_privacy_report(user_id: str) -> Dict:
        """Generate privacy report for user"""
        try:
            return {
                "user_id": PrivacyUtils._generate_anonymous_id(user_id),
                "report_generated": datetime.utcnow().isoformat(),
                "data_categories": {
                    "behavioral_data": {
                        "collected": True,
                        "stored": False,
                        "location": "On-device only",
                        "purpose": "Continuous authentication",
                        "retention": "Real-time processing only"
                    },
                    "trust_scores": {
                        "collected": True,
                        "stored": True,
                        "location": "Server (encrypted)",
                        "purpose": "Security monitoring",
                        "retention": "24 hours"
                    },
                    "session_data": {
                        "collected": True,
                        "stored": True,
                        "location": "Server (encrypted)",
                        "purpose": "Session management",
                        "retention": "1 hour"
                    },
                    "security_logs": {
                        "collected": True,
                        "stored": True,
                        "location": "Server (encrypted)",
                        "purpose": "Security monitoring",
                        "retention": "7 days"
                    }
                },
                "processing_activities": [
                    "Behavioral pattern analysis",
                    "Trust score calculation",
                    "Anomaly detection",
                    "Mirage interface activation"
                ],
                "legal_basis": "Legitimate interest (security)",
                "third_party_sharing": False,
                "user_rights_available": [
                    "Access", "Rectification", "Erasure", 
                    "Restrict processing", "Data portability", "Object"
                ],
                "contact_info": {
                    "dpo_email": "privacy@nethra.app",
                    "support_email": "support@nethra.app"
                }
            }
            
        except Exception as e:
            logger.error(f"Privacy report generation failed: {str(e)}")
            return {}
    
    @staticmethod
    def check_consent_requirements(data_type: str, processing_purpose: str) -> Dict:
        """Check if consent is required for data processing"""
        try:
            # Define consent requirements
            consent_required = {
                "behavioral_data": {
                    "continuous_auth": False,  # Legitimate interest
                    "analytics": True,         # Consent required
                    "marketing": True          # Consent required
                },
                "location_data": {
                    "fraud_detection": False,  # Legitimate interest
                    "personalization": True,   # Consent required
                    "marketing": True          # Consent required
                },
                "biometric_data": {
                    "authentication": False,   # Legitimate interest
                    "analytics": True,         # Consent required
                    "research": True           # Consent required
                }
            }
            
            requires_consent = consent_required.get(data_type, {}).get(processing_purpose, True)
            
            return {
                "consent_required": requires_consent,
                "legal_basis": "Consent" if requires_consent else "Legitimate interest",
                "data_type": data_type,
                "processing_purpose": processing_purpose,
                "gdpr_article": "6(1)(a)" if requires_consent else "6(1)(f)"
            }
            
        except Exception as e:
            logger.error(f"Consent requirement check failed: {str(e)}")
            return {"consent_required": True, "legal_basis": "Consent"}
    
    @staticmethod
    def sanitize_logs(log_data: Dict) -> Dict:
        """Sanitize log data for privacy compliance"""
        try:
            sanitized = log_data.copy()
            
            # Remove or mask sensitive fields
            sensitive_patterns = [
                "password", "token", "key", "secret", "pin", "otp",
                "ssn", "credit_card", "bank_account", "phone", "email"
            ]
            
            def sanitize_value(key: str, value: Any) -> Any:
                if isinstance(value, str):
                    key_lower = key.lower()
                    for pattern in sensitive_patterns:
                        if pattern in key_lower:
                            return "***REDACTED***"
                    return value
                elif isinstance(value, dict):
                    return {k: sanitize_value(k, v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [sanitize_value(f"item_{i}", item) for i, item in enumerate(value)]
                else:
                    return value
            
            for key, value in sanitized.items():
                sanitized[key] = sanitize_value(key, value)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Log sanitization failed: {str(e)}")
            return log_data
    
    @staticmethod
    def calculate_privacy_score(data_processing: Dict) -> Dict:
        """Calculate privacy score for data processing"""
        try:
            score = 100  # Start with perfect score
            
            # Deduct points for various privacy risks
            if data_processing.get("data_stored", False):
                score -= 10
            
            if data_processing.get("third_party_sharing", False):
                score -= 20
            
            if data_processing.get("cross_border_transfer", False):
                score -= 15
            
            if not data_processing.get("encryption_at_rest", False):
                score -= 25
            
            if not data_processing.get("encryption_in_transit", False):
                score -= 20
            
            if data_processing.get("retention_period", 0) > 30:  # Days
                score -= 10
            
            if not data_processing.get("anonymization", False):
                score -= 10
            
            # Bonus points for privacy-enhancing features
            if data_processing.get("on_device_processing", False):
                score += 15
            
            if data_processing.get("differential_privacy", False):
                score += 10
            
            score = max(0, min(100, score))
            
            return {
                "privacy_score": score,
                "rating": PrivacyUtils._get_privacy_rating(score),
                "recommendations": PrivacyUtils._get_privacy_recommendations(score, data_processing)
            }
            
        except Exception as e:
            logger.error(f"Privacy score calculation failed: {str(e)}")
            return {"privacy_score": 50, "rating": "MEDIUM"}
    
    @staticmethod
    def _get_privacy_rating(score: int) -> str:
        """Get privacy rating based on score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GOOD"
        elif score >= 70:
            return "FAIR"
        elif score >= 60:
            return "POOR"
        else:
            return "VERY_POOR"
    
    @staticmethod
    def _get_privacy_recommendations(score: int, data_processing: Dict) -> List[str]:
        """Get privacy recommendations"""
        recommendations = []
        
        if not data_processing.get("encryption_at_rest", False):
            recommendations.append("Enable encryption at rest")
        
        if not data_processing.get("encryption_in_transit", False):
            recommendations.append("Enable encryption in transit")
        
        if data_processing.get("retention_period", 0) > 30:
            recommendations.append("Reduce data retention period")
        
        if not data_processing.get("anonymization", False):
            recommendations.append("Implement data anonymization")
        
        if data_processing.get("third_party_sharing", False):
            recommendations.append("Minimize third-party data sharing")
        
        if not data_processing.get("on_device_processing", False):
            recommendations.append("Consider on-device processing")
        
        if score < 80:
            recommendations.append("Conduct privacy impact assessment")
        
        return recommendations
    
    @staticmethod
    def generate_data_map(application_components: List[str]) -> Dict:
        """Generate data flow map for privacy compliance"""
        try:
            data_map = {
                "components": {},
                "data_flows": [],
                "privacy_boundaries": [],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            for component in application_components:
                data_map["components"][component] = {
                    "data_types": PrivacyUtils._get_component_data_types(component),
                    "processing_purposes": PrivacyUtils._get_component_purposes(component),
                    "retention_period": PrivacyUtils._get_component_retention(component),
                    "encryption": True,
                    "anonymization": component != "user_interface"
                }
            
            return data_map
            
        except Exception as e:
            logger.error(f"Data map generation failed: {str(e)}")
            return {}
    
    @staticmethod
    def _get_component_data_types(component: str) -> List[str]:
        """Get data types for component"""
        component_data = {
            "behavioral_analyzer": ["touch_patterns", "swipe_patterns", "device_motion"],
            "trust_service": ["trust_scores", "session_data", "risk_assessments"],
            "mirage_controller": ["interaction_logs", "challenge_responses"],
            "tamper_detector": ["security_events", "integrity_checks"],
            "user_interface": ["user_inputs", "display_data"]
        }
        return component_data.get(component, [])
    
    @staticmethod
    def _get_component_purposes(component: str) -> List[str]:
        """Get processing purposes for component"""
        component_purposes = {
            "behavioral_analyzer": ["continuous_authentication", "anomaly_detection"],
            "trust_service": ["security_monitoring", "risk_assessment"],
            "mirage_controller": ["fraud_prevention", "attacker_deception"],
            "tamper_detector": ["security_monitoring", "integrity_verification"],
            "user_interface": ["user_interaction", "feedback_display"]
        }
        return component_purposes.get(component, [])
    
    @staticmethod
    def _get_component_retention(component: str) -> str:
        """Get retention period for component"""
        component_retention = {
            "behavioral_analyzer": "Real-time only",
            "trust_service": "24 hours",
            "mirage_controller": "24 hours",
            "tamper_detector": "7 days",
            "user_interface": "Session only"
        }
        return component_retention.get(component, "Not specified")
"""
Privacy Utilities for NETHRA Backend
GDPR and DPDP compliance utilities
"""

import logging
import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DataCategory(str, Enum):
    """Categories of data processed by NETHRA"""
    BEHAVIORAL = "behavioral"
    BIOMETRIC = "biometric"
    DEVICE = "device"
    LOCATION = "location"
    TRANSACTION = "transaction"
    AUTHENTICATION = "authentication"

class ProcessingPurpose(str, Enum):
    """Purposes for data processing"""
    AUTHENTICATION = "authentication"
    FRAUD_DETECTION = "fraud_detection"
    SECURITY_MONITORING = "security_monitoring"
    SYSTEM_IMPROVEMENT = "system_improvement"
    COMPLIANCE = "compliance"

class LegalBasis(str, Enum):
    """Legal basis for data processing"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

@dataclass
class DataProcessingRecord:
    """Record of data processing activity"""
    data_category: DataCategory
    purpose: ProcessingPurpose
    legal_basis: LegalBasis
    data_subject_id: str
    processing_date: datetime
    retention_period: timedelta
    data_minimized: bool
    anonymized: bool
    consent_given: bool
    processing_location: str  # "on_device" or "cloud"

@dataclass
class ConsentRecord:
    """User consent record"""
    user_id: str
    consent_id: str
    consent_date: datetime
    consent_type: str
    purposes: List[ProcessingPurpose]
    data_categories: List[DataCategory]
    consent_given: bool
    withdrawal_date: Optional[datetime] = None
    consent_version: str = "1.0"

class PrivacyUtils:
    """Privacy compliance utilities for NETHRA"""
    
    def __init__(self):
        self.processing_records: List[DataProcessingRecord] = []
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.data_retention_policies: Dict[DataCategory, timedelta] = {
            DataCategory.BEHAVIORAL: timedelta(days=90),
            DataCategory.BIOMETRIC: timedelta(days=30),
            DataCategory.DEVICE: timedelta(days=365),
            DataCategory.LOCATION: timedelta(days=7),
            DataCategory.TRANSACTION: timedelta(days=180),
            DataCategory.AUTHENTICATION: timedelta(days=30)
        }
        
        # Privacy settings
        self.data_minimization_enabled = True
        self.anonymization_enabled = True
        self.on_device_processing_only = True
        
        logger.info("Privacy Utils initialized with GDPR/DPDP compliance")
    
    def record_consent(self, user_id: str, purposes: List[ProcessingPurpose], 
                      data_categories: List[DataCategory]) -> str:
        """Record user consent"""
        consent_id = self._generate_consent_id(user_id)
        
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_id=consent_id,
            consent_date=datetime.now(),
            consent_type="explicit",
            purposes=purposes,
            data_categories=data_categories,
            consent_given=True
        )
        
        self.consent_records[consent_id] = consent_record
        
        logger.info(f"Consent recorded for user {user_id}: {consent_id}")
        return consent_id
    
    def withdraw_consent(self, user_id: str, consent_id: str) -> bool:
        """Withdraw user consent"""
        consent_record = self.consent_records.get(consent_id)
        
        if not consent_record or consent_record.user_id != user_id:
            return False
        
        consent_record.consent_given = False
        consent_record.withdrawal_date = datetime.now()
        
        logger.info(f"Consent withdrawn for user {user_id}: {consent_id}")
        return True
    
    def check_consent(self, user_id: str, purpose: ProcessingPurpose, 
                     data_category: DataCategory) -> bool:
        """Check if user has given consent for specific processing"""
        for consent_record in self.consent_records.values():
            if (consent_record.user_id == user_id and 
                consent_record.consent_given and
                purpose in consent_record.purposes and
                data_category in consent_record.data_categories):
                return True
        
        return False
    
    def record_processing_activity(self, user_id: str, data_category: DataCategory,
                                 purpose: ProcessingPurpose, legal_basis: LegalBasis,
                                 data_minimized: bool = True, anonymized: bool = False):
        """Record data processing activity"""
        # Check consent if required
        consent_given = True
        if legal_basis == LegalBasis.CONSENT:
            consent_given = self.check_consent(user_id, purpose, data_category)
        
        processing_record = DataProcessingRecord(
            data_category=data_category,
            purpose=purpose,
            legal_basis=legal_basis,
            data_subject_id=user_id,
            processing_date=datetime.now(),
            retention_period=self.data_retention_policies[data_category],
            data_minimized=data_minimized,
            anonymized=anonymized,
            consent_given=consent_given,
            processing_location="on_device" if self.on_device_processing_only else "cloud"
        )
        
        self.processing_records.append(processing_record)
        
        # Log processing activity
        logger.info(f"Processing activity recorded: {data_category.value} for {purpose.value}")
    
    def anonymize_behavioral_data(self, behavioral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize behavioral data"""
        if not self.anonymization_enabled:
            return behavioral_data
        
        anonymized_data = {}
        
        # Remove direct identifiers
        sensitive_fields = ['user_id', 'device_id', 'session_id', 'timestamp']
        
        for key, value in behavioral_data.items():
            if key in sensitive_fields:
                # Replace with anonymized version
                if key == 'user_id':
                    anonymized_data['user_hash'] = self._hash_identifier(value)
                elif key == 'device_id':
                    anonymized_data['device_hash'] = self._hash_identifier(value)
                elif key == 'session_id':
                    anonymized_data['session_hash'] = self._hash_identifier(value)
                elif key == 'timestamp':
                    # Round timestamp to hour for privacy
                    if isinstance(value, datetime):
                        anonymized_data['time_bucket'] = value.replace(minute=0, second=0, microsecond=0)
                    else:
                        anonymized_data[key] = value
            else:
                # Keep non-sensitive data
                anonymized_data[key] = value
        
        return anonymized_data
    
    def minimize_data(self, data: Dict[str, Any], purpose: ProcessingPurpose) -> Dict[str, Any]:
        """Apply data minimization based on processing purpose"""
        if not self.data_minimization_enabled:
            return data
        
        # Define minimal data sets for each purpose
        minimal_fields = {
            ProcessingPurpose.AUTHENTICATION: [
                'touch_patterns', 'swipe_patterns', 'device_motions'
            ],
            ProcessingPurpose.FRAUD_DETECTION: [
                'touch_patterns', 'swipe_patterns', 'device_motions', 
                'navigation_patterns', 'transaction_patterns'
            ],
            ProcessingPurpose.SECURITY_MONITORING: [
                'device_motions', 'navigation_patterns', 'app_version'
            ],
            ProcessingPurpose.SYSTEM_IMPROVEMENT: [
                'behavioral_features', 'trust_score', 'anomaly_scores'
            ]
        }
        
        required_fields = minimal_fields.get(purpose, list(data.keys()))
        
        # Keep only required fields
        minimized_data = {
            key: value for key, value in data.items() 
            if key in required_fields
        }
        
        return minimized_data
    
    def check_retention_period(self, processing_record: DataProcessingRecord) -> bool:
        """Check if data retention period has expired"""
        expiry_date = processing_record.processing_date + processing_record.retention_period
        return datetime.now() > expiry_date
    
    def get_expired_data(self) -> List[DataProcessingRecord]:
        """Get list of data that should be deleted due to retention policy"""
        expired_records = []
        
        for record in self.processing_records:
            if self.check_retention_period(record):
                expired_records.append(record)
        
        return expired_records
    
    def delete_expired_data(self) -> int:
        """Delete expired data according to retention policies"""
        expired_records = self.get_expired_data()
        
        # Remove expired records
        self.processing_records = [
            record for record in self.processing_records
            if not self.check_retention_period(record)
        ]
        
        deleted_count = len(expired_records)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired data records")
        
        return deleted_count
    
    def generate_privacy_report(self, user_id: str) -> Dict[str, Any]:
        """Generate privacy compliance report for user"""
        user_records = [
            record for record in self.processing_records
            if record.data_subject_id == user_id
        ]
        
        user_consents = [
            consent for consent in self.consent_records.values()
            if consent.user_id == user_id
        ]
        
        # Calculate privacy metrics
        total_processing = len(user_records)
        on_device_processing = sum(1 for r in user_records if r.processing_location == "on_device")
        anonymized_processing = sum(1 for r in user_records if r.anonymized)
        minimized_processing = sum(1 for r in user_records if r.data_minimized)
        
        report = {
            "user_id": user_id,
            "report_date": datetime.now().isoformat(),
            "processing_summary": {
                "total_processing_activities": total_processing,
                "on_device_processing_percentage": (on_device_processing / max(total_processing, 1)) * 100,
                "anonymized_processing_percentage": (anonymized_processing / max(total_processing, 1)) * 100,
                "minimized_processing_percentage": (minimized_processing / max(total_processing, 1)) * 100
            },
            "consent_summary": {
                "total_consents": len(user_consents),
                "active_consents": sum(1 for c in user_consents if c.consent_given),
                "withdrawn_consents": sum(1 for c in user_consents if not c.consent_given)
            },
            "data_categories_processed": list(set(r.data_category.value for r in user_records)),
            "processing_purposes": list(set(r.purpose.value for r in user_records)),
            "legal_bases": list(set(r.legal_basis.value for r in user_records)),
            "retention_compliance": {
                "records_within_retention": sum(1 for r in user_records if not self.check_retention_period(r)),
                "records_expired": sum(1 for r in user_records if self.check_retention_period(r))
            },
            "privacy_settings": {
                "data_minimization_enabled": self.data_minimization_enabled,
                "anonymization_enabled": self.anonymization_enabled,
                "on_device_processing_only": self.on_device_processing_only
            },
            "compliance_status": {
                "gdpr_compliant": self._check_gdpr_compliance(user_records, user_consents),
                "dpdp_compliant": self._check_dpdp_compliance(user_records, user_consents)
            }
        }
        
        return report
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR Article 20 - Right to data portability)"""
        user_records = [
            asdict(record) for record in self.processing_records
            if record.data_subject_id == user_id
        ]
        
        user_consents = [
            asdict(consent) for consent in self.consent_records.values()
            if consent.user_id == user_id
        ]
        
        # Convert datetime objects to ISO strings
        for record in user_records:
            if isinstance(record.get('processing_date'), datetime):
                record['processing_date'] = record['processing_date'].isoformat()
            if isinstance(record.get('retention_period'), timedelta):
                record['retention_period'] = str(record['retention_period'])
        
        for consent in user_consents:
            if isinstance(consent.get('consent_date'), datetime):
                consent['consent_date'] = consent['consent_date'].isoformat()
            if consent.get('withdrawal_date') and isinstance(consent['withdrawal_date'], datetime):
                consent['withdrawal_date'] = consent['withdrawal_date'].isoformat()
        
        export_data = {
            "export_info": {
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "data_format": "JSON",
                "export_version": "1.0"
            },
            "processing_records": user_records,
            "consent_records": user_consents,
            "privacy_notice": "This export contains all personal data processed by NETHRA for the specified user."
        }
        
        return export_data
    
    def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data (GDPR Article 17 - Right to erasure)"""
        # Count records before deletion
        processing_records_count = len([r for r in self.processing_records if r.data_subject_id == user_id])
        consent_records_count = len([c for c in self.consent_records.values() if c.user_id == user_id])
        
        # Delete processing records
        self.processing_records = [
            record for record in self.processing_records
            if record.data_subject_id != user_id
        ]
        
        # Delete consent records
        consent_ids_to_delete = [
            consent_id for consent_id, consent in self.consent_records.items()
            if consent.user_id == user_id
        ]
        
        for consent_id in consent_ids_to_delete:
            del self.consent_records[consent_id]
        
        deletion_result = {
            "user_id": user_id,
            "deletion_date": datetime.now().isoformat(),
            "deleted_records": {
                "processing_records": processing_records_count,
                "consent_records": consent_records_count
            },
            "deletion_successful": True
        }
        
        logger.info(f"Deleted all data for user {user_id}")
        return deletion_result
    
    def _generate_consent_id(self, user_id: str) -> str:
        """Generate unique consent ID"""
        timestamp = datetime.now().isoformat()
        data = f"{user_id}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier for anonymization"""
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def _check_gdpr_compliance(self, processing_records: List[DataProcessingRecord], 
                              consent_records: List[ConsentRecord]) -> bool:
        """Check GDPR compliance"""
        # Check if all processing has legal basis
        for record in processing_records:
            if record.legal_basis == LegalBasis.CONSENT and not record.consent_given:
                return False
        
        # Check data minimization
        minimized_count = sum(1 for r in processing_records if r.data_minimized)
        if minimized_count < len(processing_records) * 0.9:  # 90% should be minimized
            return False
        
        # Check retention periods
        expired_count = sum(1 for r in processing_records if self.check_retention_period(r))
        if expired_count > 0:
            return False
        
        return True
    
    def _check_dpdp_compliance(self, processing_records: List[DataProcessingRecord], 
                              consent_records: List[ConsentRecord]) -> bool:
        """Check DPDP (Digital Personal Data Protection) compliance"""
        # Similar to GDPR but with India-specific requirements
        
        # Check consent requirements
        consent_required_processing = [
            r for r in processing_records 
            if r.legal_basis == LegalBasis.CONSENT
        ]
        
        for record in consent_required_processing:
            if not record.consent_given:
                return False
        
        # Check data localization (processing should be on-device)
        on_device_count = sum(1 for r in processing_records if r.processing_location == "on_device")
        if on_device_count < len(processing_records):
            return False
        
        return True
    
    def get_privacy_metrics(self) -> Dict[str, Any]:
        """Get overall privacy metrics"""
        total_records = len(self.processing_records)
        
        if total_records == 0:
            return {"message": "No processing records found"}
        
        on_device_count = sum(1 for r in self.processing_records if r.processing_location == "on_device")
        anonymized_count = sum(1 for r in self.processing_records if r.anonymized)
        minimized_count = sum(1 for r in self.processing_records if r.data_minimized)
        expired_count = sum(1 for r in self.processing_records if self.check_retention_period(r))
        
        return {
            "total_processing_records": total_records,
            "on_device_processing_percentage": (on_device_count / total_records) * 100,
            "anonymized_processing_percentage": (anonymized_count / total_records) * 100,
            "minimized_processing_percentage": (minimized_count / total_records) * 100,
            "expired_records_count": expired_count,
            "active_consents": len([c for c in self.consent_records.values() if c.consent_given]),
            "withdrawn_consents": len([c for c in self.consent_records.values() if not c.consent_given]),
            "privacy_settings": {
                "data_minimization_enabled": self.data_minimization_enabled,
                "anonymization_enabled": self.anonymization_enabled,
                "on_device_processing_only": self.on_device_processing_only
            }
        }

# Global privacy utils instance
privacy_utils = PrivacyUtils()
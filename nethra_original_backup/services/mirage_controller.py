"""
Mirage Controller Service - Manages the Adaptive Mirage Interface
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MirageController:
    """Service for managing the Adaptive Mirage Interface"""
    
    def __init__(self, memory_store: Dict):
        self.memory_store = memory_store
        self.mirage_templates = {
            "banking": {
                "fake_balance": [1000, 5000, 10000, 25000],
                "fake_transactions": [
                    {"type": "credit", "amount": 500, "description": "Salary Credit"},
                    {"type": "debit", "amount": 50, "description": "ATM Withdrawal"},
                    {"type": "credit", "amount": 1000, "description": "Bonus Credit"},
                    {"type": "debit", "amount": 200, "description": "Bill Payment"}
                ],
                "fake_accounts": [
                    {"number": "****1234", "type": "Savings", "balance": 5000},
                    {"number": "****5678", "type": "Current", "balance": 2000}
                ]
            },
            "loading": {
                "fake_delays": [2, 3, 5, 8, 10],
                "fake_errors": [
                    "Network timeout",
                    "Server maintenance",
                    "Temporary unavailable",
                    "Please try again later"
                ]
            },
            "challenges": {
                "cognitive_tasks": [
                    {
                        "type": "pattern_recognition",
                        "description": "Tap the pattern you usually use",
                        "options": ["pattern1", "pattern2", "pattern3", "pattern4"]
                    },
                    {
                        "type": "color_selection",
                        "description": "Select your favorite color",
                        "options": ["red", "blue", "green", "yellow"]
                    },
                    {
                        "type": "number_sequence",
                        "description": "Complete the sequence: 2, 4, 6, ?",
                        "options": [7, 8, 9, 10]
                    }
                ]
            }
        }
    
    async def activate_mirage(self, user_id: str, session_id: str, trust_index: float) -> Dict:
        """Activate mirage interface for suspicious session"""
        try:
            # Generate mirage ID
            mirage_id = f"mirage_{session_id}_{datetime.utcnow().timestamp()}"
            
            # Determine mirage type based on trust index
            mirage_type = self._determine_mirage_type(trust_index)
            
            # Generate mirage content
            mirage_content = await self._generate_mirage_content(mirage_type, user_id)
            
            # Create cognitive challenges
            challenges = await self._create_cognitive_challenges(user_id, trust_index)
            
            # Calculate mirage duration
            duration = self._calculate_mirage_duration(trust_index)
            
            # Store mirage session
            mirage_data = {
                "mirage_id": mirage_id,
                "user_id": user_id,
                "session_id": session_id,
                "mirage_type": mirage_type,
                "trust_index": trust_index,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=duration)).isoformat(),
                "content": mirage_content,
                "challenges": challenges,
                "duration_minutes": duration,
                "interactions": [],
                "status": "ACTIVE"
            }
            
            # Store in memory
            self.memory_store["mirage_data"][mirage_id] = mirage_data
            
            # Add to active mirages
            if session_id not in self.memory_store.get("active_mirages", {}):
                if "active_mirages" not in self.memory_store:
                    self.memory_store["active_mirages"] = {}
                self.memory_store["active_mirages"][session_id] = set()
            
            self.memory_store["active_mirages"][session_id].add(mirage_id)
            
            # Log mirage activation
            await self._log_mirage_activation(user_id, session_id, mirage_id, mirage_type)
            
            # Create response
            from main import MirageResponse
            return MirageResponse(
                mirage_id=mirage_id,
                interface_type=mirage_type,
                fake_elements=mirage_content,
                cognitive_challenges=challenges,
                duration_minutes=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to activate mirage: {str(e)}")
            raise
    
    def _determine_mirage_type(self, trust_index: float) -> str:
        """Determine mirage type based on trust index"""
        if trust_index < 20:
            return "FULL_DECEPTION"
        elif trust_index < 35:
            return "BANKING_MIRAGE"
        elif trust_index < 50:
            return "LOADING_DELAYS"
        else:
            return "SUBTLE_CHALLENGES"
    
    async def _generate_mirage_content(self, mirage_type: str, user_id: str) -> List[Dict]:
        """Generate mirage content based on type"""
        try:
            content = []
            
            if mirage_type == "FULL_DECEPTION":
                # Generate complete fake banking interface
                content.extend([
                    {
                        "element_type": "balance_display",
                        "fake_balance": random.choice(self.mirage_templates["banking"]["fake_balance"]),
                        "display_format": "currency"
                    },
                    {
                        "element_type": "transaction_history",
                        "fake_transactions": random.sample(
                            self.mirage_templates["banking"]["fake_transactions"], 
                            3
                        )
                    },
                    {
                        "element_type": "account_list",
                        "fake_accounts": self.mirage_templates["banking"]["fake_accounts"]
                    },
                    {
                        "element_type": "navigation_delay",
                        "delay_seconds": random.choice([2, 3, 4, 5])
                    }
                ])
            
            elif mirage_type == "BANKING_MIRAGE":
                # Generate banking-specific deception
                content.extend([
                    {
                        "element_type": "balance_display",
                        "fake_balance": random.choice(self.mirage_templates["banking"]["fake_balance"][:2]),
                        "display_format": "currency"
                    },
                    {
                        "element_type": "transaction_limit",
                        "message": "Daily transaction limit reached",
                        "limit_amount": 1000
                    },
                    {
                        "element_type": "network_delay",
                        "delay_seconds": random.choice([3, 5, 8])
                    }
                ])
            
            elif mirage_type == "LOADING_DELAYS":
                # Generate loading delays and fake errors
                content.extend([
                    {
                        "element_type": "loading_spinner",
                        "duration_seconds": random.choice(self.mirage_templates["loading"]["fake_delays"])
                    },
                    {
                        "element_type": "fake_error",
                        "error_message": random.choice(self.mirage_templates["loading"]["fake_errors"]),
                        "retry_available": True
                    }
                ])
            
            elif mirage_type == "SUBTLE_CHALLENGES":
                # Generate subtle verification challenges
                content.extend([
                    {
                        "element_type": "verification_request",
                        "message": "Please verify your identity for security",
                        "challenge_type": "cognitive"
                    },
                    {
                        "element_type": "additional_step",
                        "step_description": "Additional security verification required",
                        "estimated_time": "30 seconds"
                    }
                ])
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate mirage content: {str(e)}")
            return []
    
    async def _create_cognitive_challenges(self, user_id: str, trust_index: float) -> List[Dict]:
        """Create cognitive challenges for user verification"""
        try:
            challenges = []
            
            # Determine number of challenges based on trust index
            if trust_index < 20:
                num_challenges = 3
            elif trust_index < 35:
                num_challenges = 2
            else:
                num_challenges = 1
            
            # Get user's challenge history to avoid repetition
            history = await self._get_user_challenge_history(user_id)
            
            # Select challenges
            available_challenges = self.mirage_templates["challenges"]["cognitive_tasks"]
            used_types = [h.get("type") for h in history[-3:]]  # Last 3 challenges
            
            for _ in range(num_challenges):
                # Filter out recently used challenge types
                filtered_challenges = [
                    c for c in available_challenges 
                    if c["type"] not in used_types
                ]
                
                if not filtered_challenges:
                    filtered_challenges = available_challenges
                
                challenge = random.choice(filtered_challenges)
                challenge_instance = {
                    "challenge_id": f"challenge_{datetime.utcnow().timestamp()}",
                    "type": challenge["type"],
                    "description": challenge["description"],
                    "options": challenge["options"],
                    "correct_answer": None,  # Will be determined by user's typical behavior
                    "timeout_seconds": 30,
                    "attempts_allowed": 3
                }
                
                challenges.append(challenge_instance)
                used_types.append(challenge["type"])
            
            return challenges
            
        except Exception as e:
            logger.error(f"Failed to create cognitive challenges: {str(e)}")
            return []
    
    def _calculate_mirage_duration(self, trust_index: float) -> int:
        """Calculate mirage duration based on trust index"""
        if trust_index < 20:
            return 60  # 1 hour for very low trust
        elif trust_index < 35:
            return 30  # 30 minutes for low trust
        else:
            return 15  # 15 minutes for medium-low trust
    
    async def record_mirage_interaction(self, mirage_id: str, interaction_data: Dict) -> bool:
        """Record interaction with mirage interface"""
        try:
            if "mirage_data" not in self.memory_store or mirage_id not in self.memory_store["mirage_data"]:
                return False
            
            mirage_data = self.memory_store["mirage_data"][mirage_id]
            
            # Add new interaction
            interaction_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "interaction_type": interaction_data.get("type", "unknown"),
                "element_id": interaction_data.get("element_id", ""),
                "action": interaction_data.get("action", ""),
                "response_time": interaction_data.get("response_time", 0),
                "success": interaction_data.get("success", False)
            }
            
            mirage_data["interactions"].append(interaction_record)
            
            # Analyze interaction for authenticity
            authenticity_score = await self._analyze_interaction_authenticity(interaction_record)
            
            # If interactions seem legitimate, gradually reduce mirage intensity
            if authenticity_score > 0.8:
                await self._reduce_mirage_intensity(mirage_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record mirage interaction: {str(e)}")
            return False
    
    async def _analyze_interaction_authenticity(self, interaction: Dict) -> float:
        """Analyze if interaction seems authentic"""
        try:
            authenticity_score = 0.5  # Base score
            
            # Check response time (human-like timing)
            response_time = interaction.get("response_time", 0)
            if 0.2 <= response_time <= 3.0:  # Human-like response time
                authenticity_score += 0.2
            elif response_time < 0.1:  # Too fast (bot-like)
                authenticity_score -= 0.3
            
            # Check interaction type
            interaction_type = interaction.get("interaction_type", "")
            if interaction_type in ["tap", "swipe", "scroll"]:
                authenticity_score += 0.1
            
            # Check success rate (humans make mistakes)
            if not interaction.get("success", True):
                authenticity_score += 0.1  # Mistakes are human-like
            
            return max(0.0, min(1.0, authenticity_score))
            
        except Exception as e:
            logger.error(f"Failed to analyze interaction authenticity: {str(e)}")
            return 0.5
    
    async def _reduce_mirage_intensity(self, mirage_id: str):
        """Reduce mirage intensity based on authentic interactions"""
        try:
            if "mirage_data" not in self.memory_store or mirage_id not in self.memory_store["mirage_data"]:
                return
            
            mirage_data = self.memory_store["mirage_data"][mirage_id]
            current_type = mirage_data.get("mirage_type", "")
            
            # Reduce intensity
            if current_type == "FULL_DECEPTION":
                new_type = "BANKING_MIRAGE"
            elif current_type == "BANKING_MIRAGE":
                new_type = "LOADING_DELAYS"
            elif current_type == "LOADING_DELAYS":
                new_type = "SUBTLE_CHALLENGES"
            else:
                # Already at minimum intensity
                return
            
            # Update mirage type
            mirage_data["mirage_type"] = new_type
            
            # Update content
            user_id = mirage_data.get("user_id", "")
            new_content = await self._generate_mirage_content(new_type, user_id)
            mirage_data["content"] = new_content
            
            logger.info(f"Reduced mirage intensity for {mirage_id}: {current_type} -> {new_type}")
            
        except Exception as e:
            logger.error(f"Failed to reduce mirage intensity: {str(e)}")
    
    async def deactivate_mirage(self, mirage_id: str) -> bool:
        """Deactivate mirage interface"""
        try:
            if "mirage_data" not in self.memory_store or mirage_id not in self.memory_store["mirage_data"]:
                return False
            
            mirage_data = self.memory_store["mirage_data"][mirage_id]
            
            # Update status
            mirage_data["status"] = "DEACTIVATED"
            
            # Remove from active mirages
            session_id = mirage_data.get("session_id", "")
            if session_id in self.memory_store.get("active_mirages", {}):
                self.memory_store["active_mirages"][session_id].discard(mirage_id)
            
            logger.info(f"Deactivated mirage {mirage_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate mirage: {str(e)}")
            return False
    
    async def get_mirage_status(self, mirage_id: str) -> Optional[Dict]:
        """Get mirage status"""
        try:
            if "mirage_data" not in self.memory_store or mirage_id not in self.memory_store["mirage_data"]:
                return None
            
            return self.memory_store["mirage_data"][mirage_id]
            
        except Exception as e:
            logger.error(f"Failed to get mirage status: {str(e)}")
            return None
    
    async def get_active_mirages(self, session_id: str) -> List[str]:
        """Get active mirages for session"""
        try:
            if session_id not in self.memory_store.get("active_mirages", {}):
                return []
            
            active_mirages = list(self.memory_store["active_mirages"][session_id])
            
            # Filter out expired mirages
            valid_mirages = []
            for mirage_id in active_mirages:
                if mirage_id in self.memory_store.get("mirage_data", {}):
                    mirage_data = self.memory_store["mirage_data"][mirage_id]
                    if mirage_data.get("status") == "ACTIVE":
                        valid_mirages.append(mirage_id)
                else:
                    # Remove from active set
                    self.memory_store["active_mirages"][session_id].discard(mirage_id)
            
            return valid_mirages
            
        except Exception as e:
            logger.error(f"Failed to get active mirages: {str(e)}")
            return []
    
    async def _log_mirage_activation(self, user_id: str, session_id: str, mirage_id: str, mirage_type: str):
        """Log mirage activation event"""
        try:
            log_entry = {
                "event_type": "MIRAGE_ACTIVATED",
                "user_id": user_id,
                "session_id": session_id,
                "mirage_id": mirage_id,
                "mirage_type": mirage_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in mirage log
            if "mirage_log" not in self.memory_store:
                self.memory_store["mirage_log"] = []
            
            self.memory_store["mirage_log"].append(log_entry)
            
            # Keep last 1000 entries
            if len(self.memory_store["mirage_log"]) > 1000:
                self.memory_store["mirage_log"] = self.memory_store["mirage_log"][-1000:]
            
        except Exception as e:
            logger.error(f"Failed to log mirage activation: {str(e)}")
    
    async def _get_user_challenge_history(self, user_id: str) -> List[Dict]:
        """Get user's challenge history"""
        try:
            history_key = f"user_challenge_history_{user_id}"
            return self.memory_store.get(history_key, [])
            
        except Exception as e:
            logger.error(f"Failed to get user challenge history: {str(e)}")
            return []
    
    async def get_mirage_analytics(self, user_id: str) -> Dict:
        """Get mirage analytics for user"""
        try:
            # Get mirage activation history
            mirage_log = self.memory_store.get("mirage_log", [])
            
            user_activations = [
                entry for entry in mirage_log 
                if entry.get('user_id') == user_id
            ]
            
            # Calculate analytics
            analytics = {
                "total_activations": len(user_activations),
                "mirage_types": {},
                "average_duration": 0,
                "effectiveness_score": 0
            }
            
            # Count mirage types
            for activation in user_activations:
                mirage_type = activation.get('mirage_type', 'unknown')
                analytics['mirage_types'][mirage_type] = analytics['mirage_types'].get(mirage_type, 0) + 1
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get mirage analytics: {str(e)}")
            return {}
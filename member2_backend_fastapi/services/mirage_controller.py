"""
Mirage Controller Service for NETHRA
Controls the Adaptive Mirage Interface for deceiving attackers
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from models.behavioral_models import MirageSession, CognitiveChallenge

logger = logging.getLogger(__name__)

@dataclass
class MirageConfig:
    """Mirage interface configuration"""
    deception_level: int  # 1-5
    fake_balance: float
    fake_transactions: List[Dict[str, Any]]
    fake_contacts: List[Dict[str, str]]
    delay_multiplier: float
    cognitive_challenges: List[str]

class MirageController:
    """Service for controlling the Adaptive Mirage Interface"""
    
    def __init__(self):
        self.active_sessions: Dict[str, MirageSession] = {}
        self.mirage_configs: Dict[int, MirageConfig] = {}
        self.challenge_templates: Dict[str, Dict[str, Any]] = {}
        
        # Mirage parameters
        self.max_active_sessions = 100
        self.session_timeout = timedelta(minutes=15)
        self.challenge_timeout = 30  # seconds
        
        # Performance metrics
        self.total_activations = 0
        self.successful_deceptions = 0
        self.legitimate_recoveries = 0
        
        # Initialize mirage configurations
        self._initialize_mirage_configs()
        self._initialize_challenge_templates()
        
        logger.info("Mirage Controller initialized")
    
    def _initialize_mirage_configs(self):
        """Initialize different mirage configurations"""
        # Level 1: Subtle deception
        self.mirage_configs[1] = MirageConfig(
            deception_level=1,
            fake_balance=random.uniform(1000, 5000),
            fake_transactions=[
                {"type": "credit", "amount": 500.0, "description": "Salary Credit", "date": "2024-01-15"},
                {"type": "debit", "amount": 50.0, "description": "Grocery Store", "date": "2024-01-14"}
            ],
            fake_contacts=["John Doe", "Jane Smith", "Mike Johnson"],
            delay_multiplier=1.2,
            cognitive_challenges=["tap_pattern", "color_sequence"]
        )
        
        # Level 2: Moderate deception
        self.mirage_configs[2] = MirageConfig(
            deception_level=2,
            fake_balance=random.uniform(500, 2000),
            fake_transactions=[
                {"type": "credit", "amount": 1000.0, "description": "Transfer from Savings", "date": "2024-01-15"},
                {"type": "debit", "amount": 200.0, "description": "Online Purchase", "date": "2024-01-14"},
                {"type": "debit", "amount": 75.0, "description": "ATM Withdrawal", "date": "2024-01-13"}
            ],
            fake_contacts=["Alice Brown", "Bob Wilson", "Carol Davis", "David Lee"],
            delay_multiplier=1.5,
            cognitive_challenges=["tap_pattern", "color_sequence", "math_problem"]
        )
        
        # Level 3: Strong deception
        self.mirage_configs[3] = MirageConfig(
            deception_level=3,
            fake_balance=random.uniform(100, 1000),
            fake_transactions=[
                {"type": "credit", "amount": 2000.0, "description": "Bonus Payment", "date": "2024-01-15"},
                {"type": "debit", "amount": 300.0, "description": "Utility Bill", "date": "2024-01-14"},
                {"type": "debit", "amount": 150.0, "description": "Restaurant", "date": "2024-01-13"},
                {"type": "debit", "amount": 80.0, "description": "Gas Station", "date": "2024-01-12"}
            ],
            fake_contacts=["Emma Taylor", "Frank Miller", "Grace Wilson", "Henry Davis", "Ivy Johnson"],
            delay_multiplier=2.0,
            cognitive_challenges=["tap_pattern", "color_sequence", "math_problem", "memory_game"]
        )
        
        # Level 4: Advanced deception
        self.mirage_configs[4] = MirageConfig(
            deception_level=4,
            fake_balance=random.uniform(50, 500),
            fake_transactions=[
                {"type": "credit", "amount": 1500.0, "description": "Freelance Payment", "date": "2024-01-15"},
                {"type": "debit", "amount": 400.0, "description": "Rent Payment", "date": "2024-01-14"},
                {"type": "debit", "amount": 120.0, "description": "Internet Bill", "date": "2024-01-13"},
                {"type": "debit", "amount": 90.0, "description": "Phone Bill", "date": "2024-01-12"},
                {"type": "debit", "amount": 60.0, "description": "Subscription", "date": "2024-01-11"}
            ],
            fake_contacts=["Jack Brown", "Kate Wilson", "Liam Davis", "Mia Johnson", "Noah Miller", "Olivia Taylor"],
            delay_multiplier=2.5,
            cognitive_challenges=["tap_pattern", "color_sequence", "math_problem", "memory_game", "word_puzzle"]
        )
        
        # Level 5: Maximum deception
        self.mirage_configs[5] = MirageConfig(
            deception_level=5,
            fake_balance=random.uniform(10, 100),
            fake_transactions=[
                {"type": "credit", "amount": 3000.0, "description": "Investment Return", "date": "2024-01-15"},
                {"type": "debit", "amount": 500.0, "description": "Credit Card Payment", "date": "2024-01-14"},
                {"type": "debit", "amount": 250.0, "description": "Insurance Premium", "date": "2024-01-13"},
                {"type": "debit", "amount": 180.0, "description": "Medical Bill", "date": "2024-01-12"},
                {"type": "debit", "amount": 100.0, "description": "Car Maintenance", "date": "2024-01-11"},
                {"type": "debit", "amount": 75.0, "description": "Pharmacy", "date": "2024-01-10"}
            ],
            fake_contacts=["Paul Anderson", "Quinn Roberts", "Ruby Thompson", "Sam Wilson", "Tina Davis", "Uma Johnson", "Victor Miller"],
            delay_multiplier=3.0,
            cognitive_challenges=["tap_pattern", "color_sequence", "math_problem", "memory_game", "word_puzzle", "logic_puzzle"]
        )
    
    def _initialize_challenge_templates(self):
        """Initialize cognitive challenge templates"""
        self.challenge_templates = {
            "tap_pattern": {
                "type": "tap_sequence",
                "description": "Tap the buttons in the correct sequence",
                "difficulty_levels": {
                    1: {"sequence_length": 3, "timeout": 10},
                    2: {"sequence_length": 4, "timeout": 12},
                    3: {"sequence_length": 5, "timeout": 15},
                    4: {"sequence_length": 6, "timeout": 18},
                    5: {"sequence_length": 7, "timeout": 20}
                }
            },
            "color_sequence": {
                "type": "color_memory",
                "description": "Remember and repeat the color sequence",
                "difficulty_levels": {
                    1: {"colors": 3, "timeout": 8},
                    2: {"colors": 4, "timeout": 10},
                    3: {"colors": 5, "timeout": 12},
                    4: {"colors": 6, "timeout": 15},
                    5: {"colors": 7, "timeout": 18}
                }
            },
            "math_problem": {
                "type": "arithmetic",
                "description": "Solve the math problem",
                "difficulty_levels": {
                    1: {"operations": ["addition"], "range": 10, "timeout": 15},
                    2: {"operations": ["addition", "subtraction"], "range": 20, "timeout": 20},
                    3: {"operations": ["addition", "subtraction", "multiplication"], "range": 50, "timeout": 25},
                    4: {"operations": ["addition", "subtraction", "multiplication", "division"], "range": 100, "timeout": 30},
                    5: {"operations": ["all"], "range": 200, "timeout": 35}
                }
            },
            "memory_game": {
                "type": "pattern_memory",
                "description": "Remember the pattern shown",
                "difficulty_levels": {
                    1: {"grid_size": 3, "pattern_length": 4, "timeout": 20},
                    2: {"grid_size": 3, "pattern_length": 6, "timeout": 25},
                    3: {"grid_size": 4, "pattern_length": 8, "timeout": 30},
                    4: {"grid_size": 4, "pattern_length": 10, "timeout": 35},
                    5: {"grid_size": 5, "pattern_length": 12, "timeout": 40}
                }
            },
            "word_puzzle": {
                "type": "word_completion",
                "description": "Complete the word puzzle",
                "difficulty_levels": {
                    1: {"word_length": 4, "hints": 3, "timeout": 25},
                    2: {"word_length": 5, "hints": 2, "timeout": 30},
                    3: {"word_length": 6, "hints": 2, "timeout": 35},
                    4: {"word_length": 7, "hints": 1, "timeout": 40},
                    5: {"word_length": 8, "hints": 1, "timeout": 45}
                }
            },
            "logic_puzzle": {
                "type": "logical_reasoning",
                "description": "Solve the logic puzzle",
                "difficulty_levels": {
                    1: {"complexity": "simple", "timeout": 30},
                    2: {"complexity": "easy", "timeout": 35},
                    3: {"complexity": "medium", "timeout": 40},
                    4: {"complexity": "hard", "timeout": 45},
                    5: {"complexity": "expert", "timeout": 50}
                }
            }
        }
    
    async def activate_mirage(self, user_id: str, device_id: str, trust_score: float, 
                            risk_level: str, anomalies: List[Any]) -> Dict[str, Any]:
        """Activate mirage interface based on threat level"""
        try:
            # Determine deception level based on trust score and risk
            deception_level = self._calculate_deception_level(trust_score, risk_level, anomalies)
            
            # Create mirage session
            session_id = f"mirage_{user_id}_{device_id}_{int(datetime.now().timestamp())}"
            
            mirage_session = MirageSession(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                mirage_type=f"level_{deception_level}",
                deception_level=deception_level,
                cognitive_challenges=self.mirage_configs[deception_level].cognitive_challenges.copy()
            )
            
            self.active_sessions[session_id] = mirage_session
            
            # Generate mirage interface data
            mirage_data = await self._generate_mirage_interface(deception_level)
            
            # Generate initial cognitive challenge
            initial_challenge = await self._generate_cognitive_challenge(
                session_id, deception_level
            )
            
            # Update metrics
            self.total_activations += 1
            
            logger.info(f"🎭 Mirage activated: Level {deception_level} for user {user_id}")
            
            return {
                "session_id": session_id,
                "mirage_activated": True,
                "deception_level": deception_level,
                "mirage_data": mirage_data,
                "initial_challenge": initial_challenge,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to activate mirage: {str(e)}")
            return self._get_fallback_mirage_response()
    
    def _calculate_deception_level(self, trust_score: float, risk_level: str, anomalies: List[Any]) -> int:
        """Calculate appropriate deception level"""
        # Base level from trust score
        if trust_score >= 40:
            base_level = 1
        elif trust_score >= 30:
            base_level = 2
        elif trust_score >= 20:
            base_level = 3
        elif trust_score >= 10:
            base_level = 4
        else:
            base_level = 5
        
        # Adjust based on risk level
        risk_adjustments = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3
        }
        
        base_level += risk_adjustments.get(risk_level, 1)
        
        # Adjust based on anomaly count
        anomaly_count = len(anomalies)
        if anomaly_count > 3:
            base_level += 2
        elif anomaly_count > 1:
            base_level += 1
        
        # Clamp to valid range
        return max(1, min(5, base_level))
    
    async def _generate_mirage_interface(self, deception_level: int) -> Dict[str, Any]:
        """Generate mirage interface data"""
        config = self.mirage_configs[deception_level]
        
        # Generate fake account data
        fake_data = {
            "account_balance": config.fake_balance,
            "recent_transactions": config.fake_transactions,
            "contacts": [{"name": name, "account": f"****{random.randint(1000, 9999)}"} 
                        for name in config.fake_contacts],
            "cards": [
                {
                    "type": "debit",
                    "last_four": f"{random.randint(1000, 9999)}",
                    "status": "active"
                },
                {
                    "type": "credit",
                    "last_four": f"{random.randint(1000, 9999)}",
                    "status": "active"
                }
            ],
            "notifications": [
                {
                    "type": "transaction",
                    "message": "Payment successful",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "security",
                    "message": "Login from new device",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ]
        }
        
        # Add deception-specific elements
        if deception_level >= 3:
            fake_data["fake_offers"] = [
                {"title": "Special Loan Offer", "rate": "2.5% APR"},
                {"title": "Investment Opportunity", "return": "12% annually"}
            ]
        
        if deception_level >= 4:
            fake_data["fake_alerts"] = [
                {"type": "security", "message": "Suspicious activity detected"},
                {"type": "maintenance", "message": "System maintenance scheduled"}
            ]
        
        if deception_level == 5:
            fake_data["fake_errors"] = [
                {"code": "E001", "message": "Temporary service unavailable"},
                {"code": "E002", "message": "Transaction limit exceeded"}
            ]
        
        return {
            "interface_type": "mirage",
            "deception_level": deception_level,
            "data": fake_data,
            "delay_multiplier": config.delay_multiplier,
            "interaction_delays": {
                "button_press": 200 * config.delay_multiplier,
                "screen_transition": 500 * config.delay_multiplier,
                "data_loading": 1000 * config.delay_multiplier
            }
        }
    
    async def _generate_cognitive_challenge(self, session_id: str, deception_level: int) -> CognitiveChallenge:
        """Generate cognitive challenge for user verification"""
        config = self.mirage_configs[deception_level]
        available_challenges = config.cognitive_challenges
        
        # Select random challenge type
        challenge_type = random.choice(available_challenges)
        template = self.challenge_templates[challenge_type]
        difficulty = template["difficulty_levels"][deception_level]
        
        challenge_id = f"challenge_{session_id}_{int(datetime.now().timestamp())}"
        
        # Generate challenge based on type
        if challenge_type == "tap_pattern":
            challenge = await self._generate_tap_pattern_challenge(challenge_id, difficulty)
        elif challenge_type == "color_sequence":
            challenge = await self._generate_color_sequence_challenge(challenge_id, difficulty)
        elif challenge_type == "math_problem":
            challenge = await self._generate_math_challenge(challenge_id, difficulty)
        elif challenge_type == "memory_game":
            challenge = await self._generate_memory_challenge(challenge_id, difficulty)
        elif challenge_type == "word_puzzle":
            challenge = await self._generate_word_challenge(challenge_id, difficulty)
        elif challenge_type == "logic_puzzle":
            challenge = await self._generate_logic_challenge(challenge_id, difficulty)
        else:
            challenge = await self._generate_default_challenge(challenge_id, difficulty)
        
        return challenge
    
    async def _generate_tap_pattern_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate tap pattern challenge"""
        sequence_length = difficulty["sequence_length"]
        timeout = difficulty["timeout"]
        
        # Generate random sequence
        sequence = [random.randint(1, 9) for _ in range(sequence_length)]
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="tap_pattern",
            difficulty=sequence_length,
            question=f"Tap the buttons in this sequence: {' → '.join(map(str, sequence))}",
            expected_pattern=json.dumps(sequence),
            timeout=timeout
        )
    
    async def _generate_color_sequence_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate color sequence challenge"""
        color_count = difficulty["colors"]
        timeout = difficulty["timeout"]
        
        colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink"]
        sequence = [random.choice(colors) for _ in range(color_count)]
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="color_sequence",
            difficulty=color_count,
            question="Remember and repeat the color sequence shown",
            expected_pattern=json.dumps(sequence),
            timeout=timeout
        )
    
    async def _generate_math_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate math challenge"""
        operations = difficulty["operations"]
        number_range = difficulty["range"]
        timeout = difficulty["timeout"]
        
        # Generate simple math problem
        if "addition" in operations:
            a, b = random.randint(1, number_range), random.randint(1, number_range)
            question = f"What is {a} + {b}?"
            answer = a + b
        elif "subtraction" in operations:
            a, b = random.randint(1, number_range), random.randint(1, number_range)
            if a < b:
                a, b = b, a
            question = f"What is {a} - {b}?"
            answer = a - b
        else:
            a, b = random.randint(1, 10), random.randint(1, 10)
            question = f"What is {a} + {b}?"
            answer = a + b
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="math_problem",
            difficulty=len(operations),
            question=question,
            expected_pattern=str(answer),
            timeout=timeout
        )
    
    async def _generate_memory_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate memory challenge"""
        grid_size = difficulty["grid_size"]
        pattern_length = difficulty["pattern_length"]
        timeout = difficulty["timeout"]
        
        # Generate random pattern
        pattern = []
        for _ in range(pattern_length):
            row = random.randint(0, grid_size - 1)
            col = random.randint(0, grid_size - 1)
            pattern.append([row, col])
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="memory_game",
            difficulty=pattern_length,
            question=f"Remember the pattern shown on the {grid_size}x{grid_size} grid",
            expected_pattern=json.dumps(pattern),
            timeout=timeout
        )
    
    async def _generate_word_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate word challenge"""
        word_length = difficulty["word_length"]
        hints = difficulty["hints"]
        timeout = difficulty["timeout"]
        
        # Simple word list for demo
        words = ["SECURITY", "BANKING", "TRUST", "SAFETY", "PROTECT", "VERIFY", "SECURE", "ACCOUNT"]
        word = random.choice([w for w in words if len(w) == word_length])
        
        # Create hints by showing some letters
        hint_positions = random.sample(range(word_length), hints)
        hint_word = "".join(word[i] if i in hint_positions else "_" for i in range(word_length))
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="word_puzzle",
            difficulty=word_length,
            question=f"Complete the word: {hint_word}",
            expected_pattern=word,
            timeout=timeout
        )
    
    async def _generate_logic_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate logic challenge"""
        complexity = difficulty["complexity"]
        timeout = difficulty["timeout"]
        
        # Simple logic puzzles
        puzzles = {
            "simple": {
                "question": "If A = 1, B = 2, C = 3, what is D?",
                "answer": "4"
            },
            "easy": {
                "question": "What comes next: 2, 4, 6, 8, ?",
                "answer": "10"
            },
            "medium": {
                "question": "If today is Monday, what day was it 3 days ago?",
                "answer": "Friday"
            }
        }
        
        puzzle = puzzles.get(complexity, puzzles["simple"])
        
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="logic_puzzle",
            difficulty={"simple": 1, "easy": 2, "medium": 3, "hard": 4, "expert": 5}.get(complexity, 1),
            question=puzzle["question"],
            expected_pattern=puzzle["answer"],
            timeout=timeout
        )
    
    async def _generate_default_challenge(self, challenge_id: str, difficulty: Dict[str, Any]) -> CognitiveChallenge:
        """Generate default challenge"""
        return CognitiveChallenge(
            challenge_id=challenge_id,
            challenge_type="tap_pattern",
            difficulty=1,
            question="Tap the center button to continue",
            expected_pattern="center",
            timeout=10
        )
    
    async def process_challenge_response(self, session_id: str, challenge_id: str, 
                                       response: str, response_time: float) -> Dict[str, Any]:
        """Process cognitive challenge response"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Find challenge in session
            challenge = None
            for challenge_response in session.challenge_responses:
                if challenge_response.get("challenge_id") == challenge_id:
                    challenge = challenge_response
                    break
            
            if not challenge:
                return {"error": "Challenge not found"}
            
            # Evaluate response
            expected = challenge.get("expected_pattern", "")
            passed = response.strip().lower() == expected.strip().lower()
            
            # Calculate behavioral consistency
            behavioral_consistency = self._calculate_behavioral_consistency(
                session_id, response_time, passed
            )
            
            # Update challenge
            challenge.update({
                "response": response,
                "response_time": response_time,
                "passed": passed,
                "behavioral_consistency": behavioral_consistency,
                "timestamp": datetime.now().isoformat()
            })
            
            # Determine if user is legitimate
            if passed and behavioral_consistency > 0.7:
                # Likely legitimate user
                await self._handle_legitimate_user(session_id)
                return {
                    "challenge_passed": True,
                    "legitimate_user": True,
                    "action": "restore_session",
                    "message": "Identity verified successfully"
                }
            else:
                # Likely attacker, continue deception
                next_challenge = await self._generate_cognitive_challenge(
                    session_id, session.deception_level
                )
                
                return {
                    "challenge_passed": False,
                    "legitimate_user": False,
                    "action": "continue_mirage",
                    "next_challenge": next_challenge,
                    "message": "Please try again"
                }
            
        except Exception as e:
            logger.error(f"Failed to process challenge response: {str(e)}")
            return {"error": "Failed to process response"}
    
    def _calculate_behavioral_consistency(self, session_id: str, response_time: float, passed: bool) -> float:
        """Calculate behavioral consistency score"""
        # Simple behavioral consistency calculation
        # In real implementation, this would analyze detailed behavioral patterns
        
        base_score = 0.8 if passed else 0.3
        
        # Adjust based on response time
        if 2 <= response_time <= 10:  # Normal response time
            time_score = 1.0
        elif response_time < 2:  # Too fast (suspicious)
            time_score = 0.3
        elif response_time > 20:  # Too slow
            time_score = 0.6
        else:
            time_score = 0.8
        
        return (base_score + time_score) / 2
    
    async def _handle_legitimate_user(self, session_id: str):
        """Handle legitimate user recovery"""
        session = self.active_sessions.get(session_id)
        if session:
            session.legitimate_user_recovered = True
            session.deactivated_at = datetime.now()
            session.duration = (session.deactivated_at - session.activated_at).total_seconds()
            
            self.legitimate_recoveries += 1
            
            logger.info(f"✅ Legitimate user recovered: {session.user_id}")
    
    async def deactivate_mirage(self, session_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Deactivate mirage session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Update session
            session.deactivated_at = datetime.now()
            session.duration = (session.deactivated_at - session.activated_at).total_seconds()
            
            # Determine outcome
            if reason == "legitimate_user":
                session.legitimate_user_recovered = True
                self.legitimate_recoveries += 1
            elif reason == "attack_defeated":
                session.attack_defeated = True
                self.successful_deceptions += 1
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"🎭 Mirage deactivated: {session_id} (reason: {reason})")
            
            return {
                "deactivated": True,
                "session_id": session_id,
                "reason": reason,
                "duration": session.duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to deactivate mirage: {str(e)}")
            return {"error": "Failed to deactivate mirage"}
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active mirage sessions"""
        sessions = []
        
        for session_id, session in self.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "user_id": session.user_id,
                "device_id": session.device_id,
                "deception_level": session.deception_level,
                "activated_at": session.activated_at.isoformat(),
                "duration": (datetime.now() - session.activated_at).total_seconds(),
                "challenge_count": len(session.challenge_responses)
            })
        
        return sessions
    
    def _get_fallback_mirage_response(self) -> Dict[str, Any]:
        """Fallback mirage response"""
        return {
            "mirage_activated": False,
            "error": "Failed to activate mirage",
            "fallback_action": "lock_session",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_mirage_metrics(self) -> Dict[str, Any]:
        """Get mirage controller metrics"""
        return {
            "total_activations": self.total_activations,
            "successful_deceptions": self.successful_deceptions,
            "legitimate_recoveries": self.legitimate_recoveries,
            "active_sessions": len(self.active_sessions),
            "success_rate": (self.successful_deceptions / max(self.total_activations, 1)) * 100,
            "recovery_rate": (self.legitimate_recoveries / max(self.total_activations, 1)) * 100
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired mirage sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (current_time - session.activated_at) > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.deactivate_mirage(session_id, "timeout")
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired mirage sessions")
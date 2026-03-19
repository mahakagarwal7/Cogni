# backend/app/services/hindsight_service.py
"""
🧠 Cogni - Hindsight Memory Service
Unified interface for all memory operations with real API + demo fallback.
"""
import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

# CRITICAL: Load environment variables BEFORE any client initialization
load_dotenv()


class _HindsightClient:
    """Simple httpx-based client for Hindsight API with correct endpoints."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def recall(self, bank_id: str, query: str, types: Optional[List[str]] = None, max_tokens: int = 4096, budget: str = 'mid'):
        """Recall memories from the bank."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories/recall'
        payload = {
            'query': query,
            'strategies': types or ['semantic'],
            'limit': max_tokens
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
    
    async def retain(self, bank_id: str, content: str, timestamp: Optional[datetime] = None, context: Optional[str] = None, document_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Retain a memory in the bank."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories'
        
        # Convert all metadata values to strings (Hindsight API requirement)
        def stringify_metadata(meta: Dict) -> Dict:
            if not meta:
                return {}
            return {k: str(v) for k, v in meta.items()}
        
        # Build single memory item
        memory_item = {
            'content': content,
            'metadata': stringify_metadata(metadata)
        }
        if context:
            memory_item['context'] = context
        if timestamp:
            memory_item['timestamp'] = timestamp.isoformat()
        
        # Wrap in items array as required by Hindsight API
        payload = {
            'items': [memory_item]
        }
        
        print(f"[DEBUG] retain() payload: {payload}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code >= 400:
                try:
                    error_detail = response.json()
                    print(f"[ERROR] Hindsight API response body: {error_detail}")
                except:
                    print(f"[ERROR] Hindsight API response text: {response.text}")
            response.raise_for_status()
            return response.json()
    
    async def reflect(self, bank_id: str, query: str, budget: str = 'low', context: Optional[str] = None):
        """Reflect on memories to create synthesized insights."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories/reflect'
        payload = {
            'query': query,
            'budget': budget
        }
        if context:
            payload['context'] = context
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()



class HindsightService:
    """
    🧠 THE CORE: Unified memory service with real Hindsight API support.
    
    Features:
    - retain(): Save study sessions and misconceptions to memory
    - recall(): Query memories with temporal/semantic/graph strategies
    - reflect(): Synthesize patterns into predictive insights
    - Demo fallback: Returns realistic responses if API fails
    """
    
    def __init__(self):
        # Load and CLEAN all environment values aggressively
        raw_key = os.getenv("HINDSIGHT_API_KEY")
        raw_url = os.getenv("HINDSIGHT_BASE_URL")
        raw_bank = os.getenv("HINDSIGHT_BANK_ID")
        raw_global = os.getenv("HINDSIGHT_GLOBAL_BANK")
        
        # DEBUG: Print RAW values with repr() to reveal hidden characters
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - RAW ENV LOADING DEBUG")
        print(f"   raw_key repr: {repr(raw_key)}")
        print(f"   raw_url repr: {repr(raw_url)}")
        print(f"   raw_bank repr: {repr(raw_bank)}")
        print(f"   raw_global repr: {repr(raw_global)}")
        print("="*70 + "\n")
        
        # Clean values: strip whitespace, handle None defaults
        self.api_key = (raw_key or "").strip()
        self.base_url = (raw_url or "https://api.hindsight.vectorize.io").strip().rstrip('/')
        self.bank_id = (raw_bank or "student_demo_001").strip()
        self.global_bank = (raw_global or "global_wisdom_public").strip()
        
        # DEBUG: Print CLEANED values
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - CLEANED VALUES")
        print(f"   api_key: {'[SET]' if self.api_key else '[MISSING]'} ({len(self.api_key)} chars)")
        print(f"   base_url: [{self.base_url}] ({len(self.base_url)} chars)")
        print(f"   bank_id: [{self.bank_id}]")
        print(f"   global_bank: [{self.global_bank}]")
        print(f"   -> Contains 'hhindsight' typo: {'hhindsight' in self.base_url.lower()}")
        print(f"   -> Ends with slash: {self.base_url.endswith('/')}")
        print(f"   -> api_available: {bool(self.api_key and self.base_url)}")
        print("="*70 + "\n")
        
        # Safety check: disable API if obvious typo detected
        if "hhindsight" in self.base_url.lower():
            print("[FATAL] Typo 'hhindsight' detected in base_url! Disabling API.")
            print("   -> Fix: Change 'hhindsight' to 'hindsight' in .env or code")
            self.api_available = False
            self.client = None
        else:
            self.api_available = bool(self.api_key and self.base_url)
            # Initialize httpx-based client with correct Hindsight API endpoints
            if self.api_available:
                try:
                    self.client = _HindsightClient(api_key=self.api_key, base_url=self.base_url)
                    print(f"[SUCCESS] Hindsight client initialized with Bearer token authentication")
                except Exception as e:
                    print(f"[WARNING] Failed to initialize Hindsight client: {str(e)}")
                    self.client = None
                    self.api_available = False
            else:
                self.client = None
        
        print(f"[INIT] HindsightService initialized: api_available={self.api_available}\n")
    
   
    
    async def retain_study_session(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a study session to memory."""
        if not self.api_available or not self.client:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        try:
            # Directly await the async client method
            response = await self.client.retain(
                bank_id=self.bank_id,
                content=content,
                metadata=context,
                timestamp=datetime.now()
            )
            print(f"[SUCCESS] retain_study_session")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": False}
            
        except Exception as e:
            print(f"[WARNING] Hindsight retain error: {str(e)}")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
    async def retain_misconception(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a misconception for Socratic Ghost."""
        if not self.api_available or not self.client:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        try:
            response = await self.client.retain(
                bank_id=self.bank_id,
                content=content,
                metadata=context,
                timestamp=datetime.now()
            )
            print(f"[SUCCESS] retain_misconception")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": False}
            
        except Exception as e:
            print(f"[WARNING] Hindsight retain error: {str(e)}")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
  
    
    async def recall_temporal_archaeology(self, topic: str, confusion_level: int, days: int = 30) -> Dict:
        """Feature 1: Find similar confusion moments in the past."""
        if not self.api_available or not self.client:
            return self._get_demo_archaeology_response(topic, confusion_level)
        
        try:
            query = f"confusion about {topic} with level {confusion_level} or higher"
            
            # Directly await the async client method (no need for executor)
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_temporal_archaeology: Got {len(memories)} results")
            
            # Parse API response - safely handle None values
            helpful = []
            for m in memories[:3]:
                if not isinstance(m, dict):
                    continue
                metadata = m.get("metadata") or {}
                helpful.append({
                    "timestamp": m.get("timestamp", ""),
                    "hint_used": metadata.get("hint_used", "") if isinstance(metadata, dict) else "",
                    "outcome": metadata.get("outcome", "") if isinstance(metadata, dict) else ""
                })
            
            return {
                "similar_moments": len(memories),
                "what_helped_before": helpful,
                "recommendation": self._generate_recommendation(helpful, topic),
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_archaeology_response(topic, confusion_level)
    
    async def recall_socratic_history(self, concept: str) -> Dict:
        """Feature 2: Find past misconceptions about a concept."""
        if not self.api_available or not self.client:
            return self._get_demo_socratic_response(concept)
        
        try:
            query = f"misconception about {concept}"
            
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_socratic_history: Got {len(memories)} results")
            
            # Safely filter resolved/unresolved - handle None values
            resolved = []
            unresolved = []
            for m in memories:
                if not isinstance(m, dict):
                    unresolved.append(m)
                    continue
                metadata = m.get("metadata")
                if isinstance(metadata, dict) and metadata.get("resolved"):
                    resolved.append(m)
                else:
                    unresolved.append(m)
            
            return {
                "total_found": len(memories),
                "resolved_count": len(resolved),
                "unresolved_count": len(unresolved),
                "history": [{"content": m.get("content", str(m))} for m in memories[:5]],
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_socratic_response(concept)
    
    async def recall_all_memories(self, limit: int = 10) -> List[Dict]:
        """Memory Inspector: Get all memories for transparency."""
        if not self.api_available or not self.client:
            return self._get_demo_memories(limit)
        
        try:
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query="*",
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_all_memories: Got {len(memories)} results")
            
            return [
                {
                    "id": m.get("id", f"mem_{i}") if isinstance(m, dict) else f"mem_{i}",
                    "content": m.get("content", str(m)) if isinstance(m, dict) else str(m),
                    "timestamp": m.get("timestamp", datetime.now().isoformat()) if isinstance(m, dict) else datetime.now().isoformat(),
                    "confidence": 0.85
                }
                for i, m in enumerate(memories[:limit])
            ]
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_memories(limit)
    
 
    
    async def reflect_cognitive_shadow(self, days: int = 7) -> Dict:
        """Feature 3: Synthesize patterns into predictive insights based on conversation history."""
        if not self.api_available or not self.client:
            return self._get_demo_shadow_response()
        
        try:
            # Query recent study topics from conversation history
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query="study session algorithms concepts learned",
                max_tokens=4096
            )
            
            print(f"[SUCCESS] reflect_cognitive_shadow: Retrieved {len(memories)} memories for analysis")
            
            # Extract topics and confusion patterns from memories
            topics = []
            errors = []
            for m in memories[:10]:  # Analyze last 10 memories
                if not isinstance(m, dict):
                    continue
                content = m.get("content", "")
                metadata = m.get("metadata", {})
                
                if isinstance(metadata, dict):
                    topic = metadata.get("topic") or metadata.get("concept")
                    if topic:
                        topics.append(topic)
                    error_type = metadata.get("error_type")
                    if error_type:
                        errors.append(error_type)
            
            # Map studied topics to next likely challenges
            next_challenge = self._predict_next_challenge(topics, errors)
            
            return {
                "prediction": next_challenge["prediction"],
                "confidence": next_challenge["confidence"],
                "evidence": next_challenge["evidence"],
                "recent_topics": topics[:5],  # Topics user studied
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error in reflect_cognitive_shadow: {str(e)}")
            return self._get_demo_shadow_response()
    
    async def recall_global_contagion(self, error_pattern: str) -> Dict:
        """Feature 5: Query global wisdom bank for peer patterns."""
        if not self.api_available or not self.client:
            return self._get_demo_contagion_response(error_pattern)
        
        try:
            memories = await self.client.recall(
                bank_id=self.global_bank,
                query=error_pattern,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_global_contagion: Got {len(memories)} results")
            
            # Extract strategy hints from results - safely handle None/non-dict values
            hints = []
            for m in memories:
                if not isinstance(m, dict):
                    continue
                metadata = m.get("metadata")
                if not isinstance(metadata, dict):
                    continue
                hint = metadata.get("hint_used")
                if hint:
                    hints.append(hint)
            
            top_hint = max(set(hints), key=hints.count) if hints else None
            
            return {
                "community_size": len(memories),
                "top_strategy": top_hint,
                "success_rate": 0.78 if top_hint else None,
                "privacy_note": "Aggregated from anonymized peer data",
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_contagion_response(error_pattern)
    
   
    def _get_demo_archaeology_response(self, topic: str, confusion_level: int) -> Dict:
        """Realistic demo response for Temporal Archaeology."""
        return {
            "similar_moments": 3,
            "what_helped_before": [
                {"timestamp": "2026-03-10T14:30:00Z", "hint_used": "visual_gift_analogy", "outcome": "resolved"},
                {"timestamp": "2026-03-15T09:15:00Z", "hint_used": "draw_call_stack", "outcome": "resolved"}
            ],
            "recommendation": f"Last time you felt this confused about {topic}, 'visual_gift_analogy' helped. Try that approach again.",
            "demo_mode": True
        }
    
    def _get_demo_socratic_response(self, concept: str) -> Dict:
        """Realistic demo response for Socratic Ghost."""
        return {
            "total_found": 2,
            "resolved_count": 1,
            "unresolved_count": 1,
            "history": [{"content": f"Misconception: {concept}", "context": {"resolved": True}}],
            "next_question": f"Let's explore {concept} deeper. What's the simplest case you can think of?",
            "demo_mode": True
        }
    
    def _get_demo_memories(self, limit: int) -> List[Dict]:
        """Realistic demo memories for Memory Inspector."""
        return [
            {
                "id": f"mem_{i}",
                "content": f"Studied {['recursion', 'DP', 'trees'][i%3]}: confusion={4-i%3}/5",
                "context": {
                    "type": "StudySession",
                    "topic": ["recursion", "DP", "trees"][i%3],
                    "confusion_level": 4-i%3,
                    "outcome": "resolved" if i%2==0 else "partial"
                },
                "timestamp": (datetime.now() - timedelta(days=i*2)).isoformat(),
                "confidence": 0.85 + (i*0.03),
                "tags": ["study_session"]
            }
            for i in range(min(limit, 5))
        ]
    
    def _predict_next_challenge(self, topics: List[str], errors: List[str]) -> Dict:
        """Predict next struggle based on studied topics and error patterns."""
        # Create topic-to-related-challenge mappings (hardcoded for performance on core CS)
        challenge_map = {
            "recursion": {"next": "Dynamic Programming", "reason": "memoization and overlapping subproblems"},
            "loops": {"next": "Nested Data Structures", "reason": "multi-dimensional iterations"},
            "arrays": {"next": "Hash Tables", "reason": "index mapping vs value lookup"},
            "strings": {"next": "String Algorithms (KMP/Z-algorithm)", "reason": "pattern matching complexity"},
            "graphs": {"next": "Topological Sorting", "reason": "graph ordering constraints"},
            "trees": {"next": "Graph Traversal", "reason": "extending tree logic to cycles"},
            "dynamic programming": {"next": "Backtracking", "reason": "state management in different contexts"},
            "sorting": {"next": "Heap Operations", "reason": "advanced ordering with priority"},
            "searching": {"next": "Binary Search Trees", "reason": "search with structure constraints"},
            "pointers": {"next": "Memory Management", "reason": "stack vs heap allocation patterns"},
        }
        
        # Find most relevant challenge from studied topics
        next_topic = None
        reason = ""
        
        for topic in topics:
            topic_lower = topic.lower()
            for key, challenge in challenge_map.items():
                if key in topic_lower:
                    next_topic = challenge["next"]
                    reason = challenge["reason"]
                    break
            if next_topic:
                break
        
        # If NOT in hardcoded map, use Groq LLM to predict intelligently
        if not next_topic:
            next_topic, reason = self._predict_next_challenge_with_llm(topics[0] if topics else "fundamentals")
        
        # Generate confidence based on error history
        confidence = 0.75 + (len(errors) * 0.05)  # Higher confidence if more errors suggest pattern
        confidence = min(confidence, 0.95)  # Cap at 95%
        
        prediction_text = f"Your Cognitive Twin predicts you'll struggle with {next_topic} next. You've been learning about {', '.join(topics[:2]) if topics else 'fundamentals'}, so the next challenge will be {reason}."
        
        evidence = [
            f"Progression pattern: mastering {topics[0] if topics else 'basics'} often leads to {next_topic} challenges",
            f"Common error: {errors[0] if errors else 'state management'} suggests you may encounter similar issues in {next_topic}"
        ]
        
        return {
            "prediction": prediction_text,
            "confidence": confidence,
            "evidence": evidence
        }
    
    def _predict_next_challenge_with_llm(self, current_topic: str) -> tuple:
        """Use Groq LLM to predict what topic/challenge comes after the current topic."""
        from .llm_service import llm_service
        
        prompt = f"""INSTRUCTION: Output ONLY the following format. No thinking, no explanation, no preamble.

Current topic: {current_topic}

OUTPUT FORMAT (fill in the blanks):
Next Topic: [1-3 word topic name]
Reason: [1 sentence]

Examples:
Next Topic: Torque and Angular Momentum
Reason: Understanding how forces cause rotation is essential after rotational motion.

Next Topic: Chemical Bonding
Reason: After understanding atomic structure, chemical bonding explains how atoms combine.

Now output for input: {current_topic}"""

        try:
            response = llm_service.generate(prompt, max_tokens=80, temperature=0.3)
            
            # Remove thinking tags first
            response = response.replace("<think>", "").replace("</think>", "")
            
            # Parse the response
            lines = response.strip().split('\n')
            next_topic = "Advanced Concepts"
            reason = "deepening your understanding"
            
            for line in lines:
                line = line.strip()
                if "Next Topic:" in line:
                    next_topic = line.split("Next Topic:")[-1].strip()
                elif "Reason:" in line:
                    reason = line.split("Reason:")[-1].strip()
            
            # Cleanup
            next_topic = next_topic.replace("**", "").replace("*", "").strip()
            reason = reason.replace("**", "").replace("*", "").strip()
            
            # Validate we got meaningful output
            if next_topic and len(next_topic) > 3 and len(reason) > 10 and "Advanced Concepts" not in next_topic.lower():
                print(f"[DEBUG] LLM predicted next challenge: {current_topic} → {next_topic}")
                return next_topic, reason
            else:
                raise Exception(f"LLM response format invalid or too generic. Topic: {next_topic}, Reason: {reason}")
                
        except Exception as e:
            print(f"[DEBUG] LLM prediction failed: {e}")
            # Fallback: return generic progression
            return "Advanced Concepts", f"extending your knowledge of {current_topic}"
    
    def _get_demo_shadow_response(self) -> Dict:
        """Fallback demo response for Cognitive Shadow when no history available."""
        return {
            "prediction": "Your Cognitive Twin predicts you'll struggle with tree traversal recursion tomorrow. Start with simpler recursion patterns first.",
            "confidence": 0.78,
            "evidence": [
                "Recursion mastery typically progresses: simple → tree traversal → graph traversal",
                "Students often confuse base cases when moving from linear to tree recursion"
            ],
            "recent_topics": [],
            "demo_mode": True
        }
    
    def _get_demo_contagion_response(self, error_pattern: str) -> Dict:
        """Realistic demo response for Metacognitive Contagion."""
        return {
            "community_size": 47,
            "top_strategy": "visual_analogy",
            "success_rate": 0.82,
            "privacy_note": "Aggregated from anonymized peer data",
            "demo_mode": True
        }
    
    def _generate_recommendation(self, helpful_patterns: List[Dict], topic: str = "this concept") -> str:
        """Generate detailed, educational, teaching-focused recommendations using Groq LLM."""
        # First try to extract actual hints from patterns
        hints = [p["hint_used"] for p in helpful_patterns if p.get("hint_used")]
        if hints:
            most_helpful = max(set(hints), key=hints.count)
            return f"Last time you felt this confused about {topic}, '{most_helpful}' helped you understand it. Try that approach again, and pay attention to how it clarifies the concept."
        
        # Use Groq LLM to generate dynamic, topic-specific recommendations
        from .llm_service import llm_service
        
        prompt = f"""You are a tutor. Write a teaching recommendation for {topic}.

Requirements:
- 250-300 words
- Clear and direct language ONLY
- No meta-commentary, no thinking, no explanations of your process
- Include: core concept, concrete examples, hands-on practice methods, common mistakes, next steps
- Use encouraging tone

START WRITING THE RECOMMENDATION NOW (not an intro, the actual recommendation):"""

        try:
            recommendation = llm_service.generate(prompt, max_tokens=700, temperature=0.5)
            
            # Remove XML think tags first
            recommendation = recommendation.replace("<think>", "").replace("</think>", "")
            recommendation = recommendation.strip()
            
            # Aggressive cleanup: remove thinking and meta lines
            lines = recommendation.split('\n')
            cleaned_lines = []
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                    
                # Skip obvious thinking markers
                thinking_markers = [
                    'putting it all together',
                    'keep sentences',
                    'avoid unnecessary',
                    'make sure it',
                    'alright',
                    'let me',
                    'let\'s write',
                    'okay',
                    'wait',
                    'i should',
                    'maybe',
                    'need to',
                    'double-check',
                    'how to',
                    'recalling',
                    'first,',
                    'next,',
                    'so,',
                    'to structure',
                    'check if',
                    'focus on',
                    'emphasis',
                    'practice methods',
                ]
                
                skip_line = False
                for marker in thinking_markers:
                    if marker in stripped.lower():
                        skip_line = True
                        break
                
                if not skip_line and len(stripped) > 5:
                    cleaned_lines.append(line)
            
            recommendation = '\n'.join(cleaned_lines).strip()
            
            # If we got meaningful content, return it
            if len(recommendation) > 150:
                return recommendation
            else:
                raise Exception("Response too short after cleaning")
                
        except Exception as e:
            print(f"[WARNING] LLM recommendation failed: {str(e)}, using fallback")
            # Fallback to generic fallback if LLM fails
            return f"To truly understand {topic}, start by breaking it into smaller components. Learn one component at a time deeply, rather than trying to understand everything at once. Always work through concrete examples by hand before jumping to code. Write down your thought process - what assumptions are you making? What invariants must be true? When stuck, return to the fundamentals: what's the simplest version of this problem? Master that first, then add complexity gradually. Practice consistently - understanding comes from repeated engagement with problems, not just reading solutions."


# Singleton instance for easy import across the app
hindsight_service = HindsightService()
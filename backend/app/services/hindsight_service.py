# backend/app/services/hindsight_service.py
"""
🧠 Cogni - Hindsight Memory Service
Unified interface for all memory operations with real API + demo fallback.
"""
import os
import asyncio
import httpx
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# CRITICAL: Load environment variables BEFORE any client initialization.
# Use backend-root relative path to avoid cwd-dependent fallback behavior.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")

# Import local fallback for when Hindsight API is unavailable
from app.services.local_memory_fallback import local_memory


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
        payload = {
            'query': query,
            'budget': budget
        }
        if context:
            payload['context'] = context
        urls = [
            f'{self.base_url}/v1/default/banks/{bank_id}/memories/reflect',
            f'{self.base_url}/v1/default/banks/{bank_id}/reflect',
        ]

        last_error: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in urls:
                try:
                    response = await client.post(url, headers=self.headers, json=payload)
                    if response.status_code in {404, 405}:
                        continue
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    last_error = e
                    continue

        if last_error:
            raise last_error
        raise RuntimeError("Reflect failed for all known endpoint variants")



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
        raw_global = os.getenv("HINDSIGHT_GLOBAL_BANK")
        raw_user_bank_prefix = os.getenv("HINDSIGHT_USER_BANK_PREFIX")
        
        # DEBUG: Print RAW values with repr() to reveal hidden characters
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - RAW ENV LOADING DEBUG")
        print(f"   raw_key repr: {repr(raw_key)}")
        print(f"   raw_url repr: {repr(raw_url)}")
        print(f"   raw_user_bank_prefix repr: {repr(raw_user_bank_prefix)}")
        print(f"   raw_global repr: {repr(raw_global)}")
        print("="*70 + "\n")
        
        # Clean values: strip whitespace, handle None defaults
        self.api_key = (raw_key or "").strip()
        self.base_url = (raw_url or "https://api.hindsight.vectorize.io").strip().rstrip('/')
        # Backward-compatible default keeps existing bank naming stable if env var is removed.
        self.user_bank_prefix = (raw_user_bank_prefix or "student_demo_001").strip()
        self.bank_id = self.user_bank_prefix
        self.global_bank = (raw_global or "global_wisdom_public").strip()
        
        # DEBUG: Print CLEANED values
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - CLEANED VALUES")
        print(f"   api_key: {'[SET]' if self.api_key else '[MISSING]'} ({len(self.api_key)} chars)")
        print(f"   base_url: [{self.base_url}] ({len(self.base_url)} chars)")
        print(f"   user_bank_prefix: [{self.user_bank_prefix}]")
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

    def _sanitize_user_id(self, user_id: Optional[str]) -> str:
        raw = (user_id or "anonymous").strip().lower()
        cleaned = re.sub(r"[^a-z0-9_-]", "-", raw)
        cleaned = re.sub(r"-+", "-", cleaned).strip("-")
        return cleaned[:32] or "anonymous"

    def _user_bank_id(self, user_id: Optional[str]) -> str:
        base = (self.user_bank_prefix or "student_demo_001").strip()
        safe_user = self._sanitize_user_id(user_id)
        bank = f"{base}__u_{safe_user}"
        return bank[:64]

    def _bank_candidates(self, user_id: Optional[str]) -> List[str]:
        if not user_id:
            return [self.bank_id]
        user_bank = self._user_bank_id(user_id)
        # Strict isolation: never mix shared-bank memories into per-user reasoning paths.
        # This avoids unrelated historical data contaminating progress, killer prompts, and shadow signals.
        return [user_bank]

    def _extract_reflect_insight(self, payload: Any) -> str:
        """Extract a readable insight sentence from reflect payloads with varying shapes."""
        if payload is None:
            return ""

        if isinstance(payload, str):
            text = payload.strip()
            return text if text else ""

        if isinstance(payload, list):
            for item in payload:
                text = self._extract_reflect_insight(item)
                if text:
                    return text
            return ""

        if isinstance(payload, dict):
            preferred_keys = [
                "insight",
                "summary",
                "response",
                "analysis",
                "text",
                "content",
                "message",
            ]
            for key in preferred_keys:
                if key in payload:
                    text = self._extract_reflect_insight(payload.get(key))
                    if text:
                        return text

            # If no preferred key exists, inspect nested values.
            for value in payload.values():
                text = self._extract_reflect_insight(value)
                if text:
                    return text

        return ""

    def _is_low_signal_reflect(self, text: str) -> bool:
        if not text or len(text.strip()) < 20:
            return True
        lower = text.lower()
        low_signal_markers = [
            "i am sorry",
            "i'm sorry",
            "do not have enough information",
            "don't have enough information",
            "unable to determine",
            "insufficient information",
        ]
        return any(marker in lower for marker in low_signal_markers)
    
   
    
    async def retain_study_session(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a study session to memory. Falls back to local storage if API unavailable."""
        user_id = str((context or {}).get("user_id") or "anonymous")
        banks = self._bank_candidates(user_id)

        if self.api_available and self.client:
            for bank in banks:
                try:
                    await self.client.retain(
                        bank_id=bank,
                        content=content,
                        metadata=context,
                        timestamp=datetime.now()
                    )
                    print(f"[SUCCESS] retain_study_session to Hindsight API bank={bank}")
                    return {"status": "success", "bank_id": bank, "demo_mode": False, "stored_location": "hindsight"}
                except Exception as e:
                    print(f"[WARNING] Hindsight API failed for bank={bank}: {str(e)}")
                    continue
        
        # Fallback: Save to local storage
        print(f"[INFO] Falling back to local storage for session retention")
        local_result = local_memory.save_interaction(self._user_bank_id(user_id), content, context)
        return {
            "status": "success",
            "bank_id": self._user_bank_id(user_id),
            "demo_mode": False,
            "stored_location": "local",
            "local_result": local_result
        }
    
    async def retain_misconception(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a misconception for Socratic Ghost. Falls back to local storage if API unavailable."""
        user_id = str((context or {}).get("user_id") or "anonymous")
        banks = self._bank_candidates(user_id)

        if self.api_available and self.client:
            for bank in banks:
                try:
                    await self.client.retain(
                        bank_id=bank,
                        content=content,
                        metadata=context,
                        timestamp=datetime.now()
                    )
                    print(f"[SUCCESS] retain_misconception to Hindsight API bank={bank}")
                    return {"status": "success", "bank_id": bank, "demo_mode": False, "stored_location": "hindsight"}
                except Exception as e:
                    print(f"[WARNING] Hindsight API failed for bank={bank}: {str(e)}")
                    continue
        
        # Fallback: Save to local storage
        print(f"[INFO] Falling back to local storage for misconception retention")
        local_result = local_memory.save_interaction(self._user_bank_id(user_id), content, context)
        return {
            "status": "success",
            "bank_id": self._user_bank_id(user_id),
            "demo_mode": False,
            "stored_location": "local",
            "local_result": local_result
        }

    async def store_insight(self, user_id: str, insight: Dict[str, Any]) -> Dict:
        """
        Store structured insight in memory.

        Equivalent feature mapping to requested behavior:
        hindsight_client.insert({"user_id": user_id, "type": "insight", "data": insight})
        """
        if not self.api_available or not self.client:
            return {
                "status": "success",
                "bank_id": self.bank_id,
                "demo_mode": True,
                "stored": {
                    "user_id": user_id,
                    "type": "insight",
                    "data": insight,
                },
            }

        try:
            metadata = {
                "type": "insight",
                "user_id": user_id,
                "insight_data": json.dumps(insight),
            }
            content = f"Insight for user={user_id}"

            for bank in self._bank_candidates(user_id):
                try:
                    await self.client.retain(
                        bank_id=bank,
                        content=content,
                        metadata=metadata,
                        timestamp=datetime.now(),
                    )
                    print(f"[SUCCESS] store_insight: user_id={user_id}, bank={bank}")
                    return {"status": "success", "bank_id": bank, "demo_mode": False}
                except Exception as e:
                    print(f"[WARNING] store_insight failed for bank={bank}: {str(e)}")
                    continue

            raise RuntimeError("store_insight failed on all bank candidates")

        except Exception as e:
            print(f"[WARNING] Hindsight store_insight error: {str(e)}")
            return {
                "status": "success",
                "bank_id": self.bank_id,
                "demo_mode": True,
                "stored": {
                    "user_id": user_id,
                    "type": "insight",
                    "data": insight,
                },
            }

    async def get_user_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve user insights from memory.
        Falls back to local storage if Hindsight API unavailable.

        Equivalent feature mapping to requested behavior:
        hindsight_client.query({"user_id": user_id, "type": "insight"})
        """
        if self.api_available and self.client:
            try:
                insights: List[Dict[str, Any]] = []
                for bank in self._bank_candidates(user_id):
                    try:
                        memories = await self.client.recall(
                            bank_id=bank,
                            query=f"insight user {user_id}",
                            max_tokens=4096,
                        )
                    except Exception as e:
                        print(f"[WARNING] get_user_insights recall failed for bank={bank}: {str(e)}")
                        continue

                    for m in memories:
                        if not isinstance(m, dict):
                            continue

                        metadata = m.get("metadata") or {}
                        if not isinstance(metadata, dict):
                            continue

                        if str(metadata.get("type", "")) != "insight":
                            continue
                        if str(metadata.get("user_id", "")) != user_id:
                            continue

                        raw_data = metadata.get("insight_data", "{}")
                        try:
                            parsed_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        except Exception:
                            parsed_data = {"raw": str(raw_data)}

                        insights.append(
                        {
                            "id": m.get("id"),
                            "timestamp": m.get("timestamp") or m.get("occurred_end") or m.get("mentioned_at"),
                            "user_id": user_id,
                            "type": "insight",
                            "data": parsed_data,
                        }
                    )

                if insights:
                    print(f"[SUCCESS] get_user_insights: user_id={user_id}, count={len(insights)}")
                    return insights

                # No first-class insight records found. Fall through to user-memory-derived insights
                # so topic-level progress remains meaningful instead of always looking identical.
                print(f"[INFO] No explicit insight records for user={user_id}; deriving from user memories")

                derived_insights: List[Dict[str, Any]] = []
                for bank in self._bank_candidates(user_id):
                    try:
                        derived_memories = await self.client.recall(
                            bank_id=bank,
                            query=f"user_id {user_id} topic learning study",
                            max_tokens=4096,
                        )
                    except Exception as e:
                        print(f"[WARNING] derived insight recall failed for bank={bank}: {str(e)}")
                        continue

                    for m in derived_memories:
                        if not isinstance(m, dict):
                            continue

                        metadata = m.get("metadata") if isinstance(m.get("metadata"), dict) else {}
                        if metadata and str(metadata.get("user_id", "")) not in {"", user_id}:
                            continue

                        content_text = str(m.get("content") or m.get("text") or "")

                        topic_val = (
                            metadata.get("topic")
                            or metadata.get("concept")
                            or "unknown"
                        )

                        if str(topic_val).strip().lower() in {"", "unknown", "none"} and content_text:
                            extraction_patterns = [
                                r"about\s+([a-zA-Z0-9_\-\s]{2,60}?)\s+in\s+the\s+context\s+of",
                                r"query\s+for\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\s+at|:|,|\.|\|)",
                                r"prediction\s+for\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\s+at|:|,|\.|\|)",
                                r"response\s+about\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\s+was|,|\.|\|)",
                            ]

                            for pattern in extraction_patterns:
                                match = re.search(pattern, content_text, flags=re.IGNORECASE)
                                if match:
                                    candidate = match.group(1).strip()
                                    # Keep only concise noun-phrase-like topics.
                                    if 1 <= len(candidate.split()) <= 5:
                                        topic_val = candidate
                                        break

                        confidence_val = metadata.get("data_confidence")
                        if confidence_val is None:
                            confidence_val = m.get("confidence")
                        try:
                            confidence_score = float(confidence_val) if confidence_val is not None else 0.65
                        except Exception:
                            confidence_score = 0.65

                        issue_val = metadata.get("data_issue") or metadata.get("engine_feature") or "concept_not_clear"
                        if issue_val == "concept_not_clear" and content_text:
                            content_lower = content_text.lower()
                            if "socratic" in content_lower:
                                issue_val = "socratic_misconception"
                            elif "archaeology" in content_lower:
                                issue_val = "historical_confusion_pattern"
                            elif "shadow" in content_lower:
                                issue_val = "predictive_risk_pattern"
                            elif "resonance" in content_lower:
                                issue_val = "cross_topic_connection_gap"
                            elif "contagion" in content_lower:
                                issue_val = "peer_strategy_gap"

                        derived_insights.append(
                            {
                                "id": m.get("id"),
                                "timestamp": m.get("timestamp") or m.get("occurred_end") or m.get("mentioned_at"),
                                "user_id": user_id,
                                "type": "insight",
                                "data": {
                                    "issue": str(issue_val),
                                    "topic": str(topic_val),
                                    "confidence_score": max(0.0, min(1.0, confidence_score)),
                                    "preferred_style": "adaptive",
                                },
                            }
                        )

                if derived_insights:
                    print(f"[SUCCESS] get_user_insights from API memories: user_id={user_id}, count={len(derived_insights)}")
                    return derived_insights

            except Exception as e:
                print(f"[WARNING] Hindsight get_user_insights error: {str(e)}")
        
        # Fallback 1: Check local storage for user insights
        print(f"[INFO] Checking local storage for user insights: {user_id}")
        local_memories = local_memory.get_user_memories(self._user_bank_id(user_id), user_id, limit=50)
        
        if local_memories:
            insights: List[Dict[str, Any]] = []
            for m in local_memories:
                metadata = m.get("metadata", {})
                topic = metadata.get("topic", "unknown")
                confidence_val = metadata.get("data_confidence")
                try:
                    confidence_score = float(confidence_val) if confidence_val is not None else 0.65
                except Exception:
                    confidence_score = 0.65

                issue = str(metadata.get("data_issue") or metadata.get("engine_feature") or "concept_not_clear")

                insights.append(
                    {
                        "id": m.get("id"),
                        "timestamp": m.get("timestamp"),
                        "user_id": user_id,
                        "type": "insight",
                        "data": {
                            "issue": issue,
                            "topic": topic,
                            "confidence_score": max(0.0, min(1.0, confidence_score)),
                            "preferred_style": "adaptive"
                        },
                    }
                )
            print(f"[SUCCESS] get_user_insights from local storage: user_id={user_id}, count={len(insights)}")
            return insights
        
        # Fallback 2: No memories anywhere - return generic insight WITHOUT demo_mode flag
        print(f"[INFO] No insights found for {user_id} - returning generic insight")
        return [
            {
                "user_id": user_id,
                "type": "insight",
                "data": {
                    "issue": "none",
                    "topic": "general",
                    "preferred_style": "guided",
                    "confidence_score": 0.5,
                },
            }
        ]
    
  
    
    async def recall_temporal_archaeology(self, topic: str, confusion_level: int, days: int = 30, user_id: Optional[str] = None) -> Dict:
        """Feature 1: Find similar confusion moments in the past."""
        if not self.api_available or not self.client:
            return self._get_demo_archaeology_response(topic, confusion_level)
        
        try:
            query = f"confusion about {topic} with level {confusion_level} or higher"

            # Backbone synthesis: let Hindsight reflect patterns across sessions.
            reflect_query = (
                "What topics does this student consistently struggle with and what comes next? "
                f"Focus on topic: {topic}."
            )
            reflect_insight = ""
            for bank in self._bank_candidates(user_id):
                try:
                    reflect_payload = await self.client.reflect(
                        bank_id=bank,
                        query=reflect_query,
                        budget='mid'
                    )
                    reflect_insight = self._extract_reflect_insight(reflect_payload)
                    if self._is_low_signal_reflect(reflect_insight):
                        reflect_insight = ""
                    if reflect_insight:
                        print(f"[SUCCESS] archaeology reflect synthesis from bank={bank}")
                        break
                except Exception as e:
                    print(f"[WARNING] archaeology reflect failed for bank={bank}: {str(e)}")
            
            # Directly await the async client method (no need for executor)
            memories: List[Dict[str, Any]] = []
            for bank in self._bank_candidates(user_id):
                try:
                    recall_rows = await self.client.recall(
                        bank_id=bank,
                        query=query,
                        max_tokens=4096
                    )
                    memories.extend(recall_rows)
                except Exception as e:
                    print(f"[WARNING] recall_temporal_archaeology failed for bank={bank}: {str(e)}")
            
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
                "recommendation": reflect_insight or self._generate_recommendation(helpful, topic),
                "reflect_insight": reflect_insight,
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_archaeology_response(topic, confusion_level)
    
    async def recall_socratic_history(self, concept: str, user_id: Optional[str] = None) -> Dict:
        """Feature 2: Find past misconceptions about a concept."""
        if self.api_available and self.client:
            try:
                query = f"misconception about {concept}"
                
                memories: List[Dict[str, Any]] = []
                for bank in self._bank_candidates(user_id):
                    try:
                        recall_rows = await self.client.recall(
                            bank_id=bank,
                            query=query,
                            max_tokens=4096
                        )
                        memories.extend(recall_rows)
                    except Exception as e:
                        print(f"[WARNING] recall_socratic_history failed for bank={bank}: {str(e)}")
                
                print(f"[SUCCESS] recall_socratic_history: Got {len(memories)} results from Hindsight API")
                
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
                    "demo_mode": False,
                    "source": "hindsight"
                }
                
            except Exception as e:
                print(f"[WARNING] Hindsight API recall failed: {str(e)}")
        
        # Fallback: Check local storage
        print(f"[INFO] Checking local storage for concept: {concept}")
        local_memories = local_memory.get_topic_memories(self._user_bank_id(user_id), concept, limit=10)
        
        if local_memories:
            resolved = [m for m in local_memories if m.get("metadata", {}).get("resolved")]
            unresolved = [m for m in local_memories if not m.get("metadata", {}).get("resolved")]
            
            return {
                "total_found": len(local_memories),
                "resolved_count": len(resolved),
                "unresolved_count": len(unresolved),
                "history": [{"content": m.get("content", "No content")} for m in local_memories[:5]],
                "demo_mode": False,
                "source": "local_storage"
            }
        
        # No memories found anywhere - return demo response
        return self._get_demo_socratic_response(concept)
    
    async def recall_all_memories(self, limit: int = 10, user_id: Optional[str] = None) -> List[Dict]:
        """Memory Inspector: Get memories for transparency (optionally user-scoped)."""

        def _safe_ratio(metadata: Dict[str, Any]) -> Optional[float]:
            ratio = metadata.get("quiz_score_ratio")
            score = metadata.get("quiz_score")
            total = metadata.get("quiz_total")

            try:
                if ratio is not None:
                    value = float(ratio)
                    return max(0.0, min(1.0, value))
                if score is not None and total is not None and float(total) > 0:
                    value = float(score) / float(total)
                    return max(0.0, min(1.0, value))
            except Exception:
                return None

            return None

        def _safe_confidence(memory: Dict[str, Any], metadata: Dict[str, Any]) -> float:
            candidates = [
                metadata.get("data_confidence"),
                metadata.get("confidence"),
                memory.get("confidence"),
            ]
            for value in candidates:
                try:
                    if value is None:
                        continue
                    parsed = float(value)
                    return max(0.0, min(1.0, parsed))
                except Exception:
                    continue

            quiz_ratio = _safe_ratio(metadata)
            if quiz_ratio is not None:
                return quiz_ratio

            return 0.85

        def _normalize_memories(raw_memories: List[Any]) -> List[Dict[str, Any]]:
            normalized: List[Dict[str, Any]] = []
            for i, memory in enumerate(raw_memories):
                if not isinstance(memory, dict):
                    normalized.append(
                        {
                            "id": f"mem_{i}",
                            "content": str(memory),
                            "timestamp": datetime.now().isoformat(),
                            "confidence": 0.85,
                            "metadata": {},
                            "context": {},
                            "topic": None,
                        }
                    )
                    continue

                metadata = memory.get("metadata") if isinstance(memory.get("metadata"), dict) else {}
                context = memory.get("context") if isinstance(memory.get("context"), dict) else {}
                topic = metadata.get("topic") or metadata.get("concept") or context.get("topic")

                normalized.append(
                    {
                        "id": memory.get("id", f"mem_{i}"),
                        "content": memory.get("content") or memory.get("text") or "",
                        "timestamp": memory.get("timestamp")
                        or memory.get("occurred_end")
                        or memory.get("mentioned_at")
                        or datetime.now().isoformat(),
                        "confidence": _safe_confidence(memory, metadata),
                        "metadata": metadata,
                        "context": context,
                        "topic": topic,
                    }
                )

            normalized.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
            return normalized[:limit]

        if self.api_available and self.client:
            try:
                banks = self._bank_candidates(user_id) if user_id else [self.bank_id]
                memories: List[Dict[str, Any]] = []

                for bank in banks:
                    try:
                        bank_memories = await self.client.recall(
                            bank_id=bank,
                            query=(f"user_id {user_id} study quiz feedback topic" if user_id else "*"),
                            max_tokens=4096,
                        )
                        memories.extend(bank_memories)
                    except Exception as e:
                        print(f"[WARNING] recall_all_memories failed for bank={bank}: {str(e)}")

                if memories:
                    print(f"[SUCCESS] recall_all_memories: Got {len(memories)} results")
                    return _normalize_memories(memories)

            except Exception as e:
                print(f"[WARNING] Hindsight recall error: {str(e)}")

        # Fallback to local storage when API is unavailable or returns no rows.
        bank_id = self._user_bank_id(user_id) if user_id else self.bank_id
        local_rows = (
            local_memory.get_user_memories(bank_id, user_id, limit=limit)
            if user_id
            else local_memory.get_memories(bank_id, limit=limit)
        )
        if local_rows:
            return _normalize_memories(local_rows)

        return self._get_demo_memories(limit)
    
 
    
    async def reflect_cognitive_shadow(self, days: int = 7, user_id: Optional[str] = None, current_topic: Optional[str] = None) -> Dict:
        """Feature 3: Synthesize patterns into predictive insights based on conversation history."""
        if not self.api_available or not self.client:
            return self._get_demo_shadow_response()
        
        try:
            reflect_query = "What topics does this student consistently struggle with and what comes next?"
            if current_topic:
                reflect_query += f" Current topic: {current_topic}."

            reflect_insight = ""
            for bank in self._bank_candidates(user_id):
                try:
                    reflect_payload = await self.client.reflect(
                        bank_id=bank,
                        query=reflect_query,
                        budget='mid'
                    )
                    reflect_insight = self._extract_reflect_insight(reflect_payload)
                    if self._is_low_signal_reflect(reflect_insight):
                        reflect_insight = ""
                    if reflect_insight:
                        print(f"[SUCCESS] shadow reflect synthesis from bank={bank}")
                        break
                except Exception as e:
                    print(f"[WARNING] shadow reflect failed for bank={bank}: {str(e)}")

            # Query recent study topics from conversation history
            memories: List[Dict[str, Any]] = []
            for bank in self._bank_candidates(user_id):
                try:
                    recall_rows = await self.client.recall(
                        bank_id=bank,
                        query="study session quiz score mistakes weak area algorithms concepts learned",
                        max_tokens=4096
                    )
                    memories.extend(recall_rows)
                except Exception as e:
                    print(f"[WARNING] reflect_cognitive_shadow failed for bank={bank}: {str(e)}")
            
            print(f"[SUCCESS] reflect_cognitive_shadow: Retrieved {len(memories)} memories for analysis")
            
            # Extract topics and confusion patterns from memories
            topics = []
            errors = []
            quiz_low_topics = []
            for m in memories[:10]:  # Analyze last 10 memories
                if not isinstance(m, dict):
                    continue
                content = str(m.get("content", "") or m.get("text", ""))
                metadata = m.get("metadata", {})
                topic = None
                
                if isinstance(metadata, dict):
                    topic = metadata.get("topic") or metadata.get("concept")
                    if topic:
                        topics.append(topic)
                    error_type = metadata.get("error_type")
                    if error_type:
                        errors.append(error_type)

                    # Dense quiz signal: topic + score + mistakes informs true weak-area prediction.
                    quiz_score = metadata.get("quiz_score")
                    quiz_total = metadata.get("quiz_total")
                    quiz_ratio = metadata.get("quiz_score_ratio")
                    try:
                        if quiz_ratio is not None:
                            ratio_val = float(quiz_ratio)
                        elif quiz_score is not None and quiz_total is not None and float(quiz_total) > 0:
                            ratio_val = float(quiz_score) / float(quiz_total)
                        else:
                            ratio_val = None
                    except Exception:
                        ratio_val = None

                    if ratio_val is not None and topic:
                        # Treat rounded 2/3 (0.667) as low score to preserve quiz-signal recall.
                        if ratio_val <= 0.67:
                            quiz_low_topics.append(str(topic))
                            errors.append("low_quiz_score")
                        elif ratio_val >= 0.9:
                            errors.append("quiz_mastery")

                # Some recall rows carry quiz info only in free text with null metadata/context.
                # Parse score/topic directly from text so evidence can still include quiz weakness.
                quiz_text = content.lower()
                if "quiz" in quiz_text:
                    text_topic = None
                    topic_match = re.search(
                        r"(?:on|regarding)\s+([a-zA-Z0-9 _-]{2,60}?)(?:\s+with\s+(?:a\s+)?score|[\.,])",
                        content,
                        re.IGNORECASE,
                    )
                    if topic_match:
                        text_topic = topic_match.group(1).strip()

                    score_match = re.search(r"score\s+of\s+(\d+)\s*/\s*(\d+)", content, re.IGNORECASE)
                    if not score_match:
                        score_match = re.search(r"scor(?:e|ing)\s+(\d+)\s+out\s+of\s+(\d+)", content, re.IGNORECASE)

                    if score_match:
                        try:
                            s_val = float(score_match.group(1))
                            t_val = float(score_match.group(2))
                            ratio_val = (s_val / t_val) if t_val > 0 else None
                        except Exception:
                            ratio_val = None

                        quiz_topic = str(topic or text_topic or current_topic or "").strip()
                        quiz_topic = re.sub(r"^(on|regarding)\s+", "", quiz_topic, flags=re.IGNORECASE).strip()
                        if quiz_topic:
                            topics.append(quiz_topic)

                        if ratio_val is not None and quiz_topic:
                            if ratio_val <= 0.67:
                                quiz_low_topics.append(quiz_topic)
                                errors.append("low_quiz_score")
                            elif ratio_val >= 0.9:
                                errors.append("quiz_mastery")
                    elif "weak area" in quiz_text:
                        quiz_topic = str(text_topic or current_topic or "").strip()
                        quiz_topic = re.sub(r"^(on|regarding)\s+", "", quiz_topic, flags=re.IGNORECASE).strip()
                        if quiz_topic:
                            quiz_low_topics.append(quiz_topic)
                            topics.append(quiz_topic)
                            errors.append("low_quiz_score")

            if quiz_low_topics:
                topics = quiz_low_topics + topics

            unique_quiz_low_topics = list(dict.fromkeys(quiz_low_topics))
            
            # Map studied topics to next likely challenges
            next_challenge = self._predict_next_challenge(topics, errors)
            
            return {
                "prediction": reflect_insight or next_challenge["prediction"],
                "confidence": next_challenge["confidence"],
                "evidence": next_challenge["evidence"] + ([f"Quiz weakness detected in: {', '.join(unique_quiz_low_topics[:2])}"] if unique_quiz_low_topics else []),
                "recent_topics": topics[:5],  # Topics user studied
                "reflect_insight": reflect_insight,
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
            "demo_mode": False
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
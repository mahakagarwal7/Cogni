
"""
🔗 Feature 4: Cognitive Resonance Detection
Find hidden connections between seemingly unrelated topics.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any, List
import re

class ResonanceEngine:
    """
    Resonance Detection Engine - Graph-based conceptual connections using Hindsight.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service

    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """Convert user insights into compact prompt context."""
        if not insights:
            return "No prior insight history available."

        lines: List[str] = []
        for row in insights[:5]:
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            topic = data.get("topic", "general")
            issue = data.get("issue", "unclear_concept")
            style = data.get("preferred_style", "guided")
            lines.append(f"- topic={topic}; issue={issue}; preferred_style={style}")

        return "\n".join(lines)
    
    async def _retain_interaction(self, content: str, user_id: str, topic: str, engine_feature: str, interaction_data: Dict[str, Any]) -> None:
        """
        CRITICAL HELPER: Retain interaction to hindsight memory.
        Called after EVERY engine interaction to build persistent memory.
        No errors here should block the main response flow (wrapped in try/except).
        """
        try:
            metadata = {
                "user_id": user_id,
                "topic": topic,
                "engine_feature": engine_feature,
                "interaction_type": "tutoring_session",
                "timestamp": str(__import__("datetime").datetime.now().isoformat()),
                **{f"data_{k}": str(v) for k, v in interaction_data.items()}
            }
            
         
            await self.hindsight.retain_study_session(
                content=content,
                context=metadata
            )
            print(f"✓ [RETAINED] {engine_feature} interaction for user={user_id}, topic={topic}")
        except Exception as e:
            
            print(f"⚠ [WARNING] Failed to retain interaction: {str(e)}")
    
    def _get_connection_confidence(self, num_connections: int) -> float:
        """Confidence based on number of connections found."""
        if num_connections >= 3:
            return 0.90
        elif num_connections == 2:
            return 0.80
        else:
            return 0.70
    
    async def find_connections(self, topic: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Find hidden connections between topics using Groq LLM.
        Returns related topics with connection strengths and explanations.
        
        CRITICAL: Automatically retains this interaction to hindsight for future recalls.
        """
        
        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)

        
        connections = await self._find_graph_connections(topic, user_id, memory_context)
        demo_mode = False

        if connections:
            print(f"[DEBUG] Resonance: Using Hindsight-backed connections for '{topic}'")
        else:
           
            hardcoded = self._get_demo_connections(topic)
            is_curated = not any(conn["topic"] == "foundational concepts" for conn in hardcoded[:1])

            if is_curated:
                connections = hardcoded
                print(f"[DEBUG] Resonance: Using curated fallback for '{topic}'")
            else:
               
                connections = self._connections_from_user_insights(topic, insights)
                if connections:
                    print(f"[DEBUG] Resonance: Using insight-profile fallback for '{topic}'")
                else:
                    connections = hardcoded
                    demo_mode = True
                    print(f"[DEBUG] Resonance: Using generic fallback for '{topic}'")
        
        insight = self._generate_insight(topic, connections[0]) if connections else None
        
        from uuid import uuid4
        response_id = str(uuid4())
        result = {
            "response_id": response_id,
            "feature": "resonance_detection",
            "topic": topic,
            "confidence": self._get_connection_confidence(len(connections)),
            "hidden_connections": connections,
            "insight": insight,
            "demo_mode": demo_mode
        }
        
      
        await self._retain_interaction(
            content=f"Resonance query for {topic}: found {len(connections)} connections",
            user_id=user_id,
            topic=topic,
            engine_feature="resonance",
            interaction_data={
                "connections_count": len(connections),
                "confidence": result["confidence"],
                "insight": str(insight)[:100] if insight else ""
            }
        )
        
        return result
    
    async def _generate_connections_with_llm(self, topic: str, memory_context: str = "") -> List[Dict[str, Any]]:
        """
        Use Groq LLM to generate 5 meaningful related topics with detailed connections.
        Returns structured connections with strength, reasoning, and detailed explanation.
        """
        prompt = f"""User history:
    {memory_context}

    Current question:
    Find hidden conceptual connections for {topic}.

    Instruction:
    Adapt explanation based on user's past struggles.

    TASK: Suggest 5 RELATED TOPICS for learning "{topic}"

CRITICAL: Output ONLY the topics. NO planning, NO thinking, NO explanations about how to explain, NO preamble.

Format EXACTLY (no other text):
Topic: [name]
Strength: [0.60-0.95]
Connection: [How this connects to {topic} - specific technical relationship, 1-2 sentences]
Depth: [Why learning this deepens understanding - 1-2 sentences]

Topic: [name]
Strength: [0.60-0.95]
Connection: [How this connects to {topic} - specific technical relationship, 1-2 sentences]
Depth: [Why learning this deepens understanding - 1-2 sentences]

Topic: [name]
Strength: [0.60-0.95]
Connection: [How this connects to {topic} - specific technical relationship, 1-2 sentences]
Depth: [Why learning this deepens understanding - 1-2 sentences]

Topic: [name]
Strength: [0.60-0.95]
Connection: [How this connects to {topic} - specific technical relationship, 1-2 sentences]
Depth: [Why learning this deepens understanding - 1-2 sentences]

Topic: [name]
Strength: [0.60-0.95]
Connection: [How this connects to {topic} - specific technical relationship, 1-2 sentences]
Depth: [Why learning this deepens understanding - 1-2 sentences]"""

        try:
            response = self.llm.generate(prompt, max_tokens=800, temperature=0.3)
            
           
            response = response.replace("<think>", "").replace("</think>", "")
            
         
            connections = []
            lines = response.split('\n')
            
            current_conn = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Think') or line.startswith('---'):
                 
                    if "Topic" in current_conn and "Strength" in current_conn:
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                        current_conn = {}
                    continue
                
                if line.startswith("Topic:"):
                    if current_conn.get("Topic"): 
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                    current_conn["Topic"] = line.replace("Topic:", "").strip()
                elif line.startswith("Strength:"):
                    try:
                        strength_str = line.replace("Strength:", "").strip()
                        current_conn["Strength"] = float(strength_str)
                    except:
                        current_conn["Strength"] = 0.7
                elif line.startswith("Connection:"):
                    current_conn["Connection"] = line.replace("Connection:", "").strip()
                elif line.startswith("Depth:"):
                    current_conn["Depth"] = line.replace("Depth:", "").strip()
            
            if "Topic" in current_conn and "Strength" in current_conn:
                conn = self._parse_connection_dict(current_conn)
                if conn:
                    connections.append(conn)
            
        
            for conn in connections:
                if "reason" in conn:
                    conn["reason"] = self._clean_thinking_text(conn["reason"])
                if "connection" in conn:
                    conn["connection"] = self._clean_thinking_text(conn["connection"])
                if "depth" in conn:
                    conn["depth"] = self._clean_thinking_text(conn["depth"])
            
        
            valid_connections = [c for c in connections if c and "topic" in c]
            
            if valid_connections:
                print(f"[DEBUG] Resonance LLM generated {len(valid_connections)} connections for '{topic}'")
                return valid_connections[:5]  
            
            print(f"[DEBUG] Resonance LLM parsing failed for '{topic}' - returning empty")
            return []
            
        except Exception as e:
            print(f"[DEBUG] Resonance LLM generation failed: {e}")
            return []
    
    def _normalize_topic(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    def _extract_topic_from_text(self, text: str) -> str:
        if not text:
            return ""
        patterns = [
            r"\b(?:about|on|topic)\b\s*[:]?\s*([a-zA-Z0-9_\-\s]{2,60})",
            r"\bquery\s+for\b\s+([a-zA-Z0-9_\-\s]{2,60})",
            r"\bprediction\s+for\b\s+([a-zA-Z0-9_\-\s]{2,60})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                candidate = re.sub(r"\s+", " ", m.group(1)).strip(" .,:;|-")
                candidate = re.sub(r"^(resonance\s+query\s+for\s+)", "", candidate, flags=re.IGNORECASE).strip()
                if candidate.lower().startswith("query for "):
                    candidate = candidate[10:].strip()
                candidate = re.sub(r"\bfound\s+\d+\s+connections?\b.*$", "", candidate, flags=re.IGNORECASE).strip(" .,:;|-")
                if 1 <= len(candidate.split()) <= 6:
                    return candidate
        return ""

    def _extract_connections_from_memories(self, current_topic: str, hindsight_results: List[Any]) -> List[Dict[str, Any]]:
        current_norm = self._normalize_topic(current_topic)
        counts: Dict[str, int] = {}

        for row in hindsight_results:
            if not isinstance(row, dict):
                continue

            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            candidate = str(metadata.get("topic") or metadata.get("concept") or "").strip()

            if not candidate:
                content_text = str(row.get("content") or row.get("text") or "")
                candidate = self._extract_topic_from_text(content_text)

            if not candidate:
                continue

            candidate_norm = self._normalize_topic(candidate)
            if not candidate_norm or candidate_norm == current_norm:
                continue

            if candidate_norm.startswith("resonance query"):
                continue

            if candidate_norm in {"general", "unknown", "none", "n/a"}:
                continue

            counts[candidate] = counts.get(candidate, 0) + 1

        if not counts:
            return []

        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        max_count = max(c for _, c in top) if top else 1

        connections: List[Dict[str, Any]] = []
        for candidate, count in top:
            relative = count / max_count if max_count else 0.0
            strength = round(min(0.95, max(0.60, 0.60 + 0.35 * relative)), 2)
            connections.append(
                {
                    "topic": candidate,
                    "strength": strength,
                    "reason": f"Appears with high co-occurrence in your Hindsight learning history ({count} related memories).",
                    "connection": f"Your prior study traces connect {current_topic} with {candidate} across retained sessions.",
                    "depth": "Reviewing this topic can strengthen transfer learning and improve conceptual recall for the current topic.",
                }
            )

        return connections

    def _connections_from_user_insights(self, current_topic: str, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        current_norm = self._normalize_topic(current_topic)
        counts: Dict[str, int] = {}

        for row in insights:
            if not isinstance(row, dict):
                continue
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            candidate = str(data.get("topic") or "").strip()
            if not candidate:
                continue

            candidate_norm = self._normalize_topic(candidate)
            if not candidate_norm or candidate_norm == current_norm:
                continue
            if candidate_norm in {"general", "unknown", "none", "n/a"}:
                continue

            counts[candidate] = counts.get(candidate, 0) + 1

        if not counts:
            return []

        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        max_count = max(c for _, c in top) if top else 1
        out: List[Dict[str, Any]] = []
        for candidate, count in top:
            relative = count / max_count if max_count else 0.0
            strength = round(min(0.90, max(0.60, 0.60 + 0.30 * relative)), 2)
            out.append(
                {
                    "topic": candidate,
                    "strength": strength,
                    "reason": f"This topic repeatedly appears in your learning profile ({count} insight signals).",
                    "connection": f"Your prior learning patterns connect {current_topic} and {candidate} through recurring study behavior.",
                    "depth": "Reinforcing this linked topic can improve retention and transfer for your current focus.",
                }
            )

        return out

    async def _find_graph_connections(self, topic: str, user_id: str, memory_context: str = "") -> List[Dict[str, Any]]:
        """
        Query Hindsight using graph strategy to find conceptually related topics.
        Uses LLM to extract meaningful connections from Hindsight results.
        """
        try:
            if not self.hindsight.api_available or not self.hindsight.client:
                return []

            query = f"topics related to {topic} or studied together with {topic}"
            print(f"[DEBUG] Resonance: Querying Hindsight for connections to '{topic}'")

            results: List[Any] = []
            for bank in self.hindsight._bank_candidates(user_id):
                try:
                    rows = await self.hindsight.client.recall(
                        bank_id=bank,
                        query=query,
                        types=["graph", "semantic"],
                        max_tokens=2000,
                    )
                    if rows:
                        results.extend(rows)
                except Exception as bank_error:
                    print(f"[DEBUG] Resonance: Hindsight recall failed for bank={bank}: {bank_error}")

            print(f"[DEBUG] Resonance: Got {len(results)} total results from Hindsight")
            if not results:
                return []

            deterministic = self._extract_connections_from_memories(topic, results)
            if deterministic:
                return deterministic

         
            return await self._extract_connections_with_llm(topic, results, memory_context)
            
        except Exception as e:
            print(f"[DEBUG] Resonance: Hindsight API call failed: {e}")
            return []
    
    async def _extract_connections_with_llm(self, current_topic: str, hindsight_results: List, memory_context: str = "") -> List[Dict[str, Any]]:
        """
        Use Groq LLM to analyze Hindsight results and extract meaningful topic connections.
        """
       
        results_text = ""
        for i, result in enumerate(hindsight_results[:5]):
            if isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)
            
          
            if len(content) > 200:
                content = content[:200] + "..."
            
            results_text += f"{i+1}. {content}\n"
        
        prompt = f"""User history:
    {memory_context}

    Current question:
    Extract related topics for {current_topic}.

    Instruction:
    Adapt explanation based on user's past struggles.

    I studied "{current_topic}" and here are related study memories from my past:

MEMORIES:
{results_text}

Extract up to 3 RELATED TOPICS from these memories that I studied together with or before "{current_topic}".

For EACH related topic, provide:
Topic: [specific topic name]
Strength: [0.60-0.95 connection strength]
Reason: [1-sentence explanation of the connection]

Example format:
Topic: Mathematical Induction
Strength: 0.87
Reason: Both use base case and inductive steps to build complete solutions.

Now extract connections for "{current_topic}":"""

        try:
            response = llm_service.generate(prompt, max_tokens=300, temperature=0.6)
    
            connections = []
            lines = response.split('\n')
            
            current_conn = {}
            for line in lines:
                line = line.strip()
                if not line:
                    
                    if "Topic" in current_conn and "Strength" in current_conn:
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                        current_conn = {}
                    continue
                
                if line.startswith("Topic:"):
                    if current_conn.get("Topic"):  
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                    current_conn["Topic"] = line.replace("Topic:", "").strip()
                elif line.startswith("Strength:"):
                    try:
                        strength_str = line.replace("Strength:", "").strip()
                        current_conn["Strength"] = float(strength_str)
                    except:
                        current_conn["Strength"] = 0.7
                elif line.startswith("Reason:"):
                    current_conn["Reason"] = line.replace("Reason:", "").strip()
            
           
            if "Topic" in current_conn:
                conn = self._parse_connection_dict(current_conn)
                if conn:
                    connections.append(conn)
            
          
            valid_connections = [c for c in connections if c and "topic" in c]
            
            if valid_connections:
                print(f"[DEBUG] LLM extracted {len(valid_connections)} connections from Hindsight")
                return valid_connections[:3]
            
            return []
            
        except Exception as e:
            print(f"[DEBUG] LLM extraction failed: {e}")
            return []
    
    def _parse_connection_dict(self, conn_dict: Dict) -> Dict:
        """
        Convert parsed dict with Topic/Strength/Connection/Depth to standard format.
        """
        if "Topic" not in conn_dict or "Strength" not in conn_dict:
            return None
        
        connection_text = conn_dict.get("Connection", f"Related concept in learning journey")
        depth_text = conn_dict.get("Depth", "Deepens conceptual understanding")
        reason_text = conn_dict.get("Reason", connection_text)
        
        return {
            "topic": conn_dict["Topic"],
            "strength": min(0.95, max(0.60, conn_dict.get("Strength", 0.7))),
            "reason": reason_text,
            "connection": connection_text,
            "depth": depth_text
        }
    
    def _clean_thinking_text(self, text: str) -> str:
        """
        Remove thinking/meta-reasoning patterns from resonance text.
        Similar cleaning as done in archaeology engine.
        """
        if not text:
            return text
        
        s = text.lower()
        
       
        thinking_patterns = [
            "maybe", "i think", "let me", "think about", "wait,",
            "also,", "so,", "then,", "but", "or maybe", "perhaps",
            "could be", "would be", "might", "might help", "that could",
            "should mention", "need to", "avoid", "use", "make sure",
            "let's", "consider", "important to note", "worth noting",
        ]
        
      
        for pattern in thinking_patterns:
            if s.startswith(pattern):
              
                text = text[len(pattern):].strip().lstrip("- ")
                break
        
       
        for pattern in ["for example,", "such as", "like", "for instance"]:
            if pattern in s:
                s = s.replace(pattern, "").strip()
                text = text.replace(pattern, "").strip()
        
        return text.strip()
    
    def _extract_topic_from_content(self, content: str, current_topic: str) -> str:
        """
        Fallback method - extract a related topic name from content (not used now).
        """
        return None
    
    def _generate_insight(self, topic: str, connection: Dict) -> str:
        """
        Generate a user-friendly insight message from a connection.
        """
        related_topic = connection["topic"]
        strength = int(connection["strength"] * 100)
        reason = connection["reason"]
        
        return f"You might find {topic} easier if you revisit {related_topic} first (connection strength: {strength}%). {reason}"
    
    def _get_demo_connections(self, topic: str) -> List[Dict[str, Any]]:
        """
        Generate realistic demo connections based on topic (fallback) - now 5 topics.
        """
        connection_map = {
            "recursion": [
                {
                    "topic": "mathematical induction", 
                    "strength": 0.87,
                    "reason": "Both use base case + inductive step pattern",
                    "connection": "Mathematical induction proves properties by assuming truth and proving one step, just like recursive functions assume the subproblem is solved.",
                    "depth": "Understanding induction helps visualize why recursion works - each level builds on the assumption that smaller problems are solved."
                },
                {
                    "topic": "stack data structure", 
                    "strength": 0.82,
                    "reason": "Recursive calls create a call stack",
                    "connection": "Every recursive call pushes onto the call stack and returns by popping, mirroring exactly how a stack data structure operates.",
                    "depth": "Learning how stacks work reveals why recursion has depth limits and why stack overflow occurs with infinite recursion."
                },
                {
                    "topic": "tree traversal", 
                    "strength": 0.79,
                    "reason": "Tree operations are naturally recursive",
                    "connection": "Tree traversal (DFS, BFS) can be implemented recursively by visiting a node and recursively visiting its children.",
                    "depth": "Tree traversal shows recursion's elegance - each subtree is a smaller tree, making the recursive pattern natural."
                },
                {
                    "topic": "divide and conquer",
                    "strength": 0.75,
                    "reason": "Recursion enables divide and conquer",
                    "connection": "Divide and conquer algorithms recursively split problems into independent subproblems, solve them, and combine results.",
                    "depth": "Recognizing the recursive divide-and-conquer pattern helps solve complex problems by thinking recursively."
                },
                {
                    "topic": "call stack visualization",
                    "strength": 0.72,
                    "reason": "Understanding call stack execution",
                    "connection": "Visualizing how function calls create stack frames helps understand recursion execution flow and memory usage.",
                    "depth": "Tracing through the call stack shows exactly how recursion works at the system level, demystifying the process."
                }
            ],
            "dynamic programming": [
                {
                    "topic": "recursion", 
                    "strength": 0.91,
                    "reason": "DP is optimized recursion with memoization",
                    "connection": "Dynamic programming takes recursive solutions and adds memoization to avoid recalculating the same subproblems.",
                    "depth": "Understanding recursion first makes DP clear - you're just making recursion efficient by remembering solved subproblems."
                },
                {
                    "topic": "memoization", 
                    "strength": 0.88,
                    "reason": "Core optimization technique in DP",
                    "connection": "Memoization caches subproblem solutions in DP to achieve polynomial time instead of exponential.",
                    "depth": "Memoization reveals why DP works - instead of solving f(5) multiple times, you solve it once and look it up afterward."
                },
                {
                    "topic": "optimization", 
                    "strength": 0.75,
                    "reason": "DP minimizes redundant computation",
                    "connection": "DP applies optimization principles like identifying overlapping subproblems and reducing redundant work.",
                    "depth": "Optimization thinking helps you recognize when DP applies - look for repeated subproblems, then optimize."
                },
                {
                    "topic": "graph algorithms", 
                    "strength": 0.73,
                    "reason": "Shortest path uses DP principles",
                    "connection": "Shortest path algorithms like Dijkstra and Floyd-Warshall use DP to build optimal solutions from subproblems.",
                    "depth": "Seeing DP in graph algorithms shows why DP matters practically - real problems use it to find optimal paths."
                },
                {
                    "topic": "time complexity analysis",
                    "strength": 0.68,
                    "reason": "DP transforms exponential to polynomial",
                    "connection": "DP analysis shows how memoization reduces time complexity from exponential to polynomial for many problems.",
                    "depth": "Understanding complexity changes helps you prove DP works - f(5) → O(n²) instead of O(2^n)."
                }
            ],
            "binary trees": [
                {
                    "topic": "recursion", 
                    "strength": 0.88,
                    "reason": "Tree operations are naturally recursive",
                    "connection": "Tree operations like search, insert, and traversal are naturally recursive since each subtree is a smaller tree.",
                    "depth": "Recursion is the natural language for trees - thinking recursively makes tree problems intuitive."
                },
                {
                    "topic": "divide and conquer", 
                    "strength": 0.72,
                    "reason": "Trees split into independent subproblems",
                    "connection": "Each node's problem is solved by solving left subtree, processing node, and solving right subtree independently.",
                    "depth": "Divide and conquer on trees shows how to break complex tree problems into simpler left/right subproblems."
                },
                {
                    "topic": "binary search", 
                    "strength": 0.69,
                    "reason": "Similar halving strategy",
                    "connection": "Binary search trees use recursive halving to eliminate half the search space with each comparison.",
                    "depth": "Understanding binary search's halving principle applies to BST search, showing why balanced trees are efficient."
                },
                {
                    "topic": "balanced trees",
                    "strength": 0.71,
                    "reason": "Maintaining tree height keeps operations efficient",
                    "connection": "Balanced trees maintain optimal height by restructuring after insertions, ensuring O(log n) operations.",
                    "depth": "Learning about balancing shows why BST structure matters - unbalanced trees degrade to linked lists."
                },
                {
                    "topic": "traversal algorithms",
                    "strength": 0.65,
                    "reason": "Multiple ways to visit all nodes",
                    "connection": "In-order, pre-order, and post-order traversals visit nodes in different sequences, each useful for different problems.",
                    "depth": "Mastering traversal orders helps solve tree problems systematically - knowing when to process nodes before or after children."
                }
            ],
            "arrays": [
                {
                    "topic": "sorting", 
                    "strength": 0.84,
                    "reason": "Sorting algorithms operate on arrays",
                    "connection": "Quick sort, merge sort, and heap sort rearrange array elements in-place or with extra space.",
                    "depth": "Array-based sorting reveals key algorithms - understanding how they work on arrays helps you choose the right algorithm."
                },
                {
                    "topic": "searching", 
                    "strength": 0.82,
                    "reason": "Array indexing enables search strategies",
                    "connection": "Linear and binary search traverse arrays differently - binary search exploits sorted array structure.",
                    "depth": "Search strategies show why array organization matters - sorted arrays enable exponentially faster searching."
                },
                {
                    "topic": "hash tables", 
                    "strength": 0.71,
                    "reason": "Hash functions map keys to array indices",
                    "connection": "Hash tables use arrays as underlying storage and hash functions determine where each element goes.",
                    "depth": "Understanding arrays helps explain hash tables - they're arrays with smart indexing via hash functions for O(1) access."
                },
                {
                    "topic": "dynamic arrays",
                    "strength": 0.76,
                    "reason": "Resizing arrays as capacity changes",
                    "connection": "Dynamic arrays (like vectors) grow by doubling size and copying elements when capacity is exceeded.",
                    "depth": "Dynamic arrays show how arrays manage growth - amortized O(1) insertion despite occasional O(n) resizing."
                },
                {
                    "topic": "matrix operations",
                    "strength": 0.69,
                    "reason": "2D arrays as fundamental data structure",
                    "connection": "Matrices use nested arrays to represent 2D data and enable operations like matrix multiplication.",
                    "depth": "Matrix understanding extends array knowledge - rows/columns are arrays, and nested array concepts apply."
                }
            ],
            "graphs": [
                {
                    "topic": "trees", 
                    "strength": 0.85,
                    "reason": "Trees are special acyclic graphs",
                    "connection": "Trees are connected graphs with no cycles - every graph algorithm that works on trees also applies.",
                    "depth": "Understanding trees shows why graphs are general - trees are graphs with restrictions, making them simpler."
                },
                {
                    "topic": "recursion", 
                    "strength": 0.78,
                    "reason": "DFS traversal uses recursive calls",
                    "connection": "Depth-first search traverses graphs by recursively exploring each neighbor's path before backtracking.",
                    "depth": "DFS on graphs shows recursion at scale - managing visited sets and exploring all paths recursively."
                },
                {
                    "topic": "dynamic programming", 
                    "strength": 0.73,
                    "reason": "Shortest path algorithms use DP",
                    "connection": "Dijkstra and Floyd-Warshall use DP to find shortest paths by building solutions from subproblems.",
                    "depth": "DP on graphs is practical - real routing and navigation use these algorithms built on DP principles."
                },
                {
                    "topic": "topological sorting",
                    "strength": 0.70,
                    "reason": "Ordering nodes respecting edges",
                    "connection": "Topological sort orders directed acyclic graph nodes so every edge goes from earlier to later nodes.",
                    "depth": "Topological sort shows graph structure - it's used for dependency resolution and task scheduling."
                },
                {
                    "topic": "connectivity analysis",
                    "strength": 0.67,
                    "reason": "Finding connected components",
                    "connection": "Connected components identify isolated subgraphs using DFS/BFS, crucial for understanding graph structure.",
                    "depth": "Connectivity analysis reveals graph structure - knowing which nodes reach which others is foundational."
                }
            ]
        }
        
        default = [
            {
                "topic": "foundational concepts", 
                "strength": 0.65,
                "reason": "Review fundamentals",
                "connection": "Revisiting foundational concepts strengthens your understanding and reveals hidden connections.",
                "depth": "Strong fundamentals make advanced topics click - many 'aha' moments come from deeper foundation understanding."
            },
            {
                "topic": "related algorithms", 
                "strength": 0.60,
                "reason": "Similar problem-solving patterns",
                "connection": "Related algorithms share similar approaches, making them easier to learn once you understand the pattern.",
                "depth": "Algorithm families group similar techniques - learning one deeply helps you understand others in the group."
            }
        ]
        
        connections = connection_map.get(topic.lower(), default)
        
      
        if len(connections) < 5:
            connections.extend(default)
        
        return connections[:5]  
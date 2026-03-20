
"""
🔗 Feature 4: Cognitive Resonance Detection
Find hidden connections between seemingly unrelated topics.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any, List

class ResonanceEngine:
    """
    Resonance Detection Engine - Graph-based conceptual connections using Hindsight.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service
    
    def _get_connection_confidence(self, num_connections: int) -> float:
        """Confidence based on number of connections found."""
        if num_connections >= 3:
            return 0.90
        elif num_connections == 2:
            return 0.80
        else:
            return 0.70
    
    async def find_connections(self, topic: str) -> Dict[str, Any]:
        """
        Find hidden connections between topics using Groq LLM.
        Returns related topics with connection strengths and explanations.
        """
        
        # First check if we have hardcoded connections for common topics
        hardcoded = self._get_demo_connections(topic)
        is_hardcoded_real = not any(conn["topic"] == "foundational concepts" for conn in hardcoded[:1])
        
        if is_hardcoded_real:
            # We have good hardcoded data for common topics (recursion, arrays, etc.)
            connections = hardcoded
            demo_mode = False
            print(f"[DEBUG] Resonance: Using hardcoded connections for '{topic}'")
        else:
            # For new topics, use LLM to generate smart connections
            connections = await self._generate_connections_with_llm(topic)
            
            if connections and len(connections) > 0:
                demo_mode = False
                print(f"[DEBUG] Resonance: LLM generated {len(connections)} connections for '{topic}'")
            else:
                # Fall back to generic demo if LLM fails
                connections = hardcoded
                demo_mode = True
                print(f"[DEBUG] Resonance: Using demo fallback for '{topic}'")
        
        insight = self._generate_insight(topic, connections[0]) if connections else None
        
        return {
            "feature": "resonance_detection",
            "topic": topic,
            "confidence": self._get_connection_confidence(len(connections)),
            "hidden_connections": connections,
            "insight": insight,
            "demo_mode": demo_mode
        }
    
    async def _generate_connections_with_llm(self, topic: str) -> List[Dict[str, Any]]:
        """
        Use Groq LLM to generate 5 meaningful related topics with detailed connections.
        Returns structured connections with strength, reasoning, and detailed explanation.
        """
        prompt = f"""TASK: Suggest 5 RELATED TOPICS for learning "{topic}"

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
            
            # Remove thinking tags
            response = response.replace("<think>", "").replace("</think>", "")
            
            # Parse LLM response to extract connections
            connections = []
            lines = response.split('\n')
            
            current_conn = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Think') or line.startswith('---'):
                    # Empty line or thinking line - might separate connections
                    if "Topic" in current_conn and "Strength" in current_conn:
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                        current_conn = {}
                    continue
                
                if line.startswith("Topic:"):
                    if current_conn.get("Topic"):  # Save previous if exists
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
            
            # Don't forget the last connection
            if "Topic" in current_conn and "Strength" in current_conn:
                conn = self._parse_connection_dict(current_conn)
                if conn:
                    connections.append(conn)
            
            # Clean thinking words from all text fields
            for conn in connections:
                if "reason" in conn:
                    conn["reason"] = self._clean_thinking_text(conn["reason"])
                if "connection" in conn:
                    conn["connection"] = self._clean_thinking_text(conn["connection"])
                if "depth" in conn:
                    conn["depth"] = self._clean_thinking_text(conn["depth"])
            
            # Return top 5 connections with valid data
            valid_connections = [c for c in connections if c and "topic" in c]
            
            if valid_connections:
                print(f"[DEBUG] Resonance LLM generated {len(valid_connections)} connections for '{topic}'")
                return valid_connections[:5]  # Return 5 instead of 3
            
            print(f"[DEBUG] Resonance LLM parsing failed for '{topic}' - returning empty")
            return []
            
        except Exception as e:
            print(f"[DEBUG] Resonance LLM generation failed: {e}")
            return []
    
    async def _find_graph_connections(self, topic: str) -> List[Dict[str, Any]]:
        """
        Query Hindsight using graph strategy to find conceptually related topics.
        Uses LLM to extract meaningful connections from Hindsight results.
        """
        try:
            # Query Hindsight with graph strategy
            query = f"topics related to {topic} or studied together with {topic}"
            
            print(f"[DEBUG] Resonance: Querying Hindsight for connections to '{topic}'")
            
            # Use Hindsight recall with graph strategy
            results = await self.hindsight.client.recall(
                bank_id=self.hindsight.bank_id,
                query=query,
                types=["graph"],  # Use graph strategy to find connections
                max_tokens=2000
            )
            
            print(f"[DEBUG] Resonance: Got {len(results)} results from Hindsight")
            
            if not results or len(results) == 0:
                return []
            
            # Use LLM to extract meaningful connections from raw Hindsight data
            connections = await self._extract_connections_with_llm(topic, results)
            
            if connections and len(connections) > 0:
                print(f"[DEBUG] Resonance: LLM found {len(connections)} real connections")
                return connections
            
            return []
            
        except Exception as e:
            print(f"[DEBUG] Resonance: Hindsight API call failed: {e}")
            return []
    
    async def _extract_connections_with_llm(self, current_topic: str, hindsight_results: List) -> List[Dict[str, Any]]:
        """
        Use Groq LLM to analyze Hindsight results and extract meaningful topic connections.
        """
        # Format Hindsight results into a prompt-friendly summary
        results_text = ""
        for i, result in enumerate(hindsight_results[:5]):
            if isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)
            
            # Limit content per result
            if len(content) > 200:
                content = content[:200] + "..."
            
            results_text += f"{i+1}. {content}\n"
        
        prompt = f"""I studied "{current_topic}" and here are related study memories from my past:

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
            
            # Parse LLM response to extract connections
            connections = []
            lines = response.split('\n')
            
            current_conn = {}
            for line in lines:
                line = line.strip()
                if not line:
                    # Empty line might separate connections
                    if "Topic" in current_conn and "Strength" in current_conn:
                        conn = self._parse_connection_dict(current_conn)
                        if conn:
                            connections.append(conn)
                        current_conn = {}
                    continue
                
                if line.startswith("Topic:"):
                    if current_conn.get("Topic"):  # Save previous if exists
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
            
            # Don't forget the last connection
            if "Topic" in current_conn:
                conn = self._parse_connection_dict(current_conn)
                if conn:
                    connections.append(conn)
            
            # Return top 3 connections with valid data
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
        
        # Thinking/planning patterns to filter
        thinking_patterns = [
            "maybe", "i think", "let me", "think about", "wait,",
            "also,", "so,", "then,", "but", "or maybe", "perhaps",
            "could be", "would be", "might", "might help", "that could",
            "should mention", "need to", "avoid", "use", "make sure",
            "let's", "consider", "important to note", "worth noting",
        ]
        
        # Check if text starts with thinking pattern
        for pattern in thinking_patterns:
            if s.startswith(pattern):
                # Remove the pattern and any following words that are filler
                text = text[len(pattern):].strip().lstrip("- ")
                break
        
        # Remove any remaining meta-language
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
        
        # For demo, add more if we only have few
        if len(connections) < 5:
            connections.extend(default)
        
        return connections[:5]  # Return 5 instead of 3
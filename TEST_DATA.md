# Cogni - Test Data Guide

## 1. SOCRATIC FEATURE
Test with different concepts and misconceptions:

```
Concept: recursion
Belief: "Recursion is just a loop with different syntax"

Concept: dynamic_programming
Belief: "DP is only useful for optimization problems"

Concept: pointers
Belief: "Pointers are always faster than regular variables"

Concept: async_programming
Belief: "Async automatically makes code parallel"

Concept: inheritance
Belief: "Inheritance is always better than composition"

Concept: closures
Belief: "Closures capture variables by value, not reference"
```

### Direct API Testing
```bash
# Test 1: Recursion misconception
curl "http://localhost:8000/socratic/ask?concept=recursion&user_belief=recursion%20is%20just%20loops" -X POST

# Test 2: Dynamic Programming
curl "http://localhost:8000/socratic/ask?concept=dynamic_programming&user_belief=only%20for%20optimization" -X POST

# Test 3: Pointers
curl "http://localhost:8000/socratic/ask?concept=pointers&user_belief=always%20faster" -X POST
```

---

## 2. SHADOW FEATURE
Get predictions based on current topic:

```
Topic: recursion
→ Predicts: Dynamic Programming (memoization/overlapping subproblems)

Topic: arrays
→ Predicts: Hash Tables (index mapping vs value lookup)

Topic: graphs
→ Predicts: Topological Sorting (graph ordering constraints)

Topic: sorting
→ Predicts: Heap Operations (advanced ordering with priority)

Topic: strings
→ Predicts: String Algorithms KMP/Z-algorithm (pattern matching)

Topic: trees
→ Predicts: Graph Traversal (extending tree logic to cycles)

Topic: loops
→ Predicts: Nested Data Structures (multi-dimensional iterations)

Topic: backtracking
→ Predicts: Advanced State Management (complex reset logic)
```

### Direct API Testing
```bash
# Test 1: Recursion
curl "http://localhost:8000/insights/shadow?topic=recursion" -X GET

# Test 2: Arrays
curl "http://localhost:8000/insights/shadow?topic=arrays" -X GET

# Test 3: Graphs
curl "http://localhost:8000/insights/shadow?topic=graphs" -X GET

# Test 4: Sorting
curl "http://localhost:8000/insights/shadow?topic=sorting" -X GET

# Test 5: Strings
curl "http://localhost:8000/insights/shadow?topic=strings" -X GET
```

---

## 3. ARCHAEOLOGY FEATURE
Find similar past struggles:

```
Topic: recursion
Confusion Level: 1 (very confused)

Topic: dynamic_programming
Confusion Level: 3 (moderately confused)

Topic: graph_algorithms
Confusion Level: 5 (very clear understanding)

Topic: bit_manipulation
Confusion Level: 2 (mostly confused)

Topic: binary_search
Confusion Level: 4 (mostly clear)
```

### Direct API Testing
```bash
# Test 1: High confusion
curl "http://localhost:8000/study/archaeology?topic=recursion&confusion_level=1" -X GET

# Test 2: Medium confusion
curl "http://localhost:8000/study/archaeology?topic=dynamic_programming&confusion_level=3" -X GET

# Test 3: Low confusion
curl "http://localhost:8000/study/archaeology?topic=graph_algorithms&confusion_level=5" -X GET
```

---

## 4. RESONANCE FEATURE
Find conceptual connections:

```
Topics to explore:
- recursion (connections to loops, stacks, call stack)
- dynamic_programming (connections to recursion, optimization, memoization)
- graphs (connections to trees, arrays, linked lists)
- sorting (connections to comparison, efficiency, stability)
- hashing (connections to arrays, collision, distribution)
- binary_search (connections to sorted arrays, logarithmic, divide-and-conquer)
```

### Direct API Testing
```bash
# Test 1: Recursion connections
curl "http://localhost:8000/insights/resonance?topic=recursion" -X GET

# Test 2: DP connections
curl "http://localhost:8000/insights/resonance?topic=dynamic_programming" -X GET

# Test 3: Graph connections
curl "http://localhost:8000/insights/resonance?topic=graphs" -X GET
```

---

## 5. CONTAGION FEATURE
Share community solutions for errors:

```
Error Patterns:
- "off_by_one_error" (common in array iteration)
- "null_pointer_exception" (memory access issues)
- "infinite_loop" (incorrect termination condition)
- "stack_overflow" (recursion base case missing)
- "incorrect_state_management" (in complex algorithms)
- "type_mismatch_error" (variable scope issues)
```

### Direct API Testing
```bash
# Test 1: Off-by-one errors
curl "http://localhost:8000/insights/contagion?error_pattern=off_by_one_error" -X GET

# Test 2: Stack overflow
curl "http://localhost:8000/insights/contagion?error_pattern=stack_overflow" -X GET

# Test 3: State management
curl "http://localhost:8000/insights/contagion?error_pattern=incorrect_state_management" -X GET
```

---

## 6. FRONTEND TEST WORKFLOW

### Scenario 1: Complete Learning Session
```
1. User asks about recursion
   → Socratic asks: "How can you trace through a simple recursive call?"
   → Shadow predicts: "Next you'll struggle with Dynamic Programming"
   → Archaeology finds: "Last time you confused base cases"

2. User asks about arrays
   → Socratic asks: "What happens when you access index -1?"
   → Shadow predicts: "Hash Tables will be your next challenge"
   → Archaeology finds: "You've done well with array iteration"

3. User asks about graphs
   → Socratic asks: "How is DFS different from BFS in practice?"
   → Shadow predicts: "Topological Sorting will challenge you next"
   → Contagion shows: "47 students struggled with the same concept"
```

### Scenario 2: Testing Error Recovery
```
- Ask about "null_pointer_exception" 
  → Contagion shows community solutions
  
- Ask about "infinite_loop"
  → Contagion shows: "visual_trace" helped 82% of students
  
- Ask about "stack_overflow"
  → Contagion shows: "check_base_case" helped 78% of students
```

---

## 7. BULK TEST CHECKLIST

Run these in order:
```
✅ Health Check
GET http://localhost:8000/health

✅ Socratic Tests (3 different concepts)
POST /socratic/ask?concept=recursion&user_belief=...
POST /socratic/ask?concept=arrays&user_belief=...
POST /socratic/ask?concept=graphs&user_belief=...

✅ Shadow Tests (5 different topics)
GET /insights/shadow?topic=recursion
GET /insights/shadow?topic=arrays
GET /insights/shadow?topic=graphs
GET /insights/shadow?topic=sorting
GET /insights/shadow?topic=strings

✅ Archaeology Tests (3 different confusion levels)
GET /study/archaeology?topic=recursion&confusion_level=1
GET /study/archaeology?topic=arrays&confusion_level=3
GET /study/archaeology?topic=graphs&confusion_level=5

✅ Resonance Tests (3 topics)
GET /insights/resonance?topic=recursion
GET /insights/resonance?topic=graphs
GET /insights/resonance?topic=sorting

✅ Contagion Tests (3 error patterns)
GET /insights/contagion?error_pattern=off_by_one_error
GET /insights/contagion?error_pattern=stack_overflow
GET /insights/contagion?error_pattern=infinite_loop

✅ Memory Tests
GET /memory/recall?limit=10
```

---

## 8. EXPECTED RESPONSES

### Socratic Response
```json
{
  "question": "How would you approach a simpler base case first?",
  "concept": "recursion",
  "confidence": 0.85
}
```

### Shadow Response
```json
{
  "prediction": "Your Cognitive Twin predicts you'll struggle with Dynamic Programming next...",
  "confidence": 0.85,
  "evidence": [
    "Progression pattern: mastering recursion leads to DP challenges",
    "Common error: recursion base cases suggest similar issues in DP"
  ],
  "current_topic": "recursion"
}
```

### Archaeology Response
```json
{
  "similar_moments": 3,
  "what_helped_before": [
    {
      "hint_used": "visual_analogy",
      "confidence": 0.92,
      "outcome": "resolved"
    }
  ],
  "recommendation": "Try the visual unwrapping gifts exercise again"
}
```

---

## 9. QUICK POWERSHELL TEST COMMANDS

```powershell
# Test all Socratic
"recursion", "arrays", "graphs" | ForEach-Object { 
  Write-Host "Testing: $_"
  (Invoke-RestMethod -Uri "http://localhost:8000/socratic/ask?concept=$_&user_belief=test" -Method Post).data.question
}

# Test all Shadow
"recursion", "arrays", "graphs", "sorting", "strings" | ForEach-Object {
  Write-Host "Topic: $_"
  (Invoke-RestMethod -Uri "http://localhost:8000/insights/shadow?topic=$_" -Method Get).data.prediction
}

# Test all Archaeology
"recursion", "arrays", "graphs" | ForEach-Object {
  Write-Host "Topic: $_"
  (Invoke-RestMethod -Uri "http://localhost:8000/study/archaeology?topic=$_&confusion_level=3" -Method Get).data
}
```

---

## 10. NOTES FOR TESTING

1. **Socratic** - Varies based on the concept and belief
2. **Shadow** - Predicts next topic based on current topic
3. **Archaeology** - Currently returns demo data (Hindsight API limitation)
4. **Resonance** - Shows conceptual connections (LLM-powered)
5. **Contagion** - Shows community insights (currently demo mode)
6. **Memory** - Stores/recalls study sessions

All features integrate with Hindsight Service for persistent memory storage.

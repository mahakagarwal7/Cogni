# 🚀 Cogni API Endpoints - Quick Reference

## Server Status

- **URL**: `http://localhost:8000`
- **Health Check**: `GET /health`
- **Docs**: `GET /docs` (Swagger UI)

---

## 1️⃣ SOCRATIC - Teaching Questions via Misconceptions

**Endpoint**: `POST /socratic/ask`

**Query Parameters**:

- `concept` (string, required): What topic is the misconception about?
- `user_belief` (string, required): What does the student incorrectly believe?

**Example**:

```bash
curl -X POST "http://localhost:8000/socratic/ask?concept=rotational%20motion&user_belief=I%20think%20rotational%20motion%20is%20just%20linear%20motion%20in%20circles"
```

**Sample Response**:

```json
{
  "status": "success",
  "data": {
    "feature": "socratic_method",
    "concept": "rotational motion",
    "user_belief": "I think rotational motion is just linear motion in circles",
    "question": "How does rotational motion differ from linear motion in terms of direction and acceleration?",
    "confidence": 0.85
  },
  "demo_mode": false
}
```

**Confidence**: Fixed at 0.85 for all Socratic questions (indicates system confidence in the quality of the question)

---

## 2️⃣ SHADOW - Next Challenge Prediction

**Endpoint**: `GET /insights/shadow`

**Query Parameters**:

- `topic` (string, optional): Current topic being studied
- `days` (integer, optional): Days to analyze (default: 7)

**Example**:

```bash
curl "http://localhost:8000/insights/shadow?topic=rotational%20motion&days=7"
```

**Sample Response**:

```json
{
  "status": "success",
  "data": {
    "feature": "cognitive_shadow",
    "current_topic": "rotational motion",
    "prediction": "Your Cognitive Twin predicts you'll struggle with Angular Momentum next.",
    "evidence": [
      "Progression pattern: mastering rotational motion often leads to Angular Momentum challenges"
    ],
    "confidence": 0.85,
    "recent_learning": ["linear motion", "force", "rotational motion"]
  },
  "demo_mode": false
}
```

---

## 3️⃣ ARCHAEOLOGY - Teaching Recommendations

**Endpoint**: `GET /study/archaeology`

**Query Parameters**:

- `topic` (string, required): What topic needs teaching recommendations?
- `confusion_level` (integer, required): How confused is student? (1-5 scale)
- `days` (integer, optional): How many days back to look? (default: 30)

**Example**:

```bash
curl "http://localhost:8000/study/archaeology?topic=rotational%20motion&confusion_level=3&days=30"
```

**Sample Response**:

```json
{
  "status": "success",
  "data": {
    "feature": "temporal_archaeology",
    "query": {
      "topic": "rotational motion",
      "confusion_level": 3
    },
    "confidence": 0.75,
    "result": {
      "similar_moments": 18,
      "what_helped_before": [...],
      "recommendation": "Rotational motion is a core concept... Use concrete examples like a merry-go-round... Try hands-on activities...",
      "demo_mode": false
    },
    "actionable": true
  },
  "demo_mode": false
}
```

**Confidence Calculation**: Based on `confusion_level`:
- 1 (No confusion) → 0.95
- 2 (Slight confusion) → 0.85
- 3 (Moderate) → 0.75
- 4 (High confusion) → 0.60
- 5 (Very confused) → 0.50

---

## 4️⃣ RESONANCE - Topic Connections

**Endpoint**: `GET /insights/resonance`

**Query Parameters**:

- `topic` (string, required): What topic should we find connections for?

**Example**:

```bash
curl "http://localhost:8000/insights/resonance?topic=rotational%20motion"
```

**Sample Response**:

```json
{
  "status": "success",
  "data": {
    "feature": "resonance_detection",
    "topic": "rotational motion",
    "confidence": 0.90,
    "hidden_connections": [
      {
        "topic": "Torque",
        "strength": 0.9,
        "reason": "Understanding torque is essential for analyzing the causes of rotational motion."
      },
      {
        "topic": "Angular Momentum",
        "strength": 0.85,
        "reason": "Angular momentum explains conservation principles in rotating systems."
      },
      {
        "topic": "Moment of Inertia",
        "strength": 0.8,
        "reason": "Determines how mass distribution affects rotational acceleration."
      }
    ],
    "insight": "You might find rotational motion easier if you revisit Torque first (connection strength: 90%).",
    "demo_mode": false
  },
  "demo_mode": false
}
```

**Confidence Calculation**: Based on number of connections found:
- 3+ connections → 0.90
- 2 connections → 0.80
- <2 connections → 0.70

---

## Advanced: Memory/Study Session Logging

### Save a Study Session

**Endpoint**: `POST /study/log`

**Body** (JSON):

```json
{
  "topic": "rotational motion",
  "duration_minutes": 45,
  "difficulty_level": 3,
  "confusion_areas": ["angular acceleration", "torque calculation"],
  "success_indicators": ["solved 3 problems", "understood angular momentum"]
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "status": "error",
  "detail": "Human-readable error message",
  "demo_mode": true
}
```

---

## Testing All Features Together

```bash
#!/bin/bash

TOPIC="rotational motion"
MISCONCEPTION="I think rotational motion is just linear motion in circles"

echo "1. Ask Socratic Question..."
curl -X POST "http://localhost:8000/socratic/ask?concept=$TOPIC&user_belief=$MISCONCEPTION"

echo -e "\n\n2. Get Next Challenge..."
curl "http://localhost:8000/insights/shadow?topic=$TOPIC"

echo -e "\n\n3. Get Teaching Recommendations..."
curl "http://localhost:8000/study/archaeology?topic=$TOPIC&confusion_level=3"

echo -e "\n\n4. Find Related Topics..."
curl "http://localhost:8000/insights/resonance?topic=$TOPIC"
```

---

## Frontend Integration Notes

When building the frontend UI:

1. All endpoints return `demo_mode` boolean - show indicator if in demo
2. Confidence scores (0-1) can show badge/meter
3. Hidden connections strength (0-1) can show as % or strength bars
4. Recommendations are long-form educational content (format as readable text)

For real-time updates, consider polling every 5-10 seconds or using WebSocket.

---

**API Version**: 1.0  
**Last Updated**: 2025-01  
**Status**: ✅ All endpoints tested and working

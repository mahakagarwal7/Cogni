# 🧠 Cogni — Metacognitive Study Companion

**AI learning agents powered by Hindsight memory + LLM reasoning**
---
**Live Deployed link** : https://cogni8cws.vercel.app/
---
**Video Link** : https://drive.google.com/file/d/1dUk7YRL_s8WFhrGKAbt_Ki-B2IGe2J1u/view?usp=sharing

Cogni is a full-stack learning system that helps students understand concepts deeply, track learning progress over time, and receive adaptive coaching across multiple cognitive modes.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.0-brightgreen)
![Next.js](https://img.shields.io/badge/Next.js-16.2.0-black)
![UI](https://img.shields.io/badge/UI-Tailwind%20v4-06B6D4)

---

## 📚 Table of Contents

- [Project Overview](#-project-overview)
- [What’s New](#-whats-new)
- [Core Features](#-core-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Setup](#-setup)
- [Run the App](#-run-the-app)
- [API Surface](#-api-surface)
- [Feature Usage Guide](#-feature-usage-guide)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Project Overview

Cogni combines specialized AI engines with persistent learning memory to create a personalized study experience.

### Why Cogni

- Tracks how a student learns over time, not just one chat turn.
- Uses **Hindsight memory** to ground recommendations in prior behavior.
- Uses **LLM reasoning** to adapt explanations, questions, and roadmaps.
- Provides both conversational guidance and visual memory analytics.

---

## ✨ Core Features

### 1) 🏛️ Temporal Cognitive Archaeology

**Goal:** Find when confusion patterns appeared and what helped previously.

- Endpoint: `GET /study/archaeology`
- Inputs: topic + confusion level
- Output: grounded recommendation + adaptive explanation context

---

### 2) 🤔 Socratic Ghost

**Goal:** Challenge misconceptions with targeted, adaptive questioning.

- Endpoints: `POST /socratic/ask`, `POST /socratic/reflect`, `POST /socratic/hint`
- Supports multi-turn questioning with response-aware follow-ups
- Includes compact metadata for question continuity

---

### 3) 👥 Cognitive Shadow

**Goal:** Predict likely next struggle areas from topic + patterns.

- Endpoint: `GET /insights/shadow`
- Returns prediction overview, evidence, and confidence signals

---

### 4) 🔗 Resonance Engine

**Goal:** Discover hidden conceptual links between topics.

- Endpoint: `GET /insights/resonance`
- Hybrid approach: hardcoded fast paths + LLM-generated connections

---

### 5) 🧬 Metacognitive Contagion (Personalized Roadmap)

**Goal:** Learn from personal + peer patterns with a full guided plan.

- Endpoint: `GET /insights/contagion`
- Pipeline: personal memory recall → style inference → strategy refinement → roadmap generation
- Returns:
  - top strategy
  - additional strategies
  - learning plan (full roadmap text)
  - memory grounding metadata

---

### 6) 🧠 Memory Intelligence

**Goal:** Make learning history visible and actionable.

- Endpoints:
  - `GET /memory/recall`
  - `GET /memory/timeline`
  - `GET /memory/confidence`
  - `GET /memory/summary`
  - `GET /memory/what-cogni-knows`
- Frontend uses timeline + confidence data for student performance visualization.

---

### 7) 📝 Study Summary + PDF

- `POST /memory/summary` for text summaries
- `POST /memory/summary/pdf` for downloadable study PDFs

---

### 8) ✅ Quiz & Feedback Loop

- Quiz:
  - `GET /study/quiz`
  - `POST /study/quiz/submit`
- Feedback & quality signals:
  - `POST /feedback/log`
  - `POST /feedback/suggest`
  - `GET /feedback/user-progress`
  - `GET /feedback/insights`

---

## 🛠️ Tech Stack

### Frontend

- **Framework:** Next.js 16.2.0
- **UI:** React 19 + TypeScript 5 + Tailwind CSS 4
- **Components:** Radix UI + custom UI system
- **Charts:** Recharts

### Backend

- **Framework:** FastAPI
- **Model layer:** Pydantic
- **AI:** Groq LLM + Hindsight memory client
- **Docs:** OpenAPI/Swagger (`/docs`)
- **PDF:** ReportLab + FPDF2 fallback

---

## 🧩 Architecture

Cogni follows a resilient hybrid pattern across engines:

1. Use deterministic/hardcoded logic when reliable
2. Enrich via hindsight memory retrieval
3. Personalize with LLM generation
4. Fall back safely if upstream generation is weak or unavailable

This keeps UX stable while preserving high-quality adaptive behavior.

---

## 📁 Project Structure

```text
Cogni/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── engines/
│   │   │   ├── archaeology_engine.py
│   │   │   ├── socratic_engine.py
│   │   │   ├── shadow_engine.py
│   │   │   ├── resonance_engine.py
│   │   │   └── contagion_engine.py
│   │   ├── routes/
│   │   │   ├── study_routes.py
│   │   │   ├── socratic_routes.py
│   │   │   ├── insights_routes.py
│   │   │   ├── memory_routes.py
│   │   │   ├── feedback_routes.py
│   │   │   └── health_routes.py
│   │   ├── services/
│   │   └── models/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx
│   │   ├── services/api.ts
│   │   └── components/
│   └── package.json
└── README.md
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm (or yarn/pnpm)
- Groq API key

### 1) Clone

```bash
git clone <repository-url>
cd Cogni
```

### 2) Backend

```bash
cd backend
python -m venv .venv
```

Activate environment:

- Windows PowerShell: `./.venv/Scripts/Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env`:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

### 3) Frontend

```bash
cd ../frontend
npm install
npm run dev
```

---

## ▶️ Run the App

### Backend

```bash
cd backend
python run.py
```

Backend URLs:

- API root: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### Frontend

```bash
cd frontend
npm run dev
```

Frontend URL: `http://localhost:3000`

### Production build

```bash
cd frontend
npm run build
npm run start
```

---

## 🔌 API Surface

> All routes are available under both direct paths and `/api/*` aliases.

### Health

- `GET /health`

### Study

- `POST /study/log`
- `GET /study/archaeology`
- `GET /study/quiz`
- `POST /study/quiz/submit`

### Socratic

- `POST /socratic/ask`
- `POST /socratic/reflect`
- `POST /socratic/hint`
- `POST /socratic/log`
- `GET /socratic/history`
- `GET /socratic/killer-prompt-preview`

### Insights

- `GET /insights/shadow`
- `GET /insights/patterns`
- `GET /insights/resonance`
- `GET /insights/contagion`

### Memory

- `GET /memory/recall`
- `GET /memory/timeline`
- `GET /memory/confidence`
- `GET /memory/summary`
- `GET /memory/what-cogni-knows`
- `POST /memory/summary`
- `POST /memory/summary/pdf`

### Feedback

- `GET /feedback/insights`
- `POST /feedback/suggest`
- `GET /feedback/user-progress`
- `POST /feedback/log`

---

## 🧭 Feature Usage Guide

### Archaeology

1. Select **Archaeology**
2. Set topic + confusion level
3. Submit confusion statement
4. Review past-pattern recommendation

### Socratic

1. Select **Socratic**
2. Enter belief/understanding
3. Answer follow-up questions
4. Use hints if stuck

### Shadow

1. Select **Shadow**
2. Set current topic
3. Request prediction
4. Review warning signals and micro-actions

### Resonance

1. Select **Resonance**
2. Enter topic
3. Review concept links and why they matter

### Contagion

1. Select **Contagion**
2. Enter topic/error pattern
3. Generate roadmap
4. Follow the full personalized plan in order

### Memory & Graphs

1. Open **Memory** or **Graphs**
2. Refresh analytics
3. Review confidence trends, timeline, and profile insights

---

## 🐛 Troubleshooting

### 500 on contagion endpoint

- Ensure backend is running latest code and dependencies.
- Restart backend after updates to engine signatures.
- Verify endpoint in browser/Swagger:
  - `GET /insights/contagion?error_pattern=recursion&user_id=student`

### Frontend shows fallback text

- Check backend status in UI (online/offline indicator).
- Confirm response `status` is `success` in network tab.
- Verify `learning_plan` exists in `data` payload.

### LLM behavior seems generic

- Confirm `GROQ_API_KEY` in `backend/.env`.
- Check backend logs for upstream errors/timeouts.

---

## 🤝 Contributing

- Keep route contracts backward compatible.
- Add fallbacks when introducing LLM-dependent features.
- Validate both backend and frontend behavior after changes.
- Update docs when endpoints or payloads evolve.

---

## 🎉 Final Note

Cogni is built to be both **adaptive** and **reliable**: memory-grounded where possible, LLM-augmented where useful, and safe-fallback by default.

# 🧠 Cogni - Metacognitive Study Companion

**AI Agents That Learn Using Hindsight**

Cogni is an intelligent study companion that uses advanced AI agents to help you understand concepts better, analyze your learning progress, and optimize your study sessions through metacognitive feedback and personalized insights.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.0-brightgreen)
![Next.js](https://img.shields.io/badge/Next.js-16.2.0-black)

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Features Guide](#features-guide)
- [File Organization](#file-organization)

---

## 🎯 Project Overview

Cogni is a full-stack metacognitive study application that combines intelligent AI agents with interactive learning tools. The platform helps students understand concepts deeply by providing temporal analysis of confusion points, Socratic questioning, cognitive pattern analysis, and personalized study recommendations.

**Key Innovation:** Uses Hindsight Memory technology to learn from conversation history and provide context-aware, intelligent responses.

---

## ✨ Features

### 🏛️ **Temporal Cognitive Archaeology**

Analyzes your learning history to identify when confusion patterns first emerged and trace thought evolution through time.

### 🤔 **Socratic Ghost**

Challenges your assumptions and misconceptions through carefully crafted questions designed to deepen understanding.

### 👥 **Cognitive Shadow**

Mirrors your thinking patterns and provides insights into your learning behavior and cognitive style.

### 🔄 **Resonance Engine**

Finds connections between concepts you've learned, helping you build a holistic understanding.

### 🧬 **Contagion Analysis**

Traces how understanding in one domain can propagate and influence learning in related areas.

### 📚 **Memory & Study Planning**

Generates AI-powered summaries of conversations, extracts key insights, and creates downloadable PDF study plans with dynamic topic-based filenames.

---

## 🛠️ Tech Stack

### **Frontend**

- **Framework:** Next.js 16.2.0
- **Library:** React 19.2.4
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4
- **UI Components:**
  - Radix UI (icons, labels, separators, sliders)
  - Custom component library
- **HTTP Client:** Axios 1.13.6
- **Utilities:** class-variance-authority, clsx, tailwind-merge

### **Backend**

- **Framework:** FastAPI 0.135.0
- **Server:** Uvicorn 0.32.0
- **Validation:** Pydantic 2.7.0
- **AI Integration:**
  - Hindsight Client 0.1.0 (Conversation Memory)
  - Groq 0.13.0 (LLM API - qwen/qwen3-32b)
- **PDF Generation:**
  - ReportLab 4.0.0 (Primary)
  - FPDF2 2.7.0 (Fallback)
- **HTTP:** HTTPX 0.27.2
- **Environment:** python-dotenv 1.0.1

---

## 📁 Project Structure

```
Cogni/
├── backend/                          # FastAPI backend server
│   ├── app/
│   │   ├── main.py                   # FastAPI app initialization & routing
│   │   ├── engines/                  # AI Agent Engines
│   │   │   ├── archaeology_engine.py # Temporal analysis engine
│   │   │   ├── socratic_engine.py    # Socratic questioned engine
│   │   │   ├── shadow_engine.py      # Cognitive pattern analysis
│   │   │   ├── resonance_engine.py   # Concept connection engine
│   │   │   └── contagion_engine.py   # Cross-domain learning engine
│   │   ├── routes/                   # API Endpoints
│   │   │   ├── study_routes.py       # Study feature endpoints
│   │   │   ├── socratic_routes.py    # Socratic agent endpoints
│   │   │   ├── memory_routes.py      # Memory & summary endpoints
│   │   │   ├── insights_routes.py    # Insights & analysis endpoints
│   │   │   └── health_routes.py      # Health check endpoints
│   │   ├── services/                 # Business Logic
│   │   │   ├── summary_service.py    # Summary generation & PDF creation
│   │   │   └── hindsight_service.py  # Hindsight memory integration
│   │   └── models/                   # Data Models
│   │       └── memory_types.py       # Type definitions
│   ├── requirements.txt              # Python dependencies
│   ├── run.py                        # Development server launcher
│   ├── test_*.py                     # Test scripts
│   └── scripts/
│       ├── seed_demo_data.py         # Demo data seeding
│       └── endpoint_audit.ps1        # API endpoint audit
│
├── frontend/                         # Next.js frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Main chat interface (All features)
│   │   │   ├── layout.tsx            # App layout wrapper
│   │   │   └── globals.css           # Global styles
│   │   ├── components/               # React components
│   │   │   └── ui/                   # Reusable UI components
│   │   ├── services/
│   │   │   └── api.ts                # API client & endpoints
│   │   └── lib/                      # Utility functions
│   ├── public/                       # Static assets
│   ├── package.json                  # Node.js dependencies
│   ├── tsconfig.json                 # TypeScript config
│   ├── tailwind.config.ts            # Tailwind CSS config
│   ├── next.config.ts                # Next.js config
│   └── eslint.config.mjs             # ESLint rules
│
└── README.md                         # This file
```

---

## 📦 Prerequisites

### **Required**

- **Python 3.8 or higher**
- **Node.js 18 or higher** (with npm or yarn)
- **Git** (for version control)

### **API Keys Required**

- **Groq API Key** - For LLM-powered features (free tier available)
- Create `.env` file in `backend/` directory with:
  ```
  GROQ_API_KEY=your_api_key_here
  ```

### **Optional**

- **Virtual Environment Tool** - venv, conda, or poetry (recommended for Python)
- **Package Manager** - npm, yarn, or pnpm for Node.js

---

## 🚀 Installation

### **1. Clone Repository**

```bash
git clone <repository-url>
cd Cogni
```

### **2. Backend Setup**

#### Using venv (Recommended)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Using conda

```bash
cd backend
conda create -n cogni python=3.10
conda activate cogni
pip install -r requirements.txt
```

### **3. Configure Environment**

```bash
cd backend

# Create .env file
# Add your Groq API key:
# GROQ_API_KEY=your_key_here
```

### **4. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

---

## 🎯 Running the Application

### **Start Backend Server**

```bash
cd backend

# Activate virtual environment (if using venv)
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Run development server
python run.py
```

**Backend runs on:** `http://localhost:8000`

**Available documentation:**

- Swagger UI (Interactive API): `http://localhost:8000/docs`
- ReDoc (API Reference): `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

### **Start Frontend Server**

```bash
cd frontend

# Development mode
npm run dev
# or
yarn dev
# or
pnpm dev
```

**Frontend runs on:** `http://localhost:3000`

### **Build for Production**

```bash
# Frontend
cd frontend
npm run build
npm start

# Backend (uses Uvicorn)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔌 API Documentation

### **Base URL**

- Development: `http://localhost:8000`
- Endpoints available under `/` and `/api/` paths

### **Core Endpoints**

#### **Health Check**

```
GET /health
```

Returns application status and available features.

#### **Study Features**

```
POST /study/generate
POST /study/analyze
GET /study/history
```

#### **Socratic Agent**

```
POST /socratic/question
POST /socratic/dialog
GET /socratic/history
```

#### **Memory & Summaries**

```
POST /memory/summary           # Generate AI summary from conversation
POST /memory/summary/pdf       # Download summary as PDF
GET /memory/summaries          # List previous summaries
```

#### **Insights**

```
POST /insights/analyze
GET /insights/learning-patterns
```

### **Interactive API Testing**

Visit `http://localhost:8000/docs` for full Swagger UI with:

- Real-time request/response testing
- Parameter validation
- Example requests
- Response schemas

---

## 📚 Features Guide

### **Using Archaeology Engine**

1. Start a study session
2. Click **Archaeology** button
3. Provide topic/question
4. Get temporal analysis of confusion patterns

### **Using Socratic Agent**

1. Click **Socratic** button
2. Share your understanding of a topic
3. Receive challenging questions
4. Refine your thinking

### **Using Cognitive Shadow**

1. Share your learning approach
2. Click **Shadow** button
3. Receive feedback on your cognitive patterns

### **Generating Study Summaries**

1. Have a conversation in any feature
2. Click **Memory** tab
3. Click **Generate Summary**
4. View preview in chat
5. Click **Download PDF** for topic-based study plan

### **Analyzing Learning Resonance**

1. Click **Resonance** button
2. Discuss multiple related concepts
3. Discover connections and patterns

---

## 📂 File Organization Guide

### **Backend Files Explained**

| File               | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `app/main.py`      | FastAPI app setup, CORS configuration, route registration |
| `app/engines/`     | AI agents implementing different cognitive strategies     |
| `app/routes/`      | REST API endpoint handlers                                |
| `app/services/`    | Business logic and external service integration           |
| `app/models/`      | Pydantic models for data validation                       |
| `run.py`           | Development server launcher script                        |
| `requirements.txt` | Python package dependencies                               |

### **Frontend Files Explained**

| File                  | Purpose                               |
| --------------------- | ------------------------------------- |
| `src/app/page.tsx`    | Main chat interface with feature tabs |
| `src/app/layout.tsx`  | App wrapper and metadata              |
| `src/services/api.ts` | HTTP client for backend communication |
| `src/components/ui/`  | Reusable UI component library         |
| `tailwind.config.ts`  | Tailwind CSS customization            |
| `tsconfig.json`       | TypeScript configuration              |
| `package.json`        | npm scripts and dependencies          |

---

## 🔧 Configuration

### **Backend Configuration Files**

- `.env` - Environment variables (Groq API key)
- `app/main.py` - CORS settings, app metadata

### **Frontend Configuration Files**

- `next.config.ts` - Next.js settings
- `tsconfig.json` - TypeScript settings
- `tailwind.config.ts` - Tailwind CSS theming

---

## 📖 Development Tips

### **Backend Development**

- API routes auto-reload when you modify code
- Check `http://localhost:8000/docs` for live API testing
- Use test scripts in `backend/test_*.py` for validation

### **Frontend Development**

- Hot reload enabled for `.tsx` files
- Tailwind CSS changes apply instantly
- Use browser DevTools for debugging

### **Testing**

```bash
# Backend tests
cd backend
python test_minimal_api.py
python test_routes_with_hindsight.py
```

---

## 📊 Plugin System

The application uses the following plugins/integrations:

### **Frontend Plugins**

- **Radix UI** - Accessible component library
- **Tailwind CSS** - Utility-first CSS framework
- **TypeScript** - Static type checking

### **Backend Plugins**

- **Hindsight Client** - Conversation memory library
- **Groq API** - Large language model inference
- **ReportLab/FPDF2** - PDF generation
- **Pydantic** - Data validation

---

## 🎓 Learning Resources

### **Key Components**

1. **Engines** - Read `backend/app/engines/` for AI agent implementations
2. **Routes** - Check `backend/app/routes/` for API endpoint patterns
3. **Services** - See `backend/app/services/` for business logic
4. **Frontend** - Study `frontend/src/app/page.tsx` for React patterns

### **API Testing**

- Use Swagger UI at `/docs` for interactive testing
- Check request/response formats
- Test error scenarios

---

## 🤝 Contributing

When contributing to Cogni:

1. Keep API routes RESTful and consistent
2. Add descriptive docstrings to new functions
3. Test features in both `/` and `/api/` paths
4. Update this README with new features
5. Follow existing code style and patterns

---

## 📝 Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (defaults provided)
# DEBUG=true
# LOG_LEVEL=info
```

---

## 🐛 Troubleshooting

### **Common Issues**

**PDF not generating?**

- Ensure reportlab and fpdf2 are installed: `pip install reportlab fpdf2`

**API endpoint not found?**

- Check that all routers are included in `app/main.py`
- Try both `/` and `/api/` prefixes

**Frontend can't connect to backend?**

- Ensure backend is running on port 8000
- Check CORS settings in `app/main.py`

**Getting API errors?**

- Check Groq API key is set in `.env`
- Visit `/docs` to test endpoints directly

---

## 📄 Additional Notes

- All timestamps are recorded for learning analysis
- Conversations are processed with Hindsight memory technology
- PDF summaries use dynamic filenames based on learning topics
- The application is designed for interactive learning sessions

---

## 🎉 Ready to Learn!

Your Cogni application is ready to help you master subjects through intelligent metacognitive analysis. Start a conversation, pick a feature, and let AI-powered insights guide your learning journey!

For questions or issues, check the API documentation at `http://localhost:8000/docs`

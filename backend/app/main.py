# backend/app/main.py
"""
🧠 Cogni FastAPI Application
Main entry point for the backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import study_routes, memory_routes, health_routes

# Create FastAPI app
app = FastAPI(
    title="Cogni API",
    description="Metacognitive Study Companion - Powered by Hindsight Memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (allow frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://127.0.0.1:3000",
        "*",  # Allow all for hackathon demo (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(study_routes.router)
app.include_router(memory_routes.router)
app.include_router(health_routes.router)

# Root endpoint
@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": "Cogni API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Temporal Cognitive Archaeology",
            "Socratic Ghost",
            "Cognitive Shadow",
            "Resonance Detection",
            "Metacognitive Contagion"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Quick health check for deployments"""
    return {"status": "ok", "service": "cogni-backend"}
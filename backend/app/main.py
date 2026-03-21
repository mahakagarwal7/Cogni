# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routes
from app.routes import study_routes, memory_routes, health_routes
from app.routes import socratic_routes, insights_routes  # ← ADD THESE
from app.routes import feedback_routes

app = FastAPI(
    title="Cogni API",
    description="Metacognitive Study Companion - Powered by Hindsight Memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(study_routes.router)
app.include_router(memory_routes.router)
app.include_router(health_routes.router)
app.include_router(socratic_routes.router)  # ← ADD THIS
app.include_router(insights_routes.router)  # ← ADD THIS
app.include_router(feedback_routes.router)

# Compatibility aliases: also expose all APIs under /api/*
app.include_router(study_routes.router, prefix="/api")
app.include_router(memory_routes.router, prefix="/api")
app.include_router(health_routes.router, prefix="/api")
app.include_router(socratic_routes.router, prefix="/api")
app.include_router(insights_routes.router, prefix="/api")
app.include_router(feedback_routes.router, prefix="/api")

@app.get("/")
async def root():
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

@app.get("/health")
async def health():
    return {"status": "ok", "service": "cogni-backend", "demo_mode": True}
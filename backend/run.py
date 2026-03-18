# backend/run.py
"""
🚀 Cogni Backend Entry Point
Run with: python run.py
Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Get config from environment
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", 8000))
    
    print(f"🧠 Starting Cogni Backend...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"💡 Demo Mode: {os.getenv('DEMO_MODE', 'false')}")
    print("-" * 50)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info"
    )
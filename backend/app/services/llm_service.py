# backend/app/services/llm_service.py
"""
🤖 LLM Service - Groq API Integration for AI-powered responses.
"""
import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")


class LLMService:
    """
    Unified interface for Groq LLM calls.
    Used by all engines for generating AI responses.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
        
        if not self.api_key:
            print("[WARNING] GROQ_API_KEY not set. LLM features will be disabled.")
            self.available = False
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                self.available = True
                print(f"[SUCCESS] Groq LLM initialized: model={self.model}")
            except Exception as e:
                print(f"[WARNING] Failed to initialize Groq: {str(e)}")
                self.available = False
                self.client = None
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text using Groq.
        Falls back to demo response if API unavailable.
        """
        if not self.available or not self.client:
            return self._get_demo_response(prompt)
        
        try:
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            response_text = message.choices[0].message.content
            print(f"[SUCCESS] Groq generation completed")
            return response_text
            
        except Exception as e:
            print(f"[WARNING] Groq API error: {str(e)}")
            return self._get_demo_response(prompt)
    
    def _get_demo_response(self, prompt: str) -> str:
        """Fallback demo response."""
        if "misconception" in prompt.lower():
            return "Let's explore this concept deeper. What's the simplest case you can think of?"
        elif "confusion" in prompt.lower():
            return "Based on patterns, breaking down the concept step-by-step helps most students."
        else:
            return "That's an interesting question. Let me show you how other students approached this."


# Singleton instance
llm_service = LLMService()

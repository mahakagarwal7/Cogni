"""
Local fallback storage for when Hindsight API is unavailable.
Gracefully captures interactions locally as a degraded mode.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class LocalMemoryFallback:
    """Store interactions locally when Hindsight API is unavailable."""
    
    def __init__(self):
        self.memory_dir = Path(__file__).resolve().parents[2] / "_local_memory"
        self.memory_dir.mkdir(exist_ok=True)
        
    def save_interaction(self, bank_id: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Save interaction to local JSON file."""
        try:
            # Create bank-specific file
            bank_file = self.memory_dir / f"{bank_id}_memories.json"
            
            # Load existing memories
            memories = []
            if bank_file.exists():
                with open(bank_file, 'r') as f:
                    memories = json.load(f)
            
            # Add new interaction
            memory_item = {
                "id": f"{len(memories)}_{int(datetime.now().timestamp() * 1000)}",
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "stored_locally": True
            }
            memories.append(memory_item)
            
            # Save back
            with open(bank_file, 'w') as f:
                json.dump(memories, f, indent=2)
            
            print(f"✓ [LOCAL FALLBACK] Saved to {bank_file.name}")
            return {"status": "success", "stored_locally": True, "id": memory_item["id"]}
        except Exception as e:
            print(f"⚠ [LOCAL FALLBACK ERROR] {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_memories(self, bank_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve locally stored memories."""
        try:
            bank_file = self.memory_dir / f"{bank_id}_memories.json"
            if not bank_file.exists():
                return []
            
            with open(bank_file, 'r') as f:
                memories = json.load(f)
            
            return memories[-limit:] if memories else []
        except Exception as e:
            print(f"⚠ [LOCAL FALLBACK ERROR] Failed to read memories: {str(e)}")
            return []
    
    def get_user_memories(self, bank_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memories for a specific user."""
        try:
            memories = self.get_memories(bank_id, limit * 2)  # Get extra to filter
            return [
                m for m in memories 
                if m.get("metadata", {}).get("user_id") == user_id
            ][-limit:]
        except Exception as e:
            print(f"⚠ [LOCAL FALLBACK ERROR] {str(e)}")
            return []
    
    def get_topic_memories(self, bank_id: str, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memories for a specific topic."""
        try:
            memories = self.get_memories(bank_id, limit * 2)
            return [
                m for m in memories 
                if m.get("metadata", {}).get("topic") == topic
            ][-limit:]
        except Exception as e:
            print(f"⚠ [LOCAL FALLBACK ERROR] {str(e)}")
            return []
    
    def count_memories(self, bank_id: str) -> int:
        """Count total interactions stored locally."""
        try:
            bank_file = self.memory_dir / f"{bank_id}_memories.json"
            if not bank_file.exists():
                return 0
            with open(bank_file, 'r') as f:
                memories = json.load(f)
            return len(memories)
        except:
            return 0


# Singleton instance
local_memory = LocalMemoryFallback()

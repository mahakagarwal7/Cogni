

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface APIResponse {
  status: 'success' | 'error';
  data?: unknown;
  message?: string;
  demo_mode?: boolean;
}

export const api = {
  
  async health(): Promise<unknown> {
    const res = await fetch(`${API_URL}/health`);
    return res.json();
  },

  
  async getArchaeology(topic: string, confusionLevel: number): Promise<APIResponse> {
    const res = await fetch(
      `${API_URL}/study/archaeology?topic=${encodeURIComponent(topic)}&confusion_level=${confusionLevel}`
    );
    return res.json();
  },

 
  async askSocratic(concept: string, userBelief: string): Promise<APIResponse> {
    const res = await fetch(
      `${API_URL}/socratic/ask?concept=${encodeURIComponent(concept)}&user_belief=${encodeURIComponent(userBelief)}`,
      { method: 'POST' }
    );
    return res.json();
  },

  
  async getShadowPrediction(topic?: string, days: number = 7): Promise<APIResponse> {
    const params = new URLSearchParams({ days: String(days) });
    if (topic) {
      params.append('topic', topic);
    }
    const res = await fetch(`${API_URL}/insights/shadow?${params.toString()}`);
    return res.json();
  },

  
  async getResonance(topic: string): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/insights/resonance?topic=${encodeURIComponent(topic)}`);
    return res.json();
  },

  
  async getContagion(errorPattern: string): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/insights/contagion?error_pattern=${encodeURIComponent(errorPattern)}`);
    return res.json();
  },

 
  async getMemories(limit: number = 10): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/memory/recall?limit=${limit}`);
    return res.json();
  },
  // UPGRADE: Generate conversation summary
  async generateSummary(conversation: string): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/memory/summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation })
    });
    return res.json();
  },

  // UPGRADE: Download summary as PDF
  async downloadSummaryPDF(summaryText: string, topicName?: string): Promise<Blob> {
    const res = await fetch(`${API_URL}/memory/summary/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary_text: summaryText, topic_name: topicName || 'learning_summary' })
    });
    return res.blob();
  },
  async logStudySession(session: Record<string, unknown>): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/study/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(session)
    });
    return res.json();
  }
};
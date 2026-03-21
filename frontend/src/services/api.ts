

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface APIResponse {
  status: 'success' | 'error';
  data?: unknown;
  message?: string;
  demo_mode?: boolean;
}

export interface SuggestStrategyRequest {
  user_id: string;
  query: string;
  topic?: string;
  limit?: number;
}

export interface UserProgressResponse {
  user_id: string;
  weak_topics: string[];
  improvement_score: number;
  past_mistakes: string[];
  insights_count: number;
}

export interface FeedbackLogRequest {
  user_id: string;
  user_query: string;
  llm_response: string;
  engine_used: string;
  feedback_text: string;
  rating: number;
  interaction_id?: string;
  understood?: boolean;
  confidence?: number;
  topic?: string;
  metadata?: Record<string, unknown>;
}

export interface QuizSubmissionRequest {
  user_id: string;
  topic: string;
  questions?: string[];
  student_answers?: string[];
  correct_answers?: string[];
  score?: number;
  total_questions?: number;
  mistakes?: string[];
  time_taken_seconds?: number;
}

export const api = {
  
  async health(): Promise<unknown> {
    const res = await fetch(`${API_URL}/health`);
    return res.json();
  },

  
  async getArchaeology(topic: string, confusionLevel: number, userId: string = 'student'): Promise<APIResponse> {
    const res = await fetch(
      `${API_URL}/study/archaeology?topic=${encodeURIComponent(topic)}&confusion_level=${confusionLevel}&user_id=${encodeURIComponent(userId)}`
    );
    return res.json();
  },

 
  async askSocratic(concept: string, userBelief: string, userId: string = 'student', confusionLevel: number = 3): Promise<APIResponse> {
    const res = await fetch(
      `${API_URL}/socratic/ask?concept=${encodeURIComponent(concept)}&user_belief=${encodeURIComponent(userBelief)}&user_id=${encodeURIComponent(userId)}&confusion_level=${confusionLevel}`,
      { method: 'POST' }
    );
    return res.json();
  },

  async reflectSocratic(
    concept: string,
    userResponse: string,
    previousQuestion: string,
    userId: string = 'student',
    confusionLevel: number = 3
  ): Promise<APIResponse> {
    const params = new URLSearchParams({
      concept: concept,
      user_response: userResponse,
      previous_question: previousQuestion,
      user_id: userId,
      confusion_level: String(confusionLevel)
    });
    const res = await fetch(`${API_URL}/socratic/reflect?${params.toString()}`, { method: 'POST' });
    return res.json();
  },

  
  async getShadowPrediction(topic?: string, days: number = 7, userId: string = 'student'): Promise<APIResponse> {
    const params = new URLSearchParams({ days: String(days), user_id: userId });
    if (topic) {
      params.append('topic', topic);
    }
    const res = await fetch(`${API_URL}/insights/shadow?${params.toString()}`);
    return res.json();
  },

  
  async getResonance(topic: string, userId: string = 'student'): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/insights/resonance?topic=${encodeURIComponent(topic)}&user_id=${encodeURIComponent(userId)}`);
    return res.json();
  },

  
  async getContagion(errorPattern: string, userId: string = 'student'): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/insights/contagion?error_pattern=${encodeURIComponent(errorPattern)}&user_id=${encodeURIComponent(userId)}`);
    return res.json();
  },

 
  async getMemories(limit: number = 10): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/memory/recall?limit=${limit}`);
    return res.json();
  },

  async generateQuiz(topic: string, userId: string = 'student'): Promise<APIResponse> {
    const params = new URLSearchParams({ topic, user_id: userId });
    const res = await fetch(`${API_URL}/study/quiz?${params.toString()}`);
    return res.json();
  },

  async submitQuiz(payload: QuizSubmissionRequest): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/study/quiz/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  async suggestResponseStrategy(payload: SuggestStrategyRequest): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/feedback/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  async getUserProgress(userId: string, topic?: string): Promise<APIResponse> {
    const params = new URLSearchParams({ user_id: userId });
    if (topic) {
      params.append('topic', topic);
    }
    const res = await fetch(`${API_URL}/feedback/user-progress?${params.toString()}`);
    return res.json();
  },

  async logFeedback(payload: FeedbackLogRequest): Promise<APIResponse> {
    const res = await fetch(`${API_URL}/feedback/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  // PHASE 9: Get killer prompt preview with memory context and adaptive rules
  async getKillerPromptPreview(userId: string, query: string, topic?: string): Promise<APIResponse> {
    const params = new URLSearchParams({ user_id: userId, query });
    if (topic) params.append('topic', topic);
    const res = await fetch(`${API_URL}/socratic/killer-prompt-preview?${params.toString()}`);
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
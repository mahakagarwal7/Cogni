
"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/services/api";
import {
  PlusCircledIcon,
  ReaderIcon,
  CubeIcon,
  StarIcon,
  LightningBoltIcon,
  MagicWandIcon,
  CheckIcon,
  Cross1Icon,
  TrashIcon,
  CopyIcon,
} from "@radix-ui/react-icons";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

type FeatureMode =
  | "archaeology"
  | "socratic"
  | "shadow"
  | "resonance"
  | "contagion"
  | "memory";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  feature?: FeatureMode;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

type GenericRecord = Record<string, unknown>;
type APIShape = {
  data?: unknown;
  demo_mode?: boolean;
};

type QuizQuestion = {
  id: number;
  question: string;
  expected_answer: string;
};

const FEATURES: {
  id: FeatureMode;
  label: string;
  icon: React.ReactNode;
  description: string;
}[] = [
  {
    id: "archaeology",
    label: "Archaeology",
    icon: <PlusCircledIcon className="h-5 w-5" />,
    description: "When did I last feel this confused?",
  },
  {
    id: "socratic",
    label: "Socratic",
    icon: <ReaderIcon className="h-5 w-5" />,
    description: "Question my misconceptions",
  },
  {
    id: "shadow",
    label: "Shadow",
    icon: <CubeIcon className="h-5 w-5" />,
    description: "Predict my next struggle",
  },
  {
    id: "resonance",
    label: "Resonance",
    icon: <StarIcon className="h-5 w-5" />,
    description: "Find hidden connections",
  },
  {
    id: "contagion",
    label: "Contagion",
    icon: <LightningBoltIcon className="h-5 w-5" />,
    description: "Learn from peer patterns",
  },
  {
    id: "memory",
    label: "Memory",
    icon: <MagicWandIcon className="h-5 w-5" />,
    description: "View what you remember",
  },
];

const QUICK_PROMPTS: Record<FeatureMode, string[]> = {
  archaeology: [
    "I keep missing recursion base cases",
    "I get confused with dynamic programming states",
    "Why do I mix up BFS and DFS?",
  ],
  socratic: [
    "I think recursion is just looping",
    "Binary search works on any list",
    "Memoization and tabulation are the same",
  ],
  shadow: [
    "Predict my next weak area",
    "What am I likely to struggle with this week?",
    "Show early warning signs from my pattern",
  ],
  resonance: [
    "Find links between recursion and trees",
    "How does graph thinking relate to DP?",
    "Connect sorting intuition to greedy methods",
  ],
  contagion: [
    "machine learning",
    "web development",
    "database design",
    "system design",
    "python programming",
  ],
  memory: [
    "Refresh my memory profile",
    "Show latest study memories",
    "What patterns are stored for me?",
  ],
};
export default function ChatPage() {
  // Intro screen state
  const [isStarted, setIsStarted] = useState(true);
  const [activeFeature, setActiveFeature] =
    useState<FeatureMode>("archaeology");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastDemoMode, setLastDemoMode] = useState<boolean | null>(null);
  const [backendState, setBackendState] = useState<
    "checking" | "online" | "offline"
  >("checking");
  const [context, setContext] = useState<{
    topic?: string;
    confusion?: number;
    errorPattern?: string;
  }>({});
  // UPGRADE: Add summary state
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [progressLoading, setProgressLoading] = useState(false);
  const [killerPromptLoading, setKillerPromptLoading] = useState(false);
  const [previewSummary, setPreviewSummary] = useState<string | null>(null);
  const [fullSummary, setFullSummary] = useState<string | null>(null);
  const [feedbackByMessageId, setFeedbackByMessageId] = useState<Record<string, number>>({});
  const [feedbackLoadingByMessageId, setFeedbackLoadingByMessageId] = useState<Record<string, boolean>>({});
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizTopic, setQuizTopic] = useState("recursion");
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  const [quizAnswers, setQuizAnswers] = useState<string[]>([]);
  const [quizStartedAt, setQuizStartedAt] = useState<number | null>(null);
  // UPGRADE: User session persisted to localStorage
  const [userId, setUserIdState] = useState("student");
  const [showUserIdInput, setShowUserIdInput] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        id: "welcome",
        role: "system",
        content: `Cogni — Your Metacognitive Study Companion\n\nSelect a feature to start. I remember your learning journey and adapt to how you learn.`,
        timestamp: new Date(),
      },
    ]);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("start") === "1") {
      setIsStarted(true);
      localStorage.setItem("cogni_started", "1");
    }

    const started = localStorage.getItem("cogni_started");
    if (started === "1") {
      setIsStarted(true);
    }

    const stored = localStorage.getItem("cogni_user_id");
    if (stored && stored !== "student") {
      setUserIdState(stored);
    } else {
      const generated = `student_${Math.random().toString(36).slice(2, 8)}`;
      setUserIdState(generated);
      localStorage.setItem("cogni_user_id", generated);
    }
  }, []);

  const enterApp = () => {
    setIsStarted(true);
    localStorage.setItem("cogni_started", "1");
  };

  const setUserId = (newId: string) => {
    const clean = newId.trim() || `student_${Math.random().toString(36).slice(2, 8)}`;
    setUserIdState(clean);
    localStorage.setItem("cogni_user_id", clean);
  };

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.health();
        setBackendState("online");
      } catch {
        setBackendState("offline");
      }
    };
    checkBackend();
  }, []);
  const handleSend = async () => {
    // Resonance and Contagion use header topic field, not main input
    const requiresInput = [
      "archaeology",
      "socratic",
    ].includes(activeFeature);
    
    // For contagion, check context.topic instead
    if (activeFeature === "contagion") {
      if (!context.topic?.trim()) return;
    } else if (requiresInput && !input.trim()) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Type your question first, then press Send.",
          timestamp: new Date(),
        },
      ]);
      return;
    }
    
    // For resonance, check context.topic instead
    if (activeFeature === "resonance") {
      if (!context.topic?.trim()) return;
    }
    
    if (loading) return;

    const requestQuery = input.trim() || context.topic || "general";

    if (requiresInput) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: input,
        feature: activeFeature,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
    }
    setInput("");
    setLoading(true);

    try {
      let response;
      let strategySuggestion: Record<string, unknown> | null = null;

      // Best-effort orchestrator strategy hint. If it fails, existing flow remains unchanged.
      try {
        const suggestionResponse = await api.suggestResponseStrategy({
          user_id: userId,
          query: requestQuery,
          topic: context.topic,
          limit: 15,
        });

        const suggestionData = suggestionResponse.data as Record<string, unknown> | undefined;
        const suggestion = suggestionData?.suggestion;
        if (suggestion && typeof suggestion === "object") {
          strategySuggestion = suggestion as Record<string, unknown>;
        }
      } catch {
        // Intentionally ignore to keep chat pipeline stable.
      }

      switch (activeFeature) {
        case "archaeology": {
          const topic = context.topic || extractTopic(input);
          const confusion = context.confusion || 3;
          response = await api.getArchaeology(topic, confusion, userId);
          break;
        }

        case "socratic": {
          const concept = context.topic || extractTopic(input);
          const confusion = context.confusion || 3;
          
          // Check if the previous message was a Socratic question (ending with ?)
          // If so, treat the current input as a response and reflect instead of asking
          const prevMessage = messages[messages.length - 1];
          const shouldReflect = prevMessage?.role === "assistant" && prevMessage?.content?.endsWith("?");
          
          if (shouldReflect && prevMessage?.content) {
            // User is responding to a previous Socratic question - reflect on the response
            response = await api.reflectSocratic(
              concept,
              input,
              prevMessage.content,
              userId,
              confusion
            );
          } else {
            // First question or starting a new line of thinking
            response = await api.askSocratic(concept, input, userId, confusion);
          }
          break;
        }

        case "shadow": {
          const shadowTopic = context.topic || extractTopic(input);
          response = await api.getShadowPrediction(shadowTopic, 7, userId);
          break;
        }

        case "resonance": {
          const resonanceTopic = context.topic!.trim(); // Guaranteed to exist from handleSend check
          response = await api.getResonance(resonanceTopic, userId);
          break;
        }

        case "contagion": {
          // UPGRADE: Use header topic field like Archaeology, not main input
          const contagionTopic = context.topic || input.trim();
          if (!contagionTopic) {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                role: "assistant",
                content:
                  "Please enter a topic in the header field above that you want to learn about (e.g., recursion, dynamic programming, sorting algorithms).",
                timestamp: new Date(),
              },
            ]);
            setLoading(false);
            return;
          }
          response = await api.getContagion(contagionTopic, userId);
          break;
        }

        case "memory": {
          response = await api.getMemories(10);
          break;
        }

        default: {
          response = {
            data: { result: { recommendation: "Select a feature to get started!" } },
          };
        }
      }

      if (!response) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: "No response received. Please try again.",
            timestamp: new Date(),
          },
        ]);
        setLoading(false);
        return;
      }

      if (typeof response?.demo_mode === "boolean") {
        setLastDemoMode(response.demo_mode);
      }

      const assistantMessage = formatResponse(response, activeFeature);
      const mergedMetadata: Record<string, unknown> = {
        ...(assistantMessage.metadata || {}),
      };

      if (strategySuggestion) {
        if (strategySuggestion.recommended_style) {
          mergedMetadata.recommended_style = strategySuggestion.recommended_style;
        }
        if (strategySuggestion.target_topic) {
          mergedMetadata.target_topic = strategySuggestion.target_topic;
        }
      }
      mergedMetadata.user_query = requestQuery;

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: assistantMessage.content,
          feature: activeFeature,
          timestamp: new Date(),
          metadata: mergedMetadata,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          feature: activeFeature,
          timestamp: new Date(),
        },
      ]);
      console.error("API Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const submitMessageFeedback = async (message: Message, rating: number) => {
    if (message.role !== "assistant") {
      return;
    }

    setFeedbackLoadingByMessageId((prev) => ({ ...prev, [message.id]: true }));

    try {
      const index = messages.findIndex((m) => m.id === message.id);
      const previousUserMessage = [...messages.slice(0, index)]
        .reverse()
        .find((m) => m.role === "user");

      const messageMetadata = (message.metadata || {}) as GenericRecord;
      const userQueryFromMetadata =
        typeof messageMetadata.user_query === "string"
          ? messageMetadata.user_query
          : undefined;
      const userQuery =
        previousUserMessage?.content || userQueryFromMetadata || context.topic || "general";

      const topicFromMetadata =
        typeof messageMetadata.target_topic === "string"
          ? messageMetadata.target_topic
          : undefined;
      const topic = topicFromMetadata || context.topic || extractTopic(userQuery);

      const responseId =
        typeof messageMetadata.response_id === "string"
          ? messageMetadata.response_id
          : undefined;

      const rawConfidence = messageMetadata.confidence;
      const confidence =
        typeof rawConfidence === "number"
          ? rawConfidence
          : typeof rawConfidence === "string"
            ? Number(rawConfidence)
            : undefined;

      await api.logFeedback({
        user_id: userId,
        user_query: userQuery,
        llm_response: message.content,
        engine_used: message.feature || "orchestrator",
        feedback_text:
          rating >= 4
            ? "Helpful response"
            : rating === 3
              ? "Partially helpful response"
              : "Not helpful response",
        rating,
        interaction_id: responseId,
        understood: rating >= 3,
        confidence:
          confidence !== undefined && Number.isFinite(confidence) ? confidence : undefined,
        topic,
      });

      setFeedbackByMessageId((prev) => ({ ...prev, [message.id]: rating }));
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 5).toString(),
          role: "assistant",
          content: "Could not save feedback right now. Your response is still available.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setFeedbackLoadingByMessageId((prev) => ({ ...prev, [message.id]: false }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleContextUpdate = (key: string, value: string | number) => {
    setContext((prev) => ({ ...prev, [key]: value }));
  };
  const clearChat = () => {
    setMessages([
      {
        id: "welcome",
        role: "system",
        content: `Chat cleared. Select a feature to continue.`,
        timestamp: new Date(),
      },
    ]);
    setContext({});
    setQuizQuestions([]);
    setQuizAnswers([]);
    setQuizStartedAt(null);
  };

  const handleQuickPrompt = (prompt: string) => {
    if (activeFeature === "shadow" || activeFeature === "memory") {
      void handleSend();
      return;
    }
    if (activeFeature === "contagion") {
      setContext((prev) => ({ ...prev, errorPattern: prompt }));
    }
    if (
      activeFeature === "archaeology" ||
      activeFeature === "socratic" ||
      activeFeature === "resonance"
    ) {
      setContext((prev) => ({ ...prev, topic: extractTopic(prompt) }));
    }
    setInput(prompt);
  };

  // UPGRADE: Generate conversation summary
  const generateSummary = async () => {
    setSummaryLoading(true);
    
    try {
      // Build conversation text from messages
      const conversationText = messages
        .filter(m => m.role !== 'system')
        .map(m => `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`)
        .join("\n\n");
      
      if (conversationText.length < 50) {
        const errorMsg = "Not enough conversation yet to summarize. Keep learning!";
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: errorMsg,
            timestamp: new Date(),
          }
        ]);
        setSummaryLoading(false);
        return;
      }
      
      const response = await api.generateSummary(conversationText);
      
      if (response.data) {
        const responseData = response.data as Record<string, any>;
        const preview = responseData.preview || "Summary unavailable";
        const fullSummaryText = responseData.full_summary || "Summary unavailable";
        
        setPreviewSummary(preview);
        setFullSummary(fullSummaryText);
        
        // Add preview to chat
        const previewMessage = `📚 **Your Learning Summary Preview**\n\n${preview}\n\n*(Click 'Download PDF' to get the complete study plan)*`;
        
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: previewMessage,
            timestamp: new Date(),
          }
        ]);
      } else {
        const errorMsg = "Summary generation failed. Please try again.";
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: errorMsg,
            timestamp: new Date(),
          }
        ]);
      }
    } catch (error) {
      console.error("Summary generation failed:", error);
      const errorMsg = `❌ Summary generation failed: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`;
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: errorMsg,
          timestamp: new Date(),
        }
      ]);
    } finally {
      setSummaryLoading(false);
    }
  };

  const showUserProgress = async () => {
    setProgressLoading(true);

    try {
      const currentTopic = context.topic || undefined;
      const response = await api.getUserProgress(userId, currentTopic);
      const progress = (response.data as Record<string, unknown> | undefined) || {};

      const studiedTopics = Array.isArray(progress.studied_topics)
        ? (progress.studied_topics as string[])
        : [];
      const recentTopics = Array.isArray(progress.recent_topics)
        ? (progress.recent_topics as string[])
        : [];
      const highConfidenceTopics = Array.isArray(progress.high_confidence_topics)
        ? (progress.high_confidence_topics as string[])
        : [];
      const pastMistakes = Array.isArray(progress.past_mistakes)
        ? (progress.past_mistakes as string[])
        : [];
      const improvementScore = Number(progress.improvement_score ?? 0);
        const studySessionsCount = Number(progress.study_sessions_count ?? 0);
      const topicLabel = currentTopic ? currentTopic.replace(/_/g, " ") : "Overall";

      const studiedTopicsText = studiedTopics.length
        ? studiedTopics.map((topic) => `• ${topic.replace(/_/g, " ")}`).join("\n")
        : "• No topics studied yet";
      
      const recentTopicsText = recentTopics.length
        ? recentTopics.map((topic) => `• ${topic.replace(/_/g, " ")}`).join("\n")
        : "• Get started by exploring a topic";
      
      const masteredTopicsText = highConfidenceTopics.length
        ? highConfidenceTopics.map((topic) => `✓ ${topic.replace(/_/g, " ")}`).join("\n")
        : "• Keep studying to master topics";

      const pastMistakesText = pastMistakes.length
        ? pastMistakes.map((item) => `• ${item.replace(/_/g, " ")}`).join("\n")
        : "• No repeated mistakes detected";

  const wowMessage = `📊 **Your Learning Journey**\n\n**What You've Studied** (${studySessionsCount} sessions)\n${studiedTopicsText}\n\n**Recently Explored**\n${recentTopicsText}\n\n**Topics You're Mastering** ⭐\n${masteredTopicsText}\n\n**Progress Trend**\n${improvementScore > 0 ? "📈 Improving: +" : improvementScore < 0 ? "📉 Declining: " : "→ Steady: "}${Math.abs(improvementScore).toFixed(1)}%\n\n**Focus Areas**\n${pastMistakesText}`;

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 3).toString(),
          role: "assistant",
          content: wowMessage,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 3).toString(),
          role: "assistant",
          content: `❌ Could not load progress right now: ${error instanceof Error ? error.message : "Unknown error"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setProgressLoading(false);
    }
  };

  // PHASE 9: Show killer prompt preview
  const showKillerPromptPreview = async () => {
    setKillerPromptLoading(true);

    try {
      const query = input.trim() || context.topic || "recursion";
      const topic = context.topic;

      const response = await api.getKillerPromptPreview(userId, query, topic);
      const data = (response.data as Record<string, unknown> | undefined) || {};

      const memoryContext = String(data.memory_context || "No memory context");
      const killerPrompt = String(data.killer_prompt || "No prompt generated");
      const rules = data.adaptive_rules as Record<string, unknown> | undefined;

      const rulesList = rules
        ? `• Simplify: ${rules.simplify}\n• Provide Examples: ${rules.provide_examples}\n• Change Style: ${rules.change_style}\n• Preferred Style: ${rules.preferred_style}`
        : "No rules extracted";

      const previewMessage = `🧠 **PHASE 9: Killer Prompt Preview**\n\n**Memory Context:**\n${memoryContext}\n\n**Adaptive Rules:**\n${rulesList}\n\n**Full Prompt (First 500 chars):**\n${killerPrompt.substring(0, 500)}...`;

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 4).toString(),
          role: "assistant",
          content: previewMessage,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 4).toString(),
          role: "assistant",
          content: `❌ Could not preview killer prompt: ${error instanceof Error ? error.message : "Unknown error"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setKillerPromptLoading(false);
    }
  };

  const generateQuiz = async () => {
    setQuizLoading(true);
    try {
      const topic = (quizTopic || context.topic || "recursion").trim();
      const response = await api.generateQuiz(topic, userId);
      const payload = (response.data as Record<string, unknown> | undefined) || {};
      const rawQuestions = Array.isArray(payload.questions) ? payload.questions : [];

      const parsedQuestions: QuizQuestion[] = rawQuestions
        .map((row, idx) => {
          const record = row as Record<string, unknown>;
          return {
            id: Number(record.id ?? idx + 1),
            question: String(record.question ?? ""),
            expected_answer: String(record.expected_answer ?? ""),
          };
        })
        .filter((q) => q.question && q.expected_answer)
        .slice(0, 3);

      if (!parsedQuestions.length) {
        throw new Error("No quiz questions were generated");
      }

      setQuizQuestions(parsedQuestions);
      setQuizAnswers(new Array(parsedQuestions.length).fill(""));
      setQuizStartedAt(Date.now());

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 6).toString(),
          role: "assistant",
          content: `🧪 Quiz ready on **${topic}**. Answer the 3 questions below, then click Submit Quiz.`,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 6).toString(),
          role: "assistant",
          content: `❌ Could not generate quiz: ${error instanceof Error ? error.message : "Unknown error"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setQuizLoading(false);
    }
  };

  const submitQuiz = async () => {
    if (!quizQuestions.length) {
      return;
    }

    setQuizSubmitting(true);
    try {
      const topic = (quizTopic || context.topic || "recursion").trim();
      const elapsedSeconds = quizStartedAt ? Math.max(1, Math.round((Date.now() - quizStartedAt) / 1000)) : 0;

      const response = await api.submitQuiz({
        user_id: userId,
        topic,
        questions: quizQuestions.map((q) => q.question),
        correct_answers: quizQuestions.map((q) => q.expected_answer),
        student_answers: quizAnswers,
        time_taken_seconds: elapsedSeconds,
      });

      const payload = (response.data as Record<string, unknown> | undefined) || {};
      const score = Number(payload.score ?? 0);
      const total = Number(payload.total_questions ?? quizQuestions.length);
      const mistakes = Array.isArray(payload.mistakes) ? (payload.mistakes as string[]) : [];

      const mistakesText = mistakes.length
        ? mistakes.map((m) => `• ${m}`).join("\n")
        : "• Great job, no mistakes detected";

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 7).toString(),
          role: "assistant",
          content:
            `✅ **Quiz Submitted**\n\n` +
            `**Topic:** ${topic}\n` +
            `**Score:** ${score}/${total}\n\n` +
            `**Revision Focus**\n${mistakesText}`,
          timestamp: new Date(),
        },
      ]);

      setQuizQuestions([]);
      setQuizAnswers([]);
      setQuizStartedAt(null);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 7).toString(),
          role: "assistant",
          content: `❌ Quiz submission failed: ${error instanceof Error ? error.message : "Unknown error"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setQuizSubmitting(false);
    }
  };

  // UPGRADE: Download summary as PDF
  const downloadSummaryPDF = async () => {
    if (!fullSummary) return;
    
    try {
      // Get topic name for filename
      const topicName = context.topic || extractTopic(input) || 'learning_summary';
      const sanitizedTopic = topicName.replace(/[^a-z0-9_]/gi, '_').toLowerCase();
      
      // Use fetch directly to better handle response types
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/memory/summary/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          summary_text: fullSummary, 
          topic_name: sanitizedTopic 
        })
      });
      
      // Check if response is successful
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Check content type to see if it's PDF or error JSON
      const contentType = response.headers.get('content-type') || '';
      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error('Server returned empty response');
      }
      
      // If content type is JSON, it's an error response
      if (contentType.includes('application/json')) {
        const errorText = await blob.text();
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.message || 'PDF generation failed');
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${sanitizedTopic}_study_plan.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Add success message to chat
      const successMsg = `✅ **Your Complete Study Plan is Ready!**\n\n📥 Downloaded as: **${sanitizedTopic}_study_plan.pdf**\n\n🎯 Review this summary to track your learning progress and key insights. Happy studying!`;
      
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: successMsg,
          timestamp: new Date(),
        }
      ]);
    } catch (error) {
      console.error("PDF download failed:", error);
      
      // Show error message in chat
      const errorMsg = `❌ PDF download failed: ${error instanceof Error ? error.message : 'Unknown error'}. Attempting text download...`;
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: errorMsg,
          timestamp: new Date(),
        }
      ]);
      
      // Fallback: download as text
      try {
        const element = document.createElement('a');
        const topicName = context.topic || 'learning_summary';
        const sanitizedTopic = topicName.replace(/[^a-z0-9_]/gi, '_').toLowerCase();
        
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(fullSummary || ''));
        element.setAttribute('download', `${sanitizedTopic}_study_plan.txt`);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
        
        // Add fallback success message
        const fallbackMsg = `✅ Study plan downloaded as text file instead: **${sanitizedTopic}_study_plan.txt**`;
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content: fallbackMsg,
            timestamp: new Date(),
          }
        ]);
      } catch (textError) {
        console.error("Text download also failed:", textError);
      }
    }
  };

  if (!isStarted) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-zinc-950 text-white relative overflow-hidden">
        {/* Elegant background gradients */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-900/20 via-zinc-950 to-zinc-950"></div>
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(168,85,247,0.15)_0,rgba(0,0,0,0)_50%)]" />
        
        {/* Subtle grid pattern for depth */}
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-50"></div>

        {/* Floating decorative elements */}
        <div className="pointer-events-none absolute top-1/4 left-1/4 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-600/20 blur-[120px]" />
        <div className="pointer-events-none absolute bottom-1/4 right-1/4 h-64 w-64 translate-x-1/2 translate-y-1/2 rounded-full bg-indigo-600/20 blur-[120px]" />

        <div className="z-10 flex flex-col items-center max-w-4xl text-center px-6 animate-in fade-in zoom-in duration-1000 slide-in-from-bottom-8">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-sm font-medium text-purple-300 shadow-[0_0_20px_rgba(168,85,247,0.1)] backdrop-blur-md">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-purple-500"></span>
            </span>
            Metacognitive AI Engine
          </div>

          <div className="mb-8 rounded-full bg-purple-500/10 p-6 ring-1 ring-purple-500/30 shadow-[0_0_60px_rgba(168,85,247,0.25)] backdrop-blur-sm transition-transform duration-500 hover:scale-110">
            <MagicWandIcon className="h-16 w-16 text-purple-400" />
          </div>
          <h1 className="mb-2 pt-2 pb-6 pr-2 text-8xl md:text-9xl font-extrabold leading-tight tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-purple-300 via-indigo-400 to-purple-600 drop-shadow-lg">
            Cogni
          </h1>
          <p className="mb-12 text-xl md:text-2xl text-zinc-400 leading-relaxed max-w-2xl font-light">
            Your intelligent study companion. It remembers your struggles, adapts to your patterns, and helps you master complex topics.
          </p>
          <Button
            onClick={enterApp}
            onMouseDown={enterApp}
            onTouchStart={enterApp}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                enterApp();
              }
            }}
            className="group relative h-16 overflow-hidden rounded-full bg-purple-600 px-14 text-xl font-medium text-white shadow-[0_0_40px_rgba(168,85,247,0.4)] transition-all duration-300 hover:scale-105 hover:shadow-[0_0_60px_rgba(168,85,247,0.6)] active:scale-95"
          >
            <span className="relative z-10 flex items-center gap-2">
              Let&apos;s Study
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 transition-transform duration-300 group-hover:translate-x-1">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600 opacity-0 transition-opacity duration-300 group-hover:opacity-100"></div>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-zinc-900 text-white">
      <aside className="flex w-72 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 p-5">
        <div className="flex items-center gap-2">
          <MagicWandIcon className="h-10 w-10 text-purple-500" />
          <h1 className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text pb-3 pt-1 pr-1 text-4xl font-extrabold leading-tight tracking-tight text-transparent drop-shadow-md">Cogni</h1>
        </div>
        <Separator className="my-6 border-zinc-800" />
        <nav className="flex flex-col gap-3">
          {FEATURES.map((feature) => (
            <Button
              key={feature.id}
              variant="ghost"
              size="lg"
              onClick={() => setActiveFeature(feature.id)}
              className={`justify-start gap-4 text-base transition-all duration-200 ${
                activeFeature === feature.id
                  ? "bg-purple-500/15 font-medium text-purple-300 shadow-[inset_4px_0_0_0_rgba(168,85,247,0.8)] hover:bg-purple-500/25"
                  : "text-zinc-400 font-normal hover:bg-zinc-800 hover:text-zinc-200"
              }`}
            >
              <span className="scale-110">{feature.icon}</span>
              {feature.label}
            </Button>
          ))}
        </nav>
        <div className="mt-auto">
          <Separator className="my-5 border-zinc-800" />
          <div className="flex items-center justify-between text-[15px]">
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  backendState === "online"
                    ? "bg-green-500"
                    : backendState === "offline"
                    ? "bg-red-500"
                    : "bg-zinc-500"
                }`}
              />
              <span>
                {backendState === "checking"
                  ? "Checking..."
                  : backendState === "online"
                  ? "Online"
                  : "Offline"}
              </span>
            </div>
            {lastDemoMode !== null && (
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium tracking-wide ${
                  lastDemoMode === false
                    ? "bg-green-500/20 text-green-400"
                    : "bg-yellow-500/20 text-yellow-400"
                }`}
              >
                {lastDemoMode === false ? "Live Memory" : "Demo Mode"}
              </span>
            )}
          </div>
        </div>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/85 p-6 backdrop-blur-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-3xl font-semibold text-zinc-100 tracking-tight">
                {FEATURES.find((f) => f.id === activeFeature)?.label}
              </h2>
              <p className="text-base mt-1 text-zinc-400 font-light">
                {FEATURES.find((f) => f.id === activeFeature)?.description}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowUserIdInput(!showUserIdInput)}
                  className="text-xs text-zinc-400 border-zinc-600 hover:bg-zinc-800/50 h-8 px-3"
                >
                  👤 {userId}
                </Button>
                {showUserIdInput && (
                  <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="Enter user ID..."
                    className="h-8 px-3 text-sm rounded border border-zinc-600 bg-zinc-950 text-zinc-100 placeholder:text-zinc-500 focus:border-purple-500 focus:outline-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') setShowUserIdInput(false);
                    }}
                  />
                )}
              </div>
              <Button variant="ghost" size="icon" onClick={clearChat} className="hover:bg-red-500/10 hover:text-red-400 transition-colors">
                <TrashIcon className="h-5 w-5 scale-110" />
              </Button>
            </div>
          </div>
          <Separator className="my-4 border-zinc-800" />
          <div className="flex gap-6 items-end">
            {(activeFeature === "archaeology" ||
              activeFeature === "socratic" ||
              activeFeature === "resonance" ||
              activeFeature === "shadow") && 
              activeFeature !== "resonance" && (
              <div className="flex-1">
                <Label htmlFor="topic" className="text-[15px] font-medium text-zinc-300">Target Topic</Label>
                <Input
                  id="topic"
                  type="text"
                  value={context.topic || ""}
                  onChange={(e) => handleContextUpdate("topic", e.target.value)}
                  placeholder="e.g., recursion, dynamic programming..."
                  className="mt-3 h-12 text-base border-zinc-600 bg-zinc-950/50 shadow-inner backdrop-blur-sm transition-all hover:bg-zinc-900 focus-visible:border-purple-500 focus-visible:ring-2 focus-visible:ring-purple-500/40 focus-visible:shadow-[0_0_20px_rgba(168,85,247,0.25)] placeholder:text-zinc-600"
                />
              </div>
            )}

            {activeFeature === "resonance" && (
              <div className="flex-1">
                <Label htmlFor="topic" className="text-[15px] font-medium text-zinc-300">Target Topic</Label>
                <Input
                  id="topic"
                  type="text"
                  value={context.topic || ""}
                  onChange={(e) => handleContextUpdate("topic", e.target.value)}
                  placeholder="e.g., recursion, dynamic programming..."
                  className="mt-3 h-12 text-base border-zinc-600 bg-zinc-950/50 shadow-inner backdrop-blur-sm transition-all hover:bg-zinc-900 focus-visible:border-purple-500 focus-visible:ring-2 focus-visible:ring-purple-500/40 focus-visible:shadow-[0_0_20px_rgba(168,85,247,0.25)] placeholder:text-zinc-600"
                />
              </div>
            )}

            {activeFeature === "archaeology" && (
              <div className="w-56 pb-2">
                <Label htmlFor="confusion" className="text-[15px] font-medium text-zinc-300 mb-4 block">
                  Confusion Level: {context.confusion || 3}
                </Label>
                <input
                  id="confusion"
                  type="range"
                  min={1}
                  max={5}
                  step={1}
                  value={context.confusion || 3}
                  onChange={(e) => handleContextUpdate("confusion", Number(e.target.value))}
                  className="mt-2 w-full accent-purple-500"
                />
              </div>
            )}

            {activeFeature === "contagion" && (
              <div className="flex-1">
                <Label htmlFor="topic" className="text-[15px] font-medium text-zinc-300">Topic to Learn</Label>
                <Input
                  id="topic"
                  type="text"
                  value={context.topic || ""}
                  onChange={(e) => handleContextUpdate("topic", e.target.value)}
                  placeholder="e.g., recursion, dynamic programming, sorting..."
                  className="mt-3 h-12 text-base border-zinc-600 bg-zinc-950/50 shadow-inner backdrop-blur-sm transition-all hover:bg-zinc-900 focus-visible:border-purple-500 focus-visible:ring-2 focus-visible:ring-purple-500/40 focus-visible:shadow-[0_0_20px_rgba(168,85,247,0.25)] placeholder:text-zinc-600"
                />
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 scroll-smooth overflow-y-auto p-6 md:p-10">
          <div className="space-y-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onFeedback={submitMessageFeedback}
                feedbackRating={feedbackByMessageId[msg.id]}
                feedbackLoading={!!feedbackLoadingByMessageId[msg.id]}
              />
            ))}
            {loading && <LoadingBubble />}
            <div ref={messagesEndRef} />
          </div>
          {messages.length <= 1 && !loading && (
            <div className="mt-12">
              <h3 className="mb-6 text-center text-[15px] font-medium tracking-wide text-zinc-400 uppercase">
                Suggestions
              </h3>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {QUICK_PROMPTS[activeFeature].map((prompt, i) => (
                  <Card
                    key={i}
                    onClick={() => handleQuickPrompt(prompt)}
                    className="group cursor-pointer border-zinc-700/50 bg-zinc-900/60 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-purple-500/60 hover:bg-purple-500/10 hover:shadow-[0_8px_30px_-4px_rgba(168,85,247,0.25)] active:translate-y-0 active:scale-95"
                  >
                    <CardContent className="p-4">
                      <p className="text-[15px] leading-relaxed text-zinc-300">{prompt}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
          {activeFeature === "contagion" ? (
            <div className="mx-auto flex max-w-4xl justify-center gap-4 flex-wrap mt-8">
              <Button
                onClick={handleSend}
                disabled={loading}
                className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <>
                    <CubeIcon className="mr-2 h-5 w-5" />
                    Predict My Next Challenge
                  </>
                )}
              </Button>
            </div>
          ) : activeFeature === "resonance" ? (
            <div className="mx-auto flex max-w-4xl justify-center">
              <Button
                onClick={handleSend}
                disabled={loading}
                className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <>
                    <StarIcon className="mr-2 h-5 w-5" />
                    Show Hidden Connections
                  </>
                )}
              </Button>
            </div>
          ) : activeFeature === "memory" ? (
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
              <div className="flex justify-center gap-3 flex-wrap">
                <Button
                  onClick={showUserProgress}
                  disabled={progressLoading}
                  className="h-14 rounded-full bg-emerald-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-emerald-500 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] active:scale-95"
                >
                  {progressLoading ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                  ) : (
                    <>
                      <MagicWandIcon className="mr-2 h-5 w-5" />
                      Show Progress
                    </>
                  )}
                </Button>
                <Button
                  onClick={generateSummary}
                  disabled={summaryLoading || messages.length <= 1}
                  className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95"
                >
                  {summaryLoading ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                  ) : (
                    <>
                      <MagicWandIcon className="mr-2 h-5 w-5" />
                      Generate Summary
                    </>
                  )}
                </Button>
                {fullSummary && (
                  <Button
                    onClick={downloadSummaryPDF}
                    className="h-14 rounded-full bg-indigo-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-indigo-500 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] active:scale-95"
                  >
                    📥 Download PDF
                  </Button>
                )}
              </div>

              <Card className="border-zinc-700/60 bg-zinc-900/70 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-zinc-100">Quick Quiz</CardTitle>
                  <CardDescription className="text-zinc-400">
                    Generate a 3-question revision quiz, submit answers, and store rich learning memory.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-3 flex-wrap items-end">
                    <div className="flex-1 min-w-[220px]">
                      <Label htmlFor="quiz-topic" className="text-zinc-300">Quiz Topic</Label>
                      <Input
                        id="quiz-topic"
                        value={quizTopic}
                        onChange={(e) => setQuizTopic(e.target.value)}
                        placeholder="e.g., recursion, graph traversal"
                        className="mt-2 border-zinc-600 bg-zinc-950/60"
                      />
                    </div>
                    <Button
                      onClick={generateQuiz}
                      disabled={quizLoading || !quizTopic.trim()}
                      className="h-11 rounded-lg bg-cyan-600 px-6 text-white hover:bg-cyan-500"
                    >
                      {quizLoading ? "Generating..." : "Generate Quiz"}
                    </Button>
                  </div>

                  {quizQuestions.length > 0 && (
                    <div className="space-y-4 pt-2">
                      {quizQuestions.map((q, idx) => (
                        <div key={q.id} className="rounded-lg border border-zinc-700/70 bg-zinc-950/40 p-4">
                          <p className="mb-3 text-sm font-semibold text-zinc-200">
                            <span className="text-cyan-300">Q{idx + 1}.</span> {q.question}
                          </p>
                          <div className="space-y-2">
                            {[
                              q.expected_answer,
                              "I don't know",
                              "Different answer",
                              "Need more context"
                            ].map((option, optIdx) => (
                              <button
                                key={optIdx}
                                onClick={() => {
                                  const next = [...quizAnswers];
                                  next[idx] = option;
                                  setQuizAnswers(next);
                                }}
                                className={`w-full p-3 text-left rounded-lg border-2 transition-all ${
                                  quizAnswers[idx] === option
                                    ? 'border-cyan-400 bg-cyan-500/20 text-cyan-200 font-semibold'
                                    : 'border-zinc-600 bg-zinc-900/40 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-900/60'
                                }`}
                              >
                                • {option}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}

                      <Button
                        onClick={submitQuiz}
                        disabled={quizSubmitting || quizAnswers.some((a) => !a)}
                        className="h-11 rounded-lg bg-emerald-600 px-6 text-white hover:bg-emerald-500"
                      >
                        {quizSubmitting ? "Submitting..." : "Submit Quiz"}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="relative mx-auto flex max-w-5xl items-center rounded-full border border-zinc-600/80 bg-zinc-900/70 shadow-lg backdrop-blur-md transition-all focus-within:border-purple-500 focus-within:bg-zinc-900 focus-within:ring-4 focus-within:ring-purple-500/20 focus-within:shadow-[0_0_30px_rgba(168,85,247,0.15)] hover:border-zinc-500">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getPlaceholder(activeFeature)}
                className="h-16 w-full border-0 bg-transparent px-8 pr-16 text-[17px] placeholder:text-zinc-500 focus-visible:ring-0 shadow-none"
                disabled={loading}
              />
              <Button
                size="icon"
                className="absolute right-2 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full bg-purple-600 text-white shadow-md transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95 disabled:opacity-40 disabled:hover:scale-100 disabled:hover:shadow-md"
                onClick={handleSend}
                disabled={loading}
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6 ml-0.5">
                    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                  </svg>
                )}
              </Button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  onFeedback,
  feedbackRating,
  feedbackLoading,
}: {
  message: Message;
  onFeedback?: (message: Message, rating: number) => Promise<void>;
  feedbackRating?: number;
  feedbackLoading?: boolean;
}) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const [copied, setCopied] = useState(false);
  const hiddenMetadataKeys = new Set(["response_id", "user_query"]);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isSystem) {
    return (
      <div className="my-8 text-center text-base font-medium text-zinc-500">
        {message.content.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    );
  }

  return (
    <div
      className={`group message-enter flex items-end gap-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-zinc-600 bg-zinc-800 text-purple-400 shadow-sm">
          {FEATURES.find((f) => f.id === message.feature)?.icon}
        </div>
      )}
      <Card
        className={`relative max-w-[85%] border-none shadow-md transition-all duration-300 sm:max-w-2xl ${
          isUser
            ? "rounded-2xl rounded-br-sm bg-purple-600 text-white"
            : "rounded-2xl rounded-bl-sm bg-zinc-800/90 text-zinc-100 backdrop-blur-sm"
        }`}
      >
        {!isUser && (
          <button
            onClick={handleCopy}
            className="absolute right-3 top-3 rounded-md bg-zinc-800/80 p-2 text-zinc-400 opacity-0 backdrop-blur-sm transition-all hover:scale-105 hover:bg-zinc-700 hover:text-zinc-100 active:scale-95 group-hover:opacity-100"
            title="Copy to clipboard"
          >
            {copied ? (
              <CheckIcon className="h-4 w-4 text-green-400" />
            ) : (
              <CopyIcon className="h-4 w-4" />
            )}
          </button>
        )}
        <CardContent className="px-6 py-5 text-[17px]">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={`leading-relaxed tracking-wide ${i > 0 ? "mt-4" : ""}`}>
              {renderRichLine(line, isUser)}
            </p>
          ))}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              {Object.entries(message.metadata)
                .filter(([key]) => !hiddenMetadataKeys.has(key))
                .map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center gap-1.5 rounded-full bg-zinc-700/50 px-3 py-1"
                  >
                    <span className="font-semibold capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>
                    <span>{String(value)}</span>
                  </div>
                ))}
            </div>
          )}
          {!isUser && !isSystem && onFeedback && (
            <div className="mt-5 flex items-center gap-2">
              <span className="text-xs text-zinc-400">Rate:</span>
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  disabled={feedbackLoading}
                  onClick={() => void onFeedback(message, value)}
                  className={`rounded-md px-2 py-1 text-xs transition-colors ${
                    feedbackRating === value
                      ? "bg-purple-600 text-white"
                      : "bg-zinc-700/60 text-zinc-300 hover:bg-zinc-600"
                  } ${feedbackLoading ? "cursor-not-allowed opacity-60" : ""}`}
                >
                  {value}
                </button>
              ))}
              {feedbackRating !== undefined && (
                <span className="text-xs text-zinc-400">Saved</span>
              )}
            </div>
          )}
        </CardContent>
        <CardFooter className="p-2 text-xs text-zinc-400">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </CardFooter>
      </Card>
      {isUser && (
        <div className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-[13px] font-bold text-purple-300 ring-1 ring-purple-500/50 shadow-sm">
          ST
        </div>
      )}
    </div>
  );
}

function LoadingBubble() {
  return (
    <div className="message-enter flex items-end gap-4">
      <div className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-zinc-600 bg-zinc-800 text-purple-400 shadow-sm">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
      </div>
      <Card className="max-w-[85%] rounded-2xl rounded-bl-sm border-none bg-zinc-800/90 shadow-md backdrop-blur-sm sm:max-w-2xl">
        <CardContent className="px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-purple-400" />
            <div className="h-2 w-2 animate-pulse rounded-full bg-purple-400" />
            <div className="h-2 w-2 animate-pulse rounded-full bg-purple-400" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function renderRichLine(line: string, isUser: boolean = false): React.ReactNode {
  const parts = line.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className={`font-semibold ${isUser ? "text-purple-200" : "text-purple-400"}`}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}

function formatResponse(
  apiResponse: APIShape,
  feature: FeatureMode
): { content: string; metadata: Record<string, unknown> } {
  const apiData = (apiResponse.data as GenericRecord | undefined) || {};
  const data = (apiData.result as GenericRecord | undefined) || apiData;
  const metadata: Record<string, unknown> = {
    demo_mode: apiResponse.demo_mode,
  };

  const responseId = apiData.response_id ?? data.response_id;
  if (typeof responseId === "string" && responseId.trim()) {
    metadata.response_id = responseId;
  }

  const systemConfidence = apiData.confidence ?? data.confidence;
  if (systemConfidence !== undefined && systemConfidence !== null) {
    metadata.confidence = systemConfidence;
  }

  switch (feature) {
    case "archaeology": {
      const similarMoments = Number(data.similar_moments ?? 0);
      metadata.similar_moments = similarMoments;

      let content = "";
      if (similarMoments > 0) {
        content = `Found **${similarMoments}** similar moments in your history.\n\n`;
      } else {
        content = `No similar moments found yet. Keep studying to build your learning profile!\n\n`;
      }

      if (data.recommendation) {
        content += `**Recommendation**: ${String(data.recommendation)}\n\n`;
      }

      if (data.adaptive_explanation) {
        content += `**🧠 Explanation (Adaptive)**\n\n${String(data.adaptive_explanation)}`;
        if (data.explanation_audience) {
          metadata.explanation_audience = data.explanation_audience;
        }
      }

      return { content: content.trim(), metadata };
    }

    case "socratic": {
      // Handle both initial questions (/ask) and follow-up questions (/reflect)
      const question = String(data.question || data.follow_up_question || "Let's explore this together. What's the simplest case you can think of?");
      
      // If this is a reflection response, include the response analysis
      let content: string = question;
      if (data.response_analysis) {
        content = `**Your response**: _${String(data.user_response)}_\n\n**Analysis**: ${String(data.response_analysis)}\n\n**Next question**: ${question}`;
      }
      
      return {
        content,
        metadata: {
          ...metadata,
          resolved_count: (data.past_history as GenericRecord | undefined)
            ?.resolved_count,
          unresolved_count: (data.past_history as GenericRecord | undefined)
            ?.unresolved_count,
          is_follow_up: !!data.follow_up_question,
        },
      };
    }

    case "shadow": {
      const evidence = Array.isArray(data.evidence)
        ? (data.evidence as string[])
        : [];
      return {
        content: `**Prediction**: ${String(
          data.prediction ?? "No prediction available yet."
        )}\n\n**Evidence**:\n${
          evidence.map((e) => `• ${e}`).join("\n") ||
          "Based on your learning patterns"
        }`,
        metadata,
      };
    }

    case "resonance": {
      const hiddenConnections = Array.isArray(data.hidden_connections)
        ? (data.hidden_connections as GenericRecord[])
        : [];
      
      let connectionContent = "";
      
      if (hiddenConnections.length > 0) {
        connectionContent = hiddenConnections
          .map(
            (c, idx) => {
              const num = idx + 1;
              const topicName = String(c.topic ?? "topic").replace(/_/g, " ");
              const strength = Math.round(Number(c.strength ?? 0) * 100);
              const howConnects = String(c.connection ?? c.reason ?? "Related concept");
              const whyMatters = String(c.depth ?? "Deepens conceptual understanding");
              
              return `**${num}. ${topicName}** (${strength}% connection strength)\n\n**How it connects:** ${howConnects}\n\n**Why it matters:** ${whyMatters}`;
            }
          )
          .join("\n\n---\n\n");
      } else {
        connectionContent = "No hidden connections found. Try a different topic.";
      }
      
      const insightText = String(data.insight ?? "").trim();
      const finalContent = `**Hidden Connections for "${String(
        data.topic || "your topic"
      )}"**:\n\n${connectionContent}${
        insightText ? `\n\n---\n\n**Key Insight:** ${insightText}` : ""
      }`;
      
      return {
        content: finalContent,
        metadata: { ...metadata, connection_count: hiddenConnections.length },
      };
    }

    case "contagion": {
      metadata.community_size = data.community_size;
      metadata.success_rate = data.success_rate;
      const strategies = Array.isArray(data.additional_strategies)
        ? (data.additional_strategies as GenericRecord[])
        : [];
      
      // UPGRADE: Prioritize learning_plan if available
      const learningPlan = String(data.learning_plan ?? "").trim();
      
      if (learningPlan) {
        // Get topic name for motivational context
        const topicName = String(data.error_pattern ?? "this topic").replace(/_/g, " ");
        const communitySize = Number(data.community_size ?? 0);
        
        // UPGRADE: Add motivational preamble based on community insights
        let motivationalPreamble = "";
        if (communitySize > 0) {
          motivationalPreamble = `📚 **Many students and professionals at your level have struggled with ${topicName}.** Based on what worked for ${communitySize} peers with similar learning patterns, here's your personalized path forward:\n\n`;
        } else {
          motivationalPreamble = `📚 **You're tackling ${topicName} — a topic many learners find challenging.** Here's a personalized roadmap to help you master it:\n\n`;
        }
        
        // Build complete content with motivation + plan + strategy
        let content = `**Your Personalized Learning Roadmap for "${topicName}"**\n\n${motivationalPreamble}${learningPlan}`;
        
        // Optionally add top strategy reference (without percentages)
        const topStrat = String(data.top_strategy ?? "").trim();
        if (topStrat && topStrat.length > 0) {
          content += `\n\n---\n\n**🎯 Key Strategy to Focus On**\n\n${topStrat}`;
        }
        
        // Add privacy note (optional)
        const privacyNote = String(data.privacy_note ?? "").trim();
        if (privacyNote) {
          content += `\n\n*${privacyNote}*`;
        }
        
        return { content, metadata };
      }
      
      // Fallback: Legacy display (for backward compatibility)
      return {
        content: `**Community Insights**:\n\n**Top Strategy**: ${String(
          data.top_strategy ?? "unknown"
        ).replace(/_/g, " ")}\nSuccess Rate: ${Math.round(
          Number(data.success_rate || 0) * 100
        )}%\nBased on ${
          Number(data.community_size || 0)
        } students with similar patterns\n\n**More Strategies**:\n${
          strategies
            .map(
              (s) =>
                `• ${String(s.strategy ?? "unknown")} (${Math.round(
                  Number(s.success_rate ?? 0) * 100
                )}%)`
            )
            .join("\n") || "No additional strategies available."
        }\n\n${String(data.privacy_note || "")}`,
        metadata,
      };
    }

    case "memory": {
      const memories = Array.isArray(apiData.memories)
        ? (apiData.memories as GenericRecord[])
        : [];
      if (memories.length === 0) {
        return {
          content:
            "No memories found yet. Start studying to build your cognitive profile!",
          metadata,
        };
      }
      return {
        content: `**Your Memory Profile** (${
          memories.length
        } entries):\n\n${memories
          .slice(0, 5)
          .map((m) => {
            const ctx = (m.context as GenericRecord | undefined) || {};
            const topic = String(ctx.topic || ctx.concept || "Untitled");
            const confidence = Math.round(Number(m.confidence || 0.8) * 100);
            return `• **${topic}**\n  ${String(
              m.content || "No content"
            )}\n  Confidence: ${confidence}%\n`;
          })
          .join("\n")}${
          memories.length > 5 ? `\n...and ${memories.length - 5} more` : ""
        }`,
        metadata: { ...metadata, memory_count: memories.length },
      };
    }

    default: {
      return { content: "Select a feature to get started!", metadata };
    }
  }
}

function extractTopic(message: string): string {
  const keywords = [
    "recursion",
    "dynamic programming",
    "binary tree",
    "graph",
    "sorting",
    "algorithm",
    "function",
    "loop",
  ];
  const lower = message.toLowerCase();
  for (const kw of keywords) {
    if (lower.includes(kw)) return kw;
  }
  return "recursion";
}

function getPlaceholder(feature: FeatureMode): string {
  const placeholders: Record<FeatureMode, string> = {
    archaeology:
      "Describe what you're confused about (e.g., 'I don't get recursion base cases')...",
    socratic: "Share your current understanding or misconception...",
    shadow: "Ask about upcoming challenges or request a prediction...",
    resonance: "Enter a topic to find hidden conceptual connections...",
    contagion:
      "What topic do you want to learn from peer approaches? (e.g., machine learning, web development)...",
    memory: "Memory view is read-only. Select another feature to chat.",
  };
  return placeholders[feature];
}
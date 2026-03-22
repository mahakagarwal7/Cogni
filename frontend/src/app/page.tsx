
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
import {
  MemoryTimeline,
  type TimelineEntry,
} from "@/components/memory/MemoryTimeline";
import {
  ConfidenceGraph,
  type ConfidenceSeries,
} from "@/components/memory/ConfidenceGraph";
import {
  CognitiveSummary,
  type LearningProfile,
} from "@/components/memory/CognitiveSummary";

type FeatureMode =
  | "archaeology"
  | "socratic"
  | "shadow"
  | "resonance"
  | "contagion"
  | "memory"
  | "graphs";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  feature?: FeatureMode;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

type ShadowPredictionCard = {
  title: string;
  description: string;
  trigger_condition: string;
  suggested_micro_action: string;
  difficulty?: string;
  confidence?: number;
};

type GenericRecord = Record<string, unknown>;
type APIShape = {
  data?: unknown;
  demo_mode?: boolean;
};

type QuizQuestion = {
  id: number;
  question: string;
  expected_answer: string;
  options: string[];
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
  {
    id: "graphs",
    label: "Graphs",
    icon: <CubeIcon className="h-5 w-5" />,
    description: "Visualize student performance trends",
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
  graphs: [
    "Refresh performance graphs",
    "Show confidence trends by topic",
    "Analyze my learning performance",
  ],
};
export default function ChatPage() {
  // Intro screen state
  const [isStarted, setIsStarted] = useState<boolean | null>(null);
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
  const [memoryVizLoading, setMemoryVizLoading] = useState(false);
  const [memoryVizError, setMemoryVizError] = useState<string | null>(null);
  const [memoryTimelineEntries, setMemoryTimelineEntries] = useState<TimelineEntry[]>([]);
  const [memoryConfidenceSeries, setMemoryConfidenceSeries] = useState<ConfidenceSeries[]>([]);
  const [memorySummaryText, setMemorySummaryText] = useState("");
  const [memoryLearningProfile, setMemoryLearningProfile] = useState<LearningProfile | null>(null);
  const [memoryPerformanceOverview, setMemoryPerformanceOverview] = useState<Record<string, unknown> | null>(null);
  const [memoryLastUpdatedAt, setMemoryLastUpdatedAt] = useState<string | null>(null);
  const memoryRefreshRequestRef = useRef(0);
  // UPGRADE: User session persisted to localStorage
  const [userId, setUserIdState] = useState("student");
  const [showUserIdInput, setShowUserIdInput] = useState(false);
  const [dismissedGuides, setDismissedGuides] = useState<Partial<Record<FeatureMode, boolean>>>({});
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
    const startedFromParam = params.get("start") === "1";
    setIsStarted(startedFromParam);
    if (!startedFromParam) {
      localStorage.removeItem("cogni_started");
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

  const refreshMemoryVisualization = async (forceRefresh: boolean = false) => {
    const requestId = memoryRefreshRequestRef.current + 1;
    memoryRefreshRequestRef.current = requestId;

    setMemoryVizError(null);
    setMemoryVizLoading(true);

    try {
      const [timelineRes, confidenceRes, summaryRes] = await Promise.all([
        api.getMemoryTimeline(userId, 120),
        api.getMemoryConfidence(userId, 8, 300),
        api.getMemoryCognitiveSummary(userId, forceRefresh),
      ]);

      if (requestId !== memoryRefreshRequestRef.current) {
        return;
      }

      const timelinePayload = (timelineRes.data as Record<string, unknown> | undefined) || {};
      const timelineRaw = Array.isArray(timelinePayload.timeline)
        ? (timelinePayload.timeline as Record<string, unknown>[])
        : [];
      const parsedTimeline: TimelineEntry[] = timelineRaw.map((row, idx) => ({
        session_id: Number(row.session_id ?? idx + 1),
        timestamp: String(row.timestamp ?? new Date().toISOString()),
        type: String(row.type ?? "study_session"),
        source: String(row.source ?? "memory"),
        topic: String(row.topic ?? "general"),
        confidence: Number(row.confidence ?? 0.65),
        content_preview: String(row.content_preview ?? ""),
      }));

      const confidencePayload = (confidenceRes.data as Record<string, unknown> | undefined) || {};
      const confidenceRaw = Array.isArray(confidencePayload.topic_series)
        ? (confidencePayload.topic_series as Record<string, unknown>[])
        : [];
      const parsedSeries: ConfidenceSeries[] = confidenceRaw.map((row) => {
        const pointRows = Array.isArray(row.points) ? (row.points as Record<string, unknown>[]) : [];
        return {
          topic: String(row.topic ?? "general"),
          sessions_studied: Number(row.sessions_studied ?? pointRows.length),
          current_confidence: Number(row.current_confidence ?? 0.65),
          improvement: Number(row.improvement ?? 0),
          avg_quiz_score_ratio:
            typeof row.avg_quiz_score_ratio === "number"
              ? Number(row.avg_quiz_score_ratio)
              : null,
          mastery_score:
            typeof row.mastery_score === "number"
              ? Number(row.mastery_score)
              : undefined,
          weak_signal_count:
            typeof row.weak_signal_count === "number"
              ? Number(row.weak_signal_count)
              : undefined,
          performance_label:
            typeof row.performance_label === "string"
              ? String(row.performance_label)
              : undefined,
          points: pointRows.map((point, idx) => ({
            session_index: Number(point.session_index ?? idx + 1),
            timestamp: String(point.timestamp ?? new Date().toISOString()),
            confidence: Number(point.confidence ?? 0.65),
          })),
        };
      });

      const summaryPayload = (summaryRes.data as Record<string, unknown> | undefined) || {};
      const learningProfileRaw = summaryPayload.learning_profile as Record<string, unknown> | undefined;
      const learningProfile: LearningProfile | null = learningProfileRaw
        ? {
            strengths: Array.isArray(learningProfileRaw.strengths)
              ? (learningProfileRaw.strengths as string[])
              : [],
            weaknesses: Array.isArray(learningProfileRaw.weaknesses)
              ? (learningProfileRaw.weaknesses as string[])
              : [],
            interests: Array.isArray(learningProfileRaw.interests)
              ? (learningProfileRaw.interests as string[])
              : [],
            patterns: Array.isArray(learningProfileRaw.patterns)
              ? (learningProfileRaw.patterns as string[])
              : [],
            total_sessions: Number(learningProfileRaw.total_sessions ?? 0),
            topics_studied: Number(learningProfileRaw.topics_studied ?? 0),
            average_confidence: Number(learningProfileRaw.average_confidence ?? 0),
          }
        : null;

      setMemoryTimelineEntries(parsedTimeline);
      setMemoryConfidenceSeries(parsedSeries);
      setMemoryPerformanceOverview(
        (confidencePayload.performance_overview as Record<string, unknown> | undefined) || null
      );
      setMemorySummaryText(String(summaryPayload.summary ?? ""));
      setMemoryLearningProfile(learningProfile);
      setMemoryLastUpdatedAt(new Date().toISOString());

      if (
        typeof timelineRes.demo_mode === "boolean" ||
        typeof confidenceRes.demo_mode === "boolean" ||
        typeof summaryRes.demo_mode === "boolean"
      ) {
        setLastDemoMode(
          timelineRes.demo_mode ?? confidenceRes.demo_mode ?? summaryRes.demo_mode ?? null
        );
      }
    } catch (error) {
      setMemoryVizError(
        `Could not refresh live memory visualization: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setMemoryVizLoading(false);
    }
  };

  useEffect(() => {
    const analyticsView = activeFeature === "graphs" || activeFeature === "memory";
    if (!analyticsView || memoryVizLoading) {
      return;
    }

    const hasAnyData =
      memoryTimelineEntries.length > 0 ||
      memoryConfidenceSeries.length > 0 ||
      !!memorySummaryText;

    if (!hasAnyData) {
      void refreshMemoryVisualization(true);
    }
  }, [
    activeFeature,
    userId,
    memoryVizLoading,
    memoryTimelineEntries.length,
    memoryConfidenceSeries.length,
    memorySummaryText,
  ]);

  const handleSend = async (overrideInput?: string) => {
    const activeInput = (overrideInput ?? input).trim();
    // Resonance and Contagion use header topic field, not main input
    const requiresInput = [
      "archaeology",
      "socratic",
    ].includes(activeFeature);
    
    // For contagion, check context.topic instead
    if (activeFeature === "contagion") {
      if (!context.topic?.trim()) return;
    } else if (requiresInput && !activeInput) {
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

    const requestQuery = activeInput || context.topic || "general";

    if (requiresInput) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: activeInput,
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
          const topic = context.topic || extractTopic(activeInput);
          const confusion = context.confusion || 3;
          response = await api.getArchaeology(topic, confusion, userId);
          break;
        }

        case "socratic": {
          const concept = context.topic || extractTopic(activeInput);
          const confusion = context.confusion || 3;
          
          // Check if the previous message was a Socratic question (ending with ?)
          // If so, treat the current input as a response and reflect instead of asking
          const prevMessage = messages[messages.length - 1];
          const prevMetadata = (prevMessage?.metadata || {}) as GenericRecord;
          const previousQuestion =
            typeof prevMetadata.current_question === "string" && prevMetadata.current_question.trim()
              ? prevMetadata.current_question
              : prevMessage?.content;
          const shouldReflect =
            prevMessage?.role === "assistant" &&
            typeof previousQuestion === "string" &&
            previousQuestion.trim().endsWith("?");
          
          if (shouldReflect && previousQuestion) {
            // User is responding to a previous Socratic question - reflect on the response
            response = await api.reflectSocratic(
              concept,
              activeInput,
              previousQuestion,
              userId,
              confusion
            );
          } else {
            // First question or starting a new line of thinking
            response = await api.askSocratic(concept, activeInput, userId, confusion);
          }
          break;
        }

        case "shadow": {
          const shadowTopic = context.topic || extractTopic(activeInput);
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
          const contagionTopic = context.topic || activeInput;
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
          await refreshMemoryVisualization(true);
          response = {
            data: {
              result: {
                recommendation:
                  "Memory and confidence analytics refreshed from Hindsight. Check Graphs for updated student analysis.",
              },
            },
          };
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
    if (activeFeature === "shadow") {
      setContext((prev) => ({ ...prev, topic: extractTopic(prompt) }));
      void handleShadowPredict();
      return;
    }
    if (activeFeature === "graphs" || activeFeature === "memory") {
      void refreshMemoryVisualization(true);
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

  const handleSocraticHint = async () => {
    if (loading || activeFeature !== "socratic") return;

    const latestQuestion = getLatestSocraticQuestion(messages);
    if (!latestQuestion) return;

    const concept = context.topic || extractTopic(latestQuestion);
    const confusion = context.confusion || 3;

    setLoading(true);
    try {
      const response = await api.getSocraticHint(
        concept,
        latestQuestion,
        userId,
        confusion,
        input.trim()
      );

      const payload = (response.data as GenericRecord | undefined) || {};
      const result = (payload.result as GenericRecord | undefined) || payload;
      const hint = String(result.hint || "Start with one concrete example before answering the question.");

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content: `**Hint**: ${hint}`,
          feature: "socratic",
          timestamp: new Date(),
          metadata: {
            current_question: latestQuestion,
            is_hint: true,
            user_query: latestQuestion,
          },
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content: "Could not fetch a hint right now. Try answering with what you know so far.",
          feature: "socratic",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleShadowPredict = async () => {
    const topic = (context.topic || input).trim();
    if (!topic) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 8).toString(),
          role: "assistant",
          content: "Set a target topic first, then click **Predict My Next Struggles**.",
          feature: "shadow",
          timestamp: new Date(),
        },
      ]);
      return;
    }
    await handleSend(topic);
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

      const prettyLabel = (value: string) => value.replace(/_/g, " ");

      const studiedTopics = Array.isArray(progress.studied_topics)
        ? (progress.studied_topics as string[])
        : [];
      const recentTopics = Array.isArray(progress.recent_topics)
        ? (progress.recent_topics as string[])
        : [];
      const highConfidenceTopics = Array.isArray(progress.high_confidence_topics)
        ? (progress.high_confidence_topics as string[])
        : [];
      const weakTopics = Array.isArray(progress.weak_topics)
        ? (progress.weak_topics as string[])
        : [];
      const pastMistakes = Array.isArray(progress.past_mistakes)
        ? (progress.past_mistakes as string[])
        : [];
      const improvementScore = Number(progress.improvement_score ?? 0);
      const quizAttempts = Number(progress.quiz_attempts ?? 0);
      const avgQuizScoreRatio = Number(progress.avg_quiz_score_ratio ?? 0);
      const quizImprovementScore = Number(progress.quiz_improvement_score ?? 0);
      const studySessionsCount = Number(progress.study_sessions_count ?? 0);
      const topicLabel = currentTopic ? currentTopic.replace(/_/g, " ") : "Overall";

      const studiedTopicsText = studiedTopics.length
        ? studiedTopics.map((topic) => `• ${prettyLabel(topic)}`).join("\n")
        : "• No topics studied yet";
      
      const recentTopicsText = recentTopics.length
        ? recentTopics.map((topic) => `• ${prettyLabel(topic)}`).join("\n")
        : "• Get started by exploring a topic";
      
      const masteredTopicsText = highConfidenceTopics.length
        ? highConfidenceTopics.map((topic) => `✓ ${prettyLabel(topic)}`).join("\n")
        : "• Keep studying to master topics";

      const weakTopicsText = weakTopics.length
        ? weakTopics.map((topic) => `• ${prettyLabel(topic)}`).join("\n")
        : "• No weak topic trend detected yet";

      const pastMistakesText = pastMistakes.length
        ? pastMistakes.map((item) => `• ${prettyLabel(item)}`).join("\n")
        : "• No repeated mistakes detected";

      const quizScorePercent = quizAttempts > 0
        ? `${(Math.max(0, Math.min(1, avgQuizScoreRatio)) * 100).toFixed(1)}%`
        : "N/A";

      const wowMessage = `📊 **Your Learning Journey (${topicLabel})**\n\n**What You've Studied** (${studySessionsCount} sessions)\n${studiedTopicsText}\n\n**Recently Explored**\n${recentTopicsText}\n\n**Topics You're Mastering** ⭐\n${masteredTopicsText}\n\n**Weak Topics to Revisit**\n${weakTopicsText}\n\n**Progress Trend**\n${improvementScore > 0 ? "📈 Improving: +" : improvementScore < 0 ? "📉 Declining: " : "→ Steady: "}${Math.abs(improvementScore).toFixed(1)}%\n\n**Quiz Performance (Hindsight)**\n• Attempts tracked: ${quizAttempts}\n• Average score: ${quizScorePercent}\n• Quiz trend: ${quizImprovementScore > 0 ? `📈 +${quizImprovementScore.toFixed(1)}%` : quizImprovementScore < 0 ? `📉 ${quizImprovementScore.toFixed(1)}%` : "→ Steady"}\n\n**Focus Areas**\n${pastMistakesText}`;

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
          const optionsRaw = Array.isArray(record.options)
            ? (record.options as unknown[]).map((opt) => String(opt ?? "").trim()).filter(Boolean)
            : [];
          const expectedAnswer = String(record.expected_answer ?? "");
          const options = optionsRaw.length
            ? optionsRaw
            : [
                expectedAnswer,
                `A common misconception about ${topic}`,
                `A partially correct statement about ${topic}`,
                `A related but different concept from ${topic}`,
              ];
          return {
            id: Number(record.id ?? idx + 1),
            question: String(record.question ?? ""),
            expected_answer: expectedAnswer,
            options: options.slice(0, 4),
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

  if (isStarted === null) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#09090b] text-zinc-300">
        <div className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm backdrop-blur-sm">
          Preparing your workspace...
        </div>
      </div>
    );
  }

  if (!isStarted) {
    return (
      <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#030305] text-zinc-100 font-sans selection:bg-purple-500/30">
        {/* Animated Background Gradients & Grid */}
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]" />
        
        {/* Glowing Orbs */}
        <div className="pointer-events-none absolute top-[10%] left-[20%] h-[400px] w-[400px] rounded-full bg-purple-600/10 blur-[120px] mix-blend-screen" />
        <div className="pointer-events-none absolute bottom-[10%] right-[20%] h-[400px] w-[400px] rounded-full bg-indigo-600/10 blur-[120px] mix-blend-screen" />

        <div className="z-10 flex w-full max-w-5xl flex-col items-center px-6 text-center animate-in fade-in zoom-in-95 duration-700 slide-in-from-bottom-8">
          
          {/* Top Premium Badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-purple-300 backdrop-blur-md transition-all hover:bg-purple-500/20 cursor-default shadow-[0_0_20px_rgba(168,85,247,0.1)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-purple-500"></span>
            </span>
            MetaCognitive Intelligence Engine 
          </div>

          {/* Logo Container with Glow */}
          <div className="relative mb-8 group">
            <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 opacity-40 blur-lg transition duration-500 group-hover:opacity-75"></div>
            <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-white/10 bg-[#09090b] shadow-2xl transition-transform duration-300 group-hover:scale-105">
               <img
                src="/cogni-logo.svg"
                alt="Cogni logo"
                className="h-16 w-16 rounded-full object-contain"
              />
            </div>
          </div>

          {/* Hero Typography */}
          <h1 className="mb-6 px-2 text-6xl font-extrabold leading-tight tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-zinc-200 to-zinc-500 md:text-8xl drop-shadow-sm">
         Learn With<span className="bg-gradient-to-br from-purple-400 to-indigo-500 bg-clip-text text-transparent"> Cogni</span>
          </h1>

          <p className="mb-12 max-w-2xl text-lg leading-relaxed text-zinc-400 md:text-xl font-light">
            Understand how you think, not just what you learn. Cogni remembers your struggles and adapts to your unique cognitive patterns.
          </p>

          {/* CTA Button */}
          <Button
            onClick={enterApp}
            className="group relative mb-20 h-14 overflow-hidden rounded-full bg-zinc-100 px-10 text-[16px] font-semibold text-zinc-950 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] active:scale-95 border border-transparent hover:border-white/50"
          >
            <span className="relative z-10 flex items-center gap-2">
              Let's Start Studying
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </span>
          </Button>

          {/* Feature Bento Grid */}
          <div className="grid w-full max-w-5xl grid-cols-1 gap-4 text-left sm:grid-cols-2 lg:grid-cols-4">
            {[
              { title: "Socratic Thinking", icon: "🧠", subtitle: "Challenge assumptions", border: "hover:border-purple-500/50" },
              { title: "Predict Struggles", icon: "🌑", subtitle: "See weak signals early", border: "hover:border-indigo-500/50" },
              { title: "Memory Insights", icon: "🧩", subtitle: "Review what truly sticks", border: "hover:border-emerald-500/50" },
              { title: "Learning Graphs", icon: "📊", subtitle: "Track growth with clarity", border: "hover:border-cyan-500/50" },
            ].map((item) => (
              <div
                key={item.title}
                className={`group relative overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02] p-6 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:bg-white/[0.04] ${item.border}`}
              >
                <div className="mb-4 text-3xl transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-3">{item.icon}</div>
                <p className="text-base font-semibold text-zinc-100">{item.title}</p>
                <p className="mt-1.5 text-sm text-zinc-400 font-light">{item.subtitle}</p>
              </div>
            ))}
          </div>

          {/* Footer Navigation Elements */}
          <div className="mt-14 flex flex-wrap items-center justify-center gap-3 text-xs text-zinc-500 font-medium">
            <span className="rounded-full border border-white/5 bg-white/5 px-4 py-1.5 transition-colors hover:text-zinc-300 hover:bg-white/10 cursor-default">7 Cognitive Modes</span>
            <span className="hidden sm:block h-1 w-1 rounded-full bg-zinc-800"></span>
            <span className="rounded-full border border-white/5 bg-white/5 px-4 py-1.5 transition-colors hover:text-zinc-300 hover:bg-white/10 cursor-default">Adaptive Memory</span>
            <span className="hidden sm:block h-1 w-1 rounded-full bg-zinc-800"></span>
            <span className="rounded-full border border-white/5 bg-white/5 px-4 py-1.5 transition-colors hover:text-zinc-300 hover:bg-white/10 cursor-default">Realtime Feedback</span>
          </div>
        </div>
      </div>
    );
  }

  const latestSocraticQuestion = getLatestSocraticQuestion(messages);
  const showSocraticQuickActions = activeFeature === "socratic" && !!latestSocraticQuestion;
  const showShadowQuickAction = activeFeature === "shadow";
  const guidedFlow = getGuidedFlow(activeFeature, context, messages, quizQuestions.length);
  const showGuide = !!guidedFlow && !dismissedGuides[activeFeature];
  const usesFloatingComposer = activeFeature === "archaeology" || activeFeature === "socratic";
  const showInlineComposer = usesFloatingComposer && messages.length <= 1 && !loading;
  const mainBottomPaddingClass = usesFloatingComposer && !showInlineComposer ? "pb-32 md:pb-40" : "";
  const compactEmptyState = messages.length <= 1 && !loading;

  return (
    <div className="flex h-screen bg-zinc-900 text-white">
      <aside className="flex w-72 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950/95 p-5 backdrop-blur-xl">
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
                  ? "bg-gradient-to-r from-purple-500/25 to-indigo-500/20 font-medium text-purple-200 shadow-[inset_4px_0_0_0_rgba(168,85,247,0.9),0_0_20px_rgba(99,102,241,0.15)] hover:from-purple-500/30 hover:to-indigo-500/25"
                  : "text-zinc-400 font-normal hover:bg-zinc-800/80 hover:text-zinc-200"
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
                  className="text-xs text-zinc-300 border-zinc-600 hover:bg-zinc-800/50 h-8 px-3"
                >
                  👤 {userId} ✏️
                </Button>
                <p className="text-[11px] text-zinc-500">Tip: Personalize your ID by changing one letter.</p>
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
          {showGuide && guidedFlow && (
            <div className="mt-4 rounded-xl border border-indigo-400/25 bg-indigo-500/10 px-4 py-3 backdrop-blur-sm animate-in fade-in duration-300">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-indigo-200">{guidedFlow.title}</p>
                <button
                  type="button"
                  onClick={() => setDismissedGuides((prev) => ({ ...prev, [activeFeature]: true }))}
                  className="rounded-md p-1 text-zinc-400 hover:bg-white/10 hover:text-zinc-100"
                  aria-label="Dismiss guide"
                >
                  <Cross1Icon className="h-3.5 w-3.5" />
                </button>
              </div>
              <p className="mt-1 text-xs text-zinc-300">{guidedFlow.helper}</p>
              <div className="mt-2 text-xs text-zinc-400">
                <span className="mr-3">Step 1: {guidedFlow.step1}</span>
                <span>Step 2: {guidedFlow.step2}</span>
              </div>
            </div>
          )}
        </header>
        <main className={`flex-1 scroll-smooth overflow-y-auto p-6 md:p-10 ${mainBottomPaddingClass}`}>
          {activeFeature !== "graphs" && (
            <div className="space-y-6 pb-24 md:pb-32 max-w-4xl mx-auto">
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
          )}
          {activeFeature !== "graphs" && messages.length <= 1 && !loading && (
            <div className={`mx-auto max-w-4xl ${showInlineComposer ? "-mt-1 mb-4" : "mt-12"}`}>
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
            <div className={`mx-auto flex max-w-4xl flex-wrap justify-center gap-4 ${compactEmptyState ? "mt-4" : "mt-8"}`}>
              <Button
                onClick={() => void handleSend()}
                disabled={loading}
                className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <>
                    <CubeIcon className="mr-2 h-5 w-5" />
                    Show Roadmap 
                  </>
                )}
              </Button>
            </div>
          ) : activeFeature === "resonance" ? (
            <div className={`mx-auto flex max-w-4xl justify-center ${compactEmptyState ? "mt-4" : "mt-8"}`}>
              <Button
                onClick={() => void handleSend()}
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
          ) : activeFeature === "shadow" ? (
            <div className={`mx-auto flex max-w-4xl justify-center ${compactEmptyState ? "mt-4" : "mt-8"}`}>
              <Button
                onClick={() => void handleShadowPredict()}
                disabled={loading}
                className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <>
                    <CubeIcon className="mr-2 h-5 w-5" />
                    Predict My Next Struggles
                  </>
                )}
              </Button>
            </div>
          ) : activeFeature === "memory" ? (
            <div className={`mx-auto flex w-full max-w-5xl flex-col gap-5 ${compactEmptyState ? "mt-4" : "mt-8"}`}>
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

              <Card className="border-zinc-700/60 bg-gradient-to-b from-zinc-900/80 to-zinc-950/80 shadow-[0_10px_30px_rgba(0,0,0,0.35)] backdrop-blur-sm">
                <CardHeader>
                  <div className="flex items-center justify-between gap-3">
                    <CardTitle className="text-zinc-100">Quick Quiz</CardTitle>
                    {quizQuestions.length > 0 && (
                      <span className="rounded-full border border-cyan-400/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-300">
                        {quizQuestions.length} Questions Ready
                      </span>
                    )}
                  </div>
                  <CardDescription className="text-zinc-400">
                    Generate a 3-question revision quiz, submit answers, and store rich learning memory.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="rounded-xl border border-zinc-700/70 bg-zinc-900/50 p-4">
                    <div className="flex gap-3 flex-wrap items-end">
                      <div className="flex-1 min-w-[220px]">
                      <Label htmlFor="quiz-topic" className="text-zinc-200">Quiz Topic</Label>
                      <Input
                        id="quiz-topic"
                        value={quizTopic}
                        onChange={(e) => setQuizTopic(e.target.value)}
                        placeholder="e.g., recursion, graph traversal"
                        className="mt-2 h-11 border-zinc-600 bg-zinc-950/70 text-zinc-100 placeholder:text-zinc-500 focus-visible:border-cyan-400/70 focus-visible:ring-cyan-400/30"
                      />
                    </div>
                    <Button
                      onClick={generateQuiz}
                      disabled={quizLoading || !quizTopic.trim()}
                      className="h-11 rounded-lg bg-cyan-600 px-6 text-white shadow-md transition-all hover:scale-[1.02] hover:bg-cyan-500"
                    >
                      {quizLoading ? "Generating..." : "Generate Quiz"}
                    </Button>
                  </div>
                  </div>

                  {quizQuestions.length > 0 && (
                    <div className="space-y-4 pt-1 animate-in fade-in duration-300">
                      {quizQuestions.map((q, idx) => (
                        <div key={q.id} className="rounded-xl border border-zinc-700/70 bg-zinc-950/55 p-5 shadow-[0_6px_18px_rgba(0,0,0,0.28)] transition-all hover:border-cyan-500/40">
                          <p className="mb-3 text-sm font-semibold text-zinc-100">
                            <span className="mr-2 rounded-md bg-cyan-500/20 px-2 py-1 text-cyan-300">Q{idx + 1}</span>
                            {q.question}
                          </p>
                          <div className="space-y-2.5">
                            {q.options.map((option, optionIdx) => (
                              <Button
                                key={`${q.id}-${option}`}
                                onClick={() => {
                                  const next = [...quizAnswers];
                                  next[idx] = option;
                                  setQuizAnswers(next);
                                }}
                                className={`w-full rounded-lg border-2 p-3 text-left transition-all ${
                                  quizAnswers[idx] === option
                                    ? "border-cyan-400 bg-cyan-500/20 font-semibold text-cyan-100 shadow-[0_0_15px_rgba(34,211,238,0.2)]"
                                    : "border-zinc-600 bg-zinc-900/40 text-zinc-300 hover:border-cyan-500/40 hover:bg-zinc-900/70"
                                }`}
                              >
                                <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-zinc-800 text-xs text-zinc-300">
                                  {String.fromCharCode(65 + optionIdx)}
                                </span>
                                {option}
                              </Button>
                            ))}
                          </div>
                        </div>
                      ))}

                      <Button
                        onClick={submitQuiz}
                        disabled={quizSubmitting || quizAnswers.some((a) => !a)}
                        className="h-11 rounded-lg bg-emerald-600 px-6 text-white shadow-md transition-all hover:scale-[1.02] hover:bg-emerald-500"
                      >
                        {quizSubmitting ? "Submitting..." : "Submit Quiz"}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : activeFeature === "graphs" ? (
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
              <Card className="border-zinc-700/60 bg-zinc-900/70 backdrop-blur-sm">
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <CardTitle className="text-zinc-100">Live Learning Visualization</CardTitle>
                    <Button
                      onClick={() => {
                        void refreshMemoryVisualization(true);
                      }}
                      disabled={memoryVizLoading}
                      className="h-9 rounded-lg bg-zinc-800 px-4 text-sm text-zinc-100 hover:bg-zinc-700"
                    >
                      {memoryVizLoading ? "Refreshing..." : "Refresh Now"}
                    </Button>
                  </div>
                  <CardDescription className="text-zinc-400">
                    Student-specific analytics from Hindsight. Refresh updates only on button click.
                    {memoryLastUpdatedAt && ` Last updated: ${new Date(memoryLastUpdatedAt).toLocaleTimeString()}`}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  {memoryVizError && (
                    <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-300">
                      {memoryVizError}
                    </div>
                  )}

                  {memoryPerformanceOverview && (
                    <Card className="border-zinc-700/60 bg-zinc-950/40">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-zinc-100">Student Performance Analysis</CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-3 text-sm text-zinc-300 md:grid-cols-2">
                        <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3">
                          <p>Topics tracked: {Number(memoryPerformanceOverview.topics_tracked ?? 0)}</p>
                          <p>Quiz attempts: {Number(memoryPerformanceOverview.total_quiz_attempts ?? 0)}</p>
                          <p>
                            Avg quiz score: {typeof memoryPerformanceOverview.avg_quiz_score_ratio === "number"
                              ? `${Math.round(Number(memoryPerformanceOverview.avg_quiz_score_ratio) * 100)}%`
                              : "N/A"}
                          </p>
                        </div>
                        <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3">
                          <p>
                            Strength topics: {Array.isArray(memoryPerformanceOverview.strength_topics)
                              ? (memoryPerformanceOverview.strength_topics as string[]).join(", ") || "N/A"
                              : "N/A"}
                          </p>
                          <p>
                            Focus topics: {Array.isArray(memoryPerformanceOverview.focus_topics)
                              ? (memoryPerformanceOverview.focus_topics as string[]).join(", ") || "N/A"
                              : "N/A"}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <ConfidenceGraph series={memoryConfidenceSeries} loading={memoryVizLoading} />
                  <MemoryTimeline entries={memoryTimelineEntries} loading={memoryVizLoading} />
                  <CognitiveSummary
                    summary={memorySummaryText}
                    profile={memoryLearningProfile}
                    loading={memoryVizLoading}
                  />
                </CardContent>
              </Card>
            </div>
          ) : (
            <div
              className={showInlineComposer
                ? "mx-auto mt-0 mb-2 w-full max-w-4xl"
                : "fixed bottom-0 left-[280px] right-0 z-10 bg-gradient-to-t from-[#09090b] via-[#09090b]/95 to-transparent p-6 md:p-8 pointer-events-none"
              }
            >
              {showSocraticQuickActions && (
                <div className={`mx-auto mb-3 flex max-w-4xl items-center gap-2 ${showInlineComposer ? "" : "pointer-events-auto"}`}>
                  <Button
                    variant="secondary"
                    className="h-9 rounded-lg"
                    disabled={loading}
                    onClick={() => void handleSend("I don't know")}
                  >
                    I don&apos;t know
                  </Button>
                  <Button
                    variant="outline"
                    className="h-9 rounded-lg border-zinc-600 text-zinc-200"
                    disabled={loading}
                    onClick={() => void handleSocraticHint()}
                  >
                    Hint
                  </Button>
                </div>
              )}
              {showShadowQuickAction && (
                <div className={`mx-auto mb-3 flex max-w-4xl items-center gap-2 ${showInlineComposer ? "" : "pointer-events-auto"}`}>
                  <Button
                    className="h-9 rounded-lg bg-amber-500/20 text-amber-200 border border-amber-400/30 hover:bg-amber-500/30"
                    disabled={loading}
                    onClick={() => void handleShadowPredict()}
                  >
                    {loading ? "Predicting..." : "Predict My Next Struggles"}
                  </Button>
                </div>
              )}
              <div className={`relative mx-auto flex max-w-4xl items-center rounded-2xl border border-white/10 bg-[#18181b]/90 shadow-[0_8px_40px_rgba(0,0,0,0.4)] backdrop-blur-2xl transition-all duration-300 focus-within:border-purple-500/50 focus-within:ring-4 focus-within:ring-purple-500/10 hover:border-white/20 ${showInlineComposer ? "" : "pointer-events-auto"}`}>
                <span className="pointer-events-none absolute left-4 text-zinc-500">
                  {FEATURES.find((f) => f.id === activeFeature)?.icon || <MagicWandIcon className="h-4 w-4" />}
                </span>
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={getPlaceholder(activeFeature)}
                  className="h-16 w-full border-0 bg-transparent pl-12 pr-20 text-[16px] placeholder:text-zinc-500 focus-visible:ring-0 shadow-none text-zinc-100 rounded-2xl"
                  disabled={loading}
                />
                <Button
                  size="icon"
                  className="absolute right-2 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-xl bg-gradient-to-br from-purple-600 to-indigo-600 text-white shadow-lg transition-all duration-300 hover:scale-[1.05] hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-[0.95] disabled:opacity-40 disabled:hover:scale-100 disabled:hover:shadow-lg disabled:cursor-not-allowed"
                  onClick={() => void handleSend()}
                  disabled={loading}
                >
                  {loading ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5 ml-0.5">
                      <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                    </svg>
                  )}
                </Button>
              </div>
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
  const hiddenMetadataKeys = new Set(["response_id", "user_query", "shadow_predictions"]);
  const shadowPredictions = !isUser && message.feature === "shadow"
    ? getShadowPredictionsFromMetadata(message.metadata)
    : [];

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isSystem) {
    const lines = message.content
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    const heading = lines[0] ?? "Cogni";
    const subheading = lines.slice(1).join(" ");

    return (
      <div className="my-8 flex justify-center">
        <div className="w-full max-w-4xl rounded-2xl border border-white/10 bg-gradient-to-br from-zinc-900/90 via-zinc-900/70 to-indigo-950/40 px-6 py-5 text-center shadow-[0_12px_40px_rgba(0,0,0,0.35)] backdrop-blur-sm">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-indigo-200">
            Guided Start
          </div>
          <p className="text-lg font-semibold tracking-wide text-zinc-100 md:text-xl">{heading}</p>
          {subheading && <p className="mt-2 text-sm leading-relaxed text-zinc-300 md:text-base">{subheading}</p>}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`group flex w-full animate-in slide-in-from-bottom-2 fade-in duration-500 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex max-w-[85%] sm:max-w-[75%] gap-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
        {/* Avatar */}
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl mt-auto shadow-sm ${isUser ? "bg-gradient-to-br from-purple-500 to-indigo-600 text-white ring-1 ring-white/20" : "bg-[#18181b] border border-white/10 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.1)]"}`}>
          {isUser ? <span className="text-[12px] font-bold tracking-wider">ST</span> : FEATURES.find((f) => f.id === message.feature)?.icon || <MagicWandIcon className="h-4 w-4" />}
        </div>
        
        {/* Bubble */}
        <Card
          className={`relative flex flex-col border-0 shadow-lg transition-all duration-300 ${
            isUser
              ? "bg-gradient-to-br from-purple-600 to-indigo-600 text-white rounded-3xl rounded-br-sm shadow-purple-900/20"
              : "bg-[#18181b]/90 border border-white/5 text-zinc-200 rounded-3xl rounded-bl-sm backdrop-blur-sm hover:shadow-xl hover:shadow-black/50"
          }`}
        >
          {!isUser && (
            <button
              onClick={handleCopy}
              className="absolute right-3 top-3 rounded-lg bg-white/5 p-2 text-zinc-400 opacity-0 backdrop-blur-md transition-all hover:scale-105 hover:bg-white/10 hover:text-zinc-100 active:scale-95 group-hover:opacity-100"
              title="Copy to clipboard"
            >
              {copied ? <CheckIcon className="h-4 w-4 text-emerald-400" /> : <CopyIcon className="h-4 w-4" />}
            </button>
          )}
          <CardContent className="px-6 py-5 text-[15px] sm:text-[16px]">
          {shadowPredictions.length > 0 ? (
            <div className="space-y-3">
              {message.content.split("\n").filter(Boolean).map((line, i) => (
                <p key={i} className={`leading-relaxed ${i > 0 ? "mt-2" : ""}`}>
                  {renderRichLine(line, isUser)}
                </p>
              ))}
              <div className="space-y-2">
                {shadowPredictions.map((card, idx) => {
                  const icon = idx % 2 === 0 ? "⚠️" : "💡";
                  const hasLeadingEmoji = /^[\u{1F300}-\u{1FAFF}]/u.test(card.title.trim());
                  return (
                    <div
                      key={`${card.title}-${idx}`}
                      className="rounded-xl border border-amber-300/25 bg-gradient-to-br from-amber-500/10 to-indigo-500/10 p-3 backdrop-blur-sm transition-all hover:-translate-y-0.5 hover:bg-amber-500/15 hover:shadow-[0_8px_24px_rgba(245,158,11,0.12)]"
                    >
                      <p className="font-semibold text-amber-200">{hasLeadingEmoji ? card.title : `${icon} ${card.title}`}</p>
                      <p className="mt-1 text-sm text-zinc-200">{card.description}</p>
                      <p className="mt-2 text-xs text-zinc-300"><span className="text-zinc-400">Trigger:</span> {card.trigger_condition}</p>
                      <p className="mt-1 text-xs text-emerald-300"><span className="text-zinc-400">Action:</span> {card.suggested_micro_action}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            message.content.split("\n").map((line, i) => (
              <p key={i} className={`leading-relaxed ${i > 0 ? "mt-4" : ""}`}>
                {renderRichLine(line, isUser)}
              </p>
            ))
          )}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-5 flex flex-wrap gap-2 text-[11px]">
              {Object.entries(message.metadata)
                .filter(([key]) => !hiddenMetadataKeys.has(key))
                .map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center gap-1.5 rounded-md bg-white/5 border border-white/5 px-2.5 py-1 text-zinc-400 font-medium"
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
                    className={`rounded-md h-7 w-7 text-xs font-medium transition-all ${
                    feedbackRating === value
                        ? "bg-purple-500 text-white shadow-[0_0_10px_rgba(168,85,247,0.3)]"
                        : "bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-zinc-200"
                    } ${feedbackLoading ? "cursor-not-allowed opacity-50" : "active:scale-95"}`}
                >
                  {value}
                </button>
              ))}
              {feedbackRating !== undefined && (
                  <span className="text-[11px] text-emerald-400 ml-2 animate-in fade-in flex items-center gap-1"><CheckIcon className="h-3 w-3"/> Saved</span>
              )}
            </div>
          )}
        </CardContent>
          <CardFooter className={`p-2 px-6 text-[11px] font-medium opacity-60 ${isUser ? 'text-purple-200 justify-end' : 'text-zinc-500'}`}>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </CardFooter>
      </Card>
      </div>
    </div>
  );
}

function LoadingBubble() {
  return (
    <div className="group flex w-full animate-in slide-in-from-bottom-2 fade-in duration-500 justify-start mb-6">
      <div className="flex max-w-[85%] sm:max-w-[75%] gap-4 flex-row">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl mt-auto shadow-[0_0_15px_rgba(168,85,247,0.1)] bg-[#18181b] border border-white/10 text-purple-400">
          <MagicWandIcon className="h-4 w-4 animate-pulse" />
        </div>
        <Card className="relative flex flex-col border border-white/5 bg-[#18181b]/90 rounded-3xl rounded-bl-sm shadow-lg backdrop-blur-sm">
          <CardContent className="px-5 py-4">
            <div className="flex items-center gap-1.5 px-1 py-1">
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-purple-500" style={{ animationDelay: "0ms" }} />
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-purple-500" style={{ animationDelay: "150ms" }} />
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-purple-500" style={{ animationDelay: "300ms" }} />
            </div>
          </CardContent>
        </Card>
      </div>
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
      const rawQuestion = String(data.question || data.follow_up_question || "Let's explore this together. What's the simplest case you can think of?");
      const question = rawQuestion.trim().endsWith("?") ? rawQuestion.trim() : `${rawQuestion.trim()}?`;
      const hint = data.hint ? String(data.hint) : undefined;
      const concept = data.concept ? String(data.concept) : "";
      
      // Keep Socratic output compact and readable.
      const lines: string[] = [];
      if (concept) {
        lines.push(`**Topic**: ${concept}`);
      }
      if (data.response_analysis) {
        lines.push(`**Coach Note**: ${String(data.response_analysis)}`);
      }
      lines.push(`**Question**: ${question}`);
      if (hint) {
        lines.push(`**Hint**: ${hint}`);
      }
      const content = lines.join("\n\n");
      
      return {
        content,
        metadata: {
          ...metadata,
          current_question: question,
          hint,
          resolved_count: (data.past_history as GenericRecord | undefined)
            ?.resolved_count,
          unresolved_count: (data.past_history as GenericRecord | undefined)
            ?.unresolved_count,
          is_follow_up: !!data.follow_up_question,
        },
      };
    }

    case "shadow": {
      const predictions = Array.isArray(data.predictions)
        ? (data.predictions as ShadowPredictionCard[])
        : [];
      const evidence = Array.isArray(data.evidence)
        ? (data.evidence as string[])
        : [];
      const topicAnalysis = (data.topic_analysis as GenericRecord | undefined) || {};
      const topicLabel = String(data.current_topic || topicAnalysis.topic || "current topic");
      const overview = String(data.prediction ?? "No prediction available yet.");

      return {
        content: `**Prediction Overview (${topicLabel})**: ${overview}\n\n**Signals Used**:\n${
          evidence.map((e) => `• ${e}`).join("\n") ||
          "Based on your learning patterns"
        }`,
        metadata: {
          ...metadata,
          shadow_predictions: predictions,
          prediction_count: predictions.length,
        },
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
      // Handle enhanced memory with timeline and "what cogni knows"
      const timeline = (apiData.timeline as GenericRecord) || null;
      const cogniKnows = (apiData.cogni_knows as GenericRecord) || null;
      
      if (cogniKnows && cogniKnows.summary) {
        // NEW: Display impressive "What Cogni knows about you" summary + timeline
        const timelineData = timeline as GenericRecord;
        const timelineEntries = (timelineData?.timeline as GenericRecord[]) || [];
        const topicMetrics = (timelineData?.topic_confidence_metrics as GenericRecord) || {};
        
        // Build confidence growth visualization
        let confidenceVisualization = "";
        const topicKeys = Object.keys(topicMetrics);
        if (topicKeys.length > 0) {
          confidenceVisualization = "\n\n### **📈 Confidence Growth by Topic**\n\n";
          for (const topic of topicKeys.slice(0, 5)) {
            const metrics = topicMetrics[topic] as GenericRecord;
            const improvement = Number(metrics.improvement || 0);
            const current = Number(metrics.current_confidence || 0.5);
            const initial = Number(metrics.initial_confidence || 0.3);
            const sessions = Number(metrics.sessions_studied || 1);
            
            const confBar = "█".repeat(Math.round(current * 10)) + "░".repeat(10 - Math.round(current * 10));
            const direction = improvement > 0 ? "📈 +" : improvement < 0 ? "📉 " : "→ ";
            
            confidenceVisualization += `**${topic}**\n`;
            confidenceVisualization += `${confBar} ${Math.round(current * 100)}% (${direction}${Math.round(improvement * 100)}% over ${sessions} session${sessions > 1 ? 's' : ''})\n\n`;
          }
        }
        
        // Build timeline summary
        let timelineSummary = "";
        if (timelineEntries.length > 0) {
          timelineSummary = `\n\n### **⏱️ Learning Timeline (${timelineEntries.length} sessions)**\n\n`;
          timelineSummary += timelineEntries.slice(0, 10).map((e, idx) => {
            const ent = e as GenericRecord;
            const ts = String(ent.timestamp || "");
            const topic = String(ent.topic || "general");
            const conf = Math.round(Number(ent.confidence || 0.75) * 100);
            const dateStr = ts ? new Date(ts).toLocaleDateString() : "Unknown date";
            return `${idx + 1}. **${topic}** (${conf}% confidence) - ${dateStr}`;
          }).join("\n");
          
          if (timelineEntries.length > 10) {
            timelineSummary += `\n...and ${timelineEntries.length - 10} more sessions`;
          }
        }
        
        const content = String(cogniKnows.summary || "") + confidenceVisualization + timelineSummary;
        
        return {
          content,
          metadata: {
            ...metadata,
            memory_type: "enhanced_with_timeline",
            total_sessions: timeline?.total_sessions || 0,
            topics_studied: timeline?.total_topics || 0
          }
        };
      }
      
      // Fallback to original memory format
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
    graphs: "Graphs view is read-only. Click Refresh Now to update analysis.",
  };
  return placeholders[feature];
}

function getLatestSocraticQuestion(messages: Message[]): string | null {
  for (let idx = messages.length - 1; idx >= 0; idx -= 1) {
    const msg = messages[idx];
    if (msg.role !== "assistant" || msg.feature !== "socratic") {
      continue;
    }
    const metadata = (msg.metadata || {}) as GenericRecord;
    const fromMetadata =
      typeof metadata.current_question === "string" && metadata.current_question.trim().endsWith("?")
        ? metadata.current_question.trim()
        : "";
    if (fromMetadata) {
      return fromMetadata;
    }

    const lines = msg.content.split("\n").map((line) => line.trim()).filter(Boolean);
    const lastQuestionLine = [...lines].reverse().find((line) => line.endsWith("?"));
    if (lastQuestionLine) {
      return lastQuestionLine.replace(/^\*\*Next question\*\*:\s*/i, "").trim();
    }
  }
  return null;
}

function getShadowPredictionsFromMetadata(metadata?: Record<string, unknown>): ShadowPredictionCard[] {
  if (!metadata) return [];
  const rows = metadata.shadow_predictions;
  if (!Array.isArray(rows)) return [];

  const cards: ShadowPredictionCard[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const item = row as Record<string, unknown>;
    const title = String(item.title || "").trim();
    const description = String(item.description || "").trim();
    const triggerCondition = String(item.trigger_condition || "").trim();
    const action = String(item.suggested_micro_action || "").trim();
    if (!title || !description || !triggerCondition || !action) continue;
    cards.push({
      title,
      description,
      trigger_condition: triggerCondition,
      suggested_micro_action: action,
      difficulty: String(item.difficulty || "Medium"),
      confidence: typeof item.confidence === "number" ? item.confidence : undefined,
    });
  }
  return cards;
}

function getGuidedFlow(
  activeFeature: FeatureMode,
  context: { topic?: string; confusion?: number; errorPattern?: string },
  messages: Message[],
  quizQuestionCount: number,
): { title: string; helper: string; step1: string; step2: string } | null {
  const hasTopic = !!context.topic?.trim();
  const hasUserInput = messages.some((m) => m.role === "user" && m.feature === activeFeature);

  if (activeFeature === "archaeology") {
    return {
      title: "⬇️ Now describe your confusion below",
      helper: "Add a concrete confusion statement so archaeology can retrieve similar past moments.",
      step1: hasTopic ? "Enter topic ✅" : "Enter topic",
      step2: hasUserInput ? "Describe confusion ✅" : "Describe confusion ⬇️",
    };
  }

  if (activeFeature === "socratic") {
    return {
      title: "⬇️ Answer the question below",
      helper: "Give a short belief or answer; Socratic follow-up will adapt using your memory patterns.",
      step1: hasTopic ? "Enter topic ✅" : "Enter topic",
      step2: hasUserInput ? "Answer question ✅" : "Answer question ⬇️",
    };
  }

  if (activeFeature === "shadow") {
    return {
      title: "⬇️ Click to predict challenges",
      helper: "Set your topic, then use the prediction button to anticipate upcoming struggles.",
      step1: hasTopic ? "Enter topic ✅" : "Enter topic",
      step2: hasUserInput ? "Predict challenges ✅" : "Predict challenges ⬇️",
    };
  }

  if (activeFeature === "memory") {
    return {
      title: "⬇️ Build your memory profile",
      helper: "Generate summary or quiz to enrich memory signals and track metacognitive growth.",
      step1: quizQuestionCount > 0 ? "Generate quiz ✅" : "Generate quiz",
      step2: "Submit answers ⬇️",
    };
  }

  if (activeFeature === "resonance") {
    return {
      title: "⬇️ Explore hidden concept links",
      helper: "Enter a topic and click show hidden connections to uncover adjacent ideas.",
      step1: hasTopic ? "Enter topic ✅" : "Enter topic",
      step2: "Find connections ⬇️",
    };
  }

  if (activeFeature === "contagion") {
    return {
      title: "⬇️ Learn from peer patterns",
      helper: "Enter a topic and generate a roadmap from community-level successful strategies.",
      step1: hasTopic ? "Enter topic ✅" : "Enter topic",
      step2: "Generate roadmap ⬇️",
    };
  }

  if (activeFeature === "graphs") {
    return {
      title: "⬇️ Refresh your dashboard",
      helper: "Use refresh to update your progress, weak areas, and concept mastery visuals.",
      step1: "Open graph view ✅",
      step2: "Refresh metrics ⬇️",
    };
  }
 return null;
}

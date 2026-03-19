
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
import { Slider } from "@/components/ui/slider";

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
    const requiresInput = [
      "archaeology",
      "socratic",
      "resonance",
      "contagion",
    ].includes(activeFeature);
    if ((requiresInput && !input.trim()) || loading) return;

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

      switch (activeFeature) {
        case "archaeology": {
          const topic = context.topic || extractTopic(input);
          const confusion = context.confusion || 3;
          response = await api.getArchaeology(topic, confusion);
          break;
        }

        case "socratic": {
          const concept = context.topic || extractTopic(input);
          response = await api.askSocratic(concept, input);
          break;
        }

        case "shadow": {
          const shadowTopic = context.topic || extractTopic(input);
          response = await api.getShadowPrediction(shadowTopic, 7);
          break;
        }

        case "resonance": {
          const resonanceTopic = context.topic || extractTopic(input);
          response = await api.getResonance(resonanceTopic);
          break;
        }

        case "contagion": {
          const contagionTopic = input.trim();
          if (!contagionTopic) {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                role: "assistant",
                content:
                  "Please enter a topic you want to learn from peers about (e.g., machine learning, web development, database design).",
                timestamp: new Date(),
              },
            ]);
            setLoading(false);
            return;
          }
          response = await api.getContagion(contagionTopic);
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

      if (typeof response?.demo_mode === "boolean") {
        setLastDemoMode(response.demo_mode);
      }

      const assistantMessage = formatResponse(response, activeFeature);

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: assistantMessage.content,
          feature: activeFeature,
          timestamp: new Date(),
          metadata: assistantMessage.metadata,
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

  return (
    <div className="flex h-screen bg-zinc-900 text-white">
      <aside className="flex w-64 flex-col border-r border-zinc-800 bg-zinc-950 p-4">
        <div className="flex items-center gap-2">
          <MagicWandIcon className="h-8 w-8 text-purple-500" />
          <h1 className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-2xl font-bold tracking-tight text-transparent drop-shadow-md">Cogni</h1>
        </div>
        <Separator className="my-4" />
        <nav className="flex flex-col gap-2">
          {FEATURES.map((feature) => (
            <Button
              key={feature.id}
              variant="ghost"
              onClick={() => setActiveFeature(feature.id)}
              className={`justify-start gap-3 transition-all duration-200 ${
                activeFeature === feature.id
                  ? "bg-purple-500/15 font-medium text-purple-300 shadow-[inset_4px_0_0_0_rgba(168,85,247,0.8)] hover:bg-purple-500/25"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              }`}
            >
              {feature.icon}
              {feature.label}
            </Button>
          ))}
        </nav>
        <div className="mt-auto">
          <Separator className="my-4" />
          <div className="flex items-center justify-between text-sm">
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
                className={`rounded-full px-2 py-0.5 text-xs ${
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
        <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/80 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-zinc-100">
                {FEATURES.find((f) => f.id === activeFeature)?.label}
              </h2>
              <p className="text-sm text-zinc-400">
                {FEATURES.find((f) => f.id === activeFeature)?.description}
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={clearChat}>
              <TrashIcon className="h-5 w-5" />
            </Button>
          </div>
          <Separator className="my-4" />
          <div className="flex gap-4">
            {(activeFeature === "archaeology" ||
              activeFeature === "socratic" ||
              activeFeature === "resonance" ||
              activeFeature === "shadow") && (
              <div className="flex-1">
                <Label htmlFor="topic">Target Topic</Label>
                <Input
                  id="topic"
                  type="text"
                  value={context.topic || ""}
                  onChange={(e) => handleContextUpdate("topic", e.target.value)}
                  placeholder="e.g., recursion, dynamic programming..."
                  className="mt-2 border-zinc-700 bg-zinc-900/50 shadow-sm backdrop-blur-sm transition-all hover:bg-zinc-800/50 focus-visible:border-purple-500 focus-visible:ring-1 focus-visible:ring-purple-500 focus-visible:shadow-[0_0_15px_rgba(168,85,247,0.2)]"
                />
              </div>
            )}

            {activeFeature === "archaeology" && (
              <div className="w-48">
                <Label htmlFor="confusion">
                  Confusion Level: {context.confusion || 3}
                </Label>
                <Slider
                  id="confusion"
                  min={1}
                  max={5}
                  value={[context.confusion || 3]}
                  onValueChange={(value) =>
                    handleContextUpdate("confusion", value[0])
                  }
                  className="mt-2"
                />
              </div>
            )}

            {activeFeature === "contagion" && (
              <div className="flex-1">
                <Label htmlFor="errorPattern">Error Pattern</Label>
                <select
                  id="errorPattern"
                  value={context.errorPattern || "base_case_missing"}
                  onChange={(e) =>
                    handleContextUpdate("errorPattern", e.target.value)
                  }
                  className="mt-2 w-full cursor-pointer rounded-md border border-zinc-700 bg-zinc-900/50 p-2 text-sm text-zinc-200 shadow-sm outline-none backdrop-blur-sm transition-all hover:bg-zinc-800/50 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:shadow-[0_0_15px_rgba(168,85,247,0.2)]"
                >
                  <option value="base_case_missing">Base Case Missing</option>
                  <option value="stack_overflow">Stack Overflow</option>
                  <option value="off_by_one">Off-by-One</option>
                </select>
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 scroll-smooth overflow-y-auto p-4 md:p-8">
          <div className="space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && <LoadingBubble />}
            <div ref={messagesEndRef} />
          </div>
          {messages.length <= 1 && !loading && (
            <div className="mt-8">
              <h3 className="mb-4 text-center text-sm text-zinc-400">
                Suggestions
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {QUICK_PROMPTS[activeFeature].map((prompt, i) => (
                  <Card
                    key={i}
                    onClick={() => handleQuickPrompt(prompt)}
                    className="group cursor-pointer border-zinc-800/50 bg-zinc-900/40 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-purple-500/50 hover:bg-purple-500/10 hover:shadow-[0_8px_30px_-4px_rgba(168,85,247,0.2)] active:translate-y-0 active:scale-95"
                  >
                    <CardContent className="p-4">
                      <p className="text-sm transition-colors group-hover:text-purple-300">{prompt}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </main>
        <footer className="border-t border-zinc-800/50 bg-zinc-950/50 p-4 backdrop-blur-xl">
          {activeFeature === "shadow" ? (
            <div className="mx-auto flex max-w-4xl justify-center">
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
          ) : activeFeature === "memory" ? (
            <div className="mx-auto flex max-w-4xl justify-center">
              <Button
                onClick={handleSend}
                disabled={loading}
                className="h-14 rounded-full bg-purple-600 px-8 text-base font-medium text-white shadow-lg transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] active:scale-95"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <>
                    <MagicWandIcon className="mr-2 h-5 w-5" />
                    Load Memory Profile
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="relative mx-auto flex max-w-4xl items-center">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getPlaceholder(activeFeature)}
                className="h-14 rounded-full border-zinc-700/50 bg-zinc-900/80 pr-14 text-base shadow-lg transition-all hover:bg-zinc-900 focus-visible:border-purple-500 focus-visible:bg-zinc-900 focus-visible:ring-1 focus-visible:ring-purple-500/50 focus-visible:shadow-[0_0_20px_rgba(168,85,247,0.25)]"
                disabled={loading}
              />
              <Button
                size="icon"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-purple-600 text-white shadow-md transition-all hover:scale-105 hover:bg-purple-500 hover:shadow-lg active:scale-95"
                onClick={handleSend}
                disabled={loading || !input.trim()}
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
                ) : (
                  <PlusCircledIcon className="h-5 w-5" />
                )}
              </Button>
            </div>
          )}
        </footer>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isSystem) {
    return (
      <div className="my-6 text-center text-sm font-medium text-zinc-500">
        {message.content.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    );
  }

  return (
    <div
      className={`group message-enter flex items-start gap-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-purple-400 shadow-sm">
          {FEATURES.find((f) => f.id === message.feature)?.icon}
        </div>
      )}
      <Card
        className={`relative max-w-[85%] border shadow-md transition-all duration-300 sm:max-w-xl ${
          isUser
            ? "rounded-3xl rounded-tr-sm border-purple-500/30 bg-gradient-to-br from-purple-600 to-indigo-600 text-white"
            : "rounded-3xl rounded-tl-sm border-zinc-700/50 bg-zinc-800/80 text-zinc-100 backdrop-blur-sm hover:border-zinc-600/50"
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
        <CardContent className="p-4">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={`leading-relaxed tracking-wide ${i > 0 ? "mt-3" : ""}`}>
              {renderRichLine(line)}
            </p>
          ))}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              {Object.entries(message.metadata).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center gap-1 rounded-full bg-zinc-700/50 px-2 py-1"
                >
                  <span className="font-semibold capitalize">
                    {key.replace(/_/g, " ")}:
                  </span>
                  <span>{String(value)}</span>
                </div>
              ))}
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
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-purple-400/50 bg-gradient-to-br from-purple-500 to-indigo-600 shadow-md">
          👤
        </div>
      )}
    </div>
  );
}

function LoadingBubble() {
  return (
    <div className="message-enter flex items-start gap-4">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-purple-400 shadow-sm">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-500 border-t-zinc-900" />
      </div>
      <Card className="max-w-[85%] rounded-3xl rounded-tl-sm border border-zinc-700/50 bg-zinc-800/80 shadow-md backdrop-blur-sm sm:max-w-xl">
        <CardContent className="p-4">
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

function renderRichLine(line: string): React.ReactNode {
  const parts = line.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-semibold text-purple-400">
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
        content += `**Recommendation**: ${String(data.recommendation)}`;
      }
      return { content: content.trim(), metadata };
    }

    case "socratic": {
      return {
        content: `${
          data.question ||
          "Let's explore this together. What's the simplest case you can think of?"
        }`,
        metadata: {
          resolved_count: (data.past_history as GenericRecord | undefined)
            ?.resolved_count,
          unresolved_count: (data.past_history as GenericRecord | undefined)
            ?.unresolved_count,
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
      return {
        content: `**Hidden Connections for "${String(
          data.topic || "your topic"
        )}"**:\n\n${
          hiddenConnections
            .map(
              (c) =>
                `• **${String(c.topic ?? "topic").replace(/_/g, " ")}** (${Math.round(
                  Number(c.strength ?? 0) * 100
                )}%): ${String(c.reason ?? "No reason available")}`
            )
            .join("\n") || "No connections found yet."
        }\n\n${String(data.insight || "")}`,
        metadata: { connection_count: hiddenConnections.length },
      };
    }

    case "contagion": {
      metadata.community_size = data.community_size;
      metadata.success_rate = data.success_rate;
      const strategies = Array.isArray(data.additional_strategies)
        ? (data.additional_strategies as GenericRecord[])
        : [];
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
        metadata: { memory_count: memories.length },
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
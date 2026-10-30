import { useState, useCallback } from "react";
import { api } from "@/services/api";
import type {
  ChatMessage,
  AnswerResponse,
  EvidenceEvaluationResponse,
  QueryDecisionResponse,
} from "@/types";

const LOADING_STAGES = [
  "Analyzing Query Intent & Entities...",
  "Selecting Authoritative Sources...",
  "Allocating Retrieval Budget...",
  "Executing Hybrid Search (Semantic + Lexical)...",
  "Evaluating Multi-Criterion Evidence...",
  "Synthesizing Grounded Answer & Citations...",
];

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem("quorix-chat-messages");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return [];
      }
    }
    return [];
  });

  const [isLoading, setIsLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>("");
  const [activeMessage, setActiveMessage] = useState<ChatMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"trace" | "sources" | "evidence" | "citations" | "metrics">("trace");

  const saveMessages = (newMsgs: ChatMessage[]) => {
    setMessages(newMsgs);
    try {
      localStorage.setItem("quorix-chat-messages", JSON.stringify(newMsgs));
    } catch {
      // Ignore quota errors
    }
  };

  const clearChat = () => {
    setMessages([]);
    setActiveMessage(null);
    setError(null);
    localStorage.removeItem("quorix-chat-messages");
  };

  const deleteMessage = useCallback(
    (id: string) => {
      setMessages((prev) => {
        const updated = prev.filter((m) => m.id !== id);
        try {
          localStorage.setItem("quorix-chat-messages", JSON.stringify(updated));
        } catch {
          // Ignore quota errors
        }
        return updated;
      });
      if (activeMessage?.id === id) {
        setActiveMessage(null);
      }
    },
    [activeMessage]
  );

  const sendMessage = useCallback(
    async (queryText: string) => {
      const trimmed = queryText.trim();
      if (!trimmed || isLoading) return;

      setError(null);
      setIsLoading(true);

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      const updated = [...messages, userMsg];
      saveMessages(updated);

      // Start stage progression animation
      let stageIndex = 0;
      setCurrentStage(LOADING_STAGES[0]);
      const stageTimer = setInterval(() => {
        stageIndex = (stageIndex + 1) % LOADING_STAGES.length;
        setCurrentStage(LOADING_STAGES[stageIndex]);
      }, 700);

      try {
        // Step 1: Generate grounded answer first
        const answerData = await api.generateAnswer(trimmed);

        clearInterval(stageTimer);

        // Step 2: Fetch detailed inspector breakdown (evaluation & query analysis)
        let evalData: EvidenceEvaluationResponse | undefined;
        let queryData: QueryDecisionResponse | undefined;

        try {
          const [evalRes, queryRes] = await Promise.allSettled([
            api.evaluateEvidence(trimmed),
            api.analyzeQuery(trimmed),
          ]);
          if (evalRes.status === "fulfilled") evalData = evalRes.value;
          if (queryRes.status === "fulfilled") queryData = queryRes.value;
        } catch {
          // Non-critical inspector data
        }

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: answerData.answer,
          timestamp: new Date().toISOString(),
          answerResponse: answerData,
          evaluationResponse: evalData,
          queryDecision: queryData,
        };

        const finalMessages = [...updated, assistantMsg];
        saveMessages(finalMessages);
        setActiveMessage(assistantMsg);
      } catch (err: any) {
        clearInterval(stageTimer);
        const errMsg = err?.response?.data?.detail || err?.message || "An unexpected error occurred.";
        setError(errMsg);

        const errorMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: `⚠️ **Error Encountered:** ${errMsg}\n\nPlease check your backend connection at http://localhost:8000 and ensure the server is running.`,
          timestamp: new Date().toISOString(),
        };
        saveMessages([...updated, errorMsg]);
      } finally {
        setIsLoading(false);
        setCurrentStage("");
      }
    },
    [messages, isLoading]
  );

  return {
    messages,
    isLoading,
    currentStage,
    activeMessage,
    error,
    activeTab,
    setActiveTab,
    setActiveMessage,
    sendMessage,
    deleteMessage,
    clearChat,
  };
}

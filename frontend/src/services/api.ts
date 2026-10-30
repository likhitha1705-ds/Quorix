/**
 * Quorix API Service Layer.
 * Direct Axios integration connecting frontend components to backend endpoints.
 */
import axios from "axios";
import type {
  AnswerResponse,
  BackendHealth,
  EvidenceEvaluationResponse,
  QueryDecisionResponse,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000,
});

export const api = {
  /** Check backend connectivity and status */
  async checkHealth(): Promise<BackendHealth> {
    const res = await apiClient.get<BackendHealth>("/api/health");
    return res.data;
  },

  /** Phase 6 Full Pipeline: Query -> Retrieval -> Evidence -> Grounded Answer */
  async generateAnswer(query: string): Promise<AnswerResponse> {
    const res = await apiClient.post<AnswerResponse>("/api/answer", { query });
    return res.data;
  },

  /** Phase 5 Evidence Evaluation details (chunks, scoring, conflicts) */
  async evaluateEvidence(query: string): Promise<EvidenceEvaluationResponse> {
    const res = await apiClient.post<EvidenceEvaluationResponse>("/api/evaluate", { query });
    return res.data;
  },

  /** Phase 3 Query Analysis & Source Selection breakdown */
  async analyzeQuery(query: string): Promise<QueryDecisionResponse> {
    const res = await apiClient.post<QueryDecisionResponse>("/api/query/analyze", { query });
    return res.data;
  },
};


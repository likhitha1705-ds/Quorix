/**
 * TypeScript interface definitions for Quorix Frontend & Dashboard.
 * Accurately models Phase 1–6 backend API responses.
 */

export type EvidenceDecision = "SUFFICIENT" | "INSUFFICIENT" | "CONFLICTING" | "UNSUPPORTED";

export interface BackendHealth {
  status: string;
  app: string;
}

export interface Citation {
  chunk_id: string;
  source_name: string;
  source_type: string;
  source_id: string;
  quote?: string | null;
  confidence_score: number;
  metadata?: Record<string, any>;
}

export interface BudgetConsumed {
  chunks_used: number;
  chunks_limit: number;
  chunks_remaining: number;
  tokens_used: number;
  tokens_limit: number;
  tokens_remaining: number;
  calls_used: number;
  calls_limit: number;
  calls_remaining: number;
  budget_exhausted: boolean;
}

export interface RetrievalMetrics {
  retrieval_calls: number;
  retrieved_chunks: number;
  selected_sources: string[];
  skipped_sources: string[];
  estimated_tokens: number;
  execution_time_ms: number;
  retrieval_budget_consumed?: BudgetConsumed;
}

export interface ExecutionMetrics {
  llm_latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  response_generation_time_ms: number;
  retrieval_metrics?: RetrievalMetrics;
}

export interface AnswerResponse {
  answer: string;
  summary: string;
  citations: Citation[];
  confidence: number;
  decision: EvidenceDecision;
  reasoning: string;
  execution_metrics: ExecutionMetrics;
}

export interface EvaluatedChunk {
  chunk_id: string;
  source: string;
  source_type: string;
  score: number;
  relevance_score: number;
  authority_score: number;
  freshness_score: number;
  directness_score: number;
  confidence_score: number;
  explanation: string;
  content: string;
  metadata: Record<string, any>;
}

export interface Conflict {
  conflicting_chunks: string[];
  conflicting_fields: string[];
  severity: "low" | "medium" | "high" | string;
  explanation: string;
}

export interface EvidenceSummary {
  average_confidence: number;
  highest_confidence: number;
  lowest_confidence: number;
  total_evaluated_chunks: number;
  strongest_evidence?: any[];
  supporting_sources?: string[];
  conflicting_sources?: string[];
}

export interface EvidenceEvaluationResponse {
  evaluated_chunks: EvaluatedChunk[];
  evidence_summary: EvidenceSummary;
  conflicts: Conflict[];
  confidence: number;
  decision: EvidenceDecision;
  needs_more_retrieval: boolean;
  evaluation_explanation: string;
  retrieval_metrics: RetrievalMetrics;
}

export interface QueryAnalysisData {
  query: string;
  intent: string;
  keywords: string[];
  entities: string[];
  expected_information_type: string;
  preferred_sources: string[];
}

export interface RankedSourceData {
  source_id: string;
  source_name: string;
  source_type: string;
  relevance_score: number;
  authority_score: number;
  freshness_score: number;
  expected_directness_score: number;
  overall_score: number;
  selection_reason: string;
  is_selected: boolean;
}

export interface QueryDecisionResponse {
  query_analysis: QueryAnalysisData;
  selected_sources: RankedSourceData[];
  skipped_sources: RankedSourceData[];
  selection_reasons: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  answerResponse?: AnswerResponse;
  evaluationResponse?: EvidenceEvaluationResponse;
  queryDecision?: QueryDecisionResponse;
}

export interface PipelineStage {
  id: string;
  title: string;
  description: string;
  status: "pending" | "running" | "completed" | "warning" | "error";
  details?: Record<string, any>;
  durationMs?: number;
}


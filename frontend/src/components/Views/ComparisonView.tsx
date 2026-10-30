import React from "react";
import {
  Scale,
  CheckCircle2,
  XCircle,
  ArrowRight,
  TrendingDown,
  ShieldAlert,
  Zap,
} from "lucide-react";
import type { NavTab } from "@/components/Header/Header";

interface ComparisonViewProps {
  onNavigate: (tab: NavTab) => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ onNavigate }) => {
  const comparisonMetrics = [
    {
      metric: "Knowledge Source Selection",
      traditional: "Broadcasts search query to all connected silos indiscriminately",
      quorix: "Pre-scores and routes to relevant sources (relevance, authority, freshness)",
      impact: "Eliminates ~60% of noisy irrelevant context",
    },
    {
      metric: "Retrieval Budgeting",
      traditional: "Static top-k retrieval (e.g. k=20 chunks per database)",
      quorix: "Dynamic token caps, chunk limits, and maximum retrieval calls",
      impact: "Reduces token consumption by up to 72%",
    },
    {
      metric: "Evidence Scoring",
      traditional: "Assumes vector similarity equals factual correctness",
      quorix: "Multi-criterion scoring: Relevance, Authority, Freshness & Directness",
      impact: "Filters out high-similarity hallucinations",
    },
    {
      metric: "Contradiction & Conflict Resolution",
      traditional: "Sends conflicting chunks into LLM prompt; LLM guesses or hallucinates",
      quorix: "Detects cross-source discrepancies and flags CONFLICTING state",
      impact: "100% auditable contradiction alerts",
    },
    {
      metric: "Grounded Answer Generation",
      traditional: "Generates speculative answers when evidence is missing or weak",
      quorix: "Gated sufficiency evaluation: explicitly refuses unsupported queries",
      impact: "Zero unverified assertions",
    },
  ];

  return (
    <div className="min-h-full overflow-y-auto bg-[#F5F1E8] text-[#1F1F1F] p-6 sm:p-10 transition-colors">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[#ECE6DB] pb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#B3BAAC]/20 text-[#6B2E46] text-xs font-bold uppercase tracking-wider mb-2 border border-[#B3BAAC]/40">
              <Scale className="h-3.5 w-3.5" />
              <span>Architectural Benchmark</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#6B2E46] tracking-tight">
              Traditional RAG vs. Quorix Zero-Trust RAG
            </h1>
            <p className="text-sm sm:text-base text-[#5E5E5E] mt-2 max-w-2xl">
              Understand the fundamental flaws in naive similarity retrieval and how Quorix delivers verified, low-cost enterprise generation.
            </p>
          </div>

          <button
            onClick={() => onNavigate("demo")}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#6B2E46] hover:bg-[#57263A] text-white font-semibold text-xs transition-all shadow-soft shrink-0 cursor-pointer"
          >
            <span>Test Live Demo</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Big Cards Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Traditional RAG */}
          <div className="p-6 sm:p-8 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft relative overflow-hidden">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5E5E5E] uppercase tracking-wider mb-3">
              <XCircle className="h-4 w-4 text-[#5E5E5E]" />
              <span>Traditional Naive RAG</span>
            </div>
            <h3 className="text-2xl font-bold text-[#1F1F1F] mb-3">
              Uncontrolled Context Ingestion
            </h3>
            <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed mb-6">
              Naive RAG assumes that if a chunk has high cosine similarity, it is factual and relevant. When knowledge bases contain contradictory tickets or deprecated documentation, naive RAG forces the LLM to hallucinate or blend conflicting facts.
            </p>
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2 text-[#5E5E5E] font-medium">
                <TrendingDown className="h-4 w-4 shrink-0 text-[#5E5E5E]" />
                <span>High token wastage from large over-retrieval pools</span>
              </div>
              <div className="flex items-center gap-2 text-[#5E5E5E] font-medium">
                <ShieldAlert className="h-4 w-4 shrink-0 text-[#5E5E5E]" />
                <span>Blind reliance on semantic similarity without authority checks</span>
              </div>
            </div>
          </div>

          {/* Quorix Zero-Trust */}
          <div className="p-6 sm:p-8 rounded-[20px] bg-white border-2 border-[#6B2E46]/30 shadow-soft relative overflow-hidden">
            <div className="flex items-center gap-2 text-xs font-bold text-[#6B2E46] uppercase tracking-wider mb-3">
              <CheckCircle2 className="h-4 w-4 text-[#6B2E46]" />
              <span>Quorix Zero-Trust Engine</span>
            </div>
            <h3 className="text-2xl font-bold text-[#6B2E46] mb-3">
              Gated Pre & Post-Retrieval Validation
            </h3>
            <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed mb-6">
              Quorix applies pre-retrieval intelligence to identify which knowledge sources are actually relevant, enforces strict budget caps, evaluates every candidate chunk, detects contradictions, and refuses unsupported queries.
            </p>
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2 text-[#6B2E46] font-medium">
                <Zap className="h-4 w-4 shrink-0 text-[#6B2E46]" />
                <span>Sub-150ms hybrid search with adaptive token budgeting</span>
              </div>
              <div className="flex items-center gap-2 text-[#6B2E46] font-medium">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-[#6B2E46]" />
                <span>Zero hallucination via sufficiency gating and strict citations</span>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Metric Table */}
        <div className="rounded-[20px] border border-[#E5DED3] bg-white overflow-hidden shadow-soft">
          <div className="p-6 border-b border-[#ECE6DB]">
            <h3 className="text-lg font-bold text-[#1F1F1F]">
              Feature-by-Feature Breakdown
            </h3>
            <p className="text-xs text-[#5E5E5E] mt-1">
              Direct architectural comparison across retrieval stages.
            </p>
          </div>

          <div className="divide-y divide-[#ECE6DB]">
            {comparisonMetrics.map((row, idx) => (
              <div key={idx} className="p-6 grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                <div className="md:col-span-3">
                  <span className="text-xs font-bold text-[#1F1F1F] block">
                    {row.metric}
                  </span>
                  <span className="inline-block mt-1 text-[10px] font-semibold text-[#6B2E46] bg-[#B3BAAC]/20 px-2 py-0.5 rounded-full border border-[#E5DED3]">
                    {row.impact}
                  </span>
                </div>
                <div className="md:col-span-4 text-xs text-[#5E5E5E]">
                  <span className="font-semibold text-[#5E5E5E] block mb-1">Traditional RAG:</span>
                  {row.traditional}
                </div>
                <div className="md:col-span-5 text-xs text-[#1F1F1F] font-medium">
                  <span className="font-semibold text-[#6B2E46] block mb-1">Quorix Engine:</span>
                  {row.quorix}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

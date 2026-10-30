import React from "react";
import {
  Layers,
  Database,
  Cpu,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Compass,
} from "lucide-react";
import type { NavTab } from "@/components/Header/Header";

interface ArchitectureViewProps {
  onNavigate: (tab: NavTab) => void;
}

export const ArchitectureView: React.FC<ArchitectureViewProps> = ({ onNavigate }) => {
  const phases = [
    {
      phase: "Phase 1 & 2",
      title: "Data Models & Ingestion Pipeline",
      icon: Database,
      description:
        "Normalizes heterogeneous enterprise records into uniform chunks with authority levels, timestamps, and metadata tags.",
      bullets: [
        "DocumentAdapter: Markdown specs, architecture decision records (ADRs), guides",
        "ConversationAdapter: Slack threads, team discussions, design reviews",
        "TicketAdapter: Jira issues, GitHub PRs, bug tracking and resolution notes",
      ],
    },
    {
      phase: "Phase 3",
      title: "Query Analysis & Source Selection",
      icon: Compass,
      description:
        "Deconstructs questions before database execution, scoring knowledge silos using multi-criterion authority weights.",
      bullets: [
        "Intent classification (Architectural, Troubleshooting, Configuration, General)",
        "Keyword & entity extraction with preferred source type alignment",
        "Source routing: filters out irrelevant repositories before retrieval begins",
      ],
    },
    {
      phase: "Phase 4",
      title: "Retrieval Budget Manager & Hybrid Engine",
      icon: Cpu,
      description:
        "Executes budget-bounded search across Qdrant vector embeddings and BM25 lexical keyword indexes.",
      bullets: [
        "Retrieval Budget Manager: allocates chunk caps, call quotas, and token maximums",
        "Dense vector search in Qdrant (SentenceTransformer embeddings)",
        "BM25 lexical search with Reciprocal Rank Fusion and chunk deduplication",
      ],
    },
    {
      phase: "Phase 5",
      title: "Evidence Intelligence & Sufficiency Evaluation",
      icon: ShieldCheck,
      description:
        "Every retrieved chunk is independently evaluated before anything is sent to the LLM.",
      bullets: [
        "Multi-criterion evidence scoring: Relevance (35%), Authority (25%), Freshness (20%), Directness (20%)",
        "Conflict Detection: identifies architectural and temporal contradictions across sources",
        "Sufficiency gating: SUFFICIENT, CONFLICTING, INSUFFICIENT, or UNSUPPORTED verdict",
      ],
    },
    {
      phase: "Phase 6",
      title: "Answer Generation & Citation Engine",
      icon: Sparkles,
      description:
        "Synthesizes answers exclusively from validated evidence, anchoring claims to exact cited chunks.",
      bullets: [
        "Strict prompt boundaries: zero fabrication, uncertainty acknowledgment",
        "Gemini 2.0 Flash integration with token tracking and cost estimation",
        "Structured citations linking claims to chunk IDs and source references",
      ],
    },
  ];

  return (
    <div className="min-h-full overflow-y-auto bg-[#F5F1E8] text-[#1F1F1F] p-6 sm:p-10 transition-colors">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[#ECE6DB] pb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#B3BAAC]/20 text-[#6B2E46] text-xs font-bold uppercase tracking-wider mb-2 border border-[#B3BAAC]/40">
              <Layers className="h-3.5 w-3.5" />
              <span>Pipeline Deep Dive</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#6B2E46] tracking-tight">
              Quorix System Architecture
            </h1>
            <p className="text-sm sm:text-base text-[#5E5E5E] mt-2 max-w-2xl">
              Inspect the five foundational phases of Quorix's zero-trust retrieval pipeline.
            </p>
          </div>

          <button
            onClick={() => onNavigate("demo")}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#6B2E46] hover:bg-[#57263A] text-white font-semibold text-xs transition-all shadow-soft shrink-0 cursor-pointer"
          >
            <span>Launch Interactive Demo</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Phase Timeline Cards */}
        <div className="space-y-6">
          {phases.map((p, idx) => {
            const Icon = p.icon;

            return (
              <div
                key={idx}
                className="p-6 sm:p-8 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:border-[#B3BAAC] transition-all relative overflow-hidden"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46]">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B2E46]">
                        {p.phase}
                      </span>
                      <h3 className="text-xl font-bold text-[#1F1F1F]">
                        {p.title}
                      </h3>
                    </div>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed mb-4">
                  {p.description}
                </p>

                <div className="space-y-2 pt-2 border-t border-[#ECE6DB]">
                  {p.bullets.map((b, bIdx) => (
                    <div key={bIdx} className="flex items-start gap-2 text-xs text-[#5E5E5E]">
                      <span className="text-[#6B2E46] font-bold">•</span>
                      <span>{b}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

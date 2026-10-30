import React from "react";
import { Database, Layers, ShieldCheck, ArrowRight, BookOpen, Clock } from "lucide-react";

interface LandingHeroProps {
  onSelectQuestion: (question: string) => void;
}

const SUGGESTED_QUESTIONS = [
  {
    icon: Database,
    title: "Historical Architecture Reason",
    query: "Why was Redis caching introduced?",
    desc: "Examines architectural decisions across documents & engineering discussions",
  },
  {
    icon: Layers,
    title: "Configuration Lookup",
    query: "What is the Redis cache TTL?",
    desc: "Extracts configuration parameters and tests conflict detection between sources",
  },
  {
    icon: BookOpen,
    title: "Implementation Details",
    query: "How does authentication work?",
    desc: "Queries technical documentation for auth flow and token validation logic",
  },
  {
    icon: Clock,
    title: "Feature Information",
    query: "What is the latest deployment process?",
    desc: "Evaluates freshness of deployment procedures across repositories",
  },
];

export const LandingHero: React.FC<LandingHeroProps> = ({ onSelectQuestion }) => {
  return (
    <div className="flex flex-col items-center justify-center max-w-3xl mx-auto px-4 py-12 text-center animate-fade-in">
      {/* Brand Logo Node (Deep Burgundy, no glow) */}
      <div className="relative mb-6">
        <div className="relative h-20 w-20 rounded-2xl bg-[#6B2E46] flex items-center justify-center shadow-soft text-white font-extrabold text-4xl">
          Q
        </div>
      </div>

      {/* Main Titles */}
      <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-[#6B2E46] mb-3">
        Quorix
      </h1>
      <p className="text-lg sm:text-xl font-medium text-[#1F1F1F] mb-2">
        Intelligent Context Selection & Retrieval Optimization Engine
      </p>
      <p className="text-sm text-[#5E5E5E] max-w-xl mb-10 leading-relaxed font-normal">
        Unlike conventional RAG, Quorix never assumes retrieved context is trustworthy. It scores relevance, authority, directness & freshness, detects contradictions, and bounds retrieval costs before generating grounded responses.
      </p>

      {/* Core Highlights */}
      <div className="flex flex-wrap items-center justify-center gap-2 mb-10 text-xs text-[#1F1F1F]">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[#E5DED3] shadow-soft-sm">
          <ShieldCheck className="h-3.5 w-3.5 text-[#6B2E46]" />
          <span>Multi-Criterion Evidence Scoring</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[#E5DED3] shadow-soft-sm">
          <Layers className="h-3.5 w-3.5 text-[#6B2E46]" />
          <span>Factual Conflict Detection</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[#E5DED3] shadow-soft-sm">
          <Database className="h-3.5 w-3.5 text-[#6B2E46]" />
          <span>Adaptive Retrieval Budget</span>
        </div>
      </div>

      {/* Suggested Questions Grid */}
      <div className="w-full">
        <div className="text-left text-xs font-semibold text-[#5E5E5E] uppercase tracking-wider mb-3 px-1">
          Explore retrieval capabilities
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          {SUGGESTED_QUESTIONS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => onSelectQuestion(item.query)}
                className="group p-4 rounded-[20px] border border-[#E5DED3] bg-white hover:border-[#6B2E46] shadow-soft transition-all text-left flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[11px] font-semibold text-[#6B2E46] flex items-center gap-1.5">
                      <Icon className="h-3.5 w-3.5 text-[#6B2E46]" />
                      {item.title}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-[#B3BAAC] group-hover:text-[#6B2E46] group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <h3 className="text-sm font-semibold text-[#1F1F1F] mb-1 group-hover:text-[#6B2E46] transition-colors">
                    "{item.query}"
                  </h3>
                  <p className="text-xs text-[#5E5E5E] line-clamp-2">
                    {item.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

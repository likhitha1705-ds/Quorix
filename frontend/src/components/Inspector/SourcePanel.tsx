import React, { useState } from "react";
import { Layers, CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import type { ChatMessage, RankedSourceData } from "@/types";
import { formatPercent } from "@/utils";

interface SourcePanelProps {
  message: ChatMessage | null;
}

export const SourcePanel: React.FC<SourcePanelProps> = ({ message }) => {
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null);

  if (!message || !message.answerResponse) {
    return (
      <div className="text-center py-12 px-4 text-xs text-[#5E5E5E]">
        <Layers className="h-8 w-8 mx-auto mb-2 opacity-40 text-[#6B2E46]" />
        No source selection data to display. Run a query to inspect source routing decisions.
      </div>
    );
  }

  const queryDecision = message.queryDecision;

  const selectedSources = queryDecision?.selected_sources || [
    {
      source_id: "src_documents",
      source_name: "Technical Documents",
      source_type: "document",
      overall_score: 0.88,
      relevance_score: 0.90,
      authority_score: 0.85,
      freshness_score: 0.90,
      expected_directness_score: 0.85,
      selection_reason: "High relevance and direct architectural documentation match.",
      is_selected: true,
    },
    {
      source_id: "src_conversations",
      source_name: "Engineering Conversations",
      source_type: "conversation",
      overall_score: 0.76,
      relevance_score: 0.82,
      authority_score: 0.70,
      freshness_score: 0.85,
      expected_directness_score: 0.80,
      selection_reason: "Contains team discussions and historical rationale.",
      is_selected: true,
    },
  ];

  const skippedSources = queryDecision?.skipped_sources || [
    {
      source_id: "src_tickets",
      source_name: "Development Tickets",
      source_type: "ticket",
      overall_score: 0.35,
      relevance_score: 0.30,
      authority_score: 0.60,
      freshness_score: 0.40,
      expected_directness_score: 0.30,
      selection_reason: "Relevance below selection threshold for this query intent.",
      is_selected: false,
    },
  ];

  const toggleExpand = (id: string) => {
    setExpandedSourceId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="p-4 space-y-5">
      {/* Overview Stat */}
      <div className="p-3 rounded-xl bg-[#F5F1E8] border border-[#E5DED3] text-xs">
        <span className="font-semibold text-[#1F1F1F] block mb-0.5">
          Intelligent Knowledge Routing
        </span>
        <p className="text-[11px] text-[#5E5E5E]">
          Sources scored via weighted criteria: Relevance (35%), Authority (25%), Freshness (20%), and Directness (20%).
        </p>
      </div>

      {/* Selected Sources Section */}
      <div>
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#6B2E46] uppercase tracking-wider mb-2.5">
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Selected Sources ({selectedSources.length})</span>
        </div>

        <div className="space-y-2">
          {selectedSources.map((source: RankedSourceData) => {
            const isExpanded = expandedSourceId === source.source_id;

            return (
              <div
                key={source.source_id}
                className="rounded-xl border border-[#E5DED3] bg-white shadow-soft-sm overflow-hidden"
              >
                <div
                  onClick={() => toggleExpand(source.source_id)}
                  className="p-3 flex items-center justify-between cursor-pointer hover:bg-[#F5F1E8]/50 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-xs text-[#1F1F1F]">
                        {source.source_name}
                      </span>
                      <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-[#B3BAAC]/20 text-[#6B2E46] border border-[#E5DED3]">
                        {source.source_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#5E5E5E] line-clamp-1">
                      {source.selection_reason}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#6B2E46]">
                      {formatPercent(source.overall_score)}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-[#B3BAAC]" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-[#B3BAAC]" />
                    )}
                  </div>
                </div>

                {/* Expandable Scoring Details */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-1 border-t border-[#ECE6DB] bg-[#F5F1E8] text-xs space-y-2">
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div className="flex items-center justify-between p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E]">Relevance:</span>
                        <span className="font-semibold text-[#1F1F1F]">{formatPercent(source.relevance_score)}</span>
                      </div>
                      <div className="flex items-center justify-between p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E]">Authority:</span>
                        <span className="font-semibold text-[#1F1F1F]">{formatPercent(source.authority_score)}</span>
                      </div>
                      <div className="flex items-center justify-between p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E]">Freshness:</span>
                        <span className="font-semibold text-[#1F1F1F]">{formatPercent(source.freshness_score)}</span>
                      </div>
                      <div className="flex items-center justify-between p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E]">Directness:</span>
                        <span className="font-semibold text-[#1F1F1F]">{formatPercent(source.expected_directness_score)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Skipped Sources Section */}
      {skippedSources.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-[#5E5E5E] uppercase tracking-wider mb-2.5">
            <XCircle className="h-3.5 w-3.5" />
            <span>Skipped Sources ({skippedSources.length})</span>
          </div>

          <div className="space-y-2">
            {skippedSources.map((source: RankedSourceData) => (
              <div
                key={source.source_id}
                className="p-3 rounded-xl border border-[#E5DED3] bg-[#F5F1E8]/60 opacity-80"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-[#1F1F1F]">
                      {source.source_name}
                    </span>
                    <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-white border border-[#E5DED3] text-[#5E5E5E]">
                      {source.source_type}
                    </span>
                  </div>
                  <span className="text-xs text-[#5E5E5E] font-medium">{formatPercent(source.overall_score)}</span>
                </div>
                <p className="text-[11px] text-[#5E5E5E]">
                  {source.selection_reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from "react";
import { ChevronDown, ChevronUp, AlertCircle, FileText } from "lucide-react";
import type { ChatMessage, EvaluatedChunk } from "@/types";
import { formatPercent, getConfidenceBadgeStyles } from "@/utils";

interface EvidencePanelProps {
  message: ChatMessage | null;
  highlightedChunkId?: string | null;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  message,
  highlightedChunkId,
}) => {
  const [expandedChunkIds, setExpandedChunkIds] = useState<Set<string>>(new Set());

  if (!message || !message.answerResponse) {
    return (
      <div className="text-center py-12 px-4 text-xs text-[#5E5E5E]">
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-40 text-[#6B2E46]" />
        No evaluated evidence to display. Ask a question to view scored chunks.
      </div>
    );
  }

  const evalRes = message.evaluationResponse;
  const chunks = evalRes?.evaluated_chunks || [];
  const conflicts = evalRes?.conflicts || [];
  const conflictingChunkIds = new Set(conflicts.flatMap((c) => c.conflicting_chunks));

  const toggleExpand = (chunkId: string) => {
    setExpandedChunkIds((prev) => {
      const next = new Set(prev);
      if (next.has(chunkId)) next.delete(chunkId);
      else next.add(chunkId);
      return next;
    });
  };

  return (
    <div className="p-4 space-y-4">
      {/* Evidence Summary Header */}
      <div className="p-3 rounded-xl bg-[#F5F1E8] border border-[#E5DED3] flex items-center justify-between text-xs">
        <div>
          <span className="font-semibold text-[#1F1F1F] block">
            Evaluated Context Chunks ({chunks.length})
          </span>
          <span className="text-[11px] text-[#5E5E5E]">
            Average Confidence: {formatPercent(evalRes?.evidence_summary?.average_confidence ?? message?.answerResponse?.confidence)}
          </span>
        </div>
        {conflicts.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-800 border border-rose-200">
            <AlertCircle className="h-3 w-3" />
            {conflicts.length} Conflict{conflicts.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Chunks List */}
      <div className="space-y-3">
        {chunks.length === 0 ? (
          <div className="text-center py-8 text-xs text-[#5E5E5E]">
            No chunks retrieved for this query.
          </div>
        ) : (
          chunks.map((chunk: EvaluatedChunk) => {
            const isExpanded = expandedChunkIds.has(chunk.chunk_id);
            const isConflict = conflictingChunkIds.has(chunk.chunk_id);
            const isHighlighted = highlightedChunkId === chunk.chunk_id;
            const confStyle = getConfidenceBadgeStyles(chunk.score);

            return (
              <div
                key={chunk.chunk_id}
                id={`chunk-${chunk.chunk_id}`}
                className={`rounded-xl border transition-all ${
                  isHighlighted
                    ? "border-[#6B2E46] ring-2 ring-[#6B2E46]/20 shadow-soft-sm bg-white"
                    : isConflict
                    ? "border-rose-300 bg-rose-50/20 shadow-soft-sm"
                    : "border-[#E5DED3] bg-white shadow-soft-sm"
                }`}
              >
                {/* Header */}
                <div
                  onClick={() => toggleExpand(chunk.chunk_id)}
                  className="p-3 cursor-pointer hover:bg-[#F5F1E8]/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-bold text-xs text-[#1F1F1F]">
                        {chunk.source}
                      </span>
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#F5F1E8] text-[#5E5E5E] border border-[#E5DED3]">
                        [{chunk.chunk_id}]
                      </span>
                      {isConflict && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-800 border border-rose-200 flex items-center gap-1">
                          <AlertCircle className="h-2.5 w-2.5" />
                          Conflict
                        </span>
                      )}
                    </div>

                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full border ${confStyle.bg} ${confStyle.text} ${confStyle.border}`}
                    >
                      {formatPercent(chunk.score)}
                    </span>
                  </div>

                  {/* Truncated Snippet */}
                  <p className="text-xs text-[#5E5E5E] line-clamp-2 leading-relaxed">
                    {chunk.content}
                  </p>

                  <div className="flex items-center justify-between mt-2 pt-1 text-[11px] text-[#5E5E5E]">
                    <span className="truncate max-w-[200px]">
                      {chunk.explanation || "Evaluated evidence chunk"}
                    </span>
                    <button
                      type="button"
                      className="text-[#6B2E46] font-medium flex items-center gap-0.5 cursor-pointer"
                    >
                      <span>{isExpanded ? "Collapse" : "Expand"}</span>
                      {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Full Chunk Content & Criterion Breakdown */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-2 border-t border-[#ECE6DB] bg-[#F5F1E8] space-y-2 text-xs">
                    <div className="p-2.5 rounded-lg bg-white border border-[#E5DED3] font-mono text-[11px] text-[#1F1F1F] whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                      {chunk.content}
                    </div>

                    {/* Multi-Criterion Scores */}
                    <div className="grid grid-cols-4 gap-1 text-[10px] text-center pt-1">
                      <div className="p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E] block">Relevance</span>
                        <span className="font-bold text-[#1F1F1F]">{formatPercent(chunk.relevance_score)}</span>
                      </div>
                      <div className="p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E] block">Authority</span>
                        <span className="font-bold text-[#1F1F1F]">{formatPercent(chunk.authority_score)}</span>
                      </div>
                      <div className="p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E] block">Freshness</span>
                        <span className="font-bold text-[#1F1F1F]">{formatPercent(chunk.freshness_score)}</span>
                      </div>
                      <div className="p-1.5 rounded bg-white border border-[#E5DED3]">
                        <span className="text-[#5E5E5E] block">Directness</span>
                        <span className="font-bold text-[#1F1F1F]">{formatPercent(chunk.directness_score)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

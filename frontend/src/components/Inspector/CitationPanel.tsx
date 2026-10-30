import React from "react";
import { Quote, ArrowRight } from "lucide-react";
import type { ChatMessage, Citation } from "@/types";
import { formatPercent, getConfidenceBadgeStyles } from "@/utils";

interface CitationPanelProps {
  message: ChatMessage | null;
  onSelectCitation?: (chunkId: string) => void;
}

export const CitationPanel: React.FC<CitationPanelProps> = ({
  message,
  onSelectCitation,
}) => {
  if (!message || !message.answerResponse) {
    return (
      <div className="text-center py-12 px-4 text-xs text-[#5E5E5E]">
        <Quote className="h-8 w-8 mx-auto mb-2 opacity-40 text-[#6B2E46]" />
        No citations to display yet. Submit a query to see grounded citations.
      </div>
    );
  }

  const citations = message.answerResponse.citations || [];

  return (
    <div className="p-4 space-y-4">
      <div className="p-3 rounded-xl bg-[#F5F1E8] border border-[#E5DED3] text-xs">
        <span className="font-semibold text-[#1F1F1F] block mb-0.5">
          Grounded Attributions ({citations.length})
        </span>
        <p className="text-[11px] text-[#5E5E5E]">
          Every assertion in the answer links to verified evidence. Click any citation to inspect its source chunk.
        </p>
      </div>

      <div className="space-y-2.5">
        {citations.length === 0 ? (
          <div className="text-center py-8 text-xs text-[#5E5E5E]">
            No citations required or available for this response.
          </div>
        ) : (
          citations.map((cit: Citation, idx: number) => {
            const confStyle = getConfidenceBadgeStyles(cit.confidence_score);

            return (
              <div
                key={idx}
                onClick={() => onSelectCitation?.(cit.chunk_id)}
                className="p-3.5 rounded-xl border border-[#E5DED3] bg-white shadow-soft-sm hover:border-[#6B2E46] transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[#1F1F1F] group-hover:text-[#6B2E46] transition-colors">
                      {cit.source_name}
                    </span>
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-[#B3BAAC]/20 text-[#6B2E46] border border-[#E5DED3]">
                      {cit.source_type}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border ${confStyle.bg} ${confStyle.text} ${confStyle.border}`}
                  >
                    {formatPercent(cit.confidence_score)}
                  </span>
                </div>

                <div className="text-xs text-[#5E5E5E] italic mb-2 line-clamp-3 bg-[#F5F1E8] p-2 rounded-lg border border-[#E5DED3]">
                  "{cit.quote || "Direct supporting claim verified by retrieval engine."}"
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#5E5E5E]">
                  <span className="font-mono">Chunk ID: {cit.chunk_id}</span>
                  <span className="text-[#6B2E46] font-medium flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    <span>View in Evidence</span>
                    <ArrowRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

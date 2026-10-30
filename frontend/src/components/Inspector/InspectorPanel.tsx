import React, { useState } from "react";
import { X, Layers, FileText, Quote, BarChart3, Activity } from "lucide-react";
import type { ChatMessage } from "@/types";
import { DecisionTrace } from "./DecisionTrace";
import { SourcePanel } from "./SourcePanel";
import { EvidencePanel } from "./EvidencePanel";
import { CitationPanel } from "./CitationPanel";
import { MetricsPanel } from "./MetricsPanel";

export type InspectorTab = "trace" | "sources" | "evidence" | "citations" | "metrics";

interface InspectorPanelProps {
  message: ChatMessage | null;
  activeTab: InspectorTab;
  onTabChange: (tab: InspectorTab) => void;
  onClose: () => void;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  message,
  activeTab,
  onTabChange,
  onClose,
}) => {
  const [highlightedChunkId, setHighlightedChunkId] = useState<string | null>(null);

  const handleCitationSelect = (chunkId: string) => {
    setHighlightedChunkId(chunkId);
    onTabChange("evidence");

    // Scroll to the element after state update
    setTimeout(() => {
      const el = document.getElementById(`chunk-${chunkId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 100);
  };

  const tabs: { id: InspectorTab; label: string; icon: React.ElementType }[] = [
    { id: "trace", label: "Trace", icon: Activity },
    { id: "sources", label: "Sources", icon: Layers },
    { id: "evidence", label: "Evidence", icon: FileText },
    { id: "citations", label: "Citations", icon: Quote },
    { id: "metrics", label: "Metrics", icon: BarChart3 },
  ];

  return (
    <aside className="w-80 md:w-96 border-l border-[#E5DED3] bg-white flex flex-col h-[calc(100vh-3.5rem)] shrink-0 z-10 transition-colors shadow-soft">
      {/* Header with Title and Tabs */}
      <div className="border-b border-[#E5DED3] p-3 bg-[#F5F1E8]">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-xs uppercase tracking-wider text-[#6B2E46]">
              Intelligence Inspector
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#5E5E5E] hover:text-[#1F1F1F] hover:bg-[#B3BAAC]/20 transition-colors cursor-pointer"
            title="Close Inspector"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tab Navigation Buttons (Muted Sage Grey background, White active pill) */}
        <div className="grid grid-cols-5 gap-1 p-1 bg-[#B3BAAC] rounded-xl text-xs font-semibold">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex flex-col sm:flex-row items-center justify-center gap-1 py-1.5 px-1 rounded-lg transition-all cursor-pointer ${
                  isActive
                    ? "bg-white text-[#6B2E46] shadow-soft-sm font-bold"
                    : "text-[#1F1F1F] hover:bg-[#C5CCC0]"
                }`}
                title={tab.label}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="text-[10px] sm:text-[11px] truncate">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panels Body */}
      <div className="flex-1 overflow-y-auto bg-white">
        {activeTab === "trace" && <DecisionTrace message={message} />}
        {activeTab === "sources" && <SourcePanel message={message} />}
        {activeTab === "evidence" && (
          <EvidencePanel
            message={message}
            highlightedChunkId={highlightedChunkId}
          />
        )}
        {activeTab === "citations" && (
          <CitationPanel
            message={message}
            onSelectCitation={handleCitationSelect}
          />
        )}
        {activeTab === "metrics" && <MetricsPanel message={message} />}
      </div>
    </aside>
  );
};

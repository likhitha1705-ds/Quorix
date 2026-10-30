import React from "react";
import { Plus, MessageSquare, Trash2, ShieldCheck, ChevronRight } from "lucide-react";
import type { ChatMessage } from "@/types";

interface SidebarProps {
  messages: ChatMessage[];
  onNewChat: () => void;
  onSelectMessage?: (message: ChatMessage) => void;
  activeMessageId?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  messages,
  onNewChat,
  onSelectMessage,
  activeMessageId,
}) => {
  // Extract user queries as conversation history
  const userQueries = messages.filter((m) => m.role === "user");

  return (
    <aside className="w-64 border-r border-[#E5DED3] bg-[#F5F1E8] flex flex-col justify-between h-[calc(100vh-3.5rem)] shrink-0 select-none transition-colors">
      {/* Top Section */}
      <div className="p-3 flex flex-col gap-3 overflow-hidden">
        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="flex items-center justify-center gap-2 w-full py-2.5 px-3 bg-[#6B2E46] hover:bg-[#57263A] active:bg-[#4A2030] text-white font-medium text-sm rounded-xl shadow-soft-sm transition-all cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>New Query</span>
        </button>

        {/* History Header */}
        <div className="flex items-center justify-between px-2 pt-2 text-[11px] font-semibold uppercase tracking-wider text-[#5E5E5E]">
          <span>Recent Queries</span>
          <span>{userQueries.length}</span>
        </div>

        {/* Query List */}
        <div className="flex flex-col gap-1 overflow-y-auto max-h-[calc(100vh-19rem)] pr-1">
          {userQueries.length === 0 ? (
            <div className="text-center py-8 px-4 text-xs text-[#5E5E5E]">
              <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-40 text-[#B3BAAC]" />
              No queries yet. Start a conversation to explore retrieval intelligence.
            </div>
          ) : (
            userQueries.map((q, idx) => {
              // Find matching assistant response
              const nextMsg = messages[messages.indexOf(q) + 1];
              const isSelected = activeMessageId === nextMsg?.id;

              return (
                <button
                  key={q.id || idx}
                  onClick={() => nextMsg && onSelectMessage?.(nextMsg)}
                  className={`flex items-center gap-2 text-left px-2.5 py-2 rounded-lg text-xs transition-colors cursor-pointer group ${
                    isSelected
                      ? "bg-white text-[#6B2E46] border border-[#E5DED3] font-semibold shadow-soft-sm"
                      : "text-[#5E5E5E] hover:bg-[#B3BAAC]/20 hover:text-[#1F1F1F]"
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-60 group-hover:opacity-100 text-[#6B2E46]" />
                  <span className="truncate flex-1">{q.content}</span>
                  <ChevronRight className="h-3 w-3 opacity-0 group-hover:opacity-60 transition-opacity" />
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Bottom Section: Quorix Architecture Badges & Settings */}
      <div className="p-3 border-t border-[#ECE6DB] flex flex-col gap-2 bg-[#F5F1E8]">
        <div className="p-2.5 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm text-xs">
          <div className="flex items-center gap-1.5 font-semibold text-[#1F1F1F] mb-1">
            <ShieldCheck className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Zero-Trust RAG Pipeline</span>
          </div>
          <p className="text-[11px] text-[#5E5E5E] leading-relaxed">
            Multi-criterion evidence scoring, conflict detection & budget management.
          </p>
        </div>

        {/* Clear History */}
        {userQueries.length > 0 && (
          <button
            onClick={onNewChat}
            className="flex items-center gap-2 px-2.5 py-1.5 text-xs text-[#6B2E46] hover:bg-[#B3BAAC]/20 rounded-lg transition-colors cursor-pointer font-medium"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Clear Session</span>
          </button>
        )}
      </div>
    </aside>
  );
};

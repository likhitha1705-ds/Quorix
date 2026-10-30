import React, { useState, useRef, useEffect } from "react";
import { Send, Loader2, Sparkles, X } from "lucide-react";

interface QueryInputProps {
  onSend: (query: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSend,
  isLoading,
  disabled = false,
}) => {
  const [query, setQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [query]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim() || isLoading || disabled) return;
    onSend(query.trim());
    setQuery("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-4xl mx-auto px-4 pb-4">
      <div className="relative flex items-end gap-2 p-2 rounded-2xl border border-[#E5DED3] bg-white shadow-soft focus-within:border-[#6B2E46] transition-all">
        {/* Input Textarea */}
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a technical, architectural, or configuration question..."
          rows={1}
          disabled={isLoading || disabled}
          className="flex-1 max-h-44 p-2 bg-transparent text-sm text-[#1F1F1F] placeholder:text-[#5E5E5E] focus:outline-none resize-none leading-relaxed"
        />

        {/* Clear query button if text present */}
        {query.length > 0 && !isLoading && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="p-1.5 text-[#5E5E5E] hover:text-[#1F1F1F] transition-colors"
            title="Clear input"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {/* Send Button */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading || disabled}
          className={`flex items-center justify-center h-9 w-9 rounded-xl transition-all cursor-pointer ${
            !query.trim() || isLoading || disabled
              ? "bg-[#B3BAAC]/20 text-[#B3BAAC] cursor-not-allowed"
              : "bg-[#6B2E46] hover:bg-[#57263A] active:bg-[#4A2030] text-white shadow-soft-sm"
          }`}
          aria-label="Send query"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Footer Hints */}
      <div className="flex items-center justify-between text-[11px] text-[#5E5E5E] mt-1.5 px-2">
        <span className="flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-[#6B2E46]" />
          <span>Intelligent retrieval with source selection & conflict detection</span>
        </span>
        <span className="hidden sm:inline">
          Press <kbd className="px-1 py-0.5 rounded bg-[#F5F1E8] border border-[#E5DED3] text-[10px] text-[#1F1F1F]">Enter ↵</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-[#F5F1E8] border border-[#E5DED3] text-[10px] text-[#1F1F1F]">Shift+Enter</kbd> for new line
        </span>
      </div>
    </form>
  );
};

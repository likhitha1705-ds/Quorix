import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  Copy,
  Check,
  Clock,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  User,
  Quote,
  AlertTriangle,
  RotateCw,
  Trash2,
} from "lucide-react";
import type { ChatMessage } from "@/types";
import {
  formatPercent,
  formatMs,
  formatTimestamp,
  getDecisionBadgeStyles,
  getConfidenceBadgeStyles,
} from "@/utils";

interface MessageItemProps {
  message: ChatMessage;
  userQueryForRetry?: string;
  onInspectMessage?: (message: ChatMessage, tab?: "trace" | "sources" | "evidence" | "citations" | "metrics") => void;
  onRetry?: (query: string) => void;
  onDismiss?: (id: string) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  userQueryForRetry,
  onInspectMessage,
  onRetry,
  onDismiss,
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";
  const answerRes = message.answerResponse;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 my-4 px-4 max-w-4xl mx-auto">
        <div className="flex flex-col items-end max-w-[85%] sm:max-w-[75%]">
          <div className="bg-[#6B2E46] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-soft-sm text-sm leading-relaxed">
            {message.content}
          </div>
          <span className="text-[10px] text-[#5E5E5E] mt-1 px-1">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>
        <div className="h-8 w-8 rounded-full bg-[#B3BAAC]/30 flex items-center justify-center text-[#1F1F1F] shrink-0">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }

  // Error Message View
  const isError = !answerRes && (message.content.includes("Error Encountered") || message.content.includes("timeout"));
  if (isError) {
    return (
      <div className="flex items-start gap-3 my-4 px-4 max-w-4xl mx-auto animate-fade-in">
        <div className="h-8 w-8 rounded-xl bg-white border border-[#E5DED3] text-[#6B2E46] flex items-center justify-center shrink-0 shadow-soft-sm">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="flex-1 overflow-hidden">
          <div className="bg-white border border-[#E5DED3] rounded-2xl rounded-tl-sm p-4 sm:p-5 shadow-soft text-[#1F1F1F]">
            <div className="prose prose-sm max-w-none text-[#1F1F1F] text-sm leading-relaxed mb-3">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#ECE6DB]">
              {userQueryForRetry && onRetry && (
                <button
                  onClick={() => onRetry(userQueryForRetry)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#6B2E46] hover:bg-[#57263A] text-white shadow-soft-sm transition-colors cursor-pointer"
                >
                  <RotateCw className="h-3.5 w-3.5" />
                  <span>Retry Query</span>
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={() => onDismiss(message.id)}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#5E5E5E] hover:text-[#1F1F1F] hover:bg-[#B3BAAC]/20 transition-colors cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Dismiss</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Assistant Response Card
  const decisionStyles = answerRes ? getDecisionBadgeStyles(answerRes.decision) : null;
  const confStyles = answerRes ? getConfidenceBadgeStyles(answerRes.confidence) : null;
  const metrics = answerRes?.execution_metrics;

  return (
    <div className="flex items-start gap-3 my-4 px-4 max-w-4xl mx-auto animate-fade-in">
      {/* Bot Avatar */}
      <div className="h-8 w-8 rounded-xl bg-[#6B2E46] flex items-center justify-center text-white shrink-0 shadow-soft-sm font-bold text-xs">
        Q
      </div>

      {/* Main Message Body & Response Card */}
      <div className="flex-1 overflow-hidden">
        <div className="bg-white border border-[#E5DED3] rounded-2xl rounded-tl-sm p-4 sm:p-5 shadow-soft transition-colors">
          {/* Top Metadata Badges */}
          {answerRes && decisionStyles && confStyles && (
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-[#ECE6DB]">
              <div className="flex flex-wrap items-center gap-2">
                {/* Decision Badge */}
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${decisionStyles.bg} ${decisionStyles.text} ${decisionStyles.border}`}
                >
                  <ShieldCheck className="h-3 w-3" />
                  <span>{decisionStyles.label}</span>
                </span>

                {/* Confidence Badge */}
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${confStyles.bg} ${confStyles.text} ${confStyles.border}`}
                >
                  <Sparkles className="h-3 w-3" />
                  <span>{formatPercent(answerRes.confidence)} Confidence</span>
                </span>

                {/* Execution Latency */}
                {metrics && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-[#F5F1E8] text-[#5E5E5E] border border-[#E5DED3]">
                    <Clock className="h-3 w-3 text-[#6B2E46]" />
                    <span>{formatMs(metrics.response_generation_time_ms || metrics.llm_latency_ms)}</span>
                  </span>
                )}
              </div>

              {/* Copy & Actions */}
              <div className="flex items-center gap-1">
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg text-[#5E5E5E] hover:text-[#1F1F1F] hover:bg-[#B3BAAC]/20 transition-colors cursor-pointer text-xs flex items-center gap-1"
                  title="Copy response"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#6B2E46]" />
                      <span className="text-[11px] text-[#6B2E46] font-medium">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span className="text-[11px] hidden sm:inline">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Markdown Formatted Answer */}
          <div className="prose prose-sm max-w-none text-[#1F1F1F] text-sm leading-relaxed break-words">
            <ReactMarkdown
              components={{
                code({ node, className, children, ...props }) {
                  return (
                    <code
                      className="bg-[#F5F1E8] px-1.5 py-0.5 rounded font-mono text-xs text-[#6B2E46] border border-[#E5DED3]"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                pre({ node, children, ...props }) {
                  return (
                    <pre
                      className="bg-[#1F1F1F] text-[#F5F1E8] p-3 rounded-xl overflow-x-auto text-xs my-2 font-mono"
                      {...props}
                    >
                      {children}
                    </pre>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Citations Preview Strip */}
          {answerRes?.citations && answerRes.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[#ECE6DB]">
              <div className="text-[11px] font-semibold text-[#5E5E5E] uppercase tracking-wider mb-2 flex items-center gap-1">
                <Quote className="h-3 w-3 text-[#6B2E46]" />
                <span>Supporting Citations ({answerRes.citations.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {answerRes.citations.map((c, idx) => (
                  <button
                    key={idx}
                    onClick={() => onInspectMessage?.(message, "citations")}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-[#F5F1E8] hover:bg-[#B3BAAC]/20 text-[#1F1F1F] hover:text-[#6B2E46] border border-[#E5DED3] hover:border-[#6B2E46] transition-colors cursor-pointer"
                    title={c.quote || c.source_name}
                  >
                    <span className="font-semibold">{c.source_name}</span>
                    <span className="text-[10px] text-[#5E5E5E] font-mono">[{c.chunk_id}]</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Pipeline Inspector Expand Button */}
          {answerRes && (
            <div className="mt-3 flex items-center justify-between text-xs pt-2">
              <span className="text-[11px] text-[#5E5E5E]">
                {formatTimestamp(message.timestamp)}
              </span>
              <button
                onClick={() => onInspectMessage?.(message, "trace")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-[#6B2E46] bg-[#B3BAAC]/20 hover:bg-[#B3BAAC]/30 transition-colors cursor-pointer"
              >
                <span>Inspect Pipeline & Evidence</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

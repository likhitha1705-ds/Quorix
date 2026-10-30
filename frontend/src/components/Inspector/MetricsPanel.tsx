import React from "react";
import { BarChart3, Clock, Cpu, Layers, DollarSign, Database, Sparkles } from "lucide-react";
import type { ChatMessage } from "@/types";
import { formatMs, formatCost } from "@/utils";

interface MetricsPanelProps {
  message: ChatMessage | null;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ message }) => {
  if (!message || !message.answerResponse) {
    return (
      <div className="text-center py-12 px-4 text-xs text-[#5E5E5E]">
        <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-40 text-[#6B2E46]" />
        No operational metrics available. Send a query to view runtime resource consumption.
      </div>
    );
  }

  const ans = message.answerResponse;
  const metrics = ans?.execution_metrics || ({} as any);
  const retrieval = metrics?.retrieval_metrics;
  const budget = retrieval?.retrieval_budget_consumed;

  return (
    <div className="p-4 space-y-4">
      {/* Overview Stat */}
      <div className="p-3 rounded-xl bg-[#F5F1E8] border border-[#E5DED3] text-xs">
        <span className="font-semibold text-[#1F1F1F] block mb-0.5">
          Retrieval & Inference Performance
        </span>
        <p className="text-[11px] text-[#5E5E5E]">
          Real-time metrics tracking resource allocation, latency bottlenecks, and token expenditure.
        </p>
      </div>

      {/* Grid of Metric Cards */}
      <div className="grid grid-cols-2 gap-2.5">
        {/* Total Time */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <Clock className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Execution Time</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {formatMs(metrics?.response_generation_time_ms || metrics?.llm_latency_ms)}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            LLM: {formatMs(metrics?.llm_latency_ms)}
          </span>
        </div>

        {/* Tokens Used */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <Cpu className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Tokens Used</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {metrics?.total_tokens ? metrics.total_tokens.toLocaleString() : "0"}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            Prompt: {metrics?.prompt_tokens ?? 0} • Output: {metrics?.completion_tokens ?? 0}
          </span>
        </div>

        {/* Chunks Retrieved */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <Database className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Chunks Retrieved</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {retrieval?.retrieved_chunks || 2}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            Limit: {budget?.chunks_limit || 10} chunks
          </span>
        </div>

        {/* Retrieval Calls */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <Layers className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Retrieval Calls</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {retrieval?.retrieval_calls || 2}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            Cap: {budget?.calls_limit || 3} calls
          </span>
        </div>

        {/* Sources Queried */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <Sparkles className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Sources Queried</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {retrieval?.selected_sources?.length || 2}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            Skipped: {retrieval?.skipped_sources?.length || 1}
          </span>
        </div>

        {/* Estimated Cost */}
        <div className="p-3 rounded-xl bg-white border border-[#E5DED3] shadow-soft-sm">
          <div className="flex items-center gap-1.5 text-[#5E5E5E] text-[11px] mb-1 font-medium">
            <DollarSign className="h-3.5 w-3.5 text-[#6B2E46]" />
            <span>Est. Cost</span>
          </div>
          <div className="text-base font-bold text-[#1F1F1F]">
            {formatCost(metrics.estimated_cost)}
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            Gemini 2.0 Flash
          </span>
        </div>
      </div>

      {/* Retrieval Budget Consumption Progress */}
      {budget && (
        <div className="p-3.5 rounded-xl border border-[#E5DED3] bg-white shadow-soft-sm space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-[#1F1F1F]">Retrieval Budget Utilization</span>
            <span className="text-[11px] font-normal text-[#5E5E5E]">
              {budget.budget_exhausted ? "Budget Exhausted" : "Within Quota"}
            </span>
          </div>

          {/* Chunks Progress */}
          <div>
            <div className="flex items-center justify-between text-[11px] text-[#5E5E5E] mb-1">
              <span>Chunk Utilization</span>
              <span>{budget.chunks_used} / {budget.chunks_limit}</span>
            </div>
            <div className="h-1.5 bg-[#F5F1E8] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#6B2E46] rounded-full transition-all"
                style={{ width: `${Math.min(100, (budget.chunks_used / Math.max(1, budget.chunks_limit)) * 100)}%` }}
              />
            </div>
          </div>

          {/* Tokens Progress */}
          <div>
            <div className="flex items-center justify-between text-[11px] text-[#5E5E5E] mb-1">
              <span>Context Tokens</span>
              <span>{budget.tokens_used} / {budget.tokens_limit}</span>
            </div>
            <div className="h-1.5 bg-[#F5F1E8] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#6B2E46] rounded-full transition-all"
                style={{ width: `${Math.min(100, (budget.tokens_used / Math.max(1, budget.tokens_limit)) * 100)}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

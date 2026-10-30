import React from "react";
import { ShieldCheck, Search, Layers, Cpu, Sparkles, Database } from "lucide-react";
import type { ChatMessage } from "@/types";
import { formatMs, formatPercent, getDecisionBadgeStyles } from "@/utils";

interface DecisionTraceProps {
  message: ChatMessage | null;
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ message }) => {
  if (!message || !message.answerResponse) {
    return (
      <div className="text-center py-12 px-4 text-xs text-[#5E5E5E]">
        <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-40 text-[#6B2E46]" />
        Select or submit a query to view the Quorix reasoning pipeline trace.
      </div>
    );
  }

  const ans = message.answerResponse;
  const evalRes = message.evaluationResponse;
  const queryDecision = message.queryDecision;
  const metrics = ans?.execution_metrics;
  const retrieval = metrics?.retrieval_metrics;
  const decisionStyles = getDecisionBadgeStyles(ans.decision);

  const steps = [
    {
      title: "Query Analysis",
      icon: Search,
      status: "completed",
      badge: queryDecision?.query_analysis?.intent || "Analyzed",
      description: `Extracted intent & entities: ${
        queryDecision?.query_analysis?.entities?.join(", ") || "Technical topic"
      }`,
    },
    {
      title: "Source Selection",
      icon: Layers,
      status: "completed",
      badge: `${retrieval?.selected_sources?.length || 2} Selected`,
      description: `Targeted ${
        retrieval?.selected_sources?.map((s) => s.replace("src_", "")).join(", ") || "documentation"
      }; skipped ${retrieval?.skipped_sources?.length || 1} irrelevant sources.`,
    },
    {
      title: "Budget Allocation",
      icon: Cpu,
      status: "completed",
      badge: `${retrieval?.retrieval_budget_consumed?.chunks_limit || 10} Chunks Cap`,
      description: `Allocated ${retrieval?.retrieval_budget_consumed?.calls_limit || 3} calls, ${
        retrieval?.retrieval_budget_consumed?.tokens_limit || 4000
      } tokens maximum budget.`,
    },
    {
      title: "Hybrid Retrieval",
      icon: Database,
      status: "completed",
      badge: `${retrieval?.retrieved_chunks || 2} Chunks`,
      description: `Executed vector search + BM25 lexical fusion in ${formatMs(
        retrieval?.execution_time_ms
      )}.`,
    },
    {
      title: "Evidence Evaluation",
      icon: ShieldCheck,
      status: ans.decision === "CONFLICTING" ? "warning" : "completed",
      badge: `${ans.decision} (${formatPercent(ans.confidence)})`,
      description: ans.reasoning || evalRes?.evaluation_explanation || "Evidence validated.",
    },
    {
      title: "Answer Generation",
      icon: Sparkles,
      status: "completed",
      badge: `${ans.citations?.length || 0} Citations`,
      description: `Synthesized grounded response in ${formatMs(
        metrics?.response_generation_time_ms || metrics?.llm_latency_ms
      )}.`,
    },
  ];

  return (
    <div className="p-4 space-y-6">
      {/* Top Summary Banner */}
      <div className={`p-3.5 rounded-xl border ${decisionStyles.bg} ${decisionStyles.border} space-y-1`}>
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-[#1F1F1F]">Sufficiency Verdict</span>
          <span className={decisionStyles.text}>{decisionStyles.label}</span>
        </div>
        <p className="text-xs text-[#5E5E5E] leading-relaxed">
          {ans.reasoning}
        </p>
      </div>

      {/* Vertical Animated Timeline */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#E5DED3]">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isWarning = step.status === "warning";

          return (
            <div key={idx} className="relative group">
              {/* Timeline Node Dot */}
              <div
                className={`absolute -left-6 top-0.5 h-5 w-5 rounded-full flex items-center justify-center text-white ring-4 ring-white shadow-soft-sm transition-all ${
                  isWarning
                    ? "bg-[#B3BAAC]"
                    : "bg-[#6B2E46]"
                }`}
              >
                <Icon className="h-2.5 w-2.5 text-white" />
              </div>

              {/* Step Content Card */}
              <div className="p-3 rounded-xl border border-[#E5DED3] bg-white shadow-soft-sm">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <h4 className="text-xs font-bold text-[#1F1F1F] flex items-center gap-1.5">
                    <span>{step.title}</span>
                  </h4>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F5F1E8] text-[#6B2E46] border border-[#E5DED3]">
                    {step.badge}
                  </span>
                </div>
                <p className="text-[11px] text-[#5E5E5E] leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingIndicatorProps {
  currentStage?: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  currentStage = "Processing retrieval intelligence...",
}) => {
  return (
    <div className="flex items-start gap-3 my-4 max-w-3xl mx-auto px-4 animate-fade-in">
      {/* Bot Avatar */}
      <div className="h-8 w-8 rounded-xl bg-[#6B2E46] flex items-center justify-center text-white shrink-0 shadow-soft-sm">
        <Loader2 className="h-4 w-4 animate-spin text-white" />
      </div>

      {/* Loading Stage Card */}
      <div className="flex-1 p-4 rounded-2xl bg-white border border-[#E5DED3] shadow-soft">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-semibold text-[#6B2E46] uppercase tracking-wider">
            Quorix Pipeline Active
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-[#6B2E46] animate-pulse" />
        </div>

        {/* Current Stage Label */}
        <p className="text-sm font-medium text-[#1F1F1F] flex items-center gap-2 mb-3">
          <Loader2 className="h-4 w-4 text-[#6B2E46] animate-spin" />
          <span>{currentStage}</span>
        </p>

        {/* Micro Stage Progress Bar */}
        <div className="h-1.5 w-full bg-[#F5F1E8] rounded-full overflow-hidden">
          <div className="h-full bg-[#6B2E46] w-full animate-pulse" />
        </div>
      </div>
    </div>
  );
};

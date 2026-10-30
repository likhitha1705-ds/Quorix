import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { EvidenceDecision } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return "0%";
  return `${Math.round(value * 100)}%`;
}

export function formatMs(ms: number | undefined | null): string {
  if (ms === undefined || ms === null || isNaN(ms)) return "0 ms";
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${Math.round(ms)} ms`;
}

export function formatCost(usd: number | undefined | null): string {
  if (usd === undefined || usd === null || isNaN(usd)) return "$0.00";
  if (usd === 0) return "$0.00";
  if (usd < 0.0001) return `<$0.0001`;
  return `$${usd.toFixed(5)}`;
}

export function formatTimestamp(isoString?: string): string {
  if (!isoString) return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  try {
    return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return isoString;
  }
}

export function getDecisionBadgeStyles(decision: EvidenceDecision | string): {
  bg: string;
  text: string;
  border: string;
  label: string;
} {
  switch (decision?.toUpperCase()) {
    case "SUFFICIENT":
      return {
        bg: "bg-[#6B2E46]/10",
        text: "text-[#6B2E46]",
        border: "border-[#6B2E46]/20",
        label: "SUFFICIENT",
      };
    case "CONFLICTING":
      return {
        bg: "bg-rose-500/10",
        text: "text-rose-800",
        border: "border-rose-300",
        label: "CONFLICTING",
      };
    case "INSUFFICIENT":
      return {
        bg: "bg-[#B3BAAC]/25",
        text: "text-[#1F1F1F]",
        border: "border-[#E5DED3]",
        label: "INSUFFICIENT",
      };
    case "UNSUPPORTED":
    default:
      return {
        bg: "bg-[#B3BAAC]/15",
        text: "text-[#5E5E5E]",
        border: "border-[#E5DED3]",
        label: "UNSUPPORTED",
      };
  }
}

export function getConfidenceBadgeStyles(score: number): {
  bg: string;
  text: string;
  border: string;
} {
  if (score >= 0.8) {
    return {
      bg: "bg-[#6B2E46]/10",
      text: "text-[#6B2E46]",
      border: "border-[#6B2E46]/20",
    };
  }
  if (score >= 0.65) {
    return {
      bg: "bg-[#B3BAAC]/25",
      text: "text-[#1F1F1F]",
      border: "border-[#E5DED3]",
    };
  }
  if (score >= 0.4) {
    return {
      bg: "bg-[#B3BAAC]/15",
      text: "text-[#5E5E5E]",
      border: "border-[#E5DED3]",
    };
  }
  return {
    bg: "bg-rose-500/10",
    text: "text-rose-800",
    border: "border-rose-200",
  };
}

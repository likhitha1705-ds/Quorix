import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ShieldCheck,
  Search,
  Layers,
  Cpu,
  FileText,
  MessageSquare,
  Ticket,
  AlertTriangle,
  Sparkles,
  Database,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Compass,
  Scale,
} from "lucide-react";
import type { NavTab } from "@/components/Header/Header";

interface OverviewPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  const [activeWorkflowStep, setActiveWorkflowStep] = useState<number | null>(null);

  // Workflow steps for "How It Works"
  const workflowSteps = [
    { id: 1, name: "User Query", desc: "Natural language input", icon: Search },
    { id: 2, name: "Intent Analysis", desc: "Intent, entities & format", icon: Compass },
    { id: 3, name: "Source Selection", desc: "Authoritative routing", icon: Layers },
    { id: 4, name: "Budget Manager", desc: "Tokens & chunk caps", icon: Cpu },
    { id: 5, name: "Hybrid Retrieval", desc: "Semantic + BM25 fusion", icon: Database },
    { id: 6, name: "Evidence Intelligence", desc: "Scoring & conflict check", icon: ShieldCheck },
    { id: 7, name: "Gemini", desc: "Grounded LLM generator", icon: Sparkles },
    { id: 8, name: "Answer with Citations", desc: "Verified output", icon: CheckCircle2 },
  ];

  return (
    <div className="min-h-full overflow-y-auto bg-[#F5F1E8] text-[#1F1F1F] transition-colors">
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-24 space-y-28">
        {/* ========================================================================= */}
        {/* HERO SECTION                                                              */}
        {/* ========================================================================= */}
        <section className="pt-6 sm:pt-12 lg:pt-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Hero Left Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="lg:col-span-7 flex flex-col items-start text-left"
            >
              {/* Small Category Pill */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#B3BAAC]/20 border border-[#B3BAAC]/40 text-[#6B2E46] text-xs font-semibold tracking-wider uppercase mb-6 shadow-soft-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-[#6B2E46]" />
                <span>Intelligent Context Selection & Retrieval Optimization</span>
              </div>

              {/* Main Heading */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#6B2E46] leading-[1.12] mb-6">
                Decide where to search before retrieval.
                <span className="block mt-1 text-[#6B2E46]/90">
                  Decide what to trust after.
                </span>
              </h1>

              {/* Description */}
              <p className="text-base sm:text-lg text-[#5E5E5E] max-w-2xl leading-relaxed mb-8 font-normal">
                Quorix intelligently selects the most relevant knowledge sources before retrieval, evaluates retrieved evidence, and generates trustworthy AI responses with citations while reducing unnecessary retrieval cost.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 w-full sm:w-auto">
                <button
                  onClick={() => onNavigate("demo")}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#6B2E46] hover:bg-[#57263A] text-white font-semibold text-sm shadow-soft transition-all hover:-translate-y-0.5 cursor-pointer group"
                >
                  <span>Run Live Demo</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </button>

                <button
                  onClick={() => onNavigate("comparison")}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-[#F5F1E8] text-[#6B2E46] font-semibold text-sm border border-[#B3BAAC] shadow-soft-sm transition-all cursor-pointer"
                >
                  <Scale className="h-4 w-4 text-[#6B2E46]" />
                  <span>Compare with Traditional RAG</span>
                </button>
              </div>

              {/* Trust Indicators */}
              <div className="flex flex-wrap items-center gap-6 mt-10 pt-6 border-t border-[#E5DED3] text-xs text-[#5E5E5E]">
                <div className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-[#6B2E46]" />
                  <span>Zero-Trust Evidence Scoring</span>
                </div>
                <div className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-[#6B2E46]" />
                  <span>Dynamic Cost & Token Caps</span>
                </div>
                <div className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-[#6B2E46]" />
                  <span>Contradiction Detection</span>
                </div>
              </div>
            </motion.div>

            {/* Hero Right Visual Illustration (Pure React + SVG CSS, No Images) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="lg:col-span-5 relative flex items-center justify-center"
            >
              <div className="relative w-full max-w-md aspect-square rounded-3xl bg-[#F5F1E8] border border-[#E5DED3] p-6 shadow-soft flex items-center justify-center overflow-hidden">
                {/* Background Subtle Dot Pattern */}
                <div className="absolute inset-0 bg-[radial-gradient(#E5DED3_1px,transparent_1px)] [background-size:16px_16px] opacity-70" />

                {/* SVG Connecting Flow Lines (Deep Burgundy Dashed Paths) */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  viewBox="0 0 400 400"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Connector to Top Node (Documents) */}
                  <path
                    d="M 200 70 L 200 170"
                    stroke="#6B2E46"
                    strokeWidth="2"
                    strokeDasharray="6 6"
                    className="animate-[dash_15s_linear_infinite]"
                  />
                  {/* Connector to Bottom Left Node (Conversations) */}
                  <path
                    d="M 80 300 Q 140 250 180 220"
                    stroke="#6B2E46"
                    strokeWidth="2"
                    strokeDasharray="6 6"
                    className="animate-[dash_15s_linear_infinite]"
                  />
                  {/* Connector to Bottom Right Node (Tickets) */}
                  <path
                    d="M 320 300 Q 260 250 220 220"
                    stroke="#6B2E46"
                    strokeWidth="2"
                    strokeDasharray="6 6"
                    className="animate-[dash_15s_linear_infinite]"
                  />
                </svg>

                {/* Central QUORIX Core Node (Deep Burgundy, no glow) */}
                <div className="relative z-10 flex flex-col items-center justify-center">
                  <div className="relative">
                    <div className="relative h-24 w-24 rounded-2xl bg-[#6B2E46] flex flex-col items-center justify-center text-white shadow-soft">
                      <span className="font-extrabold text-3xl tracking-tight">Q</span>
                      <span className="text-[9px] font-bold tracking-widest uppercase text-[#F5F1E8]">QUORIX</span>
                    </div>
                  </div>
                  <div className="mt-2.5 px-3 py-1 rounded-full bg-[#B3BAAC] text-[#1F1F1F] text-[10px] font-mono font-semibold tracking-wider uppercase border border-[#B3BAAC] shadow-soft-sm">
                    Zero-Trust Core
                  </div>
                </div>

                {/* Source Node 1: Documents (Top Center) */}
                <div className="absolute top-6 left-1/2 -translate-x-1/2 z-10">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-white border border-[#E5DED3] shadow-soft"
                  >
                    <div className="p-1.5 rounded-lg bg-[#B3BAAC]/20 text-[#6B2E46]">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-bold text-[#1F1F1F] flex items-center gap-1.5">
                        <span>Documents</span>
                        <span className="text-[9px] font-mono font-bold text-[#6B2E46] bg-[#B3BAAC]/20 px-1 py-0.2 rounded">
                          0.85
                        </span>
                      </div>
                      <span className="text-[10px] text-[#5E5E5E]">Architecture Specs & RFCs</span>
                    </div>
                  </motion.div>
                </div>

                {/* Source Node 2: Engineering Conversations (Bottom Left) */}
                <div className="absolute bottom-6 left-4 z-10">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white border border-[#E5DED3] shadow-soft"
                  >
                    <div className="p-1.5 rounded-lg bg-[#B3BAAC]/20 text-[#6B2E46]">
                      <MessageSquare className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-bold text-[#1F1F1F] flex items-center gap-1.5">
                        <span>Conversations</span>
                        <span className="text-[9px] font-mono font-bold text-[#6B2E46] bg-[#B3BAAC]/20 px-1 py-0.2 rounded">
                          0.50
                        </span>
                      </div>
                      <span className="text-[10px] text-[#5E5E5E]">Slack & Tech Discussions</span>
                    </div>
                  </motion.div>
                </div>

                {/* Source Node 3: Development Tickets (Bottom Right) */}
                <div className="absolute bottom-6 right-4 z-10">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white border border-[#E5DED3] shadow-soft"
                  >
                    <div className="p-1.5 rounded-lg bg-[#B3BAAC]/20 text-[#6B2E46]">
                      <Ticket className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-bold text-[#1F1F1F] flex items-center gap-1.5">
                        <span>Tickets</span>
                        <span className="text-[9px] font-mono font-bold text-[#6B2E46] bg-[#B3BAAC]/20 px-1 py-0.2 rounded">
                          0.60
                        </span>
                      </div>
                      <span className="text-[10px] text-[#5E5E5E]">Jira & GitHub Issues</span>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* STAGE SECTION                                                             */}
        {/* ========================================================================= */}
        <section>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Card 1: Pre-Retrieval */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ duration: 0.2 }}
              className="relative p-8 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:border-[#B3BAAC] transition-all flex flex-col justify-between overflow-hidden group"
            >
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#B3BAAC]/25 text-[#6B2E46] text-xs font-bold tracking-wider uppercase mb-4 border border-[#B3BAAC]/40">
                  Stage 1
                </div>
                <h3 className="text-2xl font-bold text-[#6B2E46] mb-3">
                  Pre-Retrieval Intelligence
                </h3>
                <p className="text-sm sm:text-base text-[#5E5E5E] leading-relaxed font-normal mb-6">
                  Decide where to search before reading any knowledge source.
                </p>
                <ul className="space-y-2.5 text-xs sm:text-sm text-[#5E5E5E]">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Intent, entity and expected format decomposition</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Multi-criterion source authority scoring & pruning</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Strict query limits, token budgets & call allocation</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8 pt-4 border-t border-[#ECE6DB] flex items-center justify-between text-xs font-semibold text-[#6B2E46]">
                <span>Phase 3 & 4 Orchestration</span>
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.div>

            {/* Card 2: Post-Retrieval */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ duration: 0.2 }}
              className="relative p-8 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:border-[#B3BAAC] transition-all flex flex-col justify-between overflow-hidden group"
            >
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#B3BAAC]/25 text-[#6B2E46] text-xs font-bold tracking-wider uppercase mb-4 border border-[#B3BAAC]/40">
                  Stage 2
                </div>
                <h3 className="text-2xl font-bold text-[#6B2E46] mb-3">
                  Post-Retrieval Evidence Intelligence
                </h3>
                <p className="text-sm sm:text-base text-[#5E5E5E] leading-relaxed font-normal mb-6">
                  Evaluate retrieved evidence before generating an answer.
                </p>
                <ul className="space-y-2.5 text-xs sm:text-sm text-[#5E5E5E]">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Multi-criterion chunk scoring (Relevance, Authority, Freshness, Directness)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Cross-source contradiction & temporal discrepancy detection</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] shrink-0" />
                    <span>Sufficiency gating: refusal of unsupported questions without hallucination</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8 pt-4 border-t border-[#ECE6DB] flex items-center justify-between text-xs font-semibold text-[#6B2E46]">
                <span>Phase 5 & 6 Orchestration</span>
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* THE QUORIX ADVANTAGE (6 FEATURE CARDS)                                     */}
        {/* ========================================================================= */}
        <section className="text-center">
          <div className="max-w-2xl mx-auto mb-16">
            <span className="text-xs uppercase font-bold tracking-wider text-[#6B2E46]">
              Core Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#6B2E46] mt-2 mb-4 tracking-tight">
              The Quorix Advantage
            </h2>
            <p className="text-sm sm:text-base text-[#5E5E5E]">
              Traditional RAG assumes similarity equals truth. Quorix replaces blind retrieval with a disciplined zero-trust reasoning engine.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-left">
            {/* 1. Intent Analysis */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <Compass className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Intent Analysis
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Extracts intent, entities and information type before touching the retrieval corpus.
                </p>
              </div>
            </motion.div>

            {/* 2. Smart Source Selection */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <Layers className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Smart Source Selection
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Chooses only relevant knowledge sources, dynamically skipping noise and irrelevant silos.
                </p>
              </div>
            </motion.div>

            {/* 3. Focused Retrieval */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <Cpu className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Focused Retrieval
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Retrieves fewer chunks using a retrieval budget, strictly bounding cost and token footprint.
                </p>
              </div>
            </motion.div>

            {/* 4. Evidence Evaluation */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Evidence Evaluation
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Scores every retrieved chunk across relevance, authority, freshness, and directness.
                </p>
              </div>
            </motion.div>

            {/* 5. Conflict Detection */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Conflict Detection
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Detects inconsistent or contradictory evidence across architecture docs, threads and tickets.
                </p>
              </div>
            </motion.div>

            {/* 6. Grounded Answers */}
            <motion.div
              whileHover={{ y: -3 }}
              className="p-6 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft hover:shadow-md hover:border-[#B3BAAC] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-4">
                  <Sparkles className="h-5 w-5" />
                </div>
                <h4 className="text-base font-bold text-[#1F1F1F] mb-2">
                  Grounded Answers
                </h4>
                <p className="text-xs sm:text-sm text-[#5E5E5E] leading-relaxed font-normal">
                  Answers only from validated evidence with precise inline citations and refusal of false facts.
                </p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* HOW IT WORKS (HORIZONTAL WORKFLOW)                                        */}
        {/* ========================================================================= */}
        <section>
          <div className="max-w-2xl mx-auto text-center mb-16">
            <span className="text-xs uppercase font-bold tracking-wider text-[#6B2E46]">
              Pipeline Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#6B2E46] mt-2 mb-4 tracking-tight">
              How Quorix Works
            </h2>
            <p className="text-sm sm:text-base text-[#5E5E5E]">
              An end-to-end disciplined pipeline that guarantees answers are grounded in validated truth.
            </p>
          </div>

          {/* Horizontal Scrollable Workflow Sequence */}
          <div className="overflow-x-auto pb-6 pt-2">
            <div className="flex items-center min-w-max gap-3 justify-between px-2">
              {workflowSteps.map((step, idx) => {
                const Icon = step.icon;
                const isHovered = activeWorkflowStep === step.id;

                return (
                  <React.Fragment key={step.id}>
                    {/* Workflow Node */}
                    <motion.div
                      onHoverStart={() => setActiveWorkflowStep(step.id)}
                      onHoverEnd={() => setActiveWorkflowStep(null)}
                      whileHover={{ scale: 1.05, y: -2 }}
                      className={`relative flex flex-col items-center p-4 rounded-[20px] border transition-all cursor-default w-36 text-center ${
                        isHovered
                          ? "bg-white border-[#6B2E46] shadow-soft"
                          : "bg-white border-[#E5DED3] shadow-soft-sm"
                      }`}
                    >
                      <div className="text-[10px] font-mono font-bold text-[#B3BAAC] mb-1.5">
                        0{step.id}
                      </div>
                      <div className="h-9 w-9 rounded-xl bg-[#B3BAAC]/20 text-[#6B2E46] flex items-center justify-center mb-2.5">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-bold text-[#1F1F1F] leading-tight mb-1">
                        {step.name}
                      </span>
                      <span className="text-[10px] text-[#5E5E5E] leading-tight">
                        {step.desc}
                      </span>
                    </motion.div>

                    {/* Connector Arrow */}
                    {idx < workflowSteps.length - 1 && (
                      <div className="flex items-center justify-center px-1 text-[#B3BAAC]">
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* WHY QUORIX (SIDE-BY-SIDE COMPARISON)                                      */}
        {/* ========================================================================= */}
        <section>
          <div className="max-w-2xl mx-auto text-center mb-16">
            <span className="text-xs uppercase font-bold tracking-wider text-[#6B2E46]">
              Head-to-Head Comparison
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#6B2E46] mt-2 mb-4 tracking-tight">
              Why Quorix?
            </h2>
            <p className="text-sm sm:text-base text-[#5E5E5E]">
              Compare naive enterprise RAG against Quorix's evidence intelligence architecture.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Traditional RAG Card */}
            <div className="p-8 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#B3BAAC]/20 text-[#5E5E5E] text-xs font-bold uppercase tracking-wider mb-4 border border-[#E5DED3]">
                  <XCircle className="h-3.5 w-3.5 text-[#5E5E5E]" />
                  <span>Traditional RAG</span>
                </div>
                <h3 className="text-xl font-bold text-[#1F1F1F] mb-2">
                  Naive & Unbounded
                </h3>
                <p className="text-xs text-[#5E5E5E] mb-6">
                  Blindly retrieves top-k vectors without source authority or contradiction checks.
                </p>

                <ul className="space-y-3.5 text-sm">
                  <li className="flex items-start gap-2.5 text-[#5E5E5E]">
                    <XCircle className="h-4 w-4 text-[#5E5E5E] mt-0.5 shrink-0" />
                    <span><strong>Retrieves everything:</strong> Pollutes context by querying every index indiscriminately.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#5E5E5E]">
                    <XCircle className="h-4 w-4 text-[#5E5E5E] mt-0.5 shrink-0" />
                    <span><strong>Large context:</strong> Stuffs tens of thousands of tokens into prompts, increasing latency.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#5E5E5E]">
                    <XCircle className="h-4 w-4 text-[#5E5E5E] mt-0.5 shrink-0" />
                    <span><strong>Higher cost:</strong> Massive LLM bills caused by unbounded chunk retrieval.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#5E5E5E]">
                    <XCircle className="h-4 w-4 text-[#5E5E5E] mt-0.5 shrink-0" />
                    <span><strong>No evidence validation:</strong> Assumes semantic similarity equals factual correctness.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#5E5E5E]">
                    <XCircle className="h-4 w-4 text-[#5E5E5E] mt-0.5 shrink-0" />
                    <span><strong>Possible hallucinations:</strong> Generates fluent answers even when sources disagree.</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Quorix Card */}
            <div className="p-8 rounded-[20px] bg-white border-2 border-[#6B2E46]/30 shadow-soft relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#6B2E46]/10 text-[#6B2E46] text-xs font-bold uppercase tracking-wider mb-4 border border-[#6B2E46]/20">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#6B2E46]" />
                  <span>Quorix Zero-Trust RAG</span>
                </div>
                <h3 className="text-xl font-bold text-[#6B2E46] mb-2">
                  Disciplined & Verifiable
                </h3>
                <p className="text-xs text-[#5E5E5E] mb-6">
                  Selects authoritative sources upfront and validates evidence before generation.
                </p>

                <ul className="space-y-3.5 text-sm">
                  <li className="flex items-start gap-2.5 text-[#1F1F1F]">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] mt-0.5 shrink-0" />
                    <span><strong>Intelligent source selection:</strong> Identifies and routes queries to relevant repositories.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#1F1F1F]">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] mt-0.5 shrink-0" />
                    <span><strong>Budget-aware retrieval:</strong> Enforces token, chunk, and API call caps adaptively.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#1F1F1F]">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] mt-0.5 shrink-0" />
                    <span><strong>Evidence scoring:</strong> Evaluates chunks on relevance, authority, freshness, and directness.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#1F1F1F]">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] mt-0.5 shrink-0" />
                    <span><strong>Conflict detection:</strong> Detects and highlights disagreements across disparate documentation.</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-[#1F1F1F]">
                    <CheckCircle2 className="h-4 w-4 text-[#6B2E46] mt-0.5 shrink-0" />
                    <span><strong>Grounded answers:</strong> Generates syntheses with verifiable, click-to-view citations.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* ARCHITECTURE PREVIEW                                                      */}
        {/* ========================================================================= */}
        <section>
          <div className="p-8 sm:p-12 rounded-[20px] bg-white border border-[#E5DED3] shadow-soft">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider text-[#6B2E46]">
                  Full System Overview
                </span>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-[#6B2E46] mt-1">
                  Architecture Preview
                </h3>
                <p className="text-xs sm:text-sm text-[#5E5E5E] mt-1 max-w-xl">
                  Modular multi-stage retrieval architecture running with Qdrant vector database, BM25 keyword fusion, and Gemini 2.0 Flash.
                </p>
              </div>

              <button
                onClick={() => onNavigate("architecture")}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-[#F5F1E8] text-[#6B2E46] border border-[#B3BAAC] font-semibold text-xs shadow-soft-sm transition-colors shrink-0 cursor-pointer"
              >
                <span>View Full Architecture</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Simplified Architecture Block Diagram */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
              {/* Layer 1 */}
              <div className="p-4 rounded-xl border border-[#E5DED3] bg-[#F5F1E8]">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B2E46] mb-1">
                  Phase 3
                </div>
                <h4 className="text-sm font-bold text-[#1F1F1F] mb-1">
                  Query Intelligence
                </h4>
                <p className="text-xs text-[#5E5E5E]">
                  Intent classification, entity recognition, and multi-source authority routing.
                </p>
              </div>

              {/* Layer 2 */}
              <div className="p-4 rounded-xl border border-[#E5DED3] bg-[#F5F1E8]">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B2E46] mb-1">
                  Phase 4
                </div>
                <h4 className="text-sm font-bold text-[#1F1F1F] mb-1">
                  Hybrid Retrieval
                </h4>
                <p className="text-xs text-[#5E5E5E]">
                  Adaptive budget caps, Qdrant dense vector search & BM25 keyword fusion.
                </p>
              </div>

              {/* Layer 3 */}
              <div className="p-4 rounded-xl border border-[#E5DED3] bg-[#F5F1E8]">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B2E46] mb-1">
                  Phase 5
                </div>
                <h4 className="text-sm font-bold text-[#1F1F1F] mb-1">
                  Evidence Intelligence
                </h4>
                <p className="text-xs text-[#5E5E5E]">
                  Multi-criterion scoring, contradiction matrix, and sufficiency decision gating.
                </p>
              </div>

              {/* Layer 4 */}
              <div className="p-4 rounded-xl border border-[#E5DED3] bg-[#F5F1E8]">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B2E46] mb-1">
                  Phase 6
                </div>
                <h4 className="text-sm font-bold text-[#1F1F1F] mb-1">
                  Grounded Synthesis
                </h4>
                <p className="text-xs text-[#5E5E5E]">
                  Gemini LLM response synthesis with verified attribution and structured citations.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* CALL TO ACTION (CTA)                                                      */}
        {/* ========================================================================= */}
        <section className="text-center">
          <div className="relative p-10 sm:p-14 rounded-[20px] bg-[#6B2E46] text-white shadow-soft overflow-hidden">
            <div className="relative z-10 max-w-2xl mx-auto flex flex-col items-center">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4 text-white">
                Ready to see Quorix in action?
              </h2>
              <p className="text-sm sm:text-base text-[#F5F1E8]/90 mb-8 max-w-xl font-normal">
                Query live architectural knowledge, inspect reasoning pipelines step-by-step, and observe how zero-trust retrieval halts hallucinations.
              </p>
              <button
                onClick={() => onNavigate("demo")}
                className="inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-white hover:bg-[#F5F1E8] text-[#6B2E46] font-bold text-sm shadow-soft transition-all hover:scale-105 active:scale-95 cursor-pointer group"
              >
                <span>Launch Demo</span>
                <ArrowRight className="h-4 w-4 text-[#6B2E46] transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* FOOTER                                                                    */}
        {/* ========================================================================= */}
        <footer className="pt-8 border-t border-[#ECE6DB] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#5E5E5E]">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#6B2E46]">Quorix</span>
            <span>•</span>
            <span>Intelligent Context Selection & Retrieval Optimization Engine</span>
          </div>
          <div className="flex items-center gap-2 text-[#5E5E5E]">
            <span>Built for Hackathon 2026</span>
          </div>
        </footer>
      </div>
    </div>
  );
};
